# CP Memory International MCP Growth Design

## 中文

### 目标

让国际 AI Agent / MCP 开发者能发现、理解并在常见 MCP 客户端中安装 CP Memory，同时保持现有 Codex 插件、生命周期 Hooks、本地数据库和记忆治理能力可用。

成功路径应缩短为：

1. 从 GitHub 或 MCP 目录发现项目。
2. 在首页 30 秒内理解“本地优先、可解释、可纠错的长期记忆”。
3. 用一条标准 MCP 安装命令启动服务。
4. 在不迁移或上传现有 `~/.cp-memory/memory.db` 的情况下完成首次记忆写入与恢复。

### 设计原则

- **兼容优先**：Codex 插件继续提供 Skills、Hooks 和完整 MCP 工具；标准 MCP 客户端获得不依赖 Codex 生命周期的基础能力。
- **复用现有核心**：不重写 SQLite 存储和 MCP 工具。Python 包入口调用现有实现，原有脚本保留为兼容入口。
- **本地优先**：默认不联网、不遥测、不上传记忆，数据库位置和格式保持不变。
- **证据优先**：只有经过隔离安装、MCP 握手和现有回归测试验证的安装方式才写入首页。
- **逐步发布**：文档、Python 包、Registry 元数据和推广分别交付；任一步失败都不影响当前稳定版。

### 交付阶段

#### 阶段 1：英文优先的 GitHub 首页

- 将 `README.md` 改为默认英文入口，将现有中文内容迁移为 `README.zh-CN.md`，两者保持同等信息量并互相链接。
- 首屏只保留明确价值、真实 CI 状态、一条推荐安装路径、30 秒脱敏演示和三个差异点：本地优先、可治理、Codex 深度集成。
- 复用现有演示脚本制作真实 GIF；不使用真实账户、路径、项目或记忆数据。
- 新增可上传到 GitHub Repository Settings 的社交预览图。仓库只保存源资产；实际上传单独执行。
- 修正文档中“其他客户端不是优先目标”的旧定位：标准 MCP 是通用基线，Codex 是增强体验。

#### 阶段 2：标准 Python / MCP 分发

- 发布名使用 `cp-memory-mcp`，提供 `cp-memory-mcp` 控制台命令，并以 `uvx cp-memory-mcp` 作为推荐的跨客户端启动方式。
- 使用最小 Python 包装层暴露现有 MCP server；`scripts/memory-mcp-server.py` 保留并转发到同一入口，避免破坏 `.mcp.json`、安装器和现有测试。
- 不移动或重写 `scripts/cp_memory_store.py`，除非打包验证证明模块路径无法复用。
- 增加 Claude Code、Cursor、VS Code、Gemini CLI 和 Codex 的最小配置示例；只记录经过验证或明确标注为“待客户端实测”的路径。
- 构建 wheel/sdist，并在全新临时虚拟环境中验证安装、MCP `initialize`、`tools/list`、写入、查询和纠错。

#### 阶段 3：官方 MCP Registry

- 增加符合官方 schema 的 `server.json`，服务器名使用 `io.github.CJhuochai/cp-memory`，包指向已发布的 PyPI 版本。
- PyPI 包公开可安装且隔离验证通过后，才发布 Registry 条目。
- Registry 登录、PyPI 上传和目录提交属于外部发布动作，在执行时单独确认凭证与最终元数据。

#### 阶段 4：工具面与信任证据

- 先测量当前 `tools/list` schema 大小、工具选择成功率和典型流程调用数，再决定是否需要简化。
- 第一轮不删除或重命名现有工具。若测量确认工具面造成明显选择问题，再增加可选的精简模式；完整模式继续兼容现有用户。
- README 展示可复现的 CI、隔离安装和记忆恢复基准，不使用无法复核的营销数字。
- 增加简短的数据流与安全说明：本地文件位置、默认网络边界、备份/删除方法，以及不会被提交的敏感文件。

