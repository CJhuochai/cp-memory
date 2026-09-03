# English-First Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the GitHub landing page immediately useful to international AI Agent and MCP developers without changing CP Memory runtime behavior.

**Architecture:** Reuse the current bilingual content and demo scenario, swap the default README language, and tighten the first screen around the currently verified Codex installation. Add sanitized visual assets; verify human-facing documentation with link, image, privacy, and visual checks rather than brittle prose unit tests.

**Tech Stack:** Markdown, SVG, GIF/PNG assets, Python `unittest`, GitHub Actions badges

**Spec:** `docs/superpowers/specs/2026-09-03-international-mcp-growth-design.md`

## Global Constraints

- Existing Codex Marketplace and source-install commands keep working.
- Existing `.mcp.json`, Skills, Hooks, 40 MCP tools, and `~/.cp-memory/memory.db` behavior stay unchanged.
- Existing Windows, macOS, and Linux CI stays green.
- English and Chinese user-facing documentation carry equivalent information.
- Visuals contain no real database, logs, tokens, private summaries, local paths, or local configuration.
- Do not advertise `uvx cp-memory-mcp` before Stage 2 validates and publishes the package.

---

### Task 1: Sanitized visual assets

**Files:**
- Create: `assets/demo.gif`
- Create: `assets/social-preview.svg`
- Create: `assets/social-preview.png`

**Interfaces:**
- Consumes: `assets/logo.png` and the fictional `demo-plugin` scenario in `docs/30-second-demo.md`.
- Produces: a looping 1200×675 demo GIF and a 1280×640 social-preview PNG.

- [x] **Step 1: Create the social-preview SVG source**

Use the existing dark-blue visual language from `assets/architecture.svg` with this exact visible copy:

```text
CP Memory
Local-first, governable memory for AI coding agents
Remember • Recall • Correct
MCP baseline · Codex enhanced
```

- [x] **Step 2: Render publishable raster assets**

Render `assets/social-preview.svg` to `assets/social-preview.png`. Generate three `demo-plugin` scenes from the existing demo script and combine them into `assets/demo.gif` with these captions:

```text
1. Remember a project rule locally
2. Recall it in a later session
3. Correct bad memory without hiding history
```

Keep the PNG below 1 MB and the GIF below 10 MB.

- [x] **Step 3: Validate and visually inspect**

Use an image decoder to confirm format and exact dimensions, then open both raster assets and check readable text, framing, animation, and privacy.

- [x] **Step 4: Commit**

```powershell
git add assets/demo.gif assets/social-preview.svg assets/social-preview.png
git commit -m "docs: add sanitized launch visuals"
```

### Task 2: English-first bilingual README

**Files:**
- Rename: `README.md` to `README.zh-CN.md`
- Rename: `README.en.md` to `README.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Interfaces:**
- Consumes: current bilingual README content, verified Codex installation commands, and Task 1 assets.
- Produces: an English default landing page and an equivalent Chinese translation.

- [x] **Step 1: Rename without losing Git history**

```powershell
git mv README.md README.zh-CN.md
git mv README.en.md README.md
```

- [x] **Step 2: Replace both hero sections**

English:

```html
<p align="center">
  Local-first, governable memory for AI coding agents.<br>
  Remember project rules across sessions, recall only what matters, and correct bad memory without hiding history.
</p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a> | English
</p>
```

Chinese:

```html
<p align="center">
  面向 AI 编码 Agent 的本地优先、可治理记忆层。<br>
  跨会话记住项目规则，只恢复当前相关内容，纠正错误记忆时保留历史。
</p>

<p align="center">
  简体中文 | <a href="README.md">English</a>
</p>
```

Replace the static CI badge in both files with:

```markdown
[![Cross-platform CI](https://github.com/CJhuochai/cp-memory/actions/workflows/cross-platform.yml/badge.svg)](https://github.com/CJhuochai/cp-memory/actions/workflows/cross-platform.yml)
```

- [x] **Step 3: Tighten the first screen**

Before architecture detail, show only:

1. Three differentiators: local first, governable memory, Codex-enhanced.
2. `assets/demo.gif`.
3. The verified Codex Marketplace install command labeled as enhanced integration.

State bilingually that CP Memory already exposes a stdio MCP server, standard one-command packaging comes next, and Codex Skills/Hooks are enhancements rather than requirements of the memory model.

- [x] **Step 4: Verify README resources**

Run a local Markdown-link scan for both files, confirm every relative target exists, confirm the dynamic workflow badge URL, and review the rendered first screen.

- [x] **Step 5: Commit**

```powershell
git add README.md README.zh-CN.md README.en.md
git commit -m "docs: make the repository landing page English first"
```

### Task 3: Align linked documentation

**Files:**
- Modify: `CONTRIBUTING.md`
- Modify: `docs/comparison.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/30-second-demo.md`
- Modify: `docs/launch/launch.en.md`
- Modify: `docs/launch/launch.zh-CN.md`

**Interfaces:**
- Consumes: README filenames and portable-MCP positioning from Task 2.
- Produces: consistent bilingual contributor, comparison, roadmap, demo, and launch guidance.

- [x] **Step 1: Update README filename guidance**

Change `CONTRIBUTING.md` so README changes keep `README.md` and `README.zh-CN.md` equivalent.

- [x] **Step 2: Update positioning bilingually**

Use these equivalent boundaries in comparison, roadmap, and launch documents:

```text
中文：标准 MCP 提供跨客户端基础能力；Codex 插件额外提供 Skills 和生命周期 Hooks 增强体验。
English: Standard MCP provides the cross-client baseline; the Codex plugin adds Skills and lifecycle Hooks as an enhanced experience.
```

Retain the existing real-device macOS/Linux Codex desktop Hook caveat.

- [x] **Step 3: Align the demo script**

Link `../assets/demo.gif` from `docs/30-second-demo.md` and add the three Task 1 captions plus equivalent Chinese captions to the existing scenes.

- [x] **Step 4: Verify links and stale names**

Confirm all changed relative Markdown targets exist. `README.en.md` must remain only in historical design/plan documents, not current user or contributor guidance.

- [x] **Step 5: Commit**

```powershell
git add CONTRIBUTING.md docs/comparison.md docs/roadmap.md docs/30-second-demo.md docs/launch/launch.en.md docs/launch/launch.zh-CN.md
git commit -m "docs: align MCP and Codex positioning"
```

### Task 4: Stage acceptance

**Files:**
- Verify: all tracked files changed by Tasks 1–3

**Interfaces:**
- Consumes: all Stage 1 commits.
- Produces: evidence that documentation changes did not affect runtime, installation, or memory behavior.

- [ ] **Step 1: Run repository checks**

```powershell
git diff main...HEAD --check
git status --short
rg -n "C:\\Users|token|password|README\.en\.md" assets README.md README.zh-CN.md CONTRIBUTING.md docs
```

Review every match; generic safety guidance is allowed, private values are not.

- [ ] **Step 2: Run required verification**

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
python tests\personal_memory_benchmark.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Expected: 50/50 unit tests, 20/20 benchmark cases, and 8/8 isolated installer steps pass.

- [ ] **Step 3: Audit final scope**

```powershell
git diff --stat main...HEAD
git log --oneline main..HEAD
git status --short --branch
```

Expected: only the approved specification, implementation plan, bilingual landing-page documentation, and sanitized assets differ from `main`; the worktree is clean.
