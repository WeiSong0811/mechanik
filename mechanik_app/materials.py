"""Dataclasses and section builder utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


@dataclass(frozen=True)
class Material:
    name: str
    youngs: float  # Pa
    shear: float  # Pa
    density: float  # kg/m^3
    yield_strength: float  # Pa


@dataclass(frozen=True)
class Section:
    name: str
    area: float  # m^2
    inertia: float  # m^4
    height: float  # m
    shape: str
    dimensions: Dict[str, float]  # mm


def build_section(shape: str, dims: Dict[str, float]) -> Section:
    """Create section properties using millimeter-based input."""
    mm_to_m = 1.0 / 1000.0

    if shape == "工字钢":
        h = dims["总高"] * mm_to_m
        bf = dims["翼缘宽"] * mm_to_m
        tf = dims["翼缘厚"] * mm_to_m
        tw = dims["腹板厚"] * mm_to_m
        area = 2 * bf * tf + (h - 2 * tf) * tw
        inertia = (bf * h**3 - (bf - tw) * (h - 2 * tf) ** 3) / 12
        return Section("工字钢", area, inertia, h, shape="工字钢", dimensions=dict(dims))

    if shape == "矩形钢":
        b = dims["宽"] * mm_to_m
        h = dims["高"] * mm_to_m
        area = b * h
        inertia = b * h**3 / 12
        return Section("矩形钢", area, inertia, h, shape="矩形钢", dimensions=dict(dims))

    if shape == "方钢管":
        b = dims["外宽"] * mm_to_m
        t = dims["壁厚"] * mm_to_m
        area = b**2 - (b - 2 * t) ** 2
        inertia = (b**4 - (b - 2 * t) ** 4) / 12
        return Section("方钢管", area, inertia, b, shape="方钢管", dimensions=dict(dims))

    if shape == "圆钢":
        d = dims["直径"] * mm_to_m
        area = np.pi * d**2 / 4
        inertia = np.pi * d**4 / 64
        return Section("圆钢", area, inertia, d, shape="圆钢", dimensions=dict(dims))

    raise ValueError("未知截面类型")
