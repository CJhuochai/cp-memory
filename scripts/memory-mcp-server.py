import json
import re

from mcp.server.fastmcp import FastMCP

from cp_memory_store import (
    assess_recall_strength,
    build_recall_sections,
    search_codex_auxiliary_memory,
    should_use_auxiliary_memory,
    apply_review_action,
    build_review_inbox,
    build_restore_context,
    build_review_digest,
    CATEGORY_CHECKPOINT,
    CATEGORY_DECISION,
    CATEGORY_AUTOMATION,
    CATEGORY_TASK,
    CATEGORY_TASK_DONE,
    PERSONAL_MEMORY_CATEGORIES,
    CATEGORY_SUMMARY,
    active_task,
    auto_extract_governance_stats,
    auto_extract_cleanup_candidates,
    category_explanation,
    cleanup_auto_extract_noise,
    classify_importance,
    db_path,
    delete_fact,
    consolidate_episode,
    derive_personal_from_episode,
    ensure_fulltext_populated,
    evaluate_memory_quality,
    explain_fact,
    expiry_for_importance,
    fts_available,
    get_db,
    governance_acceptance_report,
    infer_recall_intent,
    init_db,
    link_records,
    list_links,
    new_id,
    normalize_category,
    correct_memory,
    normalize_limit,
    now_local,
    payload_preview,
    personal_memory_conflicts,
    personal_memory_review,
    personal_resolution_candidates,
    resolve_personal_conflict,
    recent_records,
    recall_primary_records,
    resolve_entity,
    schema_description,
    search_records,
    semantic_upgrade_marker_path,
    touch_fact_ids,
    upsert_fact,
    upsert_decision_record,
    upsert_personal_memory,
    upsert_meta,
    review_fact,
)


mcp = FastMCP(
    "cp-memory",
    instructions=(
        "CP Memory: cross-project persistent memory for Codex by CJ. "
        "Store facts, summaries, checkpoints, aliases, decisions, tasks, workflows, payloads, and relations via MCP tools. "
        "Data is stored locally in ~/.cp-memory/memory.db."
    ),
)


def rows_to_json(rows):
    return json.dumps([dict(row) for row in rows], ensure_ascii=False, default=str)


@mcp.tool(description="Return CP Memory schema explanations and whether FTS is available.")
def memory_schema() -> str:
    conn = get_db()
    init_db(conn)
    result = {
        "tables": schema_description(),
        "db_path": str(db_path()),
        "fts_available": fts_available(conn),
    }
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="Add or update a memory fact. Supports explicit category and optional long-form content payload.")
def memory_add(
    entity: str,
    property: str,
    value: str,
    confidence: str = "high",
    tags: str = "",
    category: str = "fact",
    content: str = "",
    content_type: str = "text/plain",
) -> str:
    conn = get_db()
    init_db(conn)
    payload = content.strip() if (content or "").strip() else None
    normalized_category = normalize_category(category, entity, property, tags, "memory_add")
    importance = classify_importance(value, tags, normalized_category)
    expires_at = expiry_for_importance(importance)
    rid, action = upsert_fact(
        conn,
        entity,
        property,
        value,
        confidence=confidence,
        tags=tags,
        category=normalized_category,
        importance=importance,
        expires_at=expires_at,
        source="memory_add",
        payload=payload,
        content_type=content_type,
    )
    conn.commit()
    conn.close()
    return json.dumps({"id": rid, "ok": True, "action": action, "category": normalized_category}, ensure_ascii=False)


@mcp.tool(description="Add or update a long-term personal assistant memory using Profile, Preference, Relationship, Ongoing, Episode, or BeliefDecision.")
def memory_personal_add(
    memory_type: str,
    subject: str,
    key: str,
    value: str,
    details: str = "",
    confidence: str = "high",
    tags: str = "",
    evidence_count: int = 1,
    stability_score: int = -1,
    valid_from: str = "",
    valid_until: str = "",
    scope: str = "",
    sensitivity: str = "normal",
) -> str:
    conn = get_db()
    init_db(conn)
    try:
        rid, action, category = upsert_personal_memory(
            conn,
            memory_type,
            subject,
            key,
            value,
            details=details,
            confidence=confidence,
            tags=tags,
            source="memory_personal_add",
            evidence_count=evidence_count,
            stability_score=None if stability_score < 0 else stability_score,
            valid_from=valid_from,
            valid_until=valid_until,
            scope=scope,
            sensitivity=sensitivity,
        )
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    conn.commit()
    conn.close()
    return json.dumps({"id": rid, "ok": True, "action": action, "category": category}, ensure_ascii=False)


