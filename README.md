# CP Memory

中文 | [English](README.en.md)

CP Memory 是一个面向 Codex 的本地优先记忆插件。它把事实、对话摘要、个人记忆、决策、检查点和审计关系存到本地 SQLite 数据库里，再通过 MCP 工具和生命周期 hooks 在合适的时机恢复上下文。

这个插件的目标不是做一个大平台，而是做一个可以长期跟随个人工作的助手记忆系统：本地保存、可解释、可审阅、可纠错。

## 功能

- 默认使用本地 SQLite，数据位于 `~/.cp-memory/memory.db`。
- 支持 Codex 插件元数据、skills、生命周期 hooks 和 MCP server。
- 支持六类个人记忆模型：身份画像、偏好、关系、持续事项、事件、稳定立场/决策。
- 在对话结束时进行保守的自动提炼。
- 支持记忆审阅、冲突检测、纠错历史和治理报告。
- 可选的每周维护自动化，用于健康检查和清理预览。

## 要求

- 支持插件的 Codex。
- Python 3.10 或更高版本。
- 如果使用内置安装脚本，需要 Windows PowerShell。

## 从 GitHub 安装

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin add cp-memory@cp-memory
```

安装后重启 Codex。如果 Codex 要求信任 hooks，请在 hooks 页面确认 CP Memory 的生命周期 hooks。

## 本地安装

在本地仓库目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

安装脚本会把插件登记到 personal marketplace，刷新本地插件缓存，启用插件，创建每周维护自动化，并清理旧版本留下的全局 hook 接线。

## 配置

默认数据目录：

```text
~/.cp-memory/memory.db
```

可以通过环境变量覆盖路径：

```text
CP_MEMORY_HOME
CP_MEMORY_DB_PATH
CP_MEMORY_PLUGIN_HOME
CP_MEMORY_OLD_HOME
```

## 安全说明

CP Memory 会保存本地助手记忆。不要把真实的 `memory.db`、日志、私人摘要或环境文件提交到仓库。项目内置的 `.gitignore` 已排除常见数据库、缓存和环境文件。

自动提炼默认很保守。提炼出的记忆可以被审阅、纠正、标记为过期，或标记为错误。

## 开发

运行测试：

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

运行较完整的基准式检查：

```powershell
python tests\personal_memory_benchmark.py
```

## 许可证

MIT
