"""
SQLite database layer for study tracker application.

All database operations use parameterized queries with ? placeholders
to prevent SQL injection. User input is never interpolated directly
into SQL strings.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def init_db(db_path: str = "data/study_tracker.db") -> sqlite3.Connection:
    """
    Initialize the SQLite database with required tables and indexes.

    Creates the database file and directory structure if they don't exist.
    Sets up all tables with proper constraints and performance indexes.

    Args:
        db_path: Path to the SQLite database file. Defaults to "data/study_tracker.db"

    Returns:
        sqlite3.Connection: Active database connection with row factory enabled

    Raises:
        sqlite3.Error: If database initialization fails
    """
    # Ensure data directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows

    cursor = conn.cursor()

    # Create topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            secao TEXT NOT NULL,
            subsecao TEXT NOT NULL,
            titulo TEXT NOT NULL,
            UNIQUE(codigo, secao, subsecao)
        )
    """)

    # Create progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            topic_id INTEGER PRIMARY KEY,
            completed_at TIMESTAMP,
            last_reviewed_at TIMESTAMP,
            review_count INTEGER DEFAULT 0,
            next_review_date DATE,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Create review_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            interval_days INTEGER,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)

    # Create performance indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_next_review ON progress(next_review_date)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo ON topics(codigo)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_secao_subsecao ON topics(secao, subsecao)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_topic_id_progress ON progress(topic_id)"
    )

    conn.commit()
    return conn


def import_topics_from_json(
    conn: sqlite3.Connection, json_path: str = "conteudo.json"
) -> int:
    """
    Import topics from JSON file into the database.

    The JSON file is expected to be an array of sections, where each section
    has subsecoes, and each subsecao has topicos with codigo and titulo.

    Uses INSERT OR IGNORE to handle duplicates gracefully.

    Args:
        conn: Active database connection
        json_path: Path to the JSON file. Defaults to "conteudo.json"

    Returns:
        int: Number of topics successfully imported

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is malformed
        sqlite3.Error: If database operation fails
    """
    with open(json_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    cursor = conn.cursor()
    imported_count = 0

    # Iterate over the array of sections
    for section in sections:
        secao_titulo = section.get("titulo", "")

        # Process each subsection within the section
        for subsecao in section.get("subsecoes", []):
            subsecao_titulo = subsecao.get("titulo", "")

            # Process each topic within the subsection
            for topico in subsecao.get("topicos", []):
                codigo = topico.get("codigo", "")
                titulo = topico.get("titulo", "")

                # Use parameterized query to prevent SQL injection
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO topics (codigo, secao, subsecao, titulo)
                    VALUES (?, ?, ?, ?)
                """,
                    (codigo, secao_titulo, subsecao_titulo, titulo),
                )

                if cursor.rowcount > 0:
                    imported_count += 1

    conn.commit()
    return imported_count


def mark_topic_complete(conn: sqlite3.Connection, topic_id: int) -> bool:
    """
    Mark a topic as completed with current timestamp.

    Creates a new progress record if one doesn't exist, or updates
    the existing record's completion timestamp.

    Args:
        conn: Active database connection
        topic_id: ID of the topic to mark complete

    Returns:
        bool: True if successful, False if topic_id doesn't exist
    """
    cursor = conn.cursor()
    dt_now = datetime.now()
    now_iso = dt_now.isoformat()
    next_review = (dt_now + timedelta(days=1)).strftime("%Y-%m-%d")

    # Check if topic exists
    cursor.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
    if cursor.fetchone() is None:
        return False

    # Insert or update progress record
    cursor.execute(
        """
        INSERT INTO progress (topic_id, completed_at, next_review_date, last_reviewed_at, review_count)
        VALUES (?, ?, ?, NULL, 0)
        ON CONFLICT(topic_id) DO UPDATE SET
            completed_at = COALESCE(progress.completed_at, excluded.completed_at)
    """,
        (topic_id, now_iso, next_review),
    )

    conn.commit()
    return True


def get_topic_progress(
    conn: sqlite3.Connection, topic_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get detailed progress information for a specific topic.

    Args:
        conn: Active database connection
        topic_id: ID of the topic

    Returns:
        Dictionary with topic details and progress info, or None if not found
        Keys include: id, codigo, secao, subsecao, titulo, completed_at,
                     last_reviewed_at, review_count, next_review_date
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.id, t.codigo, t.secao, t.subsecao, t.titulo,
            p.completed_at, p.last_reviewed_at, p.review_count, p.next_review_date
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        WHERE t.id = ?
    """,
        (topic_id,),
    )

    row = cursor.fetchone()
    if row is None:
        return None

    return {
        "id": row["id"],
        "codigo": row["codigo"],
        "secao": row["secao"],
        "subsecao": row["subsecao"],
        "titulo": row["titulo"],
        "completed_at": row["completed_at"],
        "last_reviewed_at": row["last_reviewed_at"],
        "review_count": row["review_count"] or 0,
        "next_review_date": row["next_review_date"],
    }


