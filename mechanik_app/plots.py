"""Plotly helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Sequence, Tuple

from .materials import Section

import numpy as np
import plotly.graph_objects as go


def plot_loads(
    x: np.ndarray,
    q_profile: np.ndarray,
    point_loads: Sequence[Tuple[float, float, str]],
    base_color: str = "#1f77b4",
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=q_profile / 1e3,
            mode="lines",
            fill="tozeroy",
            line=dict(color=base_color, width=3),
            name="均布 (kN/m)",
        )
    )
    if point_loads:
        fig.add_trace(
            go.Scatter(
                x=[p[1] for p in point_loads],
                y=[p[0] / 1e3 for p in point_loads],
                mode="markers+text",
                marker=dict(size=12, color="#d62728"),
                text=[p[2] for p in point_loads],
                textposition="top center",
                name="集中荷载 (kN)",
            )
        )
        for load, pos, _ in point_loads:
            fig.add_shape(
                type="line",
                x0=pos,
                y0=0,
                x1=pos,
                y1=load / 1e3,
                line=dict(color="#d62728", width=2),
            )
    fig.update_layout(
        title="原始荷载分布",
        xaxis_title="x (m)",
        yaxis_title="荷载 (kN, kN/m)",
        template="plotly_white",
        height=320,
    )
    return fig


def plot_deformation(
    x: np.ndarray, deflection: np.ndarray, scale: float, color: str = "#ff7f0e"
) -> go.Figure:
    scaled = deflection * scale
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=np.zeros_like(x), mode="lines", name="原始"))
    fig.add_trace(
        go.Scatter(
            x=x,
            y=scaled * 1000,
            mode="lines",
            name=f"变形 x{scale:.1f}",
            line=dict(color=color, width=3),
        )
    )
    fig.update_layout(
        title="梁挠度（实时放大）",
        xaxis_title="x (m)",
        yaxis_title="w (mm)",
        template="plotly_white",
        height=360,
        legend=dict(orientation="h"),
    )
    return fig


def plot_heatmap(
    x: np.ndarray, y_mm: np.ndarray, stress_map: np.ndarray, colorscale: str = "RdBu"
) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            x=x,
            y=y_mm,
            z=stress_map,
            colorscale=colorscale,
            zmid=0.0,
            colorbar=dict(title="σ (MPa)"),
        )
    )
    fig.update_layout(
        title="应力热力图",
        xaxis_title="x (m)",
        yaxis_title="截面高度 y (mm)",
        template="plotly_white",
        height=360,
    )
    return fig


def plot_section(section: Section, color: str = "#1f77b4") -> go.Figure:
    dims = section.dimensions
    fig = go.Figure()
    fig.update_layout(
        title=f"{section.shape} 截面示意",
        xaxis_title="宽度 (mm)",
        yaxis_title="高度 (mm)",
        template="plotly_white",
        height=320,
        showlegend=False,
    )

    if section.shape == "工字钢":
        h = dims["总高"]
        bf = dims["翼缘宽"]
        tf = dims["翼缘厚"]
        tw = dims["腹板厚"]
        fig.add_shape(
            type="rect",
            x0=-bf / 2,
            x1=bf / 2,
            y0=h / 2 - tf,
            y1=h / 2,
            fillcolor=color,
            line=dict(color="#34495e"),
        )
        fig.add_shape(
            type="rect",
            x0=-bf / 2,
            x1=bf / 2,
            y0=-h / 2,
            y1=-h / 2 + tf,
            fillcolor=color,
            line=dict(color="#34495e"),
        )
        fig.add_shape(
            type="rect",
            x0=-tw / 2,
            x1=tw / 2,
            y0=-h / 2 + tf,
            y1=h / 2 - tf,
            fillcolor=color,
            line=dict(color="#34495e"),
        )
    elif section.shape == "矩形钢":
        b = dims["宽"]
        h = dims["高"]
        fig.add_shape(
            type="rect",
            x0=-b / 2,
            x1=b / 2,
            y0=-h / 2,
            y1=h / 2,
            fillcolor=color,
            line=dict(color="#34495e"),
        )
    elif section.shape == "方钢管":
        b = dims["外宽"]
        t = dims["壁厚"]
        fig.add_shape(
            type="rect",
            x0=-b / 2,
            x1=b / 2,
            y0=-b / 2,
            y1=b / 2,
            fillcolor=color,
            line=dict(color="#34495e"),
        )
        fig.add_shape(
            type="rect",
            x0=-(b - 2 * t) / 2,
            x1=(b - 2 * t) / 2,
            y0=-(b - 2 * t) / 2,
            y1=(b - 2 * t) / 2,
            fillcolor="white",
            line=dict(color="white"),
        )
    else:  # 圆钢
        d = dims["直径"]
        theta = np.linspace(0, 2 * np.pi, 200)
        x = (d / 2) * np.cos(theta)
        y = (d / 2) * np.sin(theta)
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                fill="toself",
                mode="lines",
                line=dict(color="#34495e"),
                fillcolor=color,
            )
        )

    span = max(section.dimensions.values())
    fig.update_xaxes(range=[-span / 1.8, span / 1.8])
    fig.update_yaxes(range=[-span / 1.8, span / 1.8], scaleanchor="x", scaleratio=1)
    return fig
