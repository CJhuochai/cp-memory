# CP Memory Changelog

## 中文

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
