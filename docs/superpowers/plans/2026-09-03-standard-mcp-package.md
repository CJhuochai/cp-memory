# Standard MCP Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate CP Memory as the `cp-memory-mcp` Python distribution while preserving the existing Codex plugin entry point and database behavior.

**Architecture:** Rename the current server implementation to the importable `memory_mcp_server` module and leave the hyphenated script as a thin compatibility wrapper. Package only the two existing Python modules with setuptools, expose `cp-memory-mcp = memory_mcp_server:main`, and validate the built wheel in a fresh virtual environment through a real MCP handshake and write/search/correct cycle.

**Tech Stack:** Python 3.10+, MCP Python SDK, setuptools, PyPA build, SQLite, `unittest`

**Spec:** `docs/superpowers/specs/2026-09-03-international-mcp-growth-design.md`

## Global Constraints

- Distribution name: `cp-memory-mcp`; console command: `cp-memory-mcp`.
- Runtime dependency remains `mcp>=1.27,<2`; Python floor is `>=3.10`, matching MCP 1.27.
- Existing `.mcp.json` continues to launch `scripts/memory-mcp-server.py`.
- Existing Skills, Hooks, 40 MCP tools, and `~/.cp-memory/memory.db` behavior stay compatible.
- No database migration, telemetry, network service, or new runtime dependency.
- Release version is `1.8.0` in both `pyproject.toml` and `.codex-plugin/plugin.json`.
- Do not advertise the public `uvx` command until the PyPI artifact is uploaded and smoke-tested.

---

### Task 1: Importable server with legacy wrapper

**Files:**
- Modify: `tests/test_cp_memory.py`
- Rename: `scripts/memory-mcp-server.py` to `scripts/memory_mcp_server.py`
- Create: `scripts/memory-mcp-server.py`

**Interfaces:**
- Consumes: existing `mcp: FastMCP` and all 40 decorated tool functions.
- Produces: `memory_mcp_server.main() -> None`; legacy script re-exports the same `mcp`, `main`, and tool functions.

- [ ] **Step 1: Write the failing compatibility test**

Add:

```python
def test_importable_mcp_module_and_legacy_entrypoint_share_server(self):
    if "memory_mcp_server" in sys.modules:
        del sys.modules["memory_mcp_server"]
    packaged = importlib.import_module("memory_mcp_server")
    spec = importlib.util.spec_from_file_location(
        "legacy_memory_mcp_server",
        SCRIPTS_DIR / "memory-mcp-server.py",
    )
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)

    self.assertIs(legacy.mcp, packaged.mcp)
    self.assertIs(legacy.main, packaged.main)
    self.assertIs(legacy.memory_recall, packaged.memory_recall)
    self.assertTrue(callable(packaged.main))
```

- [ ] **Step 2: Run the test and verify RED**

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_importable_mcp_module_and_legacy_entrypoint_share_server
```

Expected: FAIL because `memory_mcp_server` does not exist.

- [ ] **Step 3: Rename the implementation and add `main`**

Move the current implementation to `scripts/memory_mcp_server.py`. Replace its bottom block with:

```python
def main() -> None:
    init_db()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

Create the compatibility wrapper:

```python
from memory_mcp_server import *  # noqa: F401,F403


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run focused and full tests**

```powershell
python -m unittest tests.test_cp_memory.CpMemoryTests.test_importable_mcp_module_and_legacy_entrypoint_share_server
python -m unittest discover -s tests -p test_cp_memory.py
```

Expected: focused test passes and all 51 tests pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_cp_memory.py scripts/memory-mcp-server.py scripts/memory_mcp_server.py
git commit -m "refactor: expose an importable MCP server entrypoint"
```

### Task 2: Python distribution and installed-wheel smoke test

**Files:**
- Create: `pyproject.toml`
- Create: `scripts/test-package.py`

**Interfaces:**
- Consumes: `memory_mcp_server.main`, `cp_memory_store`, and `mcp>=1.27,<2`.
- Produces: wheel/sdist metadata for `cp-memory-mcp==1.8.0`, console script `cp-memory-mcp`, and a clean-environment package verifier.

- [ ] **Step 1: Write the package verifier before metadata exists**

Create `scripts/test-package.py`:

