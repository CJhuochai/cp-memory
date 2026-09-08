"""Sanitized recall regression scenarios / 脱敏召回回归场景.

Hand-authored examples, not copied private data or a population accuracy study.
人工重构问题模式，不复制真实记忆，不代表总体准确率。
"""
import argparse
import hashlib
import importlib
import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import personal_memory_benchmark as benchmark


def record(key, value, category="belief_decision", **meta):
    return {"key": key, "value": value, "category": category, **meta}


def scenarios():
    release = record("atlas_release", "Atlas 发布必须先测试再合并。", scope="project:atlas")
    other = record("boreal_release", "Boreal 发布由专人执行。", scope="project:boreal", status="confirmed")
    language = record("language", "用户喜欢中文说明。", "preference")
    # These pairs cover the follow-up precision boundaries without using live memory data.
    # 这些成对数据覆盖后续精度边界，不使用真实记忆库内容。
    # Each pair varies phrasing or scope syntax; failures remain individually visible.
    # 每组两个问法独立计分，避免用单一固定问法掩盖边界。
    groups = [
        ("scope", [release, other], ["Atlas 的发布规则是什么？", "project:atlas 发布流程"], ["atlas_release"], []),
        ("compound_scope", [release, {**other, "scope": "project:boreal;demo-only"}], ["Atlas 发布约定", "project:atlas 发布要求"], ["atlas_release"], []),
        ("repo_scope", [record("repo_release", "发布前必须测试。", scope="repo:acme/atlas"), other], ["acme/atlas 发布规则", "repo:acme/atlas 发布约定"], ["repo_release"], []),
        ("global", [release, other, record("global_style", "回答使用中文。", "preference", scope="global")], ["Atlas 发布规则", "project:atlas 发布流程"], ["atlas_release", "global_style"], []),
        ("unknown_scope", [other], ["我的默认时区是什么？", "你记得我的沟通偏好吗？"], [], []),
        ("wrong", [language, record("wrong_language", "用户不喜欢中文说明。", "preference", status="wrong")], ["我喜欢中文说明吗？", "中文说明的偏好是什么？"], ["language"], []),
        ("stale", [language, record("stale_language", "用户以前用英文说明。", "preference", status="stale")], ["中文说明偏好", "我喜欢中文吗？"], ["language"], []),
        ("expired", [record("current_task", "用户正在研究园艺。", "ongoing"), record("expired_task", "用户正在研究旧园艺方案。", "ongoing", valid_until="2000-01-01 00:00:00")], ["园艺目标现在是什么？", "园艺最近的进展"], ["current_task"], []),
        ("pending", [record("pending_style", "用户喜欢简洁说明。", "preference", source="stop-hook-auto-extract")], ["简洁说明的偏好", "我喜欢简洁说明吗？"], ["pending_style"], []),
        ("confirmed", [record("confirmed_style", "用户喜欢简洁说明。", "preference", source="stop-hook-auto-extract", status="confirmed")], ["简洁说明的偏好", "我喜欢简洁说明吗？"], ["confirmed_style"], []),
        ("weak", [record("unrelated", "用户喜欢慢跑。", "preference", status="confirmed")], ["我的咖啡口味是什么？", "你记得海洋研究计划吗？"], [], []),
        ("history", [record("garden_episode", "那次园艺讨论决定使用陶盆。", "episode"), record("music_episode", "那次音乐讨论选择钢琴。", "episode")], ["上次园艺讨论说了什么？", "之前园艺的决定是什么？"], ["garden_episode"], []),
        ("summary", [record("garden_summary", "上次园艺讨论选择陶盆。", "summary"), record("music_summary", "上次音乐讨论选择钢琴。", "summary")], ["上次园艺讨论", "之前园艺说了什么？"], ["garden_summary"], []),
        ("legacy", [record("wrong_pattern", "园艺规则用塑料盆。", "fact", entity="Pattern.Garden", status="wrong")], ["园艺项目的规则", "园艺代码实现约定"], [], []),
        ("identity", [record("timezone", "用户默认东八区 Asia/Shanghai。", "profile"), record("music", "用户喜欢钢琴。", "preference")], ["我的时区是什么？", "你记得东八区吗？"], ["timezone"], []),
        ("relationship", [record("garden_relation", "用户和园艺协会有合作关系。", "relationship"), record("music_relation", "用户和音乐协会有合作关系。", "relationship")], ["我和园艺协会的关系", "园艺协会的合作情况"], ["garden_relation"], []),
        ("startup", [language, other], ["", "你记得我的偏好吗？"], ["language"], []),
        ("explicit_other", [release, other], ["Boreal 发布规则", "project:boreal 发布要求"], ["boreal_release"], []),
        ("old_relevant", [language] + [record(f"noise_{i}", f"用户正在研究第{i}种乐器。", "ongoing", status="confirmed") for i in range(35)], ["我喜欢中文说明吗？", "中文说明偏好"], ["language"], []),
        ("case_scope", [{**release, "scope": "project:Atlas"}, other], ["project:ATLAS 发布规则", "atlas 发布流程"], ["atlas_release"], []),
        ("inactive_summary", [record("dead_summary", "园艺历史记录内容。", "summary", status="wrong")], ["上次园艺说了什么？", "之前园艺讨论"], [], []),
        ("inactive_decision", [record("dead_decision", "园艺使用塑料盆。", "decision", status="stale")], ["园艺规则是什么？", "你记得园艺的决定吗？"], [], []),
        ("english", [record("coffee", "User prefers coffee without sugar.", "preference"), record("piano", "User prefers piano music.", "preference", status="confirmed")], ["What is my coffee preference?", "Remember coffee without sugar?"], ["coffee"], []),
        ("numeric_collision", [record("cp_recall", "CP Memory 召回质量基线编号 144。"), record("other_build", "BasisProject 编译问题编号 111。", "summary")], ["召回质量 144 111", "CP Memory 召回质量基线"], ["cp_recall"], []),
        ("generic_collision", [record("cp_quality", "CP Memory 召回质量改进。", scope="project:cp-memory"), record("other_quality", "BasisProject 质量问题记录。", "summary")], ["CP Memory 质量问题", "CP Memory 召回质量"], ["cp_quality"], []),
        ("explicit_identifier", [record("release_190", "版本 v1.9.0 已完成召回修复。", "summary"), record("release_191", "版本 v1.9.1 仍在计划中。", "summary")], ["版本 v1.9.0", "v1.9.0"], ["release_190"], []),
        ("unscoped_history", [record("garden_decision", "园艺讨论决定使用陶盆。", "episode"), record("music_decision", "音乐讨论决定选择钢琴。", "episode")], ["园艺讨论决定", "园艺之前的讨论"], ["garden_decision"], []),
        ("no_result_topic", [record("known_topic", "已知主题的历史记录。", "summary")], ["完全不存在的主题", "另一个不存在的主题"], [], []),
        ("empty", [], ["你记得我的昵称吗？", "上次园艺说了什么？"], [], []),
    ]
    for name, records, prompts, required, allowed in groups:
        for index, prompt in enumerate(prompts):
            yield {"name": f"{name}_{index + 1}", "records": records, "prompt": prompt,
                   "required": required, "allowed": allowed,
                   "forbidden": [r["key"] for r in records if r["key"] not in required + allowed]}


