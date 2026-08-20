# Architecture & configuration reference

Full Claude-facing reference for this repo's moving parts — scripts, hooks, settings keys, templates, and automation. Behavioural rules and the easy-to-get-wrong gotchas live in [`CLAUDE.md`](../CLAUDE.md); user-facing catalogs live in [`README.md`](../README.md); extension recipes live in [`extending.md`](extending.md).

**Every catalog below is a generated region** (`<!-- BEGIN GENERATED: … -->`), rendered from the primitives on disk by `scripts/generate.py` (ADR-0001). Hand edits inside one are reverted on the next run — change the source instead: a hook's summary and `Why:` note live in its script header, a skill's or agent's in its frontmatter, a template's in its `_description`, and the platform-reference data in `scripts/lib/architecture_catalogs.py`. Prose outside the markers is hand-written rationale and is yours to edit.

## Key Scripts

Substitute `<repo>` below with wherever you cloned this repo (commonly
`~/Development/claude-code-config/`). Keep a **single clone**: `setup-global.sh`
symlinks `~/.claude/` at the clone that runs it, so a second clone (e.g. an old
`~/.config/claude-code-config/`) silently drifts from the one you develop in.

```bash
# Global setup (symlinks ~/.claude/agents, skills, rules; mirrors settings.json — ADR-0002)
<repo>/scripts/setup-global.sh

# Project setup (run from target project directory)
<repo>/scripts/setup-project.sh <template> [template2...]
<repo>/scripts/setup-project.sh django --tooling  # + vendor the make-check tooling layer
<repo>/scripts/setup-project.sh --list       # Show templates
<repo>/scripts/setup-project.sh --check django   # Check drift + symlinks
<repo>/scripts/setup-project.sh --status     # Show current config state
<repo>/scripts/setup-project.sh --dry-run django # Preview changes

# Vendor the hard-tooling layer (Makefile, validators, git hooks, CI) into a project.
# Run by `setup-project.sh --tooling`; also works standalone.
<repo>/scripts/install-tooling.sh --hooks [--target DIR] [--dry-run]

# Vendor the shared MkDocs Material style layer ("Ink & Indigo on warm paper",
# payload in tooling/mkdocs/) into an MkDocs project. Unlike install-tooling.sh,
# the two style-owned files (mkdocs.style.yml + custom.css) are ALWAYS
# OVERWRITTEN — re-running is the update mechanism. Wired via MkDocs `INHERIT:`
# config inheritance; the /mkdocs-style skill wraps this and cleans up the
# project's mkdocs.yml afterwards.
<repo>/scripts/install-mkdocs-style.sh [--target DIR] [--css-dest REL] [--dry-run]

# Merge templates (used internally by setup-project.sh)
python3 <repo>/scripts/merge-settings.py <templates-dir> base <type1> [type2...]
python3 <repo>/scripts/merge-mcp.py <mcp-templates-dir> base <type1> [type2...]

# One-way settings mirror: repo settings.json -> ~/.claude/settings.json (ADR-0002).
# Run by setup-global.sh; managed keys track the repo, personal keys survive.
# --check is the warn-only drift report behind the SessionStart drift hook.
python3 <repo>/scripts/sync-global-settings.py [--check]
```

Shared internals (not run directly):

- `scripts/lib/config_common.py` — helpers used by `merge-settings.py`, `merge-mcp.py`, and `generate.py` (Python version gate, template loading, output validation)
- `scripts/lib/settings_keys.py` — the managed-key sets (`ALLOWED_KEYS`, `RETIRED_KEYS`) shared by `check-settings-keys.py` and `sync-global-settings.py` (ADR-0002)
- `scripts/hooks/lib/git-context.sh` — git helpers (`in_git_work_tree`, `git_branch`, `git_dirty_count`) sourced by the hook scripts; not a hook itself
- `scripts/hooks/lib/hook-input.sh` — `hook_field <payload> <dotted.key>` helper for reading a field from the hook's stdin JSON payload; sourced by the hooks that parse stdin (format-on-edit, dangerous-cmd-check, session-end, pre/post-compact); not a hook itself
- `mcp-templates/fragments/` — shared MCP server definitions (`sqlite.json`); templates reference them as `{"$fragment": "<name>"}` and `merge-mcp.py` inlines them at merge time

## Architecture

### Hooks

Hooks are configured in **two places** so the repo works in both consumption modes:

