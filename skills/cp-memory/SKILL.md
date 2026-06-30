---
name: cp-memory
description: 面向 Codex 的本地优先通用个人助手记忆技能。适用于恢复历史上下文、解释库中记录、查询和写入用户画像、偏好、关系、持续事项、关键事件、稳定立场，并在任意话题中沉淀高质量长期记忆。
---

# CP Memory

创建人：CJ

## 技能定位

当任务涉及以下任一场景时，应优先使用 CP Memory：

- 用户问“刚刚 / 上次 / 之前 / 继续 / 说到哪了”
- 需要查询用户身份、昵称、偏好、项目规则、技术决策
- 需要恢复当前活跃任务、阶段性结论、对话摘要、压缩检查点
- 需要记住非编程话题中的身份、偏好、关系、目标、事件、长期立场
- 需要解释数据库里一条记录到底是什么、正文在哪、为什么会出现
- 需要把新的高价值信息写入长期记忆，并补 payload、links、治理元数据
- 需要评估记忆质量、噪声、冲突、维护状态

不要把 CP Memory 理解成“只搜 facts 表”。它是一个分层、可解释、可治理、可恢复的记忆系统。

## 个人助手六类模型

新版 CP Memory 用六类模型表达长期用户世界：

- `profile`：稳定身份画像，例如昵称、时区、语言、身份信息
- `preference`：偏好、厌恶、沟通风格、使用习惯
- `relationship`：用户和人、项目、工具、目标、主题之间的关系
- `ongoing`：持续事项、未完结话题、长期目标、当前状态
- `episode`：某次具体对话、事件、决定或经历，是长期记忆的证据来源
- `belief_decision`：稳定立场、原则、长期判断、个人决策

优先使用专用工具写入个人助手记忆：

```text
memory_personal_add(memory_type="preference", subject="user", key="communication_style", value="用户喜欢中文、结论先行、可执行建议")
```

当某次 `episode` 推导出长期偏好、画像或立场时，使用派生入口建立来源关系：

```text
memory_personal_derive(episode_id="<episode_fact_id>", memory_type="belief_decision", subject="user", key="memory_system_direction", value="CP Memory 是通用个人助手记忆系统，不限定编程场景")
```

当需要从 episode 中整理长期记忆时，先 dry-run 预览候选：

```text
memory_episode_consolidate(episode_id="<episode_fact_id>", dry_run=true)
```

只有候选合理、边界清楚时，再执行：

```text
memory_episode_consolidate(episode_id="<episode_fact_id>", dry_run=false)
```

对于非常明确、低歧义的高价值表达，`stop hook` 现在也会做保守的自动提炼：

- 自动写一条 `episode`
- 从明确句子中抽取少量 `profile / preference / relationship / ongoing / belief_decision`
- 只处理像“用户喜欢… / 用户决定… / 用户最近在… / 用户默认…”这种显式表达

这条链路的目标是减少手工 `memory_personal_add` 的负担，而不是替代人工判断；模糊表达仍应走显式写入或 dry-run consolidate。

当用户指出记错、过时或只在某范围成立时，使用纠正入口：

```text
memory_correct(id="<fact_id>", status="corrected", reason="用户明确修正", value="修正后的记忆")
```

当同一 subject/key 出现多条相互冲突或重复的个人记忆时，优先做“保留胜出项 + 标记失效项 + 留关系链”的治理，而不是直接删除：

```text
memory_personal_resolve(
  winner_id="<保留的fact_id>",
  loser_ids="<冲突fact_id1>,<冲突fact_id2>",
  merged_value="合并后的最终表述",
  reason="用户确认最新版本",
  loser_status="wrong"
)
```

## 存储模型

### 1. `facts`

统一主索引表，保存短预览、分类、基础检索入口。

- 适合放：一句话事实、摘要预览、任务状态、检查点说明、决策镜像
- 不适合放：长正文、复杂 JSON、需要高保真还原的原始内容

### 2. `memory_payloads`

高保真正文表，按 `fact_id` 关联。

- 适合放：完整摘要、结构化 JSON、长文本、原始 hook 上下文
- 原则：`facts.value` 给人快速扫读，`memory_payloads.content` 给系统保真恢复

### 3. `memory_links`

显式关系表。

- 用于表达“这条摘要关联哪个任务”“这条记录由哪个决策支持”“这条检查点属于哪次压缩”
- 需要解释性时优先建 link，不要只靠 tags

### 4. `memory_meta`

治理表。

- 保存重要性、过期时间、访问次数、来源、摘要类型
- 新版还会记录 `quality_score`、`noise_score`、`canonical_category`、`stability_score`、`evidence_count`、`valid_from`、`valid_until`、`scope`、`sensitivity`、`correction_status`、`last_reviewed_at`