```python
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.8.0"


def run(*args, cwd=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def venv_python(environment):
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def console_script(environment):
    return environment / ("Scripts/cp-memory-mcp.exe" if os.name == "nt" else "bin/cp-memory-mcp")


def result_json(result):
    if result.isError or not result.content or not hasattr(result.content[0], "text"):
        raise AssertionError(f"unexpected MCP result: {result}")
    return json.loads(result.content[0].text)


async def verify_mcp(command, memory_home):
    env = {
        **os.environ,
        "CP_MEMORY_HOME": str(memory_home),
        "CP_MEMORY_DB_PATH": str(memory_home / "memory.db"),
        "CP_MEMORY_OLD_HOME": str(memory_home / "old-home"),
    }
    params = StdioServerParameters(command=str(command), args=[], env=env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            required = {"memory_add", "memory_search", "memory_correct", "memory_recall"}
            if len(names) != 40 or not required.issubset(names):
                raise AssertionError(f"unexpected tool surface: {len(names)} tools; missing {required - names}")
            added = result_json(
                await session.call_tool(
                    "memory_add",
                    arguments={
                        "entity": "PackageSmoke",
                        "property": "release_rule",
                        "value": "Package smoke remembers branch test PR.",
                    },
                )
            )
            rows = result_json(await session.call_tool("memory_search", arguments={"query": "PackageSmoke"}))
            if added["id"] not in {row["id"] for row in rows}:
                raise AssertionError("installed server did not find the written memory")
            corrected = result_json(
                await session.call_tool(
                    "memory_correct",
                    arguments={"id": added["id"], "status": "wrong", "reason": "package smoke cleanup"},
                )
            )
            if not corrected.get("ok") or corrected.get("status") != "wrong":
                raise AssertionError(f"installed server did not correct memory: {corrected}")
            return len(names)


def main():
    with tempfile.TemporaryDirectory(prefix="cp-memory-package-") as raw_temp:
        temp = Path(raw_temp)
        artifacts = temp / "dist"
        run(sys.executable, "-m", "build", "--outdir", artifacts, ROOT)
        wheels = list(artifacts.glob("*.whl"))
        sdists = list(artifacts.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise AssertionError(f"expected one wheel and one sdist: {wheels}, {sdists}")

        environment = temp / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = venv_python(environment)
        run(python, "-m", "pip", "install", wheels[0])

        metadata_code = (
            "import importlib.metadata as m,json;"
            "d=m.distribution('cp-memory-mcp');"
            "print(json.dumps({'name':d.metadata['Name'],'version':d.version,"
            "'scripts':[e.name for e in d.entry_points if e.group=='console_scripts']}))"
        )
        metadata = json.loads(subprocess.check_output([str(python), "-c", metadata_code], text=True))
        if metadata != {"name": "cp-memory-mcp", "version": EXPECTED_VERSION, "scripts": ["cp-memory-mcp"]}:
            raise AssertionError(f"unexpected installed metadata: {metadata}")

        command = console_script(environment)
        if not command.is_file():
            raise AssertionError(f"console script is missing: {command}")
        tool_count = asyncio.run(verify_mcp(command, temp / "memory"))
        print(
            json.dumps(
                {
                    "ok": True,
                    "wheel": wheels[0].name,
                    "sdist": sdists[0].name,
                    "tool_count": tool_count,
                    "write_search_correct": True,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the verifier and verify RED**

```powershell
python -m pip install build
python scripts/test-package.py
```

Expected: FAIL because `pyproject.toml` does not exist.

- [ ] **Step 3: Add minimal `pyproject.toml`**

Use:

```toml
[build-system]
requires = ["setuptools>=77.0.3"]
build-backend = "setuptools.build_meta"

[project]
name = "cp-memory-mcp"
version = "1.8.0"
description = "Local-first, governable memory for AI coding agents"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
license-files = ["LICENSE"]
authors = [{ name = "Chen Jian" }]
dependencies = ["mcp>=1.27,<2"]
keywords = ["mcp", "agent-memory", "ai-memory", "local-first", "sqlite"]
classifiers = [
  "Development Status :: 4 - Beta",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
]

[project.urls]
Homepage = "https://github.com/CJhuochai/cp-memory"
Repository = "https://github.com/CJhuochai/cp-memory"
Issues = "https://github.com/CJhuochai/cp-memory/issues"

[project.scripts]
cp-memory-mcp = "memory_mcp_server:main"

