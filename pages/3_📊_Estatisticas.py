"""
Statistics Page - Study metrics and visualizations.

Displays comprehensive study statistics including completion rates,
progress by section, review trends, and topic distribution.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from components import (
    create_donut_chart,
    create_line_chart,
    create_pie_chart,
    create_progress_bar_chart,
)
from db import (
    export_all_progress_to_dict,
    get_detailed_statistics_by_section,
    get_statistics,
    get_topic_distribution_by_section,
)
from db import (
    get_weekly_review_data as db_get_weekly_review_data,
)
from session import get_db
from utils import get_section_progress

st.set_page_config(page_title="Estatísticas", page_icon="📊", layout="wide")


def display_key_metrics(engine):
    """Display top row with key study metrics using ORM."""
    stats = get_statistics(engine)

    total_topics = stats["total_topics"]
    completed_topics = stats["completed_topics"]
    completion_rate = stats["completion_rate"]
    total_reviews = stats["total_reviews"]

    # Top row: Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Tópicos", f"{total_topics}")
    with col2:
        st.metric("Tópicos Concluídos", f"{completed_topics}")
    with col3:
        st.metric("Taxa de Conclusão", f"{completion_rate:.1f}%")
    with col4:
        st.metric("Total de Revisões", f"{total_reviews}")

    return total_topics, completed_topics


def display_completion_charts(engine, total_topics, completed_topics):
    """Display completion rate and progress by section charts."""
    col1, col2 = st.columns(2)

    # Overall completion rate donut chart
    with col1:
        st.subheader("Taxa de Conclusão Geral")

        fig_donut = create_donut_chart(
            completed=completed_topics, total=total_topics, show_percentage=True
        )

        st.plotly_chart(fig_donut, width="stretch")

    # Progress by section bar chart
    with col2:
        st.subheader("Progresso por Seção")

        section_progress = get_section_progress(engine)

        fig_bar = create_progress_bar_chart(
            section_progress=section_progress, height=300
        )

        st.plotly_chart(fig_bar, width="stretch")


def display_review_charts(engine):
    """Display reviews per week line chart and topic distribution pie chart."""
    col3, col4 = st.columns(2)

    # Reviews per week line chart
    with col3:
        st.subheader("Revisões por Semana")

        raw_data = db_get_weekly_review_data(engine)
        weekly_df = _convert_weekly_data(raw_data)

        fig_line = create_line_chart(
            data=weekly_df,
            x_col="Semana",
            y_col="Revisões",
            x_axis_title="Semana",
            y_axis_title="Número de Revisões",
            height=300,
            markers=True,
            hover_template="<b>%{x}</b><br>Revisões: %{y}",
        )

        st.plotly_chart(fig_line, width="stretch")

    # Topic distribution pie chart
    with col4:
        st.subheader("Distribuição de Tópicos por Seção")

        topic_dist = _convert_topic_distribution(engine)

        fig_pie = create_pie_chart(
            data=topic_dist,
            values_col="Total",
            names_col="Seção",
            hole_size=0.3,
            height=300,
            hover_template="%{label}: %{value} tópicos (%{percent})",
        )

        st.plotly_chart(fig_pie, width="stretch")


def display_export_section(engine):
    """Display data export functionality."""
    st.subheader("Exportar Dados")

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        if st.button("📥 Exportar Progresso para CSV", type="primary"):
            df = _export_to_csv(engine)
            csv = df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(
                label="⬇️ Baixar arquivo CSV",
                data=csv,
                file_name=f"progresso_estudos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_csv",
            )

    with col_export2:
        st.info(
            "📊 O arquivo CSV contém todos os dados de progresso, "
            "incluindo datas de conclusão, revisões e próximos agendamentos."
        )


def display_detailed_stats(engine):
    """Display detailed statistics table by section using ORM."""
    st.subheader("📈 Estatísticas Detalhadas")

    detailed_stats = get_detailed_statistics_by_section(engine)

    if detailed_stats:
        df_detailed = pd.DataFrame(detailed_stats)
        df_detailed.rename(
            columns={
                "secao": "Seção",
                "total": "Total",
                "completed": "Concluídos",
                "percentage": "Porcentagem",
                "pending": "Pendentes",
            },
            inplace=True,
        )

        st.dataframe(
            df_detailed,
            width="stretch",
            hide_index=True,
            column_config={
                "Seção": st.column_config.TextColumn("Seção", width="medium"),
                "Total": st.column_config.NumberColumn(
                    "Total de Tópicos", width="small"
                ),
                "Concluídos": st.column_config.NumberColumn(
                    "Concluídos", width="small"
                ),
                "Pendentes": st.column_config.NumberColumn("Pendentes", width="small"),
                "Porcentagem": st.column_config.ProgressColumn(
                    "Progresso", format="%.1f%%", min_value=0, max_value=100
                ),
            },
        )


# --- Conversion helpers ---


def _convert_weekly_data(raw_data: list) -> pd.DataFrame:
    """Convert raw weekly review data from db.py to DataFrame for charts."""
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    # Convert review_date to datetime and group by week
    df["date"] = pd.to_datetime(df["review_date"])
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    # Group by week
    weekly_df = df.groupby("week")["count"].sum().reset_index()
    weekly_df.columns = ["Semana", "Revisões"]

    return weekly_df


def _convert_topic_distribution(engine) -> pd.DataFrame:
    """Convert topic distribution from db.py to DataFrame for charts."""
    data = get_topic_distribution_by_section(engine)

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(
        [{"Seção": item["secao"], "Total": item["total"]} for item in data]
    )

    return df


def _export_to_csv(engine) -> pd.DataFrame:
    """Convert all progress data to DataFrame for CSV export."""
    data = export_all_progress_to_dict(engine)

    df = pd.DataFrame(data)

    # Rename columns to Portuguese
    df.columns = [
        "Código",
        "Seção",
        "Subseção",
        "Título",
        "Concluído em",
        "Última Revisão",
        "Contagem de Revisões",
        "Próxima Revisão",
    ]

    return df


def main():
    """Main function for statistics page - displays all study statistics."""
    # Initialize database engine
    engine = get_db()

    # Page title
    st.title("📊 Estatísticas de Estudo")

    # Criar abas para organizar o conteúdo
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Visão Geral",
        "📚 Por Seção",
        "📅 Revisões",
        "💾 Exportar"
    ])

    with tab1:
        # Métricas principais e gráficos de conclusão
        total_topics, completed_topics = display_key_metrics(engine)
        st.markdown("---")
        display_completion_charts(engine, total_topics, completed_topics)

    with tab2:
        # Progresso detalhado por seção
        display_detailed_stats(engine)

    with tab3:
        # Análise de revisões
        display_review_charts(engine)

    with tab4:
        # Funcionalidades de exportação
        display_export_section(engine)


if __name__ == "__main__":
    main()
