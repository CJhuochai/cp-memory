# CP Memory

[中文](README.md) | English

CP Memory is a local-first memory plugin for Codex. It stores facts, conversation summaries, personal memories, decisions, checkpoints, and audit links in a local SQLite database, then restores relevant context through MCP tools and lifecycle hooks.

The goal is not to build a large platform. CP Memory is meant to be a personal assistant memory system that can follow long-running work: local, explainable, reviewable, and correctable.

## Features

- Local SQLite storage under `~/.cp-memory/memory.db` by default.
- Codex plugin metadata, skills, lifecycle hooks, and MCP server support.
- Six personal-memory models: profile, preference, relationship, ongoing, episode, and belief decision.
- Conservative automatic extraction from completed turns.
- Review, conflict detection, correction history, and governance reports.
- Optional weekly maintenance automation for health checks and cleanup previews.

## Requirements

- Codex with plugin support.
- Python 3.10 or newer.
- Windows PowerShell if you use the bundled installer.

## Install From GitHub

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin add cp-memory@cp-memory
```

Restart Codex after installation. Open the hooks view and trust the CP Memory lifecycle hooks if Codex asks.

## Local Install

From a local checkout:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer registers the plugin in your personal marketplace, refreshes the local plugin cache, enables the plugin, provisions the weekly maintenance automation, and removes legacy global hook wiring if present.

## Configuration

By default, CP Memory stores data in:

```text
~/.cp-memory/memory.db
```

You can override paths with environment variables:

```text
CP_MEMORY_HOME
CP_MEMORY_DB_PATH
CP_MEMORY_PLUGIN_HOME
CP_MEMORY_OLD_HOME
```

## Safety Notes

CP Memory stores local assistant memory. Do not commit your real `memory.db`, logs, private summaries, or environment files. The included `.gitignore` excludes common local database, cache, and environment files.

Automatic extraction is intentionally conservative. Generated memories can be reviewed, corrected, marked stale, or marked wrong.

## Development

Run the test suite:

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

Run the broader benchmark-style check:

```powershell
python tests\personal_memory_benchmark.py
```

## License

MIT
