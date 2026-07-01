# CP Memory Comparison

## 中文

CP Memory 和很多 memory 项目一样使用本地存储，但它的核心定位不是“又一个 SQLite 记忆库”，而是 Codex 的可治理个人记忆层。

| 维度 | 常见本地 memory 项目 | CP Memory |
| --- | --- | --- |
| 主要目标 | 存储和搜索事实、笔记或会话片段 | 在 Codex 工作流中恢复可信上下文 |
| 集成方式 | 通常以 MCP server 为主 | Codex plugin + MCP server + skills + lifecycle hooks |
| 记忆模型 | 多为通用 key/value、文档或图谱 | 画像、偏好、关系、持续事项、事件、稳定决策 |
| 自动提炼 | 有些项目支持，但通常偏宽松 | 默认保守，只从明确表达中提炼 |
| 纠错能力 | 常见做法是更新或删除 | 支持 wrong/stale、纠错历史和解释 |
| 治理能力 | 通常较少 | 冲突检测、复核队列、治理报告、清理预案 |
| 隐私边界 | 本地优先项目通常较好 | 本地优先，并明确禁止提交真实记忆库和私人摘要 |

## 适合谁

CP Memory 更适合：

- 长期使用 Codex 做项目开发的人
- 经常跨会话恢复项目规则、偏好和决策的人
- 关心“记错了怎么办”的用户
- 想要本地优先、不依赖云端记忆服务的人

如果你只需要一个简单笔记库或普通向量搜索，CP Memory 可能偏重。它的价值在于长期使用后的记忆质量和治理能力。

## 当前不足

- 还没有图形化审阅界面。
- README 和示例仍在完善中。
- 主要体验围绕 Codex，其他客户端不是优先目标。
- 自动提炼刻意保守，所以不会把所有聊天内容都变成长期记忆。

## English

CP Memory uses local storage like many other memory projects, but its core positioning is not "another SQLite memory store." It is a governable personal memory layer for Codex.

| Dimension | Common local memory projects | CP Memory |
| --- | --- | --- |
| Main goal | Store and search facts, notes, or conversation snippets | Restore trustworthy context inside Codex workflows |
| Integration | Usually centered on an MCP server | Codex plugin + MCP server + skills + lifecycle hooks |
| Memory model | Often generic key/value, documents, or graph entries | Profile, preference, relationship, ongoing work, episode, stable decision |
| Automatic extraction | Sometimes supported, often broad | Conservative by default, only from explicit signals |
| Correction | Usually update or delete | Supports wrong/stale status, correction history, and explanation |
| Governance | Often limited | Conflict detection, review queues, governance reports, cleanup plans |
| Privacy boundary | Local-first projects are usually good | Local-first, with explicit rules against committing real memory data |

## Best Fit

CP Memory is best for:

- People who use Codex for long-running project work
- People who need project rules, preferences, and decisions restored across sessions
- Users who care about what happens when memory is wrong
- Users who want local-first memory without relying on a cloud memory service

If you only need a simple note store or generic vector search, CP Memory may be heavier than necessary. Its value is long-term memory quality and governance.

## Current Gaps

- No graphical review UI yet.
- README and examples are still improving.
- The main experience targets Codex; other clients are not the priority.
- Automatic extraction is intentionally conservative, so it will not turn every chat message into long-term memory.
