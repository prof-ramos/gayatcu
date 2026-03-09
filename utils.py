import json
import datetime
import sqlite3
from typing import Optional, List, Dict, Any


INTERVALS = [1, 7, 15, 30]


def load_content(json_path: str = "conteudo.json") -> Dict[str, Any]:
    """
    Load and validate JSON content from file.

    Args:
        json_path: Path to the JSON file (default: "conteudo.json")

    Returns:
        Parsed JSON content as a dictionary

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    return content


def calculate_next_review(current_level: int, success: bool) -> int:
    """
    Calculate the next review interval based on SRS (Spaced Repetition System) algorithm.

    Args:
        current_level: Current mastery level (0-3, corresponding to INTERVALS indices)
        success: Whether the user answered correctly

    Returns:
        Number of days until next review

    Algorithm:
        - If correct: Advance to next level (max level 3 = 30 days)
        - If incorrect: Reset to level 0 (1 day)
    """
    if success:
        # Advance to next level, maxing out at the longest interval
        next_level = min(current_level + 1, len(INTERVALS) - 1)
        return INTERVALS[next_level]
    else:
        # Reset to beginning on failure
        return INTERVALS[0]


def format_date(date_str: Optional[str]) -> str:
    """
    Format a date string to Portuguese locale (DD/MM/YYYY).

    Args:
        date_str: ISO format date string (YYYY-MM-DD) or None

    Returns:
        Formatted date string in Portuguese format, or empty string if None
    """
    if not date_str:
        return ""

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""


def get_completion_percentage(conn: sqlite3.Connection) -> float:
    """
    Calculate the overall completion percentage of all topics.

    Args:
        conn: SQLite database connection

    Returns:
        Percentage of topics completed (0.0 to 100.0), or 0.0 if no topics exist
    """
    cursor = conn.cursor()

    # Get total topics and completed topics
    cursor.execute("SELECT COUNT(*) FROM topics")
    total = cursor.fetchone()[0]

    if total == 0:
        return 0.0

    cursor.execute("SELECT COUNT(*) FROM progress WHERE completed_at IS NOT NULL")
    completed = cursor.fetchone()[0]

    return (completed / total) * 100.0


def get_section_progress(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Calculate progress statistics grouped by section.

    Args:
        conn: SQLite database connection

    Returns:
        List of dictionaries containing:
        - 'section': Section name
        - 'total': Total topics in section
        - 'answered': Number of completed topics
        - 'percentage': Completion percentage (0.0 to 100.0)
    """
    cursor = conn.cursor()

    # Get progress per section
    cursor.execute("""
        SELECT
            t.secao as section,
            COUNT(*) as total,
            SUM(CASE WHEN p.completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        GROUP BY t.secao
        ORDER BY t.secao
    """)

    results = []
    for row in cursor.fetchall():
        section, total, completed = row
        percentage = (completed / total * 100.0) if total > 0 else 0.0
        results.append({
            'section': section,
            'total': total,
            'completed': completed,
            'percentage': percentage
        })

    return results