def evaluate():
    results = []
    for case in scenarios():
        with tempfile.TemporaryDirectory(prefix="cp-recall-quality-") as home:
            with patch.dict(os.environ):
                store = benchmark.load_store(home)
                store.codex_memory_base = lambda: Path(home) / "empty-codex"
                conn = store.get_db()
                store.init_db(conn)
                for item in case["records"]:
                    entity = item.get("entity", "CP Memory.CurrentConversation" if item["category"] == "summary" else "Evaluation")
                    rid, _ = store.upsert_fact(conn, entity, item["key"], item["value"],
                                               category=item["category"], source=item.get("source", "memory_personal_add"))
                    conn.execute("UPDATE memory_meta SET scope=?, correction_status=?, valid_until=? WHERE fact_id=?",
                                 (item.get("scope", ""), item.get("status", ""), item.get("valid_until", ""), rid))
                conn.commit()
                context = store.build_restore_context(conn, prompt=case["prompt"], max_chars=2200)
                conn.close()
                sys.modules.pop("memory_mcp_server", None)
                server = importlib.import_module("memory_mcp_server")
                recalled = json.loads(server.memory_recall(case["prompt"], limit=8, allow_auxiliary=False))
                texts = {"restore": context, "mcp_context": recalled["cp_memory"]["context"],
                         "mcp_records": "\n".join(f"{r['property']}: {r['value']}" for r in recalled["cp_memory"]["records"])}
                for surface, text in texts.items():
                    emitted = {r["key"] for r in case["records"] if f"{r['key']}:" in text}
                    missing = sorted(set(case["required"]) - emitted)
                    forbidden = sorted(set(case["forbidden"]) & emitted)
                    pending = [r for r in recalled["cp_memory"]["records"] if r.get("review_state") == "pending_review"]
                    label_ok = not case["name"].startswith("pending_") or (bool(pending) if surface == "mcp_records" else "pending_review" in text)
                    results.append({"case": case["name"], "surface": surface, "passed": not missing and not forbidden and label_ok,
                                    "required_count": len(case["required"]), "required_found": len(case["required"]) - len(missing),
                                    "emitted_count": len(emitted), "missing": missing, "forbidden": forbidden,
                                    "pending_label_ok": label_ok, "context_chars": len(text)})
    required = sum(r["required_count"] for r in results)
    emitted = sum(r["emitted_count"] for r in results)
    leaks = sum(len(r["forbidden"]) for r in results)
    return {"scenario_count": len(results) // 3, "checks": len(results), "passed": sum(r["passed"] for r in results),
            "required_recall": sum(r["required_found"] for r in results) / required if required else 1,
            "unrelated_injection_rate": leaks / emitted if emitted else 0, "forbidden_leaks": leaks,
            "mean_restore_chars": sum(r["context_chars"] for r in results if r["surface"] == "restore") / (len(results) // 3),
            "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-ref", help="Evaluate committed store/server without changing the checkout / 用指定提交作对比")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="cp-recall-source-") as source:
        source_dir = benchmark.SCRIPTS_DIR
        if args.source_ref:
            revision = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", args.source_ref + "^{commit}"], cwd=benchmark.PLUGIN_HOME, text=True).strip()
            source_dir = Path(source)
            for name in ("cp_memory_store.py", "memory_mcp_server.py"):
                code = subprocess.check_output(["git", "show", f"{revision}:scripts/{name}"], cwd=benchmark.PLUGIN_HOME)
                (source_dir / name).write_bytes(code)
        with patch.object(benchmark, "SCRIPTS_DIR", source_dir):
            report = evaluate()
        report["source"] = revision if args.source_ref else "working-tree"
        report["suite_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report["source_sha256"] = {name: hashlib.sha256((source_dir / name).read_bytes()).hexdigest() for name in ("cp_memory_store.py", "memory_mcp_server.py")}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    return 0 if report["checks"] == report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
