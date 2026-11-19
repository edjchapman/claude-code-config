#!/usr/bin/env python3
"""Measure the usage-review signals over local Claude Code session history.

Usage: signals.py measure [--until YYYY-MM-DD] [--days N] [--format table|json]

Reads the transcripts under ~/.claude/projects/ and prints aggregates only:
counts, totals, and tool, hook and model names. Nothing a transcript says —
a prompt, a file path, a project name — is ever printed, because a usage
review's pull requests quote this output verbatim (ADR-0004).

The window is whole UTC days ending at the start of --until (default:
today), so the day still in progress is left out and two runs on the same
day measure the same records.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, NamedTuple

# A pattern is proposed only when it reaches this many sessions, or this share
# of the window's sessions, whichever is larger; below that it is listed.
EVIDENCE_MIN_SESSIONS = 10
EVIDENCE_MIN_SHARE = 0.05

# Every name the script prints is a tool, hook, model or enum value taken from
# a transcript field. Anything that is not shaped like one is replaced, so a
# field that unexpectedly holds free text or a path cannot leak through.
_NAME = re.compile(r"[A-Za-z0-9_.:\[\]-]{1,80}")
UNNAMED = "(other)"


def name(value: object) -> str:
    return value if isinstance(value, str) and _NAME.fullmatch(value) else UNNAMED


class Window(NamedTuple):
    start: date
    until: date

    def __contains__(self, timestamp: object) -> bool:
        # Transcript timestamps are ISO-8601 in UTC, so the date is the first ten characters.
        if not isinstance(timestamp, str):
            return False
        return self.start.isoformat() <= timestamp[:10] < self.until.isoformat()

    def describe(self) -> dict:
        return {
            "from": self.start.isoformat(),
            "until": self.until.isoformat(),
            "days": (self.until - self.start).days,
        }


class Call(NamedTuple):
    model: str
    context: int


class Session(NamedTuple):
    """One transcript's records inside the window."""

    records: list[dict]
    calls: list[Call]
    began_in_window: bool


def percentile(values: list[int], pct: int) -> int:
    """Nearest-rank percentile: the smallest value with at least pct% of values at or below it."""
    ordered = sorted(values)
    return ordered[max(math.ceil(pct / 100 * len(ordered)), 1) - 1]


def spread(values: list[int], *pcts: int) -> dict:
    """The named percentiles and the maximum of `values`; all None when there are none."""
    result: dict = {f"p{pct}": percentile(values, pct) if values else None for pct in pcts}
    result["max"] = max(values) if values else None
    return result