### 5. `decisions`

结构化决策表。

- 适合 ADR 风格的技术决策
- 同时镜像到 `facts`，方便统一搜索

### 6. `aliases`

实体别名表。

- 用于昵称、简称、模块名、项目别名的标准化映射

### 7. `workflows`

可复用流程表。

- 用于保存排查步骤、发布流程、固定工作法

## 默认工作法

### 主事实源规则

凡是涉及“记忆相关问题”，都应先走 `CP Memory` 主库，再决定是否补查 Codex 自带记忆。

记忆相关问题包括但不限于：

- 用户问“刚刚 / 上次 / 之前 / 昨天 / 继续 / 说到哪了 / 你还记得吗”
- 查询身份、昵称、偏好、关系、长期目标、ongoing、episode、belief_decision
- 查询 `CP Memory` 产品历史、版本演进、治理结果、真实库状态
- 解释某条记录是什么、正文在哪、为什么会出现

默认顺序：

1. 先查 `CP Memory`
2. 评估主库命中是否足够强
3. 只有在主库无结果、结果太弱、需要平台侧背景快照或需要交叉验证时，才补查 `MEMORY_SUMMARY / MEMORY.md`

这条策略不仅适用于显式查询入口 `memory_recall(...)`，也适用于启动恢复与 prompt 注入等 Hook 恢复链。

冲突裁决：

- `CP Memory` 是主事实源
- Codex 自带记忆是辅助记忆
- 两边冲突时，以 `CP Memory` 为准，并说明辅助记忆可能滞后

推荐统一使用 `memory_recall(...)` 作为记忆查询总入口；仅在它不能覆盖的情况下，再单独调用 `memory_search`、`memory_probe`、`memory_inspect`、`memory_restore_context` 等工具。

### 恢复上下文

优先顺序：

1. 需要系统级恢复概览时：

```text
memory_restore_context(prompt="用户当前问题")
```

2. 需要解释一条具体记录时：

```text
memory_inspect(id="fact_id")
memory_explain(id="fact_id")
```

3. 需要看任务、健康度、维护状态时：

```text
memory_task_get()
memory_health()
memory_maintenance(dry_run=true)
```

### 检索

优先顺序：

1. 想广泛召回可能相关的信息：

```text
memory_search("关键词1 关键词2", mode="or")
```

2. 想查某个实体的稳定画像：

```text
memory_probe(entity="标准实体名")
```

3. 想看库结构与表职责：

```text
memory_schema()
```

检索规则：

- 默认先用短关键词，不要一次塞整段自然语言
- 一个词搜不到就换同义词、简称、英文名再试
- 查实体时优先 `memory_probe`，不要只依赖全文搜
- 解释 `PreCompact`、`latest-turn-summary`、`decision` 一类数据时，优先 `memory_inspect` 或 `memory_explain`

## 写入规则

### 什么时候只写预览

以下内容可以只写 `facts.value`：

- 稳定、简短、低歧义的事实
- 当前任务名
- 一句话偏好或项目规则
- 方便人工浏览的短说明

### 什么时候必须带 payload

以下内容建议或必须带 `content` / payload：

- 对话摘要
- hook 原始事件
- 结构化决策
- 复杂实现说明
- 长文本原文
- 任何后续需要“高保真恢复”的内容

### 推荐写法

普通记忆：

```text
memory_add(entity="User.Preference", property="communication", value="结论先行，直接执行", category="profile")
```

带 payload 的摘要：

```text
memory_add(
  entity="CP Memory.CurrentConversation",
  property="latest-turn-summary",
  value="本轮完成插件升级摘要",
  category="summary",
  content="{...完整结构化摘要...}",
  content_type="application/json"
)
```

结构化决策：

```text
memory_decision_add(
  title="新版仓储层用 MyBatis-Plus",
  context="新功能仓储规范",
  decision="Domain 只定义 Repository 接口，Infrastructure 默认用 MyBatis-Plus 实现"
)
```

显式关系：

```text
memory_link_add(source_kind="fact", source_id="<summary_id>", relation="about_task", target_kind="fact", target_id="<task_id>")
```

## 解释性回答规则

当用户问：

- “这条数据是什么”
- “为什么 facts 里会有这个”
- “正文去哪了”
- “这是事实、摘要还是检查点”

回答时必须明确区分：

- 预览是否在 `facts`
- 正文是否在 `memory_payloads`
- 是否存在关系链在 `memory_links`
- 这条记录的 `category`、`canonical_category`
- 它的 `source`、`summary_type`
- 它的质量分、噪声分是否异常
- 它的 `history` 里是否有纠正、确认、冲突解决、被覆盖记录

