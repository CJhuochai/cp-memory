# CP Memory Examples

## 中文

这些示例来自 CP Memory 自身的长期开发过程，但已经脱敏改写。它们不包含真实记忆库、真实本地路径、私人摘要、客户信息或完整会话内容。

### 示例 1：跨会话恢复维护规则

用户在一次会话中确定：

```text
以后更新插件时，先从 main 拉新分支，测试通过后通过 PR 合并。
```

后续会话里，Codex 开始改文档前会恢复这条规则，并采用：

```text
git switch main
git pull
git switch -c docs/product-positioning-examples
```

价值：减少“新会话忘记项目流程”的问题，避免直接在稳定分支上改动。

### 示例 2：把产品判断沉淀成长期决策

开发过程中形成过一个产品定位：

```text
CP Memory 的重点不是尽可能多地记住，而是让长期记忆可解释、可审阅、可纠错。
```

后续编写 README、插件描述和对比文档时，Codex 会优先围绕这个定位组织内容，而不是把它包装成另一个通用 SQLite memory server。

价值：产品方向可以跨会话延续，避免每次重新讨论定位。

### 示例 3：安全纠错而不是覆盖历史

如果自动提炼了一条不准确的记忆，用户可以把它标记为 `wrong` 或 `stale`，再写入修正版本。

```text
旧记忆：发布文档只需要中文。
纠正：所有面向用户或维护者的文档都需要中英双语。
```

价值：错误记忆不会被静默覆盖，审查时可以看到纠错历史。

### 示例 4：匿名化展示真实使用价值

CP Memory 本身就是在长期使用中逐步做出来的：从最初的本地 SQLite 记忆，到 hooks、MCP tools、自动提炼、冲突检测、治理报告、开源安装和发布流程。

这个过程适合作为公开案例，但公开材料只展示抽象后的工作流：

- 长期项目规则如何被记住
- 新会话如何恢复关键上下文
- 错误记忆如何被纠正
- 发布流程如何保持一致

不展示：

- 真实 `memory.db`
- 真实本地路径
- 私人会话全文
- 未脱敏项目、客户或个人信息

## English

These examples are based on the long-running development of CP Memory itself, but they are sanitized. They do not include the real memory database, real local paths, private summaries, customer information, or full conversation transcripts.

### Example 1: Restoring Maintenance Rules Across Sessions

In one session, the user decides:

```text
When updating the plugin, create a branch from main, run tests, and merge through a PR.
```

In later sessions, before editing docs, Codex restores that rule and follows:

```text
git switch main
git pull
git switch -c docs/product-positioning-examples
```

Value: fewer forgotten project rules across new sessions, and fewer accidental changes directly on the stable branch.

### Example 2: Turning Product Judgment Into Long-Term Decisions

During development, the project established this positioning:

```text
CP Memory is not about remembering as much as possible. It is about making long-term memory explainable, reviewable, and correctable.
```

When writing the README, plugin description, and comparison docs later, Codex can organize the content around that positioning instead of presenting CP Memory as just another SQLite memory server.

Value: product direction carries across sessions instead of being rediscovered each time.

### Example 3: Correcting Bad Memory Safely

If automatic extraction creates an inaccurate memory, the user can mark it `wrong` or `stale`, then write a corrected version.

```text
Old memory: Release docs only need Chinese.
Correction: All user-facing or maintainer-facing docs need both Chinese and English.
```

Value: bad memory is not silently overwritten. Reviewers can still inspect the correction history.

### Example 4: Showing Real Usage Without Exposing Private Data

CP Memory was built through long-term use of itself: from local SQLite memory, to hooks, MCP tools, automatic extraction, conflict detection, governance reports, open-source installation, and release workflow.

That history is useful as a public case study, but public material should only show sanitized workflows:

- How long-term project rules are remembered
- How new sessions restore key context
- How bad memory is corrected
- How release workflow stays consistent

Do not show:

- Real `memory.db`
- Real local paths
- Private full conversation transcripts
- Unsanitized project, customer, or personal information
