from cp_memory_common import (
    build_prompt_context,
    emit_hook_context,
    emit_json,
    extract_prompt,
    read_stdin_json,
)


def main():
    data = read_stdin_json()
    prompt = extract_prompt(data)
    context, _ = build_prompt_context(prompt)
    if context:
        emit_hook_context("UserPromptSubmit", context)
    else:
        emit_json({})


if __name__ == "__main__":
    main()
