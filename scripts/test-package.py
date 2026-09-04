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
EXPECTED_VERSION = "1.8.1"


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
