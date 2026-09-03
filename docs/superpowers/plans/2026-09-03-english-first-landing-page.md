# English-First Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the GitHub landing page immediately useful to international AI Agent and MCP developers without changing CP Memory runtime behavior.

**Architecture:** Keep the current documentation content and assets as the source of truth, swap the default README language, and tighten the first screen around one verified Codex installation path. Add deterministic, sanitized visual assets and documentation contract tests so later packaging work can replace the install path without silently regressing language links, CI evidence, or privacy boundaries.

**Tech Stack:** Markdown, SVG, GIF/PNG assets, Python `unittest`, GitHub Actions badges

**Spec:** `docs/superpowers/specs/2026-09-03-international-mcp-growth-design.md`

## Global Constraints

- Existing Codex Marketplace and source-install commands keep working.
- Existing `.mcp.json`, Skills, and Hooks keep their behavior.
- All existing 40 MCP tools keep compatible names and parameters in the default full mode.
- Existing databases require no migration; standard MCP and the Codex plugin use the same `~/.cp-memory/memory.db` by default.
- Existing Windows, macOS, and Linux CI stays green.
- All user-facing and maintainer-facing documentation must carry equivalent English and Chinese information.
- No real database, logs, tokens, private summaries, local paths, or local configuration may appear in visual assets or commits.

---

### Task 1: Landing-page contract test

**Files:**
- Modify: `tests/test_cp_memory.py`
- Test: `tests/test_cp_memory.py`

**Interfaces:**
- Consumes: repository files rooted at the existing `PLUGIN_HOME` constant.
- Produces: `CpMemoryTests.test_readme_is_english_first_and_bilingual()` and `CpMemoryTests.test_readme_visual_assets_are_publishable()`.

- [ ] **Step 1: Write the failing language and evidence test**

Add constants beside the existing repository-path constants:

```python
README_FILE = PLUGIN_HOME / "README.md"
README_ZH_FILE = PLUGIN_HOME / "README.zh-CN.md"
DEMO_GIF = PLUGIN_HOME / "assets" / "demo.gif"
SOCIAL_PREVIEW = PLUGIN_HOME / "assets" / "social-preview.png"
```

Add this test to `CpMemoryTests`:

```python
def test_readme_is_english_first_and_bilingual(self):
    english = README_FILE.read_text(encoding="utf-8")
    chinese = README_ZH_FILE.read_text(encoding="utf-8")
    self.assertIn("Local-first, governable memory for AI coding agents", english)
    self.assertIn('<a href="README.zh-CN.md">简体中文</a> | English', english)
    self.assertIn('简体中文 | <a href="README.md">English</a>', chinese)
    self.assertIn("actions/workflows/cross-platform.yml/badge.svg", english)
    self.assertIn("assets/demo.gif", english)
    self.assertIn("assets/demo.gif", chinese)
    self.assertNotIn("CI-Windows%20%7C%20macOS%20%7C%20Linux-success.svg", english)
```

- [ ] **Step 2: Write the failing visual validation test**

Add a standard-library-only header and size check:

```python
def test_readme_visual_assets_are_publishable(self):
    self.assertEqual(DEMO_GIF.read_bytes()[:6], b"GIF89a")
    preview = SOCIAL_PREVIEW.read_bytes()
    self.assertEqual(preview[:8], b"\x89PNG\r\n\x1a\n")
    self.assertLess(DEMO_GIF.stat().st_size, 10 * 1024 * 1024)
    self.assertLess(SOCIAL_PREVIEW.stat().st_size, 1024 * 1024)
```

- [ ] **Step 3: Run the focused tests and verify failure**

