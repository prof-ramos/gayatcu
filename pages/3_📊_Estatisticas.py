import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from session import get_db
from utils import get_completion_percentage, get_section_progress

st.set_page_config(page_title="Estatísticas", page_icon="📊", layout="wide")

def get_weekly_review_data(conn):
    """Get review counts per week for the last 12 weeks."""
    cursor = conn.cursor()

    # Get reviews from the last 12 weeks
    cursor.execute("""
        SELECT
            DATE(reviewed_at) as review_date,
            COUNT(*) as count
        FROM review_log
        WHERE reviewed_at >= DATE('now', '-84 days')
        GROUP BY DATE(reviewed_at)
        ORDER BY review_date
    """)

    rows = cursor.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=['date', 'count'])
    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)

    # Group by week
    weekly_df = df.groupby('week')['count'].sum().reset_index()
    weekly_df.columns = ['Semana', 'Revisões']

    return weekly_df

def get_topic_distribution(conn):
    """Get topic distribution by section."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            secao,
            COUNT(*) as count
        FROM topics
        GROUP BY secao
        ORDER BY count DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows, columns=['Seção', 'Total'])

def export_to_csv(conn):
    """Export all progress data to CSV."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.codigo,
            t.secao,
            t.subsecao,
            t.titulo,
            p.completed_at,
            p.last_reviewed_at,
            p.review_count,
            p.next_review_date
        FROM topics t
        LEFT JOIN progress p ON t.id = p.topic_id
        ORDER BY t.secao, t.subsecao, t.codigo
    """)

    rows = cursor.fetchall()

    df = pd.DataFrame(rows, columns=['Código', 'Seção', 'Subseção', 'Título',
                                      'Concluído em', 'Última Revisão',
                                      'Contagem de Revisões', 'Próxima Revisão'])

    return df

def main():
    # Initialize database connection
    conn = get_db()

    # Page title
    st.title("📊 Estatísticas de Estudo")

    # Get statistics
    cursor = conn.cursor()

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

    st.markdown("---")

    # Charts in grid layout
    col1, col2 = st.columns(2)

    # Overall completion rate donut chart
    with col1:
        st.subheader("Taxa de Conclusão Geral")

        fig_donut = go.Figure(data=[go.Pie(
            labels=['Concluídos', 'Pendentes'],
            values=[completed_topics, total_topics - completed_topics],
            hole=.5,
            marker=dict(colors=['#00CC96', '#EF553B'])
        )])

        fig_donut.update_layout(
            annotations=[dict(text=f'{completion_rate:.1f}%', x=0.5, y=0.5,
                             font_size=20, showarrow=False)]
        )

        fig_donut.update_traces(hovertemplate='%{label}: %{value} tópicos')

        st.plotly_chart(fig_donut, use_container_width=True)

    # Progress by section bar chart
    with col2:
        st.subheader("Progresso por Seção")

        section_progress = get_section_progress(conn)

        if section_progress:
            df_sections = pd.DataFrame(section_progress)

            fig_bar = px.bar(
                df_sections,
                x='percentage',
                y='section',
                orientation='h',
                labels={'percentage': 'Porcentagem (%)', 'section': 'Seção'},
                title='',
                color='percentage',
                color_continuous_scale='Viridis'
            )

            fig_bar.update_layout(
                xaxis_title='Porcentagem (%)',
                yaxis_title='Seção',
                showlegend=False,
                height=300
            )

            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado de progresso disponível.")

    # Second row: Line chart and Pie chart
    col3, col4 = st.columns(2)

    # Reviews per week line chart
    with col3:
        st.subheader("Revisões por Semana")

        weekly_data = get_weekly_review_data(conn)

        if not weekly_data.empty:
            fig_line = px.line(
                weekly_data,
                x='Semana',
                y='Revisões',
                markers=True,
                labels={'Semana': 'Semana', 'Revisões': 'Número de Revisões'},
                title=''
            )

            fig_line.update_layout(
                xaxis_title='Semana',
                yaxis_title='Número de Revisões',
                hovermode='x unified',
                height=300
            )

            fig_line.update_traces(
                hovertemplate='<b>%{x}</b><br>Revisões: %{y}'
            )

            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Nenhum dado de revisão disponível ainda.")

    # Topic distribution pie chart
    with col4:
        st.subheader("Distribuição de Tópicos por Seção")

        topic_dist = get_topic_distribution(conn)

        if not topic_dist.empty:
            fig_pie = px.pie(
                topic_dist,
                values='Total',
                names='Seção',
                title='',
                hole=0.3
            )

            fig_pie.update_layout(
                showlegend=True,
                height=300
            )

            fig_pie.update_traces(
                hovertemplate='%{label}: %{value} tópicos (%{percent})'
            )

            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhum dado de tópicos disponível.")

    st.markdown("---")

    # Export section
    st.subheader("Exportar Dados")

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        if st.button("📥 Exportar Progresso para CSV", type="primary"):
            df = export_to_csv(conn)
            csv = df.to_csv(index=False, encoding='utf-8-sig')

            st.download_button(
                label="⬇️ Baixar arquivo CSV",
                data=csv,
                file_name=f'progresso_estudos_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv',
                key='download_csv'
            )

    with col_export2:
        st.info(
            "📊 O arquivo CSV contém todos os dados de progresso, "
            "incluindo datas de conclusão, revisões e próximos agendamentos."
        )

    # Additional statistics
    st.markdown("---")
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
        df_detailed = pd.DataFrame(detailed_stats, columns=['Seção', 'Total', 'Concluídos'])
        df_detailed['Porcentagem'] = (df_detailed['Concluídos'] / df_detailed['Total'] * 100).round(1)
        df_detailed['Pendentes'] = df_detailed['Total'] - df_detailed['Concluídos']

        st.dataframe(
            df_detailed,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seção": st.column_config.TextColumn("Seção", width="medium"),
                "Total": st.column_config.NumberColumn("Total de Tópicos", width="small"),
                "Concluídos": st.column_config.NumberColumn("Concluídos", width="small"),
                "Pendentes": st.column_config.NumberColumn("Pendentes", width="small"),
                "Porcentagem": st.column_config.ProgressColumn(
                    "Progresso",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

if __name__ == "__main__":
    main()
