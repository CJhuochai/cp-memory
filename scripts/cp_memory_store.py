import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import uuid
from pathlib import Path


LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=8), name="Asia/Shanghai")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMEZONE_MIGRATION_MARKER_NAME = ".timezone-asia-shanghai-v2"
FTS_READY_MARKER_NAME = ".fts-ready-v1"
SEMANTIC_UPGRADE_MARKER_NAME = ".semantic-upgrade-v2"
DECISION_MIRROR_MARKER_NAME = ".decision-mirror-repair-v1"

CATEGORY_FACT = "fact"
CATEGORY_SUMMARY = "summary"
CATEGORY_CHECKPOINT = "checkpoint"
CATEGORY_TASK = "task"
CATEGORY_TASK_DONE = "task_done"
CATEGORY_DECISION = "decision"
CATEGORY_AUTOMATION = "automation"
CATEGORY_PROFILE = "profile"
CATEGORY_PREFERENCE = "preference"
CATEGORY_RELATIONSHIP = "relationship"
CATEGORY_ONGOING = "ongoing"
CATEGORY_EPISODE = "episode"
CATEGORY_BELIEF_DECISION = "belief_decision"
CATEGORY_CODE_REFERENCE = "code_reference"
CATEGORY_NOTE = "note"

LATEST_TURN_SUMMARY_PROPERTY = "latest-turn-summary"
SUMMARY_HISTORY_PREFIX = "turn-summary."
LATEST_CHECKPOINT_PROPERTY = "PreCompact"
CHECKPOINT_HISTORY_PREFIX = "PreCompact."

ALLOWED_CATEGORIES = {
    CATEGORY_FACT,
    CATEGORY_SUMMARY,
    CATEGORY_CHECKPOINT,
    CATEGORY_TASK,
    CATEGORY_TASK_DONE,
    CATEGORY_DECISION,
    CATEGORY_AUTOMATION,
    CATEGORY_PROFILE,
    CATEGORY_PREFERENCE,
    CATEGORY_RELATIONSHIP,
    CATEGORY_ONGOING,
    CATEGORY_EPISODE,
    CATEGORY_BELIEF_DECISION,
    CATEGORY_CODE_REFERENCE,
    CATEGORY_NOTE,
}

PERSONAL_MEMORY_CATEGORIES = {
    CATEGORY_PROFILE,
    CATEGORY_PREFERENCE,
    CATEGORY_RELATIONSHIP,
    CATEGORY_ONGOING,
    CATEGORY_EPISODE,
    CATEGORY_BELIEF_DECISION,
}

PERSONAL_MEMORY_ENTITY_PREFIX = {
    CATEGORY_PROFILE: "Personal.Profile",
    CATEGORY_PREFERENCE: "Personal.Preference",
    CATEGORY_RELATIONSHIP: "Personal.Relationship",
    CATEGORY_ONGOING: "Personal.Ongoing",
    CATEGORY_EPISODE: "Personal.Episode",
    CATEGORY_BELIEF_DECISION: "Personal.BeliefDecision",
}


def plugin_home():
    configured = os.environ.get("CP_MEMORY_PLUGIN_HOME")
    if configured:
        return Path(configured)
    return Path(os.path.expanduser("~")) / "plugins" / "cp-memory"


def memory_home():
    configured = os.environ.get("CP_MEMORY_HOME")
    if configured:
        return Path(configured)
    return Path(os.path.expanduser("~")) / ".cp-memory"


def old_memory_home():
    configured = os.environ.get("CP_MEMORY_OLD_HOME")
    if configured:
        return Path(configured)
    return Path(os.path.expanduser("~")) / ".codex-memory"


def db_path():
    configured = os.environ.get("CP_MEMORY_DB_PATH")
    if configured:
        return Path(configured)
    return memory_home() / "memory.db"


def old_db_path():
    return old_memory_home() / "memory.db"


def migration_marker_path():
    return memory_home() / ".migrated-from-codex-memory"


def timezone_marker_path():
    return memory_home() / TIMEZONE_MIGRATION_MARKER_NAME


def fts_marker_path():
    return memory_home() / FTS_READY_MARKER_NAME


def semantic_upgrade_marker_path():
    return memory_home() / SEMANTIC_UPGRADE_MARKER_NAME


def decision_mirror_marker_path():
    return memory_home() / DECISION_MIRROR_MARKER_NAME


def now_local():
    return datetime.datetime.now(LOCAL_TZ).strftime(TIME_FORMAT)


def add_days_local(days):
    return (datetime.datetime.now(LOCAL_TZ) + datetime.timedelta(days=int(days))).strftime(TIME_FORMAT)


def new_id(prefix=""):
    return prefix + str(uuid.uuid4())[:8]


def unique_property(prefix):
    return f"{prefix}{new_id('evt_')}"


def parse_keywords(query):
    return [k.strip() for k in re.split(r"[\s,，、]+", query or "") if k.strip()]


def codex_memory_base():
    return Path(os.path.expanduser("~")) / ".codex" / "memories"


def normalize_limit(limit, default=20, maximum=200):
    try:
        parsed = int(limit)
    except Exception:
        parsed = default
    return max(1, min(parsed, maximum))


def normalize_category(category, entity="", prop="", tags="", source=""):
    raw = (category or "").strip().lower()
    raw = raw.replace("-", "_")
    aliases = {
        "beliefdecision": CATEGORY_BELIEF_DECISION,
        "belief_decision": CATEGORY_BELIEF_DECISION,
        "belief": CATEGORY_BELIEF_DECISION,
        "decision_belief": CATEGORY_BELIEF_DECISION,
        "ongoing_item": CATEGORY_ONGOING,
        "current_state": CATEGORY_ONGOING,
        "personal_event": CATEGORY_EPISODE,
        "event": CATEGORY_EPISODE,
    }
    raw = aliases.get(raw, raw)
    if raw in ALLOWED_CATEGORIES:
        return raw

    text = " ".join(filter(None, [entity, prop, tags, source])).lower()
    if entity.startswith("Personal.Profile") or "profile" in text:
        return CATEGORY_PROFILE
    if entity.startswith("Personal.Preference") or "preference" in text or "偏好" in text or "喜欢" in text or "不喜欢" in text:
        return CATEGORY_PREFERENCE
    if entity.startswith("Personal.Relationship") or "relationship" in text or "关系" in text:
        return CATEGORY_RELATIONSHIP
    if entity.startswith("Personal.Ongoing") or "ongoing" in text or "持续" in text or "未完成" in text:
        return CATEGORY_ONGOING
    if entity.startswith("Personal.Episode") or "episode" in text or "事件" in text:
        return CATEGORY_EPISODE
    if entity.startswith("Personal.BeliefDecision") or "belief" in text or "belief_decision" in text or "立场" in text:
        return CATEGORY_BELIEF_DECISION
    if "precompact" in text or "checkpoint" in text or "compaction" in text:
        return CATEGORY_CHECKPOINT
    if "summary" in text or "stop-hook" in text:
        return CATEGORY_SUMMARY
    if entity == "__current_task":
        return CATEGORY_TASK
    if entity == "Decision":
        return CATEGORY_DECISION
    if "automation" in text:
        return CATEGORY_AUTOMATION
    if "display_name" in text or "identity" in text:
        return CATEGORY_PROFILE
    return CATEGORY_FACT


