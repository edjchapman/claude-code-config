# Changelog

## [0.2.0](https://github.com/edjchapman/claude-code-config/compare/v0.1.0...v0.2.0) (2026-06-01)


### Features

* add career adviser agent and update documentation ([15fc495](https://github.com/edjchapman/claude-code-config/commit/15fc495fc759f938e11d3c8d51d63a06b90404ff))
* add CLI scripts, MCP templates, GitHub Actions, macOS automation, and keybindings ([cb7f70a](https://github.com/edjchapman/claude-code-config/commit/cb7f70a78f5afaca57e47325ae3561f2bf351552))
* add content reviewer agent and update README ([43a37c1](https://github.com/edjchapman/claude-code-config/commit/43a37c16d3103e8969fb90f74c33b71fd0ed8db1))
* add repo housekeeping (templates, pre-commit, CI lints, release-please) ([#14](https://github.com/edjchapman/claude-code-config/issues/14)) ([411dce5](https://github.com/edjchapman/claude-code-config/commit/411dce5bcc0f045a84848e1fb3b8a30753127754))
* add script setup-global.sh to Claude permissions ([8b4fac3](https://github.com/edjchapman/claude-code-config/commit/8b4fac32a0d3e363f3c37d4ec02149834a9b3bee))
* **agents:** add orchestrator agents for multi-phase workflows ([bf6b6b3](https://github.com/edjchapman/claude-code-config/commit/bf6b6b3870478c0898f3625efabafc9e82bd2113))
* allow git commit in Claude permissions ([6e827de](https://github.com/edjchapman/claude-code-config/commit/6e827deda1849812e87d75cd46a223d7d3f494b3))
* **ci:** add pre-commit hooks and enhanced GitHub workflow ([4f04f3f](https://github.com/edjchapman/claude-code-config/commit/4f04f3fa5933a10f6cd6c59905671a7d2543bd8b))
* **commands:** add /scope command for task boundary definition ([5a785c2](https://github.com/edjchapman/claude-code-config/commit/5a785c2315d9bacf5bae52b3f8dbd29014a1c735))
* **commands:** add /ship-it command for end-to-end shipping workflow ([e1729e7](https://github.com/edjchapman/claude-code-config/commit/e1729e76dcbee50743ffb46b1824ff4985d370ab))
* **commands:** add /status, --notion flag, session-end logging ([#15](https://github.com/edjchapman/claude-code-config/issues/15)) ([5c943df](https://github.com/edjchapman/claude-code-config/commit/5c943df624cbe22fa7dcc8b708576545606be988))
* **commands:** add `/later` command for personal backlog management ([9229e6b](https://github.com/edjchapman/claude-code-config/commit/9229e6bc8bed34c19bda830cc0a106e8dccb5665))
* **commands:** add refinement command for backlog analysis ([91b8555](https://github.com/edjchapman/claude-code-config/commit/91b85554f513da1bacc448348ecfbc1e8d46ccc5))
* **commands:** enhance /standup with Jira, Notion, Slack, and team activity ([#1](https://github.com/edjchapman/claude-code-config/issues/1)) ([6ac54e5](https://github.com/edjchapman/claude-code-config/commit/6ac54e5f99521185fc9c1a5ea9bbd98a2c37941f))
* **commands:** overhaul format-release-notes with Slack, Notion, and GitHub publishing ([34e6ad9](https://github.com/edjchapman/claude-code-config/commit/34e6ad9894234218c1eaeede64945c3d614faf7e))
* comprehensive Claude Code config improvements ([#2](https://github.com/edjchapman/claude-code-config/issues/2)) ([eef5fb5](https://github.com/edjchapman/claude-code-config/commit/eef5fb5696ad757e4754893d8b191c38b53e64b0))
* **configuration:** add Python3 allowlist & settings schema reference ([5ecc427](https://github.com/edjchapman/claude-code-config/commit/5ecc4278aa722a8dd65b3e20bac9edca8d6ba8b6))
* enhance setup-project.sh and add .claude local configuration ([1ea8779](https://github.com/edjchapman/claude-code-config/commit/1ea877982b4276aaed2b331755ad67750f9d5180))
* expand settings and add GitHub Actions for changelog, issue triage, and PR review ([5df4c56](https://github.com/edjchapman/claude-code-config/commit/5df4c56802b4597b2eb9fd67632257f9b4cadd4e))
* introduce rules for scoped code style enforcement and enhanced setup ([23c7dbb](https://github.com/edjchapman/claude-code-config/commit/23c7dbb31d49028cecc995b391eb96ce3042eb7e))
* modernize config (WS3-WS7) — skills migration, new settings, MCP parity, plugin packaging ([#13](https://github.com/edjchapman/claude-code-config/issues/13)) ([765f2d4](https://github.com/edjchapman/claude-code-config/commit/765f2d42cfec4ab882154c0c88cd085f6b242b2c))
* **project-configs:** add clarion-app CLAUDE.md backup ([bfcd25a](https://github.com/edjchapman/claude-code-config/commit/bfcd25a19e80110552b1b5d074a6ff10190aba61))
* **scripts:** add --status, --dry-run options and improve --check ([ffbcb58](https://github.com/edjchapman/claude-code-config/commit/ffbcb5883a324f4b16194feebe2d812d8c270e19))
* **scripts:** add "all" option to setup-project.sh for all templates ([7743066](https://github.com/edjchapman/claude-code-config/commit/7743066606f16f19f039ed6f0618bd1dfd9c8127))
* **settings:** add "model" field to settings.json configuration ([b7c9b19](https://github.com/edjchapman/claude-code-config/commit/b7c9b19a4f768e20949091553f4b078907e928c9))
* **settings:** add customizable hooks for session, tool usage, and notifications ([4638cb8](https://github.com/edjchapman/claude-code-config/commit/4638cb84030a5e0398d8b5eeb0502380f6ea0aaf))
* **settings:** add disabled-by-default sandbox scaffolding ([#6](https://github.com/edjchapman/claude-code-config/issues/6)) ([997cb71](https://github.com/edjchapman/claude-code-config/commit/997cb712e65ed2150b63497c9dbdd27b4e3af874))
* **settings:** disable Claude commit/PR attribution ([#5](https://github.com/edjchapman/claude-code-config/issues/5)) ([583ec9c](https://github.com/edjchapman/claude-code-config/commit/583ec9c7402ca365e9f06aea2fae936d73f44500))
* **settings:** expand allowlist and add CI validation workflow ([5f75b17](https://github.com/edjchapman/claude-code-config/commit/5f75b17c279803799fd5774e15d7dfa29094d996))
* **settings:** extend allowlist with additional Bash commands ([41e72e3](https://github.com/edjchapman/claude-code-config/commit/41e72e3eb14e7e865555d7b117d4048f8408989f))
* **skills:** add root-cause-analysis skill for Python bug fixes ([7e69061](https://github.com/edjchapman/claude-code-config/commit/7e69061b17551b13b3b3a777d3adf65ed793b7d7))
* **symlinks:** add global settings.json symlinking ([4be35d6](https://github.com/edjchapman/claude-code-config/commit/4be35d6039af048d2d2bd238b85863209685ffa5))
* update Django review guidelines, hook scripts, and skill matching ([b61c736](https://github.com/edjchapman/claude-code-config/commit/b61c736b2e37751e8bc8f6ed247d090237ee83f5))


### Bug Fixes

* address code review issues in feature expansion implementation ([dd898b9](https://github.com/edjchapman/claude-code-config/commit/dd898b9b8a87c0cd2663c7b7787c00460ccb8c5f))
* **hooks:** convert matcher format from object to string ([d411154](https://github.com/edjchapman/claude-code-config/commit/d411154c751c329c47ea161fc787b6128547cdd1))
* **hooks:** use natural language in Stop hook prompt ([4d3f53d](https://github.com/edjchapman/claude-code-config/commit/4d3f53df4cb8ef2d87db1258a89984012229347e))
* **scripts:** resolve prettier from git root and gate MCP preview output ([#10](https://github.com/edjchapman/claude-code-config/issues/10)) ([2687d02](https://github.com/edjchapman/claude-code-config/commit/2687d0264f255a8c421507a1a91770d43a138db9))
* **settings:** refine prompt text for hooks validation ([c3ac63d](https://github.com/edjchapman/claude-code-config/commit/c3ac63d9595ff2f27d2862029fc80e1b0143a4df))
* **settings:** update hooks to new matcher-based format ([ac116f2](https://github.com/edjchapman/claude-code-config/commit/ac116f20869ae39cc9524a7ed50eae3d985f5628))
