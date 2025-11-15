"""Streamlit entry point orchestrating the modular beam simulator."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from mechanik_app.loads import DEFAULT_POINT_LOADS, point_loads_from_editor, uniform_profile
from mechanik_app.materials import Material, Section, build_section
from mechanik_app.plots import plot_deformation, plot_heatmap, plot_loads
from mechanik_app.solver import discretize, integrate_deflection, shear_moment, stress_field


st.set_page_config(page_title="连续介质梁仿真", layout="wide")


def left_panel() -> Tuple[
    float,
    Section,
    Material,
    int,
    pd.DataFrame,
    float,
    bool,
    Tuple[float, float],
]:
    """Render inputs for geometry, material, and loads."""
    st.subheader("材料与几何")
    length = st.number_input("梁长度 L (m)", min_value=0.5, max_value=80.0, value=8.0, step=0.5)
    shape = st.selectbox("截面类型", ["工字钢", "矩形钢", "方钢管", "圆钢"])

    dims: Dict[str, float] = {}
    if shape == "工字钢":
        dims["总高"] = st.number_input("总高 h (mm)", 50.0, 2500.0, 400.0, 5.0)
        dims["翼缘宽"] = st.number_input("翼缘宽 bf (mm)", 30.0, 1200.0, 200.0, 5.0)
        dims["翼缘厚"] = st.number_input("翼缘厚 tf (mm)", 3.0, 200.0, 18.0, 1.0)
        dims["腹板厚"] = st.number_input("腹板厚 tw (mm)", 3.0, 80.0, 12.0, 1.0)
    elif shape == "矩形钢":
        dims["高"] = st.number_input("高 h (mm)", 20.0, 1500.0, 400.0, 5.0)
        dims["宽"] = st.number_input("宽 b (mm)", 20.0, 500.0, 120.0, 5.0)
    elif shape == "方钢管":
        dims["外宽"] = st.number_input("外宽 b (mm)", 30.0, 1200.0, 250.0, 5.0)
        dims["壁厚"] = st.number_input(
            "壁厚 t (mm)", 2.0, max(dims["外宽"] / 2 - 1.0, 2.0), 10.0, 0.5
        )
    else:
        dims["直径"] = st.number_input("直径 d (mm)", 10.0, 800.0, 150.0, 5.0)

    section = build_section(shape, dims)
    st.markdown(
        f"""
        **截面属性**
        - 面积: {section.area*1e4:.1f} cm²
        - 惯性矩: {section.inertia*1e8:.1f} cm⁴
        - 代表高度: {section.height*1000:.1f} mm
        """
    )

    st.divider()

    st.subheader("材料参数（手动输入）")
    youngs = st.number_input("弹性模量 E (GPa)", 1.0, 400.0, 205.0, 1.0) * 1e9
    shear = st.number_input("剪切模量 G (GPa)", 0.1, 200.0, 79.0, 0.5) * 1e9
    density = st.number_input("密度 ρ (kg/m³)", 100.0, 15000.0, 7850.0, 10.0)
    yield_strength = st.number_input("屈服强度 fy (MPa)", 50.0, 1500.0, 345.0, 5.0) * 1e6
    material = Material("自定义", youngs, shear, density, yield_strength)

    mesh_nodes = st.slider("网格密度（节点数）", min_value=120, max_value=1500, value=500, step=20)

    st.divider()

    st.subheader("荷载设置（可拖动）")
    uniform_enabled = st.toggle("启用均布荷载", True)
    uniform_value = (
        st.slider("均布强度 q (kN/m)", 0.0, 600.0, 40.0, 5.0) * 1e3 if uniform_enabled else 0.0
    )
    uniform_span = st.slider("均布作用范围 (x/L)", 0.0, 1.0, (0.0, 1.0), 0.01)

    st.caption("集中荷载可在表格内通过数值或上下箭头拖动位置 (x/L)。")
    load_df = st.data_editor(
        DEFAULT_POINT_LOADS.copy(),
        use_container_width=True,
        column_config={
            "标识": st.column_config.TextColumn("标识"),
            "大小 (kN)": st.column_config.NumberColumn(
                "大小 (kN)", min_value=-5000.0, max_value=5000.0, step=10.0
            ),
            "位置": st.column_config.NumberColumn(
                "位置 x/L",
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format="%.2f",
            ),
            "启用": st.column_config.CheckboxColumn("启用"),
        },
        num_rows="dynamic",
        hide_index=True,
    )

    return (
        length,
        section,
        material,
        mesh_nodes,
        load_df,
        uniform_value,
        uniform_enabled,
        uniform_span,
    )


def main() -> None:
    st.title("交互式弹性梁仿真（模块化版）")
    st.caption("左侧输入材料/荷载，右侧查看实时弯曲和热力图，结构按功能拆分便于扩展。")

    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        (
            length,
            section,
            material,
            mesh_nodes,
            load_df,
            uniform_value,
            uniform_enabled,
            uniform_span,
        ) = left_panel()

    x = discretize(length, mesh_nodes)
    q_profile = uniform_profile(x, length, uniform_enabled, uniform_value, uniform_span)
    point_loads = point_loads_from_editor(load_df, length)
    shear, moment = shear_moment(x, q_profile, point_loads)
    _, _, deflection = integrate_deflection(x, moment, material.youngs, section.inertia)
    y_mm, stress_map = stress_field(moment, section.height, section.inertia)

    with left_col:
        st.plotly_chart(plot_loads(x, q_profile, point_loads), use_container_width=True)
        st.caption("左图为原始材料 & 荷载分布，触发任何输入都会实时更新。")

    with right_col:
        st.subheader("实时可视化")
        bend_scale = st.slider("挠度放大倍数", 1.0, 400.0, 80.0, 1.0)
        st.plotly_chart(plot_deformation(x, deflection, bend_scale), use_container_width=True)
        st.plotly_chart(plot_heatmap(x, y_mm, stress_map), use_container_width=True)

        st.subheader("关键指标")
        max_defl = float(np.min(deflection) * 1000)
        max_stress = float(np.max(np.abs(stress_map)))
        utilization = (
            max_stress * 1e6 / material.yield_strength if material.yield_strength > 0 else np.nan
        )
        summary = pd.DataFrame(
            {
                "指标": ["最小挠度 (mm)", "最大正应力 (MPa)", "σ/fy"],
                "数值": [max_defl, max_stress, utilization],
            }
        )
        st.dataframe(summary, hide_index=True, use_container_width=True)
        st.caption("右侧热力图展示 σ(x,y) 分布，可配合挠度放大倍数观察弯曲趋势。")

    st.divider()
    st.markdown(
        """
        **维护提示**
        - `mechanik_app.materials`, `loads`, `solver`, `plots` 分别管理材料、荷载、求解与可视化逻辑。
        - Streamlit 脚本只负责拼装交互，新增功能时可以在相应模块扩展函数后再导入使用。
        - 需要塑性、动力或多跨场景时，可在 solver 模块新增方程组并在此选择调用。
        """
    )


if __name__ == "__main__":
    main()
