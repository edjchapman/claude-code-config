# Changelog

## [1.15.0](https://github.com/edjchapman/claude-code-config/compare/1.14.0...1.15.0) (2026-08-19)


### Features

* **scripts:** hooks/hooks.json becomes the single source of truth ([#111](https://github.com/edjchapman/claude-code-config/issues/111)) ([#117](https://github.com/edjchapman/claude-code-config/issues/117)) ([0ad4a4f](https://github.com/edjchapman/claude-code-config/commit/0ad4a4fe0bdfc096af6f2bab872e78a403f2b728))

## [1.14.0](https://github.com/edjchapman/claude-code-config/compare/1.13.0...1.14.0) (2026-08-11)


### Features

* **settings:** disable session-URL attribution on commits and PRs ([#107](https://github.com/edjchapman/claude-code-config/issues/107)) ([0b7ba28](https://github.com/edjchapman/claude-code-config/commit/0b7ba28f556985385823e5f1e21c6850831c7292))

## [1.13.0](https://github.com/edjchapman/claude-code-config/compare/1.12.0...1.13.0) (2026-07-29)


### Features

* **hooks:** make compaction state survive via a PostCompact restore hook ([#95](https://github.com/edjchapman/claude-code-config/issues/95)) ([7c4255a](https://github.com/edjchapman/claude-code-config/commit/7c4255afd13778f9f149b3687071336292efcbd8))


### Bug Fixes

* **agents,skills:** polish frontmatter, descriptions, and exemplar docs ([#93](https://github.com/edjchapman/claude-code-config/issues/93)) ([c922054](https://github.com/edjchapman/claude-code-config/commit/c92205491230d2ac03af3bb12daf6204102c7878))
* **cli,scripts:** canonical allowedTools + repo-relative aliases + flag deprecated postgres MCP ([#96](https://github.com/edjchapman/claude-code-config/issues/96)) ([97f4a6c](https://github.com/edjchapman/claude-code-config/commit/97f4a6c6f66ad926302736ecc29e44a91754a66c))
* **hooks:** block wiping a system dir in dangerous-cmd-check (follow-up to [#89](https://github.com/edjchapman/claude-code-config/issues/89)) ([#98](https://github.com/edjchapman/claude-code-config/issues/98)) ([f963159](https://github.com/edjchapman/claude-code-config/commit/f96315982d2772b056d9947590db913ba68541f1))
* **hooks:** bound the failure log + timeout-guard the status line ([#94](https://github.com/edjchapman/claude-code-config/issues/94)) ([f266712](https://github.com/edjchapman/claude-code-config/commit/f266712362c2667d7bfa84c411f1e5c98db09bf1))
* **hooks:** read tool payloads from stdin, not unset CLAUDE_* env vars ([#89](https://github.com/edjchapman/claude-code-config/issues/89)) ([b455f23](https://github.com/edjchapman/claude-code-config/commit/b455f23373e6532b329a7740e01080f6d9c553da))
* **hooks:** sweep orphaned pre-compact snapshots in session-end cleanup ([#100](https://github.com/edjchapman/claude-code-config/issues/100)) ([3984efc](https://github.com/edjchapman/claude-code-config/commit/3984efce34b29cee9ff54bef5be1e0396108ca09))
* **settings:** harden template merge + tighten base.json permissions ([#91](https://github.com/edjchapman/claude-code-config/issues/91)) ([6dbee1f](https://github.com/edjchapman/claude-code-config/commit/6dbee1f091f5d86ef28ab8d917695f2d257c6bf7))

## [1.12.0](https://github.com/edjchapman/claude-code-config/compare/1.11.1...1.12.0) (2026-07-22)


### Features

* **agents:** read-only tool pool for plan-mode advisors ([#85](https://github.com/edjchapman/claude-code-config/issues/85)) ([fce5ac2](https://github.com/edjchapman/claude-code-config/commit/fce5ac2e3404745ded844120571be2ca7fd4a89d))
* **settings:** move personal model pin to the personal layer ([#84](https://github.com/edjchapman/claude-code-config/issues/84)) ([bc8d263](https://github.com/edjchapman/claude-code-config/commit/bc8d263d1c047ce880d7b73826744b0003b237f9))

## [1.11.1](https://github.com/edjchapman/claude-code-config/compare/1.11.0...1.11.1) (2026-07-21)


### Bug Fixes

* **scripts:** filter check-mode MCP comparison to existing templates ([#77](https://github.com/edjchapman/claude-code-config/issues/77)) ([8dee2a2](https://github.com/edjchapman/claude-code-config/commit/8dee2a2e0f82dec746d25e03350cd98021cb2a81))

## [1.11.0](https://github.com/edjchapman/claude-code-config/compare/1.10.0...1.11.0) (2026-07-16)


### Features

* **mkdocs:** style layer v2 — dark-palette warm rewrite, WCAG fixes, reading polish ([#69](https://github.com/edjchapman/claude-code-config/issues/69)) ([630df3e](https://github.com/edjchapman/claude-code-config/commit/630df3e20fa6e606db4b2b10a5743eb621f5b762))


### Bug Fixes

* **mkdocs:** style layer v3 — repair mobile block against Material defaults + espresso dark surfaces ([#71](https://github.com/edjchapman/claude-code-config/issues/71)) ([6969dae](https://github.com/edjchapman/claude-code-config/commit/6969dae3816175c258f7738a75fad2d56bef66db))
* **plugin:** add marketplace manifest so /plugin marketplace add resolves ([#72](https://github.com/edjchapman/claude-code-config/issues/72)) ([d5ed8ed](https://github.com/edjchapman/claude-code-config/commit/d5ed8ede425a9541b01702b286341f162acb81af))
* **scripts:** enumerate primitives via git ls-files in docs-drift check ([#74](https://github.com/edjchapman/claude-code-config/issues/74)) ([7ac0325](https://github.com/edjchapman/claude-code-config/commit/7ac032532c521ebba5cc88cbb2afc252cdf3e7fb))

## [1.10.0](https://github.com/edjchapman/claude-code-config/compare/1.9.0...1.10.0) (2026-07-15)


### Features

* **hooks:** desktop notification when Claude needs attention ([#66](https://github.com/edjchapman/claude-code-config/issues/66)) ([1919b09](https://github.com/edjchapman/claude-code-config/commit/1919b09a00b5b123b30b7064f5e673fc8e68dd7d))


### Bug Fixes

* **scripts:** dedupe git-context and merge helpers, harden hooks, tighten validators ([#65](https://github.com/edjchapman/claude-code-config/issues/65)) ([a349653](https://github.com/edjchapman/claude-code-config/commit/a349653642222a99fa2e1f315484ff4b82bc94cb))

## [1.9.0](https://github.com/edjchapman/claude-code-config/compare/1.8.1...1.9.0) (2026-07-14)


### Features

* **tooling:** add shared MkDocs style layer + /mkdocs-style skill ([#57](https://github.com/edjchapman/claude-code-config/issues/57)) ([7acd8e0](https://github.com/edjchapman/claude-code-config/commit/7acd8e0a202912c0ee89322faa295420c3e073fe))

## [1.8.1](https://github.com/edjchapman/claude-code-config/compare/1.8.0...1.8.1) (2026-07-09)


### Bug Fixes

* **skills:** retire the remaining --notion flags (status, pr, refinement) ([#54](https://github.com/edjchapman/claude-code-config/issues/54)) ([c441c2a](https://github.com/edjchapman/claude-code-config/commit/c441c2a58f00eaebb6802413da6702c8282db7e5))

## [1.8.0](https://github.com/edjchapman/claude-code-config/compare/1.7.0...1.8.0) (2026-07-09)


### Features

* modernization sweep — prompt hooks, skills migration, scheduled routines, agent memory ([#50](https://github.com/edjchapman/claude-code-config/issues/50)) ([95fda71](https://github.com/edjchapman/claude-code-config/commit/95fda71db9045eef3e30dbac5e60d4c610520f93))

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