如果用户追问“这条记忆为什么变成现在这样”，优先看 `memory_inspect` / `memory_explain` 的时间线，不要只看当前 payload。

## 治理规则

当用户问记忆是否准确、是否冲突、是否需要清理，优先使用：

```text
memory_health()
memory_personal_review(subject="user")
memory_conflicts()
memory_maintenance(dry_run=true)
memory_governance_report(limit=5)
memory_auto_extract_cleanup(dry_run=true, limit=10)
```

`memory_personal_review` 现在除了 `conflicts` 和 `consolidation_suggestions`，还应重点查看：

- `resolution_candidates`：系统给出的建议胜出项、待合并/待失效项、推荐动作和复查提示
- `recent`：最近活跃且仍有效的个人记忆
- `review_candidates`：自动提炼但仍未确认、低证据或应优先复核的候选记忆
- `memory_governance_report`：面向真实 `memory.db` 的非破坏性治理验收快照，适合做抽样检查和升级后验收
- `memory_auto_extract_cleanup`：针对自动提炼产生的“实现说明/代码示例类噪声”给出清理预案；默认先 `dry_run`

`memory_conflicts` 会同时返回旧式重复冲突和个人助手记忆冲突，包括：

- 同一 subject/key 下的相反偏好或立场
- 已过期的 `ongoing`
- 低证据 `belief_decision`
- 弱证据 `preference`

发现冲突后的建议动作：

- 用户只是补充细节：优先 `memory_personal_resolve(..., merged_value="合并后的表达")`
- 用户明确说旧记忆错了：优先 `memory_personal_resolve(..., loser_status="wrong")`
- 用户只是阶段变化：优先 `memory_personal_resolve(..., loser_status="stale")`
- 用户说“只在某项目/某时期成立”：优先 `memory_personal_resolve(..., loser_status="scoped")`，并配合 `scope` / `valid_until`

恢复规则补充：

- 默认不应把 `wrong` / `stale` 的个人记忆继续注入恢复上下文
- `confirmed`、高 `stability_score`、高 `evidence_count` 的候选应优先于弱证据版本
- `stop-hook-auto-extract` 产生的未确认候选应适度降权，确认后再提升恢复优先级
- 已过期的 `ongoing` 不应继续作为当前状态恢复给助手

只有用户明确要求清理时，才执行：

```text
memory_maintenance(dry_run=false, expire=true)
```

不要擅自删除高价值记录。

## 轻量 Benchmark

升级个人助手记忆相关能力后，建议运行：

```text
python tests/personal_memory_benchmark.py
```

该脚本会用临时 SQLite 库验证六类模型的跨话题恢复能力，包括身份、偏好、关系、持续事项、稳定立场和由 episode 派生的长期记忆。

## 自主并行规则

当用户已经明确授权“可以自主决定开启子 agent 并行任务”时，允许你把 CP Memory 工作拆成互不冲突的并行子任务，例如：

- 一个子 agent 看真实 `memory.db` 的历史脏数据分布
- 一个子 agent 看 hooks / restore helper / tests 的恢复策略
- 主线程继续做实现、联调和验收

并行使用规则：

- 只能拆成边界清晰、结论可直接整合的小任务
- 不要让多个 agent 同时改同一批文件
- 探查类子任务优先返回“结论 + 优先级 + 建议测试”，不要让子 agent 发散
- 主线程负责最终取舍、集成、验证与版本升级
- 默认可并行：历史脏数据分布分析、恢复召回质量抽样、治理规则风险评估、测试补齐建议、验收报告整理
- 默认不要并行写：同一个 SQLite 库的批量清洗、同一组记忆冲突的解决、同一批 hooks / skills / tests 的交叉修改
- 一旦涉及版本升级、数据迁移、真实库写入、冲突最终裁决，必须回到主线程统一执行

如果用户没有明确授权自主并行，就按普通单线程方式使用本技能。

## 推荐工具清单

```text
memory_schema
memory_add
memory_personal_add
memory_personal_derive
memory_episode_consolidate
memory_personal_list
memory_personal_review
memory_personal_resolve
memory_search
memory_probe
memory_explain
memory_inspect
memory_restore_context
memory_correct
memory_update
memory_remove
memory_list
memory_stats
memory_decision_add
memory_decision_list
memory_task_set
memory_task_get
memory_task_done
memory_workflow_save
memory_workflow_get
memory_workflow_list
memory_alias_add
memory_alias_list
memory_health
memory_link_add
memory_link_list
memory_touch
memory_conflicts
memory_maintenance
```
