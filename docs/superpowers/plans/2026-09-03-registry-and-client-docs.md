# CP Memory 1.8.1 Registry And Client Docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a registry-ready CP Memory 1.8.1 package and document the verified `uvx cp-memory-mcp` setup for common MCP clients.

**Architecture:** Keep the existing MCP implementation and 40-tool surface unchanged. Add the PyPI ownership marker required by the official MCP Registry, a schema-valid root `server.json`, and bilingual client configuration guidance; release them as a patch because PyPI 1.8.0 metadata is immutable.

**Tech Stack:** Python packaging, JSON, Markdown, GitHub Actions, PyPI Trusted Publishing, official MCP Registry.

**Spec:** `docs/superpowers/specs/2026-09-03-international-mcp-growth-design.md`

## Global Constraints

- Preserve the existing Codex plugin, lifecycle Hooks, 40 MCP tools, and `~/.cp-memory/memory.db` format and location.
- Use `cp-memory-mcp` as the PyPI distribution and `uvx cp-memory-mcp` as the portable launch command.
- Use Registry name `io.github.CJhuochai/cp-memory` and official schema `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`.
- Keep all user-facing and maintainer-facing documentation bilingual.
- Do not commit databases, logs, tokens, private summaries, or local configuration.
- Do not publish 1.8.1 or the Registry entry until the release PR is merged and the external actions are explicitly confirmed.

---

### Task 1: Registry-ready 1.8.1 metadata

