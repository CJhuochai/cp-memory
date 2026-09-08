# Round-one recall quality / 第一轮召回质量

## 中文

范围：评估基线与召回修正；不含审阅界面、自动提炼算法升级或发布。数据为人工重构的脱敏问题模式，没有复制真实记忆库。

48 个场景各检查三个入口：恢复文本、MCP recall 内嵌上下文、MCP recall 返回记录，共 144 项检查。MCP 在进程内调用正式函数；独立打包冒烟另验证真实 stdio 协议。

每条测试记录标注必须、允许或禁止。必须项召回率按三个入口的必须项命中数计算；无关注入率为禁止项次数除以所有已识别输出记录次数；上下文长度只统计恢复文本的字符数。未确认候选还须携带文本或结构化 pending_review 标记。

固定回归集用于驱动本次修复，未使用独立留出集，不代表日常错误率、用户总体准确率、token 节约或端到端模型表现。

行为：有效性与项目范围先筛选，相关性先于确认状态；弱命中不补无关最近记录。全局偏好/画像仍可作为常驻指令恢复；泛问偏好与历史时保留对应类别。原始 search/inspect 治理入口仍可查历史数据，显式 history recall 仍保留类别过滤。

兼容：无需数据库迁移，公开 MCP 参数和 40 个工具保持不变。补充未确认候选 review_state 字段，修复 allow_auxiliary=False 的内层传播，保留正文证据和实体名检索。两条原测试断言改为禁止无关关系和其他项目规则。

限制：项目范围来自问题中的名称、repo/project/workspace 标记或路径；未知范围不会猜测当前项目，因此启动时暂不注入限定项目记录。范围是召回规则，不是访问控制。词法检索只支持有限改写；候选上限为最近 200 条加搜索 200 条，尚未做大库召回率或延迟评估。本报告记录 Windows 本地验收；远端跨平台 CI 在 PR 合并前验收。评估不更新真实主库或已安装插件；1.9.0 发布步骤见发布说明。

## English

Scope: evaluation baseline and recall correction, excluding review UI, extraction upgrades and publication. Cases reconstruct sanitized failure patterns without copying private database records.

Each of 48 scenarios checks restore text, nested MCP recall context and returned MCP records (144 checks). MCP functions are invoked in-process; separate package smoke checks the real stdio protocol.

Records are labeled required, allowed or forbidden. Required recall counts hits across all three surfaces; unrelated injection divides forbidden appearances by identified emitted records. Mean context length counts restore characters only. Pending candidates also require a text or structured pending_review marker.

This fixed regression suite drove the fixes and has no independent holdout. It does not measure everyday error rate, population accuracy, model tokens or end-to-end assistant behavior.

Selection filters validity and scope, then ranks relevance before confirmation. Weak queries do not pull unrelated recent records. Explicit global preferences/profiles remain standing instructions; broad preference/history requests retain their categories. Raw search/inspect still expose historical data for governance, and explicit history recall preserves its category filter.

No database migration or public MCP parameter changes; 40 tools remain. Pending records gain review_state, auxiliary-off propagates to nested context, and payload evidence/entity-name retrieval remain supported. Two old assertions now forbid unrelated relationships and other-project rules.

Limits: scope comes from names, repo/project/workspace markers or paths in the question; unknown scope is not guessed, so startup withholds project-scoped records. Scope selection is not access control. Lexical reformulations are limited; candidates are bounded to 200 recent plus 200 search results, without large-database recall/latency evaluation. This report records local Windows validation; remote cross-platform CI is checked before PR merge. Evaluation does not update the live database or installed plugin; see the 1.9.0 release notes for publication steps.

## Results / 结果

本地验证通过：62 项 unittest、20/20 个人记忆基准、144/144 第一轮召回检查、wheel/sdist 打包与 40 个 MCP 工具/5 次调用冒烟、Windows 隔离安装、git diff --check。 / Local checks passed: 62 unit tests, 20/20 personal benchmark, 144/144 round-one recall checks, wheel/sdist smoke with 40 MCP tools and 5 calls, Windows isolated installation, and git diff --check.

| Metric / 指标 | Before / 改前 | After / 改后 |
| --- | ---: | ---: |
| Checks passed / 检查通过 | 42/144 | 144/144 |
| Required recall / 必须项召回率 | 99.12% | 100.00% |
| Forbidden appearances / 禁止项注入次数 | 111 | 0 |
| Unrelated injection / 无关注入率 | 49.55% | 0.00% |
| Mean restore characters / 平均恢复字符数 | 110.96 | 76.96 |

