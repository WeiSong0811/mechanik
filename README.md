# 交互式弹性梁仿真平台

基于 Streamlit 的二维梁力学可视化工具，集成几何/材料输入、可拖动荷载、实时挠度放大与截面应力热力图，方便教学、方案比选和参数探索。

## 功能亮点

- 手动输入材料参数（E、G、ρ、fy），支持工字钢/矩形钢/方钢管/圆钢等典型截面。
- 均布荷载可设定强度与作用区间，集中荷载位置通过 `st.data_editor` 滑动 (0~1) 实时更新。
- 左侧展示原始材料与荷载分布，右侧同步显示挠度曲线（带可调放大倍数）与 σ(x,y) 热力图。
- 结果面板输出最大挠度、最大应力及 σ/fy 比值，便于快速评估塑性风险。
- 模块化代码结构，后续扩展新截面、新求解器或自定义可视化时无需改动整个脚本。

## 目录结构

```
mechanik/
├─ mechanik_app/
│  ├─ __init__.py
│  ├─ materials.py   # Material/Section 数据结构 & 截面构造
│  ├─ loads.py       # 默认荷载表格、均布/集中荷载转换
│  ├─ solver.py      # 离散化、剪力/弯矩、挠度与应力场求解
│  └─ plots.py       # Plotly 绘图封装（荷载、挠度、热力图）
├─ streamlit_app.py  # 主入口，负责 UI 组合与模块调用
├─ requirements.txt
└─ README.md
```

## 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate        # PowerShell / CMD
pip install -r requirements.txt
```

> 若已有虚拟环境，可直接 `pip install streamlit plotly pandas numpy`。

## 运行

```bash
streamlit run streamlit_app.py
```

浏览器中可见左右分栏：左侧为几何/材料/荷载输入，右侧为挠度放大及热力图。调整任意参数、拖动集中荷载位置后图形即时刷新。

## 扩展建议

1. **新增材料 / 截面**：在 `mechanik_app/materials.py` 内扩展 `build_section` 或添加新的数据类/工厂函数，然后在 `streamlit_app.py` 的下拉菜单中引用。
2. **拓展荷载类型**：在 `mechanik_app/loads.py` 增加新的分布函数或数据编辑器列，再在主脚本中组装。
3. **高级求解**：将塑性、动力或多跨算法实现到 `mechanik_app/solver.py` 并暴露新的模式开关。
4. **可视化增强**：在 `mechanik_app/plots.py` 新增 3D 形变、剪力/弯矩图等绘图函数，通过主 UI 选择性呈现。

## 已知限制

- 目前采用 Euler-Bernoulli 梁假设，忽略剪切变形和几何非线性。
- 集中荷载表格行数越多计算越慢，可通过调低“网格密度”控制性能。
- 塑性阶段仅提供 σ/fy 提示，实际弹塑性演化需进一步建模。

欢迎根据项目需要继续扩展模块并提交改进！如遇问题，可先检查 Streamlit 控制台日志或通过 `python -m py_compile` 验证脚本语法。***