@mcp.tool(description="Derive a long-term personal memory from an existing Episode and link it back to the source episode.")
def memory_personal_derive(
    episode_id: str,
    memory_type: str,
    subject: str,
    key: str,
    value: str,
    details: str = "",
    confidence: str = "high",
    tags: str = "",
    evidence_count: int = 1,
    stability_score: int = -1,
) -> str:
    conn = get_db()
    init_db(conn)
    try:
        result = derive_personal_from_episode(
            conn,
            episode_id,
            memory_type,
            subject,
            key,
            value,
            details=details,
            confidence=confidence,
            tags=tags,
            evidence_count=evidence_count,
            stability_score=None if stability_score < 0 else stability_score,
        )
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    if not result:
        conn.close()
        return json.dumps({"ok": False, "error": "episode not found"}, ensure_ascii=False)
    rid, action, category = result
    conn.commit()
    conn.close()
    return json.dumps({"id": rid, "ok": True, "action": action, "category": category, "episode_id": episode_id}, ensure_ascii=False)


@mcp.tool(description="Preview or apply conservative Episode consolidation into long-term personal memories.")
def memory_episode_consolidate(episode_id: str, subject: str = "user", dry_run: bool = True, limit: int = 5) -> str:
    conn = get_db()
    init_db(conn)
    result = consolidate_episode(conn, episode_id, subject=subject, dry_run=dry_run, limit=limit)
    if not dry_run:
        conn.commit()
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="List personal assistant memories, optionally filtered by the six-model memory type.")
def memory_personal_list(memory_type: str = "", subject: str = "", limit: int = 30) -> str:
    conn = get_db()
    init_db(conn)
    limit = normalize_limit(limit, default=30, maximum=200)
    params = []
    conditions = []
    if memory_type:
        category = normalize_category(memory_type)
        if category not in PERSONAL_MEMORY_CATEGORIES:
            conn.close()
            return json.dumps({"ok": False, "error": f"unsupported personal memory type: {memory_type}"}, ensure_ascii=False)
        conditions.append("f.category = ?")
        params.append(category)
    else:
        placeholders = ",".join("?" for _ in PERSONAL_MEMORY_CATEGORIES)
        conditions.append(f"f.category IN ({placeholders})")
        params.extend(sorted(PERSONAL_MEMORY_CATEGORIES))
    if subject:
        conditions.append("f.entity LIKE ?")
        params.append(f"%.{subject.strip()}")
    where = " AND ".join(conditions)
    rows = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.confidence, f.tags, f.category, f.created_at, f.updated_at, "
        "m.stability_score, m.evidence_count, m.correction_status, m.valid_from, m.valid_until, m.scope, m.sensitivity, "
        "COALESCE(p.content, '') AS payload "
        "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id LEFT JOIN memory_payloads p ON p.fact_id = f.id "
        f"WHERE {where} ORDER BY f.updated_at DESC, f.created_at DESC LIMIT ?",
        [*params, limit],
    ).fetchall()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Return a user-facing personal memory review dashboard with counts, recent memories, conflicts, and consolidation candidates.")
def memory_personal_review(subject: str = "user", limit: int = 10) -> str:
    conn = get_db()
    init_db(conn)
    review = personal_memory_review(conn, subject=subject, limit=limit)
    conn.close()
    return json.dumps(review, ensure_ascii=False, default=str)


@mcp.tool(description="Return a Markdown memory review digest with recent memories, pending auto-extracts, conflicts, stale candidates, and resolution suggestions.")
def memory_review_digest(subject: str = "user", limit: int = 10) -> str:
    conn = get_db()
    init_db(conn)
    digest = build_review_digest(conn, subject=subject, limit=limit)
    conn.close()
    return digest


@mcp.tool(description="Show a small actionable inbox for pending memory review. This previews items only and never deletes memory.")
def memory_review_inbox(subject: str = "user", limit: int = 5) -> str:
    conn = get_db()
    init_db(conn)
    inbox = build_review_inbox(conn, subject=subject, limit=limit)
    conn.close()
    return json.dumps(inbox, ensure_ascii=False, default=str)


@mcp.tool(description="Apply one explicit memory review action: confirm, wrong, stale, scoped, or skip. This never physically deletes memory.")
def memory_review_apply(id: str, action: str, reason: str = "", scope: str = "") -> str:
    conn = get_db()
    init_db(conn)
    try:
        result = apply_review_action(conn, id, action, reason=reason, scope=scope)
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    if result.get("changed"):
        conn.commit()
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="Mark a memory as corrected, stale, wrong, scoped, or confirmed; optionally replace its value.")
def memory_correct(id: str, status: str, reason: str = "", value: str = "") -> str:
    conn = get_db()
    init_db(conn)
    try:
        rid = correct_memory(conn, id, status, reason=reason, value=value)
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    if not rid:
        conn.close()
        return json.dumps({"ok": False, "error": "memory not found"}, ensure_ascii=False)
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "id": rid, "status": status}, ensure_ascii=False)