- `settings.json` (`hooks` key) — read by the global install path. Since `settings.json` is mirrored into `~/.claude/settings.json` by `scripts/sync-global-settings.py` (ADR-0002), hooks are available in all projects.
- `hooks/hooks.json` at the repo root — read by the plugin install path (per [plugin docs](https://code.claude.com/docs/en/plugins.md)). Same shape as `settings.json`'s `hooks` object, wrapped as `{ "hooks": { ... } }`.

**Edit hooks in `hooks/hooks.json` only** — `settings.json`'s hooks block is regenerated from it (ADR-0001). Hook scripts themselves live in `scripts/hooks/` and the `${CLAUDE_PLUGIN_ROOT:-$(readlink ~/.claude/agents | xargs dirname)}` prefix in command paths makes them resolve correctly under either mode (anchored on the `agents` symlink — `settings.json` is a mirrored real file, not a symlink; ADR-0002).

Two small discrepancies between this repo and the docs, verified 2026-08-20 and left as-is:

- `hooks/hooks.json` carries a `$schema` pointing at the **settings** schema (`json.schemastore.org/claude-code-settings.json`). The plugin docs document no `$schema` key for that file. It is harmless — the loader ignores unknown keys — and it buys editor completion, because the settings schema defines `hooks` at the top level and `hooks.json` has the same shape one level down. Keep it, but don't read it as a documented contract.
- `settings.json`'s `statusLine.command` uses `${CLAUDE_PLUGIN_DIR:-…}` where every hook command uses `${CLAUDE_PLUGIN_ROOT:-…}`, and `CLAUDE_PLUGIN_ROOT` is the documented name. Nothing breaks: `statusLine` is settings-only (plugins cannot provide one), so the variable is never set in the mode that runs it and the `readlink` fallback always wins. The name is misleading rather than wrong-behaving.

#### Hook Format

Hooks use string-based matchers (e.g. `"Bash"`, `"Write|Edit"`, `"*"`). See the [official hooks reference](https://code.claude.com/docs/en/hooks.md) for the full schema and the per-event matcher fields.

**Handler types**: a hook entry's `type` can be `command` (shell script), `prompt` (LLM-evaluated yes/no decision — fields: required `prompt` with `$ARGUMENTS` as the hook-input-JSON placeholder; optional `model` (defaults to a fast model), `timeout`, `statusMessage`, `if`, `continueOnBlock`), `agent` (subagent-based verification), `http`, or `mcp_tool`. Command hooks additionally accept `async: true` (run in the background without blocking the turn) and `asyncRewake: true` (background + wake Claude on exit code 2). Repo gotcha: most events support a matcher (filtering on an event-specific field — e.g. `SessionStart` on start reason, `SessionEnd` on exit reason, `PreCompact` on `manual`/`auto`, `SubagentStop` on agent type). The events that **do not** support a matcher and must omit it are: `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`. Adding a `matcher` field to a no-matcher event is silently ignored per docs.

#### Available hooks

<!-- BEGIN GENERATED: arch-hooks -->

<!-- prettier-ignore-start -->

Wired in [`hooks/hooks.json`](../hooks/hooks.json) — 10 bindings across 9 events:

- **SessionStart** → `scripts/hooks/session-context.sh`: Auto-load git context at session start (branch, recent commits, dirty files).
- **SessionStart** → `scripts/hooks/settings-drift-check.sh`: Warn when ~/.claude/settings.json has drifted from the repo's settings.json. _Why:_ settings.json is mirrored — not symlinked — into ~/.claude/settings.json (ADR-0002), so a repo edit stays inert until a sync runs, and a runtime write can flip a managed key. This check surfaces pending drift at session start. Warn-only by design: it never applies changes itself, because silent mutation of the user's settings was deliberately rejected.
- **PostToolUse (Write|Edit)** → `scripts/hooks/format-on-edit.sh`: Auto-format files after Claude edits them (unified Python + JS/TS formatter). _Why:_ deliberately NOT `async` — the formatter rewrites files in place, so running it in the background could race a subsequent Edit of the same file in the same turn.
- **PostToolUseFailure** → `scripts/hooks/log-tool-failure.sh`: Append failed tool calls to ~/.claude/logs/tool-failures.jsonl for pattern analysis. _Why:_ cheap and LLM-free — it shows which tools fail most, so you can pre-allow them or fix the underlying issue.
- **PreToolUse (Bash)** → `scripts/hooks/dangerous-cmd-check.sh`: Defense-in-depth: block obviously catastrophic command patterns before they run. _Why:_ a best-effort SECONDARY guard, not a security boundary — it stays bypassable via variables, quoting and encodings, so the primary protections remain the settings deny-lists and simply not allow-listing catastrophic commands.
- **PreCompact** → `scripts/hooks/pre-compact-state.sh`: Preserve working state before context compaction. _Why:_ a hook's plain stdout is NOT injected for PreCompact (only UserPromptSubmit / UserPromptExpansion / SessionStart inject stdout), so the snapshot goes to a session-keyed file that post-compact-restore.sh re-injects via hookSpecificOutput.additionalContext once compaction completes.
- **PostCompact** → `scripts/hooks/post-compact-restore.sh`: Re-inject the pre-compaction state snapshot after context compaction completes. _Why:_ this is the half of the compaction loop that actually restores state — it reads the session-keyed snapshot pre-compact-state.sh wrote, emits it via hookSpecificOutput.additionalContext, and deletes the one-shot file.
- **TaskCompleted** → `scripts/hooks/task-completed-chime.sh`: Emit a terminal bell when an autonomous task completes. _Why:_ surfaces completion of long autonomous runs without polling. The bell is non-intrusive (terminals can mute it) and needs no platform-specific notification daemon.
- **Notification** → `scripts/hooks/notify-attention.sh`: Desktop notification when Claude is blocked on you (permission request or idle wait). _Why:_ the Notification event fires exactly when Claude needs you, and you should not have to watch the terminal to notice. macOS uses osascript (with sound), Linux notify-send, with a terminal bell fallback everywhere; always exits 0.
- **SessionEnd** → `scripts/hooks/session-end.sh`: Record each session end — always a CSV row, plus a git summary in ./standups/. _Why:_ the CSV row (~/.claude/debug/session-log.csv) is unconditional; the ./standups/YYYY-MM-DD-log.md append that /standup later reads is opt-in on that directory already existing, so ending a session in an unrelated repo does not scatter standups/ dirs across the filesystem.

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-hooks -->

Available but **not configured by default** (opt-in by adding a prompt-type entry to **both** hook files):

- **Stop**: LLM completeness gate — blocks stopping only when the turn claims implementation work is done while promised tests/linters were skipped or left failing. If you enable it, keep the `stop_hook_active` escape hatch in the prompt (see snippet): without it, an uncurable block condition re-fires the gate on every retry (the harness caps consecutive blocks at 8, but each one costs a model call and a forced continuation).
- **UserPromptSubmit**: LLM-evaluated check that the user prompt is specific enough
- **SubagentStop**: LLM-evaluated check that a subagent completed its assigned task

Opt-in snippet shape (adjust the event name and criteria):

```json
"Stop": [
  { "hooks": [ { "type": "prompt", "prompt": "You are a completeness gate deciding whether the assistant may stop. Hook input: $ARGUMENTS. If stop_hook_active is true in the input, allow. Read last_assistant_message. Block stopping ONLY if it claims implementation work is complete while tests, linters, or type checks the same turn said it would run were skipped or left failing, or if it ends by promising immediate further work that was not done. Allow conversational replies, questions to the user, plans, research or analysis summaries, and honest reports of blockers, partial progress, or waiting on background work. When unsure, allow.", "statusMessage": "Checking turn completeness", "timeout": 30 } ] }
]
```

Prompt-type hooks invoke a fast model on every fire and incur token cost. Because this config ships to plugin and symlink consumers alike, all three are opt-in (conservative defaults: cost-bearing behavior is explicit-on, never inherited from a `git pull`).

#### Platform events not wired here (reference)

<!-- BEGIN GENERATED: arch-unwired-events -->

<!-- prettier-ignore-start -->

Claude Code documents **30** hook events; this repo wires 9 of them above. Documented events it does not wire, with their matcher field where confirmed against the docs on 2026-07-29:

| Event                | Fires when                                              | Matcher field                                       |
| -------------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `Setup`              | started with `--init` / `--init-only` / `--maintenance` | CLI flag                                            |
| `PermissionRequest`  | a tool call needs a permission decision                 | tool name                                           |
| `PermissionDenied`   | a tool call is denied by the auto-mode classifier       | tool name                                           |
| `SubagentStart`      | a subagent is spawned                                   | agent type                                          |
| `StopFailure`        | the turn ends due to an API error                       | error type (`rate_limit`, `overloaded`, …)          |
| `InstructionsLoaded` | a `CLAUDE.md` / `.claude/rules/*.md` loads into context | load reason (`session_start`, `path_glob_match`, …) |
| `FileChanged`        | a watched file changes on disk                          | filename(s) to watch                                |

Also available (matcher fields not re-verified here — consult the hooks reference before wiring): `UserPromptExpansion`, `ConfigChange`, `Elicitation`, `ElicitationResult`.

Most useful to adopt here: **`PermissionRequest`** / **`PermissionDenied`** could feed a permission-tuning workflow; **`StopFailure`** matched on `rate_limit` / `overloaded`, complements the `fallbackModel` chain.

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-unwired-events -->

Not a runtime hook: `scripts/hooks/check-duplicates.sh` lives alongside the hooks but is a validator, run by pre-commit and by `.github/workflows/validate-config.yml`, failing if two agents/skills share a name.

### Settings Keys

Beyond plugins and hooks, `settings.json` sets:

<!-- BEGIN GENERATED: arch-settings-keys -->

<!-- prettier-ignore-start -->

- **`$schema`**: Settings schema URL, for editor completion and validation
- **`attribution`**: Git commit/PR attribution text — empty `commit`/`pr` strings and `sessionUrl: false` suppress the Claude trailers
- **`fallbackModel`**: Ordered fallback chain tried when the primary model is unavailable
- **`hooks`**: Per-event hook configuration — generated from `hooks/hooks.json` (ADR-0001)
- **`worktree`**: Worktree-session config: `baseRef: head` branches from local HEAD (preserving unpushed commits); `bgIsolation: worktree` blocks Edit/Write in the main checkout until `EnterWorktree` is called
- **`statusLine`**: Command-based status line showing git branch, dirty count, and PR status
- **`enabledPlugins`**: Plugin enablement map — universal plugins only, some deliberately `false`
- **`extraKnownMarketplaces`**: Extra plugin marketplaces this config expects to be available
- **`outputStyle`**: Output style for assistant responses (built-ins: `default`, `Explanatory`, `Learning`)
- **`sandbox`**: Sandbox configuration (`enabled`, `autoAllowBashIfSandboxed`)
- **`tui`**: TUI rendering mode — `fullscreen` is the flicker-free alt-screen renderer with virtualized scrollback; `default` is the classic one. Matches `/tui`
- **`autoMemoryEnabled`**: Auto-memory on/off (platform default `true`)
- **`inputNeededNotifEnabled`**: Desktop notification when Claude is blocked waiting for you
- **`agentPushNotifEnabled`**: Push notifications for background agent activity

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-settings-keys -->

Why some of them are set the way they are:

- **`attribution`**: both fields are set to empty strings (`commit: ""`, `pr: ""`) to suppress the `Co-Authored-By: Claude` trailer and the "Generated with Claude Code" line on commits **and** PRs — per the schema, the `commit` field covers trailers too, so one empty string handles both. Modern replacement for the deprecated `includeCoAuthoredBy` boolean. `sessionUrl: false` suppresses the `Claude-Session: https://claude.ai/code/session_...` link trailer as well — a separate boolean key (added in v2.1.183) that the co-author/generated-with fields do **not** cover, and which is still absent from the official settings docs (anthropics/claude-code#69614). **Scope limit — the gotcha that costs an afternoon:** these fields govern only the attribution the harness _appends_. They have no authority over a trailer the model _types_ into a message body, so a project instruction like _“Claude commits keep the `Co-Authored-By` trailer”_ silently overrides this setting, with no error surfaced anywhere. Diagnosed 2026-08-20: `career-portfolio` documented keeping the trailer in three files and had accumulated 552 trailered commits, while every other consumer of this config stayed clean. If attribution appears to “stop working” in one repo, grep that repo's `CLAUDE.md`, `CONTRIBUTING.md`, and `.claude/commands/` before suspecting the setting. Note also that the display name is unstable (`Claude`, `Claude Opus 4.5`, `Claude Sonnet 4.5`, `Claude Opus 4.8 (1M context)`, …) while the `noreply@anthropic.com` address is not — match on the address, never the name.
- **No universal `model` pin**: `settings.json` deliberately sets **no** `model`, so consumers fall through to their account's recommended default (`opus` → Opus 5, `sonnet` → Sonnet 5 on the Anthropic API as of v2.1.219). A pin is avoided here because `fallbackModel` does **not** cover entitlement — an entitlement-gated pin (e.g. `fable`) would fail outright for a consumer who lacks access. A _personal_ pin belongs directly in `~/.claude/settings.json` as an unmanaged key: the sync preserves it (ADR-0002). Do **not** put one in `~/.claude/settings.local.json` — empirical probes (2026-08-20) showed Claude Code never reads `model` from that file; the "personal layer" previously documented there was inert. The maintainer currently runs unpinned (account default), selecting Fable per-session via `/model`. If you _do_ want a universal pin, two aliases are worth knowing: **`best`** (Fable 5 where your org has access, else the latest Opus — entitlement-aware, so it degrades gracefully) and **`opusplan`** (uses `opus` in plan mode, then `sonnet` for execution — a natural fit for Explore→Plan→Code and the plan-mode advisors). Accepts aliases (`fable`, `opus`, `sonnet`, `haiku`, `best`, `opusplan`), full model IDs (e.g. `claude-opus-5`), and 1M forms (`opus[1m]`). History: `fable` → `opus` (Fable budget exhausted, 2026-07-14) → `claude-fable-5[1m]` moved to the personal layer (PR #84) → universal pin removed entirely (2026-07-29) → personal layer proven inert and retired; unpinned by choice (ADR-0002, 2026-08-20). (Model landscape verified against the model-config docs, 2026-07-29.)
- **`fallbackModel`**: Ordered fallback chain (`["sonnet", "haiku"]`) tried when the primary `model` is overloaded or unavailable — Claude switches to the next model for the rest of the turn and shows a notice. Added after a Fable-exhaustion incident (2026-07-14) broke sessions outright; the fallback makes exhaustion/rate-limits degrade gracefully to Sonnet instead. **Value is an array** (bare string is invalid), capped at 3 entries. Note: unlike most array settings it does **not** merge across settings files — the highest-precedence file that defines it supplies the whole chain — and the `--fallback-model` CLI flag overrides it for one session. It does **not** cover entitlement: a model your account can't access fails with a manual `/model` prompt rather than falling back — which is why entitlement-gated pins live in the personal layer, not here.
- **`enabledPlugins`**: Plugin enablement map. The checked-in `settings.json` lists only **universal** plugins (no external accounts required), but not all are enabled: entries set to `false` are deliberate default-offs — heavy plugins whose skill/agent/command descriptions would load into every session (see the "What earns always-loaded context" ladder in [`extending.md`](extending.md)). A repo-declared entry follows the repo on every sync (ADR-0002), so re-enable one either universally (flip it here) or per-project (`.claude/settings.json`). Personal opt-ins the repo does not declare (Figma, other account-gated plugins) go directly in `~/.claude/settings.json` — the sync preserves entries it does not manage
- **`effortLevel`** (not set): a `medium` default was set 2026-07-14 as a routine token saving, then dropped with the Fable 5 switch; effort now inherits the model default, stepped up per-task when depth matters.

<!-- BEGIN GENERATED: arch-unset-settings-keys -->

<!-- prettier-ignore-start -->

Other documented keys this repo does **not** set (available as opt-ins): `alwaysThinkingEnabled`, `autoMemoryDirectory` (custom auto-memory storage dir), `autoMode`, `availableModels` (restrict selectable models), `axScreenReader` (screen-reader-friendly output), `cleanupPeriodDays` (session file retention, default 30), `disableBundledSkills` (hide bundled skills like `/code-review`, `/loop`), `effortLevel` (default reasoning effort), `enforceAvailableModels` (restrict selectable models), `env`, `fastMode` (faster Opus output, default `false`), `fileSuggestion`, `language` (response language preference), `model`, `parentSettingsBehavior`, `skillOverrides`, `spinnerVerbs`.

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-unset-settings-keys -->

### Skills

Skills use the official nested layout: `skills/<name>/SKILL.md`. Custom commands were merged into skills upstream — a flat `commands/foo.md` still works but is the legacy form, so this repo keeps everything under `skills/` (the former `commands/` directory was migrated here). Two kinds live in `skills/`:

<!-- BEGIN GENERATED: arch-skills -->

<!-- prettier-ignore-start -->

**Domain-knowledge skills** — Claude loads these automatically when the conversation matches their `description:`:

- `api-design`: REST API conventions — resources, status codes, pagination, error shapes. Use when designing or reviewing routes, controllers, endpoints, serializers, or schemas.
- `django-patterns`: Django app-layer and ORM conventions. Use when editing models, views, serializers, admin, managers, signals, migrations, or querysets.
- `docker-patterns`: Container build, security, and caching conventions. Use when editing Dockerfiles, Compose files, build contexts, or .dockerignore.
- `git-workflow`: Git branching, commits, PRs, and release workflows. Use for anything under .git, and for tricky operations — interactive rebase, merge-conflict resolution, cherry-picking, bisecting, reflog recovery.
- `infrastructure`: Terraform, Kubernetes, and Helm conventions. Use when editing infrastructure modules, manifests, charts, or deployment config.
- `project-setup`: Install this config into a repo or bootstrap a new one — setup-project.sh, install-tooling.sh, the layered hooks setup, the new-repo runbook. Use when running the setup scripts or vendoring the tooling.
- `security-patterns`: Auth, input-validation, and secrets conventions. Use when writing or reviewing authentication, authorization, middleware, routes, JWT, CSRF, or CORS code; for a full audit of pending changes use /security-review.
- `testing-patterns`: Test structure, fixtures, factories, and mocking conventions. Use when writing or reviewing tests, or files named test\_\*, \*\_test, \*.test.\*, or \*.spec.\*.

**Workflow skills** — invoked as `/<name>`; those without `disable-model-invocation` can also be auto-invoked by Claude:

- `/adr`: Record a technical decision as an Architecture Decision Record (Nygard format). Use when weighing a framework, library, database, or schema-migration trade-off, or when asked for an ADR.
- `/commit`: Analyze staged changes and write a conventional commit message. Use when staged changes are ready to commit or a message needs wording.
- `/eow-review`: Summarize the full week's work across Git, GitHub, and Jira into end-of-week review notes. Use when wrapping up the week. **Schedulable** — fired by the end-of-week review routine (issue #52).
- `/hotfix`: Ship an urgent production fix — minimal change, targeted tests, PR. Use when the user says "hotfix" or describes a bug that has to reach main now.
- `/later`: Create a "Later" backlog item (Learn / Research / Do / Read) from a configurable template. **User-only.**
- `/mkdocs-style`: Install or refresh the shared MkDocs Material style layer (Ink & Indigo on warm paper). Use when setting up or restyling a docs project.
- `/pr`: Open a pull request with a well-crafted description. Use when branch work is finished and ready for review.
- `/refinement`: Prepare technical analysis for backlog refinement meetings. **User-only.**
- `/standup`: Summarize recent work across Git, GitHub, and Jira into a standup document. Use when asked what you worked on recently. **Schedulable** — fired by the daily standup routine (issue #51).
- `/status`: Capture a quick status update and append it to today's daily log. **User-only.**

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-skills -->

The user-only skills above set `disable-model-invocation: true`. **Scheduling constraint**: that flag also prevents a skill from running when a scheduled task fires with the skill as its prompt (v2.1.196+) — `/standup` and `/eow-review` deliberately omit it so scheduled routines can run them.

### Rules

Rules are path-scoped code style enforcement files in `rules/`. They use `paths` frontmatter for granular file matching.

**Symlink-mode only.** Rules are not a supported plugin component — the official plugin layout ships skills, agents, hooks, MCP/LSP servers, and settings, but has no rules directory or manifest field (verified against the plugin docs, 2026-07-22; rules exist only at user level `~/.claude/rules/` and project level `.claude/rules/`). Consumers installing this repo as a plugin therefore don't get `rules/`; only the `setup-global.sh` symlink path (`rules/` → `~/.claude/rules`) delivers them. If plugin support for rules lands upstream, wire it here and drop this note.

Available rules:

<!-- BEGIN GENERATED: arch-rules -->

<!-- prettier-ignore-start -->

- `python-style`: General, Naming, Error Handling, Imports, Type Hints (`**/*.py`)
- `typescript-style`: General, Naming, Error Handling, Types, React (`.tsx` files) (`**/*.ts`, `**/*.tsx`)

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-rules -->

### Settings Files: Two Purposes

The settings files this repo manages:

| File                      | Purpose                                                                                                                    | Distribution                                                                     | Source                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------- |
| `settings.json`           | **Universal** plugin enablement + hooks (no external auth required)                                                        | **Mirrored** into `~/.claude/settings.json` by the sync (ADR-0002)               | Canonical copy in repo            |
| `~/.claude/settings.json` | The live user-scope file: managed keys track the repo, the rest (model pin, permissions, personal plugin entries) is yours | Real file, untracked; `scripts/sync-global-settings.py` keeps managed keys fresh | Merged: repo + personal keys      |
| `settings.local.json`     | Bash permissions (project scope: `.claude/settings.local.json`)                                                            | **Generated** per-project                                                        | Merged from `settings-templates/` |

**Why split universal vs personal plugins?** The repo is consumable by anyone (via plugin install or the global setup). Auto-enabling Notion/Figma/etc. for someone who has no account or doesn't use those tools is surprising. `settings.json` carries only plugins that work without external accounts. Of those, `github`, `playwright`, `pyright-lsp`, `typescript-lsp`, and `mattpocock-skills` are enabled by default; `pr-review-toolkit`, `feature-dev`, `code-simplifier`, `document-skills`, and `frontend-design` are listed but set `false` — a deliberate default-off (2026-07-31 token-efficiency review): each enabled plugin ships all its skill/agent/command descriptions into every session, and these five weren't earning that fixed cost in most sessions. Repo-declared entries follow the repo on every sync; enable a default-off universally (flip it in the repo) or per-project (`.claude/settings.json`). Personal opt-ins (`figma`) are added directly to `enabledPlugins` in `~/.claude/settings.json` — the sync's per-entry merge preserves entries the repo does not declare. Entitlement-gated model pins likewise live in `~/.claude/settings.json` as unmanaged keys, never in the universal file (see the _No universal `model` pin_ note above).

**Merge semantics (ADR-0002)**: `scripts/sync-global-settings.py` performs a one-way, strict mirror — repo → `~/.claude/settings.json` — of the managed keys (`ALLOWED_KEYS` in `scripts/lib/settings_keys.py`, plus whatever the repo file carries; `RETIRED_KEYS` tombstones clean up dropped keys). `enabledPlugins` is the one exception: it merges per entry. Every other key in the home file is personal and never touched. A warn-only SessionStart hook (`settings-drift-check.sh`) reports drift; it deliberately never auto-applies. Historical note: before 2026-08-20, `~/.claude/settings.json` was a symlink into this repo, which sent every user-scope runtime write (`/model`, `/config` toggles) into the public repo as a pending diff — and the documented escape hatch, `~/.claude/settings.local.json`, was proven by experiment to not be read by Claude Code (only the project-scope `.claude/settings.local.json` exists; see the [settings docs](https://code.claude.com/docs/en/settings.md)).

### Settings Template System

Templates in `settings-templates/` are JSON files defining Claude Code permissions. The merge system:

1. Always includes `base.json` first (git, gh CLI, file operations)
2. Adds requested templates in order (django, react, etc.)
3. Merges permissions with precedence: **deny > allow**
4. Outputs combined `settings.local.json`

<!-- BEGIN GENERATED: arch-settings-templates -->

<!-- prettier-ignore-start -->

Available templates (14):

- `aws`: AWS CLI describe/validate (read-only), cfn-lint, cfn-guard, cdk synth/diff (deletion & deploy denied)
- `base`: Git, GitHub CLI, file operations, WebSearch (always included)
- `django`: Django manage.py commands (test with --no-input --parallel=8), docker compose, make, uv run (flake8, basedpyright)
- `docker`: Docker build, compose, buildx, system commands
- `fastapi`: uvicorn, alembic, pytest, ruff, mypy, uv, poetry, docker compose
- `go`: go build/test/run, golangci-lint, staticcheck, dlv, mockgen, wire
- `java`: Gradle, Maven, Java compilation (javac, jar)
- `kubernetes`: kubectl, helm, kustomize, kubectx, stern
- `nextjs`: Next.js dev/build/lint, Vercel CLI, npm/yarn/pnpm, vitest, playwright
- `node`: npm, yarn, pnpm, vitest, jest, mocha, eslint, prettier, tsc, bun
- `python`: pytest, mypy, ruff, black, isort, flake8, pylint, bandit, pre-commit, pip, uv, poetry
- `react`: npm, yarn, pnpm, vitest, playwright, TypeScript, eslint, prettier
- `rust`: cargo, rustc, rustup, rustfmt, clippy
- `terraform`: terraform fmt/validate/plan/init

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-settings-templates -->

This repo's own `.claude/settings.local.json` is generated from every template **except `aws`** (see its `_generated_from`) — deliberate selection, not drift: the repo has no AWS surface, so AWS CLI allows would be dead weight here.

Template structure:

```json
{
  "_source": "template-name",
  "_version": 1,
  "permissions": {
    "allow": ["Bash(command:*)"],
    "deny": ["Bash(dangerous:*)"]
  }
}
```

Bump `_version` when a template's permission set changes meaningfully — the value isn't used by the merge logic but signals drift to humans reviewing diffs.

**Allowlist breadth is deliberate.** Generated allowlists include broad categories (`Bash(rm:*)`, `Bash(mv:*)`, `Bash(cp:*)`, package-manager installs) to keep permission-prompt friction low. The safety layer is the deny list (catastrophic forms like `rm -rf /`) plus the `dangerous-cmd-check.sh` PreToolUse hook — not allowlist narrowness. Don't "fix" broad allows by narrowing them; strengthen the deny list or the hook instead.

### MCP Template System

MCP templates in `mcp-templates/` define MCP server configurations per project type. The merge system:

1. Always includes `base.json` first (empty by default — MCP is opt-in)
2. Adds MCP servers from matching type templates
3. Outputs combined `.mcp.json` in the project root

<!-- BEGIN GENERATED: arch-mcp-templates -->

<!-- prettier-ignore-start -->

Available MCP templates:

- `aws`: `aws-iac`
- `base`: **no MCP server** (opt-in)
- `django`: **no MCP server** (opt-in)
- `fastapi`: **no MCP server** (opt-in)
- `nextjs`: **no MCP server** (opt-in)
- `node`: `sqlite`
- `python`: `sqlite`

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-mcp-templates -->

Stacks without an MCP template (Go, Rust, Java, Kubernetes, Terraform) fall through to `base.json` (empty); Django/Next.js/FastAPI keep templates but now ship **no default MCP server** (empty `mcpServers`). Add MCP servers manually in the project's generated `.mcp.json` when needed. Generic Python/Node templates use SQLite because there's no shared external DB assumption. The `aws` template is the lone infra MCP server — it's `uvx`-based rather than `npx`-based, so verify against PyPI (confirmed `awslabs.aws-iac-mcp-server` published at template creation time) rather than the npm registry. Verify each template's package before relying on it — versions move (npm search confirmed `mcp-server-sqlite-npx@0.8.0` exists at template creation time). **Postgres note (2026-07-29):** the shared `postgres` fragment (`@modelcontextprotocol/server-postgres`) was **removed** — it's archived/deprecated with a known SQL-injection vuln, and the `npx` "replacements" are unmaintained or npm security-stub names; the one maintained option is Python-only (`uvx postgres-mcp`, Crystal DBA), so DB MCP is left to deliberate per-project opt-in.

Playwright is now provided as a first-class plugin (`playwright@claude-plugins-official`,
enabled in `settings.json`), not via an MCP template, so React projects do not
generate a `.mcp.json` from this repo by default.

**Environment Variables**: Variables like `${DATABASE_URL}` are expanded at Claude Code runtime.
Ensure required variables are set in your shell or `.envrc` before launching Claude Code.

### CLI Scripts

Headless Claude Code scripts in `scripts/cli/` for automation:

<!-- BEGIN GENERATED: arch-cli-scripts -->

<!-- prettier-ignore-start -->

- `daily-report.sh`: Summarize yesterday's git activity across all projects
- `explain-error.sh`: Pipe error output to Claude for explanation — invoke as `some-command 2>&1 | explain-error.sh`
- `review-changes.sh`: Review uncommitted changes using Claude headless mode
- `review-pr.sh`: Headless PR review — invoke as `review-pr.sh <pr-number>`

<!-- prettier-ignore-end -->
<!-- END GENERATED: arch-cli-scripts -->

### Automation: pick the right trigger

The repo's philosophy is **automatic over explicit** — prefer a mechanism that fires itself over one you must remember to invoke. Decision table:

| Mechanism                           | Fires on                                  | Runs where            | Use for                                                                         |
| ----------------------------------- | ----------------------------------------- | --------------------- | ------------------------------------------------------------------------------- |
| **Command hook**                    | Lifecycle event (tool use, session, stop) | Local, in-session     | Formatting, safety checks, context capture (see Hooks above)                    |
| **Prompt hook** (`type: "prompt"`)  | Lifecycle event, LLM-judged               | Local, in-session     | Quality gates that need judgment (e.g. the opt-in `Stop` completeness gate)     |
| **Scheduled routine** (`/schedule`) | Cron schedule / GitHub event / API call   | Anthropic cloud       | Time-based workflows; cloud sessions can't see local files                      |
| **`/loop`**                         | Recurring interval inside an open session | Local, in-session     | Polling something during active work ("check the deploy every 5 min")           |
| **Headless CLI script**             | Shell alias / OS cron / pipe              | Local, out-of-session | Shell-integrated one-shots (`scripts/cli/*`), local cron with local file access |

Live routines — this section is the canonical home for their schedules and delivery targets; README links here rather than restating them (manage at <https://claude.ai/code/routines>):

- **Daily standup prep** — weekdays 07:30 UTC (~08:30 London in summer), runs the `/standup` workflow against GitHub, delivers a comment on the pinned tracking issue [#51](https://github.com/edjchapman/claude-code-config/issues/51). Cloud sessions can't read local `./standups/` logs, so the routine prompt is self-contained.
- **End-of-week review** — Fridays 15:00 UTC (~16:00 London in summer), same pattern via the `/eow-review` workflow, delivering to issue [#52](https://github.com/edjchapman/claude-code-config/issues/52).

Delivery is a GitHub issue comment because GitHub is the one dependency the cloud sandbox already needs for activity gathering — no separate connector auth to go stale. Keep #51/#52 open — closing them orphans the routines' delivery target.

Gotchas: cron expressions are UTC (runs shift an hour in UK winter); minimum routine interval is 1 hour; and a skill with `disable-model-invocation: true` **cannot** be fired by a scheduled task — which is why `standup`/`eow-review` omit that flag.

### Agent Definitions

Agents in `agents/` are Markdown files with YAML frontmatter:

- `name`: Agent identifier (used as `@agent-name`)
- `description`: When Claude should invoke this agent — a rich `"… Use when <trigger>"` phrasing (this repo's convention; the agents use trigger prose rather than `<example>` blocks)
- `model` (optional): omit to **inherit** the session model (the default, right for deep-reasoning agents); pin `sonnet` for pattern-based cost routing or `haiku` for highly structured / data-plumbing
- `tools` / `disallowedTools` (optional): Allowlist / denylist restricting the agent's tool pool. Used by the `permissionMode: plan` advisors (`database-architect`, `devops-engineer`) with a read-only pool (`Read, Glob, Grep, Bash, WebFetch, WebSearch`) — they analyse and design; the main session implements
- `color` (optional): UI hint for the agent's display colour
- `permissionMode` (optional): Override the subagent's permission mode (e.g. `plan` starts the agent in plan mode for spec/review work that should not edit until approved)
- `memory` (optional): Persistent cross-session memory scope (`user`, `project`, or `local`). Used by `bug-resolver`, `ci-debugger`, and `performance-engineer` (`project`) so diagnosed root causes, flaky-test signatures, and perf baselines compound across sessions — pair it with a body section telling the agent to read/update its memory
- `isolation` (optional): `worktree` runs the agent in a temporary git worktree (auto-cleaned if it makes no changes)

### Skill Definitions

Skills use the official nested layout: each skill is a directory `skills/<name>/SKILL.md` with YAML frontmatter. **Canonical fields** (per the [Claude Code skills docs](https://code.claude.com/docs/en/skills)):

- `name` (optional): Display name in skill listings (defaults to the directory name; the `/name` you type comes from the directory)
- `description`: Rich description shown in the skill picker AND used by Claude to decide when to load the skill. Pattern: `"<what it does>. Use when <user trigger phrasing>."` — Claude matches this against the conversation.
- `when_to_use` (optional): Extra trigger context appended to `description` in the skill listing (the combined text is truncated at 1,536 chars — put the key use case first in `description`)
- `argument-hint` (optional): Hint shown in autocomplete for `$ARGUMENTS`
- `allowed-tools` / `disallowed-tools` (optional): Tools pre-approved / denied while the skill is active (space/comma-separated or YAML list)
- `disable-model-invocation` (optional): Set `true` for user-only invocation. Claude won't auto-fire it, its description stays out of the session context, **and scheduled tasks can't run it** (v2.1.196+)
- `user-invocable` (optional): Set `false` to hide from the `/` picker (background knowledge only)
- `model`, `effort` (optional): Per-skill model/effort overrides (apply for the rest of the turn)
- `paths` (optional): Glob patterns limiting auto-load to work on matching files
- `context: fork` + `agent` (optional): Run the skill in a forked subagent context

Historical note: `when_to_use:` and `paths:` were once non-canonical for skills; both are now official fields. This repo still prefers a rich `description:` as the primary trigger, and keeps path-scoped _style enforcement_ in `rules/` (which also use `paths:`).
