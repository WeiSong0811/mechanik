"""Core modules for the Streamlit beam simulator."""

from .materials import Material, Section, build_section
from .loads import (
    DEFAULT_POINT_LOADS,
    DEFAULT_SEGMENT_LOADS,
    point_loads_from_editor,
    segmented_profile,
    uniform_profile,
)
from .solver import (
    cumulative_trapezoid,
    discretize,
    integrate_deflection,
    shear_moment,
    stress_field,
)
from .plots import plot_deformation, plot_heatmap, plot_loads, plot_section

__all__ = [
    "Material",
    "Section",
    "build_section",
    "DEFAULT_POINT_LOADS",
    "DEFAULT_SEGMENT_LOADS",
    "point_loads_from_editor",
    "segmented_profile",
    "uniform_profile",
    "discretize",
    "cumulative_trapezoid",
    "shear_moment",
    "integrate_deflection",
    "stress_field",
    "plot_loads",
    "plot_deformation",
    "plot_heatmap",
    "plot_section",
]
