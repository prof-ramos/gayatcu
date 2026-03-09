import logging
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from components import create_donut_chart, create_progress_bar_chart
from db import get_statistics
from monitoring import cleanup_session_state, monitor_memory_usage
from session import get_db, initialize_database
from utils import get_completion_percentage, get_section_progress

logger = logging.getLogger(__name__)
TCU_LOGO_PATH = Path(__file__).parent / "assets" / "tcu_logo.png"

st.set_page_config(
    page_title="GayATCU - Dashboard de Estudos TCU", page_icon="📘", layout="wide"
)


def display_header():
    """Display enhanced header with progress bar."""
    if TCU_LOGO_PATH.exists():
        logo_left, logo_center, logo_right = st.columns([1, 10, 1])
        with logo_center:
            st.image(str(TCU_LOGO_PATH), width="stretch")

    st.title("📘 GayATCU - Dashboard de Estudos TCU")
    st.markdown(
        """
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        .header-text {
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .header-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_progress_overview(
    completion_pct: float, total_topics: int, completed_topics: int
):
    """Display enhanced progress overview with visual indicators."""
    pending_topics = total_topics - completed_topics

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📚 Total de Tópicos",
            value=f"{total_topics}",
            help="Número total de tópicos no programa de estudos",
        )

    with col2:
        delta_color = "normal" if completion_pct >= 50 else "inverse"
        st.metric(
            label="✅ Concluídos",
            value=f"{completed_topics}",
            delta=f"{completion_pct:.1f}% do total",
            delta_color=delta_color,
            help="Tópicos marcados como concluídos",
        )

    with col3:
        st.metric(
            label="📝 Pendentes",
            value=f"{pending_topics}",
            help="Tópicos que ainda precisam ser estudados",
        )

    with col4:
        # Calculate estimated weeks to completion (assuming 5 topics per week)
        weeks_remaining = -(-pending_topics // 5) if pending_topics > 0 else 0
        completion_date = datetime.now() + timedelta(weeks=weeks_remaining)
        st.metric(
            label="📅 Previsão de Conclusão",
            value=completion_date.strftime("%d/%m/%Y"),
            help=f"Estimativa baseada em 5 tópicos por semana ({weeks_remaining} semanas restantes)",
        )


def display_section_cards(section_progress: list):
    """Display section progress as interactive cards."""
    st.markdown("### 📖 Progresso por Disciplina")

    if not section_progress:
        st.info("Nenhum dado de progresso disponível.")
        return

    # Sort by percentage descending
    section_progress_sorted = sorted(
        section_progress, key=lambda x: x["percentage"], reverse=True
    )

    # Display in grid layout (3 columns)
    cols_per_row = 3
    for i in range(0, len(section_progress_sorted), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(section_progress_sorted):
                section = section_progress_sorted[idx]
                with col:
                    # Progress percentage determines color
                    pct = section["percentage"]
                    if pct >= 80:
                        emoji = "🟢"
                        border_color = "#00CC96"
                    elif pct >= 50:
                        emoji = "🟡"
                        border_color = "#FFA500"
                    elif pct >= 25:
                        emoji = "🟠"
                        border_color = "#FF8C00"
                    else:
                        emoji = "🔴"
                        border_color = "#EF553B"

                    st.markdown(
                        f"""
                        <div style="
                            border: 2px solid {border_color};
                            border-radius: 10px;
                            padding: 1rem;
                            margin-bottom: 1rem;
                            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.1) 100%);
                        ">
                            <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;">
                                {emoji} {section["section"]}
                            </div>
                            <div style="font-size: 2rem; font-weight: bold; color: {border_color};">
                                {section["percentage"]:.1f}%
                            </div>
                            <div style="font-size: 0.9rem; color: #888;">
                                {section["completed"]} de {section["total"]} tópicos
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def display_motivational_message(completion_pct: float):
    """Display motivational message based on progress."""
    if completion_pct >= 80:
        message = "🎉 Excelente! Você está quase lá!"
        submessage = "Continue firme, falta pouco para conquistar seu objetivo!"
    elif completion_pct >= 50:
        message = "💪 Ótimo progresso!"
        submessage = "Você já cobriu metade do caminho. Continue assim!"
    elif completion_pct >= 25:
        message = "📈 Bom começo!"
        submessage = "Você está construindo uma base sólida. Mantenha o ritmo!"
    elif completion_pct > 0:
        message = "🚀 Primeiros passos!"
        submessage = "Toda jornada começa com um primeiro passo. Continue estudando!"
    else:
        message = "📚 Pronto para começar?"
        submessage = (
            "Marque seu primeiro tópico como concluído para iniciar seu progresso!"
        )

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 2rem 0;
            text-align: center;
        ">
            <div style="font-size: 1.8rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">
                {message}
            </div>
            <div style="font-size: 1.1rem; color: rgba(255, 255, 255, 0.9);">
                {submessage}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    # Global exception handler for Streamlit Community Cloud
    try:
        # Initialize database and import data if needed
        initialize_database()

        # Monitor memory usage (displays in sidebar)
        monitor_memory_usage()

        # Clean up unused cache entries to prevent memory leaks
        cleanup_session_state()

        # Get database connection
        db = get_db()

        # Calculate metrics using database
        try:
            stats = get_statistics(db)
            total_topics = stats.get("total_topics", 0)
            completed_topics = stats.get("completed_topics", 0)
        except (SQLAlchemyError, ValueError):
            total_topics = 0
            completed_topics = 0

        try:
            completion_pct = get_completion_percentage(db)
        except (SQLAlchemyError, ValueError):
            completion_pct = 0.0

        try:
            section_progress = get_section_progress(db)
        except (SQLAlchemyError, ValueError):
            section_progress = []

        # Display header
        display_header()

        # Display motivational message
        display_motivational_message(completion_pct)

        # Display progress overview
        display_progress_overview(completion_pct, total_topics, completed_topics)

        st.markdown("---")

        # Display charts in improved layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Progresso Geral")

            fig_donut = create_donut_chart(
                completed=completed_topics,
                total=total_topics,
                hole_size=0.6,
                show_percentage=True,
            )

            st.plotly_chart(fig_donut, width="stretch")

        with col2:
            st.subheader("📈 Progresso por Disciplina")

            if section_progress:
                fig_bar = create_progress_bar_chart(
                    section_progress=section_progress,
                    height=400,
                    color_scale="RdYlGn",  # Red-Yellow-Green scale
                )

                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.info("Nenhum dado de progresso disponível.")

        st.markdown("---")

        # Display section cards
        display_section_cards(section_progress)

        # Footer with quick actions
        st.markdown("---")
        st.markdown("### ⚡ Ações Rápidas")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Ver Checklist", width="stretch", type="primary"):
                st.switch_page("pages/1_📋_Checklist.py")

        with col2:
            if st.button("📅 Ver Revisões", width="stretch"):
                st.switch_page("pages/2_📅_Revisoes.py")

        with col3:
            if st.button("📊 Ver Estatísticas", width="stretch"):
                st.switch_page("pages/3_📊_Estatisticas.py")

        # Footer info
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; color: #888; font-size: 0.9rem; margin-top: 2rem;">
                💡 <strong>Dica:</strong> Revise os tópicos regularmente usando o sistema de repetição espaçada
                para fixar o conteúdo na memória de longo prazo.
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Erro ao carregar aplicação: {str(e)}")
        st.info(
            "Por favor, recarregue a página. Se o problema persistir, contacte o suporte."
        )
        logger.error(f"Application error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
