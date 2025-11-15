"""Streamlit entry point orchestrating the modular beam simulator."""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from mechanik_app import (
    DEFAULT_POINT_LOADS,
    DEFAULT_SEGMENT_LOADS,
    Material,
    Section,
    build_section,
    discretize,
    integrate_deflection,
    plot_deformation,
    plot_heatmap,
    plot_loads,
    plot_section,
    point_loads_from_editor,
    segmented_profile,
    shear_moment,
    stress_field,
    uniform_profile,
)


st.set_page_config(page_title="连续介质梁仿真", layout="wide")


def _geometry_section(shape: str) -> Tuple[Section, Dict[str, float]]:
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
    return build_section(shape, dims), dims


def left_panel() -> Dict[str, object]:
    st.subheader("理论与求解设置")
    theory = st.selectbox("梁理论", ["Euler-Bernoulli", "Timoshenko"])
    default_kappa = 1.2 if theory == "Timoshenko" else 1.0
    shear_coeff = st.number_input(
        "剪切修正系数 κ",
        min_value=0.5,
        max_value=2.0,
        value=default_kappa,
        step=0.05,
        disabled=theory == "Euler-Bernoulli",
    )
    if theory == "Euler-Bernoulli":
        shear_coeff = 1.0
    load_scale = st.slider("荷载缩放系数", 0.1, 5.0, 1.0, 0.1)
    primary_color = st.color_picker("主色调 (截面/荷载)", "#1f77b4")
    deform_color = st.color_picker("变形曲线颜色", "#ff7f0e")
    heatmap_palette = st.selectbox(
        "热力图色阶", ["RdBu", "Viridis", "Plasma", "Turbo", "Picnic"], index=0
    )

    st.subheader("材料与几何")
    length = st.number_input("梁长度 L (m)", min_value=0.5, max_value=80.0, value=8.0, step=0.5)
    shape = st.selectbox("截面类型", ["工字钢", "矩形钢", "方钢管", "圆钢"])
    section, _ = _geometry_section(shape)
    st.markdown(
        f"""
        **截面属性**
        - 面积: {section.area*1e4:.1f} cm²
        - 惯性矩: {section.inertia*1e8:.1f} cm⁴
        - 代表高度: {section.height*1000:.1f} mm
        """
    )

    st.subheader("材料参数")
    youngs = st.number_input("弹性模量 E (GPa)", 1.0, 400.0, 205.0, 1.0) * 1e9
    shear_mod = st.number_input("剪切模量 G (GPa)", 0.1, 200.0, 79.0, 0.5) * 1e9
    density = st.number_input("密度 ρ (kg/m³)", 100.0, 15000.0, 7850.0, 10.0)
    yield_strength = st.number_input("屈服强度 fy (MPa)", 50.0, 1500.0, 345.0, 5.0) * 1e6
    material = Material("自定义", youngs, shear_mod, density, yield_strength)

    mesh_nodes = st.slider("网格密度（节点数）", min_value=120, max_value=1500, value=600, step=20)

    st.subheader("荷载设置")
    uniform_enabled = st.toggle("启用均布荷载", True)
    uniform_value = (
        st.slider("均布强度 q (kN/m)", 0.0, 600.0, 40.0, 5.0) * 1e3 if uniform_enabled else 0.0
    )
    uniform_span = st.slider("均布作用范围 (x/L)", 0.0, 1.0, (0.0, 1.0), 0.01)

    st.caption("补充分段均布荷载（可定义多段不同强度）。")
    distributed_df = st.data_editor(
        DEFAULT_SEGMENT_LOADS.copy(),
        use_container_width=True,
        column_config={
            "标识": st.column_config.TextColumn("标识"),
            "强度 (kN/m)": st.column_config.NumberColumn(
                "强度 (kN/m)", min_value=-800.0, max_value=800.0, step=5.0
            ),
            "起点": st.column_config.NumberColumn("起点 x/L", min_value=0.0, max_value=1.0, step=0.01),
            "终点": st.column_config.NumberColumn("终点 x/L", min_value=0.0, max_value=1.0, step=0.01),
            "启用": st.column_config.CheckboxColumn("启用"),
        },
        num_rows="dynamic",
        hide_index=True,
        key="segment_editor",
    )

    st.caption("集中荷载通过表格（位置 x/L）拖动或编辑。")
    point_df = st.data_editor(
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
        key="point_editor",
    )

    return {
        "length": length,
        "section": section,
        "material": material,
        "mesh_nodes": mesh_nodes,
        "uniform_value": uniform_value,
        "uniform_enabled": uniform_enabled,
        "uniform_span": uniform_span,
        "distributed_df": distributed_df,
        "point_df": point_df,
        "theory": theory,
        "shear_coeff": shear_coeff,
        "load_scale": load_scale,
        "primary_color": primary_color,
        "deform_color": deform_color,
        "heatmap_palette": heatmap_palette,
    }


