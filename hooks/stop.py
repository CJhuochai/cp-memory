from cp_memory_common import (
    connect,
    emit_json,
    extract_assistant_message,
    extract_prompt,
    persist_personal_signals,
    persist_turn_summary,
    read_stdin_json,
    should_save_turn,
)


def main():
    data = read_stdin_json()
    prompt = extract_prompt(data)
    assistant = extract_assistant_message(data)
    if not should_save_turn(prompt, assistant):
        emit_json({})
        return

    conn = connect()
    try:
        summary_id, _ = persist_turn_summary(conn, prompt, assistant)
        persist_personal_signals(conn, prompt, assistant, summary_id=summary_id)
        conn.commit()
    finally:
        conn.close()
    emit_json({})


if __name__ == "__main__":
    main()
