import pandas as pd
import streamlit as st

from db import get_statistics
from session import get_db, initialize_database
from utils import get_completion_percentage, get_section_progress
from components import create_donut_chart

st.set_page_config(
    page_title="GayATCU - Dashboard de Estudos TCU", page_icon="📘", layout="wide"
)


def main():
    # Initialize database and import data if needed
    initialize_database()

    # Get database connection
    db = get_db()

    # Calculate metrics using database
    try:
        stats = get_statistics(db)
        total_topics = stats.get("total_topics", 0)
        completed_topics = stats.get("completed_topics", 0)
    except Exception:
        total_topics = 0
        completed_topics = 0

    try:
        completion_pct = get_completion_percentage(db)
    except Exception:
        completion_pct = 0.0

    try:
        section_progress = get_section_progress(db)
    except Exception:
        section_progress = []

    # Dashboard title
    st.title("📘 GayATCU - Dashboard de Estudos TCU")

    # Main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Tópicos", value=f"{total_topics}")
    with col2:
        st.metric(label="Conclusão Geral", value=f"{completion_pct:.1f}%")
    with col3:
        st.metric(label="Seções", value=f"{len(section_progress)}")

    st.markdown("---")

    col_chart_1, col_chart_2 = st.columns(2)

    # Overall progress chart
    with col_chart_1:
        st.subheader("Progresso Geral")

        fig_donut = create_donut_chart(
            completed=completed_topics,
            total=total_topics,
            hole_size=0.55,
            show_percentage=True
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    # Progress by section chart
    with col_chart_2:
        st.subheader("Progresso por Seção")

        if section_progress:
            df_sections = pd.DataFrame(section_progress)

            fig_bar = px.bar(
                df_sections,
                x="percentage",
                y="section",
                orientation="h",
                labels={"percentage": "Porcentagem (%)", "section": "Seção"},
                color="percentage",
                color_continuous_scale="Viridis",
            )

            fig_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Porcentagem (%)",
                yaxis_title="Seção",
                showlegend=False,
            )
            fig_bar.update_traces(hovertemplate="%{y}: %{x:.1f}%")

            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado de progresso disponível.")


if __name__ == "__main__":
    main()
