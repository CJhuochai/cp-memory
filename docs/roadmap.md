# CP Memory Roadmap

## 中文

这份路线图描述 CP Memory 接下来可能发展的方向。它不是承诺清单，而是帮助贡献者理解优先级和非目标。

### 近期

- 强化 hook 失败兜底：失败时写入本地日志，但不打断 Codex 正常使用。
- 完善升级说明，帮助用户从旧本地安装迁移到 GitHub marketplace 安装。
- 增加更多脱敏示例，展示真实使用中的恢复、纠错和审阅流程。

### 中期

- 改进自动提炼质量，让候选记忆更少依赖固定关键词。
- 提供更顺手的审阅体验，例如导出式报告或轻量审阅页面。
- 让治理报告更容易收敛 wrong、stale、pending review 和 conflict 状态。

### 长期

- 探索可选图形化审阅界面，但不牺牲本地优先和低维护原则。
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

- Harden hook failure handling: write local logs on failure without interrupting normal Codex usage.
- Improve upgrade docs for users moving from older local installs to GitHub marketplace installation.
- Add more sanitized examples showing real recall, correction, and review flows.

### Mid Term

- Improve automatic extraction quality so memory candidates depend less on fixed keywords.
- Provide a smoother review experience, such as exportable reports or a lightweight review page.
- Make governance reports easier to converge for wrong, stale, pending review, and conflict states.

### Long Term

- Explore an optional graphical review UI without giving up local-first and low-maintenance principles.
- Explore more client integrations while keeping Codex as the primary experience.
- Provide better quality checks and example benchmarks without uploading private memory.

### Non-Goals

- No cloud memory service.
- No default upload of user memory.
- No automatic conversion of every chat message into long-term memory.
- No feature count at the cost of explainability, correctability, and privacy boundaries.
