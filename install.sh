#!/usr/bin/env sh
# Install CP Memory for local macOS/Linux Codex development.
set -eu

plugin_name="cp-memory"
plugin_source=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python_bin=$(command -v python3 || true)

if [ -z "$python_bin" ]; then
  echo "Python 3 is required. Install Python 3 and make python3 available on PATH." >&2
  exit 1
fi

plugin_target="${HOME}/plugins/${plugin_name}"
agents_home="${HOME}/.agents"
marketplace_file="${agents_home}/plugins/marketplace.json"
codex_config="${HOME}/.codex/config.toml"

mkdir -p "$plugin_target" "${agents_home}/plugins" "${HOME}/.codex"
cp -R "$plugin_source"/. "$plugin_target"/
rm -rf "$plugin_target/.git" "$plugin_target/__pycache__"

"$python_bin" - "$marketplace_file" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
    "name": "personal", "interface": {"displayName": "Personal"}, "plugins": []
}
plugins = [item for item in data.get("plugins", []) if item.get("name") != "cp-memory"]
plugins.append({
    "name": "cp-memory",
    "source": {"source": "local", "path": "./plugins/cp-memory"},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Productivity",
})
data["plugins"] = plugins
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if [ ! -f "$codex_config" ]; then
  : > "$codex_config"
fi
if ! grep -Fq '[plugins."cp-memory@personal"]' "$codex_config"; then
  printf '\n[plugins."cp-memory@personal"]\nenabled = true\n' >> "$codex_config"
fi

"$python_bin" -m py_compile \
  "$plugin_target/scripts/cp_memory_store.py" \
  "$plugin_target/scripts/memory-mcp-server.py" \
  "$plugin_target/hooks/cp_memory_common.py" \
  "$plugin_target/hooks/session_start.py" \
  "$plugin_target/hooks/user_prompt_submit.py" \
  "$plugin_target/hooks/pre_compact.py" \
  "$plugin_target/hooks/stop.py"

echo "CP Memory installed at $plugin_target. Restart Codex to load the plugin."
