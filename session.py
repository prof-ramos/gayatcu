"""
Session management module for GayATCU dashboard.

Provides centralized database connection management and caching
following Streamlit best practices.
"""

import streamlit as st
import sqlite3
import logging
from typing import Optional
from db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    """
    Get a database connection with thread safety enabled.

    This function creates a new connection each time to avoid threading issues.
    The connection is cached in st.session_state to reuse within the same session.

    Returns:
        sqlite3.Connection: Active database connection with row factory enabled
    """
    try:
        conn = sqlite3.connect("data/study_tracker.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        logger.info("Database connection established")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise


def get_db() -> sqlite3.Connection:
    """
    Get database connection from session state or create new one.

    This is the preferred method for getting database connections
    in GayATCU applications. It uses session state caching to avoid
    creating multiple connections per script run.

    Returns:
        sqlite3.Connection: Active database connection
    """
    try:
        # Use session state to cache connection within the same script run
        if 'db_connection' not in st.session_state:
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
        conn = get_db()

        # Check if database already has data
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM topics")
        topic_count = cursor.fetchone()[0]

        if topic_count == 0:
            logger.info("Database empty, importing topics from conteudo.json")
            from db import import_topics_from_json
            imported = import_topics_from_json(conn)
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
        except sqlite3.Error as e:
            logger.error(f"Database operation error: {e}")
            st.warning(f"Erro de banco de dados: {e}")
            return default_value
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            st.warning(f"Erro inesperado: {e}")
            return default_value
    return wrapper