## Reproduce / 重现

```text
python -X utf8 tests/recall_quality_benchmark.py --source-ref 5d26f98 --output before.json
python -X utf8 tests/recall_quality_benchmark.py --output after.json
```

旧基线预期非零退出；source-ref 只读取 Git 对象到临时目录，不切换或修改工作区。两个版本使用同一场景脚本。 / The old baseline intentionally exits nonzero. source-ref reads Git objects into a temporary directory without changing the checkout. Both versions use the same suite.

- Baseline / 基线: `5d26f982328cd9445f4a482c914f4c98b4752f3c`
- Suite SHA-256 / 场景脚本: `e84ab937d485b2a9beff85d2a13ccb2e1bd46a8c88c1a4c1b9b61657b524b3de`
- Current source / 当前源码 `cp_memory_store.py`: `351bd6918b27f4cda1f403614305dcdb01f630c59040098f3c3017c994442cee`
- Current source / 当前源码 `memory_mcp_server.py`: `a9fe13e26dfc351dee2fe59a5ab2475f0f9e820f151f13617d2fe5cb85ffaf43`

## Cases / 场景

| Case / 场景 | Before checks / 改前通过 | After checks / 改后通过 | Before forbidden keys / 改前禁止项 |
| --- | ---: | ---: | --- |
| scope_1 | 1/3 | 3/3 | boreal_release |
| scope_2 | 0/3 | 3/3 | boreal_release |
| compound_scope_1 | 1/3 | 3/3 | boreal_release |
| compound_scope_2 | 0/3 | 3/3 | boreal_release |
| repo_scope_1 | 0/3 | 3/3 | boreal_release |
| repo_scope_2 | 0/3 | 3/3 | boreal_release |
| global_1 | 0/3 | 3/3 | boreal_release |
| global_2 | 0/3 | 3/3 | boreal_release |
| unknown_scope_1 | 0/3 | 3/3 | boreal_release |
| unknown_scope_2 | 0/3 | 3/3 | boreal_release |
| wrong_1 | 3/3 | 3/3 | - |
| wrong_2 | 3/3 | 3/3 | - |
| stale_1 | 3/3 | 3/3 | - |
| stale_2 | 3/3 | 3/3 | - |
| expired_1 | 2/3 | 3/3 | expired_task |
| expired_2 | 2/3 | 3/3 | expired_task |
| pending_1 | 0/3 | 3/3 | - |
| pending_2 | 0/3 | 3/3 | - |
| confirmed_1 | 3/3 | 3/3 | - |
| confirmed_2 | 3/3 | 3/3 | - |
| weak_1 | 0/3 | 3/3 | unrelated |
| weak_2 | 0/3 | 3/3 | unrelated |
| history_1 | 0/3 | 3/3 | music_episode |
| history_2 | 0/3 | 3/3 | music_episode |
| summary_1 | 1/3 | 3/3 | music_summary |
| summary_2 | 0/3 | 3/3 | music_summary |
| legacy_1 | 0/3 | 3/3 | wrong_pattern |
| legacy_2 | 0/3 | 3/3 | wrong_pattern |
| identity_1 | 0/3 | 3/3 | music |
| identity_2 | 1/3 | 3/3 | music |
| relationship_1 | 0/3 | 3/3 | music_relation |
| relationship_2 | 0/3 | 3/3 | music_relation |
| startup_1 | 0/3 | 3/3 | boreal_release |
| startup_2 | 0/3 | 3/3 | boreal_release |
| explicit_other_1 | 1/3 | 3/3 | atlas_release |
| explicit_other_2 | 0/3 | 3/3 | atlas_release |
| old_relevant_1 | 1/3 | 3/3 | noise_0, noise_1, noise_2, noise_3, noise_4 |
| old_relevant_2 | 1/3 | 3/3 | noise_0, noise_1, noise_2, noise_3, noise_4 |
| case_scope_1 | 0/3 | 3/3 | boreal_release |
| case_scope_2 | 1/3 | 3/3 | boreal_release |
| inactive_summary_1 | 0/3 | 3/3 | dead_summary |
| inactive_summary_2 | 0/3 | 3/3 | dead_summary |
| inactive_decision_1 | 2/3 | 3/3 | dead_decision |
| inactive_decision_2 | 3/3 | 3/3 | - |
| english_1 | 0/3 | 3/3 | piano |
| english_2 | 1/3 | 3/3 | piano |
| empty_1 | 3/3 | 3/3 | - |
| empty_2 | 3/3 | 3/3 | - |