#### 阶段 5：聚焦发布

- 功能验收后再提交一个 MCP 社区目录和少量高相关 Awesome 列表，避免一次性铺设大量难维护入口。
- 复用现有英文发布稿，围绕一个可验证场景发布；不夸大 macOS/Linux Codex 桌面 Hook 的人工验收状态。
- 用 GitHub Traffic 的独立访客、来源、README 到安装的转化反馈评估效果，不把自动化克隆当作真实用户。

### 兼容性边界

- 现有 Codex Marketplace / 源码安装命令继续工作。
- 现有 `.mcp.json`、Skills 和 Hooks 的行为不变。
- 现有 40 个 MCP 工具在默认完整模式中保持名称和参数兼容。
- 现有数据库无需迁移；标准 MCP 与 Codex 插件默认读取同一 `~/.cp-memory/memory.db`。
- Windows、macOS、Linux 的现有 CI 继续通过；尚未完成的真实 macOS/Linux Codex 桌面 Hook 冒烟仍明确标注。

### 验收门槛

每个实现 PR 必须满足与改动范围对应的门槛：

- `python -m unittest discover -s tests -p test_cp_memory.py`
- 涉及安装、MCP、manifest、marketplace 或打包时运行隔离安装验证。
- 涉及记忆行为时运行个人记忆基准。
- Python 分发必须在干净临时环境完成 build、install、MCP 握手和最小写入/恢复冒烟。
- README 中的命令必须从空环境复制执行验证。
- 提交前确认没有真实数据库、日志、token、个人摘要或本地配置。

### 回滚

- 每个阶段使用独立 PR；文档和分发改造不与记忆核心功能混合。
- Python 包入口失败时，可回退到原有脚本入口，数据库无需回滚。
- Registry 元数据仅在对应 PyPI 版本可用后发布；错误版本通过新的补丁版本修复，不覆盖已有制品。

### 非目标

- 不建设云端记忆服务、账号系统、遥测或付费功能。
- 不为曝光目的新增 GUI。
- 不立即重构三个大 Python 文件。
- 不立即删减 MCP 工具或制造破坏性 API。
- 不在功能验收前做大规模社区推广。

## English

### Goal

Make CP Memory discoverable, understandable, and installable for international AI Agent and MCP developers across common MCP clients while keeping the existing Codex plugin, lifecycle hooks, local database, and memory-governance features working.

The successful path should become:

1. Discover the project through GitHub or an MCP directory.
2. Understand “local-first, explainable, correctable long-term memory” within 30 seconds.
3. Start the server with one standard MCP installation command.
4. Complete the first memory write and recall without migrating or uploading the existing `~/.cp-memory/memory.db`.

### Design Principles

- **Compatibility first**: the Codex plugin keeps Skills, Hooks, and the full MCP toolset; standard MCP clients receive a baseline that does not depend on Codex lifecycle events.
- **Reuse the existing core**: do not rewrite SQLite storage or MCP tools. The Python package entry point calls the existing implementation, while the existing script remains as a compatibility entry point.
- **Local first**: no network access, telemetry, or memory upload by default; the database location and format remain unchanged.
- **Evidence first**: only installation paths verified through isolated install, MCP handshake, and existing regression tests appear on the landing page.
- **Incremental release**: documentation, Python packaging, Registry metadata, and promotion ship separately; a failed step must not affect the current stable release.

### Delivery Stages

#### Stage 1: English-first GitHub landing page

- Make `README.md` the default English entry, move the current Chinese content to `README.zh-CN.md`, keep both versions equivalent, and cross-link them.
- Keep the hero focused on a clear value proposition, real CI status, one recommended install path, a sanitized 30-second demo, and three differentiators: local first, governable memory, and deep Codex integration.
- Turn the existing demo script into a real GIF without real accounts, paths, projects, or memory data.
- Add a social-preview asset suitable for upload in GitHub Repository Settings. Store the source asset in the repository; upload it as a separate action.
- Replace the outdated “other clients are not a priority” wording: standard MCP is the portable baseline, while Codex remains the enhanced experience.

