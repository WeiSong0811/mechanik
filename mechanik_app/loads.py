"""Load definitions and helpers."""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd

DEFAULT_POINT_LOADS = pd.DataFrame(
    {
        "标识": ["P1"],
        "大小 (kN)": [120.0],
        "位置": [0.65],
        "启用": [True],
    }
)

DEFAULT_SEGMENT_LOADS = pd.DataFrame(
    {
        "标识": ["S1"],
        "强度 (kN/m)": [20.0],
        "起点": [0.0],
        "终点": [1.0],
        "启用": [True],
    }
)


def uniform_profile(
    x: np.ndarray, length: float, enabled: bool, magnitude: float, span: Tuple[float, float]
) -> np.ndarray:
    profile = np.zeros_like(x)
    if enabled and magnitude != 0:
        start = min(span) * length
        end = max(span) * length
        mask = (x >= start) & (x <= end)
        profile[mask] = magnitude
    return profile


def segmented_profile(
    x: np.ndarray, length: float, segments_df: pd.DataFrame | None
) -> np.ndarray:
    profile = np.zeros_like(x)
    if segments_df is None or segments_df.empty:
        return profile
    for _, row in segments_df.iterrows():
        if not row.get("启用", True):
            continue
        start = float(np.clip(row.get("起点", 0.0), 0.0, 1.0)) * length
        end = float(np.clip(row.get("终点", 1.0), 0.0, 1.0)) * length
        if end < start:
            start, end = end, start
        magnitude = float(row.get("强度 (kN/m)", 0.0)) * 1e3
        mask = (x >= start) & (x <= end)
        profile[mask] += magnitude
    return profile


def point_loads_from_editor(df: pd.DataFrame, length: float) -> List[Tuple[float, float, str]]:
    loads: List[Tuple[float, float, str]] = []
    if df is None or df.empty:
        return loads
    for _, row in df.iterrows():
        if not row.get("启用", True):
            continue
        magnitude = float(row.get("大小 (kN)", 0.0)) * 1e3
        if magnitude == 0.0:
            continue
        position = float(np.clip(row.get("位置", 0.0), 0.0, 1.0)) * length
        label = str(row.get("标识", "P"))
        loads.append((magnitude, position, label))
    return loads
