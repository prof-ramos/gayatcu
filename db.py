"""
SQLite database layer for study tracker application.

Refactored to use SQLModel ORM.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

import streamlit as st
from sqlalchemy import Engine, UniqueConstraint, case, func, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Field, Session, SQLModel, create_engine, select

logger = logging.getLogger(__name__)

_BACKUP_SCHEMA_VERSION = 1
_BACKUP_REQUEST_TIMEOUT_SECONDS = 15
_VALID_BACKUP_PUT_METHODS = {"PUT", "POST"}
_DEFAULT_SQLITE_PATH = "data/study_tracker.db"
_DB_URL_ENV_KEYS = (
    "DATABASE_URL",
    "POSTGRES_URL_NON_POOLING",
    "POSTGRES_URL",
    "POSTGRES_PRISMA_URL",
)
_UNSUPPORTED_DB_QUERY_PARAMS = {"pgbouncer", "supa"}
_REQUIRED_TABLES = {"topics", "progress", "review_log"}

# --- Models ---


class Topic(SQLModel, table=True):
    __tablename__ = "topics"
    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(index=True)
    secao: str = Field(index=True)
    subsecao: str
    titulo: str

    __table_args__ = (
        UniqueConstraint("codigo", "secao", "subsecao"),
        {"extend_existing": True},
    )


class Progress(SQLModel, table=True):
    __tablename__ = "progress"
    topic_id: int = Field(primary_key=True, foreign_key="topics.id")
    completed_at: str | None = None
    last_reviewed_at: str | None = None
    review_count: int = Field(default=0)
    next_review_date: str | None = Field(default=None, index=True)
    __table_args__ = {"extend_existing": True}


class ReviewLog(SQLModel, table=True):
    __tablename__ = "review_log"
    id: int | None = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topics.id")
    reviewed_at: str
    interval_days: int
    __table_args__ = {"extend_existing": True}


# --- Engine ---


def _normalize_sqlalchemy_url(url: str) -> str:
    """
    Normalize DB URL to an explicit SQLAlchemy-compatible format.
    """
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        # Compatibility with legacy postgres:// URLs
        normalized = normalized.replace("postgres://", "postgresql+psycopg://", 1)
    elif normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)

    if normalized.startswith("postgresql+psycopg://"):
        parsed = urlparse(normalized)
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query_items = [
            (key, value)
            for key, value in query_items
            if key.lower() not in _UNSUPPORTED_DB_QUERY_PARAMS
        ]
        normalized = urlunparse(parsed._replace(query=urlencode(filtered_query_items)))

    return normalized


def _get_configured_database_url() -> str | None:
    """
    Read database URL from Streamlit secrets or environment variables.
    """
    try:
        secrets = st.secrets
    except Exception:
        secrets = None

    if secrets is not None:
        db_cfg = _safe_mapping_get(secrets, "database", {})
        secret_url = _safe_mapping_get(db_cfg, "url") or _safe_mapping_get(
            secrets, "DATABASE_URL"
        )
        if secret_url:
            return _normalize_sqlalchemy_url(str(secret_url))

    for key in _DB_URL_ENV_KEYS:
        value = os.getenv(key)
        if value:
            return _normalize_sqlalchemy_url(value)

    return None


def _resolve_database_target(db_path: str | None = None) -> tuple[str, bool]:
    """
    Resolve database target URL and whether it points to SQLite.
    """
    if db_path:
        # Explicit URL override (e.g. tests/local scripts)
        if "://" in db_path:
            url = _normalize_sqlalchemy_url(db_path)
            return url, url.startswith("sqlite:///")

        sqlite_path = db_path
    else:
        configured_url = _get_configured_database_url()
        if configured_url:
            return configured_url, configured_url.startswith("sqlite:///")
        sqlite_path = _DEFAULT_SQLITE_PATH

    db_dir = os.path.dirname(sqlite_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return f"sqlite:///{sqlite_path}", True


def init_db(db_path: str | None = None) -> Engine:
    """
    Initialize database engine with required tables and indexes.

    Priority:
    1) Explicit URL/path passed in `db_path`
    2) Secrets/env (PostgreSQL/Supabase)
    3) Local SQLite fallback

    Returns the SQLAlchemy engine.
    """
    db_url, is_sqlite = _resolve_database_target(db_path)
    if is_sqlite:
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args={"prepare_threshold": None},
        )

    if is_sqlite:
        SQLModel.metadata.create_all(engine)
        return engine

    if db_url.startswith("postgresql+psycopg://"):
        existing_tables = set(inspect(engine).get_table_names())
        if _REQUIRED_TABLES.issubset(existing_tables):
            return engine

    try:
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        message = str(exc).lower()
        if "already exists" in message and "ix_topics_" in message:
            logger.warning(
                "Schema já existente detectado durante bootstrap; seguindo startup."
            )
        else:
            raise

    return engine


def _safe_mapping_get(container: Any, key: str, default: Any = None) -> Any:
    """
    Safely get a value from mapping-like objects (dict or Streamlit AttrDict).
    """
    if container is None:
        return default

    try:
        return container.get(key, default)
    except Exception:
        pass

    try:
        return container[key]
    except Exception:
        return default


def _get_remote_backup_config() -> dict[str, str | None]:
    """
    Read remote JSON backup configuration from Streamlit secrets.

    Supported keys:
      - [backup].json_get_url / BACKUP_JSON_GET_URL
      - [backup].json_put_url / BACKUP_JSON_PUT_URL
      - [backup].json_put_method / BACKUP_JSON_PUT_METHOD (PUT|POST)
    """
    config = {"get_url": None, "put_url": None, "put_method": "PUT"}

    try:
        secrets = st.secrets
    except Exception:
        return config

    backup_cfg = _safe_mapping_get(secrets, "backup", {})
    get_url = _safe_mapping_get(backup_cfg, "json_get_url") or _safe_mapping_get(
        secrets, "BACKUP_JSON_GET_URL"
    )
    put_url = _safe_mapping_get(backup_cfg, "json_put_url") or _safe_mapping_get(
        secrets, "BACKUP_JSON_PUT_URL"
    )
    put_method_raw = _safe_mapping_get(
        backup_cfg, "json_put_method", _safe_mapping_get(secrets, "BACKUP_JSON_PUT_METHOD", "PUT")
    )

    put_method = str(put_method_raw or "PUT").strip().upper()
    if put_method not in _VALID_BACKUP_PUT_METHODS:
        put_method = "PUT"

    config["get_url"] = str(get_url).strip() if get_url else None
    config["put_url"] = str(put_url).strip() if put_url else None
    config["put_method"] = put_method
    return config


def _normalize_topic_key(raw_data: dict[str, Any]) -> tuple[str, str, str] | None:
    """
    Build the natural topic key (codigo, secao, subsecao) from raw payload.
    """
    codigo = str(raw_data.get("codigo", "")).strip()
    secao = str(raw_data.get("secao", "")).strip()
    subsecao = str(raw_data.get("subsecao", "")).strip()

    if not codigo or not secao or not subsecao:
        return None
    return (codigo, secao, subsecao)


def _optional_str(value: Any) -> str | None:
    """
    Normalize optional string values for snapshot import.
    """
    if value is None:
        return None
    string_value = str(value).strip()
    return string_value or None


def export_snapshot_to_dict(engine: Engine) -> dict[str, Any]:
    """
    Export the full database state as a JSON-serializable snapshot dict.
    """
    with Session(engine) as session:
        topics = session.exec(
            select(Topic).order_by(Topic.secao, Topic.subsecao, Topic.codigo)
        ).all()
        progress_rows = session.exec(
            select(Topic, Progress)
            .join(Progress, Topic.id == Progress.topic_id)
            .order_by(Topic.secao, Topic.subsecao, Topic.codigo)
        ).all()
        review_rows = session.exec(
            select(Topic, ReviewLog)
            .join(ReviewLog, Topic.id == ReviewLog.topic_id)
            .order_by(ReviewLog.reviewed_at, Topic.secao, Topic.subsecao, Topic.codigo)
        ).all()

    return {
        "version": _BACKUP_SCHEMA_VERSION,
        "exported_at": datetime.now().isoformat(),
        "topics": [
            {
                "codigo": topic.codigo,
                "secao": topic.secao,
                "subsecao": topic.subsecao,
                "titulo": topic.titulo,
            }
            for topic in topics
        ],
        "progress": [
            {
                "codigo": topic.codigo,
                "secao": topic.secao,
                "subsecao": topic.subsecao,
                "completed_at": progress.completed_at,
                "last_reviewed_at": progress.last_reviewed_at,
                "review_count": progress.review_count,
                "next_review_date": progress.next_review_date,
            }
            for topic, progress in progress_rows
        ],
        "review_log": [
            {
                "codigo": topic.codigo,
                "secao": topic.secao,
                "subsecao": topic.subsecao,
                "reviewed_at": review.reviewed_at,
                "interval_days": review.interval_days,
            }
            for topic, review in review_rows
        ],
    }


def import_snapshot_from_dict(engine: Engine, snapshot: dict[str, Any]) -> dict[str, int]:
    """
    Import a snapshot dict into the current database (upsert by natural key).
    """
    topics_payload = snapshot.get("topics", [])
    progress_payload = snapshot.get("progress", [])
    review_payload = snapshot.get("review_log", [])

    if not isinstance(topics_payload, list):
        topics_payload = []
    if not isinstance(progress_payload, list):
        progress_payload = []
    if not isinstance(review_payload, list):
        review_payload = []

    stats = {
        "topics_created": 0,
        "topics_updated": 0,
        "progress_upserted": 0,
        "review_logs_added": 0,
    }

    with Session(engine) as session:
        existing_topics = session.exec(select(Topic)).all()
        topic_by_key = {
            (topic.codigo, topic.secao, topic.subsecao): topic for topic in existing_topics
        }

        for raw_topic in topics_payload:
            if not isinstance(raw_topic, dict):
                continue
            topic_key = _normalize_topic_key(raw_topic)
            if topic_key is None:
                continue

            titulo = _optional_str(raw_topic.get("titulo")) or ""
            existing = topic_by_key.get(topic_key)

            if existing is None:
                new_topic = Topic(
                    codigo=topic_key[0],
                    secao=topic_key[1],
                    subsecao=topic_key[2],
                    titulo=titulo,
                )
                session.add(new_topic)
                session.flush()
                topic_by_key[topic_key] = new_topic
                stats["topics_created"] += 1
            elif titulo and existing.titulo != titulo:
                existing.titulo = titulo
                session.add(existing)
                stats["topics_updated"] += 1

        existing_progress = session.exec(select(Progress)).all()
        progress_by_topic_id = {progress.topic_id: progress for progress in existing_progress}

        for raw_progress in progress_payload:
            if not isinstance(raw_progress, dict):
                continue
            topic_key = _normalize_topic_key(raw_progress)
            if topic_key is None:
                continue

            topic = topic_by_key.get(topic_key)
            if topic is None or topic.id is None:
                continue

            progress = progress_by_topic_id.get(topic.id)
            if progress is None:
                progress = Progress(topic_id=topic.id)
                progress_by_topic_id[topic.id] = progress
                session.add(progress)

            progress.completed_at = _optional_str(raw_progress.get("completed_at"))
            progress.last_reviewed_at = _optional_str(raw_progress.get("last_reviewed_at"))
            progress.next_review_date = _optional_str(raw_progress.get("next_review_date"))
            try:
                progress.review_count = max(int(raw_progress.get("review_count", 0) or 0), 0)
            except (TypeError, ValueError):
                progress.review_count = 0

            session.add(progress)
            stats["progress_upserted"] += 1

        existing_logs = session.exec(select(ReviewLog)).all()
        existing_log_keys = {
            (log.topic_id, log.reviewed_at, log.interval_days) for log in existing_logs
        }

        for raw_review in review_payload:
            if not isinstance(raw_review, dict):
                continue
            topic_key = _normalize_topic_key(raw_review)
            if topic_key is None:
                continue

            topic = topic_by_key.get(topic_key)
            if topic is None or topic.id is None:
                continue

            reviewed_at = _optional_str(raw_review.get("reviewed_at"))
            if reviewed_at is None:
                continue

            try:
                interval_days = int(raw_review.get("interval_days", 1) or 1)
            except (TypeError, ValueError):
                interval_days = 1

            dedupe_key = (topic.id, reviewed_at, interval_days)
            if dedupe_key in existing_log_keys:
                continue

            session.add(
                ReviewLog(
                    topic_id=topic.id,
                    reviewed_at=reviewed_at,
                    interval_days=interval_days,
                )
            )
            existing_log_keys.add(dedupe_key)
            stats["review_logs_added"] += 1

        session.commit()

    _invalidate_progress_cache()
    return stats


def push_snapshot_to_remote(engine: Engine, put_url: str | None = None) -> bool:
    """
    Push a JSON snapshot to remote storage via HTTP PUT/POST URL.
    """
    config = _get_remote_backup_config()
    target_url = put_url or config["put_url"]
    if not target_url:
        return False

    method = config["put_method"] if put_url is None else "PUT"
    payload = json.dumps(export_snapshot_to_dict(engine), ensure_ascii=False).encode(
        "utf-8"
    )
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(payload)),
    }

    try:
        request = Request(target_url, data=payload, method=method, headers=headers)
        with urlopen(request, timeout=_BACKUP_REQUEST_TIMEOUT_SECONDS):
            return True
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("Falha no push do backup JSON remoto: %s", exc)
        return False


def restore_snapshot_from_remote(engine: Engine, get_url: str | None = None) -> bool:
    """
    Restore database state from remote JSON snapshot via HTTP GET URL.
    """
    config = _get_remote_backup_config()
    target_url = get_url or config["get_url"]
    if not target_url:
        return False

    try:
        request = Request(target_url, method="GET")
        with urlopen(request, timeout=_BACKUP_REQUEST_TIMEOUT_SECONDS) as response:
            raw_payload = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            logger.info("Backup remoto JSON ainda não existe (HTTP 404).")
            return False
        logger.warning("Falha no restore do backup JSON remoto: %s", exc)
        return False
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning("Falha no restore do backup JSON remoto: %s", exc)
        return False

    if not raw_payload:
        return False

    try:
        snapshot = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("Backup JSON remoto inválido: %s", exc)
        return False

    if not isinstance(snapshot, dict):
        return False

    stats = import_snapshot_from_dict(engine, snapshot)
    changed_rows = (
        stats["topics_created"]
        + stats["topics_updated"]
        + stats["progress_upserted"]
        + stats["review_logs_added"]
    )
    return changed_rows > 0


def _sync_remote_backup_after_write(engine: Engine) -> None:
    """
    Try to sync remote JSON backup after write operations.

    This must never raise to avoid blocking user actions.
    """
    try:
        push_snapshot_to_remote(engine)
    except Exception:
        # Fail-safe: backup is best effort.
        pass


def _invalidate_progress_cache() -> None:
    """
    Invalidate cached progress queries after write operations.

    get_all_progress() uses st.cache_data and excludes `_engine` from hashing,
    so writes must explicitly clear cache to avoid stale UI state.
    """
    try:
        get_all_progress.clear()
    except Exception:
        # Cache clear can fail in non-Streamlit runtimes; ignore safely.
        pass


def import_topics_from_json(engine: Engine, json_path: str = "conteudo.json") -> int:
    """
    Import topics from JSON file into the database.
    """
    with open(json_path, encoding="utf-8") as f:
        sections = json.load(f)

    imported_count = 0
    updated_count = 0

    with Session(engine) as session:
        for section in sections:
            secao_titulo = section.get("titulo", "")
            for subsecao in section.get("subsecoes", []):
                subsecao_titulo = subsecao.get("titulo", "")
                for topico in subsecao.get("topicos", []):
                    codigo = topico.get("codigo", "")
                    titulo = topico.get("titulo", "")

                    statement = select(Topic).where(
                        Topic.codigo == codigo,
                        Topic.secao == secao_titulo,
                        Topic.subsecao == subsecao_titulo,
                    )
                    existing = session.exec(statement).first()

                    if not existing:
                        new_topic = Topic(
                            codigo=codigo,
                            secao=secao_titulo,
                            subsecao=subsecao_titulo,
                            titulo=titulo,
                        )
                        session.add(new_topic)
                        imported_count += 1
                    elif existing.titulo != titulo:
                        existing.titulo = titulo
                        session.add(existing)
                        updated_count += 1

        session.commit()

    if imported_count > 0 or updated_count > 0:
        _invalidate_progress_cache()
        _sync_remote_backup_after_write(engine)
    return imported_count


def mark_topic_complete(engine: Engine, topic_id: int) -> bool:
    """
    Mark a topic as completed with current timestamp.
    """
    dt_now = datetime.now()
    now_iso = dt_now.isoformat()
    next_review = (dt_now + timedelta(days=1)).strftime("%Y-%m-%d")

    with Session(engine) as session:
        topic = session.get(Topic, topic_id)
        if not topic:
            return False

        progress = session.get(Progress, topic_id)
        if progress:
            if not progress.completed_at:
                progress.completed_at = now_iso
        else:
            progress = Progress(
                topic_id=topic_id,
                completed_at=now_iso,
                next_review_date=next_review,
                review_count=0,
            )
            session.add(progress)

        session.commit()
        _invalidate_progress_cache()
        _sync_remote_backup_after_write(engine)
        return True


def get_topic_progress(engine: Engine, topic_id: int) -> dict[str, Any] | None:
    """
    Get detailed progress information for a specific topic.
    """
    with Session(engine) as session:
        topic = session.get(Topic, topic_id)
        if not topic:
            return None

        progress = session.get(Progress, topic_id)

        return {
            "id": topic.id,
            "codigo": topic.codigo,
            "secao": topic.secao,
            "subsecao": topic.subsecao,
            "titulo": topic.titulo,
            "completed_at": progress.completed_at if progress else None,
            "last_reviewed_at": progress.last_reviewed_at if progress else None,
            "review_count": progress.review_count if progress else 0,
            "next_review_date": progress.next_review_date if progress else None,
        }


@st.cache_data(
    ttl=60, max_entries=100
)  # Cache por 1 minuto, max 100 entries para otimizar memória
def get_all_progress(
    _engine: Engine, offset: int = 0, limit: int | None = None
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Get progress information for all topics with pagination.

    Args:
        _engine: Database engine
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (None = sem limite)

    Returns:
        Lista completa de progresso por padrão.
        Quando paginação for solicitada (`offset > 0` ou `limit` definido),
        retorna dict com 'data' e 'total'.
    """
    with Session(_engine) as session:
        # Get total count
        total_statement = select(func.count(Topic.id))
        total_count = session.exec(total_statement).first()

        # Get paginated data
        statement = (
            select(Topic, Progress)
            .join(Progress, isouter=True)
            .order_by(Topic.secao, Topic.subsecao, Topic.codigo)
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)
        results = session.exec(statement).all()

        output = []
        for topic, progress in results:
            output.append(
                {
                    "id": topic.id,
                    "codigo": topic.codigo,
                    "secao": topic.secao,
                    "subsecao": topic.subsecao,
                    "titulo": topic.titulo,
                    "completed_at": progress.completed_at if progress else None,
                    "last_reviewed_at": progress.last_reviewed_at if progress else None,
                    "review_count": progress.review_count if progress else 0,
                    "next_review_date": progress.next_review_date if progress else None,
                }
            )

        # Return dict when pagination is explicitly requested
        if offset > 0 or limit is not None:
            return {"data": output, "total": total_count or 0}
        # Return full list by default for app compatibility
        return output


