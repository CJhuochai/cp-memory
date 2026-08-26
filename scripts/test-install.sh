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
python3 - "$test_home/.agents/plugins/marketplace.json" <<'PY'
import json
import pathlib
import sys
assert any(item.get("name") == "cp-memory" for item in json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["plugins"])
PY

echo "POSIX isolated installation validation passed."
