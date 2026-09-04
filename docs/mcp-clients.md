# MCP Client Setup / MCP 客户端配置

## English

### Prerequisites

- Python 3.10 or newer.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) with `uvx` available on `PATH`.

The portable server command is:

```text
uvx cp-memory-mcp
```

It was verified from public PyPI with a clean `uv` cache through MCP initialization, all 40 tools, and a write/search/correct flow. The examples below use each client's documented stdio configuration format. Codex CLI acceptance is described below; other clients are not installed on the verification machine, and client-specific UI discovery and approval screens remain pending manual testing.

### Codex

```text
codex mcp add cp-memory -- uvx cp-memory-mcp
codex mcp get cp-memory
```

The command shape was checked against the installed Codex CLI. On 2026-09-04, four independent Windows Codex CLI 0.140.0 sessions verified the published `cp-memory-mcp==1.8.1` package: write a synthetic memory, recall it in a fresh session, correct its value, then recall and restore the corrected value in another fresh session. Both final results contained the new value, not the old one. The six successful MCP calls were `memory_add`, `memory_recall`, `memory_probe`, `memory_correct`, `memory_recall`, and `memory_restore_context`.

This acceptance run used a temporary database with explicit `CP_MEMORY_HOME`, `CP_MEMORY_DB_PATH`, and `CP_MEMORY_OLD_HOME` overrides, ephemeral sessions, and disabled plugins, hooks, and auxiliary memories. The recall calls set `allow_auxiliary=false`. The initial non-interactive write was cancelled by client approval; the successful run used user-authorized, invocation-only approval for the test server. It did not change the user's permanent configuration. This proves a guided CLI workflow, not unattended default approval, desktop UI behavior, other clients, or a general model accuracy rate. To repeat it, use four fresh sessions against the same isolated database and do not include the expected value in either recall prompt.

Codex plugin users can keep the Marketplace installation instead to receive lifecycle Hooks and Skills in addition to MCP tools.

### Claude Code

```text
claude mcp add cp-memory -- uvx cp-memory-mcp
claude mcp get cp-memory
```

Claude Code documents `--` as the separator before the stdio command and its arguments.

### Cursor

Create `.cursor/mcp.json` for a project or `~/.cursor/mcp.json` for global use:

```json
{
  "mcpServers": {
    "cp-memory": {
      "command": "uvx",
      "args": ["cp-memory-mcp"]
    }
  }
}
```

### VS Code

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "cpMemory": {
      "type": "stdio",
      "command": "uvx",
      "args": ["cp-memory-mcp"]
    }
  }
}
```

### Gemini CLI

```text
gemini mcp add cp-memory uvx cp-memory-mcp
gemini mcp list
```

Gemini CLI tests local stdio servers only when the current folder is trusted.

### Data and security boundary

- CP Memory stores data locally in `~/.cp-memory/memory.db` by default; the Codex plugin and portable MCP command use the same database.
- `uvx` accesses the package registry to install or refresh the package. The running CP Memory server has no telemetry or memory-upload path by default.
- Stop MCP clients before copying the database for backup. To reset all memory, back up and then remove `memory.db`; this is intentionally a manual destructive action.
- Never commit the database, logs, private summaries, tokens, or environment files.

Official format references: [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp), [Cursor MCP](https://docs.cursor.com/context/model-context-protocol), [VS Code MCP configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration), and [Gemini CLI MCP](https://geminicli.com/docs/tools/mcp-server/).

## 中文

### 前置条件

- Python 3.10 或更高版本。
- 已安装 [`uv`](https://docs.astral.sh/uv/getting-started/installation/)，并且 `uvx` 位于 `PATH`。

通用 MCP 启动命令：

```text
uvx cp-memory-mcp
```

该命令已从公开 PyPI 使用干净的 `uv` 缓存完成 MCP 初始化、40 个工具以及写入/检索/纠正链路验证。下列示例采用各客户端官方记录的 stdio 配置格式。Codex CLI 验收见下文；验收机器未安装其他客户端，各客户端界面中的发现和授权步骤仍标记为待手工实测。

### Codex

```text
codex mcp add cp-memory -- uvx cp-memory-mcp
codex mcp get cp-memory
```

命令格式已通过当前安装的 Codex CLI 帮助信息核对。2026-09-04 使用四个独立的 Windows Codex CLI 0.140.0 会话验证了公开发布的 `cp-memory-mcp==1.8.1`：写入合成记忆、新会话召回、纠正记忆值，再开新会话召回并恢复纠正后的值。最后两项结果均包含新值，不包含旧值。六次成功的 MCP 调用依次为 `memory_add`、`memory_recall`、`memory_probe`、`memory_correct`、`memory_recall` 和 `memory_restore_context`。

本次验收显式覆盖 `CP_MEMORY_HOME`、`CP_MEMORY_DB_PATH` 和 `CP_MEMORY_OLD_HOME`，使用临时数据库及不持久化的会话，并禁用插件、Hooks 和辅助记忆。召回调用设置 `allow_auxiliary=false`。首次非交互写入被客户端审批取消；成功运行时，经用户授权，仅对该次调用中的测试服务器预先批准工具调用，没有修改用户永久配置。这证明的是受指导的 CLI 流程，不代表默认无需审批、桌面界面行为、其他客户端或总体模型准确率。复验时应使用同一个隔离数据库启动四个全新会话，并且不要在两次召回提示中包含预期值。

Codex 插件用户可以继续使用 Marketplace 安装，以便在 MCP 工具之外获得生命周期 Hooks 和 Skills。

### Claude Code

```text
claude mcp add cp-memory -- uvx cp-memory-mcp
claude mcp get cp-memory
```

Claude Code 使用 `--` 分隔自身参数与 stdio 命令及其参数。

### Cursor

项目级配置写入 `.cursor/mcp.json`，全局配置写入 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "cp-memory": {
      "command": "uvx",
      "args": ["cp-memory-mcp"]
    }
  }
}
```

### VS Code

创建 `.vscode/mcp.json`：

```json
{
  "servers": {
    "cpMemory": {
      "type": "stdio",
      "command": "uvx",
      "args": ["cp-memory-mcp"]
    }
  }
}
```

### Gemini CLI

```text
gemini mcp add cp-memory uvx cp-memory-mcp
gemini mcp list
```

Gemini CLI 只有在当前目录受信任时才会测试本地 stdio MCP server 的连接状态。

### 数据与安全边界

- CP Memory 默认把数据保存在本地 `~/.cp-memory/memory.db`；Codex 插件和通用 MCP 命令使用同一个数据库。
- `uvx` 会访问包仓库以安装或刷新软件包；运行中的 CP Memory server 默认没有遥测或记忆上传链路。
- 备份数据库前先停止 MCP 客户端。若要重置全部记忆，应先备份再移除 `memory.db`；这是刻意保留为人工执行的破坏性操作。
- 不要提交数据库、日志、私人摘要、Token 或环境文件。

官方格式参考：[Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)、[Cursor MCP](https://docs.cursor.com/context/model-context-protocol)、[VS Code MCP 配置](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)和 [Gemini CLI MCP](https://geminicli.com/docs/tools/mcp-server/)。
