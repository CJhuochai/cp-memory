# CP Memory Growth Launch Materials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve first-visit comprehension with accurate bilingual README copy and a reusable sanitized demo script.

**Architecture:** Documentation-only change. The two READMEs remain equivalent, and the demo script is a standalone bilingual Markdown asset that can later guide a GIF, video, or launch post without exposing real memory data.

**Tech Stack:** Markdown, existing repository assets.

**Spec:** `docs/superpowers/specs/2026-08-26-growth-launch-materials-design.md`

## Global Constraints

- Do not change runtime code, hooks, installers, manifests, or version numbers.
- Keep all user-facing and maintainer-facing material bilingual.
- Use only fictional, sanitized examples.
- State hidden assistant-context reminders accurately.

---

### Task 1: Align README landing copy and safety claims

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

**Interfaces:**
- Consumes: Existing install, platform-support, asset, and safety sections.
- Produces: Equivalent Chinese and English first-visit messaging.

- [x] **Step 1: Replace the hero sentence with an outcome-led statement**

Use the Chinese sentence `让 Codex 跨会话记住项目规则：本地保存、按需恢复、可解释且可纠错。` and its English equivalent `Help Codex keep project rules across sessions: local storage, relevant restore, explainable memory, and safe correction.`

- [x] **Step 2: Add a short concrete three-step outcome before architecture details**

Show the sequence `state a rule -> start a later session -> receive relevant restored context`, without claiming a visible product UI.

- [x] **Step 3: Correct the review-reminder wording in both safety sections**

State that the current reminder is injected into assistant context and does not create a user-facing popup or visible review panel.

- [x] **Step 4: Verify bilingual parity and Markdown integrity**

Run: `git diff --check`

Expected: exit code 0 and no whitespace errors.

### Task 2: Add a reusable bilingual 30-second demonstration script

**Files:**
- Create: `docs/30-second-demo.md`

**Interfaces:**
- Consumes: Existing fictional release-rule example and privacy boundaries.
- Produces: A shot-by-shot script usable for a GIF, video, README link, and launch posts.

- [x] **Step 1: Write a Chinese and English three-scene script**

Use one fictional release-rule workflow: record the rule, restore it in a later session, then correct a deliberately wrong memory. Label every scene as sanitized.

- [x] **Step 2: Add capture guidance and a privacy checklist**

Require a clean demo profile, fictional repository name, no local paths, no real memory records, and no account identifiers.

- [x] **Step 3: Link the script from both READMEs**

Place the link immediately after the 30-second example so visitors can find the proof material before deep technical sections.

- [x] **Step 4: Verify all documentation changes**

Run: `git diff --check; python -m unittest discover -s tests -p test_cp_memory.py`

Expected: exit code 0 and 50 passing tests.