def read_records(path: Path) -> Iterator[dict]:
    with path.open(errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield record


def context_tokens(usage: dict) -> int:
    fields = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
    return sum(usage.get(field) or 0 for field in fields)


def api_calls(records: list[dict]) -> list[tuple[dict, Call]]:
    """Each API call among `records`, in order, with the first record that carries it.

    A streamed response is written as one record per content block, all
    carrying the same message id and usage, so calls are keyed by that id.
    An API error is written as an assistant record with no usage; it is not a call.
    """
    calls: dict[object, tuple[dict, Call]] = {}
    for record in records:
        if record.get("type") != "assistant":
            continue
        message = record.get("message") or {}
        context = context_tokens(message.get("usage") or {})
        if context:
            calls.setdefault(message.get("id"), (record, Call(name(message.get("model")), context)))
    return list(calls.values())


def load_session(path: Path, window: Window) -> Session | None:
    """The part of a transcript inside the window, or None when it made no call there."""
    records = list(read_records(path))
    calls = api_calls(records)
    in_window = [call for record, call in calls if record.get("timestamp") in window]
    if not in_window:
        return None
    return Session(
        records=[record for record in records if record.get("timestamp") in window],
        calls=in_window,
        began_in_window=calls[0][0].get("timestamp") in window,
    )


def load_sessions(projects_dir: Path, window: Window) -> list[Session]:
    # Subagent transcripts sit one level deeper and are left out: their context
    # is their own, not the session's.
    sessions = (load_session(path, window) for path in sorted(projects_dir.glob("*/*.jsonl")))
    return [session for session in sessions if session]


def attachments(session: Session, kind: str) -> Iterator[dict]:
    for record in session.records:
        attachment = record.get("attachment")
        if record.get("type") != "attachment" or not isinstance(attachment, dict):
            continue
        if attachment.get("type") == kind:
            yield attachment


def content_blocks(record: dict, kind: str) -> Iterator[dict]:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == kind:
                yield block


def tool_uses(session: Session) -> dict[str, dict]:
    """{tool_use id: the tool_use block}, in call order."""
    uses: dict[str, dict] = {}
    for record in session.records:
        if record.get("type") == "assistant":
            for block in content_blocks(record, "tool_use"):
                uses.setdefault(str(block.get("id")), block)
    return uses


class ToolCall(NamedTuple):
    tool: str
    target: str  # what the call acted on; compared to spot a retry, never printed
    failed: bool
    denial: str | None  # the toolDenialKind, when the call was refused rather than run
    prompted: bool  # the user was asked to allow or reject it


# Tools whose whole purpose is to put a choice in front of the user. Their
# answer is recorded like a permission decision, but it is not a prompt the
# config could have avoided.
ASKING_TOOLS = frozenset({"AskUserQuestion", "ExitPlanMode"})


def call_target(tool_input: object) -> str:
    """What a call acted on: its file, or the program and subcommand of a shell command."""
    if not isinstance(tool_input, dict):
        return ""
    if isinstance(tool_input.get("file_path"), str):
        return tool_input["file_path"]
    if isinstance(tool_input.get("command"), str):
        return " ".join(tool_input["command"].split()[:2])
    return ""


def tool_calls(session: Session) -> list[ToolCall]:
    """Every tool call in the session, in call order, joined to its result."""
    results: dict[str, tuple[dict, dict]] = {}
    for record in session.records:
        if record.get("type") == "user":
            for block in content_blocks(record, "tool_result"):
                results.setdefault(str(block.get("tool_use_id")), (record, block))
    calls = []
    for use_id, use in tool_uses(session).items():
        record, block = results.get(use_id, ({}, {}))
        denial = record.get("toolDenialKind")
        decision = record.get("permissionDecision")
        source = decision.get("source") if isinstance(decision, dict) else None
        asked = str(source).startswith("user") or denial == "user-rejected"
        calls.append(
            ToolCall(
                tool=name(use.get("name")),
                target=call_target(use.get("input")),
                failed=bool(block.get("is_error")) and denial is None,
                denial=name(denial) if denial is not None else None,
                prompted=asked and use.get("name") not in ASKING_TOOLS,
            )
        )
    return calls


INTERRUPT_MARKER = "[Request interrupted by user"

# Messages the harness writes in the user's voice: shell passthrough and its
# output, local slash commands such as /clear, background-task notices. A
# skill invocation opens with <command-message> and is a real turn.
_HARNESS_WRAPPED = re.compile(
    r"<(?:bash-input|bash-stdout|bash-stderr|command-name|local-command-caveat"
    r"|local-command-stdout|local-command-stderr|system-reminder|task-notification)>"
)


def message_text(record: dict) -> str:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    return "\n".join(str(block.get("text", "")) for block in content_blocks(record, "text"))


def is_interruption(record: dict) -> bool:
    return record.get("type") == "user" and message_text(record).startswith(INTERRUPT_MARKER)


def is_human_turn(record: dict) -> bool:
    if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary"):
        return False
    if record.get("turnOrigin", "human") != "human" or record.get("promptSource") == "system":
        return False
    if "toolUseResult" in record or any(content_blocks(record, "tool_result")):
        return False
    return not is_interruption(record) and not _HARNESS_WRAPPED.match(message_text(record))


class Tally:
    """How often each key occurred, and in how many sessions."""

    def __init__(self) -> None:
        self.counts: Counter = Counter()
        self.key_sessions: Counter = Counter()
        self.sessions = 0

    def add_session(self, keys: list[str]) -> None:
        self.counts.update(keys)
        self.key_sessions.update(set(keys))
        self.sessions += bool(keys)

    def summary(self, by: str) -> dict:
        return {
            "count": sum(self.counts.values()),
            "sessions": self.sessions,
            by: {
                key: {"count": n, "sessions": self.key_sessions[key]}
                for key, n in self.counts.items()
            },
        }


def evidence_bar(session_count: int) -> int:
    return max(EVIDENCE_MIN_SESSIONS, math.ceil(EVIDENCE_MIN_SHARE * session_count))


def context_size(sessions: list[Session]) -> dict:
    by_model: dict[str, list[int]] = defaultdict(list)
    model_sessions: Counter = Counter()
    for session in sessions:
        for call in session.calls:
            by_model[call.model].append(call.context)
        model_sessions.update({call.model for call in session.calls})
    everything = [context for contexts in by_model.values() for context in contexts]
    return {
        "calls": len(everything),
        **spread(everything, 50, 90),
        "session_peak": spread([max(c.context for c in s.calls) for s in sessions], 50, 90),
        "by_model": {
            model: {
                "calls": len(contexts),
                "sessions": model_sessions[model],
                **spread(contexts, 50, 90),
            }
            for model, contexts in by_model.items()
        },
    }


def compactions(sessions: list[Session]) -> dict:
    triggers: Counter = Counter()
    pre_tokens: list[int] = []
    affected = 0
    for session in sessions:
        boundaries = [
            record.get("compactMetadata") or {}
            for record in session.records
            if record.get("type") == "system" and record.get("subtype") == "compact_boundary"
        ]
        affected += bool(boundaries)
        triggers.update(name(metadata.get("trigger")) for metadata in boundaries)
        pre_tokens.extend(m["preTokens"] for m in boundaries if isinstance(m.get("preTokens"), int))
    return {
        "count": sum(triggers.values()),
        "sessions": affected,
        "by_trigger": dict(triggers),
        "pre_tokens": spread(pre_tokens, 50),
    }


def _chars(value: object) -> int:
    """Total characters of a string, or of every string in a list."""
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(len(item) for item in value if isinstance(item, str))
    return 0


def _tool_definition_chars(tools: list) -> int:
    return sum(
        len(str(tool.get("name", "")))
        + len(str(tool.get("description", "")))
        + len(json.dumps(tool.get("schema", {})))
        for tool in tools
        if isinstance(tool, dict)
    )


def always_loaded_components(session: Session) -> dict[str, int]:
    """Character size of each piece of context a session loaded before its first prompt.

    Each is announced once at session start and again only when it changes, so
    the first announcement is the always-loaded cost.
    """

    def first(kind: str, field: str) -> object:
        candidates = (a for a in attachments(session, kind) if a.get("isInitial", True))
        return next((a[field] for a in candidates if a.get(field)), None)

    instructions = first("instructions", "files")
    tools = first("prompt_snapshot", "tools")
    sizes = {
        "skill_listing": _chars(first("skill_listing", "content")),
        "agent_listing": _chars(first("agent_listing_delta", "addedLines")),
        "instructions": sum(
            _chars(item.get("content"))
            for item in (instructions if isinstance(instructions, list) else [])
            if isinstance(item, dict)
        ),
        "mcp_instructions": _chars(first("mcp_instructions_delta", "addedBlocks")),
        "system_prompt": _chars(first("prompt_snapshot", "systemPrompt")),
        "tool_definitions": _tool_definition_chars(tools) if isinstance(tools, list) else 0,
    }
    return {component: size for component, size in sizes.items() if size}


def always_loaded(sessions: list[Session]) -> dict:
    first_calls = [s.calls[0].context for s in sessions if s.began_in_window]
    components: dict[str, list[int]] = defaultdict(list)
    skills_listed: list[int] = []
    invoked: Counter = Counter()
    for session in sessions:
        for component, size in always_loaded_components(session).items():
            components[component].append(size)
        listing = next(attachments(session, "skill_listing"), {})
        if isinstance(listing.get("skillCount"), int):
            skills_listed.append(listing["skillCount"])
        invoked.update(
            str((use.get("input") or {}).get("skill"))
            for use in tool_uses(session).values()
            if use.get("name") == "Skill"
        )
    return {
        "first_call_tokens": {"sessions": len(first_calls), **spread(first_calls, 50, 90)},
        "components_chars": {
            component: {"sessions": len(sizes), **spread(sizes, 50)}
            for component, sizes in components.items()
        },
        "skills_listed": spread(skills_listed, 50),
        # Skill names can describe private work, so only how many is reported.
        "skills_invoked": {"distinct": len(invoked), "invocations": sum(invoked.values())},
    }


def permission_prompts(sessions: list[Session]) -> dict:
    tally = Tally()
    for session in sessions:
        tally.add_session([call.tool for call in tool_calls(session) if call.prompted])
    return tally.summary("by_tool")


_HOOK_SCRIPT = re.compile(r"[\w.-]+\.(?:sh|bash|zsh|py|js|mjs|cjs|ts|rb|pl|php)\b")
_HARNESS_HOOK_LABEL = re.compile(r"(?:command|http|prompt|agent|mcp) hook(?: \d+)?")


def hook_script(command: object) -> str:
    """A printable name for a hook's command: its script, never the command line."""
    if isinstance(command, str):
        if _HARNESS_HOOK_LABEL.fullmatch(command):
            return command
        scripts = _HOOK_SCRIPT.findall(command)
        if scripts:
            return scripts[-1]
    return "(inline command)"


def hook_runs(session: Session) -> Iterator[tuple[str, int]]:
    """(hook, duration in ms) for every timed hook run in the session.

    Stop hooks are read from the per-turn stop summary, which records every
    run; the attachment form covers only some of them, so reading both would
    count those twice.
    """
    for record in session.records:
        if record.get("type") == "system" and record.get("subtype") == "stop_hook_summary":
            for info in record.get("hookInfos") or []:
                if isinstance(info, dict) and isinstance(info.get("durationMs"), int):
                    yield f"Stop {hook_script(info.get('command'))}", info["durationMs"]
    for kind in ("hook_success", "hook_cancelled"):
        for run in attachments(session, kind):
            if run.get("hookEvent") != "Stop" and isinstance(run.get("durationMs"), int):
                yield (
                    f"{name(run.get('hookName'))} {hook_script(run.get('command'))}",
                    run["durationMs"],
                )


def hook_latency(sessions: list[Session]) -> dict:
    durations: dict[str, list[int]] = defaultdict(list)
    hook_sessions: Counter = Counter()
    blocked = Tally()
    for session in sessions:
        seen = set()
        for hook, duration in hook_runs(session):
            durations[hook].append(duration)
            seen.add(hook)
        hook_sessions.update(seen)
        blocked.add_session(
            [name(error.get("hookName")) for error in attachments(session, "hook_blocking_error")]
        )
    return {
        "total": sum(sum(runs) for runs in durations.values()),
        "by_hook": {
            hook: {
                "runs": len(runs),
                "sessions": hook_sessions[hook],
                **spread(runs, 50, 90),
                "total": sum(runs),
            }
            for hook, runs in durations.items()
        },
        "blocking_errors": blocked.summary("by_hook")["by_hook"],
    }


def tool_failures(sessions: list[Session]) -> dict:
    calls: Counter = Counter()
    retried: Counter = Counter()
    failed = Tally()
    for session in sessions:
        session_calls = tool_calls(session)
        calls.update(call.tool for call in session_calls)
        failed.add_session([call.tool for call in session_calls if call.failed])
        # A retry is a failed call followed straight away by the same tool on
        # the same target. Tool alone would count nearly every failed shell
        # command, since most calls are shell commands.
        retried.update(
            call.tool
            for call, following in zip(session_calls, session_calls[1:])
            if call.failed and (following.tool, following.target) == (call.tool, call.target)
        )
    records = [record for session in sessions for record in session.records]
    return {
        "calls": sum(calls.values()),
        "failed": sum(failed.counts.values()),
        "retried": sum(retried.values()),
        "sessions": failed.sessions,
        "by_tool": {
            tool: {
                "calls": n,
                "failed": failed.counts[tool],
                "retried": retried[tool],
                "sessions": failed.key_sessions[tool],
            }
            for tool, n in calls.items()
        },
        "api_errors": sum(bool(r.get("isApiErrorMessage")) for r in records),
        "model_fallbacks": sum(
            r.get("type") == "system" and r.get("subtype") == "model_fallback" for r in records
        ),
    }


def interruptions(sessions: list[Session]) -> dict:
    per_session = [sum(is_interruption(record) for record in s.records) for s in sessions]
    return {"count": sum(per_session), "sessions": sum(bool(n) for n in per_session)}


def denied_tool_calls(sessions: list[Session]) -> dict:
    by_tool = Tally()
    kinds: Counter = Counter()
    for session in sessions:
        denied = [call for call in tool_calls(session) if call.denial]
        by_tool.add_session([call.tool for call in denied])
        kinds.update(call.denial for call in denied)
    return {**by_tool.summary("by_tool"), "by_kind": dict(kinds)}


def measure(projects_dir: Path, window: Window) -> dict:
    sessions = load_sessions(projects_dir, window)
    return {
        "window": window.describe(),
        "sessions": len(sessions),
        "evidence_bar_sessions": evidence_bar(len(sessions)),
        "human_turns": sum(is_human_turn(record) for s in sessions for record in s.records),
        "efficiency": {
            "context_size_per_call": context_size(sessions),
            "compactions": compactions(sessions),
            "always_loaded_context": always_loaded(sessions),
            "permission_prompts": permission_prompts(sessions),
            "hook_latency_ms": hook_latency(sessions),
            "tool_failures": tool_failures(sessions),
        },
        "quality_proxies": {
            "interruptions": interruptions(sessions),
            "denied_tool_calls": denied_tool_calls(sessions),
        },
    }


# A breakdown can run to every MCP tool the user has; the table shows the head
# of it and counts the rest. The JSON form always carries every row.
TABLE_ROWS = 15


def _cell(value: object) -> str:
    if value is None:
        return "–"
    return f"{value:,}" if isinstance(value, int) else str(value)


def _table(headers: list[str], rows: list[list]) -> list[str]:
    if not rows:
        return ["None in the window.", ""]
    lines = ["| " + " | ".join(headers) + " |", "|" + " --- |" * len(headers)]
    lines += ["| " + " | ".join(_cell(cell) for cell in row) + " |" for row in rows[:TABLE_ROWS]]
    if len(rows) > TABLE_ROWS:
        lines.append(f"… and {len(rows) - TABLE_ROWS} more rows.")
    return [*lines, ""]


def _ranked(breakdown: dict, by: str, *columns: str) -> list[list]:
    """A breakdown's rows as [key, *columns], largest `by` first, then by key."""
    ordered = sorted(breakdown.items(), key=lambda item: (-item[1][by], item[0]))
    return [[key, *(entry[column] for column in columns)] for key, entry in ordered]


def render_table(report: dict) -> str:
    window = report["window"]
    efficiency = report["efficiency"]
    context = efficiency["context_size_per_call"]
    compaction = efficiency["compactions"]
    loaded = efficiency["always_loaded_context"]
    prompts = efficiency["permission_prompts"]
    hooks = efficiency["hook_latency_ms"]
    failures = efficiency["tool_failures"]
    interrupted = report["quality_proxies"]["interruptions"]
    denied = report["quality_proxies"]["denied_tool_calls"]
    last_day = date.fromisoformat(window["until"]) - timedelta(days=1)
    peak, first_call = context["session_peak"], loaded["first_call_tokens"]

    lines = [
        "# Usage review signals",
        "",
        f"Window: {window['from']} to {last_day} ({window['days']} days). "
        f"{_cell(report['sessions'])} sessions, {_cell(report['human_turns'])} human turns.",
        f"Evidence bar: a pattern is proposed only when seen in at least "
        f"{report['evidence_bar_sessions']} sessions.",
        "Subagent transcripts are not measured.",
        "",
        "## Efficiency signals",
        "",
        "### Context size per call",
        "",
        "Tokens sent per API call: input, cache read and cache write.",
        "",
        *_table(
            ["Model", "Calls", "Sessions", "p50", "p90", "Max"],
            [
                ["all models", context["calls"], report["sessions"]]
                + [context[key] for key in ("p50", "p90", "max")],
                *_ranked(context["by_model"], "calls", "calls", "sessions", "p50", "p90", "max"),
            ],
        ),
        f"Largest call per session: p50 {_cell(peak['p50'])}, p90 {_cell(peak['p90'])}, "
        f"max {_cell(peak['max'])}.",
        "",
        "### Compactions",
        "",
        f"{_cell(compaction['count'])} in {_cell(compaction['sessions'])} sessions. "
        f"Size before compaction: p50 {_cell(compaction['pre_tokens']['p50'])}, "
        f"max {_cell(compaction['pre_tokens']['max'])} tokens.",
        "",
        *_table(["Trigger", "Count"], sorted(compaction["by_trigger"].items())),
        "### Always-loaded context",
        "",
        f"First call of a session, over the {_cell(first_call['sessions'])} sessions that began "
        f"in the window: p50 {_cell(first_call['p50'])}, p90 {_cell(first_call['p90'])}, "
        f"max {_cell(first_call['max'])} tokens.",
        "",
        *_table(
            ["Component", "Sessions", "p50 chars", "Max chars"],
            _ranked(loaded["components_chars"], "p50", "sessions", "p50", "max"),
        ),
        f"Skills listed per session: p50 {_cell(loaded['skills_listed']['p50'])}, "
        f"max {_cell(loaded['skills_listed']['max'])}. "
        f"Skills invoked: {_cell(loaded['skills_invoked']['distinct'])} distinct, "
        f"{_cell(loaded['skills_invoked']['invocations'])} invocations.",
        "",
        "### Permission prompts",
        "",
        f"{_cell(prompts['count'])} in {_cell(prompts['sessions'])} sessions.",
        "",
        *_table(
            ["Tool", "Prompts", "Sessions"],
            _ranked(prompts["by_tool"], "count", "count", "sessions"),
        ),
        "### Hook latency",
        "",
        f"{_cell(hooks['total'])} ms across every timed run.",
        "",
        *_table(
            ["Hook", "Runs", "Sessions", "p50 ms", "p90 ms", "Max ms", "Total ms"],
            _ranked(hooks["by_hook"], "total", "runs", "sessions", "p50", "p90", "max", "total"),
        ),
        "Hooks that blocked a tool call or a stop:",
        "",
        *_table(
            ["Hook", "Blocks", "Sessions"],
            _ranked(hooks["blocking_errors"], "count", "count", "sessions"),
        ),
        "### Failed or retried tool calls",
        "",
        f"{_cell(failures['failed'])} of {_cell(failures['calls'])} calls failed, in "
        f"{_cell(failures['sessions'])} sessions; {_cell(failures['retried'])} were retried. "
        f"API errors: {_cell(failures['api_errors'])}. "
        f"Model fallbacks: {_cell(failures['model_fallbacks'])}.",
        "",
        *_table(
            ["Tool", "Calls", "Failed", "Retried", "Sessions"],
            [
                row
                for row in _ranked(
                    failures["by_tool"], "failed", "calls", "failed", "retried", "sessions"
                )
                if row[2]
            ],
        ),
        "## Quality proxies",
        "",
        "### Interruptions",
        "",
        f"{_cell(interrupted['count'])} in {_cell(interrupted['sessions'])} sessions.",
        "",
        "### Denied tool calls",
        "",
        f"{_cell(denied['count'])} in {_cell(denied['sessions'])} sessions.",
        "",
        *_table(
            ["Kind", "Count"], sorted(denied["by_kind"].items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        *_table(
            ["Tool", "Denied", "Sessions"], _ranked(denied["by_tool"], "count", "count", "sessions")
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


# A pasted log can make one prompt enormous; the opening is enough to tell a
# correction from a new request.
SAMPLE_TURN_CHARS = 2000
# Whether a turn corrects anything depends on what it answers, and a reply
# ends on its conclusion — so each turn carries the end of the reply before it.
SAMPLE_REPLY_CHARS = 1000


def human_turns(session: Session) -> list[dict]:
    """Each human turn's opening, with the end of the assistant reply it follows."""
    turns = []
    reply = ""
    for record in session.records:
        if record.get("type") == "assistant":
            reply = message_text(record) or reply
        elif is_human_turn(record):
            turns.append(
                {
                    "reply_before": reply[-SAMPLE_REPLY_CHARS:],
                    "prompt": message_text(record)[:SAMPLE_TURN_CHARS],
                }
            )
            reply = ""
    return turns


def write_sample(projects_dir: Path, window: Window, size: int, out: Path) -> str:
    """Write a random sample of sessions' human turns to `out`; return the one-line receipt.

    This is the only place prompt text leaves a transcript, and it goes to a
    file the owner alone can read — never to stdout. The draw is seeded by the
    window, so re-running a review samples the same sessions.
    """
    candidates = [turns for turns in map(human_turns, load_sessions(projects_dir, window)) if turns]
    rng = random.Random(f"{window.start}:{window.until}:{size}")
    chosen = sorted(rng.sample(range(len(candidates)), min(size, len(candidates))))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as handle:
        os.chmod(out, 0o600)
        for index in chosen:
            handle.write(json.dumps({"turns": candidates[index]}) + "\n")
    return f"Sampled {len(chosen)} of {len(candidates)} sessions with human turns."


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Measure the usage-review signals.")
    window_args = argparse.ArgumentParser(add_help=False)
    window_args.add_argument("--until", type=date.fromisoformat, help="first day after the window")
    window_args.add_argument("--days", type=int, default=30)
    window_args.add_argument("--projects-dir", type=Path, default=Path.home() / ".claude/projects")
    commands = parser.add_subparsers(dest="command", required=True)
    measure_cmd = commands.add_parser(
        "measure", parents=[window_args], help="print the aggregate signal table"
    )
    measure_cmd.add_argument("--format", choices=("table", "json"), default="table")
    sample_cmd = commands.add_parser(
        "sample", parents=[window_args], help="write sampled human turns to a private file"
    )
    sample_cmd.add_argument("--size", type=int, default=30)
    sample_cmd.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    until = args.until or datetime.now(timezone.utc).date()
    window = Window(until - timedelta(days=args.days), until)
    if args.command == "sample":
        print(write_sample(args.projects_dir, window, args.size, args.out))
        return 0
    report = measure(args.projects_dir, window)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_table(report), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
