"""
Session management module for GayATCU dashboard.

Provides centralized database connection management and caching
following Streamlit best practices.
"""

import logging
from typing import Any

import streamlit as st
from sqlalchemy import func
from sqlmodel import Session, select

from db import Topic, import_topics_from_json, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection() -> Any:
    """
    Get a database connection with thread safety enabled.

    This function creates a new connection each time to avoid threading issues.
    The connection is cached in st.session_state to reuse within the same session.

    Returns:
        Any: Active database engine
    """
    try:
        # Create connection and automatically initialize schema and directories
        engine = init_db("data/study_tracker.db")
        logger.info("Database connection established")
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise


def get_db() -> Any:
    """
    Get database engine from session state or create new one.

    This is the preferred method for getting data layer connections
    in GayATCU applications. It uses session state caching to avoid
    creating multiple connections per script run.

    Returns:
        Any: Active database engine
    """
    try:
        # Use session state to cache connection within the same script run
        if "db_connection" not in st.session_state:
            st.session_state.db_connection = get_db_connection()

        return st.session_state.db_connection
    except Exception as e:
        logger.error(f"Error getting database connection: {e}")
        st.error(f"Erro ao obter conexão com banco: {e}")
        # Fallback: create new connection
        return get_db_connection()


def initialize_database() -> bool:
    """
    Initialize the database schema and import data if needed.

    This function should be called once at application startup to ensure:
    - Database tables are created
    - Indexes are established
    - Study content is imported from conteudo.json

    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        engine = get_db()

        # Check if database already has data
        with Session(engine) as session:
            topic_count = session.exec(select(func.count(Topic.id))).first() or 0

        if topic_count == 0:
            logger.info("Database empty, importing topics from conteudo.json")

            imported = import_topics_from_json(engine)
            logger.info(f"Imported {imported} topics successfully")
            return True
        else:
            logger.info(f"Database already contains {topic_count} topics")
            return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        st.error(f"Erro ao inicializar banco de dados: {e}")
        return False


def safe_db_operation(operation_func, default_value=None):
    """
    Decorator for safe database operations with error handling.

    Args:
        operation_func: Function that performs database operation
        default_value: Value to return if operation fails

    Returns:
        Result of operation or default_value on failure
    """

    def wrapper(*args, **kwargs):
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            st.warning(f"Erro inesperado: {e}")
            return default_value

    return wrapper


class SessionStateManager:
    """Gerenciador centralizado de st.session_state."""

    COMPLETED_PREFIX = "topic_completed_"
    CONFIRM_PREFIX = "confirm_"
    EXPANDER_PREFIX = "expander_"

    @staticmethod
    def set_topic_completed(topic_id: int, completed: bool):
        """Define estado de conclusão do tópico."""
        key = f"{SessionStateManager.COMPLETED_PREFIX}{topic_id}"
        st.session_state[key] = completed

    @staticmethod
    def is_topic_completed(topic_id: int) -> bool:
        """Verifica se tópico está concluído."""
        key = f"{SessionStateManager.COMPLETED_PREFIX}{topic_id}"
        return st.session_state.get(key, False)

    @staticmethod
    def set_expander_state(section_id: str, expanded: bool):
        """Define estado de expander."""
        key = f"{SessionStateManager.EXPANDER_PREFIX}{section_id}"
        st.session_state[key] = expanded

    @staticmethod
    def get_expander_state(section_id: str) -> bool:
        """Obtém estado de expander."""
        key = f"{SessionStateManager.EXPANDER_PREFIX}{section_id}"
        return st.session_state.get(key, False)

    @staticmethod
    def set_confirm_state(topic_id: int, confirmed: bool):
        """Define estado de confirmação para diálogos."""
        key = f"{SessionStateManager.CONFIRM_PREFIX}{topic_id}"
        st.session_state[key] = confirmed

    @staticmethod
    def get_confirm_state(topic_id: int) -> bool:
        """Obtém estado de confirmação para diálogos."""
        key = f"{SessionStateManager.CONFIRM_PREFIX}{topic_id}"
        return st.session_state.get(key, False)

    @staticmethod
    def clear_confirm_state(topic_id: int):
        """Limpa estado de confirmação após uso."""
        key = f"{SessionStateManager.CONFIRM_PREFIX}{topic_id}"
        if key in st.session_state:
            del st.session_state[key]
