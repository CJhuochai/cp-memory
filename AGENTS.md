# CP Memory Agent Rules

## 中文

这些规则适用于所有在本仓库中工作的 Codex/agent 会话。

### 必须遵守

- 不要直接在 `main` 上修改代码、脚本、插件清单或文档。
- 开始任何改动前，先从 `main` 创建分支，例如 `docs/...`、`feat/...`、`fix/...`、`release/...`。
- 修改前先阅读 `CONTRIBUTING.md` 和 `docs/release.md`。
- 所有面向用户或维护者的文档必须提供中英双语内容。
- 修改安装、hooks、MCP、marketplace、插件清单或打包逻辑后，必须运行隔离安装验证。
- 完成前必须运行测试，并在总结中说明验证结果。
- 不要提交真实 `memory.db`、日志、密钥、token、私人摘要或本地环境文件。

### 默认验证

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

涉及安装、hooks、MCP、marketplace 或打包时，还要运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

### 发布边界

- `main` 代表公开稳定版。
- 新功能、修复和文档更新都应通过分支和 PR 合并。
- 发布前更新 `.codex-plugin/plugin.json` 版本号，并按 `docs/release.md` 执行。

## English

These rules apply to every Codex/agent session working in this repository.

### Required

- Do not modify code, scripts, plugin manifests, or documentation directly on `main`.
- Before any change, create a branch from `main`, such as `docs/...`, `feat/...`, `fix/...`, or `release/...`.
- Read `CONTRIBUTING.md` and `docs/release.md` before implementation.
- All user-facing or maintainer-facing documentation must include both Chinese and English content.
- After changing installer, hooks, MCP, marketplace, plugin manifest, or packaging logic, run the isolated installer validation.
- Run tests before completion and report the verification results.
- Do not commit real `memory.db` files, logs, secrets, tokens, private summaries, or local environment files.

### Default Verification

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

For installer, hooks, MCP, marketplace, or packaging changes, also run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

### Release Boundary

- `main` represents the public stable version.
- Features, fixes, and documentation updates should be merged through branches and PRs.
- Before release, update the version in `.codex-plugin/plugin.json` and follow `docs/release.md`.