[tool.setuptools]
package-dir = { "" = "scripts" }
py-modules = ["cp_memory_store", "memory_mcp_server"]
```

- [ ] **Step 4: Run package verification and inspect metadata**

```powershell
python scripts/test-package.py
python -m build
python -m twine check dist/*
```

Install `twine` for this verification command if it is absent. Expected: wheel/sdist build, installed console MCP smoke, and metadata checks all pass.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml scripts/test-package.py
git commit -m "feat: package CP Memory as a standard MCP server"
```

### Task 3: Installer and cross-platform CI coverage

**Files:**
- Modify: `install.ps1`
- Modify: `install.sh`
- Modify: `.github/workflows/cross-platform.yml`

**Interfaces:**
- Consumes: legacy wrapper plus importable module from Task 1 and package verifier from Task 2.
- Produces: plugin installation validation for both entrypoint files and package smoke coverage on Windows, macOS, and Ubuntu.

- [ ] **Step 1: Extend installer compile checks**

Add `scripts/memory_mcp_server.py` beside `scripts/memory-mcp-server.py` in both installer `py_compile` command lists. Do not change `.mcp.json`.

- [ ] **Step 2: Add package verification to CI**

In both jobs, install build tooling and run the verifier after unit tests:

```yaml
- run: python -m pip install build
- run: python scripts/test-package.py
```

- [ ] **Step 3: Run local integration checks**

```powershell
python scripts/test-package.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Expected: package smoke passes and all 8 installer steps pass using the unchanged legacy `.mcp.json` path.

- [ ] **Step 4: Commit**

```powershell
git add install.ps1 install.sh .github/workflows/cross-platform.yml
git commit -m "ci: validate the standard MCP package"
```

### Task 4: Version 1.8.0 release preparation

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Interfaces:**
- Consumes: validated distribution metadata from Task 2.
- Produces: synchronized 1.8.0 plugin/package metadata and honest pre-release documentation.

- [ ] **Step 1: Synchronize version and positioning**

Set `.codex-plugin/plugin.json` to `1.8.0`. Update its bilingual description to state that standard MCP is the portable baseline and Codex Skills/Hooks are the enhanced integration.

- [ ] **Step 2: Add bilingual changelog entries**

Document the importable server, `cp-memory-mcp` package, compatibility wrapper, clean wheel smoke, unchanged database, and no migration requirement under `v1.8.0` in both languages.

- [ ] **Step 3: Update README status without advertising an unavailable command**

Replace “package is the next delivery stage” with equivalent English and Chinese wording that 1.8.0 contains the package and that the public `uvx` command will be added after PyPI publication verification.

- [ ] **Step 4: Verify metadata consistency**

Run a Python check that parses `pyproject.toml` with `tomllib`, parses `.codex-plugin/plugin.json`, and asserts both versions equal `1.8.0`.

- [ ] **Step 5: Run full acceptance**

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
python tests\personal_memory_benchmark.py
python scripts/test-package.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

Expected: 51/51 unit tests, 20/20 memory benchmark, clean package smoke, and 8/8 installer steps pass.

- [ ] **Step 6: Commit**

```powershell
git add .codex-plugin/plugin.json CHANGELOG.md README.md README.zh-CN.md
git commit -m "release: prepare CP Memory 1.8.0"
```

### Task 5: Branch acceptance

**Files:**
- Verify: all files changed by Tasks 1–4

**Interfaces:**
- Consumes: all package-foundation commits.
- Produces: a reviewable PR that does not publish PyPI, create a tag, or alter the real local installation.

- [ ] **Step 1: Audit privacy, scope, and compatibility**

```powershell
git diff main...HEAD --check
git status --short
git diff --stat main...HEAD
git diff main...HEAD -- .mcp.json scripts/memory-mcp-server.py scripts/memory_mcp_server.py
```

Confirm `.mcp.json` is unchanged, the legacy wrapper is thin, the importable module contains the former implementation plus `main`, and no private files are present.

- [ ] **Step 2: Run fresh final verification**

```powershell
python -m unittest discover -s tests -p test_cp_memory.py
python tests\personal_memory_benchmark.py
python scripts/test-package.py
powershell -ExecutionPolicy Bypass -File .\scripts\test-install.ps1
```

- [ ] **Step 3: Prepare the next delivery boundary**

After PR review, merge, tag, GitHub Release, PyPI upload, and public `uvx` smoke are separate externally visible actions. Only after those succeed should a follow-up client-documentation PR advertise `uvx cp-memory-mcp`.