@mcp.tool(description="Resolve a personal-memory conflict by confirming or merging one winner and marking other memories stale, wrong, or scoped with audit links.")
def memory_personal_resolve(
    winner_id: str,
    loser_ids: str = "",
    merged_value: str = "",
    reason: str = "",
    loser_status: str = "stale",
    scope: str = "",
    valid_until: str = "",
) -> str:
    conn = get_db()
    init_db(conn)
    try:
        result = resolve_personal_conflict(
            conn,
            winner_id,
            loser_ids=loser_ids,
            merged_value=merged_value,
            reason=reason,
            loser_status=loser_status,
            scope=scope,
            valid_until=valid_until,
        )
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    if not result:
        conn.close()
        return json.dumps({"ok": False, "error": "winner memory not found"}, ensure_ascii=False)
    conn.commit()
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="Search memories using FTS when available, with OR ranking by default or strict AND matching.")
def memory_search(query: str, limit: int = 20, mode: str = "or", category: str = "") -> str:
    conn = get_db()
    init_db(conn)
    categories = [item.strip() for item in re.split(r"[,，、]+", category or "") if item.strip()]
    rows = search_records(conn, query, limit=limit, mode=mode, categories=categories or None)
    touch_fact_ids(conn, [row["id"] for row in rows if row["id"]])
    conn.commit()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Get all facts about an entity. Aliases resolve to the canonical entity first.")
def memory_probe(entity: str) -> str:
    conn = get_db()
    init_db(conn)
    canonical = resolve_entity(conn, entity)
    rows = conn.execute(
        "SELECT id, entity, property, value, confidence, tags, category, created_at, updated_at FROM facts WHERE entity=? ORDER BY updated_at DESC, created_at DESC",
        (canonical,),
    ).fetchall()
    conn.close()
    return json.dumps({"query": entity, "entity": canonical, "facts": [dict(row) for row in rows]}, ensure_ascii=False, default=str)


@mcp.tool(description="Explain a memory record, including meta, payload, and relations.")
def memory_explain(id: str = "", entity: str = "", property: str = "") -> str:
    conn = get_db()
    init_db(conn)
    explanation = explain_fact(conn, fact_id=id, entity=entity, prop=property)
    conn.close()
    if not explanation:
        return json.dumps({"error": "memory not found"}, ensure_ascii=False)
    return json.dumps(explanation, ensure_ascii=False, default=str)


@mcp.tool(description="Inspect a memory record in a user-friendly way, including where the preview, payload, and relations live.")
def memory_inspect(id: str = "", entity: str = "", property: str = "") -> str:
    conn = get_db()
    init_db(conn)
    explanation = explain_fact(conn, fact_id=id, entity=entity, prop=property)
    conn.close()
    if not explanation:
        return json.dumps({"error": "memory not found"}, ensure_ascii=False)
    fact = explanation["fact"]
    meta = explanation.get("meta") or {}
    payload = explanation.get("payload") or {}
    lines = [
        f"类别: {fact['category']}",
        f"对象: {fact['entity']}",
        f"属性: {fact['property']}",
        f"预览: {fact['value']}",
        f"含正文: {'是' if payload else '否'}",
        f"正文类型: {payload.get('content_type', '') or '无'}",
        f"来源: {meta.get('source', '') or '未知'}",
        f"摘要类型: {meta.get('summary_type', '') or '无'}",
        f"质量分: {meta.get('quality_score', '')}",
        f"噪声分: {meta.get('noise_score', '')}",
        f"稳定性: {meta.get('stability_score', '')}",
        f"证据数: {meta.get('evidence_count', '')}",
        f"适用范围: {meta.get('scope', '') or '全局'}",
        f"有效期: {meta.get('valid_from', '') or '未限定'} -> {meta.get('valid_until', '') or '未限定'}",
        f"敏感度: {meta.get('sensitivity', '') or 'normal'}",
        f"纠正状态: {meta.get('correction_status', '') or '无'}",
        f"解释: {explanation['meaning']}",
    ]
    if explanation["relations"]:
        lines.append("关系:")
        for relation in explanation["relations"]:
            lines.append(
                f"- {relation['source_kind']}:{relation['source_id']} --{relation['relation']}--> {relation['target_kind']}:{relation['target_id']}"
            )
    if explanation.get("history"):
        lines.append("历史时间线:")
        for event in explanation["history"][:5]:
            preview = f"{event['created_at']} | {event['event_type']}"
            if event.get("reason"):
                preview += f" | {event['reason']}"
            if event.get("new_value"):
                preview += f" | -> {str(event['new_value'])[:80]}"
            lines.append(f"- {preview}")
    if payload:
        lines.append(f"正文预览: {payload_preview(payload.get('content', ''), 240)}")
    return json.dumps(
        {"summary": "\n".join(lines), "detail": explanation},
        ensure_ascii=False,
        default=str,
    )


