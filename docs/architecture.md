# Architecture & configuration reference

Full Claude-facing reference for this repo's moving parts — scripts, hooks, settings keys, templates, and automation. Behavioural rules and the easy-to-get-wrong gotchas live in [`CLAUDE.md`](../CLAUDE.md); user-facing catalogs live in [`README.md`](../README.md); extension recipes live in [`extending.md`](extending.md).

## Key Scripts

Substitute `<repo>` below with wherever you cloned this repo (commonly
`~/.config/claude-code-config/` or `~/Development/claude-code-config/`).

```bash
# Global setup (creates ~/.claude/agents, skills, rules, and settings.json symlinks)
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
```

Shared internals (not run directly):

- `scripts/lib/config_common.py` — helpers used by `merge-settings.py`, `merge-mcp.py`, and `check-hooks-sync.py` (Python version gate, template loading, output validation)
- `scripts/hooks/lib/git-context.sh` — git helpers (`in_git_work_tree`, `git_branch`, `git_dirty_count`) sourced by the hook scripts; not a hook itself
- `mcp-templates/fragments/` — shared MCP server definitions (`postgres.json`, `sqlite.json`); templates reference them as `{"$fragment": "<name>"}` and `merge-mcp.py` inlines them at merge time

## Architecture

### Hooks

Hooks are configured in **two places** so the repo works in both consumption modes:

