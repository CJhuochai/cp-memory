# Recall quality implementation plan / 召回质量实施计划

## 中文

已批准范围：第一轮评估基线与召回修正。基于 main `5d26f98`，在 `codex-cj-recall-quality` 实施；版本发布另行确认。

- [x] 在 `tests/recall_quality_benchmark.py` 建立独立临时库场景，标注必须、允许、禁止出现的记录，覆盖恢复和正式 MCP recall 入口。场景使用人工构造的脱敏问题模式，不复制私人记录，不宣称真实用户准确率。
- [x] 在修改生产代码前保存基线 JSON；保留场景级失败、召回率、无关注入率、禁止项泄漏数与上下文字符数。
- [x] 修正 `scripts/cp_memory_store.py` 的共享候选筛选：有效性、范围、相关性先于确认状态；弱命中不补无关最近记录。未确认自动候选显式标注；治理查询仍可查看原始记录。
- [x] 检查 `scripts/memory_mcp_server.py` 和 hooks 调用链，覆盖辅助记忆关闭及多入口一致性，不改变公开工具参数或数据库结构。
- [x] 运行现有 53 项测试、20 项个人记忆基准、新评估、打包和 Windows 隔离安装。记录行为变化与未覆盖范围，更新双语验证说明。

验收：固定评估中必须项不漏、禁止项不注入；保留全局沟通偏好、历史追溯和纠错审计。先运行新增失败场景，再改生产代码；不清理真实主库、不新增依赖、不发布。

## English

Approved scope: round-one evaluation baseline and recall correction, based on main `5d26f98`, on `codex-cj-recall-quality`. Publishing requires a separate decision.

1. Add isolated, hand-authored scenarios to `tests/recall_quality_benchmark.py`, with required/allowed/forbidden records and both restore and MCP recall coverage. Reconstruct sanitized failure patterns; never copy private records or claim population accuracy.
2. Save baseline JSON before production edits, including per-case failures, recall, unrelated injection, forbidden leaks and context characters.
3. Fix shared selection in `scripts/cp_memory_store.py`: validity, scope and relevance before confirmation; no unrelated recent fallback on weak queries. Label unconfirmed automatic candidates; keep raw inspection available for governance.
4. Check MCP and hook callers, including auxiliary-off behavior; preserve public tool parameters and database schema.
5. Run existing unit tests, personal benchmark, new evaluation, packaging and Windows isolated installation. Record results and limitations in bilingual verification documentation.

Acceptance: required records present and forbidden records absent on the fixed suite, while preserving global communication preferences, history access and correction audits. Tests precede production changes. No private database cleanup, new dependencies or publication.
