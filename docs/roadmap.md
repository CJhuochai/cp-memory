# CP Memory Roadmap

## 中文

这份路线图描述 CP Memory 接下来可能发展的方向。它不是承诺清单，而是帮助贡献者理解优先级和非目标。

### 近期

- 完善 README、示例、对比文档和 FAQ，让新用户更快理解 CP Memory 的定位。
- 增加更多脱敏示例，展示跨会话恢复、纠错、冲突处理和治理报告。
- 继续改进安装和升级说明，保持 Windows/macOS/Linux 的插件安装路径清晰。
- 补充更多针对 hooks、MCP tools、manifest 和安装脚本的回归测试。

### 中期

- 提供更易读的记忆审阅体验，例如导出式报告或轻量审阅页面。
- 改进自动提炼的解释信息，让用户更容易判断“为什么这条被记住”。
- 增强治理报告，让 wrong、stale、pending review、conflict 等状态更容易收敛。
- 增加更完整的迁移说明，帮助早期本地安装用户平滑切换到 GitHub marketplace 安装。

### 长期

- 探索可选的图形化审阅界面，但不牺牲本地优先和低运维原则。
- 研究更多客户端集成方式，但 Codex 仍是首要体验目标。
- 在不上传私人记忆的前提下，提供更好的质量评估和示例基准。

### 非目标

- 不做云端记忆服务。
- 不默认上传用户记忆。
- 不把所有聊天内容都自动变成长期记忆。
- 不为了功能数量牺牲可解释性、可纠错性和隐私边界。

## English

This roadmap describes possible directions for CP Memory. It is not a promise list; it helps contributors understand priorities and non-goals.

### Near Term

- Improve README, examples, comparison docs, and FAQ so new users understand CP Memory faster.
- Add more sanitized examples for cross-session recall, correction, conflict handling, and governance reports.
- Keep installation and upgrade docs clear for Windows, macOS, and Linux plugin installation paths.
- Add more regression coverage for hooks, MCP tools, manifest behavior, and installer scripts.

### Mid Term

- Provide a more readable memory review experience, such as exportable reports or a lightweight review page.
- Improve automatic extraction explanations so users can understand why a memory was created.
- Improve governance reports so wrong, stale, pending review, and conflict states are easier to resolve.
- Add clearer migration docs for early local installs moving to GitHub marketplace installation.

### Long Term

- Explore an optional graphical review UI without giving up local-first and low-maintenance principles.
- Explore more client integrations while keeping Codex as the primary experience.
- Provide better quality checks and example benchmarks without uploading private memory.

### Non-Goals

- No cloud memory service.
- No default upload of user memory.
- No automatic conversion of every chat message into long-term memory.
- No feature count at the cost of explainability, correctability, and privacy boundaries.
