import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLUGIN_HOME = Path(os.environ.get("CP_MEMORY_PLUGIN_HOME", str(Path(os.path.expanduser("~")) / "plugins" / "cp-memory")))
SCRIPTS_DIR = PLUGIN_HOME / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cp_memory_store import (  # noqa: E402
    CATEGORY_DECISION,
    CATEGORY_BELIEF_DECISION,
    CATEGORY_CHECKPOINT,
    CATEGORY_ONGOING,
    CATEGORY_PREFERENCE,
    CATEGORY_PROFILE,
    CATEGORY_RELATIONSHIP,
    CATEGORY_SUMMARY,
    CHECKPOINT_HISTORY_PREFIX,
    LATEST_CHECKPOINT_PROPERTY,
    LATEST_TURN_SUMMARY_PROPERTY,
    SUMMARY_HISTORY_PREFIX,
    active_task,
    build_restore_context,
    classify_importance,
    detect_restore_intent,
    expiry_for_importance,
    get_db,
    init_db,
    link_records,
    now_local,
    recent_conversation_summaries,
    search_records,
    slugify_key,
    should_inject_restore_context,
    touch_fact_ids,
    unique_property,
    upsert_fact,
    upsert_decision_record,
    upsert_personal_memory,
)


def connect():
    conn = get_db()
    init_db(conn)
    return conn


def read_stdin_json():
    try:
        raw_bytes = sys.stdin.buffer.read()
        if not raw_bytes.strip():
            return {}
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                raw = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                raw = ""
        if raw.strip():
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def repair_mojibake(text):
    if not isinstance(text, str) or not text:
        return ""
    suspicious = ("鎴", "浣", "锛", "銆", "闂", "璇", "鐨", "缁", "杩", "鍒")
    if not any(token in text for token in suspicious):
        return text
    for source_encoding in ("gbk", "gb18030"):
        try:
            repaired = text.encode(source_encoding).decode("utf-8")
        except Exception:
            continue
        if repaired and repaired != text:
            return repaired
    return text


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("\ufeff", "").strip()
    text = repair_mojibake(text)
    return text.encode("utf-8", "ignore").decode("utf-8", "ignore").strip()


def emit_json(payload):
    print(json.dumps(payload, ensure_ascii=True))


def emit_hook_context(event_name, additional_context):
    emit_json({"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": additional_context}})


