"""
Reviews Page - Spaced Repetition System for Study Topics

This page implements a complete review system using the SRS (Spaced Repetition System)
algorithm to optimize learning retention through scheduled reviews.
"""

from datetime import datetime

import streamlit as st

from db import (
    get_all_progress,
    get_topics_due_for_review,
    get_upcoming_reviews,
    mark_review_complete,
)
from session import get_db
from utils import INTERVALS, calculate_next_review, format_date

st.set_page_config(page_title="Revisões - GayATCU", page_icon="📅", layout="wide")


def get_interval_label(days: int) -> str:
    """
    Get a human-readable label for a review interval.

    Args:
        days: Number of days in the interval

    Returns:
        Formatted label string (e.g., "24h", "7d", "15d", "30d")
    """
    if days == 1:
        return "24h"
    return f"{days}d"


def group_by_interval(topics: list) -> dict:
    """
    Group topics by their next review interval.

    Args:
        topics: List of topic dictionaries with next_review_date

    Returns:
        Dictionary with interval labels as keys and topic lists as values
    """
    today = datetime.now().date()
    grouped = {"24h": [], "7d": [], "15d": [], "30d": [], "overdue": []}

    for topic in topics:
        if topic["next_review_date"]:
            review_date = datetime.strptime(
                topic["next_review_date"], "%Y-%m-%d"
            ).date()
            days_until = (review_date - today).days

            if days_until <= 1:
                grouped["24h"].append(topic)
            elif days_until <= 7:
                grouped["7d"].append(topic)
            elif days_until <= 15:
                grouped["15d"].append(topic)
            elif days_until <= 30:
                grouped["30d"].append(topic)
            else:
                grouped["overdue"].append(topic)
        else:
            grouped["24h"].append(topic)

    return grouped


def display_topic_card(topic: dict, key: str, engine):
    """
    Display a topic review card with action buttons.

    Args:
        topic: Topic dictionary with all relevant information
        key: Unique key for the widget
        engine: Database engine
    """
    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**{topic['codigo']} - {topic['titulo']}**")
            st.caption(f"{topic['secao']} > {topic['subsecao']}")
            if topic["last_reviewed_at"]:
                st.caption(f"Última revisão: {format_date(topic['last_reviewed_at'])}")
            else:
                st.caption("Primeira revisão")

        with col2:
            current_level = min(topic["review_count"], len(INTERVALS) - 1)
            next_interval = calculate_next_review(current_level, True)

            if st.button("✓ Concluir", key=f"complete_{key}", use_container_width=True):
                if mark_review_complete(engine, topic["id"], next_interval):
                    st.success("Revisão registrada!")
                    st.rerun()
                else:
                    st.error("Erro ao registrar revisão")

        st.markdown("---")


def display_calendar_view(upcoming: list):
    """
    Display upcoming reviews in a calendar-like format.

    Args:
        upcoming: List of topics with scheduled review dates
    """
    st.subheader("📆 Próximas Revisões")

    if not upcoming:
        st.info("Nenhuma revisão agendada para os próximos 30 dias.")
        return

    # Group by date
    by_date = {}
    for topic in upcoming:
        date_str = topic["next_review_date"]
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(topic)

    # Display each date
    for date_str, topics in sorted(by_date.items()):
        formatted_date = format_date(date_str)
        days_until = (
            datetime.strptime(date_str, "%Y-%m-%d").date() - datetime.now().date()
        ).days

        if days_until == 0:
            date_label = f"📌 **Hoje** ({formatted_date})"
        elif days_until == 1:
            date_label = f"📌 **Amanhã** ({formatted_date})"
        else:
            date_label = f"📌 **Em {days_until} dias** ({formatted_date})"

        with st.expander(date_label):
            for topic in topics:
                st.markdown(f"- **{topic['codigo']}**: {topic['titulo']}")
                st.caption(
                    f"   {topic['secao']} > {topic['subsecao']}"
                    f" • Revisões: {topic['review_count']}"
                )


