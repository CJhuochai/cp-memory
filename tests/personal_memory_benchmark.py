import importlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
import subprocess


PLUGIN_HOME = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_HOME / "scripts"
HOOKS_DIR = PLUGIN_HOME / "hooks"


CASES = [
    {
        "name": "profile_identity",
        "type": "profile",
        "key": "timezone",
        "value": "用户默认使用东八区 Asia/Shanghai。",
        "prompt": "你记得我的默认时区吗？",
        "expected": ["Identity", "东八区"],
    },
    {
        "name": "preference_style",
        "type": "preference",
        "key": "communication_style",
        "value": "用户喜欢中文、结论先行、直接给可执行建议。",
        "prompt": "你记得我喜欢什么沟通方式吗？",
        "expected": ["Preferences", "结论先行"],
    },
    {
        "name": "relationship_memory_system",
        "type": "relationship",
        "key": "cp_memory",
        "value": "用户把 CP Memory 当作通用个人助手记忆系统。",
        "prompt": "我和 CP Memory 的关系是什么？",
        "expected": ["Relationships", "通用个人助手"],
    },
    {
        "name": "ongoing_goal",
        "type": "ongoing",
        "key": "memory_goal",
        "value": "用户正在把 CP Memory 升级为本地优先的个人助手记忆系统。",
        "prompt": "我最近在推进什么目标？",
        "expected": ["Ongoing", "本地优先"],
    },
    {
        "name": "belief_direction",
        "type": "belief_decision",
        "key": "product_direction",
        "value": "CP Memory 不做大平台，优先成为本地优先、强解释、低运维的个人助手。",
        "prompt": "这个记忆系统的长期方向是什么？",
        "expected": ["Rules And Decisions", "不做大平台"],
    },
]


def load_store(temp_home):
    os.environ["CP_MEMORY_HOME"] = temp_home
    os.environ["CP_MEMORY_DB_PATH"] = str(Path(temp_home) / "memory.db")
    os.environ["CP_MEMORY_PLUGIN_HOME"] = str(PLUGIN_HOME)
    os.environ["CP_MEMORY_OLD_HOME"] = str(Path(temp_home) / "old-home")
    sys.path.insert(0, str(SCRIPTS_DIR))
    if "cp_memory_store" in sys.modules:
        del sys.modules["cp_memory_store"]
    return importlib.import_module("cp_memory_store")