def extract_prompt(data):
    for key in ("prompt", "user_prompt", "message", "input"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    return ""


def extract_assistant_message(data):
    for key in ("last_assistant_message", "assistant_message", "message", "response"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    return ""


def meaningful_text(text, max_len=360):
    text = re.sub(r"\s+", " ", clean_text(text))
    return text[:max_len]


def has_any(text, terms):
    return any(term.lower() in text.lower() for term in terms)


def keyword_terms(text):
    terms = []
    for token in re.findall(r"[A-Za-z0-9_.:/\\-]{3,}", text or ""):
        if token.lower() not in {"the", "and", "for", "with", "this", "that"}:
            terms.append(token[:48])
    chinese_terms = [
        "刚刚",
        "上次",
        "之前",
        "昨天",
        "今天",
        "聊了",
        "记忆",
        "进度",
        "继续",
        "未完成",
        "偏好",
        "规则",
        "决策",
        "项目",
        "接口",
        "导出",
        "流程",
        "审批",
        "合同",
        "资产",
        "学生",
        "检查",
        "bug",
        "CP Memory",
        "Hermes",
    ]
    for term in chinese_terms:
        if term in text:
            terms.append(term)
    deduped = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped[:8]


def split_sentences(text):
    cleaned = clean_text(text)
    if not cleaned:
        return []
    parts = re.split(r"[。！？!\?\n\r;；]+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def normalize_user_statement(sentence):
    text = clean_text(sentence)
    replacements = [
        ("我不喜欢", "用户不喜欢"),
        ("我喜欢", "用户喜欢"),
        ("我希望", "用户希望"),
        ("我想", "用户想"),
        ("我要", "用户要"),
        ("我最近在", "用户最近在"),
        ("我正在", "用户正在"),
        ("我还在", "用户还在"),
        ("我先做", "用户先做"),
        ("我先", "用户先"),
        ("我后面", "用户后面"),
        ("我准备", "用户准备"),
        ("我打算", "用户打算"),
        ("我是", "用户是"),
        ("我叫", "用户叫"),
        ("我的昵称是", "用户昵称是"),
        ("我的默认时区是", "用户默认时区是"),
        ("我的时区是", "用户时区是"),
    ]
    for source, target in replacements:
        if text.startswith(source):
            return text.replace(source, target, 1)
    return text


def is_explicit_memory_sentence(sentence):
    text = clean_text(sentence)
    if not text or "?" in text or "？" in text:
        return False
    trigger_terms = (
        "用户喜欢",
        "用户不喜欢",
        "用户希望",
        "用户想",
        "用户要",
        "用户正在",
        "用户最近在",
        "用户还在",
        "用户先做",
        "用户先",
        "用户后面",
        "用户准备",
        "用户打算",
        "用户决定",
        "用户明确",
        "用户默认",
        "用户时区",
        "用户昵称",
        "用户是",
        "用户把",
        "用户将",
    )
    if any(term in text for term in trigger_terms):
        return True
    if explicit_memory_intents(text):
        return True
    first_person_terms = ("我喜欢", "我不喜欢", "我想", "我要", "我希望", "我正在", "我最近在", "我还在", "我先做", "我先", "我后面", "我准备", "我打算", "我是", "我叫")
    return text.startswith(first_person_terms)


def looks_like_meta_explanation(sentence):
    text = clean_text(sentence)
    noisy_markers = (
        "[",
        "](",
        ".py",
        ".md",
        "`",
        "hook",
        "stop hook",
        "cp_memory_common",
        "memory_personal_add",
        "memory_episode_consolidate",
        "自动提炼入口",
        "实现",
        "代码",
        "插件",
    )
    return len(text) > 120 or any(marker.lower() in text.lower() for marker in noisy_markers)


@dataclass(frozen=True)
class ExtractionRule:
    name: str
    category: str
    signals: tuple
    stability_score: int
    required_intents: tuple = ()
    negative_signals: tuple = ()


EXPLICIT_MEMORY_INTENTS = (
    "记住",
    "以后",
    "后续",
    "下次",
    "默认",
    "规则",
    "原则",
    "必须",
    "一定要",
    "不要再",
    "别再",
    "不能",
    "统一",
    "一律",
    "优先",
    "作为",
    "定下来",
    "先做",
    "待处理",
    "先放一放",
)

GLOBAL_NEGATIVE_SIGNALS = (
    "比如",
    "例如",
    "假设",
    "如果用户",
    "测试用例",
    "代码示例",
    "只是示例",
    "示例文本",
    "输出如下",
    "报错",
    "Traceback",
)

EXTRACTION_RULES = (
    ExtractionRule("profile_identity", CATEGORY_PROFILE, ("时区", "东八区", "Asia/Shanghai", "昵称", "我是", "我叫", "用户默认", "用户时区"), 88),
    ExtractionRule("communication_preference", CATEGORY_PREFERENCE, ("喜欢", "不喜欢", "偏好", "习惯", "结论先行", "中文说明", "用户希望", "我希望"), 78),
    ExtractionRule("relationship", CATEGORY_RELATIONSHIP, ("当作", "关系", "和 CP Memory", "把 CP Memory"), 72),
    ExtractionRule("ongoing_work", CATEGORY_ONGOING, ("正在", "最近在", "目标", "计划", "推进", "本周优先", "继续", "先做", "后面再说", "先放一放", "这轮先", "当前在做", "还没做完", "待处理"), 62),
    ExtractionRule("stable_decision", CATEGORY_BELIEF_DECISION, ("决定", "不做", "不是", "而是", "原则", "长期方向", "通用个人助手", "不限定编程", "必须", "不要再", "不能", "默认", "一律", "统一", "先开分支", "PR"), 86),
)


def matched_terms(text, terms):
    return [term for term in terms if term and term in text]


def extraction_noise_reasons(text):
    reasons = []
    if looks_like_meta_explanation(text):
        reasons.append("meta_explanation")
    reasons.extend(f"negative:{term}" for term in matched_terms(text, GLOBAL_NEGATIVE_SIGNALS))
    return reasons


def explicit_memory_intents(text):
    return matched_terms(text, EXPLICIT_MEMORY_INTENTS)


def evaluate_extraction_rule(rule, text):
    signals = matched_terms(text, rule.signals)
    if not signals:
        return None
    intents = explicit_memory_intents(text)
    required = matched_terms(text, rule.required_intents)
    if rule.required_intents and not required:
        return None
    negatives = extraction_noise_reasons(text) + [f"rule_negative:{term}" for term in matched_terms(text, rule.negative_signals)]
    if negatives:
        return None
    confidence = "high" if (intents and len(signals) >= 2) or required else "medium"
    return {
        "rule": rule.name,
        "signals": signals,
        "intents": intents,
        "confidence": confidence,
        "reason": f"rule={rule.name}; signals={','.join(signals[:4])}; intents={','.join(intents[:4]) or 'none'}",
    }


def candidate_key_for(category, statement):
    text = clean_text(statement)
    if "时区" in text or "Asia/Shanghai" in text or "东八区" in text:
        return "timezone"
    if "昵称" in text:
        return "nickname"
    if "中文" in text or "结论先行" in text:
        return "communication_style"
    if "CP Memory" in text and category == CATEGORY_RELATIONSHIP:
        return "cp_memory"
    if "不做大平台" in text or "通用个人助手" in text:
        return "product_direction"
    if "目标" in text or "计划" in text or "最近在" in text or "正在" in text:
        return "current_goal"
    if "先做" in text or "这轮先" in text or "当前在做" in text:
        return "current_focus"
    if "后面再说" in text or "先放一放" in text or "待处理" in text:
        return "pending_queue"
    return slugify_key(text, fallback=category)


def looks_like_explicit_rule(statement):
    text = clean_text(statement)
    if len(text) < 12 or len(text) > 180:
        return False
    rule_markers = ("只能", "必须", "一定要", "优先", "为准", "不要", "不能", "统一", "一律", "默认")
    return any(marker in text for marker in rule_markers)


def decision_title_for(statement):
    text = clean_text(statement)
    lower_text = text.lower()
    if any(token in text for token in ("config.toml", "配置文件", "双引号", "双斜杠", "双反斜杠", "路径")):
        return "Windows TOML 路径转义规则"
    if "cp memory" in lower_text and any(token in text for token in ("主库", "优先", "辅助记忆", "Codex memory", "自带记忆")):
        return "记忆检索顺序：CP Memory 主库优先"
    if "自动化" in text and any(token in text for token in ("唯一", "混淆")):
        return "CP Memory 自动化唯一性规则"
    return ""


def decision_text_for(statement):
    text = clean_text(statement)
    if text.startswith("用户要求"):
        text = text[4:].lstrip("：:，, ")
    if text.startswith("用户"):
        text = text[2:].lstrip("：:，, ")
    return clean_text(text)


def extract_personal_candidates(prompt, assistant):
    candidates = []
    seen = set()
    for sentence in split_sentences(prompt) + split_sentences(assistant):
        normalized = normalize_user_statement(sentence)
        effective_text = normalized
        raw_text = clean_text(sentence)
        if not is_explicit_memory_sentence(sentence):
            if any(token in raw_text for token in ("先做", "后面再说", "先放一放", "这轮先", "当前在做", "还没做完", "待处理", "继续推进")):
                effective_text = f"用户当前{raw_text}"
            else:
                continue
        if not effective_text.startswith("用户"):
            effective_text = f"用户要求{effective_text}"
        if extraction_noise_reasons(normalized):
            continue
        for rule in EXTRACTION_RULES:
            evaluation = evaluate_extraction_rule(rule, effective_text)
            if not evaluation:
                continue
            key = candidate_key_for(rule.category, effective_text)
            dedupe_key = (rule.category, key, effective_text)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append(
                {
                    "memory_type": rule.category,
                    "key": key,
                    "value": effective_text[:220],
                    "details": f"Auto extracted from stop hook ({evaluation['reason']})",
                    "stability_score": rule.stability_score,
                    "confidence": evaluation["confidence"],
                    "extraction_rule": evaluation["rule"],
                    "matched_signals": evaluation["signals"],
                    "matched_intents": evaluation["intents"],
                    "needs_review": evaluation["confidence"] != "high",
                }
            )
    return candidates[:6]


def extract_decision_candidates(prompt, assistant):
    candidates = []
    seen = set()
    for sentence in split_sentences(prompt) + split_sentences(assistant):
        raw_text = clean_text(sentence)
        if not raw_text or "?" in raw_text or "？" in raw_text:
            continue
        normalized = normalize_user_statement(sentence)
        effective_text = normalized
        if not effective_text.startswith("用户") and looks_like_explicit_rule(raw_text):
            effective_text = f"用户要求{raw_text}"
        if not effective_text.startswith("用户"):
            continue
        if looks_like_meta_explanation(normalized):
            continue
        if not looks_like_explicit_rule(effective_text):
            continue
        title = decision_title_for(effective_text)
        if not title:
            continue
        decision_text = decision_text_for(effective_text)
        dedupe_key = (title, decision_text)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidates.append(
            {
                "title": title,
                "context": meaningful_text(prompt, 180),
                "decision": decision_text,
                "rationale": "Auto extracted from explicit user governance rule in stop hook",
            }
        )
    return candidates[:3]


def classify_topics(text):
    topics = []
    mapping = [
        ("CP Memory", ["CP Memory", "记忆", "hook", "插件", "Hermes"]),
        ("Codex", ["Codex", "新会话", "MCP", "skill", "plugin"]),
        ("BasisProject", ["BasisProject", "DDD", "MyBatis", "Application", "Repository"]),
        ("Bug", ["bug", "问题", "报错", "修复", "原因"]),
        ("Export", ["导出", "Excel", "流程", "审批"]),
        ("Database", ["数据库", "SQL", "MySQL", "表", "字段"]),
    ]
    for topic, terms in mapping:
        if has_any(text, terms):
            topics.append(topic)
    return topics[:4]


def make_turn_summary(prompt, assistant):
    prompt_part = meaningful_text(prompt, 360)
    assistant_part = meaningful_text(assistant, 900)
    topics = classify_topics(f"{prompt}\n{assistant}")
    importance = classify_importance(prompt, assistant)
    lines = [f"用户问题：{prompt_part}", f"处理结果：{assistant_part}"]
    if topics:
        lines.append(f"主题：{', '.join(topics)}")
    lines.append(f"重要性：{importance}/5")
    return "\n".join(lines), importance, topics


def should_save_turn(prompt, assistant):
    text = f"{prompt}\n{assistant}"
    if len(text.strip()) < 80:
        return False
    save_terms = [
        "记住",
        "总结",
        "改造",
        "修复",
        "实现",
        "计划",
        "方案",
        "决定",
        "约定",
        "偏好",
        "以后",
        "下次",
        "bug",
        "问题",
        "原因",
        "结论",
        "CP Memory",
        "hook",
        "插件",
        "数据库",
        "接口",
    ]
    return has_any(text, save_terms) or len(text) > 1200


def search_facts(conn, terms, limit=8, categories=None):
    query = " ".join(term for term in terms if term)
    return search_records(conn, query, limit=limit, mode="or", categories=categories)


def persist_turn_summary(conn, prompt, assistant):
    value, importance, topics = make_turn_summary(prompt, assistant)
    tags = ["cp-memory", "auto-summary", "stop-hook", f"importance:{importance}"]
    tags.extend(f"topic:{topic}" for topic in topics)
    task = active_task(conn)
    rid, action = upsert_fact(
        conn,
        "CP Memory.CurrentConversation",
        LATEST_TURN_SUMMARY_PROPERTY,
        value,
        tags=",".join(tags),
        category=CATEGORY_SUMMARY,
        importance=importance,
        expires_at=expiry_for_importance(importance),
        source="stop-hook",
        summary_type="turn",
        payload={
            "prompt": prompt,
            "assistant": assistant,
            "summary": value,
            "topics": topics,
            "importance": importance,
            "task": {"id": task["id"], "name": task["property"]} if task else None,
        },
        content_type="application/json",
    )
    history_id, _ = upsert_fact(
        conn,
        "CP Memory.CurrentConversation",
        unique_property(SUMMARY_HISTORY_PREFIX),
        value,
        tags=",".join(tags + ["history"]),
        category=CATEGORY_SUMMARY,
        importance=importance,
        expires_at=expiry_for_importance(importance),
        source="stop-hook-history",
        summary_type="turn",
        payload={
            "prompt": prompt,
            "assistant": assistant,
            "summary": value,
            "topics": topics,
            "importance": importance,
            "task": {"id": task["id"], "name": task["property"]} if task else None,
        },
        content_type="application/json",
    )
    if task:
        link_records(conn, "fact", rid, "about_task", "fact", task["id"])
        link_records(conn, "fact", history_id, "about_task", "fact", task["id"])
    return rid, action


def persist_personal_signals(conn, prompt, assistant, summary_id=""):
    candidates = extract_personal_candidates(prompt, assistant)
    decision_candidates = extract_decision_candidates(prompt, assistant)
    if not candidates and not decision_candidates:
        return {"episode_id": "", "created": []}
    episode_text = meaningful_text(f"{prompt} {assistant}", 240)
    episode_id, _, _ = upsert_personal_memory(
        conn,
        "episode",
        "user",
        unique_property("conversation.auto."),
        f"自动提炼事件：{episode_text}",
        details="Auto extracted high-value personal signal from stop hook",
        tags="cp-memory,auto-extract,episode",
        source="stop-hook-auto-episode",
        evidence_count=1,
        stability_score=48,
        payload={"prompt": prompt, "assistant": assistant, "candidates": candidates},
    )
    if summary_id:
        link_records(conn, "fact", episode_id, "derived_from_summary", "fact", summary_id)
        link_records(conn, "fact", summary_id, "captures_episode", "fact", episode_id)
    created = []
    for candidate in candidates:
        rid, action, category = upsert_personal_memory(
            conn,
            candidate["memory_type"],
            "user",
            candidate["key"],
            candidate["value"],
            details=candidate["details"],
            confidence=candidate.get("confidence", "medium"),
            tags=f"cp-memory,auto-extract,{candidate['memory_type']}",
            source="stop-hook-auto-extract",
            evidence_count=1,
            stability_score=candidate["stability_score"],
            payload={
                "prompt": prompt,
                "assistant": assistant,
                "episode_id": episode_id,
                "extraction_rule": candidate.get("extraction_rule", ""),
                "matched_signals": candidate.get("matched_signals", []),
                "matched_intents": candidate.get("matched_intents", []),
                "needs_review": candidate.get("needs_review", True),
            },
        )
        link_records(conn, "fact", rid, "derived_from_episode", "fact", episode_id)
        created.append({"id": rid, "action": action, "category": category, "key": candidate["key"]})
    created_decisions = []
    for candidate in decision_candidates:
        rid, action = upsert_decision_record(
            conn,
            title=candidate["title"],
            context=candidate["context"],
            decision=candidate["decision"],
            rationale=candidate["rationale"],
            source="stop-hook-auto-decision",
            review_state="pending_review",
            confidence="medium",
            payload={"prompt": prompt, "assistant": assistant, "episode_id": episode_id},
        )
        link_records(conn, "decision", rid, "derived_from_episode", "fact", episode_id)
        link_records(conn, "fact", rid, "derived_from_episode", "fact", episode_id)
        if summary_id:
            link_records(conn, "decision", rid, "derived_from_summary", "fact", summary_id)
            link_records(conn, "fact", rid, "derived_from_summary", "fact", summary_id)
        created_decisions.append({"id": rid, "action": action, "category": CATEGORY_DECISION, "title": candidate["title"]})
    return {"episode_id": episode_id, "created": created, "decisions": created_decisions}


def persist_checkpoint(conn, trigger, turn_id, raw_data):
    task = active_task(conn)
    preview = f"Conversation compacted (trigger: {trigger})"
    if turn_id:
        preview += f" | turn: {turn_id}"
    rid, action = upsert_fact(
        conn,
        "Hook",
        LATEST_CHECKPOINT_PROPERTY,
        preview,
        confidence="high",
        tags="compaction,checkpoint",
        category=CATEGORY_CHECKPOINT,
        importance=4,
        expires_at="",
        source="pre-compact-hook",
        summary_type="checkpoint",
        payload={
            "trigger": trigger,
            "turn_id": turn_id,
            "task": {"id": task["id"], "name": task["property"]} if task else None,
            "raw_event": raw_data,
        },
        content_type="application/json",
    )
    history_id, _ = upsert_fact(
        conn,
        "Hook",
        unique_property(CHECKPOINT_HISTORY_PREFIX),
        preview,
        confidence="high",
        tags="compaction,checkpoint,history",
        category=CATEGORY_CHECKPOINT,
        importance=4,
        expires_at="",
        source="pre-compact-hook-history",
        summary_type="checkpoint",
        payload={
            "trigger": trigger,
            "turn_id": turn_id,
            "task": {"id": task["id"], "name": task["property"]} if task else None,
            "raw_event": raw_data,
        },
        content_type="application/json",
    )
    if task:
        link_records(conn, "fact", rid, "about_task", "fact", task["id"])
        link_records(conn, "fact", history_id, "about_task", "fact", task["id"])
    return rid, action


def build_startup_context(prompt=""):
    conn = connect()
    try:
        return build_restore_context(conn, prompt=prompt, max_chars=3200), detect_restore_intent(prompt)
    finally:
        conn.close()


def build_prompt_context(prompt=""):
    if not should_inject_restore_context(prompt):
        return "", detect_restore_intent(prompt)
    conn = connect()
    try:
        return build_restore_context(conn, prompt=prompt, max_chars=2200), detect_restore_intent(prompt)
    finally:
        conn.close()
