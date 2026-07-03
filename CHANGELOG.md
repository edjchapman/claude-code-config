# Changelog

## [1.7.0](https://github.com/edjchapman/claude-code-config/compare/1.6.0...1.7.0) (2026-06-26)

### Features

* **templates:** add AWS IaC MCP + permission template ([#37](https://github.com/edjchapman/claude-code-config/issues/37)) ([ffc46c8](https://github.com/edjchapman/claude-code-config/commit/ffc46c8e801e00b5a1d368f67e65cafabf6539f2))

## [1.6.0](https://github.com/edjchapman/claude-code-config/compare/1.5.0...1.6.0) (2026-06-25)

### Features

* **tooling:** add Claude-on-web bootstrap to the --tooling payload ([#38](https://github.com/edjchapman/claude-code-config/issues/38)) ([aa21d1f](https://github.com/edjchapman/claude-code-config/commit/aa21d1f9adac8f6e6030b1895969a40d00a125ef))

## [1.5.0](https://github.com/edjchapman/claude-code-config/compare/1.4.0...1.5.0) (2026-06-25)

### Features

* **scripts:** add setup-project --tooling to vendor a project quality-gate layer ([#33](https://github.com/edjchapman/claude-code-config/issues/33)) ([220082d](https://github.com/edjchapman/claude-code-config/commit/220082d7f339ab80bf81c3d5fe314c2309392012))
* **settings:** disable Claude git attribution on commits and PRs ([#35](https://github.com/edjchapman/claude-code-config/issues/35)) ([f9b3147](https://github.com/edjchapman/claude-code-config/commit/f9b3147cee69813615f547afd6d35a38b77f8190))

### Bug Fixes

* **tooling:** address code-review follow-ups for setup-project --tooling ([#34](https://github.com/edjchapman/claude-code-config/issues/34)) ([d23aa54](https://github.com/edjchapman/claude-code-config/commit/d23aa54a422cb77ac910c84d2b7fa8a4fd0a4cca))

## [1.4.0](https://github.com/edjchapman/claude-code-config/compare/1.3.0...1.4.0) (2026-06-17)

### Features

* **home:** add global CLAUDE.md and symlink it from ~/.claude/ ([34cb72e](https://github.com/edjchapman/claude-code-config/commit/34cb72e394cca2c6ca1611e8ec4febf4e827038e))

## [1.3.0](https://github.com/edjchapman/claude-code-config/compare/1.2.0...1.3.0) (2026-06-06)

### Features

* add repo housekeeping (templates, pre-commit, CI lints, release-please) ([#14](https://github.com/edjchapman/claude-code-config/issues/14)) ([411dce5](https://github.com/edjchapman/claude-code-config/commit/411dce5bcc0f045a84848e1fb3b8a30753127754))
* **commands:** add /status, --notion flag, session-end logging ([#15](https://github.com/edjchapman/claude-code-config/issues/15)) ([5c943df](https://github.com/edjchapman/claude-code-config/commit/5c943df624cbe22fa7dcc8b708576545606be988))
* modernize config (WS3-WS7) — skills migration, new settings, MCP parity, plugin packaging ([#13](https://github.com/edjchapman/claude-code-config/issues/13)) ([765f2d4](https://github.com/edjchapman/claude-code-config/commit/765f2d42cfec4ab882154c0c88cd085f6b242b2c))

### Bug Fixes

* **ci:** exclude auto-generated CHANGELOG.md from markdownlint ([#26](https://github.com/edjchapman/claude-code-config/issues/26)) ([f3265f8](https://github.com/edjchapman/claude-code-config/commit/f3265f8445b7d109839d20cb7f77d675a48e7710))
* **ci:** exclude CHANGELOG.md via markdownlint-cli2 globs negation ([#27](https://github.com/edjchapman/claude-code-config/issues/27)) ([a2ea73f](https://github.com/edjchapman/claude-code-config/commit/a2ea73ff36678f789b0f0295a103aca259ac2e60))
* **release-please:** align manifest with actual release history (1.2.0) ([#23](https://github.com/edjchapman/claude-code-config/issues/23)) ([e620767](https://github.com/edjchapman/claude-code-config/commit/e620767fe0641eb44981b05892345f5b30cea2ee))
