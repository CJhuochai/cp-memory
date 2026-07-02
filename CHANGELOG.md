# CP Memory Changelog

## 中文

### v1.5.0

- 新增 `memory_review_inbox`，用小批量 Inbox 展示待审阅记忆和冲突建议。
- 新增 `memory_review_apply`，支持显式执行 `confirm`、`wrong`、`stale`、`scoped` 或 `skip`，不物理删除记忆。

### v1.4.1

- 为生命周期 hooks 增加统一安全兜底：失败时写入本地日志并返回空结果，避免打断 Codex 使用。

### v1.4.0

- 新增会话启动提醒：当存在待审阅记忆、冲突、可提炼事件或噪声候选时提示用户。
- 加强周维护安全边界：受保护的长期记忆、任务和决策不会被过期清理删除。
- `memory_maintenance` 增加 `protected_expired_skipped`，便于审计被保护跳过的过期项。
- README 补充自动提醒和周维护安全说明。

### v1.3.0

- 新增轻量 project scope ranking，让 CP Memory 优先恢复当前项目相关记忆。
- 自动提炼和恢复上下文支持 `repo:`、`project:`、`workspace:` 等范围信息。

### v1.2.0

- 新增 `memory_review_digest`，输出可审阅记忆报告。
- 报告覆盖最近记忆、待确认候选、冲突/过期项、解决建议和可提炼事件。

### v1.1.0

- 改进自动提炼规则，记录触发信号、意图、置信度和复核原因。
- 降低实现说明、代码示例等内容被误提炼为长期记忆的概率。

## English

### v1.5.0

- Added `memory_review_inbox` for a small actionable queue of pending memory review items and conflict suggestions.
- Added `memory_review_apply` for explicit `confirm`, `wrong`, `stale`, `scoped`, or `skip` actions without physically deleting memory.

### v1.4.1

- Added a shared safety wrapper for lifecycle hooks: failures are logged locally and return an empty result without interrupting Codex.

### v1.4.0

- Added session-start reminders when memories need review, conflict handling, consolidation, or cleanup attention.
- Hardened weekly maintenance so protected long-term memories, tasks, and decisions are not removed by expiry cleanup.
- Added `protected_expired_skipped` to `memory_maintenance` for safer auditability.
- Documented reminder and weekly maintenance safety boundaries in the READMEs.

### v1.3.0

- Added lightweight project scope ranking so CP Memory prioritizes memories related to the current project.
- Auto-extraction and restore context now support `repo:`, `project:`, and `workspace:` style scopes.

### v1.2.0

- Added `memory_review_digest` for reviewable memory reports.
- Reports include recent memories, pending candidates, conflicts/stale items, resolution suggestions, and consolidation candidates.

### v1.1.0

- Improved automatic extraction rules with recorded signals, intents, confidence, and review reasons.
- Reduced accidental long-term memory extraction from implementation notes and code examples.