def main() -> None:
    st.title("交互式弹性梁仿真（重构版）")
    st.caption("结合 CSDN 梁实验文章的布局，在其基础上补充可定制理论、荷载段、截面配色与可视化。")

    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        settings = left_panel()

    length = settings["length"]
    section: Section = settings["section"]
    material: Material = settings["material"]

    x = discretize(length, settings["mesh_nodes"])
    q_uniform = uniform_profile(
        x, length, settings["uniform_enabled"], settings["uniform_value"], settings["uniform_span"]
    )
    q_segment = segmented_profile(x, length, settings["distributed_df"])
    q_profile = (q_uniform + q_segment) * settings["load_scale"]

    raw_point_loads = point_loads_from_editor(settings["point_df"], length)
    point_loads = [
        (mag * settings["load_scale"], pos, label) for mag, pos, label in raw_point_loads
    ]

    shear, moment = shear_moment(x, q_profile, point_loads)
    _, rotation, deflection, shear_gamma = integrate_deflection(
        x,
        moment,
        shear,
        material.youngs,
        section.inertia,
        section.area,
        material.shear,
        settings["shear_coeff"],
        settings["theory"],
    )
    y_mm, stress_map = stress_field(moment, section.height, section.inertia)

    with left_col:
        st.plotly_chart(
            plot_loads(x, q_profile, point_loads, base_color=settings["primary_color"]),
            use_container_width=True,
        )
        st.caption("左图融合基础均布加载和分段加载，方便对照原始荷载分布。")

    with right_col:
        st.subheader("实时可视化")
        bend_scale = st.slider("挠度放大倍数", 1.0, 400.0, 80.0, 1.0)
        st.plotly_chart(
            plot_deformation(x, deflection, bend_scale, color=settings["deform_color"]),
            use_container_width=True,
        )
        st.plotly_chart(
            plot_heatmap(x, y_mm, stress_map, colorscale=settings["heatmap_palette"]),
            use_container_width=True,
        )
        st.plotly_chart(
            plot_section(section, color=settings["primary_color"]), use_container_width=True
        )

        st.subheader("关键指标 & 探测")
        probe_ratio = st.slider("探测位置 x/L", 0.0, 1.0, 0.5, 0.01)
        probe_idx = min(int(probe_ratio * (len(x) - 1)), len(x) - 1)
        sigma_top = float(stress_map[-1, probe_idx])
        sigma_bottom = float(stress_map[0, probe_idx])
        data = pd.DataFrame(
            {
                "指标": [
                    "最大挠度 (mm)",
                    "最大正应力 (MPa)",
                    "σ/fy",
                    f"x/L={probe_ratio:.2f} 挠度 (mm)",
                    f"x/L={probe_ratio:.2f} σ_top (MPa)",
                    f"x/L={probe_ratio:.2f} σ_bottom (MPa)",
                ],
                "数值": [
                    float(np.min(deflection) * 1000),
                    float(np.max(np.abs(stress_map))),
                    float(np.max(np.abs(stress_map)) * 1e6 / material.yield_strength)
                    if material.yield_strength > 0
                    else np.nan,
                    float(deflection[probe_idx] * 1000),
                    sigma_top,
                    sigma_bottom,
                ],
            }
        )
        st.dataframe(data, hide_index=True, use_container_width=True)
        st.caption(
            "若 σ/fy>1 ，代表屈服风险；可在材料输入区调整 fy 或在 load 数据编辑器减小荷载。"
        )

    st.divider()
    st.markdown(
        """
        **自定义扩展建议**
        - 在 `mechanik_app/solver.py` 中追加更多理论（如铁木辛科动力学）或边界条件函数，再通过 `theory` 下拉扩展。
        - 通过 `mechanik_app/plots.py` 新增动图/3D 形变，可在右栏中追加 plotly 动画。
        - 利用 data_editor 的 `key` 和 `session_state` 可记忆不同组合，便于科研报告多方案对比。
        """
    )


if __name__ == "__main__":
    main()
