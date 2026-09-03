# CP Memory Changelog

## 中文

### v1.8.0

- 新增标准 Python 发行包 `cp-memory-mcp` 和控制台入口 `cp-memory-mcp`，为通用 MCP 客户端提供可移植基础。
- 保留现有 Codex 插件入口和默认数据库位置，无需迁移已有 `~/.cp-memory/memory.db`。
- 新增干净虚拟环境中的 wheel/sdist 构建、40 个 MCP 工具握手及写入/检索/纠错冒烟验证，并接入三平台 CI。
- PyPI 上传与公开 `uvx` 命令将在合并后单独验证；本次准备不提前声明线上包可用。

### v1.7.2

- 修复公开 Marketplace 的仓库内插件定位：marketplace 清单改用 `source: "local"` 与根目录路径 `"."`。
- 这与 Marketplace 已克隆仓库后解析插件的方式一致；普通用户的 GitHub 安装命令无需改变。

### v1.7.1

- 修复公开 Marketplace 兼容性：插件 hooks 清单改为标准根目录 `hooks.json`。
- 移除重复的非标准 hooks 清单，避免两个配置入口发生漂移。
- 无需迁移既有 `memory.db`；Windows、macOS/Linux 的 hook 脚本路径保持不变。

### v1.7.0

- 新增 macOS/Linux 源码安装器 `install.sh`，使用 `python3` 创建插件私有运行环境并安装 MCP 依赖。
- Hooks 在 POSIX 优先使用 `python3`，Windows 保留 `python` / `py -3` 兼容路径。
- 新增 Windows、macOS、Ubuntu CI；三端均覆盖单元测试，macOS/Linux 额外覆盖隔离安装和 MCP 启动。
- 真实 macOS/Linux Codex 桌面端 Hook 注入手工冒烟仍待补测；无需迁移既有 `memory.db`。

### v1.6.1

- 修复插件 MCP 服务器未设置工作目录的问题，确保从任意项目目录启动 Codex 时都能加载 `memory_*` 工具。
- 新增真实 MCP 初始化与工具列表回归测试，并覆盖带空格的插件安装路径。
- 明确当前正式支持并验证 Windows；本次补丁不扩展 macOS/Linux 支持。
- 无需迁移或修改既有 `memory.db`。

### v1.6.0

- Stop hook 对相同的历史会话摘要去重，重复触发不再新增历史记录。
- 自动长期记忆只从用户输入提炼；助手的方案、示例和代码解释不再被误记为用户记忆。
- 无需迁移或清理既有数据；新规则只影响后续自动写入。

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

### v1.8.0

- Added the standard `cp-memory-mcp` Python distribution and `cp-memory-mcp` console entry point as the portable baseline for general MCP clients.
- Preserved the existing Codex plugin entry point and default database location; existing `~/.cp-memory/memory.db` files need no migration.
- Added clean-venv wheel/sdist builds, a 40-tool MCP handshake, and write/search/correct smoke coverage to the three-platform CI matrix.
- PyPI upload and the public `uvx` command will be verified separately after merge; this preparation does not claim that the online package is available yet.

### v1.7.2

- Fixed public Marketplace plugin resolution inside the cloned repository: the marketplace manifest now uses `source: "local"` and the root path `"."`.
- This matches the Marketplace's cloned-repository resolution model; the normal GitHub installation command is unchanged.

### v1.7.1

- Fixed public Marketplace compatibility: the plugin hooks manifest now uses the standard root-level `hooks.json`.
- Removed the duplicate non-standard hooks manifest to prevent configuration drift.
- No existing `memory.db` migration is required; hook script paths remain unchanged on Windows and macOS/Linux.

### v1.7.0

- Added the macOS/Linux source installer `install.sh`, which uses `python3` to create a private plugin runtime and install MCP dependencies.
- Hooks prefer `python3` on POSIX while Windows retains `python` / `py -3` compatibility.
- Added Windows, macOS, and Ubuntu CI. All three run unit tests; macOS/Linux also run isolated installation and MCP startup validation.
- Manual real-Codex-desktop Hook-injection smoke testing on macOS/Linux remains pending; no migration of an existing `memory.db` is required.

### v1.6.1

- Fixed the missing working directory for the bundled MCP server so Codex can load `memory_*` tools from any project directory.
- Added a real MCP initialization and tool-list regression test, including a plugin installation path with spaces.
- Clarified that Windows is the currently supported and verified platform; this patch does not add macOS/Linux support.
- No migration or change to an existing `memory.db` is required.

### v1.6.0

- Deduplicated identical historical turn summaries in the stop hook, so repeated triggers no longer create extra history records.
- Automatic long-term memory extraction now uses user input only; assistant proposals, examples, and code explanations are not recorded as user memories.
- No migration or cleanup is required; the new rules affect future automatic writes only.

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