@mcp.tool(description="Add or update an alias for a canonical entity.")
def memory_alias_add(alias: str, entity: str, tags: str = "") -> str:
    conn = get_db()
    init_db(conn)
    ts = now_local()
    clean_alias = alias.strip()
    clean_entity = entity.strip()
    clean_tags = tags.strip()
    existing = conn.execute("SELECT created_at FROM aliases WHERE alias = ?", (clean_alias,)).fetchone()
    created = existing["created_at"] if existing else ts
    conn.execute(
        "INSERT OR REPLACE INTO aliases (alias, entity, tags, created_at, updated_at) VALUES (?,?,?,?,?)",
        (clean_alias, clean_entity, clean_tags, created, ts),
    )
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "alias": clean_alias, "entity": clean_entity}, ensure_ascii=False)


@mcp.tool(description="List aliases, optionally filtered by canonical entity.")
def memory_alias_list(entity: str = "", limit: int = 100) -> str:
    conn = get_db()
    init_db(conn)
    limit = normalize_limit(limit, default=100, maximum=500)
    if entity:
        canonical = resolve_entity(conn, entity)
        rows = conn.execute(
            "SELECT alias, entity, tags, created_at, updated_at FROM aliases WHERE entity=? ORDER BY updated_at DESC LIMIT ?",
            (canonical, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT alias, entity, tags, created_at, updated_at FROM aliases ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Update an existing fact value, confidence, category, or content payload.")
def memory_update(
    id: str,
    value: str,
    confidence: str = "",
    category: str = "",
    content: str = "",
    content_type: str = "text/plain",
) -> str:
    conn = get_db()
    init_db(conn)
    row = conn.execute(
        "SELECT entity, property, confidence, tags, category FROM facts WHERE id=?",
        (id,),
    ).fetchone()
    if not row:
        conn.close()
        return json.dumps({"error": f"fact {id} not found"}, ensure_ascii=False)
    normalized_category = normalize_category(category or row["category"], row["entity"], row["property"], row["tags"], "memory_update")
    importance = classify_importance(value, row["tags"], normalized_category)
    rid, _ = upsert_fact(
        conn,
        row["entity"],
        row["property"],
        value,
        confidence=confidence or row["confidence"],
        tags=row["tags"],
        category=normalized_category,
        importance=importance,
        expires_at=expiry_for_importance(importance),
        source="memory_update",
        payload=content if content else None,
        content_type=content_type,
    )
    if not content:
        ensure_fulltext_populated(conn)
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "id": rid, "category": normalized_category}, ensure_ascii=False)


@mcp.tool(description="Delete a fact by ID, including its metadata, payload, and graph links.")
def memory_remove(id: str) -> str:
    conn = get_db()
    init_db(conn)
    delete_fact(conn, id)
    conn.commit()
    conn.close()
    return json.dumps({"ok": True}, ensure_ascii=False)


