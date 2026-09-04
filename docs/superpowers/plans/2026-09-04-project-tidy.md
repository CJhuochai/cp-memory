# Project Tidy Implementation Plan / 项目整理实施计划

> Execute inline without subagents. / 在当前会话执行，不委派子代理。

**Goal / 目标:** Correct project status and strengthen existing verification without changing runtime behavior. / 校准项目状态并补齐已有验证，不改变运行行为。

**Architecture / 方案:** Reuse the version consistency test and plugin manifest; extend the existing CI matrix. / 复用版本一致性测试和插件清单，扩展现有 CI 矩阵。

**Tech Stack:** Python 3.10+, unittest, GitHub Actions; no new dependencies. / 不新增依赖。

**Spec / 依据:** User-approved three-item maintenance roadmap. / 用户确认的文档、CI、版本校验三项整理。

## Scope and steps / 范围与步骤

Implementation and local verification completed on 2026-09-04: 53 unit tests, 20 benchmark cases, package smoke (40 tools / five calls), isolated Windows installation and diff checks passed. The version-mismatch mutation failed as expected and was reverted. Remote CI and PR integration remain separate. / 2026-09-04 已完成实现与本地验证：53 项单测、20 项基准、打包冒烟（40 个工具／五次调用）、Windows 隔离安装与差异检查通过。版本不一致负向检查按预期失败，测试改动已恢复。远端 CI 与 PR 集成另行确认。

- [ ] Update `docs/roadmap.md` and the tool-surface evidence plan to distinguish completed work from remaining validation. / 校准路线图和工具验证计划的完成状态与验证边界。
- [ ] Add `python -X utf8 tests/personal_memory_benchmark.py` to both CI jobs; add Ubuntu Python 3.10 while preserving existing check names. / 两类 CI 作业加入个人记忆基准，新增 Ubuntu Python 3.10，保留已有检查名称。
- [ ] Remove the fixed release assertion in `tests/test_cp_memory.py`; derive `scripts/test-package.py` expected version from `.codex-plugin/plugin.json`. Temporarily mismatch Registry version and confirm the existing consistency test fails, then restore it and confirm passing. / 去掉测试中的固定版本号，打包测试读取插件清单；临时制造 Registry 版本不一致，确认失败后恢复并验证通过。
- [ ] Run unit tests, personal benchmark, package smoke, Windows isolated installer and `git diff --check`; inspect only intended changes before commit and PR. / 运行单测、记忆基准、打包冒烟、Windows 隔离安装与差异检查，再提交 PR。

No runtime, tools, Hooks, database, release version, platform submissions or worktree cleanup changes. / 不修改运行逻辑、工具、Hooks、数据库、发布版本，不新增平台投稿，不清理工作区。