- `settings.json` (`hooks` key) — read by the symlink-global install path. Since `settings.json` is symlinked into `~/.claude/`, hooks are available in all projects.
- `hooks/hooks.json` at the repo root — read by the plugin install path (per [plugin docs](https://code.claude.com/docs/en/plugins.md)). Same shape as `settings.json`'s `hooks` object, wrapped as `{ "hooks": { ... } }`.

**Keep both files in sync** whenever you add or change a hook. Hook scripts themselves live in `scripts/hooks/` and the `${CLAUDE_PLUGIN_DIR:-$(readlink ~/.claude/settings.json | xargs dirname)}` prefix in command paths makes them resolve correctly under either mode.

#### Hook Format

Hooks use string-based matchers (e.g. `"Bash"`, `"Write|Edit"`, `"*"`). See the [official hooks reference](https://code.claude.com/docs/en/hooks.md) for the full schema and the per-event matcher fields.

**Handler types**: a hook entry's `type` can be `command` (shell script), `prompt` (LLM-evaluated yes/no decision — fields: required `prompt` with `$ARGUMENTS` as the hook-input-JSON placeholder; optional `model` (defaults to a fast model), `timeout`, `statusMessage`, `if`, `continueOnBlock`), `agent` (subagent-based verification), `http`, or `mcp_tool`. Command hooks additionally accept `async: true` (run in the background without blocking the turn) and `asyncRewake: true` (background + wake Claude on exit code 2). Repo gotcha: most events support a matcher (filtering on an event-specific field — e.g. `SessionStart` on start reason, `SessionEnd` on exit reason, `PreCompact` on `manual`/`auto`, `SubagentStop` on agent type). The events that **do not** support a matcher and must omit it are: `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`. Adding a `matcher` field to a no-matcher event is silently ignored per docs.

#### Available hooks

Currently configured in `settings.json`:

- **SessionStart** → `scripts/hooks/session-context.sh`: auto-loads git context (branch, recent commits, dirty files)
- **SessionEnd** → `scripts/hooks/session-end.sh`: appends session summary to `./standups/YYYY-MM-DD-log.md` for later `/standup` consumption
- **PostToolUse (Write|Edit)** → `scripts/hooks/format-on-edit.sh`: auto-formats Python files (ruff) and JS/TS files (prettier). Deliberately **not** `async`: the formatter rewrites files in place, so running it in the background could race a subsequent Edit of the same file in the same turn.
- **PostToolUseFailure** → `scripts/hooks/log-tool-failure.sh`: appends failed tool calls to `~/.claude/logs/tool-failures.jsonl` for later pattern analysis
- **PreToolUse (Bash)** → `scripts/hooks/dangerous-cmd-check.sh`: blocks dangerous command patterns (defense-in-depth)
- **PreCompact** → `scripts/hooks/pre-compact-state.sh`: preserves working state before context compaction
- **TaskCompleted** → `scripts/hooks/task-completed-chime.sh`: emits a terminal bell when an autonomous task completes

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

CI-only utility (not a runtime hook): `scripts/hooks/check-duplicates.sh` runs from `.github/workflows/validate-config.yml` to fail CI if two agents/skills share a name.

### Settings Keys

Beyond plugins and hooks, `settings.json` currently sets (listed in file order — keep this list in sync when reordering keys):

- **`model`**: Default model alias (`opus`). Was `fable` until the maintainer's Fable token budget was exhausted (2026-07-14). Briefly removed in `cd66b43` as "deprecated", then restored after verifying the key is still canonical in the settings schema. Accepts aliases (`fable`, `opus`, `sonnet`, `haiku`), full model IDs, and 1M-context forms (e.g. `opus[1m]`). (A former `skillListingBudgetFraction` key was removed 2026-07-15 after confirming it does not exist in the official settings reference.)
- **`fallbackModel`**: Ordered fallback chain (`["sonnet", "haiku"]`) tried when the primary `model` is overloaded or unavailable — Claude switches to the next model for the rest of the turn and shows a notice. Added after a Fable-exhaustion incident (2026-07-14) broke sessions outright; the fallback makes exhaustion/rate-limits degrade gracefully to Sonnet instead. **Value is an array** (bare string is invalid), capped at 3 entries. Note: unlike most array settings it does **not** merge across settings files — the highest-precedence file that defines it supplies the whole chain — and the `--fallback-model` CLI flag overrides it for one session.
- **`attribution`**: Git commit/PR attribution text. Both fields are set to empty strings (`commit: ""`, `pr: ""`) to suppress the `Co-Authored-By: Claude` trailer and the "Generated with Claude Code" line on commits **and** PRs — per the schema, the `commit` field covers trailers too, so one empty string handles both. Modern replacement for the deprecated `includeCoAuthoredBy` boolean.
- **`hooks`**: Per-event hook configuration (see Hooks section above)
- **`worktree`**: Worktree-session config. `baseRef: head` branches new worktrees from local HEAD (preserving unpushed commits) instead of `origin/<default>`; `bgIsolation: worktree` blocks Edit/Write in the main checkout until `EnterWorktree` is called.
- **`statusLine`**: Command-based status line showing git branch, dirty count, and PR status
- **`enabledPlugins`**: Plugin enablement map. The checked-in `settings.json` lists only **universal** plugins (no external accounts required). Personal opt-ins (Figma, frontend-design) live in `settings.personal.json.example`
- **`outputStyle`**: Output style for assistant responses (`Explanatory`; built-ins are `default`, `Explanatory`, `Learning`)
- **`sandbox`**: Sandbox configuration with `enabled` and `autoAllowBashIfSandboxed`
- **`effortLevel`**: Default reasoning effort (`medium`; valid values `low`/`medium`/`high`/`xhigh`). Lowered from `high` (2026-07-14) as the highest-leverage routine token saving — `medium` on Opus 4.8 keeps strong quality while cutting per-turn reasoning tokens; step up per-task when depth matters.
- **`tui`**: TUI rendering mode (`fullscreen` = flicker-free alt-screen renderer with virtualized scrollback; `default` = classic renderer). Corresponds to the `/tui` command.
- **`agentPushNotifEnabled`**: Push notifications for background agent activity

Other documented keys that this repo does **not** currently set (available as opt-ins): `env`, `fileSuggestion`, `spinnerVerbs`, `skillOverrides`, `autoMode`, `alwaysThinkingEnabled`, `parentSettingsBehavior`, `autoMemoryDirectory` (custom auto-memory storage dir), `autoMemoryEnabled` (auto-memory on/off, default `true`), `availableModels` / `enforceAvailableModels` (restrict selectable models), `axScreenReader` (screen-reader-friendly output), `fastMode` (faster Opus output, default `false`), `language` (response language preference), `cleanupPeriodDays` (session file retention, default 30), `disableBundledSkills` (hide bundled skills like `/code-review`, `/loop`).

### Skills

Skills use the official nested layout: `skills/<name>/SKILL.md`. Custom commands were merged into skills upstream — a flat `commands/foo.md` still works but is the legacy form, so this repo keeps everything under `skills/` (the former `commands/` directory was migrated here). Two kinds live in `skills/`:

**Domain-knowledge skills** — Claude loads these automatically when the conversation matches their `description:`:

- `git-workflow`: Conventional commits, branch naming, PR size, release workflow guidance, and complex operations (rebase, bisect, reflog recovery)
- `testing-patterns`: AAA pattern, factories, mocks, coverage, and test organization
- `security-patterns`: Input validation, JWT, CSRF, auth, secrets, and security-sensitive routes
- `api-design`: REST conventions, status codes, pagination, schemas, and error formats
- `django-patterns`: Fat models, managers, query optimization, signals, migrations, and admin patterns
- `docker-patterns`: Multi-stage builds, layer caching, Compose files, and container security
- `infrastructure`: Terraform modules, Kubernetes resources, Helm charts, and deployment configuration
- `root-cause-analysis`: Guides incident and bug investigations toward root causes over symptom-level bandaids
- `project-setup`: Applying this config's tooling to a project — `setup-project.sh`, `install-tooling.sh`, the `--hooks`/`--tooling` caveat, and the new-repo bootstrap runbook

**Workflow skills** — invoked as `/<name>`; those with trigger-rich descriptions can also be auto-invoked by Claude when the conversation calls for them:

- `commit` (`/commit`): Analyze staged changes and write a conventional commit message
- `pr` (`/pr`): Create a pull request with a well-crafted description
- `hotfix` (`/hotfix`): Create a hotfix branch with a minimal fix, targeted tests, and PR
- `tdd` (`/tdd`): Guide a TDD workflow (Red-Green-Refactor) for a feature or change
- `adr` (`/adr`): Create an Architecture Decision Record (Nygard format)
- `standup` (`/standup`): Summarize recent work activity across Git, GitHub, and Jira — **schedulable** (see Automation)
- `eow-review` (`/eow-review`): End-of-week review notes — **schedulable** (see Automation)
- `status` (`/status`, user-only): Append a quick status update to today's daily log
- `refinement` (`/refinement`, user-only): Technical analysis for backlog refinement meetings
- `later` (`/later`, user-only): Create a Later backlog item (Learn/Research/Do/Read)

The three user-only skills set `disable-model-invocation: true`. **Scheduling constraint**: that flag also prevents a skill from running when a scheduled task fires with the skill as its prompt (v2.1.196+) — `/standup` and `/eow-review` deliberately omit it so scheduled routines can run them.

### Rules

Rules are path-scoped code style enforcement files in `rules/`. They use `paths` frontmatter for granular file matching.

Available rules:

- `python-style.md`: Naming, error handling, imports, type hints (`**/*.py`)
- `typescript-style.md`: Naming, error handling, type usage, plus a React-specific section for `.tsx` (`**/*.ts`, `**/*.tsx`)

### Settings Files: Two Purposes

This repo manages three distinct settings files:

| File                             | Purpose                                                             | Distribution                                            | Source                            |
| -------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------- |
| `settings.json`                  | **Universal** plugin enablement + hooks (no external auth required) | **Symlinked** from repo root                            | Canonical copy in repo            |
| `settings.personal.json.example` | Opt-in fragment for plugins requiring external accounts/auth        | **Copied** by hand into `~/.claude/settings.local.json` | Template in repo                  |
| `settings.local.json`            | Bash permissions + any personal plugin opt-ins                      | **Generated** per-project + hand-edited globally        | Merged from `settings-templates/` |

**Why split universal vs personal plugins?** The repo is consumable by anyone (via plugin install or symlink). Auto-enabling Notion/Figma/etc. for someone who has no account or doesn't use those tools is surprising. `settings.json` carries only plugins that work without external accounts (github, pr-review-toolkit, feature-dev, code-simplifier, playwright, pyright-lsp, typescript-lsp, document-skills). Personal opt-ins (`figma`, `frontend-design`) live in `settings.personal.json.example` and are merged into the maintainer's `~/.claude/settings.local.json` by hand.

**Note on merge semantics**: Claude Code's documented behavior for `enabledPlugins` across settings layers is not explicitly spelled out in the docs (the example given covers scalars, where the higher-precedence layer wins). If you observe universal plugins being shadowed when the example is active, include the universal list alongside the personal entries in your local file. See [Claude Code settings docs](https://code.claude.com/docs/en/settings.md) for precedence rules.

### Settings Template System

Templates in `settings-templates/` are JSON files defining Claude Code permissions. The merge system:

1. Always includes `base.json` first (git, gh CLI, file operations)
2. Adds requested templates in order (django, react, etc.)
3. Merges permissions with precedence: **deny > allow**
4. Outputs combined `settings.local.json`

Available templates (14 total):

- **Base**: `base.json` (always included)
- **Backend stacks**: `django.json`, `fastapi.json`, `go.json`, `java.json`, `node.json`, `python.json`, `rust.json`
- **Frontend stacks**: `nextjs.json`, `react.json`
- **Platform / infra**: `aws.json`, `docker.json`, `kubernetes.json`, `terraform.json`

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

### MCP Template System

MCP templates in `mcp-templates/` define MCP server configurations per project type. The merge system:

1. Always includes `base.json` first (empty by default — MCP is opt-in)
2. Adds MCP servers from matching type templates
3. Outputs combined `.mcp.json` in the project root

Available MCP templates:

- `base.json`: Empty (MCP servers are opt-in)
- `django.json` (`_version: 2`): PostgreSQL MCP server (`@modelcontextprotocol/server-postgres`)
- `nextjs.json`: PostgreSQL MCP server
- `fastapi.json`: PostgreSQL MCP server
- `python.json` (`_version: 1`): SQLite MCP server (`mcp-server-sqlite-npx`) for generic Python local dev
- `node.json` (`_version: 1`): SQLite MCP server (`mcp-server-sqlite-npx`) for generic Node local dev
- `aws.json` (`_version: 1`): AWS Infrastructure-as-Code MCP server (`awslabs.aws-iac-mcp-server`) for CloudFormation/CDK validation, `cfn-guard` compliance, and deployment troubleshooting. Runs via `uvx` (Python/PyPI), not `npx` — needs the `uv` package manager plus AWS credentials (`AWS_PROFILE`/`AWS_REGION`). The deprecated `awslabs.terraform-mcp-server` is deliberately excluded; HashiCorp's official Terraform MCP server has superseded it.

Stacks without an MCP template (Go, Rust, Java, Kubernetes, Terraform) fall through to `base.json` (empty); add MCP servers manually in the project's generated `.mcp.json` when needed. The frameworks with web/DB context default to PostgreSQL; generic Python/Node templates use SQLite because there's no shared external DB assumption. The `aws` template is the lone infra MCP server — it's `uvx`-based rather than `npx`-based, so verify against PyPI (confirmed `awslabs.aws-iac-mcp-server` published at template creation time) rather than the npm registry. Verify each template's package before relying on it — versions move (npm search confirmed `mcp-server-sqlite-npx@0.8.0` exists at template creation time).

Playwright is now provided as a first-class plugin (`playwright@claude-plugins-official`,
enabled in `settings.json`), not via an MCP template, so React projects do not
generate a `.mcp.json` from this repo by default.

**Environment Variables**: Variables like `${DATABASE_URL}` are expanded at Claude Code runtime.
Ensure required variables are set in your shell or `.envrc` before launching Claude Code.

### CLI Scripts

Headless Claude Code scripts in `scripts/cli/` for automation:

- `review-changes.sh`: Review uncommitted changes for bugs, security, quality
- `explain-error.sh`: Pipe errors to Claude for explanation (`cmd 2>&1 | explain-error.sh`)
- `daily-report.sh`: Summarize last 24h of git activity
- `review-pr.sh <number>`: Headless PR review

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
- `description`: When Claude should invoke this agent (include examples)
- `model` (optional): omit to **inherit** the session model (the default, right for deep-reasoning agents); pin `sonnet` for pattern-based cost routing or `haiku` for highly structured / data-plumbing
- `tools` / `disallowedTools` (optional): Allowlist / denylist restricting the agent's tool pool
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
