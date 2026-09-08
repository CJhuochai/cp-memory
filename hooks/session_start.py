import json

from cp_memory_common import build_startup_context, emit_hook_context, extract_prompt, read_stdin_json, run_hook_safely


def main():
    data = read_stdin_json()
    context, intent = build_startup_context(extract_prompt(data), event_data=data)
    if context.strip():
        emit_hook_context("SessionStart", context)
    else:
        print(json.dumps({"intent": intent}))


if __name__ == "__main__":
    run_hook_safely("SessionStart", main)
