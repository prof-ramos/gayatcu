import streamlit as st
import pandas as pd
from datetime import datetime
from session import get_db
from utils import get_section_progress
from components import create_donut_chart, create_progress_bar_chart, create_line_chart, create_pie_chart
from db import get_detailed_statistics_by_section, get_weekly_review_data, get_topic_distribution_by_section, export_all_progress_to_dict

st.set_page_config(page_title="Estatísticas", page_icon="📊", layout="wide")


def display_key_metrics(cursor):
    """Display top row with key study metrics."""
    # Overall completion rate
    cursor.execute("SELECT COUNT(*) FROM topics")
    total_topics = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM progress WHERE completed_at IS NOT NULL")
    completed_topics = cursor.fetchone()[0]

    completion_rate = (completed_topics / total_topics * 100) if total_topics > 0 else 0

    # Top row: Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Tópicos", f"{total_topics}")
    with col2:
        st.metric("Tópicos Concluídos", f"{completed_topics}")
    with col3:
        st.metric("Taxa de Conclusão", f"{completion_rate:.1f}%")
    with col4:
        cursor.execute("SELECT SUM(review_count) FROM progress")
        total_reviews = cursor.fetchone()[0] or 0
        st.metric("Total de Revisões", f"{total_reviews}")

    return total_topics, completed_topics


def display_completion_charts(conn, total_topics, completed_topics):
    """Display completion rate and progress by section charts."""
    col1, col2 = st.columns(2)

    # Overall completion rate donut chart
    with col1:
        st.subheader("Taxa de Conclusão Geral")

        fig_donut = create_donut_chart(
            completed=completed_topics,
            total=total_topics,
            show_percentage=True
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    # Progress by section bar chart
    with col2:
        st.subheader("Progresso por Seção")

        section_progress = get_section_progress(conn)

        fig_bar = create_progress_bar_chart(
            section_progress=section_progress,
            height=300
        )

        st.plotly_chart(fig_bar, use_container_width=True)


def display_review_charts(conn):
    """Display reviews per week line chart and topic distribution pie chart."""
    col3, col4 = st.columns(2)

    # Reviews per week line chart
    with col3:
        st.subheader("Revisões por Semana")

        weekly_data = get_weekly_review_data(conn)

        fig_line = create_line_chart(
            data=weekly_data,
            x_col="Semana",
            y_col="Revisões",
            x_axis_title="Semana",
            y_axis_title="Número de Revisões",
            height=300,
            markers=True,
            hover_template="<b>%{x}</b><br>Revisões: %{y}"
        )

        st.plotly_chart(fig_line, use_container_width=True)

    # Topic distribution pie chart
    with col4:
        st.subheader("Distribuição de Tópicos por Seção")

        topic_dist = get_topic_distribution(conn)

        fig_pie = create_pie_chart(
            data=topic_dist,
            values_col="Total",
            names_col="Seção",
            hole_size=0.3,
            height=300,
            hover_template="%{label}: %{value} tópicos (%{percent})"
        )

        st.plotly_chart(fig_pie, use_container_width=True)


def display_export_section(conn):
    """Display data export functionality."""
    st.subheader("Exportar Dados")

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        if st.button("📥 Exportar Progresso para CSV", type="primary"):
            df = export_to_csv(conn)
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


def display_detailed_stats(cursor):
    """Display detailed statistics table by section."""
    st.subheader("📈 Estatísticas Detalhadas")

    cursor.execute("""
        SELECT
            secao,
            COUNT(*) as total,
            SUM(CASE WHEN p.completed_at IS NOT NULL THEN 1 ELSE 0 END) as concluidos
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        GROUP BY secao
        ORDER BY secao
    """)

    detailed_stats = cursor.fetchall()

    if detailed_stats:
        df_detailed = pd.DataFrame(
            detailed_stats, columns=["Seção", "Total", "Concluídos"]
        )
        df_detailed["Porcentagem"] = (
            df_detailed["Concluídos"] / df_detailed["Total"] * 100
        ).round(1)
        df_detailed["Pendentes"] = df_detailed["Total"] - df_detailed["Concluídos"]

        st.dataframe(
            df_detailed,
            use_container_width=True,
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





# Wrapper functions to convert db.py results to expected formats

def get_weekly_review_data(conn):
    """Wrapper to get weekly review data and convert to DataFrame."""
    from db import get_weekly_review_data as db_get_weekly_review_data

    data = db_get_weekly_review_data(conn)

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert review_date to datetime and group by week
    df["date"] = pd.to_datetime(df["review_date"])
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)

    # Group by week
    weekly_df = df.groupby("week")["count"].sum().reset_index()
    weekly_df.columns = ["Semana", "Revisões"]

    return weekly_df


def get_topic_distribution(conn):
    """Wrapper to get topic distribution and convert to DataFrame."""
    from db import get_topic_distribution_by_section

    data = get_topic_distribution_by_section(conn)

    if not data:
        return pd.DataFrame()

    # Convert to DataFrame with expected column names
    df = pd.DataFrame([
        {"Seção": item["secao"], "Total": item["total"]}
        for item in data
    ])

    return df


def export_to_csv(conn):
    """Wrapper to export all progress data to CSV."""
    from db import export_all_progress_to_dict

    data = export_all_progress_to_dict(conn)

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
    # Initialize database connection
    conn = get_db()

    # Page title
    st.title("📊 Estatísticas de Estudo")

    # Get statistics
    cursor = conn.cursor()

    # Display key metrics row
    total_topics, completed_topics = display_key_metrics(cursor)

    st.markdown("---")

    # Display completion charts (donut + bar chart)
    display_completion_charts(conn, total_topics, completed_topics)

    # Display review charts (line + pie chart)
    display_review_charts(conn)

    st.markdown("---")

    # Display export section
    display_export_section(conn)

    # Display detailed statistics table
    st.markdown("---")
    display_detailed_stats(cursor)



if __name__ == "__main__":
    main()