发布前独立审查另补回归：泛历史/英文偏好、正文不重复项目名的范围查询、原生 Windows 路径。对应失败已复现并修复，62 项测试通过。 / Independent pre-release review added broad history/English preference, scope-only queries without project names in values, and native Windows path regressions. Failures were reproduced and fixed; 62 tests pass.

## Follow-up recall improvement proposal / 后续召回质量提升建议

### 中文建议

本轮目标是降低“数字或通用词碰巧命中”造成的无关注入，同时保留明确编号查询，并让相关性与记忆可信度各自承担清晰职责。

现状证据：恢复选择器会把查询拆成词，在事实、属性和正文中做任一词子串匹配；数字、常见业务词和项目词没有分层。无范围记录默认放行；强度评估又把记录数量、分类、payload、来源和证据数累加，因此多条弱相关记录可能被标成 `strong`。这正好解释了包含“召回质量 144 111”的查询为什么可能带入其他项目摘要。

实施方案：

1. 将查询词分成主题词、通用词和数字/编号词。通用词（例如“质量”“问题”“规则”“偏好”等）单独命中不产生相关性；带有明确主题的复合词保留其主题片段，避免粗暴全部 AND。数字默认只在已有主题命中时辅助排序；`#23`、`issue 23`、`v1.9.0`、`版本 1.9.0` 等明确编号查询使用边界匹配作为编号证据，避免 `23` 命中 `123`。
2. 先做有效期、纠正状态和范围筛选，再要求至少一个主题词或明确编号命中。项目/仓库/工作区范围只从用户问题中的显式名称、路径或仓库标识解析；没有可靠范围的历史记录保持无范围状态，不推测归属。已标记范围的记录继续严格隔离；全局画像和偏好仍按既有规则保留。
3. 第二阶段将范围上下文贯通到 Stop、SessionStart、UserPromptSubmit 与恢复入口。Stop 只为会话摘要写入由显式 prompt 或事件 `cwd` 等明确项目字段解析出的范围；个人信号仍只从对话文本判断范围，避免把目录中的个人话题误归到项目。SessionStart 与 UserPromptSubmit 使用同一解析器恢复对应范围；无上下文的历史查询保持现有无范围语义。范围不是访问控制。
4. 召回强度同时返回“相关性”和“可信度”两个独立维度。相关性只由主题/编号命中和范围匹配决定；可信度只描述确认状态、证据数、稳定度及来源等治理信号。`strong` 不再由返回条数、payload 存在与否或来源数量堆出来；无主题命中时不因记录很多而升级。
5. 增加脱敏回归：数字碰撞、通用词碰撞、跨项目、无 scope 历史记录、同义/中英文表达、明确编号、无结果，以及相关记录排在大量噪声后的防漏召回。验收同时检查召回率、无关注入率、编号精确性和强度维度的解释是否一致。

权衡与边界：这是轻量词法门槛，不引入向量数据库或新依赖；同义词先覆盖现有中英文和项目别名，未覆盖的自然语言改写仍可能漏召回。范围识别不是安全隔离，真正的权限控制仍需在外部边界实现。大库性能继续受限于最近 200 条加搜索 200 条候选，若基准显示漏召回或延迟，再升级索引和候选策略。

验收标准：固定脱敏场景全部通过；数字/通用词单独命中不产生无关记录；明确编号可精确命中；已明确标记的项目范围不会串库；无 scope 历史记录不被猜测归属，但不承诺对无 scope 数据提供绝对项目隔离；至少一个主题词的相关记录在噪声存在时仍能召回；返回结果能分别说明相关性与可信度。验证使用默认 unittest、个人记忆基准、召回质量基准、打包冒烟和 Windows 隔离安装（若 hooks/MCP 代码变更）。

### English proposal

This round aims to reduce unrelated injection caused by accidental numeric or generic-word matches while preserving explicit identifier searches and separating topical relevance from memory credibility.

Evidence: the restore selector tokenizes a query and accepts substring matches across facts, properties, and payloads. Numeric terms, generic business words, and project terms are not separated. Unscoped rows are allowed by default, while the strength assessor adds row count, category, payload, source, and evidence signals. Several weakly related rows can therefore become `strong`, which explains why a query containing “recall quality 144 111” may pull a summary from another project.

