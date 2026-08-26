#!/usr/bin/env sh
# Run install.sh in an isolated HOME without changing the real Codex profile.
set -eu

plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_home=$(mktemp -d "${TMPDIR:-/tmp}/cp-memory-install-test.XXXXXX")
cleanup() { rm -rf "$test_home"; }
trap cleanup EXIT

HOME="$test_home" sh "$plugin_root/install.sh" >/dev/null
test -f "$test_home/plugins/cp-memory/.codex-plugin/plugin.json"
test -f "$test_home/.agents/plugins/marketplace.json"
test -f "$test_home/.codex/config.toml"
test "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["mcpServers"]["cp-memory-server"]["command"])' "$test_home/plugins/cp-memory/.mcp.json")" = "$test_home/plugins/cp-memory/.venv/bin/python"
python3 - "$test_home/plugins/cp-memory" <<'PY'
import asyncio
import json
import os
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

plugin = pathlib.Path(sys.argv[1])
server = json.loads((plugin / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["cp-memory-server"]

async def verify():
    params = StdioServerParameters(
        command=server["command"],
        args=server["args"],
        cwd=plugin / server["cwd"],
        env={**os.environ, "CP_MEMORY_HOME": str(plugin / ".test-memory")},
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
    assert {"memory_recall", "memory_search", "memory_probe"}.issubset(names)

asyncio.run(verify())
PY
python3 - "$test_home/.agents/plugins/marketplace.json" <<'PY'
import json
import pathlib
import sys
assert any(item.get("name") == "cp-memory" for item in json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["plugins"])
PY

echo "POSIX isolated installation validation passed."
