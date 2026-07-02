import json
import sys

from cp_memory_common import connect, emit_json, persist_checkpoint, run_hook_safely


def main():
    trigger = "unknown"
    turn_id = ""
    data = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            trigger = data.get("trigger", trigger)
            turn_id = data.get("turn_id", "")
    except Exception:
        data = {}

    conn = connect()
    try:
        persist_checkpoint(conn, trigger, turn_id, data)
        conn.commit()
    finally:
        conn.close()
    emit_json({})


if __name__ == "__main__":
    run_hook_safely("PreCompact", main)
