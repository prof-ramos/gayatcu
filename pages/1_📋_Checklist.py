"""
Checklist page for tracking study progress.

Displays all topics from conteudo.json with checkboxes to mark completion.
Progress is synced with the database and completion percentages are shown
per subsection.
"""

import streamlit as st
from session import get_db
from db import mark_topic_complete, get_topic_progress, get_all_progress
from utils import load_content

st.set_page_config(page_title="Checklist", page_icon="📋", layout="wide")


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
        p for p in progress_data
        if p['secao'] == section_title and p['subsecao'] == subsection_title
    ]

    total = len(subsection_topics)
    if total == 0:
        return 0, 0, 0.0

    completed = sum(1 for p in subsection_topics if p['completed_at'] is not None)
    percentage = (completed / total) * 100.0

    return completed, total, percentage


def main():
    st.title("📋 Checklist de Estudos")

    # Get database connection from centralized session module
    conn = get_db()

    # Load content from JSON
    try:
        content = load_content()
    except FileNotFoundError:
        st.error("Arquivo conteudo.json não encontrado. Execute a importação primeiro.")
        return

    # Get all progress data from database
    progress_data = get_all_progress(conn)

    # Create a dictionary for quick lookup of completion status
    completion_status = {
        p['id']: p['completed_at'] is not None
        for p in progress_data
    }

    # Track if any checkboxes changed
    if 'checkbox_states' not in st.session_state:
        st.session_state.checkbox_states = {}

    # Display sections and subsections
    for section in content:
        with st.expander(f"📚 {section['titulo']}", expanded=False):
            for subsection in section.get('subsecoes', []):
                subsection_title = subsection['titulo']

                # Calculate completion percentage for this subsection
                completed, total, percentage = get_subsection_completion(
                    progress_data, section['titulo'], subsection_title
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
                for topic_idx, topic in enumerate(subsection.get('topicos', [])):
                    # Find the topic ID from progress data
                    topic_id = None
                    for p in progress_data:
                        if (p['codigo'] == topic['codigo'] and
                            p['secao'] == section['titulo'] and
                            p['subsecao'] == subsection_title and
                            p['titulo'] == topic['titulo']):
                            topic_id = p['id']
                            break

                    if topic_id is None:
                        st.warning(f"Tópico não encontrado no banco: {topic['codigo']} - {topic['titulo']}")
                        continue

                    # Get current completion status
                    is_completed = completion_status.get(topic_id, False)

                    # Create a unique key for the checkbox using index to avoid duplicates
                    checkbox_key = f"topic_{topic_id}_{topic_idx}_{subsection_title[:20]}"

                    # Display checkbox with topic title
                    col_check, col_text = st.columns([1, 12])
                    with col_check:
                        new_state = st.checkbox(
                            "",
                            value=is_completed,
                            key=checkbox_key,
                            label_visibility="collapsed"
                        )
                    with col_text:
                        # Format topic display
                        topic_display = f"**{topic['codigo']}** - {topic['titulo']}"
                        st.markdown(topic_display)

                    # Check if checkbox state changed
                    if new_state != is_completed:
                        if new_state:
                            # Mark as complete
                            if mark_topic_complete(conn, topic_id):
                                st.success(f"✓ Marcado como concluído: {topic['titulo']}")
                                completion_status[topic_id] = True
                        else:
                            # Unmark completion (delete from progress)
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE progress SET completed_at = NULL WHERE topic_id = ?",
                                (topic_id,)
                            )
                            conn.commit()
                            st.info(f"○ Desmarcado: {topic['titulo']}")
                            completion_status[topic_id] = False

                        # Force rerun to update UI
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
