# CP Memory Release Guide

## 中文

本文档说明 CP Memory 的维护和发布流程。`main` 分支代表公开稳定版，所有升级都应从分支开始。

### 分支策略

- `main`：公开稳定版
- `feat/...`：新功能
- `fix/...`：修复
- `docs/...`：文档
- `release/...`：发布准备

不要直接在 `main` 上修改文件。

### 开始开发

```powershell
git switch main
git pull
git switch -c feat/your-change
```

### 发布前检查

默认测试：

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

如果改动涉及安装、hooks、MCP、marketplace、插件清单或打包逻辑：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

如果改动涉及记忆恢复、自动提炼、治理或冲突处理：

```powershell
python tests\personal_memory_benchmark.py
```

### 版本号

版本号位于：

```text
.codex-plugin/plugin.json
```

建议遵循语义化版本：

- 补丁修复：`1.4.0` -> `1.4.1`
- 向后兼容的新功能：`1.4.0` -> `1.5.0`
- 破坏性变更：`1.x.x` -> `2.0.0`

### 合并和发布

1. 确认所有测试通过。
2. 创建 PR，将分支合并到 `main`。
3. 合并后同步本地 `main`。

```powershell
git switch main
git pull
```

4. 打版本 tag。

```powershell
git tag vX.Y.Z
git push origin main --tags
```

5. 通过 PyPI Trusted Publisher 发布标准 Python 包。

首次发布时，在 PyPI 创建待定发布者：项目名 `cp-memory-mcp`、Owner `CJhuochai`、仓库 `cp-memory`、工作流 `publish-pypi.yml`，Environment 留空。配置完成后，在 GitHub Actions 的 `Publish Python package` 工作流中从 `main` 手动运行；后续 GitHub Release 发布会自动触发同一工作流。仓库不保存长期 PyPI Token。

6. 验证远程 marketplace。

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin list
```

### 文档发布规则

- 所有面向用户或维护者的文档必须提供中英双语内容。
- README 中文版和英文版应保持同等信息量。
- 发布说明中应包含验证命令和迁移注意事项。

## English

This document describes the CP Memory maintenance and release process. The `main` branch represents the public stable version, and every upgrade should start from a branch.

### Branch Strategy

- `main`: public stable version
- `feat/...`: new feature
- `fix/...`: bug fix
- `docs/...`: documentation
- `release/...`: release preparation

Do not modify files directly on `main`.

### Start Development

```powershell
git switch main
git pull
git switch -c feat/your-change
```

### Pre-Release Checks

Default test suite:

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

For installer, hooks, MCP, marketplace, plugin manifest, or packaging changes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

For memory restore, automatic extraction, governance, or conflict handling changes:

```powershell
python tests\personal_memory_benchmark.py
```

### Versioning

The version lives in:

```text
.codex-plugin/plugin.json
```

Recommended semantic versioning:

- Patch fix: `1.4.0` -> `1.4.1`
- Backward-compatible feature: `1.4.0` -> `1.5.0`
- Breaking change: `1.x.x` -> `2.0.0`

### Merge And Release

1. Confirm all required tests pass.
2. Open a PR and merge the branch into `main`.
3. Sync local `main`.

```powershell
git switch main
git pull
```

4. Create a release tag.

```powershell
git tag vX.Y.Z
git push origin main --tags
```

5. Publish the standard Python package through PyPI Trusted Publishing.

For the first release, create a pending publisher on PyPI with project name `cp-memory-mcp`, owner `CJhuochai`, repository `cp-memory`, workflow `publish-pypi.yml`, and a blank Environment. Then manually run the `Publish Python package` GitHub Actions workflow from `main`. Future GitHub Release publications trigger the same workflow automatically. The repository stores no long-lived PyPI token.

6. Verify the remote marketplace.

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin list
```

### Documentation Release Rule

- All user-facing or maintainer-facing documentation must include both Chinese and English content.
- Chinese and English READMEs should carry equivalent information.
- Release notes should include verification commands and migration notes.