#### Stage 2: Standard Python / MCP distribution

- Use the distribution name `cp-memory-mcp`, provide a `cp-memory-mcp` console command, and recommend `uvx cp-memory-mcp` as the cross-client launch command.
- Add the smallest Python wrapper that exposes the existing MCP server. Keep `scripts/memory-mcp-server.py` as a forwarding compatibility entry point so `.mcp.json`, installers, and current tests do not break.
- Do not move or rewrite `scripts/cp_memory_store.py` unless package validation proves that its module path cannot be reused.
- Add minimal configuration examples for Claude Code, Cursor, VS Code, Gemini CLI, and Codex. Include only verified paths or label them clearly as pending client validation.
- Build wheel and sdist artifacts, then verify installation, MCP `initialize`, `tools/list`, write, query, and correction in a fresh temporary virtual environment.

#### Stage 3: Official MCP Registry

- Add a schema-valid `server.json` named `io.github.CJhuochai/cp-memory`, pointing to the published PyPI package.
- Publish the Registry entry only after the PyPI package is publicly installable and passes isolated validation.
- Registry login, PyPI upload, and directory submission are external publishing actions; credentials and final metadata are confirmed separately when executed.

#### Stage 4: Tool surface and trust evidence

- Measure the current `tools/list` schema size, tool-selection success, and call count for representative workflows before deciding whether simplification is needed.
- Do not delete or rename existing tools in the first iteration. If measurements show a material selection problem, add an optional compact mode while keeping full mode compatible for current users.
- Show reproducible CI, isolated-install, and memory-recall benchmark evidence in the README; do not use marketing numbers that readers cannot verify.
- Add a concise data-flow and security note covering local file location, default network boundary, backup/deletion, and sensitive files that must never be committed.

#### Stage 5: Focused launch

- After functional acceptance, submit to one MCP community directory and a small number of relevant Awesome lists instead of creating many maintenance-heavy listings at once.
- Reuse the existing English launch draft around one verifiable use case, without overstating manual macOS/Linux Codex desktop Hook validation.
- Evaluate results through GitHub Traffic unique visitors, referrers, and README-to-install feedback; do not treat automated clones as real users.

### Compatibility Boundaries

- Existing Codex Marketplace and source-install commands keep working.
- Existing `.mcp.json`, Skills, and Hooks keep their behavior.
- All existing 40 MCP tools keep compatible names and parameters in the default full mode.
- Existing databases require no migration; standard MCP and the Codex plugin use the same `~/.cp-memory/memory.db` by default.
- Existing Windows, macOS, and Linux CI stays green. The outstanding real-device macOS/Linux Codex desktop Hook smoke test remains disclosed.

### Acceptance Gates

Each implementation PR must pass the gates relevant to its scope:

- `python -m unittest discover -s tests -p test_cp_memory.py`
- Run isolated installer validation for installer, MCP, manifest, marketplace, or packaging changes.
- Run the personal-memory benchmark for memory-behavior changes.
- Python distribution work must pass build, install, MCP handshake, and minimal write/recall smoke tests in a clean temporary environment.
- Commands shown in the README must be copied and executed from an empty environment.
- Confirm that no real database, logs, tokens, private summaries, or local configuration are committed.

### Rollback

- Use an independent PR for each stage; do not mix landing-page or distribution work with memory-core changes.
- If the package entry point fails, revert to the existing script entry point; no database rollback is required.
- Publish Registry metadata only after its matching PyPI version is available. Fix a bad artifact with a new patch version rather than overwriting a published artifact.

### Non-goals

- No cloud memory service, accounts, telemetry, or paid features.
- No GUI added for discoverability.
- No immediate refactor of the three large Python files.
- No immediate MCP-tool deletion or breaking API changes.
- No broad community promotion before functional acceptance.
