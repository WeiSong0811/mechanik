"""Numerical routines for beam response."""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np


def discretize(length: float, nodes: int) -> np.ndarray:
    return np.linspace(0.0, length, nodes)


def cumulative_trapezoid(values: np.ndarray, x: np.ndarray) -> np.ndarray:
    dx = np.diff(x)
    avg = 0.5 * (values[:-1] + values[1:])
    integral = np.concatenate(([0.0], np.cumsum(avg * dx)))
    return integral


def shear_moment(
    x: np.ndarray, q_profile: np.ndarray, point_loads: Sequence[Tuple[float, float, str]]
) -> Tuple[np.ndarray, np.ndarray]:
    dist_integral = cumulative_trapezoid(q_profile, x)
    total_distributed = dist_integral[-1]
    point_total = sum(load for load, _, _ in point_loads)
    reaction = total_distributed + point_total

    point_cumulative = np.zeros_like(x)
    for load, position, _ in point_loads:
        point_cumulative += load * (x >= position)

    shear = reaction - dist_integral - point_cumulative

    moment_root = np.trapz(q_profile * x, x) + sum(load * position for load, position, _ in point_loads)
    shear_avg = 0.5 * (shear[:-1] + shear[1:])
    moment = moment_root - np.concatenate(([0.0], np.cumsum(shear_avg * np.diff(x))))
    return shear, moment


def integrate_deflection(
    x: np.ndarray, moment: np.ndarray, youngs: float, inertia: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    curvature = moment / (youngs * inertia)
    slope = np.zeros_like(curvature)
    deflection = np.zeros_like(curvature)
    for i in range(1, len(x)):
        dx = x[i] - x[i - 1]
        slope[i] = slope[i - 1] + 0.5 * (curvature[i] + curvature[i - 1]) * dx
        deflection[i] = deflection[i - 1] + 0.5 * (slope[i] + slope[i - 1]) * dx
    return curvature, slope, deflection


def stress_field(moment: np.ndarray, section_height: float, inertia: float, points: int = 120):
    if section_height <= 0 or inertia <= 0:
        return np.array([0.0]), np.zeros((1, len(moment)))
    y = np.linspace(-section_height / 2, section_height / 2, points)
    stress = np.outer(y, moment) / inertia
    return y * 1000, stress / 1e6  # y in mm, stress in MPa
