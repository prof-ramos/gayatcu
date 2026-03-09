import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from session import get_db, initialize_database
from db import get_statistics
from utils import get_completion_percentage, get_section_progress

st.set_page_config(
    page_title="GayATCU - Dashboard de Estudos TCU",
    page_icon="📘",
    layout="wide"
)

def main():
    # Initialize database and import data if needed
    initialize_database()

    # Get database connection
    db = get_db()

    # Calculate metrics using database
    stats = get_statistics(db)
    total_topics = stats['total_topics']
    completed_topics = stats['completed_topics']
    completion_pct = get_completion_percentage(db)
    section_progress = get_section_progress(db)

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
        pending_topics = max(total_topics - completed_topics, 0)

        fig_donut = go.Figure(data=[go.Pie(
            labels=["Concluídos", "Pendentes"],
            values=[completed_topics, pending_topics],
            hole=0.55,
            marker=dict(colors=["#00CC96", "#EF553B"])
        )])

        fig_donut.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            annotations=[dict(
                text=f"{completion_pct:.1f}%",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=24)
            )]
        )
        fig_donut.update_traces(hovertemplate="%{label}: %{value} tópicos")

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
                color_continuous_scale="Viridis"
            )

            fig_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Porcentagem (%)",
                yaxis_title="Seção",
                showlegend=False
            )
            fig_bar.update_traces(hovertemplate="%{y}: %{x:.1f}%")

            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado de progresso disponível.")

if __name__ == "__main__":
    main()
