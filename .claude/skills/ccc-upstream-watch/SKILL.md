---
name: ccc-upstream-watch
description: Review Claude Code's releases since the last run for what this config should adopt and what they have made stale, and open up to three proposal pull requests. Use when the weekly upstream-watch routine fires, or when asked to run the upstream watch.
---

Run an **upstream watch**: read what Claude Code has released since the last run, rank what it means for this config, turn the best three **proposals** into pull requests, and record the run on the tracking issue. Bold terms are defined in `CONTEXT.md`.

The run's one required output is the tracking-issue comment in step 7. Every run ends with it, including a run that finds nothing and a run that could open no pull request.

## State

A run remembers nothing; GitHub holds all of it.

- **Tracking issue**: #187. The newest comment headed `## Upstream watch` carries a `Reviewed up to:` line, and the next run starts after that version. With no such comment, start after **2.1.267**, the release that was current when the declared sets were last verified.
- **Proposal record**: pull requests labelled both `proposal` and `upstream-watch`. An open one means that change is already proposed. A closed, unmerged one is a **rejection** and that change stays unproposed. A merged one is done.

## GitHub access

Use `gh api` for everything: in a cloud session `gh pr` and `gh issue` return 403, and the REST forms work everywhere.

| To                    | Call                                                                                                 |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| Read the tracking log | `gh api repos/{owner}/{repo}/issues/187/comments --paginate`                                         |
| List proposal records | `gh api "repos/{owner}/{repo}/issues?labels=proposal,upstream-watch&state=all" --paginate`           |
| Open a pull request   | `gh api repos/{owner}/{repo}/pulls -f title=… -f head=… -f base=main -f body=…`                      |
| Label it              | `gh api repos/{owner}/{repo}/issues/<number>/labels -f "labels[]=proposal" -f "labels[]=upstream-watch"` |
| Comment on the log    | `gh api repos/{owner}/{repo}/issues/187/comments -f body=…`                                          |

In the records listing, an entry with `pull_request.merged_at` set was merged; `state: closed` without it is a rejection.

## Steps

1. **Find the starting version** from the tracking issue, as described under State.

2. **Read the releases.** Fetch `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` and take every `## <version>` section newer than the starting version. With no newer section, go to step 7 and record the same version.

3. **Check the declared sets** against their reference pages. A difference is a **refresh** finding.

   | Declared set                              | Lives in                               | Reference page                               |
   | ----------------------------------------- | -------------------------------------- | -------------------------------------------- |
   | `DOCUMENTED_EVENTS`, `EVENTS_VERIFIED_ON` | `scripts/lib/architecture_catalogs.py` | `https://code.claude.com/docs/en/hooks.md`    |
   | `ALLOWED_KEYS`                            | `scripts/lib/settings_keys.py`         | `https://code.claude.com/docs/en/settings.md` |
   | `SETTINGS_KEY_GLOSSES`                    | `scripts/lib/architecture_catalogs.py` | `https://code.claude.com/docs/en/settings.md` |

4. **Collect findings.** Read every changelog entry in range against what this repo ships and sets (`settings.json`, `hooks/hooks.json`, `skills/`, `agents/`, `rules/`, the settings and MCP templates, the vendored-plugin pin). A finding is one entry, or one declared-set difference, that calls for one change here. Give each a kind:

   - **breakage** — a release broke something this repo relies on
   - **deprecation** — still works, marked legacy or scheduled for removal
   - **refresh** — a declared set no longer matches the platform
   - **adoption** — a new capability, optional

   **Evidence bar**: the changelog entry and its version, plus the reference page that confirms the behaviour. A finding resting on a changelog line alone is recorded as unconfirmed and gets no pull request. The step is done when every section in range has been read to its last entry.

5. **Rank** findings by kind in the order above; an adoption takes a slot only when no finding of another kind is waiting for one. Remove any finding whose change already has a proposal record, noting which.

6. **Open pull requests for the top three**, one change each. For each finding:

   - Branch `claude/upstream-watch-<slug>` from `main`, so the three stay independent.
   - Make the one change. **In scope**: primitives this repo owns, managed keys in `settings.json`, the declared sets, the vendored-plugin pin. **Recommendation only** — described in the comment, never changed by this skill: CI workflows, the validation checkers under `scripts/`, the branch ruleset, and this skill file.
   - Run `python3 scripts/generate.py`, then the validation suite in `CLAUDE.md`. In a cloud session, `pip install pre-commit` first; if a hook environment cannot be built there, run the other two commands and say in the pull request which gate is left to CI.
   - A change that fails validation and cannot be fixed inside its own scope is recorded as failed validation and gets no pull request.
   - Push, open the pull request, and add both labels. The title is a conventional commit (CI checks it). The body states the kind, the changelog entry and version, the reference page URL, the **minimum Claude Code version** the change needs (a cloud run cannot see what the maintainer has installed), and what validation ran.

   Merging is the maintainer's: a run opens pull requests and stops there. If a push or pull-request call is refused, record that finding as "could not open from this run" and carry on to step 7; the maintainer can then run this skill locally to open the ones they pick.

7. **Comment on the tracking issue** in this shape:

   ```markdown
   ## Upstream watch YYYY-MM-DD

   Reviewed up to: <newest version read>
   Reviewed from: <starting version>

   ### Pull requests opened

   - #<number> — <title> (<kind>, needs Claude Code <minimum version> or later)

   ### Not opened

   - <finding> (<kind>, <version>) — <overflow | unconfirmed | failed validation | recommendation only | could not open from this run | already proposed in #n | rejected in #n>
   ```

   Write "None." under a heading with nothing to list.
