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


async def verify_mcp(command, memory_home, report=None):
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
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            calls = []

            async def call_tool(name, arguments):
                result = await session.call_tool(name, arguments=arguments)
                result_json(result)
                calls.append(name)
                return result
            required = {"memory_add", "memory_search", "memory_correct", "memory_recall"}
            if len(names) != 40 or not required.issubset(names):
                raise AssertionError(f"unexpected tool surface: {len(names)} tools; missing {required - names}")
            added = result_json(
                await call_tool(
                    "memory_add",
                    arguments={
                        "entity": "PackageSmoke",
                        "property": "release_rule",
                        "value": "Package smoke remembers branch test PR.",
                        "category": "belief_decision",
                    },
                )
            )
            rows = result_json(await call_tool("memory_search", arguments={"query": "PackageSmoke"}))
            if added["id"] not in {row["id"] for row in rows}:
                raise AssertionError("installed server did not find the written memory")
            recalled = result_json(await call_tool(
                "memory_recall", arguments={"query": "PackageSmoke", "allow_auxiliary": False}
            ))
            if added["id"] not in {row["id"] for row in recalled["cp_memory"]["records"]}:
                raise AssertionError("installed server did not recall the written memory")
            if recalled["used_auxiliary"] or recalled["codex_memory"]["records"]:
                raise AssertionError("isolated recall unexpectedly used auxiliary memory")
            if "Package smoke remembers branch test PR." not in recalled["cp_memory"]["context"]:
                raise AssertionError("active memory was missing from restore context before correction")
            corrected = result_json(
                await call_tool(
                    "memory_correct",
                    arguments={"id": added["id"], "status": "wrong", "reason": "package smoke cleanup"},
                )
            )
            if not corrected.get("ok") or corrected.get("status") != "wrong":
                raise AssertionError(f"installed server did not correct memory: {corrected}")
            restored = result_json(await call_tool(
                "memory_restore_context", arguments={"prompt": "PackageSmoke"}
            ))
            if "Package smoke remembers branch test PR." in restored["context"]:
                raise AssertionError("wrong memory was still injected into restore context")
            if report is not None:
                def utf8_bytes(value):
                    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

                tools = [tool.model_dump(mode="json", exclude_none=True) for tool in listed.tools]
                report.update({
                    "tools_list_payload_utf8_bytes": utf8_bytes({"tools": tools}),
                    "input_schemas_utf8_bytes": sum(utf8_bytes(tool["inputSchema"]) for tool in tools),
                    "successful_tool_calls": calls,
                    "tool_call_count": len(calls),
                    "model_selection_success_rate": None,
                })
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
        report = {}
        tool_count = asyncio.run(verify_mcp(command, temp / "memory", report))
        assert report["successful_tool_calls"] == [
            "memory_add", "memory_search", "memory_recall", "memory_correct", "memory_restore_context"
        ]
        assert report["tool_call_count"] == 5
        assert 0 < report["input_schemas_utf8_bytes"] < report["tools_list_payload_utf8_bytes"]
        print(
            json.dumps(
                {
                    "ok": True,
                    "wheel": wheels[0].name,
                    "sdist": sdists[0].name,
                    "tool_count": tool_count,
                    "write_search_correct": True,
                    "recall_primary_only": True,
                    "wrong_memory_not_restored": True,
                    "protocol_measurements": report,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
