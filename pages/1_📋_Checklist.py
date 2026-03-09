"""
Checklist page for tracking study progress.

Displays all topics from conteudo.json with checkboxes to mark completion.
Progress is synced with the database and completion percentages are shown
per subsection.
"""

import streamlit as st

from db import get_all_progress, mark_topic_complete, unmark_topic_complete
from session import SessionStateManager, get_db
from utils import load_content

st.set_page_config(page_title="Checklist", page_icon="📋", layout="wide")


@st.dialog("Confirmar Conclusão")
def confirm_completion(topic_title: str, topic_id: int):
    """Exibir diálogo de confirmação antes de marcar como concluído."""
    st.write(f"Tem certeza que deseja marcar **{topic_title}** como concluído?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar", type="primary", key=f"confirm_yes_{topic_id}"):
            SessionStateManager.set_confirm_state(topic_id, True)
            st.rerun()
    with col2:
        if st.button("❌ Cancelar", key=f"confirm_no_{topic_id}"):
            SessionStateManager.set_confirm_state(topic_id, False)
            st.rerun()


def get_subsection_completion(progress_data, section_title, subsection_title):
    """
    Calculate completion percentage for a subsection.

    Args:
        progress_data: List of all topic progress from database
        section_title: Title of the section
        subsection_title: Title of the subsection

    Returns:
        Tuple of (completed_count, total_count, percentage)
    """
    subsection_topics = [
        p
        for p in progress_data
        if p["secao"] == section_title and p["subsecao"] == subsection_title
    ]

    total = len(subsection_topics)
    if total == 0:
        return 0, 0, 0.0

    completed = sum(1 for p in subsection_topics if p["completed_at"] is not None)
    percentage = (completed / total) * 100.0

    return completed, total, percentage


def main():
    st.title("📋 Checklist de Estudos")

    # Get database engine from centralized session module
    engine = get_db()

    # Load content from JSON
    try:
        content = load_content()
    except FileNotFoundError:
        st.error("Arquivo conteudo.json não encontrado. Execute a importação primeiro.")
        return

    # Get all progress data from database
    progress_data = get_all_progress(engine)

    # Create a dictionary for quick lookup of completion status
    completion_status = {p["id"]: p["completed_at"] is not None for p in progress_data}

    # Create lookup dictionary for O(1) topic ID search (fixes N+1 query problem)
    # Key: (codigo, secao, subsecao, titulo) -> Value: topic_id
    progress_lookup = {
        (p["codigo"], p["secao"], p["subsecao"], p["titulo"]): p["id"]
        for p in progress_data
    }

    # Track if any checkboxes changed
    if "checkbox_states" not in st.session_state:
        st.session_state.checkbox_states = {}

    # Display sections and subsections
    for section in content:
        with st.expander(f"📚 {section['titulo']}", expanded=False):
            for subsection in section.get("subsecoes", []):
                subsection_title = subsection["titulo"]

                # Calculate completion percentage for this subsection
                completed, total, percentage = get_subsection_completion(
                    progress_data, section["titulo"], subsection_title
                )

                # Display subsection header with progress
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"📖 {subsection_title}")
                with col2:
                    st.metric("% Concluído", f"{percentage:.1f}%")

                # Progress bar for subsection
                if total > 0:
                    st.progress(percentage / 100)
                    st.caption(f"{completed} de {total} tópicos concluídos")

                st.markdown("---")

                # Display topics with checkboxes
                for topic_idx, topic in enumerate(subsection.get("topicos", [])):
                    # Find the topic ID using O(1) lookup (fixes N+1 query problem)
                    lookup_key = (
                        topic["codigo"],
                        section["titulo"],
                        subsection_title,
                        topic["titulo"],
                    )
                    topic_id = progress_lookup.get(lookup_key)

                    if topic_id is None:
                        st.warning(
                            f"Tópico não encontrado no banco: "
                            f"{topic['codigo']} - {topic['titulo']}"
                        )
                        continue

                    # Get current completion status
                    is_completed = completion_status.get(topic_id, False)

                    # Unique key for checkbox using index
                    # to avoid duplicates
                    checkbox_key = (
                        f"topic_{topic_id}_{topic_idx}_{subsection_title[:20]}"
                    )

                    # Display checkbox with topic title
                    col_check, col_text = st.columns([1, 12])
                    with col_check:
                        new_state = st.checkbox(
                            "",
                            value=is_completed,
                            key=checkbox_key,
                            label_visibility="collapsed",
                        )
                    with col_text:
                        # Format topic display
                        topic_display = f"**{topic['codigo']}** - {topic['titulo']}"
                        st.markdown(topic_display)

                    # Check if checkbox state changed
                    if new_state != is_completed:
                        if new_state:
                            # Check if already confirmed
                            if not SessionStateManager.get_confirm_state(topic_id):
                                # Show confirmation dialog
                                confirm_completion(topic['titulo'], topic_id)
                            else:
                                # Mark as complete
                                if mark_topic_complete(engine, topic_id):
                                    st.success(
                                        f"✓ Marcado como concluído: {topic['titulo']}"
                                    )
                                    completion_status[topic_id] = True
                                    SessionStateManager.clear_confirm_state(topic_id)
                        else:
                            # Unmark completion via ORM (no confirmation needed)
                            if unmark_topic_complete(engine, topic_id):
                                st.info(f"○ Desmarcado: {topic['titulo']}")
                                completion_status[topic_id] = False

                        # Force rerun to update UI
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