**Files:**
- Modify: `tests/test_cp_memory.py`
- Create: `server.json`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `pyproject.toml`
- Modify: `.codex-plugin/plugin.json`
- Modify: `scripts/test-package.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: the existing `cp-memory-mcp` console entry point and version fields.
- Produces: Registry identity `io.github.CJhuochai/cp-memory` and synchronized version `1.8.1`.

- [ ] **Step 1: Add a failing registry metadata contract test**

Add `SERVER_MANIFEST = PLUGIN_HOME / "server.json"` and a test that loads `pyproject.toml` with `tomllib`, then asserts:

```python
def test_registry_metadata_matches_python_distribution(self):
    import tomllib

    package = tomllib.loads((PLUGIN_HOME / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    plugin = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    registry = json.loads(SERVER_MANIFEST.read_text(encoding="utf-8"))
    readme = (PLUGIN_HOME / "README.md").read_text(encoding="utf-8")

    self.assertEqual(package["version"], "1.8.1")
    self.assertEqual(plugin["version"], package["version"])
    self.assertEqual(registry["name"], "io.github.CJhuochai/cp-memory")
    self.assertEqual(registry["version"], package["version"])
    self.assertEqual(registry["packages"], [{
        "registryType": "pypi",
        "identifier": package["name"],
        "version": package["version"],
        "transport": {"type": "stdio"},
    }])
    self.assertIn("<!-- mcp-name: io.github.CJhuochai/cp-memory -->", readme)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_registry_metadata_matches_python_distribution
```

Expected: FAIL because `server.json` does not exist.

- [ ] **Step 3: Add the minimum Registry metadata and synchronized patch version**

Create `server.json`:

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.CJhuochai/cp-memory",
  "title": "CP Memory",
  "description": "Local-first, governable long-term memory for AI coding agents",
  "repository": {
    "url": "https://github.com/CJhuochai/cp-memory",
    "source": "github"
  },
  "version": "1.8.1",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "cp-memory-mcp",
      "version": "1.8.1",
      "transport": { "type": "stdio" }
    }
  ]
}
```

Add this hidden ownership marker to both README variants near the title:

```html
<!-- mcp-name: io.github.CJhuochai/cp-memory -->
```

Set `1.8.1` in `pyproject.toml`, `.codex-plugin/plugin.json`, and `scripts/test-package.py`. Add bilingual `v1.8.1` changelog entries explaining the public `uvx` path, Registry ownership marker, client docs, and that no database migration or MCP API change is required.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the focused test from Step 2. Expected: PASS.

- [ ] **Step 5: Commit the metadata contract**

```powershell
git add tests/test_cp_memory.py server.json README.md README.zh-CN.md pyproject.toml .codex-plugin/plugin.json scripts/test-package.py CHANGELOG.md
git commit -m "release: prepare registry-ready 1.8.1 metadata"
```

---

### Task 2: Verified portable setup and client configurations

**Files:**
- Modify: `tests/test_cp_memory.py`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Create: `docs/mcp-clients.md`

**Interfaces:**
- Consumes: public command `uvx cp-memory-mcp` and the existing default database path.
- Produces: copyable setup examples for Codex, Claude Code, Cursor, VS Code, and Gemini CLI.

- [ ] **Step 1: Add a failing documentation contract test**

Add `CLIENT_DOC = PLUGIN_HOME / "docs" / "mcp-clients.md"` and a test that asserts both README variants contain `uvx cp-memory-mcp`, that the client document contains each client name, and that these exact portable forms appear:

```python
def test_portable_client_docs_cover_supported_clients(self):
    english = (PLUGIN_HOME / "README.md").read_text(encoding="utf-8")
    chinese = (PLUGIN_HOME / "README.zh-CN.md").read_text(encoding="utf-8")
    clients = CLIENT_DOC.read_text(encoding="utf-8")
    self.assertIn("uvx cp-memory-mcp", english)
    self.assertIn("uvx cp-memory-mcp", chinese)
    for name in ("Codex", "Claude Code", "Cursor", "VS Code", "Gemini CLI"):
        self.assertIn(name, clients)
    self.assertIn("codex mcp add cp-memory -- uvx cp-memory-mcp", clients)
    self.assertIn("claude mcp add cp-memory -- uvx cp-memory-mcp", clients)
    self.assertIn("gemini mcp add cp-memory uvx cp-memory-mcp", clients)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_portable_client_docs_cover_supported_clients
```

Expected: FAIL because `docs/mcp-clients.md` does not exist and the READMEs still describe PyPI as pending.

- [ ] **Step 3: Document only the verified portable baseline**

Replace the pending status callouts in both READMEs with a portable quick start:

```text
uvx cp-memory-mcp
```

State that PyPI 1.8.0 passed a clean-cache MCP handshake with 40 tools and write/search/correct, and link to `docs/mcp-clients.md`.

Create `docs/mcp-clients.md` with equivalent Chinese and English sections containing:

```text
codex mcp add cp-memory -- uvx cp-memory-mcp
claude mcp add cp-memory -- uvx cp-memory-mcp
gemini mcp add cp-memory uvx cp-memory-mcp
```

For Cursor, document `.cursor/mcp.json` or `~/.cursor/mcp.json`:

```json
{"mcpServers":{"cp-memory":{"command":"uvx","args":["cp-memory-mcp"]}}}
```

For VS Code, document `.vscode/mcp.json`:

```json
{"servers":{"cpMemory":{"type":"stdio","command":"uvx","args":["cp-memory-mcp"]}}}
```

Label the server runtime as verified independently through MCP protocol smoke testing. Label client UI discovery and approval steps as client-specific, because the current machine does not have Claude Code, Cursor, VS Code, or Gemini CLI installed for interactive UI validation.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the focused test from Step 2. Expected: PASS.

- [ ] **Step 5: Validate both JSON examples**

Parse the Cursor and VS Code JSON blocks with Python `json.loads`, and assert each launches `uvx` with `cp-memory-mcp`.

- [ ] **Step 6: Commit the client documentation**

```powershell
git add tests/test_cp_memory.py README.md README.zh-CN.md docs/mcp-clients.md
git commit -m "docs: add portable MCP client setup"
```

---

### Task 3: Release and Registry acceptance gates

**Files:**
- Verify only: repository tree and generated package artifacts.

**Interfaces:**
- Consumes: Task 1 release metadata and Task 2 client docs.
- Produces: a reviewable release PR; publishing remains behind explicit external-action confirmation.

- [ ] **Step 1: Validate `server.json` against the official schema**

Fetch `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` and validate `server.json` with the already installed `jsonschema` library. Expected: validation succeeds.

- [ ] **Step 2: Run repository and installer tests**

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Expected: all unit tests and all 8 installer steps pass.

- [ ] **Step 3: Build and smoke-test the package**

```powershell
python scripts/test-package.py
python -m build
python -m twine check dist/*
```

Expected: one 1.8.1 wheel, one 1.8.1 sdist, 40 MCP tools, and successful write/search/correct.

- [ ] **Step 4: Inspect the built PyPI description**

Open the wheel or sdist metadata and assert it contains `mcp-name: io.github.CJhuochai/cp-memory`; this proves the later Registry ownership check can see the marker after PyPI publication.

- [ ] **Step 5: Audit the commit and open a PR**

Confirm the diff contains only release metadata, tests, bilingual documentation, and `server.json`; confirm no database, logs, token, or private data are tracked. Push `codex-cj-release/1.8.1-registry` and open a PR to `main`.

- [ ] **Step 6: Stop at the external release gate**

After CI passes, request one explicit confirmation covering administrator merge, tag/GitHub Release `v1.8.1`, PyPI Trusted Publishing, and MCP Registry authentication/publication. Do not perform those irreversible external actions before confirmation.