@mcp.tool(description="List recent facts, optionally filtered by category.")
def memory_list(category: str = "", limit: int = 30) -> str:
    conn = get_db()
    init_db(conn)
    limit = normalize_limit(limit, default=30)
    if category:
        rows = conn.execute(
            "SELECT id, entity, property, value, confidence, tags, category, created_at, updated_at FROM facts WHERE category=? ORDER BY updated_at DESC, created_at DESC LIMIT ?",
            (normalize_category(category), limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, entity, property, value, confidence, tags, category, created_at, updated_at FROM facts ORDER BY updated_at DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Get memory statistics across facts, payloads, decisions, workflows, aliases, and relations.")
def memory_stats() -> str:
    conn = get_db()
    init_db(conn)
    total = conn.execute("SELECT COUNT(*) AS cnt FROM facts").fetchone()["cnt"]
    cats = conn.execute("SELECT category, COUNT(*) AS cnt FROM facts GROUP BY category").fetchall()
    top = conn.execute("SELECT entity, COUNT(*) AS cnt FROM facts GROUP BY entity ORDER BY cnt DESC LIMIT 10").fetchall()
    dec_count = conn.execute("SELECT COUNT(*) AS cnt FROM decisions").fetchone()["cnt"]
    wf_count = conn.execute("SELECT COUNT(*) AS cnt FROM workflows").fetchone()["cnt"]
    alias_count = conn.execute("SELECT COUNT(*) AS cnt FROM aliases").fetchone()["cnt"]
    payload_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_payloads").fetchone()["cnt"]
    link_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_links").fetchone()["cnt"]
    personal_placeholders = ",".join("?" for _ in PERSONAL_MEMORY_CATEGORIES)
    personal_counts = conn.execute(
        f"SELECT category, COUNT(*) AS cnt FROM facts WHERE category IN ({personal_placeholders}) GROUP BY category",
        sorted(PERSONAL_MEMORY_CATEGORIES),
    ).fetchall()
    auto_extract_stats = auto_extract_governance_stats(conn, limit=5)
    conn.close()
    return json.dumps(
        {
            "total_facts": total,
            "by_category": {row["category"]: row["cnt"] for row in cats},
            "top_entities": [{"entity": row["entity"], "count": row["cnt"]} for row in top],
            "decisions_count": dec_count,
            "workflows_count": wf_count,
            "aliases_count": alias_count,
            "payloads_count": payload_count,
            "links_count": link_count,
            "personal_memory_counts": {row["category"]: row["cnt"] for row in personal_counts},
            "auto_extract_governance": auto_extract_stats,
        },
        ensure_ascii=False,
    )


@mcp.tool(description="Return CP Memory health, migration state, FTS state, and active task.")
def memory_health() -> str:
    conn = get_db()
    init_db(conn)
    facts = conn.execute("SELECT COUNT(*) AS cnt FROM facts").fetchone()["cnt"]
    decisions = conn.execute("SELECT COUNT(*) AS cnt FROM decisions").fetchone()["cnt"]
    workflows = conn.execute("SELECT COUNT(*) AS cnt FROM workflows").fetchone()["cnt"]
    aliases = conn.execute("SELECT COUNT(*) AS cnt FROM aliases").fetchone()["cnt"]
    meta_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_meta").fetchone()["cnt"]
    payload_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_payloads").fetchone()["cnt"]
    link_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_links").fetchone()["cnt"]
    expired_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE expires_at != '' AND expires_at < ?",
        (now_local(),),
    ).fetchone()["cnt"]
    high_importance_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_meta WHERE importance >= 5").fetchone()["cnt"]
    avg_quality = conn.execute("SELECT ROUND(AVG(quality_score), 2) AS val FROM memory_meta").fetchone()["val"]
    avg_noise = conn.execute("SELECT ROUND(AVG(noise_score), 2) AS val FROM memory_meta").fetchone()["val"]
    personal_placeholders = ",".join("?" for _ in PERSONAL_MEMORY_CATEGORIES)
    personal_count = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM facts WHERE category IN ({personal_placeholders})",
        sorted(PERSONAL_MEMORY_CATEGORIES),
    ).fetchone()["cnt"]
    corrected_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_meta WHERE correction_status != ''").fetchone()["cnt"]
    auto_extract_stats = auto_extract_governance_stats(conn, limit=5)
    legacy_marker = semantic_upgrade_marker_path().exists()
    task = active_task(conn)
    result = {
        "name": "CP Memory",
        "db_path": str(db_path()),
        "fts_available": fts_available(conn),
        "semantic_upgrade_applied": legacy_marker,
        "facts_count": facts,
        "decisions_count": decisions,
        "workflows_count": workflows,
        "aliases_count": aliases,
        "meta_count": meta_count,
        "payload_count": payload_count,
        "link_count": link_count,
        "expired_count": expired_count,
        "high_importance_count": high_importance_count,
        "avg_quality_score": avg_quality,
        "avg_noise_score": avg_noise,
        "personal_memory_count": personal_count,
        "corrected_memory_count": corrected_count,
        "auto_extract_governance": auto_extract_stats,
        "active_task": dict(task) if task else None,
    }
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="Record an architecture or technical decision and mirror it into facts with strong metadata.")
def memory_decision_add(title: str, context: str, decision: str, rationale: str = "") -> str:
    conn = get_db()
    init_db(conn)
    rid, action = upsert_decision_record(
        conn,
        title=title.strip(),
        context=context.strip(),
        decision=decision.strip(),
        rationale=rationale.strip(),
        source="memory_decision_add",
        review_state="confirmed",
        confidence="high",
    )
    conn.commit()
    conn.close()
    return json.dumps({"id": rid, "ok": True, "action": action}, ensure_ascii=False)


@mcp.tool(description="List recorded decisions, most recent first.")
def memory_decision_list(limit: int = 20) -> str:
    conn = get_db()
    init_db(conn)
    rows = conn.execute(
        "SELECT id, title, context, decision, rationale, source, status, review_state, confidence, created_at, updated_at FROM decisions ORDER BY updated_at DESC, created_at DESC LIMIT ?",
        (normalize_limit(limit),),
    ).fetchall()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Set the current active task.")
def memory_task_set(task_name: str, description: str = "") -> str:
    conn = get_db()
    init_db(conn)
    ts = now_local()
    conn.execute(
        "UPDATE facts SET category=?, updated_at=? WHERE entity='__current_task' AND category=?",
        ("task_done", ts, "task"),
    )
    rid = "task_" + new_id()
    _, _ = upsert_fact(
        conn,
        "__current_task",
        task_name.strip(),
        (description or "").strip(),
        confidence="high",
        tags="status:active",
        category="task",
        importance=4,
        expires_at="",
        source="memory_task_set",
        summary_type="task",
        payload={"task_name": task_name.strip(), "description": (description or "").strip(), "status": "active"},
        content_type="application/json",
    )
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "task": task_name}, ensure_ascii=False)


