import json

from cp_memory_common import build_startup_context, emit_hook_context


def main():
    context, intent = build_startup_context("")
    if context.strip():
        emit_hook_context("SessionStart", context)
    else:
        print(json.dumps({"intent": intent}))


if __name__ == "__main__":
    main()
