---
name: run-claude-code-config
description: Run, launch, drive, smoke-test, or verify this claude-code-config repo — fire its hook scripts with real payloads, run the generator and validation gates, and test the global/project installers in a sandbox. Use when asked to run the app, check a change works for real, exercise a hook, or verify an install.
---

# Run claude-code-config

This repo has **no server, no GUI, and no build step**. Its "running app" is three surfaces:

1. **The hook scripts** in `scripts/hooks/` — the harness executes these at runtime with a JSON payload on **stdin**; exit `0` = allow, exit `2` = block, and the block reason must go to **stderr**.
2. **The generator CLI**, `scripts/generate.py`, which owns the generated regions in `README.md`, `docs/architecture.md`, and `settings.json`.
3. **The installers**, `scripts/setup-global.sh` and `scripts/setup-project.sh`.

All three are driven by one script: **`.claude/skills/run-claude-code-config/drive.sh`**.

Paths below are relative to the repo root.

## Prerequisites

Already present on a normal dev box; the driver skips or fails loudly if not.

```bash
python3 --version        # 3.14.7 here; generate.py + the hook JSON parser need it
bash --version           # 5.3.15 (macOS ships bash 3.2 — hooks run under `bash`, not `sh`)
ruff --version           # 0.16.1 — format-on-edit.sh shells out to it
shellcheck --version     # pre-commit runs it at --severity=warning
pre-commit --version
```

There is **no `npm install`** and no `node_modules/` in this repo.

## Run (agent path) — start here

The driver runs everything under a **throwaway `HOME`**, because four hooks write into `$HOME/.claude/` and the installers symlink into it. A driver run can never mutate your real config.

```bash
bash .claude/skills/run-claude-code-config/drive.sh check     # the 3 validation gates
bash .claude/skills/run-claude-code-config/drive.sh hooks     # fire all 10 hooks, assert exits + side effects
bash .claude/skills/run-claude-code-config/drive.sh install   # sandboxed setup-global.sh + setup-project.sh
bash .claude/skills/run-claude-code-config/drive.sh all       # all of the above
```

A clean `all` run reports:

```
== Summary
  pass=32 fail=0 skip=1
```

The one skip is `notify-attention.sh` (fires a real desktop banner). Opt in with `DRIVE_NOTIFY=1`. Add `DRIVE_KEEP=1` to keep the sandbox directory and inspect what the hooks wrote.

### Direct invocation — fire one hook

Most PRs here touch a single hook or a single generator target. To poke one hook in isolation, with its output and exit code shown and `HOME` still sandboxed:

```bash
bash .claude/skills/run-claude-code-config/drive.sh hook session-context.sh '{"source":"startup"}'
bash .claude/skills/run-claude-code-config/drive.sh hook format-on-edit.sh '{"tool_input":{"file_path":"/tmp/x.py"}}'
```

