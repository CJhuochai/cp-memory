# Reproducible verification / 可复现验证

## English

From a source checkout, install development dependencies and run:

```text
python -m pip install -r requirements.txt build
python -m unittest discover -s tests -p test_cp_memory.py
python scripts/test-package.py
python -X utf8 tests/personal_memory_benchmark.py
```

On Windows, also run `powershell -ExecutionPolicy Bypass -File scripts/test-install.ps1`. On macOS/Linux, run `sh scripts/test-install.sh`. The [cross-platform workflow](../.github/workflows/cross-platform.yml) is the authoritative CI recipe.

The package smoke builds wheel/sdist, installs the wheel in a fresh virtual environment, initializes the installed stdio server, checks 40 tools, and verifies a synthetic write/search/correct flow. Its temporary database does not read or modify your personal memory. The JSON report measures the actual tool-list payload using compact JSON encoded as UTF-8, and records successful tool calls at execution time. The three-call flow excludes initialize and tools/list; it is not a whole-agent conversation cost.

Bytes are not model tokens. These are scripted protocol checks, **not** an independent model tool-selection evaluation: `model_selection_success_rate` stays `null`. No claim of lower model cost or better selection follows from a smaller payload. Optional compact mode is not justified by size alone.

The personal-memory benchmark uses synthetic temporary data to check restore, correction, review and governance behavior. It is not a population-level accuracy score. Client-specific UI/approval flows and real macOS/Linux Codex desktop hooks remain outside these automated claims; see [client verification boundaries](mcp-clients.md).

## 中文

在源码目录中安装开发依赖后执行上述四条命令。Windows 另运行 `powershell -ExecutionPolicy Bypass -File scripts/test-install.ps1`；macOS/Linux 运行 `sh scripts/test-install.sh`。[跨平台工作流](../.github/workflows/cross-platform.yml) 是 CI 命令的权威来源。

打包冒烟构建 wheel/sdist，在全新虚拟环境中安装 wheel，初始化已安装的 stdio 服务，检查 40 个工具，并验证合成数据的写入／查询／纠错。临时数据库不会读取或修改个人记忆。JSON 报告按紧凑 JSON 的 UTF-8 字节数测量实际工具清单，并在执行时记录成功调用。三次调用不包含 initialize 和 tools/list，也不代表完整 Agent 对话成本。

字节数不是模型 token 数。这些是脚本协议检查，**不是**独立模型的工具选择评估，因此 `model_selection_success_rate` 保持 `null`。清单较小不能直接证明模型成本更低或选工具更准确；不能仅凭大小决定新增精简模式。

个人记忆基准使用临时合成数据检查恢复、纠错、审阅和治理行为，不代表总体准确率。客户端 UI／审批流程和真实 macOS/Linux Codex 桌面 Hooks 不在这些自动化结论内，详见[客户端验证边界](mcp-clients.md)。
