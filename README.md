<p align="center">
  <img src="assets/logo.png" width="140" alt="CP Memory logo">
</p>

<h1 align="center">CP Memory</h1>

<p align="center">
  本地优先的 Codex 记忆插件，让助手记住重要上下文，并且可以审阅、解释和纠错。
</p>

<p align="center">
  中文 | <a href="README.en.md">English</a>
</p>

---

CP Memory 是一个面向 Codex 的本地优先个人记忆插件。它把事实、对话摘要、个人偏好、关系、持续事项、决策和检查点保存到本地 SQLite 数据库，再通过 MCP 工具和生命周期 hooks 在合适的时机恢复上下文。

它的目标不是把记忆做成一个复杂平台，而是提供一个能长期跟随个人工作的助手记忆层：本地保存、可解释、可审阅、可纠错。

## 亮点

- 本地优先：默认数据位于 `~/.cp-memory/memory.db`。
- 插件原生：支持 Codex plugin、MCP server、skills 和 lifecycle hooks。
- 个人记忆：支持身份画像、偏好、关系、持续事项、事件、稳定立场/决策。
- 可治理：支持冲突检测、纠错历史、复核队列和治理报告。
- 保守提炼：只在明确表达中提炼长期记忆，避免把实现说明误当偏好。
- 跨平台安装：推荐通过 GitHub marketplace 安装，Windows/macOS/Linux 都可走插件安装链路。

## 安装

推荐使用 GitHub marketplace 安装：

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin add cp-memory@cp-memory
```

安装后重启 Codex。如果 Codex 提示信任 hooks，请在 hooks 页面确认 CP Memory 的生命周期 hooks。

## 本地开发安装

普通用户不需要运行 `install.ps1`。它主要用于本地开发、刷新 personal marketplace 缓存，以及迁移旧版本留下的全局 hook 接线。

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

目前这个脚本是 Windows 优先；通过 GitHub marketplace 安装不依赖它。

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

## 安全边界

CP Memory 会保存本地助手记忆。不要提交真实的 `memory.db`、日志、私人摘要或环境文件。项目内置的 `.gitignore` 已排除常见数据库、缓存和环境文件。

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
