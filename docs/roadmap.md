# CP Memory Roadmap

## 中文

这份路线图描述 CP Memory 接下来可能发展的方向。它不是承诺清单，而是帮助贡献者理解优先级和非目标。

### 已完成（截至 2026-09-04）

- v1.8.1 已提供标准 MCP 安装包、隔离安装验证和常见客户端最小配置，见[客户端指南](mcp-clients.md)。
- 已提供合成数据的恢复、纠错与治理基准，以及 Codex CLI 跨会话验收；这不代表所有客户端 UI 或桌面 Hooks 均已验证，见[验证说明](verification.md)。

### 近期
- 在取得设备后完成 macOS/Linux 真实 Codex 桌面端 Hook 注入手工冒烟。
- 研究让 GitHub Marketplace 在 POSIX 也能自动准备插件私有运行环境的最小兼容方案。
- 增加更多脱敏示例，展示真实使用中的恢复、纠错和审阅流程。

### 中期

- 改进自动提炼质量，让候选记忆更少依赖固定关键词。
- 提供更顺手的审阅体验，例如导出式报告或轻量审阅页面。
- 让治理报告更容易收敛 wrong、stale、pending review 和 conflict 状态。

### 长期

- 探索可选图形化审阅界面，但不牺牲本地优先和低维护原则。
- 标准 MCP 提供跨客户端基础能力；Codex 插件继续提供 Skills 和生命周期 Hooks 增强体验。
- 在不上传私人记忆的前提下，提供更好的质量评估和示例基准。

### 非目标

- 不做云端记忆服务。
- 不默认上传用户记忆。
- 不把所有聊天内容都自动变成长期记忆。
- 不为了功能数量牺牲可解释性、可纠错性和隐私边界。

## English

This roadmap describes possible directions for CP Memory. It is not a promise list; it helps contributors understand priorities and non-goals.

### Completed (as of 2026-09-04)

- v1.8.1 provides the standard MCP package, isolated installation verification, and minimal client configurations; see the [client guide](mcp-clients.md).
- Synthetic restore/correction/governance benchmarks and Codex CLI cross-session acceptance are available. This does not establish coverage of every client UI or desktop Hook; see [verification](verification.md).

### Near Term
- Complete manual real-Codex-desktop Hook-injection smoke testing on macOS/Linux when devices are available.
- Investigate the smallest compatible way for GitHub Marketplace to provision the private plugin runtime on POSIX.
- Add more sanitized examples showing real recall, correction, and review flows.

### Mid Term

- Improve automatic extraction quality so memory candidates depend less on fixed keywords.
- Provide a smoother review experience, such as exportable reports or a lightweight review page.
- Make governance reports easier to converge for wrong, stale, pending review, and conflict states.

### Long Term

- Explore an optional graphical review UI without giving up local-first and low-maintenance principles.
- Standard MCP provides the cross-client baseline; the Codex plugin continues to add Skills and lifecycle Hooks as an enhanced experience.
- Provide better quality checks and example benchmarks without uploading private memory.

### Non-Goals

- No cloud memory service.
- No default upload of user memory.
- No automatic conversion of every chat message into long-term memory.
- No feature count at the cost of explainability, correctability, and privacy boundaries.
