<p align="center">
  <img src="assets/logo.png" width="140" alt="CP Memory logo">
</p>

<h1 align="center">CP Memory</h1>

<p align="center">
  A local-first memory plugin for Codex that remembers important context and keeps it reviewable, explainable, and correctable.
</p>

<p align="center">
  <a href="README.md">中文</a> | English
</p>

---

CP Memory is a local-first personal memory plugin for Codex. It stores facts, conversation summaries, personal preferences, relationships, ongoing work, decisions, and checkpoints in a local SQLite database, then restores relevant context through MCP tools and lifecycle hooks.

It is not trying to be a large memory platform. It is a memory layer for long-running personal assistant work: local, explainable, reviewable, and correctable.

## Highlights

- Local-first: data is stored under `~/.cp-memory/memory.db` by default.
- Plugin-native: supports Codex plugin metadata, MCP server, skills, and lifecycle hooks.
- Personal memory: supports profile, preference, relationship, ongoing, episode, and belief decision models.
- Governable: includes conflict detection, correction history, review queues, and governance reports.
- Conservative extraction: extracts long-term memory only from explicit signals, avoiding implementation-note noise.
- Cross-platform install: GitHub marketplace installation works through Codex plugin support on Windows, macOS, and Linux.

## Install

The recommended path is GitHub marketplace installation:

```powershell
codex plugin marketplace add CJhuochai/cp-memory
codex plugin add cp-memory@cp-memory
```

Restart Codex after installation. If Codex asks you to trust hooks, approve the CP Memory lifecycle hooks in the hooks view.

## Local Development Install

Regular users do not need to run `install.ps1`. It is mainly for local development, refreshing the personal marketplace cache, and migrating old global hook wiring from earlier versions.

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The script is currently Windows-first. GitHub marketplace installation does not depend on it.

## Configuration

Default data path:

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

## Safety

CP Memory stores local assistant memory. Do not commit your real `memory.db`, logs, private summaries, or environment files. The included `.gitignore` excludes common local database, cache, and environment files.

Automatic extraction is intentionally conservative. Generated memories can be reviewed, corrected, marked stale, or marked wrong.

## Development

Run the test suite:

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
```

Validate the installer in an isolated temporary profile without touching your real Codex configuration:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Run the broader benchmark-style check:

```powershell
python tests\personal_memory_benchmark.py
```

## License

MIT