Run:

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_readme_is_english_first_and_bilingual tests.test_cp_memory.CpMemoryTests.test_readme_visual_assets_are_publishable
```

Expected: both tests fail because `README.zh-CN.md`, `assets/demo.gif`, and `assets/social-preview.png` do not exist.

- [ ] **Step 4: Commit the failing contract**

```powershell
git add tests/test_cp_memory.py
git commit -m "test: define international landing page contract"
```

### Task 2: Sanitized visual assets

**Files:**
- Create: `assets/demo.gif`
- Create: `assets/social-preview.svg`
- Create: `assets/social-preview.png`
- Test: `tests/test_cp_memory.py`

**Interfaces:**
- Consumes: `assets/logo.png`, the fictional `demo-plugin` scenario in `docs/30-second-demo.md`, and the size/header assertions from Task 1.
- Produces: a three-scene animated GIF referenced by both READMEs and a 1280×640 social-preview PNG suitable for GitHub Repository Settings.

- [ ] **Step 1: Add the social-preview SVG source**

Create a 1280×640 SVG with this exact visible copy:

```text
CP Memory
Local-first, governable memory for AI coding agents
Remember • Recall • Correct
MCP baseline · Codex enhanced
```

Use the existing dark-blue visual language from `assets/architecture.svg`, high-contrast text, and no local or personal data.

- [ ] **Step 2: Render the social-preview PNG**

Render `assets/social-preview.svg` to `assets/social-preview.png` at 1280×640 using the available local image renderer. Verify the PNG signature, dimensions, and size below 1 MB.

- [ ] **Step 3: Render the three-scene demo GIF**

Create a 1200×675 animated GIF with three sanitized scenes and these exact captions:

```text
1. Remember a project rule locally
2. Recall it in a later session
3. Correct bad memory without hiding history
```

Use only the fictional project name `demo-plugin` and the release rule from `docs/30-second-demo.md`. Keep the file below 10 MB and loop continuously.

- [ ] **Step 4: Run the focused visual test**

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_readme_visual_assets_are_publishable
```

Expected: PASS.

- [ ] **Step 5: Visually inspect both assets**

Open `assets/demo.gif` and `assets/social-preview.png`; confirm readable text, correct framing, no clipping, and no personal data.

- [ ] **Step 6: Commit the assets**

```powershell
git add assets/demo.gif assets/social-preview.svg assets/social-preview.png
git commit -m "docs: add sanitized launch visuals"
```

### Task 3: English-first bilingual README

**Files:**
- Rename: `README.md` to `README.zh-CN.md`
- Rename: `README.en.md` to `README.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/test_cp_memory.py`

**Interfaces:**
- Consumes: the current equivalent README content, verified Codex installation commands, and Task 2 visual paths.
- Produces: the English default landing page and an equivalent Chinese translation.

- [ ] **Step 1: Rename the README files without losing history**

```powershell
git mv README.md README.zh-CN.md
git mv README.en.md README.md
```

- [ ] **Step 2: Replace the English first screen**

Use this exact value proposition and language navigation:

```html
<p align="center">
  Local-first, governable memory for AI coding agents.<br>
  Remember project rules across sessions, recall only what matters, and correct bad memory without hiding history.
</p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a> | English
</p>
```

Replace the static CI badge with:

```markdown
[![Cross-platform CI](https://github.com/CJhuochai/cp-memory/actions/workflows/cross-platform.yml/badge.svg)](https://github.com/CJhuochai/cp-memory/actions/workflows/cross-platform.yml)
```

Show `assets/demo.gif` immediately after a three-bullet “Why CP Memory” section. Keep the currently verified Codex Marketplace command as the only hero install path and label it `Codex (enhanced integration)`. Do not mention `uvx` until Stage 2 validates the package.

- [ ] **Step 3: Apply equivalent Chinese copy**

Use this exact translated value proposition and navigation:

```html
<p align="center">
  面向 AI 编码 Agent 的本地优先、可治理记忆层。<br>
  跨会话记住项目规则，只恢复当前相关内容，纠正错误记忆时保留历史。
</p>

<p align="center">
  简体中文 | <a href="README.md">English</a>
</p>
```

Use the same badge, demo, section order, installation facts, platform caveats, and security boundaries as the English page.

- [ ] **Step 4: Clarify portable MCP versus Codex enhancement**