Or call a hook directly — the contract is just JSON on stdin:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash scripts/hooks/dangerous-cmd-check.sh; echo "exit=$?"
```

Read Gotcha 1 before you try that with an actually-dangerous command.

### Generator, one target at a time

```bash
python3 scripts/generate.py --check              # verify only; exit 1 if stale
python3 scripts/generate.py                      # rewrite stale destinations
python3 scripts/generate.py --only readme         # single target: architecture | readme | settings-hooks
python3 scripts/generate.py --root /path/to/copy # operate on a scratch copy
```

## Run (human path)

Installing the config for real — **these write to your actual `~/.claude`**, so don't run them just to "check it works"; that's what `drive.sh install` is for.

```bash
scripts/setup-global.sh          # symlinks agents/ skills/ rules/ into ~/.claude, mirrors settings.json
scripts/setup-project.sh python  # per-project .claude/ in the CWD
```

Or as a plugin: `/plugin marketplace add edjchapman/claude-code-config`, then `/plugin install claude-code-config`.

## Test

The three gates CI runs, in order of speed:

```bash
python3 scripts/generate.py --check       # ~1s
python3 -m unittest discover -s tests     # 40 tests, ~3s
pre-commit run --all-files                # 19 checks, ~40s
```

## Gotchas

1. **This repo's own hook blocks your attempt to test it.** If the config is installed in your session, `dangerous-cmd-check.sh` is live — and it inspects the **command string of every Bash call**, including one that merely carries a dangerous pattern as *test data*. Putting a literal root-wipe inside a JSON payload on a Bash command line gets the whole tool call killed before it runs, with `PreToolUse:Bash hook error: BLOCKED: dangerous command pattern detected`. The fix, which `drive.sh` uses: assemble the fixture from pieces (`printf 'rm -r%s /' 'f'`) so the literal never appears contiguously in any command line. Same reason the driver was created with the Write tool rather than a Bash heredoc.

2. **Four hooks write into `$HOME/.claude/` — always sandbox `HOME`.** `log-tool-failure.sh` → `logs/tool-failures.jsonl`, `pre-compact-state.sh` → `cache/`, `post-compact-restore.sh` reads and **deletes** from `cache/`, `session-end.sh` → `debug/session-log.csv`. Running these bare pollutes your real logs. `HOME=$(mktemp -d)` is enough; tilde expansion follows `$HOME`, so even `setup-global.sh` lands entirely in the sandbox.

3. **A naive sandbox makes `settings-drift-check.sh` a false pass.** It begins `[ -L ~/.claude/agents ] || exit 0` — global-mode detection. In an empty sandbox it exits 0 immediately without running any logic. `drive.sh` plants a `.claude/agents` symlink and a `settings.json` copy in the sandbox so the hook actually executes.

4. **`prettier` is not installed and there is no `node_modules/`.** So `format-on-edit.sh` silently no-ops on `.md`, `.json`, `.ts`, `.css` — it only really formats `.py`, via `ruff`. This is easy to misread as "the hook is broken", and easy to miss because pre-commit's prettier check *does* pass: pre-commit vendors its own prettier in an isolated env that the hook cannot see.

5. **shellcheck runs at `--severity=warning`.** SC2088 (tilde inside a quoted string) **fails the gate**; SC2015 (`A && B || C`) is `info` and is filtered out. Any new shell script — including this driver — must pass. Check with `shellcheck --severity=warning <file>`, not bare `shellcheck`.

6. **`PreCompact` and `PostCompact` are a stateful pair keyed by `session_id`.** `pre-compact-state.sh` writes `~/.claude/cache/precompact-<id>.md`; `post-compact-restore.sh` prints it and then **removes** it. Running restore twice is a silent no-op with exit 0 — not a bug. Fire them in order with a matching `session_id` or you're testing nothing.

7. **`hooks/hooks.json` is the source of truth; the `hooks` key in `settings.json` is generated** (ADR-0001). Hand-editing `settings.json` gets reverted by pre-commit and fails `generate.py --check` in CI. Edit `hooks/hooks.json`.

8. **The login shell is zsh, but the scripts are bash.** Two traps this causes when driving things by hand: `PIPESTATUS` is bash-only (zsh spells it `pipestatus`, so `echo "EXIT=${PIPESTATUS[0]}"` prints empty), and an unmatched glob like `.claude/skills/*/SKILL.md` is a hard error in zsh rather than passing through — probe with `find` instead.

9. **`.claude/` is in `.prettierignore` and `skills/*/SKILL.md` is what the generator globs.** So this skill is neither reflowed by prettier nor picked up by the README/architecture catalogs — adding it needs no regeneration. It *is* still linted by markdownlint.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `PreToolUse:Bash hook error: BLOCKED: dangerous command pattern detected` while testing | Gotcha 1 — your test fixture tripped the live hook. Assemble the string from pieces, or put it in a file written by a non-Bash tool. |
| `drive.sh hooks` → `FAIL file not reformatted — is ruff on PATH?` | `ruff` missing. `command -v ruff`; it lives at `~/.local/bin/ruff` here. The hook also accepts a `.venv/bin/ruff` at the git root. |
| `shellcheck` clean by hand but pre-commit fails | You ran bare `shellcheck`. The gate is `--severity=warning`. |
| `sed: can't read s\|...\|: No such file or directory` | BSD `sed -i ''` arg parsing under zsh. Use `perl -pi -e 's{a}{b}g' file`. |
| `generate.py --check` exits 1 naming a stale file | Run `python3 scripts/generate.py` (no `--check`) to rewrite, then re-check. |
| A hook "does nothing" and exits 0 | Expected for most hooks on an unmatched payload — they read a specific dotted key (e.g. `tool_input.file_path`) and exit 0 when it's absent. Confirm your payload shape against the hook's header comment. |
| Real `~/.claude` changed after a test run | You ran an installer directly instead of `drive.sh install`. Compare with `ls -la ~/.claude \| md5`. |
