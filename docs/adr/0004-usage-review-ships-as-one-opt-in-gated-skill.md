# ADR-0004: Usage review ships as one adaptive skill, gated by a per-repo opt-in

**Status:** Accepted — 2026-11-19

## Context

This config was improved several times by analysing the maintainer's own session
transcripts — the `autoCompactWindow` and per-model effort entries in
`docs/architecture.md` both came from a 30-day read. Each analysis was ad hoc:
only its conclusion was committed, never the method, so none was repeatable and no
later run could tell whether a change had worked.

Making it repeatable produced two loops (`CONTEXT.md`): a **usage review** over
local session history, and an **upstream watch** over Claude Code's releases. Both
end in **proposals** that become pull requests the repo's owner merges.

Three facts constrain the usage review:

- **Its evidence is private and local.** Transcripts live under
  `~/.claude/projects/` and span every project on the machine, including
  non-public work. A cloud routine cannot read them.
- **This repo is public, and it is a plugin.** Anything under `skills/` or wired in
  `hooks/hooks.json` reaches every consumer in both install modes, and anything
  written into a PR here is published.
- **The pull-request flow is repo-specific.** Which commands validate a change,
  which paths are off-limits, and whether evidence should come from one project or
  all of them differ per repo and cannot be guessed.

The measurement is useful to any consumer. The pull-request flow is useful only
where someone owns the repo holding the config — and harmful where they do not: a
consumer running the skill from a team repository would otherwise open PRs
against it, built from their usage everywhere.

## Decision

**The usage review ships as a single user-only skill that adapts to where it
runs.** In any repo it measures and writes a local report. It opens pull requests
only in an **opted-in repo** — one that commits a marker file, `.claude/usage-review`.

The marker does three jobs: it turns on pull-request mode, it turns on the
session-start reminder, and it declares what the skill cannot infer — the repo's
validation commands, its off-limits paths, and whether evidence rests on that
repo's sessions (the default) or every project's (a global config, as here).

Guardrails live in the skill and are **not overridable by the marker**: only
aggregates leave the machine; the best few proposals of a run become PRs, one
change each; the skill confirms once before pushing; it never merges; and it does
not open PRs against the repo's safety net or its own guardrails.

Pull requests are the only record of a proposal. Each carries a label and a fixed
body block naming its signal and baseline; open means skip, closed means rejected,
merged means judge it after a full window. There is no ledger file.

Alternatives rejected:

- **Two layers** — a shipped measure-and-report skill, with the pull-request flow
  kept maintainer-only under `.claude/skills/`. Simpler to ship and impossible for
  a consumer to misuse, but it leaves every other config owner to rebuild the half
  that makes the loop self-improving, and splits one loop across two primitives
  that must agree on the report's shape.
- **Maintainer-only** — nothing shipped. Rejected because the measurement is
  generally useful and, as a user-only skill, costs consumers no always-loaded
  context.
- **Pull requests whenever the target file is tracked in the current repo**, with
  no opt-in. Rejected: it publishes into repos whose owners never asked.
- **A committed ledger** of proposals. Rejected: it duplicates state GitHub already
  maintains as the owner merges or closes, and it conflicts across the parallel
  branches a run opens.

The upstream watch is not covered by this decision; it stays maintainer-only.

## Consequences

A shipped skill now contains machinery — branching, pushing, PR bodies, verdict
comments — that most consumers will never run, and that must stay correct for repos
this one has never seen. The marker's format becomes a public interface: once
another repo commits one, changing it is a breaking change.

The opt-in is the only thing standing between a consumer's private usage and a
repository's pull requests, so the aggregates-only rule has to hold by
construction (PR bodies quote the signal script's output and nothing else), not by
the model's judgement at write time.

The reminder hook is wired for every consumer and exits on a file check where no
marker exists — the pattern the stop-check hook already uses. That is a small
always-on cost accepted in a config whose purpose is to find such costs.

Because pull requests are the record, relabelling or deleting one loses a
proposal's history, and a repo that squashes or rewrites PR bodies breaks verdicts.
The record is also only as private as the repo: in a public repo, baselines and
verdicts are published aggregates.

Verdicts rest on signals that move for reasons unrelated to the change under
judgement — a switch of daily model moves most of them. Such windows are marked
inconclusive, so some proposals will never receive a clear verdict.