def main():
    # Initialize database engine
    engine = get_db()

    # Page header
    st.title("📅 Sistema de Revisões")
    st.markdown("Revise os tópicos usando o sistema de repetição espaçada (SRS)")

    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")

    # Load topics due for review
    due_topics = get_topics_due_for_review(engine, today)

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Revisões Pendentes", f"{len(due_topics)}")
    with col2:
        upcoming = get_upcoming_reviews(engine, 7)
        st.metric("Próximos 7 dias", f"{len(upcoming)}")
    with col3:
        all_progress = get_all_progress(engine)
        completed = [p for p in all_progress if p["completed_at"]]
        total_reviews = sum(p["review_count"] for p in completed)
        st.metric("Total de Revisões", f"{total_reviews}")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Fila de Revisão", "📆 Calendário"])

    with tab1:
        if not due_topics:
            st.success("🎉 Nenhuma revisão pendente para hoje!")
            st.info(
                "Tópicos concluídos aparecerão aqui quando "
                "estiverem agendados para revisão."
            )
        else:
            # Group by interval
            grouped = group_by_interval(due_topics)

            # Display each interval group
            interval_order = ["24h", "7d", "15d", "30d", "overdue"]

            for interval in interval_order:
                if grouped[interval]:
                    if interval == "overdue":
                        st.markdown("### ⚠️ Revisões Atrasadas")
                    else:
                        interval_label = get_interval_label(
                            INTERVALS[interval_order.index(interval)]
                        )
                        st.markdown(f"### Intervalo: {interval_label}")

                    for idx, topic in enumerate(grouped[interval]):
                        display_topic_card(topic, f"{interval}_{idx}", engine)

                    st.markdown("<br>", unsafe_allow_html=True)

    with tab2:
        # Show calendar view of upcoming reviews
        all_upcoming = get_upcoming_reviews(engine, 30)
        display_calendar_view(all_upcoming)

        # Statistics about review distribution
        st.markdown("---")
        st.subheader("📊 Estatísticas de Revisão")

        if all_upcoming:
            # Calculate distribution
            distribution = {}
            for topic in all_upcoming:
                review_date = datetime.strptime(
                    topic["next_review_date"], "%Y-%m-%d"
                ).date()
                week_num = review_date.isocalendar()[1]
                week_label = f"Semana {week_num}"

                if week_label not in distribution:
                    distribution[week_label] = 0
                distribution[week_label] += 1

            # Display as simple stats
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Média por dia", f"{len(all_upcoming) / 30:.1f}")
            with col2:
                st.metric(
                    "Pico semanal",
                    f"{max(distribution.values()) if distribution else 0}",
                )
        else:
            st.info("Sem revisões agendadas para os próximos 30 dias.")

    # Sidebar with SRS information
    with st.sidebar:
        st.markdown("### ℹ️ Como Funciona")
        st.markdown("""
        **Sistema de Repetição Espaçada (SRS)**

        O algoritmo ajusta o intervalo de revisão baseado no seu desempenho:

        1. **24h** → Primeira revisão
        2. **7d** → Segunda revisão (se acertar)
        3. **15d** → Terceira revisão (se acertar)
        4. **30d** → Revisões seguintes (se acertar)

        Ao errar, o intervalo reinicia para **24h**.
        """)

        st.markdown("---")

        st.markdown("### 📈 Intervalos")
        for idx, interval in enumerate(INTERVALS):
            label = get_interval_label(interval)
            level_desc = [
                "Primeira revisão",
                "Consolidação",
                "Reforço intermediário",
                "Revisão de longo prazo",
            ][idx]
            st.markdown(f"**{label}**: {level_desc}")

        st.markdown("---")

        st.markdown("### 💡 Dicas")
        st.markdown("""
        - Revise sempre que possível
        - Seja honesto sobre seu aprendizado
        - Tópicos difíceis reaparecerão com mais frequência
        - A constância é a chave do aprendizado eficaz
        """)


if __name__ == "__main__":
    main()
