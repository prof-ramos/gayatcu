"""
Reusable chart components for GayATCU dashboard.

This module contains standardized Plotly chart functions that are used
across multiple pages to eliminate code duplication and ensure consistency.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Chart color scheme (consistent with Streamlit theme)
CHART_COLORS = {
    "completed": "#00CC96",
    "pending": "#EF553B",
    "primary": "#22c55e",
    "background": "#0f172a",
}


def create_donut_chart(
    completed: int,
    total: int,
    title: str = "",
    hole_size: float = 0.5,
    show_percentage: bool = True,
) -> go.Figure:
    """
    Create a standardized donut chart for completion rates.

    Args:
        completed: Number of completed items
        total: Total number of items
        title: Optional chart title
        hole_size: Size of the center hole (0-1)
        show_percentage: Whether to show percentage in center

    Returns:
        Plotly Figure object ready for st.plotly_chart()
    """
    if total == 0:
        pending = 0
        percentage = 0.0
    else:
        pending = total - completed
        percentage = (completed / total) * 100.0

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Concluídos", "Pendentes"],
                values=[completed, pending],
                hole=hole_size,
                marker=dict(
                    colors=[CHART_COLORS["completed"], CHART_COLORS["pending"]]
                ),
            )
        ]
    )

    layout_updates = {
        "margin": dict(l=10, r=10, t=30 if title else 10, b=10),
    }

    if show_percentage:
        layout_updates["annotations"] = [
            dict(
                text=f"{percentage:.1f}%",
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False,
            )
        ]

    if title:
        layout_updates["title"] = dict(text=title, x=0.5, xanchor="center")

    fig.update_layout(**layout_updates)
    fig.update_traces(hovertemplate="%{label}: %{value} tópicos")

    return fig


def create_progress_bar_chart(
    section_progress: List[Dict[str, Any]],
    title: str = "",
    height: int = 300,
    color_scale: str = "Viridis",
) -> go.Figure:
    """
    Create a standardized horizontal bar chart for section progress.

    Args:
        section_progress: List of dicts with 'section', 'percentage', 'total', 'completed'
        title: Optional chart title
        height: Chart height in pixels
        color_scale: Plotly color scale name

    Returns:
        Plotly Figure object ready for st.plotly_chart()
    """
    if not section_progress:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Nenhum dado de progresso disponível",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ]
        )
        return fig

    df = pd.DataFrame(section_progress)

    fig = px.bar(
        df,
        x="percentage",
        y="section",
        orientation="h",
        labels={"percentage": "Porcentagem (%)", "section": "Seção"},
        title=title,
        color="percentage",
        color_continuous_scale=color_scale,
    )

    fig.update_layout(
        xaxis_title="Porcentagem (%)",
        yaxis_title="Seção",
        showlegend=False,
        height=height,
    )

    return fig


def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    x_axis_title: str = "",
    y_axis_title: str = "",
    height: int = 300,
    markers: bool = True,
    hover_template: Optional[str] = None,
) -> go.Figure:
    """
    Create a standardized line chart for trends over time.

    Args:
        data: DataFrame with the data to plot
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Optional chart title
        x_axis_title: Optional x-axis label
        y_axis_title: Optional y-axis label
        height: Chart height in pixels
        markers: Whether to show markers on data points
        hover_template: Optional custom hover template

    Returns:
        Plotly Figure object ready for st.plotly_chart()
    """
    if data.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Nenhum dado disponível",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ]
        )
        return fig

    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        markers=markers,
        title=title,
    )

    layout_updates = {"height": height}

    if x_axis_title:
        layout_updates["xaxis_title"] = x_axis_title
    if y_axis_title:
        layout_updates["yaxis_title"] = y_axis_title

    fig.update_layout(**layout_updates)

    if hover_template:
        fig.update_traces(hovertemplate=hover_template)

    return fig


def create_pie_chart(
    data: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str = "",
    hole_size: float = 0.0,
    height: int = 300,
    hover_template: Optional[str] = None,
) -> go.Figure:
    """
    Create a standardized pie chart for categorical distribution.

    Args:
        data: DataFrame with the data to plot
        values_col: Column name for values
        names_col: Column name for category names
        title: Optional chart title
        hole_size: Size of center hole (0-1, 0=pie, >0=donut)
        height: Chart height in pixels
        hover_template: Optional custom hover template

    Returns:
        Plotly Figure object ready for st.plotly_chart()
    """
    if data.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Nenhum dado disponível",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ]
        )
        return fig

    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        title=title,
        hole=hole_size,
    )

    fig.update_layout(showlegend=True, height=height)

    if hover_template:
        fig.update_traces(hovertemplate=hover_template)

    return fig


def create_metric_row(
    metrics: List[Dict[str, Any]],
    use_container_width: bool = True,
) -> None:
    """
    Display a row of metrics in Streamlit with consistent styling.

    Args:
        metrics: List of dicts with 'label' and 'value' keys
        use_container_width: Whether to use container width

    Example:
        create_metric_row([
            {"label": "Total de Tópicos", "value": "345"},
            {"label": "Concluídos", "value": "120"},
            {"label": "Taxa", "value": "34.8%"},
        ])
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            st.metric(metric["label"], metric["value"])
