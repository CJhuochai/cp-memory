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

本地验证通过：61 项 unittest、20/20 个人记忆基准、144/144 召回检查、wheel/sdist 打包与 40 个 MCP 工具/5 次调用冒烟、Windows 隔离安装、git diff --check。 / Local checks passed: 61 unit tests, 20/20 personal benchmark, 144/144 recall checks, wheel/sdist smoke with 40 MCP tools and 5 calls, Windows isolated installation, and git diff --check.

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

发布前独立审查另补回归：泛历史/英文偏好、正文不重复项目名的范围查询、原生 Windows 路径。对应失败已复现并修复，61 项测试通过。 / Independent pre-release review added broad history/English preference, scope-only queries without project names in values, and native Windows path regressions. Failures were reproduced and fixed; 61 tests pass.