@mcp.tool(description="Get the current active task.")
def memory_task_get() -> str:
    conn = get_db()
    init_db(conn)
    row = conn.execute(
        "SELECT id, property AS task_name, value AS description, created_at, updated_at FROM facts WHERE entity='__current_task' AND category='task' ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return json.dumps(dict(row) if row else {"task_name": None, "description": None}, ensure_ascii=False, default=str)


@mcp.tool(description="Mark the current task as complete with a result summary.")
def memory_task_done(result: str = "") -> str:
    conn = get_db()
    init_db(conn)
    row = conn.execute(
        "SELECT id, property FROM facts WHERE entity='__current_task' AND category='task' ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    if row:
        upsert_fact(
            conn,
            "__current_task",
            row["property"],
            (result or "").strip(),
            confidence="high",
            tags="status:done",
            category="task_done",
            importance=4,
            expires_at="",
            source="memory_task_done",
            summary_type="task",
            payload={"task_name": row["property"], "result": (result or "").strip(), "status": "done"},
            content_type="application/json",
        )
    conn.commit()
    conn.close()
    return json.dumps({"ok": True}, ensure_ascii=False)


@mcp.tool(description="Save a reusable workflow or procedure.")
def memory_workflow_save(name: str, steps: str, category: str = "") -> str:
    conn = get_db()
    init_db(conn)
    ts = now_local()
    existing = conn.execute("SELECT created_at FROM workflows WHERE name=?", (name.strip(),)).fetchone()
    created = existing["created_at"] if existing else ts
    conn.execute(
        "INSERT OR REPLACE INTO workflows (name, steps, category, created_at, updated_at) VALUES (?,?,?,?,?)",
        (name.strip(), steps.strip(), category.strip(), created, ts),
    )
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "name": name.strip()}, ensure_ascii=False)


@mcp.tool(description="Get a saved workflow by name.")
def memory_workflow_get(name: str) -> str:
    conn = get_db()
    init_db(conn)
    row = conn.execute(
        "SELECT name, steps, category, created_at, updated_at FROM workflows WHERE name=?",
        (name.strip(),),
    ).fetchone()
    conn.close()
    if row:
        return json.dumps(dict(row), ensure_ascii=False, default=str)
    return json.dumps({"error": f"workflow '{name}' not found"}, ensure_ascii=False)


@mcp.tool(description="List saved workflows.")
def memory_workflow_list(category: str = "") -> str:
    conn = get_db()
    init_db(conn)
    if category:
        rows = conn.execute(
            "SELECT name, category, updated_at FROM workflows WHERE category=? ORDER BY updated_at DESC",
            (category.strip(),),
        ).fetchall()
    else:
        rows = conn.execute("SELECT name, category, updated_at FROM workflows ORDER BY updated_at DESC").fetchall()
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Create an explicit memory relation between two records.")
def memory_link_add(source_kind: str, source_id: str, relation: str, target_kind: str, target_id: str) -> str:
    conn = get_db()
    init_db(conn)
    link_id, action = link_records(conn, source_kind, source_id, relation, target_kind, target_id)
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "id": link_id, "action": action}, ensure_ascii=False)


@mcp.tool(description="List explicit memory relations.")
def memory_link_list(source_kind: str = "", source_id: str = "", target_kind: str = "", target_id: str = "", relation: str = "") -> str:
    conn = get_db()
    init_db(conn)
    rows = list_links(conn, source_kind=source_kind, source_id=source_id, target_kind=target_kind, target_id=target_id, relation=relation)
    conn.close()
    return rows_to_json(rows)


@mcp.tool(description="Mark matching memories as accessed, optionally by IDs.")
def memory_touch(ids: str = "", query: str = "") -> str:
    conn = get_db()
    init_db(conn)
    touched = []
    if ids:
        touched = [item.strip() for item in re.split(r"[,，、\s]+", ids) if item.strip()]
    elif query:
        touched = [row["id"] for row in search_records(conn, query, 20, "or")]
    count = touch_fact_ids(conn, touched)
    conn.commit()
    conn.close()
    return json.dumps({"ok": True, "touched": count}, ensure_ascii=False)


