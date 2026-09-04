# Tool Surface Evidence Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. No subagents.

**Goal:** Make stage 4 protocol measurements reproducible without changing memory behavior.

**Architecture:** Extend the existing isolated package smoke report; keep its real MCP assertions and record calls where they execute. Reuse the existing personal-memory benchmark.

**Tech Stack:** Python 3.10+, standard library, existing MCP SDK.

**Spec:** `docs/superpowers/specs/2026-09-03-international-mcp-growth-design.md`

## Constraints / 约束

Keep all 40 tools, hooks and database formats unchanged. No new dependencies, private data, telemetry or model calls. Documentation is bilingual.

保持 40 个工具、Hooks 和数据库格式不变。不新增依赖、私人数据、遥测或模型调用。文档提供中英双语。

## Task 1: Protocol report / 协议报告

- [ ] Modify `scripts/test-package.py`: retain `verify_mcp`'s integer return and add an optional report dictionary. Serialize the actual `tools/list` result with `ensure_ascii=False`, compact separators and UTF-8 encoding. Record successful `call_tool` names inside a local wrapper, not a hard-coded count.
- [ ] Run the existing build/install/initialize/write/search/correct smoke and assert the report contains 40 tools, positive schema bytes, and exactly the three executed calls. Command: `python scripts/test-package.py`.
- [ ] Re-run `python -m unittest discover -s tests -p test_cp_memory.py` and `powershell -ExecutionPolicy Bypass -File scripts/test-install.ps1`.

## Task 2: Trust evidence / 信任证据

- [ ] Add `docs/verification.md` and link it from both READMEs. Include the package-smoke and personal-memory benchmark commands, temporary database isolation, byte-versus-token distinction, and scripted-call-versus-model-selection distinction.
- [ ] Run `python -X utf8 tests/personal_memory_benchmark.py`. Report only actual results and state that cross-client UI and independent model tool-selection rates remain unmeasured.
- [ ] Inspect the diff and `git status --short`, then commit only the report and bilingual documentation files.

## Remaining stage 4/5 scope / 阶段 4/5 剩余范围

This increment does not complete stage 4: an independent model-selection evaluation and additional representative flows remain required. Do not infer success from scripted calls or add compact mode based on byte size alone. Community submissions require separate final publication approval.

本增量不代表阶段 4 完成：仍需独立模型工具选择评估和更多典型流程。不得将脚本调用成功当作模型选择成功，也不根据字节数单独新增精简模式。社区投稿另行确认最终发布内容。