In both languages, state the current boundary exactly: CP Memory already exposes a stdio MCP server, but the verified packaged install is currently the Codex plugin/source installer; standard one-command MCP packaging arrives in the next delivery stage. Describe Codex Skills and lifecycle Hooks as enhancements, not requirements of the memory model.

- [ ] **Step 5: Run the focused language test**

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_readme_is_english_first_and_bilingual
```

Expected: PASS.

- [ ] **Step 6: Commit the README landing page**

```powershell
git add README.md README.zh-CN.md README.en.md
git commit -m "docs: make the repository landing page English first"
```

### Task 4: Align linked documentation

**Files:**
- Modify: `CONTRIBUTING.md`
- Modify: `docs/comparison.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/30-second-demo.md`
- Modify: `docs/launch/launch.en.md`
- Modify: `docs/launch/launch.zh-CN.md`
- Test: `tests/test_cp_memory.py`

**Interfaces:**
- Consumes: the positioning and language filenames from Task 3.
- Produces: documentation that consistently treats standard MCP as the portable baseline and Codex as the enhanced integration.

- [ ] **Step 1: Update maintainer language-file guidance**

Change `CONTRIBUTING.md` so README changes keep `README.md` and `README.zh-CN.md` equivalent; remove `README.en.md` as the English filename.

- [ ] **Step 2: Update positioning documents bilingually**

Replace claims that other clients are not a priority with these equivalent boundaries:

```text
中文：标准 MCP 提供跨客户端基础能力；Codex 插件额外提供 Skills 和生命周期 Hooks 增强体验。
English: Standard MCP provides the cross-client baseline; the Codex plugin adds Skills and lifecycle Hooks as an enhanced experience.
```

Keep the existing disclosure that macOS/Linux Codex desktop Hook injection has not received real-device manual smoke testing.

- [ ] **Step 3: Make the demo script match the generated asset**

Keep the three existing scenes but add the exact English captions from Task 2 and their equivalent Chinese captions. Link to `../assets/demo.gif` from `docs/30-second-demo.md`.

- [ ] **Step 4: Add a broken-link filename assertion**

Extend `test_readme_is_english_first_and_bilingual()`:

```python
for path in (PLUGIN_HOME / "CONTRIBUTING.md", PLUGIN_HOME / "docs" / "comparison.md"):
    self.assertNotIn("README.en.md", path.read_text(encoding="utf-8"))
```

- [ ] **Step 5: Run the focused test and full regression**

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_readme_is_english_first_and_bilingual
python -m unittest discover -s tests -p test_cp_memory.py
```

Expected: focused test passes and all 52 tests pass.

- [ ] **Step 6: Commit documentation alignment**

```powershell
git add CONTRIBUTING.md docs/comparison.md docs/roadmap.md docs/30-second-demo.md docs/launch/launch.en.md docs/launch/launch.zh-CN.md tests/test_cp_memory.py
git commit -m "docs: align MCP and Codex positioning"
```

### Task 5: Stage acceptance

**Files:**
- Verify: all tracked files changed by Tasks 1–4

**Interfaces:**
- Consumes: all Stage 1 commits.
- Produces: evidence that the landing-page changes do not affect CP Memory runtime, installation, or memory behavior.

- [ ] **Step 1: Run whitespace and privacy checks**

```powershell
git diff main...HEAD --check
git status --short
rg -n "C:\\Users|token|password|memory\.db" assets README.md README.zh-CN.md docs
```

Review matches and confirm every remaining `memory.db` mention is generic documentation rather than a real file or path.

- [ ] **Step 2: Run the required verification suite**

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
python tests\personal_memory_benchmark.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Expected: 52/52 unit tests, 20/20 benchmark cases, and 8/8 isolated installer steps pass.

- [ ] **Step 3: Inspect the final diff and commit state**

```powershell
git diff --stat main...HEAD
git log --oneline main..HEAD
git status --short --branch
```

Expected: only the approved specification, implementation plan, bilingual landing-page documentation, tests, and sanitized assets differ from `main`; the worktree is clean.