@mcp.tool(description="Find possible conflicting memories, including duplicate facts and personal-memory contradictions.")
def memory_conflicts(limit: int = 50) -> str:
    conn = get_db()
    init_db(conn)
    limit = normalize_limit(limit, default=50, maximum=200)
    fact_groups = conn.execute(
        "SELECT entity, property, COUNT(*) AS cnt FROM facts GROUP BY entity, property HAVING cnt > 1 ORDER BY cnt DESC LIMIT ?",
        (limit,),
    ).fetchall()
    decision_groups = conn.execute(
        "SELECT title, COUNT(*) AS cnt FROM decisions GROUP BY title HAVING cnt > 1 ORDER BY cnt DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conflicts = []
    for group in fact_groups:
        items = conn.execute(
            "SELECT id, entity, property, value, tags, category, updated_at FROM facts WHERE entity=? AND property=? ORDER BY updated_at DESC",
            (group["entity"], group["property"]),
        ).fetchall()
        conflicts.append({"type": "fact", "entity": group["entity"], "property": group["property"], "count": group["cnt"], "items": [dict(item) for item in items]})
    for group in decision_groups:
        items = conn.execute(
            "SELECT id, title, decision, created_at FROM decisions WHERE title=? ORDER BY created_at DESC",
            (group["title"],),
        ).fetchall()
        conflicts.append({"type": "decision", "title": group["title"], "count": group["cnt"], "items": [dict(item) for item in items]})
    personal_conflicts = personal_memory_conflicts(conn, limit=limit)
    resolution_candidates = personal_resolution_candidates(personal_conflicts, limit=limit)
    conn.close()
    return json.dumps(
        {
            "legacy_conflicts": conflicts,
            "personal_conflicts": personal_conflicts,
            "resolution_candidates": resolution_candidates,
            "total": len(conflicts) + len(personal_conflicts),
        },
        ensure_ascii=False,
        default=str,
    )


@mcp.tool(description="Run memory maintenance: backfill meta, rebuild indexes, and optionally expire low-value records.")
def memory_maintenance(dry_run: bool = True, expire: bool = False, limit: int = 200) -> str:
    conn = get_db()
    init_db(conn)
    ts = now_local()
    facts_without_meta = conn.execute(
        "SELECT id, value, tags, category FROM facts WHERE id NOT IN (SELECT fact_id FROM memory_meta) LIMIT ?",
        (normalize_limit(limit, default=200, maximum=1000),),
    ).fetchall()
    backfilled = 0
    reviewed = 0
    for row in facts_without_meta:
        importance = classify_importance(row["value"], row["tags"], row["category"])
        upsert_meta(conn, row["id"], importance, expiry_for_importance(importance), source="maintenance-backfill")
        backfilled += 1
    rows = conn.execute(
        "SELECT f.id, f.category, f.value, f.tags, COALESCE(m.source, '') AS source FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id LIMIT ?",
        (normalize_limit(limit, default=200, maximum=1000),),
    ).fetchall()
    for row in rows:
        review_fact(conn, row["id"], category=row["category"], source=row["source"])
        reviewed += 1
    ensure_fulltext_populated(conn)
    protected_categories = sorted(
        {
            CATEGORY_AUTOMATION,
            CATEGORY_DECISION,
            CATEGORY_TASK,
            CATEGORY_TASK_DONE,
            *PERSONAL_MEMORY_CATEGORIES,
        }
    )
    protected_placeholders = ",".join("?" for _ in protected_categories)
    expired_rows = conn.execute(
        "SELECT m.fact_id FROM memory_meta m JOIN facts f ON f.id=m.fact_id "
        f"WHERE m.pinned=0 AND m.importance <= 3 AND m.expires_at != '' AND m.expires_at < ? AND f.category NOT IN ({protected_placeholders}) LIMIT ?",
        (ts, *protected_categories, normalize_limit(limit, default=200, maximum=1000)),
    ).fetchall()
    protected_expired = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta m JOIN facts f ON f.id=m.fact_id "
        f"WHERE m.pinned=0 AND m.importance <= 3 AND m.expires_at != '' AND m.expires_at < ? AND f.category IN ({protected_placeholders})",
        (ts, *protected_categories),
    ).fetchone()["cnt"]
    expired_ids = [row["fact_id"] for row in expired_rows]
    deleted = 0
    if expire and not dry_run:
        for fact_id in expired_ids:
            delete_fact(conn, fact_id)
            deleted += 1
    duplicate_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM (SELECT entity, property FROM facts GROUP BY entity, property HAVING COUNT(*) > 1)"
    ).fetchone()["cnt"]
    personal_conflicts = personal_memory_conflicts(conn, limit=limit)
    auto_extract_stats = auto_extract_governance_stats(conn, limit=5)
    cleanup_preview = cleanup_auto_extract_noise(conn, dry_run=True, limit=min(limit, 20), action="mark_wrong")
    low_quality = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE quality_score < 55"
    ).fetchone()["cnt"]
    noisy_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE noise_score >= 20"
    ).fetchone()["cnt"]
    category_health = recent_records(
        conn,
        categories=["summary", "checkpoint", "decision", "task", "profile", "preference", "relationship", "ongoing", "episode", "belief_decision"],
        limit=10,
    )
    conn.commit()
    conn.close()
    return json.dumps(
        {
            "ok": True,
            "dry_run": dry_run,
            "backfilled_meta": backfilled,
            "reviewed_records": reviewed,
            "expired_candidates": len(expired_ids),
            "protected_expired_skipped": protected_expired,
            "deleted": deleted,
            "duplicate_groups": duplicate_count,
            "personal_conflict_count": len(personal_conflicts),
            "personal_conflict_samples": personal_conflicts[:5],
            "auto_extract_governance": auto_extract_stats,
            "auto_extract_cleanup_candidates": cleanup_preview["candidates"][:5],
            "low_quality_count": low_quality,
            "high_noise_count": noisy_count,
            "category_health_samples": [dict(item) for item in category_health],
        },
        ensure_ascii=False,
    )


