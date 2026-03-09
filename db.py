"""
SQLite database layer for study tracker application.

Refactored to use SQLModel ORM.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from sqlalchemy import UniqueConstraint, func
from sqlmodel import Field, Session, SQLModel, create_engine, select

# --- Models ---


class Topic(SQLModel, table=True):
    __tablename__ = "topics"
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True)
    secao: str = Field(index=True)
    subsecao: str
    titulo: str

    __table_args__ = (UniqueConstraint("codigo", "secao", "subsecao"),)


class Progress(SQLModel, table=True):
    __tablename__ = "progress"
    topic_id: int = Field(primary_key=True, foreign_key="topics.id")
    completed_at: Optional[str] = None
    last_reviewed_at: Optional[str] = None
    review_count: int = Field(default=0)
    next_review_date: Optional[str] = Field(default=None, index=True)


class ReviewLog(SQLModel, table=True):
    __tablename__ = "review_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="topics.id")
    reviewed_at: str
    interval_days: int


# --- Engine ---


def init_db(db_path: str = "data/study_tracker.db") -> Any:
    """
    Initialize the SQLite database with required tables and indexes.
    Returns the SQLAlchemy engine.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

    SQLModel.metadata.create_all(engine)
    return engine


def import_topics_from_json(engine: Any, json_path: str = "conteudo.json") -> int:
    """
    Import topics from JSON file into the database.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    imported_count = 0

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

        session.commit()

    return imported_count


def mark_topic_complete(engine: Any, topic_id: int) -> bool:
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
        return True


def get_topic_progress(engine: Any, topic_id: int) -> Optional[Dict[str, Any]]:
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


@st.cache_data(ttl=60)  # Cache por 1 minuto para dados dinâmicos
def get_all_progress(engine: Any) -> List[Dict[str, Any]]:
    """
    Get progress information for all topics in the database.
    """
    with Session(engine) as session:
        statement = (
            select(Topic, Progress)
            .join(Progress, isouter=True)
            .order_by(Topic.secao, Topic.subsecao, Topic.codigo)
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
                    "completed_at": progress.completed_at if progress else None,
                    "last_reviewed_at": progress.last_reviewed_at if progress else None,
                    "review_count": progress.review_count if progress else 0,
                    "next_review_date": progress.next_review_date if progress else None,
                }
            )
        return output


def get_topics_due_for_review(engine: Any, date: str) -> List[Dict[str, Any]]:
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


def mark_review_complete(engine: Any, topic_id: int, interval: int) -> bool:
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
        return True


def get_statistics(engine: Any) -> Dict[str, Any]:
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


def get_detailed_statistics_by_section(engine: Any) -> List[Dict[str, Any]]:
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
                func.sum(
                    func.case((Progress.completed_at.is_not(None), 1), else_=0)
                ).label("completed"),
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


def get_weekly_review_data(engine: Any, weeks: int = 12) -> List[Dict[str, Any]]:
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
        # Calculate the date N weeks ago
        from datetime import timedelta

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


def get_topic_distribution_by_section(engine: Any) -> List[Dict[str, Any]]:
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


def export_all_progress_to_dict(engine: Any) -> List[Dict[str, Any]]:
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


def unmark_topic_complete(engine: Any, topic_id: int) -> bool:
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
        session.add(progress)
        session.commit()
        return True


def get_upcoming_reviews(engine: Any, days: int = 30) -> List[Dict[str, Any]]:
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
