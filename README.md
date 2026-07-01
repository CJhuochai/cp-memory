<p align="center">
  <img src="assets/logo.png" width="140" alt="CP Memory logo">
</p>

<h1 align="center">CP Memory</h1>

<p align="center">
  Codex 的本地优先、可审阅记忆层：记住重要上下文，解释为什么记住，并允许安全纠错。
</p>

<p align="center">
  中文 | <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green.svg"></a>
  <img alt="Local first" src="https://img.shields.io/badge/memory-local--first-blue.svg">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-black.svg">
</p>

---

CP Memory 是一个面向 Codex 的本地记忆插件。它把事实、偏好、持续事项、事件、决策和会话检查点保存到本地 SQLite 数据库，再通过 MCP 工具和生命周期 hooks 在合适的时机恢复上下文。

它的重点不是“尽可能多地记住”，而是“长期使用后仍然可信”：可解释、可审阅、可纠错、可治理。

![CP Memory recall demo](assets/demo-recall.svg)

## 为什么用它

- 本地优先：默认数据保存在 `~/.cp-memory/memory.db`。
- Codex 原生：同时支持 plugin manifest、MCP server、skills 和 lifecycle hooks。
- 长期个人记忆：支持画像、偏好、关系、持续事项、事件和稳定决策。
- 可治理：支持冲突检测、纠错历史、复核队列和治理报告。
- 保守提炼：只从明确表达中提炼长期记忆，降低“乱记”和上下文污染。

## 30 秒例子

你告诉 Codex：

```text
记住一下：这个项目的发布流程必须先开分支、跑测试、再通过 PR 合并。
```

之后的新会话里，你可以问：

```text
我们这个插件的发布规则是什么？
```

CP Memory 会优先从本地主库恢复相关记忆，并让 Codex 按这条规则工作。如果记错了，你可以把那条记忆标记为错误、过期，或写入新的纠正版本。

更多匿名化示例见 [docs/examples.md](docs/examples.md)。

## 安装

推荐通过 GitHub marketplace 安装：

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin add cp-memory@cp-memory
```

安装后重启 Codex。如果 Codex 提示信任 hooks，请在 hooks 页面确认 CP Memory 的生命周期 hooks。

## 安全边界

- 不要提交真实 `memory.db`、日志、私人摘要或环境文件。
- 自动提炼默认保守，生成的记忆可以审阅、纠正、标记过期或标记错误。
- 新会话会在发现待审阅记忆时提示用户，但不会自动删除或自动解决冲突。
- 每周维护只做健康检查、治理预检和低风险过期清理；长期个人记忆、任务和决策默认受保护。
- 示例和截图均使用脱敏内容，不需要暴露真实记忆库。

## 对比

如果你已经看过其他 memory 项目，可以直接看 [docs/comparison.md](docs/comparison.md)。CP Memory 的主要差异是：Codex 生命周期集成 + 记忆治理，而不是只做存储和搜索。

## 路线图

后续方向见 [docs/roadmap.md](docs/roadmap.md)。路线图会优先保持本地优先、可解释、可纠错和隐私安全。

## 本地开发

普通用户不需要运行 `install.ps1`。它主要用于本地开发、刷新 personal marketplace 缓存，以及迁移旧版本留下的全局 hook 接线。

运行测试：

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

隔离验证安装脚本，不会触碰真实 Codex 配置：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

## License

MIT