Plan: classify query terms as topical, generic, or numeric/identifier terms; ignore generic-only matches; require a topical or explicit identifier match after validity, correction, and scope filters; preserve explicit project/repository/workspace scope without guessing missing historical scope; propagate reliable scope context through Stop, SessionStart, UserPromptSubmit, and restore while leaving personal-memory scope text-derived; and return independent relevance and credibility dimensions. Relevance comes from topic/identifier and scope matches. Credibility reports confirmation, evidence, stability, and source signals. Row count, payload presence, and source diversity must not manufacture `strong`. Explicit scope markers are isolated; unscoped historical data has no absolute project isolation guarantee.

Regression coverage will include numeric collisions, generic-word collisions, cross-project leakage, unscoped history, Chinese/English and synonym phrasing, exact identifiers, no-result queries, and recall protection when noise ranks ahead of the target. Acceptance checks recall, unrelated injection, identifier precision, and explainable strength dimensions. This remains a small lexical gate with no new dependency; semantic paraphrase coverage and large-scale latency remain follow-up work if measured failures justify them.

### Follow-up validation / 后续验证

本分支新增 5 组脱敏场景，共 58 个场景、174 个入口检查：`174/174` 通过，必须项召回率 `100%`，禁止项注入 `0`，无关注入率 `0%`。默认 CP Memory 单元测试与个人记忆基准会在每次阶段完成后重跑；未执行发布、push、真实主库写入或已安装缓存更新。 / This branch adds five sanitized scenario groups for 58 scenarios and 174 surface checks: `174/174` passed, required recall `100%`, forbidden appearances `0`, and unrelated injection `0%`. The default CP Memory unit suite and personal-memory benchmark are rerun after each stage. No release, push, live-database write, or installed-cache update was performed.

## Next stages / 后续阶段

### 第二阶段：范围上下文贯通 / Stage 2: propagate scope context

中文：已实现并验证 `cwd`、`working_directory`、`workspace`、`workspace_path`、`project_root` 的受限解析：只有能识别为项目、仓库或工作区的值才产生范围。Stop 用该范围标记会话摘要；SessionStart、UserPromptSubmit 和恢复入口使用同一解析器。显式 prompt 优先于事件目录，个人信号不使用目录自动标记；无事件上下文时维持原有无范围查询语义。临时库的三段链路 Stop 写入 → SessionStart 泛历史恢复 → UserPromptSubmit 恢复均已验证，同时覆盖 CP Memory 与 BasisProject 串入隔离、旧 latest summary 范围清理和 Windows 路径。范围不是权限或数据隔离机制。

English: Implemented and verified restricted parsing for `cwd`, `working_directory`, `workspace`, `workspace_path`, and `project_root`: only values recognized as a project, repository, or workspace produce a scope. Stop marks conversation summaries with that scope; SessionStart, UserPromptSubmit, and restore use the same parser. An explicit prompt takes precedence over the event directory, personal signals are never scoped from the directory alone, and no-event queries retain the existing unscoped behavior. A temporary-database chain—Stop write, SessionStart broad-history restore, and UserPromptSubmit restore—covers CP Memory/BasisProject isolation, clearing an old latest-summary scope, and Windows paths. Scope is not authorization or data isolation.

### 第三阶段：匿名留出集与升级触发 / Stage 3: anonymous holdout and upgrade triggers

中文：从固定回归集之外建立不含私人文本的匿名留出集，按主题命中、明确编号、通用词/数字碰撞、跨项目、同义改写、无结果和噪声排序分别统计 Recall、Precision、MRR、无关注入率、编号精确率、scope 串入率和 p95 延迟。每次规则或版本变更同时跑固定集与留出集，记录场景脚本和源码哈希。只有当留出集出现稳定漏召回、编号精确率下降、已标记 scope 串入，或候选规模导致 p95 延迟超出项目可接受阈值时，才考虑同义词扩充、字段级索引或语义检索；在此之前不引入向量库或复杂重排。

English: Build an anonymous holdout set outside the fixed regression suite, with no private text. Report Recall, Precision, MRR, unrelated-injection rate, identifier precision, scoped leakage, and p95 latency separately for topical matches, explicit identifiers, generic/numeric collisions, cross-project cases, paraphrases, no-result queries, and noisy rankings. Run both suites for every rule or version change and record the scenario and source hashes. Consider synonym expansion, field-level indexing, or semantic retrieval only after the holdout shows persistent misses, reduced identifier precision, leakage from an explicit scope, or p95 latency beyond the project threshold. Until then, do not add a vector database or complex reranker.