def main():
    temp_dir = tempfile.mkdtemp(prefix="cp-memory-benchmark-")
    try:
        store = load_store(temp_dir)
        conn = store.get_db()
        store.init_db(conn)
        for case in CASES:
            store.upsert_personal_memory(
                conn,
                case["type"],
                "user",
                case["key"],
                case["value"],
                evidence_count=2,
            )
        episode_id, _, _ = store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.memory-scope",
            "用户澄清个人助手记忆系统不限定编程场景，要记住任何重要沟通内容。",
        )
        store.derive_personal_from_episode(
            conn,
            episode_id,
            "belief_decision",
            "user",
            "general_assistant_scope",
            "CP Memory 应能记住任何话题中的重要信息，不限定编程场景。",
            evidence_count=2,
        )
        conn.commit()

        results = []
        for case in CASES:
            context = store.build_restore_context(conn, prompt=case["prompt"], max_chars=2200)
            passed = all(token in context for token in case["expected"])
            results.append({"name": case["name"], "passed": passed, "expected": case["expected"]})
        episode_context = store.build_restore_context(conn, prompt="你记得我说过它不能只服务编程吗？", max_chars=2200)
        results.append(
            {
                "name": "episode_derived_belief",
                "passed": "不限定编程" in episode_context and "Rules And Decisions" in episode_context,
                "expected": ["不限定编程", "Rules And Decisions"],
            }
        )
        history_context = store.build_restore_context(conn, prompt="你还记得我那次澄清它不能只服务编程吗？", max_chars=2200)
        results.append(
            {
                "name": "episode_history_recall",
                "passed": "Relevant Episodes" in history_context and "不限定编程场景" in history_context,
                "expected": ["Relevant Episodes", "不限定编程场景"],
            }
        )
        consolidation_episode_id, _, _ = store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.consolidation",
            "用户喜欢可解释的记忆系统，并决定 CP Memory 不做大平台。",
        )
        preview = store.consolidate_episode(conn, consolidation_episode_id, subject="user", dry_run=True)
        applied = store.consolidate_episode(conn, consolidation_episode_id, subject="user", dry_run=False)
        review = store.personal_memory_review(conn, subject="user", limit=10)
        results.append(
            {
                "name": "episode_consolidation_preview",
                "passed": bool(preview["candidates"]) and bool(applied["created"]),
                "expected": ["candidates", "created"],
            }
        )
        results.append(
            {
                "name": "personal_review_dashboard",
                "passed": bool(review["counts"]) and bool(review["recent"]) and bool(review["consolidation_suggestions"]),
                "expected": ["counts", "recent", "consolidation_suggestions"],
            }
        )
        winner_id, _, _ = store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文说明。",
            evidence_count=2,
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("bench_conflict", "Personal.BeliefDecision.user", "communication_style", "用户不喜欢中文说明。", "high", "personal-assistant,belief_decision", "belief_decision", store.now_local(), store.now_local()),
        )
        store.upsert_meta(conn, "bench_conflict", 5, "", source="benchmark-conflict", summary_type="belief_decision")
        resolution = store.resolve_personal_conflict(
            conn,
            winner_id,
            loser_ids="bench_conflict",
            merged_value="用户喜欢中文说明，并希望结论先行。",
            reason="用户确认最新偏好。",
            loser_status="wrong",
        )
        conflicts_after_resolution = store.personal_memory_conflicts(conn, limit=20)
        results.append(
            {
                "name": "personal_conflict_resolution",
                "passed": bool(resolution and resolution["ok"]) and "personal_possible_contradiction" not in {item["type"] for item in conflicts_after_resolution},
                "expected": ["ok", "no contradiction"],
            }
        )
        confirmed_id, _, _ = store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language",
            "用户喜欢中文说明。",
            evidence_count=3,
            stability_score=85,
        )
        stale_id, _, _ = store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language_old",
            "用户以前偏向英文说明。",
            evidence_count=1,
            stability_score=40,
        )
        wrong_id, _, _ = store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "language_wrong",
            "用户不喜欢中文说明。",
            evidence_count=1,
            stability_score=30,
        )
        store.correct_memory(conn, confirmed_id, "confirmed", reason="用户再次确认当前偏好。")
        store.correct_memory(conn, stale_id, "stale", reason="旧偏好。")
        store.correct_memory(conn, wrong_id, "wrong", reason="错误记录。")
        filtered_context = store.build_restore_context(conn, prompt="你记得我喜欢中文说明吗？", max_chars=2200)
        review_after_resolution = store.personal_memory_review(conn, subject="user", limit=10)
        results.append(
            {
                "name": "restore_filters_inactive_memory",
                "passed": "用户喜欢中文说明。" in filtered_context and "英文说明" not in filtered_context and "不喜欢中文说明" not in filtered_context,
                "expected": ["confirmed only", "no stale", "no wrong"],
            }
        )
        results.append(
            {
                "name": "review_resolution_candidates",
                "passed": bool(review_after_resolution.get("resolution_candidates") is not None),
                "expected": ["resolution_candidates"],
            }
        )
        history_id, _, _ = store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "product_route",
            "用户最初想做平台化记忆系统。",
        )
        store.correct_memory(conn, history_id, "corrected", reason="用户改成个人助手路线。", value="用户想做个人助手级记忆系统。")
        store.correct_memory(conn, history_id, "confirmed", reason="用户再次确认个人助手路线。")
        explanation = store.explain_fact(conn, fact_id=history_id)
        results.append(
            {
                "name": "inspect_history_timeline",
                "passed": len(explanation.get("history", [])) >= 2 and any(item["event_type"] == "memory_corrected" for item in explanation.get("history", [])),
                "expected": ["history", "memory_corrected"],
            }
        )
        conn.commit()
        conn.close()
        hook_payload = json.dumps(
            {
                "prompt": "记住一下，我喜欢中文、结论先行。我最近在把 CP Memory 做成通用个人助手，不做大平台。",
                "assistant_message": "用户明确说自己喜欢中文、结论先行，并且决定 CP Memory 不做大平台，而是本地优先的通用个人助手记忆系统。",
            },
            ensure_ascii=False,
        )
        hook_env = os.environ.copy()
        hook_env["CP_MEMORY_HOME"] = temp_dir
        hook_env["CP_MEMORY_DB_PATH"] = str(Path(temp_dir) / "memory.db")
        hook_env["CP_MEMORY_PLUGIN_HOME"] = str(PLUGIN_HOME)
        hook_env["CP_MEMORY_OLD_HOME"] = str(Path(temp_dir) / "old-home")
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=hook_payload,
            text=True,
            env=hook_env,
            check=True,
            capture_output=True,
        )
        conn = store.get_db()
        store.init_db(conn)
        auto_review = store.personal_memory_review(conn, subject="user", limit=10)
        auto_context = store.build_restore_context(conn, prompt="你记得我想把 CP Memory 做成什么吗？", max_chars=2200)
        results.append(
            {
                "name": "hook_auto_extraction",
                "passed": "不做大平台" in auto_context and auto_review["counts"].get("episode", 0) >= 1,
                "expected": ["hook extraction", "episode created"],
            }
        )
        auto_candidate_id, _, _ = store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "product_direction_auto",
            "用户决定 CP Memory 不做大平台，而是通用个人助手。",
            evidence_count=1,
            stability_score=86,
            source="stop-hook-auto-extract",
        )
        store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "product_direction_manual",
            "用户希望记忆系统本地优先、强解释、低运维。",
            evidence_count=2,
            stability_score=82,
            source="memory_personal_add",
        )
        review_candidates_before = store.personal_memory_review(conn, subject="user", limit=10)
        restore_before_confirm = store.build_restore_context(conn, prompt="你记得这个记忆系统的长期方向吗？", max_chars=2200)
        store.correct_memory(conn, auto_candidate_id, "confirmed", reason="用户确认自动提炼结果。")
        review_candidates_after = store.personal_memory_review(conn, subject="user", limit=10)
        restore_after_confirm = store.build_restore_context(conn, prompt="你记得这个记忆系统的长期方向吗？", max_chars=2200)
        results.append(
            {
                "name": "auto_extract_review_queue",
                "passed": any(item["id"] == auto_candidate_id for item in review_candidates_before.get("review_candidates", []))
                and not any(item["id"] == auto_candidate_id for item in review_candidates_after.get("review_candidates", [])),
                "expected": ["review queue before", "removed after confirm"],
            }
        )
        results.append(
            {
                "name": "confirmed_auto_extract_rank_upgrade",
                "passed": "本地优先" in restore_before_confirm and "不做大平台" in restore_after_confirm,
                "expected": ["manual first", "confirmed auto restored"],
            }
        )
        governance_stats = store.auto_extract_governance_stats(conn, limit=5)
        results.append(
            {
                "name": "auto_extract_governance_stats",
                "passed": governance_stats["total"] >= 1 and "pending_review" in governance_stats and "confirmed" in governance_stats,
                "expected": ["total", "pending_review", "confirmed"],
            }
        )
        governance_report = store.governance_acceptance_report(conn, limit=5)
        results.append(
            {
                "name": "governance_acceptance_report",
                "passed": governance_report["gates"]["has_personal_memory"] and bool(governance_report["restore_probes"]) and "auto_extract_governance" in governance_report,
                "expected": ["gates", "restore_probes", "auto_extract_governance"],
            }
        )
        noisy_hook_payload = json.dumps(
            {
                "prompt": "继续说明一下自动提炼是怎么实现的。",
                "assistant_message": "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口，比如“用户喜欢… / 用户决定… / 用户最近在… / 用户默认…”这类句子才会被处理。",
            },
            ensure_ascii=False,
        )
        conn.commit()
        conn.close()
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=noisy_hook_payload,
            text=True,
            env=hook_env,
            check=True,
            capture_output=True,
        )
        conn = store.get_db()
        store.init_db(conn)
        noise_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM facts f JOIN memory_meta m ON m.fact_id = f.id "
            "WHERE m.source='stop-hook-auto-extract' AND f.value LIKE '%cp_memory_common.py%'"
        ).fetchone()["cnt"]
        results.append(
            {
                "name": "auto_extract_ignores_meta_examples",
                "passed": noise_count == 0,
                "expected": ["no meta-example extraction"],
            }
        )
        cleanup_preview = store.cleanup_auto_extract_noise(conn, dry_run=True, limit=10, action="mark_wrong")
        results.append(
            {
                "name": "auto_extract_cleanup_preview",
                "passed": cleanup_preview.get("action") == "mark_wrong" and "candidate_count" in cleanup_preview and isinstance(cleanup_preview["candidates"], list),
                "expected": ["action", "candidate_count", "candidates"],
            }
        )
        conn.close()
        passed_count = sum(1 for result in results if result["passed"])
        output = {
            "ok": passed_count == len(results),
            "passed": passed_count,
            "total": len(results),
            "results": results,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if output["ok"] else 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