@mcp.tool(description="Build a non-destructive governance acceptance report over the current memory.db, including auto-extract review queue, conflict samples, corrected samples, and restore probes.")
def memory_governance_report(limit: int = 5) -> str:
    conn = get_db()
    init_db(conn)
    report = governance_acceptance_report(conn, limit=limit)
    conn.close()
    return json.dumps(report, ensure_ascii=False, default=str)


@mcp.tool(description="Preview or apply cleanup for auto-extracted noise records that look like implementation explanations rather than real user memory. Prefer action=mark_wrong for safer governance; use delete only when you really want to remove rows.")
def memory_auto_extract_cleanup(dry_run: bool = True, limit: int = 20, action: str = "mark_wrong") -> str:
    conn = get_db()
    init_db(conn)
    try:
        result = cleanup_auto_extract_noise(conn, dry_run=dry_run, limit=limit, action=action)
    except ValueError as exc:
        conn.close()
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    if not dry_run:
        conn.commit()
    conn.close()
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(description="Build a compact restored context for startup, history recovery, or project continuation.")
def memory_restore_context(prompt: str = "", max_chars: int = 3200) -> str:
    conn = get_db()
    init_db(conn)
    context = build_restore_context(conn, prompt=prompt, max_chars=max_chars)
    conn.close()
    return json.dumps({"context": context}, ensure_ascii=False, default=str)


@mcp.tool(description="CP Memory-first recall入口。任何记忆相关问题都先查 CP Memory 主库，再根据主库命中质量决定是否补查 Codex 自带 memory 作为辅助背景。")
def memory_recall(query: str, intent: str = "", limit: int = 8, allow_auxiliary: bool = True) -> str:
    conn = get_db()
    init_db(conn)
    clean_limit = normalize_limit(limit, default=8, maximum=30)
    resolved_intent = infer_recall_intent(query, explicit_intent=intent)
    rows, resolved_intent = recall_primary_records(conn, query=query, intent=resolved_intent, limit=clean_limit)
    touch_fact_ids(conn, [dict(row).get("id", "") for row in rows if dict(row).get("id", "")])
    strength = assess_recall_strength(conn, rows, intent=resolved_intent, query=query)
    context = build_restore_context(conn, prompt=query, max_chars=1400 if clean_limit <= 10 else 2200)
    governance = None
    if resolved_intent == "governance":
        governance = governance_acceptance_report(conn, limit=min(clean_limit, 5))
    should_use_auxiliary = allow_auxiliary and should_use_auxiliary_memory(
        strength,
        intent=resolved_intent,
        row_count=len(rows),
        query=query,
    )
    auxiliary = []
    if should_use_auxiliary:
        auxiliary = search_codex_auxiliary_memory(query=query, limit=min(clean_limit, 6))
    sections = build_recall_sections(conn, rows, intent=resolved_intent, query=query, limit_per_section=max(2, min(clean_limit, 5)))
    conn.commit()
    conn.close()

    decision = "cp-memory-hit-strong"
    if strength["level"] == "medium":
        decision = "cp-memory-hit-medium"
    elif strength["level"] == "weak":
        decision = "cp-memory-hit-weak-auxiliary-considered"
    elif strength["level"] == "none":
        decision = "cp-memory-miss-auxiliary-fallback"

    return json.dumps(
        {
            "query": query,
            "intent": resolved_intent,
            "primary_source": "cp-memory",
            "used_auxiliary": bool(auxiliary),
            "decision": decision,
            "cp_memory": {
                "records": [dict(row) for row in rows],
                "sections": sections,
                "context": context,
                "strength": strength,
                "governance": governance,
            },
            "codex_memory": {
                "records": auxiliary,
                "note": "auxiliary_only",
            },
            "merged_answer_hints": {
                "winner": "cp-memory",
                "reason": "cp-memory is the primary governed memory source; Codex memory is only auxiliary background.",
            },
        },
        ensure_ascii=False,
        default=str,
    )


if __name__ == "__main__":
    init_db()
    mcp.run(transport="stdio")
