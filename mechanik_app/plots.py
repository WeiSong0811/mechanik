"""Plotly helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np
import plotly.graph_objects as go


def plot_loads(
    x: np.ndarray, q_profile: np.ndarray, point_loads: Sequence[Tuple[float, float, str]]
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=q_profile / 1e3,
            mode="lines",
            fill="tozeroy",
            line=dict(color="#1f77b4", width=3),
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


def plot_deformation(x: np.ndarray, deflection: np.ndarray, scale: float) -> go.Figure:
    scaled = deflection * scale
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=np.zeros_like(x), mode="lines", name="原始"))
    fig.add_trace(
        go.Scatter(
            x=x,
            y=scaled * 1000,
            mode="lines",
            name=f"变形 x{scale:.1f}",
            line=dict(color="#ff7f0e", width=3),
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


def plot_heatmap(x: np.ndarray, y_mm: np.ndarray, stress_map: np.ndarray) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            x=x,
            y=y_mm,
            z=stress_map,
            colorscale="RdBu",
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