def get_topics_due_for_review(engine: Engine, date: str) -> list[dict[str, Any]]:
    """
    Get all topics that are due for review on or before the given date.
    """
    with Session(engine) as session:
        statement = (
            select(Topic, Progress)
            .join(Progress)
            .where(
                Progress.completed_at.is_not(None),
                (Progress.next_review_date.is_(None))
                | (Progress.next_review_date <= date),
            )
            .order_by(Progress.next_review_date, Topic.secao, Topic.subsecao)
        )

        results = session.exec(statement).all()

        output = []
        for topic, progress in results:
            output.append(
                {
                    "id": topic.id,
                    "codigo": topic.codigo,
                    "secao": topic.secao,
                    "subsecao": topic.subsecao,
                    "titulo": topic.titulo,
                    "completed_at": progress.completed_at,
                    "last_reviewed_at": progress.last_reviewed_at,
                    "review_count": progress.review_count,
                    "next_review_date": progress.next_review_date,
                }
            )
        return output


def mark_review_complete(engine: Engine, topic_id: int, interval: int) -> bool:
    """
    Mark a review as complete and schedule the next review date.
    """
    now = datetime.now()

    with Session(engine) as session:
        progress = session.get(Progress, topic_id)
        if not progress or not progress.completed_at:
            return False

        next_review = (now + timedelta(days=interval)).strftime("%Y-%m-%d")
        now_iso = now.isoformat()

        review_log = ReviewLog(
            topic_id=topic_id, reviewed_at=now_iso, interval_days=interval
        )
        session.add(review_log)

        progress.last_reviewed_at = now_iso
        progress.review_count += 1
        progress.next_review_date = next_review

        session.add(progress)
        session.commit()
        _invalidate_progress_cache()
        _sync_remote_backup_after_write(engine)
        return True


