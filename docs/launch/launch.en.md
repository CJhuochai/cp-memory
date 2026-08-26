# CP Memory English Launch Post

## Title

CP Memory: local-first, explainable memory for Codex project rules

## Post

Starting a new Codex session should not mean re-explaining your project rules, preferences, and earlier decisions.

I built CP Memory to restore useful context in later sessions. The harder problem turned out not to be whether an AI can remember, but what happens when it remembers the wrong thing.

CP Memory does not try to retain every chat message. It stores rules, preferences, ongoing work, and decisions in local SQLite storage, then restores relevant context through Codex MCP tools and lifecycle hooks. It also supports explanation, correction, expiry, and scope rather than silently overwriting a bad record.

A minimal example:

```text
Remember this: before releasing this project, create a branch, run tests, and merge through a PR.
```

In a later session for the same project, Codex can restore that rule and continue following it. If the rule is no longer valid, it can be marked wrong, stale, or limited to a specific scope.

The design principles are deliberately conservative:

- Local-first by default: private memories are not uploaded.
- Relevant restore: project context should not leak across unrelated work.
- Explainable: a remembered rule needs a reason and provenance.
- Correctable: wrong and stale memory need governance history, not just deletion.

CP Memory is an open-source Codex plugin. Windows can install it through GitHub Marketplace; macOS/Linux have a source installation path with three-platform CI coverage. It does not have a graphical review UI yet. Its current pending-review reminder is injected into assistant context, not shown as a user-facing popup.

Repository, installation instructions, and a sanitized 30-second demo script:

<https://github.com/CJhuochai/cp-memory>

I would especially value feedback on two questions: what should a coding agent remember across sessions, and how should users decide that a memory should no longer be used?

## Suggested destinations

- Codex/MCP/plugin communities: use the full post above.
- GitHub Discussion or Release announcement: use the first four paragraphs plus the repository link.
- Short-form social post: use the title, the three-sentence problem statement, and the repository link.

## Publication boundaries

- Verify that no real memory records, paths, usernames, customer information, tokens, or logs appear in accompanying media.
- Do not describe the hidden assistant-context reminder as a visible notification or review panel.
- Do not claim manual real-Codex-desktop validation on macOS/Linux.