def parse_timestamp(value):
    text = (value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(LOCAL_TZ)
    except ValueError:
        pass
    for fmt in (TIME_FORMAT, "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.datetime.strptime(text, fmt).replace(tzinfo=datetime.timezone.utc)
            return parsed.astimezone(LOCAL_TZ)
        except ValueError:
            continue
    return None


def normalize_timestamp_text(value):
    parsed = parse_timestamp(value)
    return parsed.strftime(TIME_FORMAT) if parsed else value


def payload_checksum(content):
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def payload_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, sort_keys=True)


def payload_preview(content, limit=800):
    text = payload_text(content).replace("\r", " ").replace("\n", " ")
    return text[:limit]


def clean_text(value):
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def classify_importance(value, tags="", category=CATEGORY_FACT):
    text = f"{value or ''} {tags or ''} {category or ''}"
    if category in {CATEGORY_DECISION, CATEGORY_BELIEF_DECISION, CATEGORY_PROFILE, CATEGORY_PREFERENCE} or any(k in text for k in ("决定", "约定", "必须", "偏好", "架构", "规则")):
        return 5
    if category in {CATEGORY_SUMMARY, CATEGORY_CHECKPOINT, CATEGORY_TASK, CATEGORY_RELATIONSHIP, CATEGORY_ONGOING}:
        return 4
    if any(k in text for k in ("实现", "修复", "方案", "问题", "原因", "CP Memory", "hook", "插件", "数据库")):
        return 4
    return 3


def expiry_for_importance(importance):
    if importance >= 5:
        return ""
    days = 180 if importance == 4 else 45
    return (datetime.datetime.now(LOCAL_TZ) + datetime.timedelta(days=days)).strftime(TIME_FORMAT)


def resolve_paths():
    home = memory_home()
    return {
        "memory_dir": home,
        "db_path": db_path(),
        "old_db_path": old_db_path(),
        "migration_marker": migration_marker_path(),
        "timezone_marker": timezone_marker_path(),
        "fts_marker": fts_marker_path(),
    }


def migrate_old_db_if_needed():
    paths = resolve_paths()
    paths["memory_dir"].mkdir(parents=True, exist_ok=True)
    if paths["db_path"].exists() or not paths["old_db_path"].exists():
        return False
    shutil.copy2(paths["old_db_path"], paths["db_path"])
    paths["migration_marker"].write_text(
        f"migrated_from={paths['old_db_path']}\nmigrated_at={now_local()}\n",
        encoding="utf-8",
    )
    return True


def get_db():
    migrate_old_db_if_needed()
    conn = sqlite3.connect(str(db_path()), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn=None):
    owns_conn = conn is None
    conn = conn or get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS facts (
            id          TEXT PRIMARY KEY,
            entity      TEXT NOT NULL,
            property    TEXT NOT NULL,
            value       TEXT NOT NULL,
            confidence  TEXT DEFAULT 'high',
            tags        TEXT DEFAULT '',
            category    TEXT DEFAULT 'fact',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS decisions (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            context     TEXT DEFAULT '',
            decision    TEXT NOT NULL,
            rationale   TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS workflows (
            name        TEXT PRIMARY KEY,
            steps       TEXT NOT NULL,
            category    TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS aliases (
            alias       TEXT PRIMARY KEY,
            entity      TEXT NOT NULL,
            tags        TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_meta (
            fact_id          TEXT PRIMARY KEY,
            importance       INTEGER DEFAULT 3,
            expires_at       TEXT DEFAULT '',
            access_count     INTEGER DEFAULT 0,
            last_accessed_at TEXT DEFAULT '',
            pinned           INTEGER DEFAULT 0,
            source           TEXT DEFAULT '',
            summary_type     TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS memory_payloads (
            fact_id       TEXT PRIMARY KEY,
            content       TEXT NOT NULL,
            content_type  TEXT DEFAULT 'text/plain',
            checksum      TEXT DEFAULT '',
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_links (
            id            TEXT PRIMARY KEY,
            source_kind   TEXT NOT NULL,
            source_id     TEXT NOT NULL,
            target_kind   TEXT NOT NULL,
            target_id     TEXT NOT NULL,
            relation      TEXT NOT NULL,
            created_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_audit_log (
            id              TEXT PRIMARY KEY,
            fact_id         TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            source          TEXT DEFAULT '',
            previous_value  TEXT DEFAULT '',
            new_value       TEXT DEFAULT '',
            reason          TEXT DEFAULT '',
            related_fact_id TEXT DEFAULT '',
            payload         TEXT DEFAULT '',
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_facts_entity_property ON facts(entity, property);
        CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
        CREATE INDEX IF NOT EXISTS idx_aliases_entity ON aliases(entity);
        CREATE INDEX IF NOT EXISTS idx_meta_importance ON memory_meta(importance);
        CREATE INDEX IF NOT EXISTS idx_meta_expires_at ON memory_meta(expires_at);
        CREATE INDEX IF NOT EXISTS idx_links_source ON memory_links(source_kind, source_id);
        CREATE INDEX IF NOT EXISTS idx_links_target ON memory_links(target_kind, target_id);
        CREATE INDEX IF NOT EXISTS idx_payloads_checksum ON memory_payloads(checksum);
        CREATE INDEX IF NOT EXISTS idx_audit_fact_time ON memory_audit_log(fact_id, created_at);
        """
    )
    ensure_table_column(conn, "memory_meta", "quality_score", "INTEGER DEFAULT 50")
    ensure_table_column(conn, "memory_meta", "noise_score", "INTEGER DEFAULT 0")
    ensure_table_column(conn, "memory_meta", "canonical_category", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "last_reviewed_at", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "stability_score", "INTEGER DEFAULT 50")
    ensure_table_column(conn, "memory_meta", "evidence_count", "INTEGER DEFAULT 1")
    ensure_table_column(conn, "memory_meta", "correction_status", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "corrected_at", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "valid_from", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "valid_until", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "scope", "TEXT DEFAULT ''")
    ensure_table_column(conn, "memory_meta", "sensitivity", "TEXT DEFAULT 'normal'")
    ensure_table_column(conn, "decisions", "updated_at", "TEXT DEFAULT ''")
    ensure_table_column(conn, "decisions", "source", "TEXT DEFAULT ''")
    ensure_table_column(conn, "decisions", "status", "TEXT DEFAULT 'active'")
    ensure_table_column(conn, "decisions", "review_state", "TEXT DEFAULT 'confirmed'")
    ensure_table_column(conn, "decisions", "confidence", "TEXT DEFAULT 'high'")
    create_fts_objects(conn)
    migrate_timestamps_to_localtime(conn)
    migrate_legacy_semantics(conn)
    repair_decision_mirrors(conn)
    ensure_fulltext_populated(conn)
    conn.commit()
    if owns_conn:
        conn.close()


def ensure_table_column(conn, table_name, column_name, column_definition):
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def create_fts_objects(conn):
    try:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
                fact_id UNINDEXED,
                entity,
                property,
                value,
                tags,
                category,
                payload
            );
            """
        )
    except sqlite3.OperationalError:
        pass


def ensure_fulltext_populated(conn):
    try:
        conn.execute("SELECT 1 FROM facts_fts LIMIT 1")
    except sqlite3.OperationalError:
        return

    facts_count = conn.execute("SELECT COUNT(*) AS cnt FROM facts").fetchone()["cnt"]
    fts_count = conn.execute("SELECT COUNT(*) AS cnt FROM facts_fts").fetchone()["cnt"]
    if fts_count == facts_count and fts_marker_path().exists():
        return

    conn.execute("DELETE FROM facts_fts")
    rows = conn.execute(
        """
        SELECT f.id, f.entity, f.property, f.value, f.tags, f.category, COALESCE(p.content, '') AS payload
        FROM facts f
        LEFT JOIN memory_payloads p ON p.fact_id = f.id
        """
    ).fetchall()
    for row in rows:
        conn.execute(
            "INSERT INTO facts_fts (fact_id, entity, property, value, tags, category, payload) VALUES (?,?,?,?,?,?,?)",
            (
                row["id"],
                row["entity"],
                row["property"],
                row["value"],
                row["tags"],
                row["category"],
                row["payload"],
            ),
        )
    fts_marker_path().write_text(f"rebuilt_at={now_local()}\ncount={facts_count}\n", encoding="utf-8")


def migrate_timestamps_to_localtime(conn):
    if timezone_marker_path().exists():
        return

    timestamp_columns = {
        "facts": ("created_at", "updated_at"),
        "decisions": ("created_at",),
        "workflows": ("created_at", "updated_at"),
        "aliases": ("created_at", "updated_at"),
        "memory_meta": ("expires_at", "last_accessed_at"),
        "memory_payloads": ("created_at", "updated_at"),
        "memory_links": ("created_at",),
        "memory_audit_log": ("created_at",),
    }

    for table, columns in timestamp_columns.items():
        select_sql = f"SELECT rowid, {', '.join(columns)} FROM {table}"
        for row in conn.execute(select_sql).fetchall():
            assignments = []
            values = []
            for column in columns:
                raw_value = row[column]
                converted = normalize_timestamp_text(raw_value)
                if converted != raw_value:
                    assignments.append(f"{column} = ?")
                    values.append(converted)
            if assignments:
                values.append(row["rowid"])
                conn.execute(f"UPDATE {table} SET {', '.join(assignments)} WHERE rowid = ?", values)

    timezone_marker_path().write_text(
        f"timezone=Asia/Shanghai\nmigrated_at={now_local()}\n",
        encoding="utf-8",
    )


def upsert_meta(conn, fact_id, importance, expires_at="", source="", summary_type=""):
    quality_score = 50
    noise_score = 0
    canonical_category = ""
    reviewed_at = ""
    stability_score = 50
    evidence_count = 1
    correction_status = ""
    corrected_at = ""
    valid_from = ""
    valid_until = ""
    scope = ""
    sensitivity = "normal"
    existing = conn.execute(
        "SELECT quality_score, noise_score, canonical_category, last_reviewed_at, stability_score, evidence_count, correction_status, corrected_at, valid_from, valid_until, scope, sensitivity FROM memory_meta WHERE fact_id=?",
        (fact_id,),
    ).fetchone()
    if existing:
        quality_score = existing["quality_score"] or quality_score
        noise_score = existing["noise_score"] or noise_score
        canonical_category = existing["canonical_category"] or canonical_category
        reviewed_at = existing["last_reviewed_at"] or reviewed_at
        stability_score = existing["stability_score"] or stability_score
        evidence_count = existing["evidence_count"] or evidence_count
        correction_status = existing["correction_status"] or correction_status
        corrected_at = existing["corrected_at"] or corrected_at
        valid_from = existing["valid_from"] or valid_from
        valid_until = existing["valid_until"] or valid_until
        scope = existing["scope"] or scope
        sensitivity = existing["sensitivity"] or sensitivity
    conn.execute(
        "INSERT OR REPLACE INTO memory_meta "
        "(fact_id, importance, expires_at, access_count, last_accessed_at, pinned, source, summary_type, quality_score, noise_score, canonical_category, last_reviewed_at, stability_score, evidence_count, correction_status, corrected_at, valid_from, valid_until, scope, sensitivity) "
        "VALUES (?, ?, ?, COALESCE((SELECT access_count FROM memory_meta WHERE fact_id=?), 0), "
        "COALESCE((SELECT last_accessed_at FROM memory_meta WHERE fact_id=?), ''), "
        "COALESCE((SELECT pinned FROM memory_meta WHERE fact_id=?), 0), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            fact_id,
            importance,
            expires_at,
            fact_id,
            fact_id,
            fact_id,
            source,
            summary_type,
            quality_score,
            noise_score,
            canonical_category,
            reviewed_at,
            stability_score,
            evidence_count,
            correction_status,
            corrected_at,
            valid_from,
            valid_until,
            scope,
            sensitivity,
        ),
    )


def resolve_entity(conn, entity):
    name = clean_text(entity)
    if not name:
        return name
    row = conn.execute("SELECT entity FROM aliases WHERE alias = ?", (name,)).fetchone()
    return row["entity"] if row else name


def upsert_fact(
    conn,
    entity,
    prop,
    value,
    confidence="high",
    tags="",
    category=CATEGORY_FACT,
    importance=None,
    expires_at="",
    source="",
    summary_type="",
    payload=None,
    content_type="text/plain",
):
    ts = now_local()
    clean_entity = resolve_entity(conn, entity)
    clean_property = clean_text(prop)
    clean_value = clean_text(value)
    clean_confidence = clean_text(confidence or "high") or "high"
    clean_tags = clean_text(tags)
    normalized_category = normalize_category(category, clean_entity, clean_property, clean_tags, source)
    importance_value = importance if importance is not None else classify_importance(clean_value, clean_tags, normalized_category)
    expiry_value = expires_at if expires_at is not None else expiry_for_importance(importance_value)
    row = conn.execute(
        "SELECT id, created_at FROM facts WHERE entity=? AND property=? ORDER BY updated_at DESC LIMIT 1",
        (clean_entity, clean_property),
    ).fetchone()
    if row:
        rid = row["id"]
        conn.execute(
            "UPDATE facts SET value=?, confidence=?, tags=?, category=?, updated_at=? WHERE id=?",
            (clean_value, clean_confidence, clean_tags, normalized_category, ts, rid),
        )
        action = "updated"
    else:
        rid = new_id()
        conn.execute(
            "INSERT INTO facts (id, entity, property, value, confidence, tags, category, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (rid, clean_entity, clean_property, clean_value, clean_confidence, clean_tags, normalized_category, ts, ts),
        )
        action = "created"
    upsert_meta(conn, rid, importance_value, expiry_value, source=source, summary_type=summary_type)
    if payload is not None:
        upsert_payload(conn, rid, payload, content_type=content_type)
    auto_link_neighbors(conn, rid, clean_entity, clean_property, normalized_category)
    sync_fulltext_row(conn, rid)
    return rid, action


def upsert_decision_record(
    conn,
    title,
    context,
    decision,
    rationale="",
    source="memory_decision_add",
    status="active",
    review_state="confirmed",
    confidence="high",
    payload=None,
):
    clean_title = clean_text(title)
    clean_context = clean_text(context)
    clean_decision = clean_text(decision)
    clean_rationale = clean_text(rationale)
    clean_source = clean_text(source)
    clean_status = clean_text(status) or "active"
    clean_review_state = clean_text(review_state) or "confirmed"
    clean_confidence = clean_text(confidence) or "high"
    if not clean_title or not clean_decision:
        raise ValueError("decision title and decision text are required")
    existing_decision = conn.execute("SELECT id FROM decisions WHERE title=?", (clean_title,)).fetchone()
    existing_fact = conn.execute("SELECT id FROM facts WHERE entity='Decision' AND property=?", (clean_title,)).fetchone()
    existing = existing_decision or existing_fact
    rid = existing["id"] if existing else new_id()
    ts = now_local()
    if existing_decision:
        conn.execute(
            "UPDATE decisions SET context=?, decision=?, rationale=?, updated_at=?, source=?, status=?, review_state=?, confidence=? WHERE id=?",
            (clean_context, clean_decision, clean_rationale, ts, clean_source, clean_status, clean_review_state, clean_confidence, rid),
        )
    else:
        conn.execute(
            "INSERT INTO decisions (id, title, context, decision, rationale, created_at, updated_at, source, status, review_state, confidence) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (rid, clean_title, clean_context, clean_decision, clean_rationale, ts, ts, clean_source, clean_status, clean_review_state, clean_confidence),
        )
    structured_payload = {
        "title": clean_title,
        "context": clean_context,
        "decision": clean_decision,
        "rationale": clean_rationale,
        "source": clean_source,
        "status": clean_status,
        "review_state": clean_review_state,
        "confidence": clean_confidence,
    }
    if payload is not None:
        structured_payload["payload"] = payload
    fact_id, action = upsert_fact(
        conn,
        "Decision",
        clean_title,
        clean_decision,
        confidence=clean_confidence,
        tags="decision",
        category=CATEGORY_DECISION,
        importance=5,
        expires_at="",
        source=clean_source,
        summary_type="decision",
        payload=structured_payload,
        content_type="application/json",
    )
    link_records(conn, "decision", rid, "mirrors", "fact", fact_id)
    conn.execute(
        "UPDATE memory_meta SET correction_status=?, last_reviewed_at=? WHERE fact_id=?",
        ("confirmed" if clean_review_state == "confirmed" else "", ts, fact_id),
    )
    return rid, action


def normalize_personal_memory_type(memory_type):
    return normalize_category(memory_type)


def personal_memory_entity(memory_type, subject):
    category = normalize_personal_memory_type(memory_type)
    prefix = PERSONAL_MEMORY_ENTITY_PREFIX.get(category, "Personal.Memory")
    clean_subject = clean_text(subject) or "default"
    return f"{prefix}.{clean_subject}"


def stability_for_category(category, value):
    text = clean_text(value)
    if category in {CATEGORY_PROFILE, CATEGORY_BELIEF_DECISION}:
        return 85
    if category == CATEGORY_PREFERENCE:
        return 75
    if category == CATEGORY_RELATIONSHIP:
        return 70
    if category == CATEGORY_ONGOING:
        return 55
    if category == CATEGORY_EPISODE:
        return 45
    return 50


def upsert_personal_memory(
    conn,
    memory_type,
    subject,
    key,
    value,
    details="",
    confidence="high",
    tags="",
    source="personal-memory",
    evidence_count=1,
    stability_score=None,
    valid_from="",
    valid_until="",
    scope="",
    sensitivity="normal",
    payload=None,
):
    category = normalize_personal_memory_type(memory_type)
    if category not in PERSONAL_MEMORY_CATEGORIES:
        raise ValueError(f"unsupported personal memory type: {memory_type}")
    clean_key = clean_text(key) or category
    clean_value = clean_text(value)
    clean_subject = clean_text(subject) or "default"
    merged_tags = ",".join(item for item in [clean_text(tags), "personal-assistant", category] if item)
    existing_row = conn.execute(
        """
        SELECT f.id, f.value,
               COALESCE(m.evidence_count, 1) AS evidence_count,
               COALESCE(m.valid_until, '') AS valid_until,
               COALESCE(m.scope, '') AS scope
        FROM facts f
        LEFT JOIN memory_meta m ON m.fact_id = f.id
        WHERE f.entity=? AND f.property=?
        ORDER BY f.updated_at DESC
        LIMIT 1
        """,
        (personal_memory_entity(category, clean_subject), clean_key),
    ).fetchone()
    clean_valid_until = clean_text(valid_until)
    if category == CATEGORY_ONGOING and not clean_valid_until:
        if clean_text(source).startswith("stop-hook-auto"):
            clean_valid_until = add_days_local(21)
        elif existing_row and clean_text(existing_row["valid_until"]):
            clean_valid_until = clean_text(existing_row["valid_until"])
    clean_scope = clean_text(scope) or (clean_text(existing_row["scope"]) if existing_row else "")
    structured_payload = {
        "memory_type": category,
        "subject": clean_subject,
        "key": clean_key,
        "value": clean_value,
        "details": clean_text(details),
        "evidence_count": max(1, int(evidence_count or 1)),
        "valid_from": clean_text(valid_from),
        "valid_until": clean_valid_until,
        "scope": clean_scope,
        "sensitivity": clean_text(sensitivity) or "normal",
        "source": source,
    }
    if payload is not None:
        structured_payload["payload"] = payload
    rid, action = upsert_fact(
        conn,
        personal_memory_entity(category, clean_subject),
        clean_key,
        clean_value,
        confidence=confidence,
        tags=merged_tags,
        category=category,
        importance=classify_importance(clean_value, merged_tags, category),
        expires_at="",
        source=source,
        summary_type=category,
        payload=structured_payload,
        content_type="application/json",
    )
    stability = stability_score if stability_score is not None else stability_for_category(category, clean_value)
    merged_evidence_count = max(1, int(evidence_count or 1))
    if existing_row:
        merged_evidence_count = max(merged_evidence_count, int(existing_row["evidence_count"] or 1))
        if clean_text(source).startswith("stop-hook-auto") and clean_value == clean_text(existing_row["value"]):
            merged_evidence_count = int(existing_row["evidence_count"] or 1) + max(1, int(evidence_count or 1))
    if category == CATEGORY_ONGOING and existing_row and clean_value == clean_text(existing_row["value"]):
        existing_valid_until = clean_text(existing_row["valid_until"])
        if existing_valid_until and (not clean_valid_until or existing_valid_until > clean_valid_until):
            clean_valid_until = existing_valid_until
        if clean_text(source).startswith("stop-hook-auto"):
            extended_valid_until = add_days_local(21)
            if not clean_valid_until or extended_valid_until > clean_valid_until:
                clean_valid_until = extended_valid_until
    conn.execute(
        "UPDATE memory_meta SET stability_score=?, evidence_count=?, canonical_category=?, last_reviewed_at=?, valid_from=?, valid_until=?, scope=?, sensitivity=? WHERE fact_id=?",
        (
            max(0, min(100, int(stability))),
            merged_evidence_count,
            category,
            now_local(),
            clean_text(valid_from),
            clean_valid_until,
            clean_scope,
            clean_text(sensitivity) or "normal",
            rid,
        ),
    )
    return rid, action, category


def derive_personal_from_episode(conn, episode_id, memory_type, subject, key, value, details="", confidence="high", tags="", evidence_count=1, stability_score=None):
    episode = conn.execute("SELECT id, category FROM facts WHERE id=?", (clean_text(episode_id),)).fetchone()
    if not episode:
        return None
    rid, action, category = upsert_personal_memory(
        conn,
        memory_type,
        subject,
        key,
        value,
        details=details,
        confidence=confidence,
        tags=tags,
        source="derive_personal_from_episode",
        evidence_count=evidence_count,
        stability_score=stability_score,
        payload={"derived_from_episode": episode_id},
    )
    link_records(conn, "fact", rid, "derived_from_episode", "fact", episode_id)
    if category == CATEGORY_BELIEF_DECISION:
        link_records(conn, "fact", rid, "supports_belief", "fact", episode_id)
    return rid, action, category


def slugify_key(text, fallback="memory"):
    cleaned = clean_text(text).lower()
    tokens = re.findall(r"[a-z0-9]+", cleaned)
    if tokens:
        return "_".join(tokens[:6])
    if "偏好" in cleaned or "喜欢" in cleaned or "不喜欢" in cleaned:
        return "preference"
    if "目标" in cleaned or "推进" in cleaned or "正在" in cleaned:
        return "ongoing_goal"
    if "方向" in cleaned or "原则" in cleaned or "立场" in cleaned or "不做" in cleaned:
        return "belief_direction"
    return fallback


def suggest_personal_derivations_from_episode(conn, episode_id, subject="user", limit=5):
    row = conn.execute(
        """
        SELECT f.id, f.value, COALESCE(p.content, '') AS payload
        FROM facts f
        LEFT JOIN memory_payloads p ON p.fact_id = f.id
        WHERE f.id=? AND f.category=?
        """,
        (clean_text(episode_id), CATEGORY_EPISODE),
    ).fetchone()
    if not row:
        return []
    text = " ".join([clean_text(row["value"]), clean_text(row["payload"])])
    candidates = []
    rules = [
        (
            CATEGORY_PREFERENCE,
            "communication_or_preference",
            ("喜欢", "不喜欢", "偏好", "习惯", "希望", "倾向"),
            74,
        ),
        (
            CATEGORY_ONGOING,
            "ongoing_goal",
            ("正在", "继续", "目标", "计划", "推进", "未完成"),
            58,
        ),
        (
            CATEGORY_RELATIONSHIP,
            "relationship",
            ("关系", "当作", "关于", "相关", "属于"),
            68,
        ),
        (
            CATEGORY_BELIEF_DECISION,
            "belief_direction",
            ("决定", "原则", "方向", "立场", "不做", "必须", "应该"),
            82,
        ),
        (
            CATEGORY_PROFILE,
            "profile",
            ("我是", "我叫", "昵称", "时区", "语言"),
            84,
        ),
    ]
    for category, fallback_key, terms, stability in rules:
        if any(term in text for term in terms):
            candidates.append(
                {
                    "memory_type": category,
                    "subject": clean_text(subject) or "user",
                    "key": slugify_key(text, fallback=fallback_key),
                    "value": clean_text(row["value"]),
                    "details": f"Derived from episode {episode_id}",
                    "evidence_count": 1,
                    "stability_score": stability,
                }
            )
        if len(candidates) >= limit:
            break
    return candidates


def consolidate_episode(conn, episode_id, subject="user", dry_run=True, limit=5):
    candidates = suggest_personal_derivations_from_episode(conn, episode_id, subject=subject, limit=limit)
    if dry_run:
        return {"episode_id": episode_id, "dry_run": True, "candidates": candidates, "created": []}
    created = []
    for candidate in candidates:
        result = derive_personal_from_episode(
            conn,
            episode_id,
            candidate["memory_type"],
            candidate["subject"],
            candidate["key"],
            candidate["value"],
            details=candidate["details"],
            evidence_count=candidate["evidence_count"],
            stability_score=candidate["stability_score"],
        )
        if result:
            rid, action, category = result
            created.append({"id": rid, "action": action, "category": category, "key": candidate["key"]})
    return {"episode_id": episode_id, "dry_run": False, "candidates": candidates, "created": created}


def correct_memory(conn, fact_id, status, reason="", value=""):
    allowed = {"corrected", "stale", "wrong", "scoped", "confirmed"}
    clean_status = clean_text(status).lower().replace("-", "_")
    if clean_status not in allowed:
        raise ValueError(f"unsupported correction status: {status}")
    row = conn.execute("SELECT id, entity, property, value, confidence, tags, category FROM facts WHERE id=?", (clean_text(fact_id),)).fetchone()
    if not row:
        return None
    if clean_text(value):
        upsert_fact(
            conn,
            row["entity"],
            row["property"],
            clean_text(value),
            confidence=row["confidence"],
            tags=row["tags"],
            category=row["category"],
            source="memory_correct",
            payload={"previous_value": row["value"], "new_value": clean_text(value), "reason": clean_text(reason), "status": clean_status},
            content_type="application/json",
        )
    conn.execute(
        "UPDATE memory_meta SET correction_status=?, corrected_at=?, last_reviewed_at=? WHERE fact_id=?",
        (clean_status, now_local(), now_local(), row["id"]),
    )
    append_audit_event(
        conn,
        row["id"],
        "memory_corrected",
        source="memory_correct",
        previous_value=row["value"],
        new_value=clean_text(value) or row["value"],
        reason=clean_text(reason),
        payload={"status": clean_status},
    )
    if clean_text(reason):
        upsert_payload(
            conn,
            row["id"],
            {"reason": clean_text(reason), "status": clean_status, "current_value": clean_text(value) or row["value"]},
            content_type="application/json",
        )
    review_fact(conn, row["id"], category=row["category"], source="memory_correct")
    return row["id"]


def normalize_id_list(values):
    if isinstance(values, str):
        items = re.split(r"[,，、\s]+", values)
    elif isinstance(values, (list, tuple, set)):
        items = list(values)
    else:
        items = []
    cleaned = []
    seen = set()
    for item in items:
        text = clean_text(item)
        if text and text not in seen:
            cleaned.append(text)
            seen.add(text)
    return cleaned


def personal_subject_from_entity(entity):
    text = clean_text(entity)
    for prefix in PERSONAL_MEMORY_ENTITY_PREFIX.values():
        marker = f"{prefix}."
        if text.startswith(marker):
            return text[len(marker):]
    return ""


def has_opposition(values):
    joined = "\n".join(clean_text(value) for value in values)
    pairs = [
        ("喜欢", "不喜欢"),
        ("想", "不想"),
        ("要", "不要"),
        ("需要", "不需要"),
        ("应该", "不应该"),
        ("平台化", "不是大平台"),
        ("编码助手", "不限定编程"),
        ("只", "不只是"),
    ]
    return any(left in joined and right in joined for left, right in pairs)


def active_memory_row(row, now_text=""):
    status = clean_text(row.get("correction_status") if isinstance(row, dict) else row["correction_status"]).lower()
    if status in {"wrong", "stale"}:
        return False
    return True


def detect_memory_scope(text):
    cleaned = clean_text(text)
    lowered = cleaned.lower()
    if not cleaned:
        return ""
    if "cjhuochai/cp-memory" in lowered:
        return "repo:CJhuochai/cp-memory"
    if "cp memory" in lowered or "cp-memory" in lowered:
        return "project:cp-memory"
    if "basisproject" in lowered or "e:\\basisproject" in lowered:
        return "workspace:E:\\BasisProject"
    repo_match = re.search(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b", cleaned)
    if repo_match:
        return f"repo:{repo_match.group(1)}"
    return ""


def prompt_scopes(prompt):
    scope = detect_memory_scope(prompt)
    scopes = []
    if scope:
        scopes.append(scope)
        if scope == "repo:CJhuochai/cp-memory":
            scopes.append("project:cp-memory")
    return scopes


def scope_rank(row_scope, active_scopes=None):
    scope = clean_text(row_scope)
    if not scope:
        return 1
    if active_scopes and scope in active_scopes:
        return 3
    if scope == "global":
        return 2
    return 0


def restorable_memory_row(row, now_text=""):
    if not active_memory_row(row, now_text=now_text):
        return False
    valid_until = clean_text(row.get("valid_until") if isinstance(row, dict) else row["valid_until"])
    if valid_until and valid_until < (now_text or now_local()):
        return False
    return True


def personal_resolution_candidates(conflicts, limit=10):
    suggestions = []
    for item in conflicts:
        if item.get("type") not in {"personal_duplicate_key", "personal_possible_contradiction"}:
            continue
        entries = [dict(entry) for entry in item.get("items", [])]
        if len(entries) < 2:
            continue
        ranked = sorted(
            entries,
            key=lambda row: (
                clean_text(row.get("correction_status", "")) == "confirmed",
                int(row.get("stability_score") or 50),
                int(row.get("evidence_count") or 1),
                clean_text(row.get("updated_at", "")),
            ),
            reverse=True,
        )
        winner = ranked[0]
        losers = ranked[1:]
        recommended_action = "merge"
        reason_bits = []
        if item.get("type") == "personal_possible_contradiction":
            recommended_action = "resolve_contradiction"
            reason_bits.append("同一 subject/key 出现了相反表述")
        else:
            reason_bits.append("同一 subject/key 出现了重复候选")
        if clean_text(winner.get("correction_status", "")) == "confirmed":
            reason_bits.append("当前胜出项已被确认")
        if int(winner.get("evidence_count") or 1) > 1:
            reason_bits.append(f"胜出项证据数更高({winner['evidence_count']})")
        if int(winner.get("stability_score") or 50) >= 70:
            reason_bits.append(f"胜出项稳定性更高({winner['stability_score']})")
        suggestions.append(
            {
                "type": item.get("type"),
                "subject": item.get("subject", ""),
                "property": item.get("property", ""),
                "winner_suggestion": winner,
                "loser_ids": [entry["id"] for entry in losers],
                "recommended_action": recommended_action,
                "reason_summary": "；".join(reason_bits) or "建议确认一个最终版本并合并其余候选",
                "review_after_resolve": "调用 memory_personal_resolve 后，应在 review/conflicts 中不再看到此开放冲突，但仍能在 inspect 里看到 supersedes 关系链。",
            }
        )
        if len(suggestions) >= limit:
            break
    return suggestions


def personal_memory_conflicts(conn, limit=50):
    limit = normalize_limit(limit, default=50, maximum=200)
    rows = conn.execute(
        """
        SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at,
               COALESCE(m.evidence_count, 1) AS evidence_count,
               COALESCE(m.stability_score, 50) AS stability_score,
               COALESCE(m.valid_until, '') AS valid_until,
               COALESCE(m.correction_status, '') AS correction_status
        FROM facts f
        LEFT JOIN memory_meta m ON m.fact_id = f.id
        WHERE f.category IN (?, ?, ?, ?, ?, ?)
        ORDER BY f.updated_at DESC
        LIMIT ?
        """,
        [*sorted(PERSONAL_MEMORY_CATEGORIES), limit * 5],
    ).fetchall()
    now_text = now_local()
    active_rows = [dict(row) for row in rows if active_memory_row(dict(row), now_text=now_text)]
    conflicts = []
    grouped = {}
    for row in active_rows:
        subject = personal_subject_from_entity(row["entity"]) or row["entity"]
        key = (subject, row["property"])
        grouped.setdefault(key, []).append(row)

    for (subject, prop), items in grouped.items():
        if len(items) > 1:
            categories = sorted({item["category"] for item in items})
            conflict_type = "personal_duplicate_key"
            if has_opposition([item["value"] for item in items]):
                conflict_type = "personal_possible_contradiction"
            conflicts.append(
                {
                    "type": conflict_type,
                    "subject": subject,
                    "property": prop,
                    "categories": categories,
                    "count": len(items),
                    "items": items,
                }
            )

    for row in active_rows:
        if row["category"] == CATEGORY_ONGOING and row["valid_until"] and row["valid_until"] < now_text:
            conflicts.append({"type": "personal_expired_ongoing", "item": row})
        if row["category"] == CATEGORY_BELIEF_DECISION and row["evidence_count"] <= 1 and row["stability_score"] < 70:
            conflicts.append({"type": "personal_low_evidence_belief", "item": row})
        if row["category"] == CATEGORY_PREFERENCE and row["evidence_count"] <= 1 and row["stability_score"] < 60:
            conflicts.append({"type": "personal_weak_preference", "item": row})

    return conflicts[:limit]


def resolve_personal_conflict(
    conn,
    winner_id,
    loser_ids=None,
    merged_value="",
    reason="",
    loser_status="stale",
    scope="",
    valid_until="",
):
    clean_winner_id = clean_text(winner_id)
    clean_loser_status = clean_text(loser_status).lower().replace("-", "_") or "stale"
    if clean_loser_status not in {"stale", "wrong", "scoped"}:
        raise ValueError(f"unsupported loser status: {loser_status}")
    winner = conn.execute(
        """
        SELECT f.id, f.entity, f.property, f.value, f.confidence, f.tags, f.category,
               COALESCE(m.evidence_count, 1) AS evidence_count,
               COALESCE(m.stability_score, 50) AS stability_score,
               COALESCE(m.scope, '') AS scope,
               COALESCE(m.valid_until, '') AS valid_until
        FROM facts f
        LEFT JOIN memory_meta m ON m.fact_id = f.id
        WHERE f.id=?
        """,
        (clean_winner_id,),
    ).fetchone()
    if not winner:
        return None
    if winner["category"] not in PERSONAL_MEMORY_CATEGORIES:
        raise ValueError("winner must be a personal memory")

    subject = personal_subject_from_entity(winner["entity"]) or winner["entity"]
    losers = normalize_id_list(loser_ids)
    if losers:
        placeholders = ",".join("?" for _ in losers)
        loser_rows = conn.execute(
            f"""
            SELECT f.id, f.entity, f.property, f.value, f.category,
                   COALESCE(m.evidence_count, 1) AS evidence_count,
                   COALESCE(m.stability_score, 50) AS stability_score,
                   COALESCE(m.correction_status, '') AS correction_status
            FROM facts f
            LEFT JOIN memory_meta m ON m.fact_id = f.id
            WHERE f.id IN ({placeholders})
            """,
            losers,
        ).fetchall()
    else:
        loser_rows = conn.execute(
            """
            SELECT f.id, f.entity, f.property, f.value, f.category,
                   COALESCE(m.evidence_count, 1) AS evidence_count,
                   COALESCE(m.stability_score, 50) AS stability_score,
                   COALESCE(m.correction_status, '') AS correction_status
            FROM facts f
            LEFT JOIN memory_meta m ON m.fact_id = f.id
            WHERE f.id != ? AND f.property = ? AND f.category IN (?, ?, ?, ?, ?, ?)
            ORDER BY f.updated_at DESC
            """,
            (clean_winner_id, winner["property"], *sorted(PERSONAL_MEMORY_CATEGORIES)),
        ).fetchall()
        loser_rows = [
            row
            for row in loser_rows
            if (personal_subject_from_entity(row["entity"]) or row["entity"]) == subject
        ]

    active_losers = [
        dict(row)
        for row in loser_rows
        if row["id"] != clean_winner_id and row["correction_status"] not in {"wrong", "stale"}
    ]
    if not active_losers:
        return {
            "ok": True,
            "winner_id": clean_winner_id,
            "winner_value": winner["value"],
            "loser_ids": [],
            "loser_status": clean_loser_status,
            "merged": False,
            "message": "no active losers to resolve",
        }

    final_value = clean_text(merged_value) or winner["value"]
    total_evidence = max(1, int(winner["evidence_count"] or 1)) + sum(max(1, int(item["evidence_count"] or 1)) for item in active_losers)
    target_stability = max(int(winner["stability_score"] or 50), min(95, 70 + len(active_losers) * 5))
    rid, action = upsert_fact(
        conn,
        winner["entity"],
        winner["property"],
        final_value,
        confidence=winner["confidence"],
        tags=winner["tags"],
        category=winner["category"],
        source="personal_conflict_resolution",
        payload={
            "resolution": "merge" if clean_text(merged_value) else "confirm",
            "winner_id": clean_winner_id,
            "loser_ids": [item["id"] for item in active_losers],
            "reason": clean_text(reason),
            "subject": subject,
        },
        content_type="application/json",
    )
    conn.execute(
        "UPDATE memory_meta SET evidence_count=?, stability_score=?, correction_status=?, corrected_at=?, "
        "last_reviewed_at=?, scope=?, valid_until=? WHERE fact_id=?",
        (
            total_evidence,
            target_stability,
            "confirmed",
            now_local(),
            now_local(),
            clean_text(scope) or winner["scope"],
            clean_text(valid_until) or winner["valid_until"],
            rid,
        ),
    )
    append_audit_event(
        conn,
        rid,
        "personal_conflict_resolved",
        source="personal_conflict_resolution",
        previous_value=winner["value"],
        new_value=final_value,
        reason=clean_text(reason),
        payload={
            "loser_ids": [item["id"] for item in active_losers],
            "loser_status": clean_loser_status,
            "resolution": "merge" if clean_text(merged_value) else "confirm",
        },
    )
    for loser in active_losers:
        conn.execute(
            "UPDATE memory_meta SET correction_status=?, corrected_at=?, last_reviewed_at=? WHERE fact_id=?",
            (clean_loser_status, now_local(), now_local(), loser["id"]),
        )
        append_audit_event(
            conn,
            loser["id"],
            "memory_superseded",
            source="personal_conflict_resolution",
            previous_value=loser["value"],
            new_value=final_value,
            reason=clean_text(reason),
            related_fact_id=rid,
            payload={"status": clean_loser_status},
        )
        link_records(conn, "fact", rid, "supersedes", "fact", loser["id"])
        link_records(conn, "fact", loser["id"], "superseded_by", "fact", rid)
        review_fact(conn, loser["id"], category=loser["category"], source="personal_conflict_resolution")
    review_fact(conn, rid, category=winner["category"], source="personal_conflict_resolution")
    return {
        "ok": True,
        "winner_id": rid,
        "winner_value": final_value,
        "winner_action": action,
        "loser_ids": [item["id"] for item in active_losers],
        "loser_status": clean_loser_status,
        "merged": bool(clean_text(merged_value)),
        "reason": clean_text(reason),
        "evidence_count": total_evidence,
        "stability_score": target_stability,
        "scope": clean_text(scope) or winner["scope"],
        "valid_until": clean_text(valid_until) or winner["valid_until"],
    }


def personal_memory_review(conn, subject="user", limit=10):
    limit = normalize_limit(limit, default=10, maximum=50)
    placeholders = ",".join("?" for _ in PERSONAL_MEMORY_CATEGORIES)
    counts = conn.execute(
        f"SELECT category, COUNT(*) AS cnt FROM facts WHERE category IN ({placeholders}) GROUP BY category",
        sorted(PERSONAL_MEMORY_CATEGORIES),
    ).fetchall()
    recent = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
        "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
        "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.source, '') AS source "
        "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id "
        f"WHERE f.category IN ({placeholders}) ORDER BY f.updated_at DESC LIMIT ?",
        [*sorted(PERSONAL_MEMORY_CATEGORIES), limit],
    ).fetchall()
    episode_rows = conn.execute(
        "SELECT id FROM facts WHERE category=? ORDER BY updated_at DESC LIMIT ?",
        (CATEGORY_EPISODE, limit),
    ).fetchall()
    suggestions = []
    for row in episode_rows:
        preview = consolidate_episode(conn, row["id"], subject=subject, dry_run=True, limit=3)
        if preview["candidates"]:
            suggestions.append(preview)
    conflicts = personal_memory_conflicts(conn, limit=limit)
    return {
        "subject": clean_text(subject) or "user",
        "counts": {row["category"]: row["cnt"] for row in counts},
        "recent": [dict(row) for row in recent],
        "conflicts": conflicts,
        "resolution_candidates": personal_resolution_candidates(conflicts, limit=limit),
        "review_candidates": auto_extract_review_candidates([dict(row) for row in recent], limit=limit),
        "consolidation_suggestions": suggestions[:limit],
    }


def format_digest_memory(row):
    scope = clean_text(row.get("scope", ""))
    scope_suffix = f" scope=`{scope}`" if scope else ""
    return f"- `{clean_text(row.get('category', ''))}/{clean_text(row.get('property', ''))}`{scope_suffix} {clean_text(row.get('value', ''))}"


def format_digest_conflict(conflict):
    conflict_type = clean_text(conflict.get("type", ""))
    if "item" in conflict:
        item = dict(conflict.get("item") or {})
        return f"- `{conflict_type}` {clean_text(item.get('property', ''))}: {clean_text(item.get('value', ''))}"
    items = [dict(item) for item in conflict.get("items", [])]
    values = " | ".join(clean_text(item.get("value", "")) for item in items[:2])
    return f"- `{conflict_type}` {clean_text(conflict.get('property', ''))}: {values}"


def build_review_digest(conn, subject="user", limit=10):
    review = personal_memory_review(conn, subject=subject, limit=limit)
    lines = [
        "# CP Memory Review Digest",
        "",
        f"- Subject: `{review['subject']}`",
        f"- Total personal memories: {sum(int(value or 0) for value in review['counts'].values())}",
        f"- Review candidates: {len(review['review_candidates'])}",
        f"- Conflicts: {len(review['conflicts'])}",
        f"- Consolidation suggestions: {len(review['consolidation_suggestions'])}",
        "",
        "## 最近新增 / Recent Memories",
    ]
    if review["recent"]:
        lines.extend(format_digest_memory(dict(row)) for row in review["recent"][:limit])
    else:
        lines.append("- No recent personal memories.")

    lines.extend(["", "## 待确认 / Needs Review"])
    if review["review_candidates"]:
        for item in review["review_candidates"][:limit]:
            lines.append(f"- `{item['category']}/{item['property']}` {item['value']}")
            lines.append(f"  - 建议 / Action: {item['recommended_action']}")
            lines.append(f"  - 原因 / Reason: {item['reason_summary']}")
    else:
        lines.append("- No pending auto-extracted memories.")

    lines.extend(["", "## 冲突和过期 / Conflicts And Stale Candidates"])
    if review["conflicts"]:
        lines.extend(format_digest_conflict(dict(item)) for item in review["conflicts"][:limit])
    else:
        lines.append("- No open conflicts or stale candidates.")

    lines.extend(["", "## 解决建议 / Resolution Suggestions"])
    if review["resolution_candidates"]:
        for item in review["resolution_candidates"][:limit]:
            winner = dict(item.get("winner_suggestion") or {})
            lines.append(f"- `{item['recommended_action']}` {clean_text(item.get('property', ''))}")
            lines.append(f"  - 建议保留 / Keep: `{winner.get('id', '')}` {clean_text(winner.get('value', ''))}")
            lines.append(f"  - 建议处理 / Resolve: {', '.join(item.get('loser_ids', [])) or 'none'}")
            lines.append(f"  - 原因 / Reason: {item['reason_summary']}")
    else:
        lines.append("- No conflict resolution suggestions.")

    lines.extend(["", "## 可提炼事件 / Consolidation Suggestions"])
    if review["consolidation_suggestions"]:
        for item in review["consolidation_suggestions"][:limit]:
            candidates = item.get("candidates", [])
            lines.append(f"- Episode `{item.get('episode_id', '')}` has {len(candidates)} candidate(s).")
    else:
        lines.append("- No episode consolidation suggestions.")

    return "\n".join(lines).strip() + "\n"


def build_review_reminder(conn, subject="user", limit=10):
    review = personal_memory_review(conn, subject=subject, limit=limit)
    cleanup_count = len(auto_extract_cleanup_candidates(conn, limit=limit))
    needs_review = len(review["review_candidates"])
    conflicts = len(review["conflicts"])
    suggestions = len(review["consolidation_suggestions"])
    total = needs_review + conflicts + suggestions + cleanup_count
    if total <= 0:
        return ""
    return (
        "\n\n---\n"
        "CP Memory 提醒 / Reminder: "
        f"{total} 项记忆待审阅 "
        f"(待确认 {needs_review}, 冲突/过期 {conflicts}, 可提炼 {suggestions}, 噪声候选 {cleanup_count})。"
        "需要时可运行 `memory_review_digest(subject=\"user\")` 查看详情；不会自动删除记忆。"
    )


def upsert_payload(conn, fact_id, content, content_type="text/plain"):
    ts = now_local()
    text = payload_text(content)
    checksum = payload_checksum(text)
    existing = conn.execute("SELECT created_at FROM memory_payloads WHERE fact_id=?", (fact_id,)).fetchone()
    created_at = existing["created_at"] if existing else ts
    conn.execute(
        "INSERT OR REPLACE INTO memory_payloads (fact_id, content, content_type, checksum, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (fact_id, text, content_type, checksum, created_at, ts),
    )
    sync_fulltext_row(conn, fact_id)


def append_audit_event(
    conn,
    fact_id,
    event_type,
    source="",
    previous_value="",
    new_value="",
    reason="",
    related_fact_id="",
    payload=None,
):
    rid = new_id("aud_")
    payload_text_value = payload_text(payload) if payload is not None else ""
    conn.execute(
        "INSERT INTO memory_audit_log (id, fact_id, event_type, source, previous_value, new_value, reason, related_fact_id, payload, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            rid,
            clean_text(fact_id),
            clean_text(event_type),
            clean_text(source),
            clean_text(previous_value),
            clean_text(new_value),
            clean_text(reason),
            clean_text(related_fact_id),
            payload_text_value,
            now_local(),
        ),
    )
    return rid


def list_audit_events(conn, fact_id="", limit=20):
    clean_fact_id = clean_text(fact_id)
    clean_limit = normalize_limit(limit, default=20, maximum=200)
    if clean_fact_id:
        rows = conn.execute(
            "SELECT id, fact_id, event_type, source, previous_value, new_value, reason, related_fact_id, payload, created_at "
            "FROM memory_audit_log WHERE fact_id=? ORDER BY created_at DESC LIMIT ?",
            (clean_fact_id, clean_limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, fact_id, event_type, source, previous_value, new_value, reason, related_fact_id, payload, created_at "
            "FROM memory_audit_log ORDER BY created_at DESC LIMIT ?",
            (clean_limit,),
        ).fetchall()
    return rows


def sync_fulltext_row(conn, fact_id):
    try:
        conn.execute("SELECT 1 FROM facts_fts LIMIT 1")
    except sqlite3.OperationalError:
        return

    conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
    row = conn.execute(
        """
        SELECT f.id, f.entity, f.property, f.value, f.tags, f.category, COALESCE(p.content, '') AS payload
        FROM facts f
        LEFT JOIN memory_payloads p ON p.fact_id = f.id
        WHERE f.id = ?
        """,
        (fact_id,),
    ).fetchone()
    if row:
        conn.execute(
            "INSERT INTO facts_fts (fact_id, entity, property, value, tags, category, payload) VALUES (?,?,?,?,?,?,?)",
            (
                row["id"],
                row["entity"],
                row["property"],
                row["value"],
                row["tags"],
                row["category"],
                row["payload"],
            ),
        )


def delete_fact(conn, fact_id):
    conn.execute("DELETE FROM facts WHERE id=?", (fact_id,))
    conn.execute("DELETE FROM memory_meta WHERE fact_id=?", (fact_id,))
    conn.execute("DELETE FROM memory_payloads WHERE fact_id=?", (fact_id,))
    conn.execute("DELETE FROM memory_links WHERE source_kind='fact' AND source_id=?", (fact_id,))
    conn.execute("DELETE FROM memory_links WHERE target_kind='fact' AND target_id=?", (fact_id,))
    try:
        conn.execute("DELETE FROM facts_fts WHERE fact_id = ?", (fact_id,))
    except sqlite3.OperationalError:
        pass


def link_records(conn, source_kind, source_id, relation, target_kind, target_id):
    source_kind = clean_text(source_kind)
    source_id = clean_text(source_id)
    relation = clean_text(relation)
    target_kind = clean_text(target_kind)
    target_id = clean_text(target_id)
    existing = conn.execute(
        "SELECT id FROM memory_links WHERE source_kind=? AND source_id=? AND relation=? AND target_kind=? AND target_id=?",
        (source_kind, source_id, relation, target_kind, target_id),
    ).fetchone()
    if existing:
        return existing["id"], "existing"
    rid = new_id("lnk_")
    conn.execute(
        "INSERT INTO memory_links (id, source_kind, source_id, target_kind, target_id, relation, created_at) VALUES (?,?,?,?,?,?,?)",
        (rid, source_kind, source_id, target_kind, target_id, relation, now_local()),
    )
    return rid, "created"


def list_links(conn, source_kind="", source_id="", target_kind="", target_id="", relation=""):
    conditions = []
    params = []
    for column, value in (
        ("source_kind", source_kind),
        ("source_id", source_id),
        ("target_kind", target_kind),
        ("target_id", target_id),
        ("relation", relation),
    ):
        if clean_text(value):
            conditions.append(f"{column} = ?")
            params.append(clean_text(value))
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return conn.execute(
        f"SELECT id, source_kind, source_id, relation, target_kind, target_id, created_at FROM memory_links {where} ORDER BY created_at DESC",
        params,
    ).fetchall()


def auto_link_neighbors(conn, fact_id, entity, prop, category):
    if category == CATEGORY_SUMMARY:
        task = active_task(conn)
        if task and task["id"] != fact_id:
            link_records(conn, "fact", fact_id, "about_task", "fact", task["id"])
    if category == CATEGORY_CHECKPOINT:
        task = active_task(conn)
        if task and task["id"] != fact_id:
            link_records(conn, "fact", fact_id, "about_task", "fact", task["id"])
        summary = conn.execute(
            "SELECT id FROM facts WHERE entity='CP Memory.CurrentConversation' AND category=? ORDER BY updated_at DESC LIMIT 1",
            (CATEGORY_SUMMARY,),
        ).fetchone()
        if summary and summary["id"] != fact_id:
            link_records(conn, "fact", fact_id, "follows_summary", "fact", summary["id"])
    if category == CATEGORY_DECISION:
        row = conn.execute("SELECT id FROM decisions WHERE title=?", (prop,)).fetchone()
        if row:
            link_records(conn, "fact", fact_id, "mirrors", "decision", row["id"])


def touch_fact_ids(conn, ids):
    cleaned = [clean_text(item) for item in ids if clean_text(item)]
    if not cleaned:
        return 0
    placeholders = ",".join("?" for _ in cleaned)
    conn.execute(
        f"UPDATE memory_meta SET access_count=access_count+1, last_accessed_at=? WHERE fact_id IN ({placeholders})",
        [now_local(), *cleaned],
    )
    return len(cleaned)


def fts_available(conn):
    try:
        conn.execute("SELECT 1 FROM facts_fts LIMIT 1")
        return True
    except sqlite3.OperationalError:
        return False


def fact_search_text(row):
    keys = set(row.keys()) if hasattr(row, "keys") else set()
    return " ".join(str(row[key] if key in keys else "" or "") for key in ("entity", "property", "value", "tags", "category", "payload")).lower()


def like_search(conn, keywords, limit, mode):
    if not keywords:
        return []
    operator = " AND " if mode == "and" else " OR "
    conditions = []
    params = []
    for kw in keywords:
        like = f"%{kw}%"
        conditions.append("(f.entity || ' ' || f.property || ' ' || f.value || ' ' || f.tags || ' ' || f.category || ' ' || COALESCE(p.content, '') LIKE ?)")
        params.append(like)
    rows = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.confidence, f.tags, f.category, f.created_at, f.updated_at, COALESCE(p.content, '') AS payload, "
        "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
        "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source "
        "FROM facts f LEFT JOIN memory_payloads p ON p.fact_id = f.id LEFT JOIN memory_meta m ON m.fact_id = f.id "
        f"WHERE {operator.join(conditions)} ORDER BY f.updated_at DESC, f.created_at DESC LIMIT ?",
        [*params, limit * 5],
    ).fetchall()

    lowered = [kw.lower() for kw in keywords]
    ranked = []
    for row in rows:
        text = fact_search_text(row)
        score = sum(1 for kw in lowered if kw in text)
        if mode == "and" and score != len(lowered):
            continue
        ranked.append((score, row["updated_at"] or row["created_at"], row))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in ranked[:limit]]


def fts_search(conn, keywords, limit, mode):
    if not keywords or not fts_available(conn):
        return None
    terms = []
    for keyword in keywords:
        escaped = keyword.replace('"', ' ')
        terms.append(f'"{escaped}"')
    joiner = " AND " if mode == "and" else " OR "
    match = joiner.join(terms)
    rows = conn.execute(
        """
        SELECT f.id, f.entity, f.property, f.value, f.confidence, f.tags, f.category, f.created_at, f.updated_at,
               bm25(facts_fts) AS rank,
               COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count,
               COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source
        FROM facts_fts
        JOIN facts f ON f.id = facts_fts.fact_id
        LEFT JOIN memory_meta m ON m.fact_id = f.id
        WHERE facts_fts MATCH ?
        ORDER BY rank, f.updated_at DESC
        LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    return rows


def search_records(conn, query, limit=20, mode="or", categories=None):
    keywords = parse_keywords(query)
    limit = normalize_limit(limit)
    mode = (mode or "or").strip().lower()
    rows = fts_search(conn, keywords, limit, mode)
    if rows is None or not rows:
        rows = like_search(conn, keywords, limit, mode)
    if categories:
        allowed = {normalize_category(item) for item in categories}
        rows = [row for row in rows if row["category"] in allowed]
    return rows


def infer_recall_intent(query="", explicit_intent=""):
    clean_explicit = clean_text(explicit_intent).lower()
    if clean_explicit:
        return clean_explicit
    text = clean_text(query).lower()
    if not text:
        return "general_memory"
    if any(token in text for token in ("治理", "冲突", "纠正", "audit", "review", "噪声", "质量", "版本演进", "产品历史")):
        return "governance"
    if any(token in text for token in ("昨天", "上次", "之前", "刚刚", "那次", "提过", "回忆", "总结", "继续")):
        return "history"
    if any(token in text for token in ("昵称", "身份", "偏好", "喜欢", "不喜欢", "关系", "长期目标", "ongoing", "episode", "belief", "记得")):
        return "identity"
    if "cp memory" in text:
        return "product_history"
    return "general_memory"


def recall_primary_categories(intent):
    mapping = {
        "identity": [
            CATEGORY_PROFILE,
            CATEGORY_PREFERENCE,
            CATEGORY_RELATIONSHIP,
            CATEGORY_ONGOING,
            CATEGORY_BELIEF_DECISION,
            CATEGORY_EPISODE,
        ],
        "history": [CATEGORY_SUMMARY, CATEGORY_EPISODE, CATEGORY_CHECKPOINT, CATEGORY_ONGOING],
        "product_history": [CATEGORY_SUMMARY, CATEGORY_DECISION, CATEGORY_EPISODE, CATEGORY_BELIEF_DECISION],
        "governance": [
            CATEGORY_SUMMARY,
            CATEGORY_EPISODE,
            CATEGORY_PROFILE,
            CATEGORY_PREFERENCE,
            CATEGORY_RELATIONSHIP,
            CATEGORY_ONGOING,
            CATEGORY_BELIEF_DECISION,
            CATEGORY_CHECKPOINT,
        ],
        "general_memory": None,
    }
    return mapping.get(intent, None)


def recall_primary_records(conn, query="", intent="", limit=8):
    resolved_intent = infer_recall_intent(query, explicit_intent=intent)
    categories = recall_primary_categories(resolved_intent)
    clean_limit = normalize_limit(limit, default=8, maximum=30)
    if clean_text(query):
        rows = search_records(conn, query, limit=clean_limit, mode="or", categories=categories)
        if rows:
            return rows, resolved_intent
    if resolved_intent == "identity":
        rows = matching_personal_memories(conn, prompt=query, limit=clean_limit)
        if rows:
            return rows, resolved_intent
    if resolved_intent in {"history", "product_history"}:
        summary_rows = recent_conversation_summaries(conn, limit=min(clean_limit, 4))
        episode_rows = recent_personal_episodes(conn, prompt=query, limit=min(clean_limit, 3))
        combined = list(summary_rows) + list(episode_rows)
        if combined:
            return combined[:clean_limit], resolved_intent
    rows = recent_records(conn, categories=categories, limit=clean_limit) if categories else recent_records(conn, limit=clean_limit)
    return rows, resolved_intent


def has_payload_for_fact(conn, fact_id):
    row = conn.execute("SELECT 1 FROM memory_payloads WHERE fact_id=? LIMIT 1", (fact_id,)).fetchone()
    return row is not None


def assess_recall_strength(conn, rows, intent="", query=""):
    if not rows:
        return {
            "level": "none",
            "score": 0,
            "reason": "no_cp_memory_hits",
        }
    keywords = [item.lower() for item in parse_keywords(query)]
    relevance_hits = 0
    score = 0
    reasons = []
    for row in rows[:5]:
        row_dict = dict(row)
        category = clean_text(row_dict.get("category", ""))
        source = clean_text(row_dict.get("source", ""))
        correction = clean_text(row_dict.get("correction_status", "")).lower()
        text = fact_search_text(row_dict)
        if keywords:
            relevance_hits += sum(1 for keyword in keywords if keyword and keyword in text)
        if category in {CATEGORY_PROFILE, CATEGORY_PREFERENCE, CATEGORY_RELATIONSHIP, CATEGORY_ONGOING, CATEGORY_BELIEF_DECISION, CATEGORY_SUMMARY, CATEGORY_EPISODE}:
            score += 2
        if correction in {"confirmed", ""}:
            score += 1
        if int(row_dict.get("stability_score") or 50) >= 70:
            score += 1
        if int(row_dict.get("evidence_count") or 1) > 1:
            score += 1
        if has_payload_for_fact(conn, row_dict.get("id", "")):
            score += 1
        if source and source != "stop-hook-auto-extract":
            score += 1
        if source == "stop-hook-auto-extract" and correction not in {"confirmed"}:
            score -= 1
    if keywords and relevance_hits == 0:
        score = min(score, 2)
        reasons.append("query_relevance=none")
    elif keywords and relevance_hits > 0:
        score += min(4, relevance_hits)
        reasons.append(f"query_relevance={relevance_hits}")
    if score >= 12:
        level = "strong"
    elif score >= 6:
        level = "medium"
    else:
        level = "weak"
    reasons.append(f"intent={intent or 'general_memory'}")
    reasons.append(f"rows={len(rows)}")
    return {
        "level": level,
        "score": score,
        "reason": ",".join(reasons),
    }


def search_codex_auxiliary_memory(query="", limit=6):
    base = codex_memory_base()
    clean_limit = normalize_limit(limit, default=6, maximum=20)
    files = [base / "memory_summary.md", base / "MEMORY.md"]
    notes_dir = base / "extensions" / "ad_hoc" / "notes"
    if notes_dir.exists():
        recent_notes = sorted(notes_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        files.extend(recent_notes)
    keywords = [item.lower() for item in parse_keywords(query)]
    if not keywords and clean_text(query):
        keywords = [clean_text(query).lower()]
    if not keywords:
        return []
    hits = []
    for path in files:
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            lowered = line.lower()
            score = sum(1 for keyword in keywords if keyword and keyword in lowered)
            if score <= 0:
                continue
            hits.append(
                {
                    "file": str(path),
                    "line": idx,
                    "score": score,
                    "snippet": clean_text(line)[:240],
                }
            )
    hits.sort(key=lambda item: (item["score"], item["line"]), reverse=True)
    return hits[:clean_limit]


def should_use_auxiliary_memory(strength, intent="", row_count=0, query=""):
    level = clean_text((strength or {}).get("level", "")).lower()
    resolved_intent = clean_text(intent).lower()
    if level in {"none", "weak"}:
        return True
    if resolved_intent in {"history", "general_memory"} and row_count < 2 and clean_text(query):
        return True
    return False


def auto_extract_review_candidates(rows, limit=10):
    candidates = []
    for row in rows:
        item = dict(row)
        source = clean_text(item.get("source", ""))
        if source != "stop-hook-auto-extract":
            continue
        correction_status = clean_text(item.get("correction_status", "")).lower()
        if correction_status in {"confirmed", "wrong", "stale"}:
            continue
        if int(item.get("evidence_count") or 1) > 1 and int(item.get("stability_score") or 50) >= 75:
            continue
        candidates.append(
            {
                "id": item.get("id", ""),
                "category": item.get("category", ""),
                "property": item.get("property", ""),
                "value": item.get("value", ""),
                "recommended_action": "review_or_confirm",
                "reason_summary": "自动提炼结果目前仍是低证据或未确认状态，建议在真正依赖前做一次确认、修正或合并。",
            }
        )
        if len(candidates) >= limit:
            break
    return candidates


def looks_like_meta_extracted_noise(value):
    text = clean_text(value)
    if not text:
        return False
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


def auto_extract_governance_stats(conn, limit=5):
    total = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE source='stop-hook-auto-extract'"
    ).fetchone()["cnt"]
    confirmed = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE source='stop-hook-auto-extract' AND correction_status='confirmed'"
    ).fetchone()["cnt"]
    corrected = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_meta WHERE source='stop-hook-auto-extract' AND correction_status IN ('corrected', 'wrong', 'stale', 'scoped')"
    ).fetchone()["cnt"]
    pending_rows = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
        "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
        "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.source, '') AS source "
        "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id "
        "WHERE m.source='stop-hook-auto-extract' ORDER BY f.updated_at DESC LIMIT ?",
        (normalize_limit(limit, default=5, maximum=50) * 4,),
    ).fetchall()
    review_candidates = auto_extract_review_candidates([dict(row) for row in pending_rows], limit=limit)
    return {
        "total": total,
        "confirmed": confirmed,
        "corrected_or_resolved": corrected,
        "pending_review": len(review_candidates),
        "pending_samples": review_candidates[:limit],
    }


def auto_extract_cleanup_candidates(conn, limit=20):
    rows = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
        "COALESCE(m.source, '') AS source, COALESCE(m.correction_status, '') AS correction_status "
        "FROM facts f JOIN memory_meta m ON m.fact_id = f.id "
        "WHERE m.source='stop-hook-auto-extract' ORDER BY f.updated_at DESC LIMIT ?",
        (normalize_limit(limit, default=20, maximum=200) * 4,),
    ).fetchall()
    candidates = []
    for row in rows:
        item = dict(row)
        if clean_text(item.get("correction_status", "")).lower() in {"confirmed", "wrong", "stale"}:
            continue
        if looks_like_meta_extracted_noise(item.get("value", "")):
            item["recommended_action"] = "remove_or_mark_wrong"
            item["reason_summary"] = "自动提炼结果看起来像实现说明、代码路径或工具示例，不像真实长期用户记忆。"
            candidates.append(item)
        if len(candidates) >= normalize_limit(limit, default=20, maximum=200):
            break
    return candidates


def cleanup_auto_extract_noise(conn, dry_run=True, limit=20, action="mark_wrong"):
    candidates = auto_extract_cleanup_candidates(conn, limit=limit)
    cleaned = []
    clean_action = clean_text(action).lower() or "mark_wrong"
    if clean_action not in {"mark_wrong", "delete"}:
        raise ValueError(f"unsupported cleanup action: {action}")
    if not dry_run:
        for item in candidates:
            if clean_action == "mark_wrong":
                correct_memory(
                    conn,
                    item["id"],
                    "wrong",
                    reason=f"auto_extract_cleanup: {item['reason_summary']}",
                )
                append_audit_event(
                    conn,
                    item["id"],
                    "auto_extract_noise_marked_wrong",
                    source="memory_auto_extract_cleanup",
                    previous_value=item["value"],
                    new_value=item["value"],
                    reason=item["reason_summary"],
                    payload={"category": item["category"], "property": item["property"]},
                )
            else:
                append_audit_event(
                    conn,
                    item["id"],
                    "auto_extract_noise_removed",
                    source="memory_auto_extract_cleanup",
                    previous_value=item["value"],
                    new_value="",
                    reason=item["reason_summary"],
                    payload={"category": item["category"], "property": item["property"]},
                )
                delete_fact(conn, item["id"])
            cleaned.append(item["id"])
    return {
        "dry_run": dry_run,
        "action": clean_action,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "cleaned_ids": cleaned,
    }


def governance_acceptance_report(conn, limit=5):
    clean_limit = normalize_limit(limit, default=5, maximum=20)
    personal_placeholders = ",".join("?" for _ in PERSONAL_MEMORY_CATEGORIES)
    facts_count = conn.execute("SELECT COUNT(*) AS cnt FROM facts").fetchone()["cnt"]
    personal_count = conn.execute(
        f"SELECT COUNT(*) AS cnt FROM facts WHERE category IN ({personal_placeholders})",
        sorted(PERSONAL_MEMORY_CATEGORIES),
    ).fetchone()["cnt"]
    corrected_count = conn.execute("SELECT COUNT(*) AS cnt FROM memory_meta WHERE correction_status != ''").fetchone()["cnt"]
    avg_quality = conn.execute("SELECT ROUND(AVG(quality_score), 2) AS val FROM memory_meta").fetchone()["val"]
    avg_noise = conn.execute("SELECT ROUND(AVG(noise_score), 2) AS val FROM memory_meta").fetchone()["val"]
    personal_review = personal_memory_review(conn, subject="user", limit=clean_limit)
    auto_extract_stats = auto_extract_governance_stats(conn, limit=clean_limit)
    cleanup_candidates = auto_extract_cleanup_candidates(conn, limit=clean_limit)
    corrected_samples = conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
        "COALESCE(m.correction_status, '') AS correction_status "
        "FROM facts f JOIN memory_meta m ON m.fact_id = f.id "
        "WHERE m.correction_status != '' ORDER BY m.corrected_at DESC, f.updated_at DESC LIMIT ?",
        (clean_limit,),
    ).fetchall()
    restore_probe_rows = conn.execute(
        f"SELECT f.id, f.entity, f.property, f.value, f.category, COALESCE(m.correction_status, '') AS correction_status "
        "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id "
        f"WHERE f.category IN ({personal_placeholders}) ORDER BY f.updated_at DESC LIMIT ?",
        [*sorted(PERSONAL_MEMORY_CATEGORIES), clean_limit],
    ).fetchall()
    restore_probes = []
    prompt_map = {
        CATEGORY_PROFILE: "你记得我的身份信息吗？",
        CATEGORY_PREFERENCE: "你记得我的偏好吗？",
        CATEGORY_RELATIONSHIP: "你记得我和某个对象的关系吗？",
        CATEGORY_ONGOING: "你记得我最近在推进什么吗？",
        CATEGORY_EPISODE: "你记得我之前提过的那次事情吗？",
        CATEGORY_BELIEF_DECISION: "你记得这个事情的长期方向吗？",
    }
    seen_probe_categories = set()
    for row in restore_probe_rows:
        category = row["category"]
        if category in seen_probe_categories:
            continue
        seen_probe_categories.add(category)
        prompt = prompt_map.get(category, "你还记得之前的重要信息吗？")
        context = build_restore_context(conn, prompt=prompt, max_chars=800)
        restore_probes.append(
            {
                "category": category,
                "prompt": prompt,
                "context_preview": context[:280],
            }
        )
        if len(restore_probes) >= clean_limit:
            break
    gates = {
        "has_personal_memory": personal_count > 0,
        "auto_extract_pending_review_visible": "pending_review" in auto_extract_stats,
        "conflicts_reviewable": isinstance(personal_review.get("resolution_candidates"), list),
        "history_explainable": facts_count > 0,
        "restore_probes_available": bool(restore_probes),
    }
    return {
        "summary": {
            "facts_count": facts_count,
            "personal_memory_count": personal_count,
            "corrected_memory_count": corrected_count,
            "avg_quality_score": avg_quality,
            "avg_noise_score": avg_noise,
        },
        "gates": gates,
        "personal_review": {
            "counts": personal_review.get("counts", {}),
            "conflict_count": len(personal_review.get("conflicts", [])),
            "resolution_candidate_count": len(personal_review.get("resolution_candidates", [])),
            "review_candidate_count": len(personal_review.get("review_candidates", [])),
        },
        "auto_extract_governance": auto_extract_stats,
        "cleanup_candidates": {
            "count": len(cleanup_candidates),
            "samples": cleanup_candidates[:clean_limit],
        },
        "samples": {
            "pending_review": auto_extract_stats.get("pending_samples", []),
            "conflicts": personal_review.get("conflicts", [])[:clean_limit],
            "corrected": [dict(row) for row in corrected_samples],
            "recent_personal": personal_review.get("recent", [])[:clean_limit],
        },
        "restore_probes": restore_probes,
    }


def personal_restore_rank(row, keywords=None, active_scopes=None):
    row_dict = dict(row)
    text = fact_search_text(row_dict)
    clean_keywords = [clean_text(item).lower() for item in (keywords or []) if clean_text(item)]
    keyword_hits = sum(1 for kw in clean_keywords if kw in text)
    correction_status = clean_text(row_dict.get("correction_status", "")).lower()
    source = clean_text(row_dict.get("source", ""))
    category = clean_text(row_dict.get("category", ""))
    auto_extract_penalty = 0
    if source == "stop-hook-auto-extract" and correction_status != "confirmed":
        auto_extract_penalty = 1
    ongoing_recent_boost = 0
    if category == CATEGORY_ONGOING:
        ongoing_recent_boost = 1
    return (
        active_memory_row(row_dict),
        correction_status == "confirmed",
        auto_extract_penalty == 0,
        scope_rank(row_dict.get("scope", ""), active_scopes=active_scopes),
        ongoing_recent_boost,
        keyword_hits,
        int(row_dict.get("stability_score") or 50),
        int(row_dict.get("evidence_count") or 1),
        clean_text(row_dict.get("updated_at", "")),
    )


def recent_conversation_summaries(conn, limit=3):
    rows = conn.execute(
        "SELECT id, entity, property, value, updated_at, created_at FROM facts WHERE entity='CP Memory.CurrentConversation' AND category='summary' ORDER BY updated_at DESC, created_at DESC LIMIT ?",
        (max(limit * 3, limit),),
    ).fetchall()
    deduped = []
    seen_values = set()
    for row in rows:
        value_key = clean_text(row["value"])
        if value_key in seen_values:
            continue
        seen_values.add(value_key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def classify_restore_intents(prompt):
    text = clean_text(prompt).lower()
    if not text:
        return {"startup": 3}
    scores = {
        "history": 0,
        "identity": 0,
        "project": 0,
        "general": 1,
    }
    history_terms = ("刚刚", "上次", "之前", "继续", "说到哪", "聊了什么", "进展", "续上", "未完成", "那次", "那回", "之前说过", "提过")
    identity_terms = ("你是谁", "我是谁", "昵称", "偏好", "规则", "约定", "记忆", "记得", "喜欢", "不喜欢", "习惯", "关系", "目标", "计划", "最近在意")
    project_terms = ("basisproject", "项目", "模块", "仓库", "repo", "代码", "实现", "表", "sql")
    if any(token in text for token in history_terms):
        scores["history"] += 4
    if any(token in text for token in identity_terms):
        scores["identity"] += 4
    if any(token in text for token in project_terms):
        scores["project"] += 3
    if len(parse_keywords(text)) >= 3:
        scores["general"] += 1
    return scores


def should_inject_restore_context(prompt):
    scored = classify_restore_intents(prompt)
    if "startup" in scored:
        return True
    return max(scored.values(), default=0) >= 3


def payload_teaser(payload_row, max_len=100):
    if not payload_row:
        return ""
    text = re.sub(r"\s+", " ", clean_text(payload_row["content"]))
    return text[:max_len]


def render_bullets(lines, title, entries, max_chars):
    if not entries:
        return
    staged = ["", title]
    for entry in entries:
        candidate = "\n".join(lines + staged + [f"- {entry}"])
        if len(candidate) > max_chars:
            break
        staged.append(f"- {entry}")
    if len(staged) > 2:
        lines.extend(staged)


def restore_keywords(prompt):
    text = clean_text(prompt)
    keywords = []
    for token in parse_keywords(text):
        if len(token) >= 2:
            keywords.append(token)
    for term in ("中文", "结论先行", "偏好", "关系", "目标", "计划", "继续", "待处理", "当前", "喜欢", "不喜欢", "记忆", "个人助手", "平台", "东八区", "时区"):
        if term in text and term not in keywords:
            keywords.append(term)
    return keywords[:8]


def recall_section_key(row):
    category = clean_text((dict(row) if not isinstance(row, dict) else row).get("category", ""))
    if category == CATEGORY_PROFILE:
        return "profile"
    if category == CATEGORY_PREFERENCE:
        return "preference"
    if category == CATEGORY_RELATIONSHIP:
        return "relationship"
    if category == CATEGORY_ONGOING:
        return "ongoing"
    if category in {CATEGORY_DECISION, CATEGORY_BELIEF_DECISION}:
        return "decision"
    if category == CATEGORY_EPISODE:
        return "episode"
    if category == CATEGORY_SUMMARY:
        return "summary"
    if category == CATEGORY_CHECKPOINT:
        return "checkpoint"
    return "other"


def recall_section_title(section_key):
    mapping = {
        "profile": "Identity",
        "preference": "Preferences",
        "relationship": "Relationships",
        "ongoing": "Ongoing",
        "decision": "Rules And Decisions",
        "episode": "Episodes",
        "summary": "Summaries",
        "checkpoint": "Checkpoints",
        "other": "Other Memory",
    }
    return mapping.get(section_key, "Other Memory")


def enrich_decision_metadata(conn, row_dict):
    if clean_text(row_dict.get("category", "")) != CATEGORY_DECISION:
        return row_dict
    decision_row = conn.execute(
        "SELECT status, review_state, confidence, source, updated_at FROM decisions WHERE title=? ORDER BY updated_at DESC LIMIT 1",
        (clean_text(row_dict.get("property", "")),),
    ).fetchone()
    if decision_row:
        row_dict = dict(row_dict)
        row_dict["decision_status"] = decision_row["status"]
        row_dict["decision_review_state"] = decision_row["review_state"]
        row_dict["decision_confidence"] = decision_row["confidence"]
        if not clean_text(row_dict.get("source", "")):
            row_dict["source"] = decision_row["source"]
        row_dict["decision_updated_at"] = decision_row["updated_at"]
    return row_dict


def format_recall_entry(row_dict):
    category = clean_text(row_dict.get("category", ""))
    value = str(row_dict.get("value", ""))[:220]
    if category == CATEGORY_DECISION:
        status = clean_text(row_dict.get("decision_status", ""))
        review_state = clean_text(row_dict.get("decision_review_state", ""))
        tail = []
        if review_state:
            tail.append(f"review={review_state}")
        if status:
            tail.append(f"status={status}")
        suffix = f" | {' '.join(tail)}" if tail else ""
        return f"{row_dict.get('property', '')}: {value}{suffix}"
    return f"{row_dict.get('property', '')}: {value}"


def build_recall_sections(conn, rows, intent="", query="", limit_per_section=4):
    ordered_sections = ["profile", "preference", "relationship", "ongoing", "decision", "episode", "summary", "checkpoint", "other"]
    buckets = {key: [] for key in ordered_sections}
    seen = set()
    now_text = now_local()
    for row in rows:
        row_dict = dict(row)
        if not restorable_memory_row(row_dict, now_text=now_text):
            continue
        section_key = recall_section_key(row_dict)
        dedupe_key = (section_key, clean_text(row_dict.get("entity", "")), clean_text(row_dict.get("property", "")), clean_text(row_dict.get("value", "")))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        enriched = enrich_decision_metadata(conn, row_dict)
        buckets[section_key].append(enriched)
    rendered = []
    for key in ordered_sections:
        items = buckets[key][:limit_per_section]
        if not items:
            continue
        rendered.append(
            {
                "key": key,
                "title": recall_section_title(key),
                "items": items,
            }
        )
    return rendered


def matching_personal_memories(conn, prompt="", limit=6):
    keywords = restore_keywords(prompt)
    scopes = prompt_scopes(prompt)
    rows = []
    if keywords:
        rows = search_records(conn, " ".join(keywords), limit=limit * 2, mode="or", categories=sorted(PERSONAL_MEMORY_CATEGORIES))
    if not rows:
        rows = recent_records(conn, categories=sorted(PERSONAL_MEMORY_CATEGORIES), limit=limit * 2)
    now_text = now_local()
    rows = [row for row in rows if restorable_memory_row(dict(row), now_text=now_text)]
    rows = sorted(rows, key=lambda row: personal_restore_rank(row, keywords=keywords, active_scopes=scopes), reverse=True)
    deduped = []
    seen = set()
    for row in rows:
        key = (row["entity"], row["property"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def recent_personal_episodes(conn, prompt="", limit=3):
    keywords = restore_keywords(prompt)
    scopes = prompt_scopes(prompt)
    if keywords:
        rows = search_records(conn, " ".join(keywords), limit=limit * 3, mode="or", categories=[CATEGORY_EPISODE])
        if not rows:
            rows = recent_records(conn, categories=[CATEGORY_EPISODE], limit=limit * 2)
    else:
        rows = recent_records(conn, categories=[CATEGORY_EPISODE], limit=limit * 2)
    now_text = now_local()
    rows = [row for row in rows if restorable_memory_row(dict(row), now_text=now_text)]
    rows = sorted(rows, key=lambda row: personal_restore_rank(row, keywords=keywords, active_scopes=scopes), reverse=True)
    deduped = []
    seen = set()
    for row in rows:
        key = (row["entity"], row["property"], clean_text(row["value"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def active_task(conn):
    return conn.execute(
        "SELECT id, property, value, updated_at FROM facts WHERE entity='__current_task' AND category='task' ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()


def infer_category(entity, prop, value, tags="", source=""):
    inferred = normalize_category("", entity, prop, tags, source)
    text = " ".join(filter(None, [entity, prop, value, tags, source])).lower()
    if entity.startswith("Personal.Profile"):
        return CATEGORY_PROFILE
    if entity.startswith("Personal.Preference"):
        return CATEGORY_PREFERENCE
    if entity.startswith("Personal.Relationship"):
        return CATEGORY_RELATIONSHIP
    if entity.startswith("Personal.Ongoing"):
        return CATEGORY_ONGOING
    if entity.startswith("Personal.Episode"):
        return CATEGORY_EPISODE
    if entity.startswith("Personal.BeliefDecision"):
        return CATEGORY_BELIEF_DECISION
    if entity == "CP Memory.CurrentConversation":
        return CATEGORY_SUMMARY
    if entity == "Hook" and prop == "PreCompact":
        return CATEGORY_CHECKPOINT
    if entity.startswith(("BasisProject.", "Pattern.", "Bug.", "Env.")):
        return CATEGORY_CODE_REFERENCE
    if entity.startswith(("User.Profile", "@agent:", "@user:")):
        return CATEGORY_PROFILE
    if entity.startswith("HermesMemory.") or "automation" in text or "trigger_mode" in prop.lower():
        return CATEGORY_AUTOMATION
    if "summary" in prop.lower() or "summary" in text:
        return CATEGORY_SUMMARY
    if "current_task" in entity.lower():
        return CATEGORY_TASK
    return inferred


def evaluate_memory_quality(category, value, payload_exists=False, link_count=0, tags="", source=""):
    quality = 55
    noise = 10
    text = value or ""
    if category in {CATEGORY_SUMMARY, CATEGORY_DECISION, CATEGORY_PROFILE, CATEGORY_PREFERENCE, CATEGORY_RELATIONSHIP, CATEGORY_ONGOING, CATEGORY_BELIEF_DECISION, CATEGORY_CODE_REFERENCE}:
        quality += 15
        noise -= 4
    if category == CATEGORY_EPISODE:
        quality += 8
        noise -= 2
    if payload_exists:
        quality += 18
        noise -= 3
    if link_count > 0:
        quality += min(12, link_count * 4)
        noise -= min(4, link_count)
    if len(text) < 12:
        quality -= 8
        noise += 8
    if category == CATEGORY_CHECKPOINT and "Conversation compacted" in text:
        noise += 6
    if "legacy-upgrade" in source:
        quality -= 4
    quality = max(0, min(100, quality))
    noise = max(0, min(100, noise))
    return quality, noise


def review_fact(conn, fact_id, category=None, source=""):
    row = conn.execute(
        "SELECT id, entity, property, value, tags, category FROM facts WHERE id=?",
        (fact_id,),
    ).fetchone()
    if not row:
        return None
    effective_category = category or row["category"]
    payload_exists = conn.execute("SELECT 1 FROM memory_payloads WHERE fact_id=?", (fact_id,)).fetchone() is not None
    link_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM memory_links WHERE (source_kind='fact' AND source_id=?) OR (target_kind='fact' AND target_id=?)",
        (fact_id, fact_id),
    ).fetchone()["cnt"]
    quality_score, noise_score = evaluate_memory_quality(
        effective_category,
        row["value"],
        payload_exists=payload_exists,
        link_count=link_count,
        tags=row["tags"],
        source=source,
    )
    conn.execute(
        "UPDATE memory_meta SET quality_score=?, noise_score=?, canonical_category=?, last_reviewed_at=? WHERE fact_id=?",
        (quality_score, noise_score, effective_category, now_local(), fact_id),
    )
    return {"quality_score": quality_score, "noise_score": noise_score, "canonical_category": effective_category}


def migrate_legacy_semantics(conn):
    marker = semantic_upgrade_marker_path()
    if marker.exists():
        return
    rows = conn.execute(
        "SELECT id, entity, property, value, tags, category FROM facts ORDER BY updated_at DESC"
    ).fetchall()
    upgraded = 0
    payload_backfilled = 0
    for row in rows:
        inferred = infer_category(row["entity"], row["property"], row["value"], row["tags"], "legacy-upgrade")
        changed = False
        if row["category"] != inferred:
            conn.execute("UPDATE facts SET category=? WHERE id=?", (inferred, row["id"]))
            changed = True
        payload_exists = conn.execute("SELECT 1 FROM memory_payloads WHERE fact_id=?", (row["id"],)).fetchone() is not None
        if not payload_exists and inferred in {CATEGORY_SUMMARY, CATEGORY_CHECKPOINT, CATEGORY_DECISION}:
            upsert_payload(
                conn,
                row["id"],
                {
                    "legacy_preview": row["value"],
                    "legacy_category": row["category"],
                    "upgraded_category": inferred,
                    "upgraded_at": now_local(),
                },
                content_type="application/json",
            )
            payload_backfilled += 1
            changed = True
        source = "legacy-upgrade"
        summary_type = "legacy"
        if inferred == CATEGORY_SUMMARY:
            summary_type = "turn"
        elif inferred == CATEGORY_CHECKPOINT:
            summary_type = "checkpoint"
        upsert_meta(
            conn,
            row["id"],
            classify_importance(row["value"], row["tags"], inferred),
            expiry_for_importance(classify_importance(row["value"], row["tags"], inferred)),
            source=source,
            summary_type=summary_type,
        )
        review_fact(conn, row["id"], category=inferred, source=source)
        auto_link_neighbors(conn, row["id"], row["entity"], row["property"], inferred)
        if changed:
            upgraded += 1
    ensure_fulltext_populated(conn)
    marker.write_text(
        f"upgraded_at={now_local()}\nrecords_upgraded={upgraded}\npayloads_backfilled={payload_backfilled}\n",
        encoding="utf-8",
    )


def repair_decision_mirrors(conn):
    marker = decision_mirror_marker_path()
    if marker.exists():
        return
    rows = conn.execute(
        "SELECT id, title, context, decision, rationale, source, status, review_state, confidence FROM decisions ORDER BY created_at DESC"
    ).fetchall()
    repaired = 0
    links_added = 0
    for row in rows:
        decision_id, action = upsert_decision_record(
            conn,
            title=row["title"],
            context=row["context"],
            decision=row["decision"],
            rationale=row["rationale"],
            source=clean_text(row["source"]) or "decision-mirror-repair",
            status=clean_text(row["status"]) or "active",
            review_state=clean_text(row["review_state"]) or "confirmed",
            confidence=clean_text(row["confidence"]) or "high",
            payload={"repair": True},
        )
        fact_row = conn.execute(
            "SELECT id FROM facts WHERE entity='Decision' AND property=? ORDER BY updated_at DESC LIMIT 1",
            (row["title"],),
        ).fetchone()
        if fact_row:
            existing_link = conn.execute(
                "SELECT 1 FROM memory_links WHERE source_kind='decision' AND source_id=? AND relation='mirrors' AND target_kind='fact' AND target_id=? LIMIT 1",
                (decision_id, fact_row["id"]),
            ).fetchone()
            if not existing_link:
                link_records(conn, "decision", decision_id, "mirrors", "fact", fact_row["id"])
                links_added += 1
        if action == "created":
            repaired += 1
    marker.write_text(
        f"repaired_at={now_local()}\nrepaired={repaired}\nlinks_added={links_added}\n",
        encoding="utf-8",
    )


def recent_records(conn, categories=None, limit=8):
    if categories:
        placeholders = ",".join("?" for _ in categories)
        return conn.execute(
            f"SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
            "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
            "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source "
            "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id "
            f"WHERE f.category IN ({placeholders}) ORDER BY f.updated_at DESC LIMIT ?",
            [*categories, limit],
        ).fetchall()
    return conn.execute(
        "SELECT f.id, f.entity, f.property, f.value, f.category, f.updated_at, "
        "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
        "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source "
        "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id ORDER BY f.updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()


def detect_restore_intent(prompt):
    scored = classify_restore_intents(prompt)
    if not scored:
        return "startup"
    return max(scored.items(), key=lambda item: item[1])[0]


def build_restore_context(conn, prompt="", max_chars=3200):
    intent = detect_restore_intent(prompt)
    scored = classify_restore_intents(prompt)
    keywords = restore_keywords(prompt)
    scopes = prompt_scopes(prompt)
    lines = ["## CP Memory Context", f"Intent: {intent}"]
    task = active_task(conn)
    if task:
        lines.append(f"- Active task: {task['property']}: {task['value']}")

    if intent in {"startup", "history", "general"}:
        summary_entries = []
        summaries = recent_conversation_summaries(conn, limit=1 if intent == "startup" else 4)
        for row in summaries:
            payload_row = conn.execute("SELECT content FROM memory_payloads WHERE fact_id=?", (row["id"],)).fetchone()
            teaser = payload_teaser(payload_row, 80)
            entry = f"{row['property']}: {str(row['value'])[:220]}"
            if teaser:
                entry += f" | payload: {teaser}"
            summary_entries.append(entry)
        render_bullets(lines, "### Recent Summaries", summary_entries, min(max_chars, 1100 if intent == "startup" else max_chars))

    personal_categories = [
        CATEGORY_PROFILE,
        CATEGORY_PREFERENCE,
        CATEGORY_RELATIONSHIP,
        CATEGORY_ONGOING,
        CATEGORY_BELIEF_DECISION,
    ]
    layered_seed_rows = []
    if intent in {"identity", "general", "startup", "history"} or scored.get("identity", 0) >= 3:
        placeholders = ",".join("?" for _ in personal_categories)
        personal_rows = conn.execute(
            f"SELECT f.entity, f.property, f.value, f.category, f.updated_at, "
            "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
            "COALESCE(m.correction_status, '') AS correction_status, COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source "
            "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id "
            f"WHERE f.category IN ({placeholders}) ORDER BY f.updated_at DESC LIMIT ?",
            [*personal_categories, 5 if intent == "startup" else 10],
        ).fetchall()
        matched_rows = matching_personal_memories(conn, prompt=prompt, limit=6 if intent != "startup" else 3)
        now_text = now_local()
        personal_rows = [row for row in personal_rows if restorable_memory_row(dict(row), now_text=now_text)]
        personal_rows = sorted(personal_rows, key=lambda row: personal_restore_rank(row, keywords=keywords, active_scopes=scopes), reverse=True)
        combined_rows = []
        seen = set()
        for row in list(matched_rows) + list(personal_rows):
            key = (row["entity"], row["property"])
            if key in seen:
                continue
            seen.add(key)
            combined_rows.append(row)
            if len(combined_rows) >= (6 if intent != "startup" else 4):
                break
        layered_seed_rows.extend(combined_rows)

    if intent in {"history", "general"} or (keywords and any(token in prompt for token in ("那次", "那回", "之前说过", "提过"))):
        episode_rows = recent_personal_episodes(conn, prompt=prompt, limit=3)
        render_bullets(
            lines,
            "### Relevant Episodes",
            [f"{row['property']}: {str(row['value'])[:220]}" for row in episode_rows],
            max_chars,
        )

    if intent in {"identity", "general", "startup"} or scored.get("identity", 0) >= 3:
        identity_rows = conn.execute(
            "SELECT f.entity, f.property, f.value, f.category, COALESCE(m.correction_status, '') AS correction_status, "
            "COALESCE(m.stability_score, 50) AS stability_score, COALESCE(m.evidence_count, 1) AS evidence_count, "
            "COALESCE(m.scope, '') AS scope, COALESCE(m.valid_until, '') AS valid_until, COALESCE(m.source, '') AS source, f.updated_at "
            "FROM facts f LEFT JOIN memory_meta m ON m.fact_id = f.id WHERE f.category IN (?, ?) ORDER BY f.updated_at DESC LIMIT ?",
            (CATEGORY_PROFILE, CATEGORY_DECISION, 6 if intent == "startup" else 12),
        ).fetchall()
        identity_rows = [row for row in identity_rows if restorable_memory_row(dict(row))]
        identity_rows = sorted(identity_rows, key=lambda row: personal_restore_rank(row, keywords=keywords, active_scopes=scopes), reverse=True)
        layered_seed_rows.extend(identity_rows)

    if layered_seed_rows:
        for section in build_recall_sections(conn, layered_seed_rows, intent=intent, query=prompt, limit_per_section=4 if intent == "startup" else 6):
            render_bullets(
                lines,
                f"### {section['title']}",
                [format_recall_entry(item) for item in section["items"]],
                min(max_chars, 1800 if intent == "startup" else max_chars),
            )

    if intent in {"project", "general", "startup"} or scored.get("project", 0) >= 3:
        project_rows = conn.execute(
            "SELECT entity, property, value FROM facts WHERE entity LIKE 'BasisProject.%' OR entity LIKE 'Pattern.%' OR entity LIKE 'Bug.%' OR entity LIKE 'Env.%' ORDER BY updated_at DESC LIMIT ?",
            (2 if intent == "startup" else 8,),
        ).fetchall()
        render_bullets(
            lines,
            "### Project Memory",
            [f"{row['entity']} | {row['property']}: {str(row['value'])[:220]}" for row in project_rows],
            max_chars,
        )

    if intent in {"history", "general"}:
        noisy = conn.execute(
            "SELECT entity, property, quality_score, noise_score FROM facts f JOIN memory_meta m ON m.fact_id = f.id WHERE m.noise_score >= 20 ORDER BY m.noise_score DESC LIMIT 3"
        ).fetchall()
        render_bullets(
            lines,
            "### Watch Items",
            [f"{row['entity']} | {row['property']}: noise={row['noise_score']} quality={row['quality_score']}" for row in noisy],
            max_chars,
        )

    primary_rows, recall_intent = recall_primary_records(conn, query=prompt, intent=intent, limit=4)
    strength = assess_recall_strength(conn, primary_rows, intent=recall_intent, query=prompt)
    if should_use_auxiliary_memory(strength, intent=recall_intent, row_count=len(primary_rows), query=prompt):
        auxiliary = search_codex_auxiliary_memory(query=prompt, limit=3)
        render_bullets(
            lines,
            "### Auxiliary Snapshot",
            [
                f"Codex Memory | {Path(item['file']).name}:{item['line']} | {item['snippet']}"
                for item in auxiliary
            ],
            max_chars,
        )

    context = "\n".join(lines)
    return context[:max_chars]


def explain_fact(conn, fact_id=None, entity="", prop=""):
    row = None
    if clean_text(fact_id):
        row = conn.execute(
            "SELECT id, entity, property, value, confidence, tags, category, created_at, updated_at FROM facts WHERE id=?",
            (clean_text(fact_id),),
        ).fetchone()
    elif clean_text(entity) and clean_text(prop):
        row = conn.execute(
            "SELECT id, entity, property, value, confidence, tags, category, created_at, updated_at FROM facts WHERE entity=? AND property=? ORDER BY updated_at DESC LIMIT 1",
            (clean_text(entity), clean_text(prop)),
        ).fetchone()
    if not row:
        return None

    meta = conn.execute(
        "SELECT importance, expires_at, access_count, last_accessed_at, pinned, source, summary_type, quality_score, noise_score, canonical_category, last_reviewed_at, stability_score, evidence_count, correction_status, corrected_at, valid_from, valid_until, scope, sensitivity FROM memory_meta WHERE fact_id=?",
        (row["id"],),
    ).fetchone()
    payload = conn.execute(
        "SELECT content, content_type, checksum, created_at, updated_at FROM memory_payloads WHERE fact_id=?",
        (row["id"],),
    ).fetchone()
    related = list_links(conn, source_kind="fact", source_id=row["id"]) + list_links(conn, target_kind="fact", target_id=row["id"])
    audit_history = list_audit_events(conn, fact_id=row["id"], limit=12)
    return {
        "fact": dict(row),
        "meta": dict(meta) if meta else None,
        "payload": dict(payload) if payload else None,
        "relations": [dict(item) for item in related],
        "history": [dict(item) for item in audit_history],
        "meaning": category_explanation(row["category"], meta["source"] if meta else "", meta["summary_type"] if meta else ""),
    }


def category_explanation(category, source="", summary_type=""):
    mapping = {
        CATEGORY_FACT: "Stable knowledge or a plain remembered fact.",
        CATEGORY_SUMMARY: "Conversation or state summary with a short preview in facts and full detail in memory_payloads.",
        CATEGORY_CHECKPOINT: "Hook/event checkpoint that records something happened; detail lives in memory_payloads when available.",
        CATEGORY_TASK: "Current active task.",
        CATEGORY_TASK_DONE: "Completed task history.",
        CATEGORY_DECISION: "High-value decision mirrored from the decisions table.",
        CATEGORY_AUTOMATION: "Automation or maintenance record.",
        CATEGORY_PROFILE: "Stable identity profile memory about the user or assistant.",
        CATEGORY_PREFERENCE: "Long-term preference, habit, dislike, communication style, or user taste.",
        CATEGORY_RELATIONSHIP: "Relationship between the user and a person, project, tool, place, goal, or topic.",
        CATEGORY_ONGOING: "Ongoing item such as an unfinished thread, long-running goal, todo, or current state.",
        CATEGORY_EPISODE: "Specific event or conversation episode that can later derive longer-term memories.",
        CATEGORY_BELIEF_DECISION: "Stable belief, principle, decision, or long-term stance.",
        CATEGORY_CODE_REFERENCE: "Code structure or file/reference memory.",
        CATEGORY_NOTE: "Ad-hoc note with weaker structure.",
    }
    details = mapping.get(category, "General memory record.")
    if clean_text(source):
        details += f" Source: {source}."
    if clean_text(summary_type):
        details += f" Summary type: {summary_type}."
    return details


def schema_description():
    return {
        "facts": "General memory index table storing the canonical preview record for facts, summaries, tasks, checkpoints, and mirrored decisions.",
        "aliases": "Alias-to-entity mapping for retrieval and entity normalization.",
        "decisions": "Structured ADR-style decision records with title/context/decision/rationale.",
        "memory_meta": "Governance metadata for facts: importance, expiry, access frequency, source, summary type, quality score, noise score, canonical category, stability score, evidence count, validity window, scope, sensitivity, correction status, and review time.",
        "personal_memory_categories": "Six personal-assistant memory categories represented in facts.category: profile, preference, relationship, ongoing, episode, and belief_decision.",
        "workflows": "Reusable step-by-step procedures.",
        "memory_payloads": "High-fidelity long-form or structured payloads attached to facts.",
        "memory_links": "Explicit relations between facts, decisions, workflows, and other memory records.",
        "memory_audit_log": "User-viewable audit timeline for corrections, conflict resolutions, superseded memories, and other important memory mutations.",
        "facts_fts": "FTS5 full-text index over facts plus payload text when SQLite FTS5 is available.",
    }