def get_all_progress(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Get progress information for all topics in the database.

    Returns topics grouped by section and subsection, including completion
    status and review information.

    Args:
        conn: Active database connection

    Returns:
        List of dictionaries, each representing a topic with its progress
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.id, t.codigo, t.secao, t.subsecao, t.titulo,
            p.completed_at, p.last_reviewed_at, p.review_count, p.next_review_date
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        ORDER BY t.secao, t.subsecao, t.codigo
    """)

    results = []
    for row in cursor.fetchall():
        results.append(
            {
                "id": row["id"],
                "codigo": row["codigo"],
                "secao": row["secao"],
                "subsecao": row["subsecao"],
                "titulo": row["titulo"],
                "completed_at": row["completed_at"],
                "last_reviewed_at": row["last_reviewed_at"],
                "review_count": row["review_count"] or 0,
                "next_review_date": row["next_review_date"],
            }
        )

    return results


def get_topics_due_for_review(
    conn: sqlite3.Connection, date: str
) -> List[Dict[str, Any]]:
    """
    Get all topics that are due for review on or before the given date.

    Filters for topics where next_review_date is NULL or <= given date.

    Args:
        conn: Active database connection
        date: Date string in YYYY-MM-DD format

    Returns:
        List of dictionaries with topic and progress information
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.id, t.codigo, t.secao, t.subsecao, t.titulo,
            p.completed_at, p.last_reviewed_at, p.review_count, p.next_review_date
        FROM topics t
        INNER JOIN progress p ON t.id = p.topic_id
        WHERE p.completed_at IS NOT NULL
          AND (p.next_review_date IS NULL OR p.next_review_date <= ?)
        ORDER BY p.next_review_date, t.secao, t.subsecao
    """,
        (date,),
    )

    results = []
    for row in cursor.fetchall():
        results.append(
            {
                "id": row["id"],
                "codigo": row["codigo"],
                "secao": row["secao"],
                "subsecao": row["subsecao"],
                "titulo": row["titulo"],
                "completed_at": row["completed_at"],
                "last_reviewed_at": row["last_reviewed_at"],
                "review_count": row["review_count"] or 0,
                "next_review_date": row["next_review_date"],
            }
        )

    return results


def mark_review_complete(
    conn: sqlite3.Connection, topic_id: int, interval: int
) -> bool:
    """
    Mark a review as complete and schedule the next review date.

    Records the review in the review_log, updates the progress record,
    and calculates the next review date using the spaced repetition interval.

    Args:
        conn: Active database connection
        topic_id: ID of the topic being reviewed
        interval: Number of days until next review (spaced repetition interval)

    Returns:
        bool: True if successful, False if topic_id doesn't exist or not completed
    """
    cursor = conn.cursor()
    now = datetime.now()

    # Check if topic exists and is completed
    cursor.execute(
        """
        SELECT p.completed_at FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        WHERE t.id = ?
    """,
        (topic_id,),
    )

    result = cursor.fetchone()
    if result is None or result["completed_at"] is None:
        return False

    # Calculate next review date
    next_review = (now + timedelta(days=interval)).strftime("%Y-%m-%d")
    now_iso = now.isoformat()

    # Log this review
    cursor.execute(
        """
        INSERT INTO review_log (topic_id, reviewed_at, interval_days)
        VALUES (?, ?, ?)
    """,
        (topic_id, now_iso, interval),
    )

    # Update progress record
    cursor.execute(
        """
        UPDATE progress
        SET last_reviewed_at = ?,
            review_count = review_count + 1,
            next_review_date = ?
        WHERE topic_id = ?
    """,
        (now_iso, next_review, topic_id),
    )

    conn.commit()
    return True


def get_statistics(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calculate and return overall study statistics.

    Provides metrics on total topics, completion status, review activity,
    and upcoming review workload.

    Args:
        conn: Active database connection

    Returns:
        Dictionary containing:
        - total_topics: Total number of topics in database
        - completed_topics: Number of topics marked as complete
        - pending_topics: Number of topics not yet started
        - total_reviews: Total number of reviews completed
        - due_today: Number of topics due for review today
        - completion_rate: Percentage of topics completed (0-100)
    """
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    # Total topics
    cursor.execute("SELECT COUNT(*) as count FROM topics")
    total_topics = cursor.fetchone()["count"]

    # Completed topics
    cursor.execute(
        "SELECT COUNT(*) as count FROM progress WHERE completed_at IS NOT NULL"
    )
    completed_topics = cursor.fetchone()["count"]

    # Total reviews completed
    cursor.execute("SELECT SUM(review_count) as total FROM progress")
    total_reviews = cursor.fetchone()["total"] or 0

    # Topics due for review today
    cursor.execute(
        """
        SELECT COUNT(*) as count FROM progress
        WHERE completed_at IS NOT NULL
          AND (next_review_date IS NULL OR next_review_date <= ?)
    """,
        (today,),
    )
    due_today = cursor.fetchone()["count"]

    # Calculate completion rate
    completion_rate = (completed_topics / total_topics * 100) if total_topics > 0 else 0

    return {
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "pending_topics": total_topics - completed_topics,
        "total_reviews": total_reviews,
        "due_today": due_today,
        "completion_rate": round(completion_rate, 2),
    }
