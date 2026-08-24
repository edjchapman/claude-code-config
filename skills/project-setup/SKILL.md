---
name: project-setup
description: Bootstrap a new repository end-to-end, or install this config's tooling into an existing one. Use when starting a new repo, or when applying the quality gate, git hooks, CI, and branch protection to a project that already exists.
argument-hint: "[stack] [--existing]"
allowed-tools: Bash(bash *)
---

# Project Setup

## Environment

!`bash "${CLAUDE_SKILL_DIR}/detect-env.sh"`

Facts come from the block above; only **decisions** go to the user.

## Invariants

These hold for every repo. The **default** column is today's recommendation, not
a mandate — propose it, let the user swap the tool, keep the invariant.

| Invariant                                                  | Test that it holds                                       | Default                     |
| ---------------------------------------------------------- | -------------------------------------------------------- | --------------------------- |
| One command runs the full quality gate                     | That command exits 0                                     | `make check`                |
| The gate runs locally and in CI                            | A local hook and a CI job both invoke it                 | pre-commit + GitHub Actions |
| A local hook mechanism never silently shadows a global one | `core.hooksPath` unset, or set with the user's knowledge | run the layers separately   |
| Personal config stays out of git, shared config stays in   | `.gitignore` names only the personal paths               | see `.gitignore` below      |
| The gate is green before the first commit                  | Gate exits 0 on a clean tree                             | —                           |

Additional invariants **when the host is GitHub**:

| Invariant                                                          | Test that it holds                                 | Default                                                   |
| ------------------------------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------- |
| The permanent commit subject is validated, not merely warned about | A non-conforming subject fails the check           | `--strict` in `commit-style.yml` + `.githooks/commit-msg` |
| `main` is protected and history stays linear                       | Direct push to `main` is rejected                  | `main-protection` ruleset                                 |
| The maintainer cannot be locked out                                | An always-bypass entry exists for the user         | `RepositoryRole` id 5 (admin)                             |
| The process proves itself                                          | The setup change itself landed through the process | branch → PR → checks → squash                             |

Under squash-merge the **PR title** becomes the permanent commit subject; branch
commits are disposable WIP. A brand-new repo has no legacy runway, so promote
commit style to strict immediately rather than leaving it warn-only.

Required status checks are job **names**, not workflow names — renaming a job
orphans the requirement.

## Interview

Ask what the environment cannot tell you. Use `AskUserQuestion`, batched, and
let later rounds depend on earlier answers — a throwaway spike should never be
asked about a release process.

**Round 1 — shape.** What is this for (spike / tool / library / service)? Host
(GitHub / other / local-only)? Visibility? Licence?

**Round 2 — conditional on round 1.** Only what the shape makes relevant:
dependency automation, release/versioning, docs, published artifacts, a CI
matrix.

Then propose the concrete setup — tool by tool, with the default named and the
invariant it serves — and let the user swap any of it before anything runs.

Question every tool choice rather than assuming this repo's defaults still fit:
the gate runner (make / just / npm scripts / task), the local hook manager
(pre-commit / lefthook / husky / native `.githooks`), and CI (GitHub Actions /
alternatives). The invariants outlive all of them.

## Confirm before irreversible actions

Creating a remote, changing merge policy, and writing a ruleset reach outside
the working tree. Confirm each with the user immediately before running it.

## Layers

Two layers, distinguished by how updates reach a project (see `CONTEXT.md`):

- **Claude layer** — received by reference. Updates to this repo propagate.
  `<repo>/scripts/setup-project.sh <template> [more...]`
- **Tooling layer** — received by copy. Updates never propagate; re-run to
  refresh. `<repo>/scripts/install-tooling.sh <stack>`

`setup-project.sh <type> --tooling` runs both. It copies the git hooks but does
**not** activate them; `--git-hooks` does that, and is opt-in because a
repo-local `core.hooksPath` shadows a global dispatcher. `install-tooling.sh`
declines to wire it when a global one exists.

With a global dispatcher in play, satisfy the "gate runs locally" invariant by
invoking the gate from the existing hook manager instead — e.g. a `repo: local`
pre-commit hook running `make check` (`language: system`,
`pass_filenames: false`).

Inspect before applying: `--list`, `--dry-run <template>`, `--check <template>`,
`--status`.

## .gitignore

Commit `.claude/settings.json` and `.claude/hooks/` — the Claude-on-web
bootstrap needs them in the repo. Ignore only the personal paths:
`.claude/{agents,skills,rules}`, `.claude/settings.local.json`, `.mcp.json`.
Never blanket-ignore `.claude/`.

## Order

1. Claude layer, then tooling layer.
2. Wire the gate to the stack's fmt + lint + test; run it green.
3. Manifest hygiene — name per ecosystem convention, plus description, licence,
   readme, repository fields; pin the minimum toolchain to what is installed.
4. Standard files — README (quick start, gate command, CI badge), LICENSE,
   CONTRIBUTING, and where the host supports them a PR template and dependency
   automation. Add toolchain-install and cache steps to the CI workflow.
5. First commit, then the remote.
6. Host policy — merge method, branch protection, maintainer bypass.
7. Land this setup through the process itself. After a squash merge use
   `git branch -D` — ancestry never records the merge, so `-d` refuses.

8. Vendored-plugin setup (below), if the plugin is installed.

Create `CONTEXT.md` and `docs/adr/` lazily — at the first term or decision worth recording.

## Vendored-plugin setup

Several `mattpocock-skills` skills — `to-spec`, `to-tickets`, `triage`, `implement`,
`wayfinder` — read per-repo configuration that does not exist until it is scaffolded:
which issue tracker the repo uses, the triage label strings, and where domain docs
live. Without it they interrogate the user from scratch in every new repo, or guess.

If that plugin is installed, run **`/setup-matt-pocock-skills`** once in the new repo.
It writes `docs/agents/{issue-tracker,triage-labels,domain}.md`. Defer to it rather
than writing those files here: it owns their contract, and a copy kept in this skill
would rot silently the next time the pin moves (ADR-0003).

It is prompt-driven and cannot run silently. Skip it where the plugin is absent —
including plugin-mode installs of this repo, which never receive it — and say so.

## Related

- **Global install**: `<repo>/scripts/setup-global.sh` (ADR-0002).
- **MkDocs style layer**: `/mkdocs-style`.
- Full script and flag reference: [`docs/architecture.md`](../../docs/architecture.md).
