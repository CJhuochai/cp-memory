# Contributing to CP Memory

## 中文

感谢你关注 CP Memory。这个项目是一个本地优先的 Codex 记忆插件，因此贡献流程重点关注三件事：不要破坏本地数据、不要绕过插件规范、不要把私人记忆提交到仓库。

### 工作流程

1. 从最新 `main` 创建分支。

```powershell
git switch main
git pull
git switch -c feat/your-change
```

2. 根据改动类型选择分支前缀。

- `feat/...`：新功能
- `fix/...`：修复
- `docs/...`：文档
- `release/...`：发布准备

3. 修改前阅读：

- `AGENTS.md`
- `docs/release.md`

4. 文档要求：

- 所有面向用户或维护者的文档必须提供中英双语内容。
- 如果修改 `README.md`，通常也要同步修改 `README.en.md`。
- 如果新增维护流程文档，可以在同一个 Markdown 文件中按“中文 / English”组织。

### 测试

默认测试：

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

涉及安装、hooks、MCP、marketplace、插件清单或打包逻辑时，必须运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

涉及记忆恢复、自动提炼、治理或冲突处理时，建议运行：

```powershell
python tests\personal_memory_benchmark.py
```

### 安全

不要提交：

- 真实 `memory.db`
- 日志文件
- `.env`
- token、密钥、密码
- 私人摘要或真实长期记忆数据
- 本地 Codex 配置文件

项目 `.gitignore` 已经排除了常见本地文件，但提交前仍应检查 `git status`。

### PR 检查清单

- 已从分支开发，而不是直接改 `main`
- 已运行相关测试
- 已更新中英文文档
- 没有提交私人数据或本地环境文件
- 如果发布版本，已按 `docs/release.md` 更新版本号和 tag

## English

Thanks for your interest in CP Memory. This project is a local-first Codex memory plugin, so contributions focus on three things: do not damage local data, do not bypass plugin conventions, and do not commit private memory data.

### Workflow

1. Create a branch from the latest `main`.

```powershell
git switch main
git pull
git switch -c feat/your-change
```

2. Choose a branch prefix based on the change type.

- `feat/...`: new feature
- `fix/...`: bug fix
- `docs/...`: documentation
- `release/...`: release preparation

3. Before changing code, read:

- `AGENTS.md`
- `docs/release.md`

4. Documentation rule:

- All user-facing or maintainer-facing documentation must include both Chinese and English content.
- If you update `README.md`, usually update `README.en.md` as well.
- If you add maintainer documentation, you may keep Chinese and English sections in the same Markdown file.

### Tests

Default test suite:

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

For installer, hooks, MCP, marketplace, plugin manifest, or packaging changes, also run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

For memory restore, automatic extraction, governance, or conflict handling changes, consider running:

```powershell
python tests\personal_memory_benchmark.py
```

### Safety

Do not commit:

- Real `memory.db` files
- Logs
- `.env`
- Tokens, secrets, or passwords
- Private summaries or real long-term memory data
- Local Codex configuration files

The project `.gitignore` excludes common local files, but still check `git status` before committing.

### PR Checklist

- Developed on a branch instead of directly on `main`
- Ran the relevant tests
- Updated Chinese and English documentation
- Did not commit private data or local environment files
- For releases, updated version and tag according to `docs/release.md`
