---
name: usage-review
description: Measure your Claude Code session history for where your config costs output quality or efficiency, and write a local report of ranked proposals.
argument-hint: "[--days <n>] [--until <YYYY-MM-DD>]"
disable-model-invocation: true
---

Run a **usage review**: measure this machine's session history across every project, then write a dated report of ranked **proposals** — one suggested config change each, carrying the evidence for it.

The review is **report-only**. Its single output is one file under `~/.claude/usage-review/`; every config file, branch and pull request stays as it was.

## Aggregates only

The evidence is private: the transcripts span every project on the machine. Everything you write — the report and your reply — is built from **aggregates**: the counts, totals, and tool, hook and model names that `signals.py` prints. `signals.py` is the only reader of the transcripts, and what it prints is the whole vocabulary of the report. Describe a pattern by its row in the table ("the slowest Stop hook", "Bash calls denied by a permission rule"), which is always enough to state a proposal.

## Steps

1. **Measure.** Run `python3 "${CLAUDE_SKILL_DIR}/signals.py" measure $ARGUMENTS`. It prints the signal table for the window (30 days ending yesterday unless the arguments say otherwise). If the table shows zero sessions, say so and stop.

2. **Count corrections.** Run `python3 "${CLAUDE_SKILL_DIR}/signals.py" sample --out ~/.claude/usage-review/corrections-sample.jsonl $ARGUMENTS`. It writes up to 30 randomly drawn sessions, one per line, to a file only the user can read; each human turn is a `prompt` with `reply_before`, the end of the reply it answers. Dispatch a subagent to read that file and return two numbers and nothing else: sessions read, and sessions with at least one **correction** — a prompt that redirects work its `reply_before` got wrong (a rejection, a restated instruction, "no, I meant…"), as distinct from a new request or a refinement of work that was right. Then delete the file. The step is done when you hold the two numbers and the file is gone.

3. **Collect patterns.** Go through every section of the table, and the corrections count. A **pattern** is a figure showing a cost that a config change could reduce. For each one record its **signal**, its **baseline** (the figure itself, over the window), and the number of sessions behind it. The step is done when every section has been either mined or judged clean.

4. **Turn patterns into proposals.** A proposal is exactly one change to a config — a settings key, a permission rule, a hook, a skill, an instruction file, an enabled plugin or MCP server — that names the signal it expects to move. Apply these rules to every pattern:

   - **Evidence bar.** The table states the bar. A pattern seen in fewer sessions than that is **listed, not proposed**.
   - **Docs.** A proposal that sets a settings key, wires a hook event or uses a frontmatter field cites the current Claude Code reference page that confirms it (fetch it from `https://code.claude.com/docs/`). One you cannot confirm is listed as unconfirmed.
   - **Ranking.** Order proposals by estimated effect on their signal, weighted by the share of the window's sessions affected. A tie goes to the smaller change.

5. **Write the report** to `~/.claude/usage-review/<today's date, YYYY-MM-DD>.md`, in the shape below. A second run on the same day replaces the file.

6. **Reply** with the ranked proposals and the report's path.

## Signals

**Efficiency signals** measure cost directly; **quality proxies** stand in for output quality, which session history does not record.

| Signal                       | Kind       | What a config can change                                                |
| ---------------------------- | ---------- | ----------------------------------------------------------------------- |
| Context size per call        | Efficiency | When compaction fires; what gets loaded mid-session                     |
| Compaction frequency         | Efficiency | The compaction window, per model                                        |
| Always-loaded context        | Efficiency | Skill and agent listings, instruction files, enabled plugins, MCP tools |
| Permission prompts           | Efficiency | Allow rules for what is approved every time                             |
| Hook latency                 | Efficiency | A slow hook's work, its matcher, or whether it runs at all              |
| Failed or retried tool calls | Efficiency | An instruction or hook that prevents a recurring failure                |
| Interruptions                | Proxy      | Behaviour the user keeps stopping                                       |
| Corrections                  | Proxy      | Instructions that are missing or being overridden                       |
| Denied tool calls            | Proxy      | Rules that block wanted work, or work that should not be attempted      |

## Report shape

```markdown
# Usage review — <date>

<the signal table, verbatim>

## Corrections

<n> of <m> sampled sessions contained a correction.

## Proposals

### 1. <the change, in one line>

- **Change:** <what to set, add or remove, and in which config file>
- **Signal:** <one signal from the table above>
- **Baseline:** <the figure from the signal table>
- **Sessions:** <sessions behind the pattern> of <sessions in the window>
- **Expected effect:** <which way the signal should move, and roughly how far>
- **Docs:** <reference page URL, when the change sets a key, event or frontmatter field>

## Listed, not proposed

- <pattern> — <signal>, <baseline>, <n> sessions (<below the evidence bar | unconfirmed in the docs>)
```
