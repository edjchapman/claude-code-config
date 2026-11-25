"""Behavioural tests for skills/ccc-usage-review/signals.py, run against fixture transcripts.

The seam is the script's command line: every test lays down a throwaway
`projects/` tree, runs the script as a subprocess and asserts on what it
prints. Expected numbers are worked out by hand from the fixture.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "ccc-usage-review" / "signals.py"

UNTIL = "2026-11-19"
IN_WINDOW = "2026-11-10T12:00:00.000Z"


class Session:
    """Builds one transcript file, a record per call, in the shapes Claude Code writes."""

    def __init__(self, path):
        self.path = path
        self.records = []
        self._n = 0

    def _id(self, prefix):
        self._n += 1
        return f"{prefix}_{self.path.stem}_{self._n}"

    def _add(self, record, at):
        self.records.append({"sessionId": self.path.stem, "timestamp": at, **record})
        return self

    def call(self, context, model="claude-opus-5-5", at=IN_WINDOW, message_id=None, content=None):
        """One API call whose context was `context` tokens, split across the usage fields."""
        usage = {
            "input_tokens": 10,
            "cache_read_input_tokens": context - 30,
            "cache_creation_input_tokens": 20,
            "output_tokens": 5,
        }
        message = {
            "id": message_id or self._id("msg"),
            "model": model,
            "usage": usage,
            "content": content or [{"type": "text", "text": "ok"}],
        }
        return self._add({"type": "assistant", "message": message}, at)

    def prompt(self, text, at=IN_WINDOW, **fields):
        return self.user(text, at=at, turnOrigin="human", **fields)

    def user(self, content, at=IN_WINDOW, **fields):
        """A user-role record that is not a typed prompt: a tool result, an injected message."""
        return self._add(
            {"type": "user", "message": {"role": "user", "content": content}, **fields}, at
        )

    def tool(self, name, tool_input=None, error=False, at=IN_WINDOW, **result_fields):
        """One tool call and its result."""
        use_id = self._id("toolu")
        use = {"type": "tool_use", "id": use_id, "name": name, "input": tool_input or {}}
        self.call(1000, at=at, content=[use])
        result = {"type": "tool_result", "tool_use_id": use_id, "content": "out", "is_error": error}
        return self.user([result], at=at, **result_fields)

    def compaction(self, pre_tokens, trigger="auto", at=IN_WINDOW):
        metadata = {"trigger": trigger, "preTokens": pre_tokens, "postTokens": 9000}
        record = {"type": "system", "subtype": "compact_boundary", "compactMetadata": metadata}
        return self._add(record, at)

    def attachment(self, kind, at=IN_WINDOW, **fields):
        return self._add({"type": "attachment", "attachment": {"type": kind, **fields}}, at)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(json.dumps(r) + "\n" for r in self.records))


class SignalsCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.projects = pathlib.Path(self._tmp.name) / "projects"
        self.projects.mkdir()
        self._sessions = []

    def tearDown(self):
        self._tmp.cleanup()

    def session(self, name="s1", project="-Users-someone-proj"):
        session = Session(self.projects / project / f"{name}.jsonl")
        self._sessions.append(session)
        return session

    def run_script(self, *args):
        for session in self._sessions:
            session.save()
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--projects-dir", str(self.projects)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def measure(self, *args):
        return json.loads(self.run_script("measure", "--until", UNTIL, "--format", "json", *args))


class ContextSizeTest(SignalsCase):
    def test_context_size_is_the_sum_of_a_calls_input_token_fields(self):
        self.session().call(1000).call(2000).call(3000).call(4000).call(50000)

        context = self.measure()["efficiency"]["context_size_per_call"]

        self.assertEqual(context["calls"], 5)
        self.assertEqual(context["p50"], 3000)
        self.assertEqual(context["p90"], 50000)
        self.assertEqual(context["max"], 50000)

    def test_a_call_streamed_as_several_records_counts_once(self):
        session = self.session()
        for _ in range(3):
            session.call(1000, message_id="msg_streamed")
        session.call(9000)

        context = self.measure()["efficiency"]["context_size_per_call"]

        self.assertEqual(context["calls"], 2)
        self.assertEqual(context["p50"], 1000)

    def test_a_record_with_no_usage_is_not_a_call(self):
        session = self.session().call(1000)
        session.records.append(
            {
                "type": "assistant",
                "timestamp": IN_WINDOW,
                "isApiErrorMessage": True,
                "message": {"id": "err", "model": "<synthetic>", "usage": {"input_tokens": 0}},
            }
        )

        self.assertEqual(self.measure()["efficiency"]["context_size_per_call"]["calls"], 1)

    def test_only_calls_inside_the_window_are_measured(self):
        # The window is the 30 whole UTC days before --until: 20 Oct 00:00 to 19 Nov 00:00.
        session = self.session()
        session.call(111, at="2026-10-19T23:59:59.999Z")
        session.call(2000, at="2026-10-20T00:00:00.000Z")
        session.call(3000, at="2026-11-18T23:59:59.999Z")
        session.call(999, at="2026-11-19T00:00:00.000Z")

        report = self.measure()

        self.assertEqual(
            report["window"], {"from": "2026-10-20", "until": "2026-11-19", "days": 30}
        )
        context = report["efficiency"]["context_size_per_call"]
        self.assertEqual((context["calls"], context["p50"], context["max"]), (2, 2000, 3000))

    def test_days_narrows_the_window(self):
        session = self.session()
        session.call(2000, at="2026-11-11T23:59:59.000Z")
        session.call(3000, at="2026-11-12T00:00:00.000Z")

        context = self.measure("--days", "7")["efficiency"]["context_size_per_call"]

        self.assertEqual((context["calls"], context["max"]), (1, 3000))

    def test_the_window_ends_at_the_start_of_today_by_default(self):
        now = datetime.now(timezone.utc)
        self.session().call(4000, at=now.strftime("%Y-%m-%dT%H:%M:%S.000Z"))

        report = json.loads(self.run_script("measure", "--format", "json"))

        self.assertEqual(report["window"]["until"], now.strftime("%Y-%m-%d"))
        self.assertEqual(report["efficiency"]["context_size_per_call"]["calls"], 0)


class SessionsTest(SignalsCase):
    def test_a_session_counts_when_it_has_a_call_in_the_window(self):
        self.session("a").call(1000)
        self.session("b").call(1000, at="2026-01-01T00:00:00.000Z")
        self.session("c").prompt("no call was ever made")

        self.assertEqual(self.measure()["sessions"], 1)

    def test_subagent_transcripts_are_not_sessions(self):
        self.session("a").call(1000)
        subagent = Session(
            self.projects / "-Users-someone-proj" / "a" / "subagents" / "agent-1.jsonl"
        )
        self._sessions.append(subagent.call(99999))

        report = self.measure()

        self.assertEqual(report["sessions"], 1)
        self.assertEqual(report["efficiency"]["context_size_per_call"]["max"], 1000)

    def test_context_size_is_broken_down_by_model(self):
        self.session("a").call(1000).call(3000).call(8000, model="claude-fable-5-2")
        self.session("b").call(6000, model="claude-fable-5-2")

        by_model = self.measure()["efficiency"]["context_size_per_call"]["by_model"]

        self.assertEqual(
            by_model,
            {
                "claude-opus-5-5": {
                    "calls": 2,
                    "sessions": 1,
                    "p50": 1000,
                    "p90": 3000,
                    "max": 3000,
                },
                "claude-fable-5-2": {
                    "calls": 2,
                    "sessions": 2,
                    "p50": 6000,
                    "p90": 8000,
                    "max": 8000,
                },
            },
        )

    def test_session_peak_is_the_largest_call_of_each_session(self):
        self.session("a").call(1000).call(5000)
        self.session("b").call(2000)
        self.session("c").call(9000).call(300)

        peak = self.measure()["efficiency"]["context_size_per_call"]["session_peak"]

        self.assertEqual(peak, {"p50": 5000, "p90": 9000, "max": 9000})

    def test_the_evidence_bar_is_ten_sessions_when_the_window_is_small(self):
        self.session("a").call(1000)

        self.assertEqual(self.measure()["evidence_bar_sessions"], 10)

    def test_the_evidence_bar_is_five_percent_of_a_large_window(self):
        for n in range(221):
            self.session(f"s{n}").call(1000)

        report = self.measure()

        # 5% of 221 sessions is 11.05; a pattern needs to reach it, so 12.
        self.assertEqual((report["sessions"], report["evidence_bar_sessions"]), (221, 12))

    def test_human_turns_are_the_prompts_a_person_sent(self):
        session = self.session().call(1000)
        session.prompt("first").prompt("second")
        session.tool("Bash")
        session.user("<task-notification>done</task-notification>", turnOrigin="task_notification")
        session.user("injected context", isMeta=True)
        session.user("summary of earlier turns", isCompactSummary=True)

        self.assertEqual(self.measure()["human_turns"], 2)

    def test_a_skill_invocation_is_a_human_turn_but_harness_wrapped_messages_are_not(self):
        session = self.session().call(1000)
        session.prompt(
            "<command-message>commit</command-message>\n<command-name>/commit</command-name>"
        )
        session.user("<command-name>/clear</command-name>")
        session.user("<local-command-stdout>cleared</local-command-stdout>")
        session.user("<bash-input>ls</bash-input>")
        session.prompt("<bash-stdout>README.md</bash-stdout>")
        session.user("<task-notification>agent finished</task-notification>", promptSource="system")
        session.prompt("scheduled wake-up", promptSource="system")

        self.assertEqual(self.measure()["human_turns"], 1)


class CompactionTest(SignalsCase):
    def test_compactions_are_counted_by_trigger_with_their_pre_compaction_size(self):
        self.session("a").call(1000).compaction(400000).compaction(500000)
        self.session("b").call(1000).compaction(120000, trigger="manual")
        self.session("c").call(1000)

        self.assertEqual(
            self.measure()["efficiency"]["compactions"],
            {
                "count": 3,
                "sessions": 2,
                "by_trigger": {"auto": 2, "manual": 1},
                "pre_tokens": {"p50": 400000, "max": 500000},
            },
        )


class AlwaysLoadedTest(SignalsCase):
    def test_the_first_call_of_a_session_measures_what_is_always_loaded(self):
        self.session("a").call(30000).call(90000)
        self.session("b").call(40000).call(41000)
        self.session("c").call(20000)

        first = self.measure()["efficiency"]["always_loaded_context"]["first_call_tokens"]

        self.assertEqual(first, {"sessions": 3, "p50": 30000, "p90": 40000, "max": 40000})

    def test_a_session_that_began_before_the_window_has_no_first_call_in_it(self):
        self.session("a").call(30000)
        self.session("old").call(25000, at="2026-10-01T00:00:00.000Z").call(70000)

        report = self.measure()

        self.assertEqual(report["sessions"], 2)
        first = report["efficiency"]["always_loaded_context"]["first_call_tokens"]
        self.assertEqual(first, {"sessions": 1, "p50": 30000, "p90": 30000, "max": 30000})

    def test_always_loaded_components_are_sized_in_characters(self):
        a = self.session("a").call(1000)
        a.attachment("skill_listing", content="x" * 1200, skillCount=12, isInitial=True)
        a.attachment("skill_listing", content="x" * 5000, skillCount=13, isInitial=False)
        a.attachment("agent_listing_delta", addedLines=["a" * 100, "b" * 50], isInitial=True)
        a.attachment("instructions", files=[{"content": "c" * 700}, {"content": "d" * 300}])
        a.attachment("mcp_instructions_delta", addedBlocks=["m" * 400])
        a.attachment(
            "prompt_snapshot",
            systemPrompt=["s" * 2000, "t" * 500],
            tools=[{"name": "Bash", "description": "d" * 96, "schema": {}}],
        )
        b = self.session("b").call(1000)
        b.attachment("skill_listing", content="x" * 800, skillCount=8, isInitial=True)

        loaded = self.measure()["efficiency"]["always_loaded_context"]

        self.assertEqual(
            loaded["components_chars"],
            {
                "skill_listing": {"sessions": 2, "p50": 800, "max": 1200},
                "agent_listing": {"sessions": 1, "p50": 150, "max": 150},
                "instructions": {"sessions": 1, "p50": 1000, "max": 1000},
                "mcp_instructions": {"sessions": 1, "p50": 400, "max": 400},
                "system_prompt": {"sessions": 1, "p50": 2500, "max": 2500},
                # name (4) + description (96) + schema serialised as "{}" (2)
                "tool_definitions": {"sessions": 1, "p50": 102, "max": 102},
            },
        )
        self.assertEqual(loaded["skills_listed"], {"p50": 8, "max": 12})

    def test_skills_are_counted_as_invoked_without_being_named(self):
        session = self.session().call(1000)
        session.tool("Skill", {"skill": "commit"}).tool("Skill", {"skill": "commit"})
        session.tool("Skill", {"skill": "private-client-skill"})

        loaded = self.measure()["efficiency"]["always_loaded_context"]

        self.assertEqual(loaded["skills_invoked"], {"distinct": 2, "invocations": 3})


USER_ALLOWED = {"decision": "accept", "source": "user_temporary", "grantScope": "once"}
RULE_ALLOWED = {"decision": "accept", "source": "config", "reasonType": "rule"}


class PermissionPromptTest(SignalsCase):
    def test_a_prompt_is_a_tool_call_the_user_had_to_decide(self):
        a = self.session("a")
        a.tool("Bash", permissionDecision=USER_ALLOWED)
        a.tool("Bash", permissionDecision=RULE_ALLOWED)
        a.tool(
            "Edit",
            error=True,
            toolDenialKind="user-rejected",
            permissionDecision={"decision": "reject", "source": "user_reject"},
        )
        b = self.session("b")
        b.tool("Bash", permissionDecision=USER_ALLOWED)
        b.tool("Write", error=True, toolDenialKind="user-rejected")
        # Answering a question or approving a plan is the tool's purpose, not a prompt about it.
        b.tool("AskUserQuestion", permissionDecision=USER_ALLOWED)
        b.tool("ExitPlanMode", permissionDecision=USER_ALLOWED)

        self.assertEqual(
            self.measure()["efficiency"]["permission_prompts"],
            {
                "count": 4,
                "sessions": 2,
                "by_tool": {
                    "Bash": {"count": 2, "sessions": 2},
                    "Edit": {"count": 1, "sessions": 1},
                    "Write": {"count": 1, "sessions": 1},
                },
            },
        )


class HookLatencyTest(SignalsCase):
    FORMAT = "${CLAUDE_PLUGIN_ROOT:-$(readlink ~/.claude/agents)}/scripts/hooks/format-on-edit.sh"

    def edit_hook(self, session, duration):
        session.attachment(
            "hook_success",
            hookEvent="PostToolUse",
            hookName="PostToolUse:Edit",
            command=self.FORMAT,
            durationMs=duration,
        )

    def test_hook_runs_are_timed_per_hook(self):
        a = self.session("a").call(1000)
        for duration in (100, 300, 200):
            self.edit_hook(a, duration)
        self.edit_hook(self.session("b").call(1000), 400)

        latency = self.measure()["efficiency"]["hook_latency_ms"]

        self.assertEqual(
            latency["by_hook"],
            {
                "PostToolUse:Edit format-on-edit.sh": {
                    "runs": 4,
                    "sessions": 2,
                    "p50": 200,
                    "p90": 400,
                    "max": 400,
                    "total": 1000,
                }
            },
        )
        self.assertEqual(latency["total"], 1000)

    def test_stop_hooks_are_timed_once_from_the_stop_summary(self):
        session = self.session().call(1000)
        session._add(
            {
                "type": "system",
                "subtype": "stop_hook_summary",
                "hookInfos": [
                    {
                        "command": "/Users/someone/cfg/scripts/hooks/stop-check.sh",
                        "durationMs": 1500,
                    },
                    {"command": "command hook 2", "durationMs": 20},
                ],
            },
            IN_WINDOW,
        )
        # The same Stop run is sometimes also written as an attachment.
        session.attachment(
            "hook_success",
            hookEvent="Stop",
            hookName="Stop",
            command="stop-check.sh",
            durationMs=1500,
        )

        by_hook = self.measure()["efficiency"]["hook_latency_ms"]["by_hook"]

        self.assertEqual(sorted(by_hook), ["Stop command hook 2", "Stop stop-check.sh"])
        self.assertEqual(
            (by_hook["Stop stop-check.sh"]["runs"], by_hook["Stop stop-check.sh"]["total"]),
            (1, 1500),
        )

    def test_an_inline_hook_command_is_never_printed(self):
        self.session().call(1000).attachment(
            "hook_success",
            hookEvent="PreToolUse",
            hookName="PreToolUse:Bash",
            command="echo hunter2 >> /Users/someone/notes.txt",
            durationMs=5,
        )

        by_hook = self.measure()["efficiency"]["hook_latency_ms"]["by_hook"]

        self.assertEqual(list(by_hook), ["PreToolUse:Bash (inline command)"])

    def test_hooks_that_blocked_are_counted(self):
        session = self.session().call(1000)
        session.attachment(
            "hook_blocking_error", hookEvent="PostToolUse", hookName="PostToolUse:Write"
        )
        session.attachment(
            "hook_blocking_error", hookEvent="PostToolUse", hookName="PostToolUse:Write"
        )

        blocked = self.measure()["efficiency"]["hook_latency_ms"]["blocking_errors"]

        self.assertEqual(blocked, {"PostToolUse:Write": {"count": 2, "sessions": 1}})


class ToolFailureTest(SignalsCase):
    def test_failed_tool_calls_are_counted_per_tool(self):
        self.session("a").tool("Bash", error=True).tool("Bash").tool("Read").tool(
            "Edit", error=True
        )
        self.session("b").tool("Bash", error=True)

        failures = self.measure()["efficiency"]["tool_failures"]

        self.assertEqual((failures["calls"], failures["failed"], failures["sessions"]), (5, 3, 2))
        self.assertEqual(
            failures["by_tool"],
            {
                "Bash": {"calls": 3, "failed": 2, "retried": 1, "sessions": 2},
                "Edit": {"calls": 1, "failed": 1, "retried": 0, "sessions": 1},
                "Read": {"calls": 1, "failed": 0, "retried": 0, "sessions": 0},
            },
        )

    def test_a_retry_is_a_failed_call_followed_by_the_same_tool(self):
        self.session().tool("Bash", error=True).tool("Read").tool("Bash", error=True).tool("Bash")

        self.assertEqual(self.measure()["efficiency"]["tool_failures"]["retried"], 1)

    def test_a_shell_retry_runs_the_same_command_again(self):
        session = self.session()
        session.tool("Bash", {"command": "git push origin main"}, error=True)
        session.tool("Bash", {"command": "git push --force-with-lease"})
        session.tool("Bash", {"command": "make check"}, error=True)
        session.tool("Bash", {"command": "git status"})

        self.assertEqual(self.measure()["efficiency"]["tool_failures"]["retried"], 1)

    def test_a_file_tool_retry_targets_the_same_file(self):
        session = self.session()
        session.tool("Edit", {"file_path": "/repo/a.py"}, error=True)
        session.tool("Edit", {"file_path": "/repo/a.py"})
        session.tool("Edit", {"file_path": "/repo/b.py"}, error=True)
        session.tool("Edit", {"file_path": "/repo/c.py"})

        self.assertEqual(self.measure()["efficiency"]["tool_failures"]["retried"], 1)

    def test_a_denied_call_is_not_a_failed_call(self):
        self.session().tool("Bash", error=True, toolDenialKind="permission-rule")

        failures = self.measure()["efficiency"]["tool_failures"]

        self.assertEqual((failures["calls"], failures["failed"]), (1, 0))

    def test_api_errors_and_model_fallbacks_are_counted(self):
        session = self.session().call(1000)
        session._add(
            {"type": "assistant", "isApiErrorMessage": True, "message": {"id": "e1"}}, IN_WINDOW
        )
        session._add({"type": "system", "subtype": "model_fallback"}, IN_WINDOW)

        failures = self.measure()["efficiency"]["tool_failures"]

        self.assertEqual((failures["api_errors"], failures["model_fallbacks"]), (1, 1))


class QualityProxyTest(SignalsCase):
    def test_interruptions_are_the_users_interrupt_markers(self):
        a = self.session("a").call(1000).prompt("carry on")
        a.prompt("[Request interrupted by user]")
        a.user([{"type": "text", "text": "[Request interrupted by user for tool use]"}])
        self.session("b").call(1000)

        report = self.measure()

        self.assertEqual(report["quality_proxies"]["interruptions"], {"count": 2, "sessions": 1})
        self.assertEqual(report["human_turns"], 1)

    def test_denied_tool_calls_are_counted_by_kind_and_tool(self):
        a = self.session("a")
        a.tool("Bash", error=True, toolDenialKind="automode-blocked")
        a.tool("Bash", error=True, toolDenialKind="permission-rule")
        b = self.session("b")
        b.tool("Edit", error=True, toolDenialKind="user-rejected")
        b.tool("Bash")

        self.assertEqual(
            self.measure()["quality_proxies"]["denied_tool_calls"],
            {
                "count": 3,
                "sessions": 2,
                "by_kind": {"automode-blocked": 1, "permission-rule": 1, "user-rejected": 1},
                "by_tool": {
                    "Bash": {"count": 2, "sessions": 1},
                    "Edit": {"count": 1, "sessions": 1},
                },
            },
        )


class AggregatesOnlyTest(SignalsCase):
    """Everything a transcript says is planted with a canary; none may be printed."""

    CANARIES = ("zebra", "hunter2", "secret-client", "quokka", "private-skill", "/Users")
    HOME = "/Users/someone/secret-client"

    def setUp(self):
        super().setUp()
        session = self.session("sess-quokka", project="-Users-someone-secret-client")
        session.prompt("please zebra the thing in " + self.HOME)
        session.call(1000, model=self.HOME + "/model")
        session.tool(self.HOME + "/tool", {"command": f"cat {self.HOME}/hunter2"})
        session.tool("Skill", {"skill": "private-skill"})
        session.tool(
            "Bash",
            {"command": "echo hunter2"},
            error=True,
            toolDenialKind="zebra said no",
            permissionDecision={"decision": "reject", "source": "user_reject"},
        )
        session.tool("Read", {"file_path": self.HOME + "/quokka.md"}, error=True)
        session.compaction(50000, trigger="zebra asked for it")
        session.attachment(
            "hook_success",
            hookEvent="PreToolUse",
            hookName="PreToolUse:Bash",
            command=f"bash {self.HOME}/hooks/lint.sh hunter2",
            durationMs=40,
        )
        session.attachment(
            "hook_success",
            hookEvent="PreToolUse",
            hookName=self.HOME,
            command="echo quokka",
            durationMs=1,
        )
        session.attachment("hook_blocking_error", hookName=self.HOME, blockingError="zebra")
        session.attachment(
            "skill_listing", content="private-skill: for secret-client", skillCount=1
        )
        session.attachment(
            "instructions", files=[{"path": self.HOME + "/CLAUDE.md", "content": "quokka"}]
        )
        for record in session.records:
            record.update(cwd=self.HOME, gitBranch="quokka-feature", slug="zebra-session")

    def assert_aggregates_only(self, output):
        for canary in self.CANARIES:
            self.assertNotIn(canary, output)

    def test_json_output_names_no_prompt_path_or_project(self):
        output = self.run_script("measure", "--until", UNTIL, "--format", "json")

        self.assert_aggregates_only(output)
        report = json.loads(output)
        self.assertEqual((report["sessions"], report["human_turns"]), (1, 1))
        self.assertIn("PreToolUse:Bash lint.sh", report["efficiency"]["hook_latency_ms"]["by_hook"])

    def test_table_output_names_no_prompt_path_or_project(self):
        output = self.run_script("measure", "--until", UNTIL)

        self.assert_aggregates_only(output)
        self.assertIn("PreToolUse:Bash lint.sh", output)


class RepeatabilityTest(SignalsCase):
    def test_two_runs_over_the_same_window_print_the_same_output(self):
        for n in range(6):
            session = self.session(f"s{n}", project=f"-proj-{n % 3}")
            session.call(1000 * (n + 1), model=("claude-opus-5-5", "claude-fable-5-2")[n % 2])
            session.tool(("Bash", "Edit", "Read")[n % 3], error=n % 2 == 0).compaction(90000 + n)

        for fmt in ("json", "table"):
            first = self.run_script("measure", "--until", UNTIL, "--format", fmt)
            second = self.run_script("measure", "--until", UNTIL, "--format", fmt)
            self.assertEqual(first, second)


class TableTest(SignalsCase):
    def test_the_table_has_a_section_for_every_signal(self):
        self.session().call(1000)

        output = self.run_script("measure", "--until", UNTIL)

        for heading in (
            "Context size per call",
            "Compactions",
            "Always-loaded context",
            "Permission prompts",
            "Hook latency",
            "Failed or retried tool calls",
            "Interruptions",
            "Denied tool calls",
        ):
            self.assertIn(f"### {heading}", output)

    def test_the_table_states_the_window_and_the_evidence_bar(self):
        self.session("a").call(1000).prompt("one").prompt("two")
        self.session("b").call(1000)

        output = self.run_script("measure", "--until", UNTIL)

        self.assertIn("2026-10-20 to 2026-11-18 (30 days)", output)
        self.assertIn("2 sessions, 2 human turns", output)
        self.assertIn("at least 10 sessions", output)

    def test_table_rows_carry_the_measured_numbers(self):
        self.session("a").call(1000).call(3000).tool("Bash", error=True)
        self.session("b").call(250000, model="claude-fable-5-2")

        output = self.run_script("measure", "--until", UNTIL)

        self.assertIn("| claude-fable-5-2 | 1 | 1 | 250,000 | 250,000 | 250,000 |", output)
        self.assertIn("| Bash | 1 | 1 | 0 | 1 |", output)


class SampleTest(SignalsCase):
    def setUp(self):
        super().setUp()
        self.out = pathlib.Path(self._tmp.name) / "review" / "sample.jsonl"
        for n in range(5):
            self.session(f"s{n}").call(1000).prompt(f"prompt {n}a").tool("Bash").prompt(
                f"prompt {n}b"
            )
        self.session("silent").call(1000)

    def sample(self, *args):
        return self.run_script("sample", "--until", UNTIL, "--out", str(self.out), *args)

    def sampled(self):
        return [json.loads(line) for line in self.out.read_text().splitlines()]

    def test_sample_writes_human_turns_to_a_file_and_prints_only_a_count(self):
        output = self.sample("--size", "2")

        self.assertEqual(output, "Sampled 2 of 5 sessions with human turns.\n")
        sessions = self.sampled()
        self.assertEqual(len(sessions), 2)
        for session in sessions:
            first, second = (turn["prompt"] for turn in session["turns"])
            self.assertRegex(first, r"^prompt \da$")
            self.assertEqual(second, first[:-1] + "b")

    def test_each_turn_carries_the_end_of_the_reply_it_answers(self):
        # Whether a turn is a correction depends on what it is replying to.
        session = self.session("replied").prompt("build the thing")
        session.call(1000, content=[{"type": "text", "text": "x" * 5000 + " and it is done."}])
        session.tool("Bash").prompt("no, I meant the other thing")

        self.sample("--size", "100")

        (turns,) = (
            s["turns"] for s in self.sampled() if s["turns"][0]["prompt"] == "build the thing"
        )
        self.assertEqual(turns[0]["reply_before"], "")
        self.assertEqual(len(turns[1]["reply_before"]), 1000)
        self.assertTrue(turns[1]["reply_before"].endswith(" and it is done."))

    def test_a_small_window_is_sampled_whole(self):
        self.assertEqual(self.sample(), "Sampled 5 of 5 sessions with human turns.\n")

    def test_the_same_window_draws_the_same_sample(self):
        self.sample("--size", "2")
        first = self.out.read_text()
        self.sample("--size", "2")

        self.assertEqual(self.out.read_text(), first)

    def test_the_sample_is_readable_only_by_its_owner(self):
        self.sample()

        self.assertEqual(self.out.stat().st_mode & 0o777, 0o600)

    def test_a_long_turn_is_cut_short(self):
        self.session("long").call(1000).prompt("x" * 50000)

        self.sample("--size", "100")

        prompts = [turn["prompt"] for s in self.sampled() for turn in s["turns"]]
        self.assertEqual(max(len(prompt) for prompt in prompts), 2000)


if __name__ == "__main__":
    unittest.main()
