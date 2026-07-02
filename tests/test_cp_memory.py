import importlib
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_HOME = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_HOME / "scripts"
HOOKS_DIR = PLUGIN_HOME / "hooks"
PLUGIN_MANIFEST = PLUGIN_HOME / ".codex-plugin" / "plugin.json"
INSTALL_SCRIPT = PLUGIN_HOME / "install.ps1"
INSTALL_TEST_SCRIPT = PLUGIN_HOME / "scripts" / "test-install.ps1"
MCP_CONFIG = PLUGIN_HOME / ".mcp.json"
MARKETPLACE_CONFIG = PLUGIN_HOME / ".agents" / "plugins" / "marketplace.json"


def load_store(temp_home):
    os.environ["CP_MEMORY_HOME"] = temp_home
    os.environ["CP_MEMORY_DB_PATH"] = str(Path(temp_home) / "memory.db")
    os.environ["CP_MEMORY_PLUGIN_HOME"] = str(PLUGIN_HOME)
    os.environ["CP_MEMORY_OLD_HOME"] = str(Path(temp_home) / "old-home")
    if "cp_memory_store" in sys.modules:
        del sys.modules["cp_memory_store"]
    sys.path.insert(0, str(SCRIPTS_DIR))
    return importlib.import_module("cp_memory_store")


class CpMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="cp-memory-test-")
        self.store = load_store(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def hook_env(self):
        env = os.environ.copy()
        env["CP_MEMORY_HOME"] = self.temp_dir
        env["CP_MEMORY_DB_PATH"] = str(Path(self.temp_dir) / "memory.db")
        env["CP_MEMORY_PLUGIN_HOME"] = str(PLUGIN_HOME)
        env["CP_MEMORY_OLD_HOME"] = str(Path(self.temp_dir) / "old-home")
        return env

    def test_plugin_manifest_declares_hook_bundle_with_legacy_contract(self):
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("hooks", manifest)

        hook_bundle = (PLUGIN_HOME / manifest["hooks"]).resolve()
        hook_config = json.loads(hook_bundle.read_text(encoding="utf-8"))
        hooks = hook_config["hooks"]

        self.assertEqual(set(hooks), {"SessionStart", "UserPromptSubmit", "PreCompact", "Stop"})

        session = hooks["SessionStart"][0]
        self.assertEqual(session["matcher"], "startup|resume")
        self.assertEqual(session["hooks"][0]["statusMessage"], "Loading memory context")
        self.assertIn("session_start.py", session["hooks"][0]["commandWindows"])
        self.assertIn("CLAUDE_PLUGIN_ROOT", session["hooks"][0]["commandWindows"])

        submit = hooks["UserPromptSubmit"][0]["hooks"][0]
        self.assertEqual(submit["statusMessage"], "Retrieving CP Memory context")
        self.assertIn("user_prompt_submit.py", submit["commandWindows"])
        self.assertNotIn(r".codex\\hooks", submit["commandWindows"])

        compact = hooks["PreCompact"][0]["hooks"][0]
        self.assertEqual(compact["statusMessage"], "Saving conversation checkpoint")
        self.assertIn("pre_compact.py", compact["commandWindows"])

        stop = hooks["Stop"][0]["hooks"][0]
        self.assertEqual(stop["statusMessage"], "Saving CP Memory turn summary")
        self.assertIn("stop.py", stop["commandWindows"])

    def test_open_source_packaging_uses_portable_mcp_and_marketplace_config(self):
        mcp = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        server = mcp["mcpServers"]["cp-memory-server"]
        self.assertEqual(server["command"], "python")
        self.assertEqual(server["args"], ["scripts/memory-mcp-server.py"])
        self.assertFalse(any("C:\\Users" in arg for arg in server["args"]))

        marketplace = json.loads(MARKETPLACE_CONFIG.read_text(encoding="utf-8"))
        plugin = marketplace["plugins"][0]
        self.assertEqual(plugin["name"], "cp-memory")
        self.assertEqual(plugin["source"]["source"], "url")
        self.assertIn("github.com", plugin["source"]["url"])
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["interface"]["websiteURL"], "https://github.com/CJhuochai/cp-memory")
        self.assertTrue(INSTALL_TEST_SCRIPT.exists())

    def test_install_keeps_global_hooks_config_untouched_and_does_not_copy_hook_scripts(self):
        temp_profile = Path(tempfile.mkdtemp(prefix="cp-memory-install-"))
        try:
            codex_home = temp_profile / ".codex"
            agents_home = temp_profile / ".agents" / "plugins"
            codex_home.mkdir(parents=True, exist_ok=True)
            agents_home.mkdir(parents=True, exist_ok=True)

            config_file = codex_home / "config.toml"
            config_file.write_text('model = "gpt-5.5"\n', encoding="utf-8")

            marketplace_file = agents_home / "marketplace.json"
            marketplace_file.write_text(
                json.dumps(
                    {
                        "name": "personal",
                        "interface": {"displayName": "Personal"},
                        "plugins": [
                            {
                                "name": "example",
                                "source": {"source": "local", "path": "./plugins/example"},
                                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                                "category": "Productivity",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            original_hooks = {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": 'python "C:\\temp\\keep.py"',
                                    "statusMessage": "keep me",
                                }
                            ],
                        }
                    ]
                }
            }
            hooks_file = codex_home / "hooks.json"
            hooks_file.write_text(json.dumps(original_hooks, ensure_ascii=False, indent=2), encoding="utf-8")

            env = os.environ.copy()
            env["USERPROFILE"] = str(temp_profile)

            subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(INSTALL_SCRIPT),
                ],
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )

            installed_manifest = json.loads(
                (temp_profile / "plugins" / "cp-memory" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertIn("hooks", installed_manifest)
            self.assertEqual(json.loads(hooks_file.read_text(encoding="utf-8")), original_hooks)
            self.assertFalse((codex_home / "hooks" / "session_start.py").exists())
            self.assertFalse((codex_home / "hooks" / "user_prompt_submit.py").exists())
        finally:
            shutil.rmtree(temp_profile, ignore_errors=True)

    def test_summary_payload_and_explain(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _ = self.store.upsert_fact(
            conn,
            "CP Memory.CurrentConversation",
            "latest-turn-summary",
            "简短摘要",
            tags="cp-memory,summary",
            category="summary",
            importance=4,
            expires_at="",
            source="test",
            summary_type="turn",
            payload={"prompt": "你好", "assistant": "我很好"},
            content_type="application/json",
        )
        conn.commit()
        explanation = self.store.explain_fact(conn, fact_id=rid)
        conn.close()

        self.assertEqual(explanation["fact"]["category"], "summary")
        self.assertEqual(explanation["payload"]["content_type"], "application/json")
        self.assertIn("Conversation", explanation["meaning"])

    def test_fts_search_and_links(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        fact_id, _ = self.store.upsert_fact(
            conn,
            "BasisProject",
            "workflow-export",
            "修复 skip 条件",
            tags="workflow,export",
            category="code_reference",
            payload={"details": "目标作用域过滤"},
            content_type="application/json",
        )
        decision_id, _ = self.store.upsert_fact(
            conn,
            "Decision",
            "workflow-scope",
            "范围条件不进入最终条件列",
            tags="decision",
            category="decision",
            importance=5,
            expires_at="",
        )
        self.store.link_records(conn, "fact", fact_id, "supported_by", "fact", decision_id)
        conn.commit()
        rows = self.store.search_records(conn, "目标作用域过滤", limit=5, mode="or")
        links = self.store.list_links(conn, source_kind="fact", source_id=fact_id)
        conn.close()

        self.assertTrue(any(row["id"] == fact_id for row in rows))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["relation"], "supported_by")

    def test_precompact_hook_writes_checkpoint_payload(self):
        env = self.hook_env()
        payload = json.dumps({"trigger": "auto", "turn_id": "turn-123", "prompt": "abc"}, ensure_ascii=False)
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "pre_compact.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        row = conn.execute(
            "SELECT id, category, value FROM facts WHERE entity='Hook' AND property='PreCompact' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        payload_row = conn.execute("SELECT content_type, content FROM memory_payloads WHERE fact_id=?", (row["id"],)).fetchone()
        conn.close()

        self.assertEqual(row["category"], "checkpoint")
        self.assertIn("turn-123", row["value"])
        self.assertEqual(payload_row["content_type"], "application/json")
        self.assertIn('"trigger": "auto"', payload_row["content"])

    def test_hook_safe_wrapper_logs_failure_and_returns_empty_json(self):
        spec = importlib.util.spec_from_file_location("cp_memory_common_test", HOOKS_DIR / "cp_memory_common.py")
        common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(common)

        def boom():
            raise RuntimeError("simulated hook failure")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            common.run_hook_safely("TestHook", boom)

        log_path = Path(self.temp_dir) / "logs" / "hooks.log"
        self.assertEqual(json.loads(stdout.getvalue()), {})
        self.assertTrue(log_path.exists())
        self.assertIn("TestHook failed: RuntimeError: simulated hook failure", log_path.read_text(encoding="utf-8"))

    def test_legacy_semantic_upgrade_reclassifies_and_backfills_payload(self):
        conn = self.store.get_db()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS facts (id TEXT PRIMARY KEY, entity TEXT, property TEXT, value TEXT, confidence TEXT, tags TEXT, category TEXT, created_at TEXT, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("legacy001", "Hook", "PreCompact", "Conversation compacted (trigger: auto) | turn: old", "high", "compaction,checkpoint", "fact", "2026-06-01 10:00:00", "2026-06-01 10:00:00"),
        )
        conn.commit()
        self.store.init_db(conn)
        row = conn.execute("SELECT category FROM facts WHERE id='legacy001'").fetchone()
        meta = conn.execute("SELECT canonical_category, quality_score, noise_score FROM memory_meta WHERE fact_id='legacy001'").fetchone()
        payload = conn.execute("SELECT content_type, content FROM memory_payloads WHERE fact_id='legacy001'").fetchone()
        conn.close()

        self.assertEqual(row["category"], "checkpoint")
        self.assertEqual(meta["canonical_category"], "checkpoint")
        self.assertIsNotNone(meta["quality_score"])
        self.assertEqual(payload["content_type"], "application/json")
        self.assertIn('"upgraded_category": "checkpoint"', payload["content"])

    def test_memory_inspect_reports_quality_and_payload(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _ = self.store.upsert_fact(
            conn,
            "CP Memory.CurrentConversation",
            "latest-turn-summary",
            "插件升级摘要",
            tags="cp-memory,summary",
            category="summary",
            importance=4,
            expires_at="",
            source="test",
            summary_type="turn",
            payload={"summary": "插件升级摘要", "detail": "完整正文"},
            content_type="application/json",
        )
        self.store.review_fact(conn, rid, category="summary", source="test")
        explanation = self.store.explain_fact(conn, fact_id=rid)
        conn.close()

        self.assertEqual(explanation["meta"]["canonical_category"], "summary")
        self.assertGreaterEqual(explanation["meta"]["quality_score"], 60)
        self.assertEqual(explanation["payload"]["content_type"], "application/json")

    def test_stop_hook_keeps_latest_and_history_summaries(self):
        env = self.hook_env()
        first = json.dumps(
            {
                "prompt": "第一轮问题：请总结插件表结构、payload 去向和治理思路",
                "assistant_message": "第一轮回答总结：facts 只放预览，payload 保存完整正文，links 保存关系链，meta 负责质量分和噪声分，这些都是后续恢复和解释的基础。",
            },
            ensure_ascii=False,
        )
        second = json.dumps(
            {
                "prompt": "第二轮问题：继续总结恢复策略和历史保留机制",
                "assistant_message": "第二轮回答总结：我们决定增加 latest 镜像和 history 双轨写入，这样既能快速取最新状态，也能在历史追问时找回多轮摘要，不再只剩一条 latest。",
            },
            ensure_ascii=False,
        )
        for payload in (first, second):
            subprocess.run(
                [sys.executable, str(HOOKS_DIR / "stop.py")],
                input=payload,
                text=True,
                env=env,
                check=True,
                capture_output=True,
            )

        conn = self.store.get_db()
        self.store.init_db(conn)
        rows = conn.execute(
            "SELECT property, value FROM facts WHERE entity='CP Memory.CurrentConversation' AND category='summary' ORDER BY updated_at DESC"
        ).fetchall()
        latest = conn.execute(
            "SELECT value FROM facts WHERE entity='CP Memory.CurrentConversation' AND property='latest-turn-summary'"
        ).fetchone()
        conn.close()

        self.assertEqual(latest["value"], rows[0]["value"])
        self.assertGreaterEqual(len(rows), 3)
        self.assertTrue(any(row["property"].startswith("turn-summary.") for row in rows))

    def test_stop_hook_auto_extracts_personal_memory_from_explicit_turn(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "记住一下，我喜欢中文、结论先行。我最近在把 CP Memory 做成通用个人助手，不做大平台。",
                "assistant_message": "用户明确说自己喜欢中文、结论先行，并且决定 CP Memory 不做大平台，而是本地优先的通用个人助手记忆系统。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        preference = conn.execute(
            "SELECT f.value, m.source FROM facts f JOIN memory_meta m ON m.fact_id = f.id WHERE f.category='preference' ORDER BY f.updated_at DESC LIMIT 1"
        ).fetchone()
        belief = conn.execute(
            "SELECT f.value, m.source FROM facts f JOIN memory_meta m ON m.fact_id = f.id WHERE f.category='belief_decision' ORDER BY f.updated_at DESC LIMIT 1"
        ).fetchone()
        episode = conn.execute(
            "SELECT id, value FROM facts WHERE category='episode' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        links = self.store.list_links(conn, target_kind="fact", target_id=episode["id"], relation="derived_from_episode")
        conn.close()

        self.assertEqual(preference["source"], "stop-hook-auto-extract")
        self.assertIn("中文", preference["value"])
        self.assertEqual(belief["source"], "stop-hook-auto-extract")
        self.assertIn("不做大平台", belief["value"])
        self.assertIn("自动提炼事件", episode["value"])
        self.assertGreaterEqual(len(links), 2)

    def test_stop_hook_does_not_extract_from_meta_implementation_examples(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "继续说明一下自动提炼是怎么实现的。",
                "assistant_message": "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口，比如“用户喜欢… / 用户决定… / 用户最近在… / 用户默认…”这类句子才会被处理。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM facts WHERE category IN ('profile','preference','relationship','ongoing','belief_decision')"
        ).fetchone()["cnt"]
        conn.close()

        self.assertEqual(count, 0)

    def test_stop_hook_extracts_rule_signals_with_explanation(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "以后不要再直接改 main，先开分支开发，测试通过后再 PR 合并。",
                "assistant_message": "收到，后续我会遵守这个发布和开发规则。这个规则会用于后续维护 CP Memory：先开分支、完成验证、再通过 PR 合并。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        row = conn.execute(
            """
            SELECT f.value, f.confidence, p.content
            FROM facts f
            JOIN memory_payloads p ON p.fact_id = f.id
            WHERE f.category='belief_decision'
            ORDER BY f.updated_at DESC
            LIMIT 1
            """
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn("不要再直接改 main", row["value"])
        self.assertEqual(row["confidence"], "high")
        payload_content = json.loads(row["content"])
        nested = payload_content["payload"]
        self.assertEqual(nested["extraction_rule"], "stable_decision")
        self.assertIn("不要再", nested["matched_signals"])
        self.assertIn("以后", nested["matched_intents"])
        self.assertFalse(nested["needs_review"])

    def test_stop_hook_skips_example_rule_text(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "下面只是一个测试用例：以后不要再直接改 main，先开分支开发。",
                "assistant_message": "这是示例文本，不应该沉淀成用户长期规则。即使文本里包含以后、分支、测试、PR 等词，也只是测试用例。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM facts WHERE category IN ('profile','preference','relationship','ongoing','belief_decision')"
        ).fetchone()["cnt"]
        conn.close()

        self.assertEqual(count, 0)

    def test_stop_hook_keeps_real_preference_about_examples(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "记住一下，我喜欢用具体示例解释复杂问题，最好先给结论再给例子。",
                "assistant_message": "收到，我会记住这个沟通偏好：解释复杂问题时优先给结论，并配合具体示例说明。后续遇到复杂设计、测试或发布流程，我会按这个方式表达。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        row = conn.execute(
            "SELECT value FROM facts WHERE category='preference' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertIn("具体示例", row["value"])

    def test_user_prompt_submit_skips_irrelevant_prompt(self):
        env = self.hook_env()
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "user_prompt_submit.py")],
            input=json.dumps({"prompt": "帮我写一个 hello world"}, ensure_ascii=False),
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )
        self.assertEqual(json.loads(result.stdout), {})

    def test_user_prompt_submit_restores_history_context(self):
        env = self.hook_env()
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_fact(
            conn,
            "CP Memory.CurrentConversation",
            "latest-turn-summary",
            "最新摘要：我们决定增加 latest 镜像和 history 双轨写入。",
            category="summary",
            tags="cp-memory,summary",
            payload={"summary": "最新摘要", "detail": "恢复逻辑应该优先带回最新结论"},
            content_type="application/json",
        )
        self.store.upsert_fact(
            conn,
            "CP Memory.CurrentConversation",
            "turn-summary.test001",
            "历史摘要：我们分析了 facts 和 payload 的分层职责。",
            category="summary",
            tags="cp-memory,summary,history",
            payload={"summary": "历史摘要", "detail": "facts 放预览，payload 放正文"},
            content_type="application/json",
        )
        conn.commit()
        conn.close()

        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "user_prompt_submit.py")],
            input=json.dumps({"prompt": "我们上次说到哪了，继续"}, ensure_ascii=False),
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )
        parsed = json.loads(result.stdout)
        context = parsed["hookSpecificOutput"]["additionalContext"]

        self.assertIn("Recent Summaries", context)
        self.assertIn("latest-turn-summary", context)
        self.assertIn("turn-summary.", context)

    def test_personal_memory_model_writes_structured_preference(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, action, category = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文、结论先行、直接给可执行建议。",
            details="这是跨话题都应该生效的沟通偏好。",
            evidence_count=3,
            scope="global",
            sensitivity="normal",
        )
        conn.commit()
        row = conn.execute("SELECT entity, property, category FROM facts WHERE id=?", (rid,)).fetchone()
        meta = conn.execute("SELECT stability_score, evidence_count, canonical_category, scope, sensitivity FROM memory_meta WHERE fact_id=?", (rid,)).fetchone()
        payload = conn.execute("SELECT content_type, content FROM memory_payloads WHERE fact_id=?", (rid,)).fetchone()
        conn.close()

        self.assertEqual(action, "created")
        self.assertEqual(category, "preference")
        self.assertEqual(row["entity"], "Personal.Preference.user")
        self.assertEqual(row["property"], "communication_style")
        self.assertEqual(row["category"], "preference")
        self.assertGreaterEqual(meta["stability_score"], 70)
        self.assertEqual(meta["evidence_count"], 3)
        self.assertEqual(meta["canonical_category"], "preference")
        self.assertEqual(meta["scope"], "global")
        self.assertEqual(meta["sensitivity"], "normal")
        self.assertEqual(payload["content_type"], "application/json")
        self.assertIn('"memory_type": "preference"', payload["content"])

    def test_restore_context_includes_personal_memory_for_identity_prompt(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "relationship",
            "user",
            "cp_memory",
            "用户把 CP Memory 当作通用个人助手记忆系统，而不只是编码助手。",
            evidence_count=2,
        )
        self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "local_first",
            "用户希望记忆系统本地优先、强解释、低运维。",
            evidence_count=2,
        )
        context = self.store.build_restore_context(conn, prompt="你记得我想把它做成什么样的个人助手吗？")
        conn.close()

        self.assertIn("### Relationships", context)
        self.assertIn("### Rules And Decisions", context)
        self.assertIn("cp_memory", context)
        self.assertIn("local_first", context)
        self.assertIn("通用个人助手", context)

    def test_memory_correction_records_status_and_new_value(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "weekly_goal",
            "用户本周优先做平台化记忆系统。",
        )
        corrected = self.store.correct_memory(
            conn,
            rid,
            "corrected",
            reason="用户明确说目标是个人助手级，不是大平台。",
            value="用户本周优先做本地优先的通用个人助手记忆系统。",
        )
        conn.commit()
        row = conn.execute("SELECT value FROM facts WHERE id=?", (rid,)).fetchone()
        meta = conn.execute("SELECT correction_status, corrected_at FROM memory_meta WHERE fact_id=?", (rid,)).fetchone()
        payload = conn.execute("SELECT content FROM memory_payloads WHERE fact_id=?", (rid,)).fetchone()
        conn.close()

        self.assertEqual(corrected, rid)
        self.assertIn("通用个人助手", row["value"])
        self.assertEqual(meta["correction_status"], "corrected")
        self.assertTrue(meta["corrected_at"])
        self.assertIn("不是大平台", payload["content"])

    def test_memory_inspect_keeps_correction_history_timeline(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "assistant_direction",
            "用户最初想做平台化记忆系统。",
        )
        self.store.correct_memory(conn, rid, "corrected", reason="用户改成个人助手路线。", value="用户想做个人助手级记忆系统。")
        self.store.correct_memory(conn, rid, "confirmed", reason="用户再次确认个人助手路线。")
        conn.commit()
        explanation = self.store.explain_fact(conn, fact_id=rid)
        conn.close()

        history = explanation["history"]
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0]["event_type"], "memory_corrected")
        self.assertTrue(any("平台化记忆系统" in item["previous_value"] for item in history))
        self.assertTrue(any("个人助手级记忆系统" in item["new_value"] for item in history))

    def test_episode_can_derive_long_term_personal_memory(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        episode_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.cp-memory-direction",
            "用户澄清 CP Memory 应该是通用个人助手记忆系统，不限定编程场景。",
            details="这是一次方向性澄清，应派生为长期产品立场。",
        )
        derived_id, action, category = self.store.derive_personal_from_episode(
            conn,
            episode_id,
            "belief_decision",
            "user",
            "personal_assistant_scope",
            "CP Memory 的目标是通用个人助手记忆系统，能记住任何重要沟通内容。",
            evidence_count=2,
        )
        conn.commit()
        links = self.store.list_links(conn, source_kind="fact", source_id=derived_id, relation="derived_from_episode")
        derived = conn.execute("SELECT category, value FROM facts WHERE id=?", (derived_id,)).fetchone()
        conn.close()

        self.assertEqual(action, "created")
        self.assertEqual(category, "belief_decision")
        self.assertEqual(derived["category"], "belief_decision")
        self.assertIn("任何重要沟通内容", derived["value"])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["target_id"], episode_id)

    def test_personal_memory_conflicts_detect_contradiction_and_expired_ongoing(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        first_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文说明。",
            evidence_count=1,
            stability_score=50,
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("manual_conflict", "Personal.BeliefDecision.user", "communication_style", "用户不喜欢中文说明。", "high", "personal-assistant,belief_decision", "belief_decision", self.store.now_local(), self.store.now_local()),
        )
        self.store.upsert_meta(conn, "manual_conflict", 5, "", source="test-conflict", summary_type="belief_decision")
        self.store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "temporary_plan",
            "用户有一个已经过期的临时计划。",
            valid_until="2026-01-01 00:00:00",
        )
        conn.commit()

        conflicts = self.store.personal_memory_conflicts(conn, limit=20)
        conn.close()

        conflict_types = {item["type"] for item in conflicts}
        self.assertIn("personal_possible_contradiction", conflict_types)
        self.assertIn("personal_expired_ongoing", conflict_types)
        self.assertTrue(any(first_id in [entry["id"] for entry in item.get("items", [])] for item in conflicts if "items" in item))

    def test_personal_conflict_resolution_marks_loser_and_keeps_audit_links(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        winner_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文说明。",
            evidence_count=2,
            stability_score=72,
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("resolve_conflict", "Personal.BeliefDecision.user", "communication_style", "用户不喜欢中文说明。", "high", "personal-assistant,belief_decision", "belief_decision", self.store.now_local(), self.store.now_local()),
        )
        self.store.upsert_meta(conn, "resolve_conflict", 5, "", source="test-resolve", summary_type="belief_decision")

        result = self.store.resolve_personal_conflict(
            conn,
            winner_id,
            loser_ids="resolve_conflict",
            merged_value="用户喜欢中文说明，并希望结论先行。",
            reason="用户明确确认了偏好。",
            loser_status="wrong",
            scope="global",
        )
        conn.commit()
        winner = conn.execute(
            "SELECT f.value, m.evidence_count, m.correction_status, m.scope FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id WHERE f.id=?",
            (winner_id,),
        ).fetchone()
        loser = conn.execute(
            "SELECT correction_status FROM memory_meta WHERE fact_id=?",
            ("resolve_conflict",),
        ).fetchone()
        links = self.store.list_links(conn, source_kind="fact", source_id=winner_id, relation="supersedes")
        conflicts = self.store.personal_memory_conflicts(conn, limit=20)
        explanation = self.store.explain_fact(conn, fact_id=winner_id)
        conn.close()

        self.assertTrue(result["ok"])
        self.assertTrue(result["merged"])
        self.assertEqual(result["loser_ids"], ["resolve_conflict"])
        self.assertIn("结论先行", winner["value"])
        self.assertEqual(winner["evidence_count"], 3)
        self.assertEqual(winner["correction_status"], "confirmed")
        self.assertEqual(winner["scope"], "global")
        self.assertEqual(loser["correction_status"], "wrong")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["target_id"], "resolve_conflict")
        self.assertNotIn("personal_possible_contradiction", {item["type"] for item in conflicts})
        self.assertTrue(any(item["event_type"] == "personal_conflict_resolved" for item in explanation["history"]))

    def test_episode_consolidation_preview_and_apply_are_auditable(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        episode_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.preference",
            "用户喜欢中文结论先行，并决定 CP Memory 不做大平台。",
        )
        preview = self.store.consolidate_episode(conn, episode_id, subject="user", dry_run=True)
        rows_before = conn.execute("SELECT COUNT(*) AS cnt FROM facts WHERE category != 'episode'").fetchone()["cnt"]
        applied = self.store.consolidate_episode(conn, episode_id, subject="user", dry_run=False)
        conn.commit()
        rows_after = conn.execute("SELECT COUNT(*) AS cnt FROM facts WHERE category != 'episode'").fetchone()["cnt"]
        derived_links = conn.execute(
            "SELECT COUNT(*) AS cnt FROM memory_links WHERE relation='derived_from_episode' AND target_id=?",
            (episode_id,),
        ).fetchone()["cnt"]
        conn.close()

        self.assertTrue(preview["dry_run"])
        self.assertGreaterEqual(len(preview["candidates"]), 1)
        self.assertEqual(rows_before, 0)
        self.assertFalse(applied["dry_run"])
        self.assertGreaterEqual(len(applied["created"]), 1)
        self.assertGreater(rows_after, rows_before)
        self.assertGreaterEqual(derived_links, 1)

    def test_personal_memory_review_shows_counts_conflicts_and_suggestions(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "style",
            "用户喜欢简洁说明。",
            evidence_count=1,
            stability_score=50,
        )
        self.store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.direction",
            "用户决定 CP Memory 不做大平台，并希望它保持本地优先。",
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("review_conflict", "Personal.BeliefDecision.user", "style", "用户不喜欢简洁说明。", "high", "personal-assistant,belief_decision", "belief_decision", self.store.now_local(), self.store.now_local()),
        )
        self.store.upsert_meta(conn, "review_conflict", 5, "", source="test-review", summary_type="belief_decision")
        conn.commit()

        review = self.store.personal_memory_review(conn, subject="user", limit=10)
        conn.close()

        self.assertGreaterEqual(review["counts"].get("preference", 0), 1)
        self.assertTrue(review["recent"])
        self.assertTrue(review["conflicts"])
        self.assertTrue(review["resolution_candidates"])
        self.assertEqual(review["resolution_candidates"][0]["winner_suggestion"]["property"], "style")
        self.assertIn("review_candidates", review)
        self.assertTrue(review["consolidation_suggestions"])

    def test_review_digest_outputs_markdown_with_actionable_sections(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文结论先行。",
            source="stop-hook-auto-extract",
            evidence_count=1,
            stability_score=50,
            scope="global",
        )
        self.store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "readme_work",
            "用户当前在做 README 优化。",
            valid_until="2000-01-01 00:00:00",
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("digest_conflict", "Personal.BeliefDecision.user", "communication_style", "用户不喜欢中文说明。", "high", "personal-assistant,belief_decision", "belief_decision", self.store.now_local(), self.store.now_local()),
        )
        self.store.upsert_meta(conn, "digest_conflict", 5, "", source="test-digest", summary_type="belief_decision")
        conn.commit()

        digest = self.store.build_review_digest(conn, subject="user", limit=10)
        conn.close()

        self.assertIn("# CP Memory Review Digest", digest)
        self.assertIn("## 最近新增 / Recent Memories", digest)
        self.assertIn("## 待确认 / Needs Review", digest)
        self.assertIn("## 冲突和过期 / Conflicts And Stale Candidates", digest)
        self.assertIn("用户喜欢中文结论先行", digest)
        self.assertIn("scope=`global`", digest)
        self.assertIn("review_or_confirm", digest)
        self.assertIn("personal_possible_contradiction", digest)
        self.assertIn("personal_expired_ongoing", digest)

    def test_review_reminder_only_appears_when_action_is_needed(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.assertEqual(self.store.build_review_reminder(conn, subject="user"), "")

        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文结论先行。",
            source="stop-hook-auto-extract",
            evidence_count=1,
            stability_score=50,
        )
        reminder = self.store.build_review_reminder(conn, subject="user")
        conn.close()

        self.assertIn("CP Memory 提醒 / Reminder", reminder)
        self.assertIn("待确认 1", reminder)
        self.assertIn("不会自动删除记忆", reminder)

    def test_maintenance_expire_does_not_delete_protected_personal_memory(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        old_date = "2000-01-01 00:00:00"
        normal_id, _ = self.store.upsert_fact(conn, "Scratch", "old_note", "临时低价值记录", category="fact")
        protected_id, _, _ = self.store.upsert_personal_memory(conn, "preference", "user", "style", "用户喜欢中文说明。")
        self.store.upsert_meta(conn, normal_id, 1, old_date, source="test")
        self.store.upsert_meta(conn, protected_id, 1, old_date, source="test")
        conn.commit()
        conn.close()

        spec = importlib.util.spec_from_file_location("memory_mcp_server_test", MCP_CONFIG.parent / "scripts" / "memory-mcp-server.py")
        mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_server)
        result = json.loads(mcp_server.memory_maintenance(dry_run=False, expire=True, limit=20))

        conn = self.store.get_db()
        normal = conn.execute("SELECT id FROM facts WHERE id=?", (normal_id,)).fetchone()
        protected = conn.execute("SELECT id FROM facts WHERE id=?", (protected_id,)).fetchone()
        conn.close()

        self.assertEqual(result["deleted"], 1)
        self.assertEqual(result["protected_expired_skipped"], 1)
        self.assertIsNone(normal)
        self.assertIsNotNone(protected)

    def test_review_recomputes_after_resolution_and_leaves_audit_links(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        winner_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文说明。",
            evidence_count=2,
            stability_score=75,
        )
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            ("review_after_resolve", "Personal.BeliefDecision.user", "communication_style", "用户不喜欢中文说明。", "high", "personal-assistant,belief_decision", "belief_decision", self.store.now_local(), self.store.now_local()),
        )
        self.store.upsert_meta(conn, "review_after_resolve", 5, "", source="test-review-after-resolve", summary_type="belief_decision")
        before = self.store.personal_memory_review(conn, subject="user", limit=10)
        self.store.resolve_personal_conflict(
            conn,
            winner_id,
            loser_ids="review_after_resolve",
            reason="用户确认最终偏好。",
            loser_status="wrong",
        )
        conn.commit()
        after = self.store.personal_memory_review(conn, subject="user", limit=10)
        links = self.store.list_links(conn, source_kind="fact", source_id=winner_id, relation="supersedes")
        explanation = self.store.explain_fact(conn, fact_id=winner_id)
        conn.close()

        self.assertTrue(before["resolution_candidates"])
        self.assertFalse(after["resolution_candidates"])
        self.assertNotIn("personal_possible_contradiction", {item["type"] for item in after["conflicts"]})
        self.assertEqual(len(links), 1)
        self.assertTrue(any(item["relation"] == "supersedes" for item in explanation["relations"]))

    def test_restore_context_surfaces_relevant_episode_for_history_prompt(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "episode",
            "user",
            "conversation.scope-clarification",
            "那次澄清里，用户明确说 CP Memory 不限定编程场景，而是通用个人助手记忆系统。",
        )
        context = self.store.build_restore_context(conn, prompt="你还记得我那次澄清它不能只服务编程吗？", max_chars=2200)
        conn.close()

        self.assertIn("Relevant Episodes", context)
        self.assertIn("不限定编程场景", context)

    def test_restore_context_prefers_prompt_matched_personal_memory(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language",
            "用户喜欢中文说明。",
        )
        self.store.upsert_personal_memory(
            conn,
            "relationship",
            "user",
            "memory_system",
            "用户把 CP Memory 当作通用个人助手。",
        )
        context = self.store.build_restore_context(conn, prompt="你记得我喜欢中文说明吗？", max_chars=2200)
        conn.close()

        self.assertIn("### Preferences", context)
        self.assertIn("### Relationships", context)
        self.assertIn("中文说明", context)

    def test_restore_context_filters_wrong_and_stale_personal_memory(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        confirmed_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language",
            "用户喜欢中文说明。",
            evidence_count=3,
            stability_score=85,
        )
        stale_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language_old",
            "用户以前偏向英文说明。",
            evidence_count=1,
            stability_score=40,
        )
        wrong_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "language_wrong",
            "用户不喜欢中文说明。",
            evidence_count=1,
            stability_score=30,
        )
        self.store.correct_memory(conn, confirmed_id, "confirmed", reason="用户再次确认当前偏好。")
        self.store.correct_memory(conn, stale_id, "stale", reason="这是旧偏好。")
        self.store.correct_memory(conn, wrong_id, "wrong", reason="这条记录不正确。")
        conn.commit()
        context = self.store.build_restore_context(conn, prompt="你记得我喜欢中文说明吗？", max_chars=2200)
        conn.close()

        self.assertIn("用户喜欢中文说明。", context)
        self.assertNotIn("英文说明", context)
        self.assertNotIn("不喜欢中文说明", context)

    def test_personal_memory_scope_is_preserved_on_update(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "release_rule",
            "CP Memory 发版先开分支。",
            scope="project:cp-memory",
        )
        self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "release_rule",
            "CP Memory 发版先开分支并通过 PR 合并。",
        )
        scope = conn.execute("SELECT scope FROM memory_meta WHERE fact_id=?", (rid,)).fetchone()["scope"]
        conn.close()

        self.assertEqual(scope, "project:cp-memory")

    def test_restore_context_prioritizes_matching_scope_without_filtering_global(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "basis_release",
            "BasisProject 发布规则使用内部环境流程。",
            scope="workspace:E:\\BasisProject",
        )
        self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "cp_release",
            "CP Memory 发布规则是先开分支、测试、PR 合并。",
            scope="project:cp-memory",
        )
        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "communication_style",
            "用户喜欢中文结论先行。",
            scope="global",
        )
        context = self.store.build_restore_context(conn, prompt="CP Memory 的发布规则是什么？", max_chars=2200)
        conn.close()

        self.assertIn("CP Memory 发布规则", context)
        self.assertIn("用户喜欢中文结论先行", context)
        self.assertLess(context.index("CP Memory 发布规则"), context.index("BasisProject 发布规则"))

    def test_stop_hook_auto_extract_writes_project_scope(self):
        env = self.hook_env()
        payload = json.dumps(
            {
                "prompt": "记住一下，CP Memory 发版以后要先开分支、测试、PR 合并。",
                "assistant_message": "收到，这是 CP Memory 项目的发布规则，我会在后续维护这个插件时优先遵守。后续涉及版本发布、Release、tag 和 PR 合并时，都会按这个项目规则处理。",
            },
            ensure_ascii=False,
        )
        subprocess.run(
            [sys.executable, str(HOOKS_DIR / "stop.py")],
            input=payload,
            text=True,
            env=env,
            check=True,
            capture_output=True,
        )

        conn = self.store.get_db()
        self.store.init_db(conn)
        scope = conn.execute(
            "SELECT m.scope FROM facts f JOIN memory_meta m ON m.fact_id=f.id WHERE f.category='belief_decision' ORDER BY f.updated_at DESC LIMIT 1"
        ).fetchone()["scope"]
        conn.close()

        self.assertEqual(scope, "project:cp-memory")

    def test_auto_extract_review_candidates_and_confirmed_priority(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        auto_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "product_direction_auto",
            "用户决定 CP Memory 不做大平台，而是通用个人助手。",
            evidence_count=1,
            stability_score=86,
            source="stop-hook-auto-extract",
        )
        manual_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "product_direction_manual",
            "用户希望记忆系统本地优先、强解释、低运维。",
            evidence_count=2,
            stability_score=82,
            source="memory_personal_add",
        )
        review_before = self.store.personal_memory_review(conn, subject="user", limit=10)
        context_before = self.store.build_restore_context(conn, prompt="你记得这个记忆系统的长期方向吗？", max_chars=2200)
        self.store.correct_memory(conn, auto_id, "confirmed", reason="用户确认自动提炼结果。")
        conn.commit()
        review_after = self.store.personal_memory_review(conn, subject="user", limit=10)
        context_after = self.store.build_restore_context(conn, prompt="你记得这个记忆系统的长期方向吗？", max_chars=2200)
        conn.close()

        self.assertTrue(any(item["id"] == auto_id for item in review_before["review_candidates"]))
        self.assertFalse(any(item["id"] == auto_id for item in review_after["review_candidates"]))
        self.assertIn("本地优先", context_before)
        self.assertIn("不做大平台", context_after)

    def test_auto_extract_governance_stats_track_pending_and_confirmed(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        pending_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "auto_pending",
            "用户喜欢中文说明。",
            evidence_count=1,
            stability_score=78,
            source="stop-hook-auto-extract",
        )
        confirmed_id, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "auto_confirmed",
            "用户决定 CP Memory 不做大平台。",
            evidence_count=1,
            stability_score=86,
            source="stop-hook-auto-extract",
        )
        self.store.correct_memory(conn, confirmed_id, "confirmed", reason="用户确认自动提炼结果。")
        conn.commit()
        stats = self.store.auto_extract_governance_stats(conn, limit=5)
        conn.close()

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["confirmed"], 1)
        self.assertEqual(stats["pending_review"], 1)
        self.assertEqual(stats["pending_samples"][0]["id"], pending_id)

    def test_marked_wrong_auto_extract_leaves_review_and_cleanup_queues(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "auto_noise",
            "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口。",
            evidence_count=1,
            stability_score=78,
            source="stop-hook-auto-extract",
        )
        self.store.correct_memory(conn, rid, "wrong", reason="实现说明噪声。")
        conn.commit()
        stats = self.store.auto_extract_governance_stats(conn, limit=5)
        cleanup = self.store.auto_extract_cleanup_candidates(conn, limit=5)
        review = self.store.personal_memory_review(conn, subject="user", limit=10)
        conn.close()

        self.assertEqual(stats["pending_review"], 0)
        self.assertFalse(cleanup)
        self.assertFalse(any(item["id"] == rid for item in review["review_candidates"]))

    def test_governance_acceptance_report_contains_gates_samples_and_probes(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        self.store.upsert_personal_memory(
            conn,
            "preference",
            "user",
            "language",
            "用户喜欢中文说明。",
            evidence_count=2,
            stability_score=80,
            source="stop-hook-auto-extract",
        )
        self.store.upsert_personal_memory(
            conn,
            "ongoing",
            "user",
            "current_goal",
            "用户最近在把 CP Memory 做成通用个人助手。",
            evidence_count=2,
            stability_score=70,
            source="memory_personal_add",
        )
        conn.commit()
        report = self.store.governance_acceptance_report(conn, limit=5)
        conn.close()

        self.assertIn("summary", report)
        self.assertIn("gates", report)
        self.assertTrue(report["gates"]["has_personal_memory"])
        self.assertIn("auto_extract_governance", report)
        self.assertIn("cleanup_candidates", report)
        self.assertIn("samples", report)
        self.assertTrue(report["restore_probes"])

    def test_restore_identity_rules_filters_wrong_profile_memory(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "profile",
            "user",
            "current_goal",
            "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口。",
            evidence_count=1,
            stability_score=88,
            source="stop-hook-auto-extract",
        )
        self.store.correct_memory(conn, rid, "wrong", reason="实现说明噪声。")
        context = self.store.build_restore_context(conn, prompt="你记得这个事情的长期方向吗？", max_chars=2200)
        conn.close()

        self.assertNotIn("自动提炼入口", context)

    def test_auto_extract_cleanup_candidates_preview_and_apply(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "current_goal",
            "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口。",
            evidence_count=1,
            stability_score=86,
            source="stop-hook-auto-extract",
        )
        conn.commit()
        preview = self.store.cleanup_auto_extract_noise(conn, dry_run=True, limit=10, action="mark_wrong")
        self.assertEqual(preview["candidate_count"], 1)
        self.assertEqual(preview["candidates"][0]["id"], rid)
        applied = self.store.cleanup_auto_extract_noise(conn, dry_run=False, limit=10, action="mark_wrong")
        conn.commit()
        exists = conn.execute("SELECT 1 FROM facts WHERE id=?", (rid,)).fetchone()
        status = conn.execute("SELECT correction_status FROM memory_meta WHERE fact_id=?", (rid,)).fetchone()
        conn.close()

        self.assertEqual(applied["cleaned_ids"], [rid])
        self.assertIsNotNone(exists)
        self.assertEqual(status["correction_status"], "wrong")

    def test_auto_extract_cleanup_delete_strategy_removes_row(self):
        conn = self.store.get_db()
        self.store.init_db(conn)
        rid, _, _ = self.store.upsert_personal_memory(
            conn,
            "belief_decision",
            "user",
            "current_goal_delete",
            "现在在 [cp_memory_common.py](C:/Users/24520/plugins/cp-memory/hooks/cp_memory_common.py) 里加了一个很保守的自动提炼入口。",
            evidence_count=1,
            stability_score=86,
            source="stop-hook-auto-extract",
        )
        conn.commit()
        applied = self.store.cleanup_auto_extract_noise(conn, dry_run=False, limit=10, action="delete")
        conn.commit()
        exists = conn.execute("SELECT 1 FROM facts WHERE id=?", (rid,)).fetchone()
        conn.close()

        self.assertEqual(applied["action"], "delete")
        self.assertEqual(applied["cleaned_ids"], [rid])
        self.assertIsNone(exists)