def get_statistics(engine: Engine) -> dict[str, Any]:
    """
    Calculate and return overall study statistics.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    with Session(engine) as session:
        total_topics_result = session.exec(select(func.count(Topic.id))).first()
        total_topics = total_topics_result if total_topics_result is not None else 0

        completed_topics_result = session.exec(
            select(func.count(Progress.topic_id)).where(
                Progress.completed_at.is_not(None)
            )
        ).first()
        completed_topics = (
            completed_topics_result if completed_topics_result is not None else 0
        )

        total_reviews_result = session.exec(
            select(func.sum(Progress.review_count))
        ).first()
        total_reviews = total_reviews_result if total_reviews_result is not None else 0

        due_today_result = session.exec(
            select(func.count(Progress.topic_id)).where(
                Progress.completed_at.is_not(None),
                (Progress.next_review_date.is_(None))
                | (Progress.next_review_date <= today),
            )
        ).first()
        due_today = due_today_result if due_today_result is not None else 0

        completion_rate = (
            (completed_topics / total_topics * 100) if total_topics > 0 else 0
        )

        return {
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "pending_topics": total_topics - completed_topics,
            "total_reviews": total_reviews,
            "due_today": due_today,
            "completion_rate": round(completion_rate, 2),
        }


def get_detailed_statistics_by_section(engine: Engine) -> list[dict[str, Any]]:
    """
    Get detailed statistics grouped by section.

    Returns a list of dicts with section name, total topics, completed topics,
    and calculated percentage. This query is used in the statistics page.
    """
    with Session(engine) as session:
        statement = (
            select(
                Topic.secao,
                func.count(Topic.id).label("total"),
                func.sum(case((Progress.completed_at.is_not(None), 1), else_=0)).label(
                    "completed"
                ),
            )
            .outerjoin(Progress, Topic.id == Progress.topic_id)
            .group_by(Topic.secao)
            .order_by(Topic.secao)
        )

        results = session.exec(statement).all()

        output = []
        for secao, total, completed in results:
            completed_val = completed if completed is not None else 0
            percentage = (completed_val / total * 100.0) if total > 0 else 0.0
            output.append(
                {
                    "secao": secao,
                    "total": total,
                    "completed": completed_val,
                    "percentage": round(percentage, 1),
                    "pending": total - completed_val,
                }
            )

        return output


def get_weekly_review_data(engine: Engine, weeks: int = 12) -> list[dict[str, Any]]:
    """
    Get review counts per week for the last N weeks.

    Args:
        engine: Database engine
        weeks: Number of weeks to look back (default: 12)

    Returns:
        List of dicts with 'week' (date) and 'count' (number of reviews)
    """
    days_back = weeks * 7

    with Session(engine) as session:
        cutoff_date = datetime.now() - timedelta(days=days_back)

        statement = (
            select(
                func.date(ReviewLog.reviewed_at).label("review_date"),
                func.count(ReviewLog.id).label("count"),
            )
            .where(ReviewLog.reviewed_at >= cutoff_date)
            .group_by(func.date(ReviewLog.reviewed_at))
            .order_by(func.date(ReviewLog.reviewed_at))
        )

        results = session.exec(statement).all()

        output = [{"review_date": str(row[0]), "count": row[1]} for row in results]

        return output


def get_topic_distribution_by_section(engine: Engine) -> list[dict[str, Any]]:
    """
    Get topic distribution by section.

    Returns a list of dicts with section name and total topic count.
    Used for pie chart visualization.
    """
    with Session(engine) as session:
        statement = (
            select(Topic.secao, func.count(Topic.id).label("total"))
            .group_by(Topic.secao)
            .order_by(func.count(Topic.id).desc())
        )

        results = session.exec(statement).all()

        output = [{"secao": row[0], "total": row[1]} for row in results]

        return output


def export_all_progress_to_dict(engine: Engine) -> list[dict[str, Any]]:
    """
    Export all progress data as a list of dicts for CSV export.

    Returns comprehensive progress data including topics, completion dates,
    review counts, and next review dates.
    """
    with Session(engine) as session:
        statement = (
            select(
                Topic.codigo,
                Topic.secao,
                Topic.subsecao,
                Topic.titulo,
                Progress.completed_at,
                Progress.last_reviewed_at,
                Progress.review_count,
                Progress.next_review_date,
            )
            .outerjoin(Progress, Topic.id == Progress.topic_id)
            .order_by(Topic.secao, Topic.subsecao, Topic.codigo)
        )

        results = session.exec(statement).all()

        output = [
            {
                "codigo": row[0],
                "secao": row[1],
                "subsecao": row[2],
                "titulo": row[3],
                "completed_at": row[4],
                "last_reviewed_at": row[5],
                "review_count": row[6] if row[6] else 0,
                "next_review_date": row[7],
            }
            for row in results
        ]

        return output


def unmark_topic_complete(engine: Engine, topic_id: int) -> bool:
    """
    Unmark a topic as completed by setting completed_at to None.

    Args:
        engine: Database engine
        topic_id: ID of the topic to unmark

    Returns:
        True if successful, False if topic/progress not found
    """
    with Session(engine) as session:
        progress = session.get(Progress, topic_id)
        if not progress:
            return False

        progress.completed_at = None
        progress.review_count = 0
        progress.last_reviewed_at = None
        progress.next_review_date = None
        session.add(progress)
        session.commit()
        _invalidate_progress_cache()
        _sync_remote_backup_after_write(engine)
        return True


def get_upcoming_reviews(engine: Engine, days: int = 30) -> list[dict[str, Any]]:
    """
    Get topics scheduled for review in the next N days.

    Args:
        engine: Database engine
        days: Number of days to look ahead (default: 30)

    Returns:
        List of topic dicts with review dates
    """
    today = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    with Session(engine) as session:
        statement = (
            select(Topic, Progress)
            .join(Progress)
            .where(
                Progress.completed_at.is_not(None),
                Progress.next_review_date.is_not(None),
                Progress.next_review_date > today,
                Progress.next_review_date <= end_date,
            )
            .order_by(Progress.next_review_date)
        )

        results = session.exec(statement).all()

        output = []
        for topic, progress in results:
            output.append(
                {
                    "id": topic.id,
                    "codigo": topic.codigo,
                    "secao": topic.secao,
                    "subsecao": topic.subsecao,
                    "titulo": topic.titulo,
                    "next_review_date": progress.next_review_date,
                    "review_count": progress.review_count or 0,
                }
            )

        return output
