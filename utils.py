import datetime
import json
import logging
from typing import Any

import streamlit as st
from sqlalchemy import Engine, case, func
from sqlmodel import Session, select

from db import Progress, Topic

logger = logging.getLogger(__name__)

INTERVALS = [1, 7, 15, 30]


@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_content(json_path: str = "conteudo.json") -> list:
    """
    Load and validate JSON content from file.

    Validates that the JSON is a list of sections, each containing
    'titulo' and 'subsecoes' keys with proper structure.

    Args:
        json_path: Path to the JSON file.

    Returns:
        List of section dictionaries.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If the JSON structure is invalid.
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Arquivo JSON inválido em '%s': %s", json_path, e)
        raise ValueError(f"Arquivo JSON inválido: {e}") from e

    if not isinstance(content, list):
        raise ValueError(
            f"Esperado lista de seções no JSON, obtido {type(content).__name__}"
        )

    if len(content) == 0:
        logger.warning("Arquivo JSON '%s' está vazio", json_path)

    for idx, section in enumerate(content):
        if not isinstance(section, dict):
            raise ValueError(f"Seção {idx} não é um dicionário")
        if "titulo" not in section:
            raise ValueError(f"Seção {idx} não possui campo 'titulo'")
        if "subsecoes" not in section:
            logger.warning(
                "Seção '%s' não possui campo 'subsecoes'",
                section.get("titulo", f"idx={idx}"),
            )

    return content


def calculate_next_review(current_level: int, success: bool) -> int:
    """
    Calculate the next review interval based on SRS (Spaced Repetition System) algorithm.
    """
    if success:
        next_level = min(current_level + 1, len(INTERVALS) - 1)
        return INTERVALS[next_level]
    else:
        return INTERVALS[0]


def format_date(date_str: str | None) -> str:
    """
    Format a date string to Portuguese locale (DD/MM/YYYY).
    """
    if not date_str:
        return ""

    try:
        if "T" in date_str:
            date_obj = datetime.datetime.fromisoformat(date_str).date()
        else:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""


def get_completion_percentage(engine: Engine) -> float:
    """
    Calculate the overall completion percentage of all topics.
    """
    with Session(engine) as session:
        total = session.exec(select(func.count(Topic.id))).first() or 0
        if total == 0:
            return 0.0

        completed = (
            session.exec(
                select(func.count(Progress.topic_id)).where(
                    Progress.completed_at.is_not(None)
                )
            ).first()
            or 0
        )

        return (completed / total) * 100.0


def get_section_progress(engine: Engine) -> list[dict[str, Any]]:
    """
    Calculate progress statistics grouped by section.
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
            .join(Progress, isouter=True)
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
                    "section": secao,
                    "total": total,
                    "completed": completed_val,
                    "percentage": percentage,
                }
            )

        return output
