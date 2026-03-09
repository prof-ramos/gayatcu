import streamlit as st

from db import get_statistics
from session import get_db, initialize_database
from utils import get_completion_percentage, get_section_progress

st.set_page_config(page_title="Teste - GayATCU", page_icon="📘", layout="wide")


def main():
    st.title("📘 Teste - GayATCU Dashboard")

    # Initialize database and import data if needed
    initialize_database()

    # Get database connection
    db = get_db()

    # Calculate metrics using database
    try:
        stats = get_statistics(db)
        total_topics = stats.get("total_topics", 0)
    except Exception:
        total_topics = 0

    try:
        completion_pct = get_completion_percentage(db)
    except Exception:
        completion_pct = 0.0

    try:
        section_progress = get_section_progress(db)
    except Exception:
        section_progress = []

    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Total Topics: {total_topics}")
    logger.debug(f"Completion %: {completion_pct}")
    logger.debug(f"Sections: {len(section_progress)}")

    # Main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Tópicos", value=f"{total_topics}")
    with col2:
        st.metric(label="Conclusão Geral", value=f"{completion_pct:.1f}%")
    with col3:
        st.metric(label="Seções", value=f"{len(section_progress)}")

    st.markdown("---")

    # Overall progress bar
    st.subheader("Progresso Geral")
    st.progress(max(0.0, min(1.0, completion_pct / 100.0)))
    st.markdown("<br>", unsafe_allow_html=True)

    # Progress by section
    st.subheader("Progresso por Seção")

    for section_data in section_progress:
        section = section_data["section"]
        total = section_data["total"]
        completed = section_data["completed"]
        pct = section_data["percentage"]

        st.write(f"**{section}**")
        st.progress(max(0.0, min(1.0, pct / 100.0)))
        st.markdown(
            f"<small>{completed}/{total} ({pct:.1f}%)</small><br>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
