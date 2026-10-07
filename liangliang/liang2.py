"""
FLAC3D 圆柱体蠕变试验模拟器 —— 优化单文件版（含三维动态模拟·修复版）
================================================
运行：
    pip install streamlit numpy pandas matplotlib plotly
    streamlit run liang2.py
"""

import time

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import plotly.graph_objects as go
from matplotlib.ticker import LogLocator
from dataclasses import dataclass, field

# =====================================================
# 常量与单位
# =====================================================
MM = 1e-3
GPA = 1e9
MPA = 1e6
HOUR = 3600.0
EPS_FLOOR = 1e-30

st.set_page_config(
    page_title="FLAC3D 蠕变试验模拟器",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# 全局样式：字体 + 配色 + 图表风格
# =====================================================
_CN_FONTS = [
    "Microsoft YaHei", "SimHei", "PingFang SC",
    "Hiragino Sans GB", "Noto Sans CJK SC", "WenQuanYi Micro Hei",
    "Source Han Sans SC", "Arial Unicode MS",
]
mpl.rcParams["font.sans-serif"] = _CN_FONTS + ["DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

COLOR_TOTAL = "#2563EB"
COLOR_ELASTIC = "#EF4444"
COLOR_CREEP = "#10B981"
COLOR_GRID = "#E5E7EB"
COLOR_AXIS = "#9CA3AF"
COLOR_TEXT = "#1F2937"
COLOR_BG = "#FFFFFF"

mpl.rcParams.update({
    "figure.facecolor": COLOR_BG,
    "axes.facecolor": COLOR_BG,
    "axes.edgecolor": COLOR_AXIS,
    "axes.labelcolor": COLOR_TEXT,
    "axes.titlecolor": COLOR_TEXT,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.color": COLOR_TEXT,
    "ytick.color": COLOR_TEXT,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "legend.frameon": True,
    "legend.framealpha": 0.9,
    "legend.edgecolor": COLOR_GRID,
    "figure.dpi": 110,
})

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    div[data-testid="stSidebar"] > div:first-child {padding-top: 0.8rem;}
    .stMetric > label {font-size: 0.85rem; color: #6B7280;}
    .stMetric > div {font-size: 1.25rem; font-weight: 600;}
    h3 {color: #1F2937;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧪 FLAC3D 圆柱体蠕变试验模拟器")
st.caption("圆柱体单轴压缩 | Power (Norton) / Burgers 蠕变 | SI 单位制")


# =====================================================
# 数据结构
# =====================================================
@dataclass
class ElasticParams:
    young: float
    poisson: float
    bulk: float = field(init=False)
    shear: float = field(init=False)

    def __post_init__(self):
        self.bulk = self.young / (3.0 * (1.0 - 2.0 * self.poisson))
        self.shear = self.young / (2.0 * (1.0 + self.poisson))


@dataclass
class PowerParams:
    A: float
    n: float
    sigma_ref: float


@dataclass
class BurgersParams:
    eta_m: float
    eta_k: float
    Gk_ratio: float


@dataclass
class Geometry:
    radius: float
    height: float


@dataclass
class Loading:
    stress: float
    total_time: float
    time_step: float


# =====================================================
# 核心计算
# =====================================================
def compute_power_curve(p, E, stress, t_max, n_pts=400):
    t = np.linspace(0.0, t_max, n_pts)
    eps_e = stress / E
    rate = p.A * (stress / p.sigma_ref) ** p.n
    eps_c = rate * t
    return t, eps_e + eps_c, np.full_like(t, eps_e), eps_c, np.full_like(t, rate)


def compute_burgers_curve(bp, K, G, stress, t_max, n_pts=400):
    Gk = bp.Gk_ratio * G
    t = np.linspace(0.0, t_max, n_pts)
    eps_me = stress / (9.0 * K) + stress / (3.0 * G)
    eps_k = stress / (3.0 * Gk) * (1.0 - np.exp(-Gk / bp.eta_k * t))
    eps_v = stress / (3.0 * bp.eta_m) * t
    total = eps_me + eps_k + eps_v
    creep = eps_k + eps_v
    rate = np.full_like(t, stress / (3.0 * bp.eta_m))
    return t, total, np.full_like(t, eps_me), creep, rate


def safe_positive(arr):
    return np.where(arr > EPS_FLOOR, arr, EPS_FLOOR)


def compute_characteristic_time(p, E, stress):
    denom = p.A * (stress / p.sigma_ref) ** p.n * E
    return np.inf if denom <= 0 else 1.0 / denom


# =====================================================
# 二维绘图函数
# =====================================================
def make_creep_figure(
    t_hour, strain_total, strain_elastic, strain_creep,
    title, log_x=False, log_y=False, height_mm=100.0,
):
    """生成美化后的蠕变曲线图，返回 Figure"""
    fig, ax = plt.subplots(figsize=(7.8, 5.0), constrained_layout=True)

    y_total = strain_total * 1e3
    y_elastic = strain_elastic * 1e3
    y_creep = strain_creep * 1e3

    if log_y:
        y_total, y_elastic, y_creep = map(safe_positive, (y_total, y_elastic, y_creep))
    x_plot = safe_positive(t_hour) if log_x else t_hour

    ax.fill_between(
        x_plot, y_elastic, y_total,
        color=COLOR_CREEP, alpha=0.08, linewidth=0, zorder=0,
    )

    ax.plot(
        x_plot, y_elastic, color=COLOR_ELASTIC, lw=2.2, ls="--", zorder=5,
        marker="s", markevery=max(1, len(x_plot) // 10),
        markersize=5, markerfacecolor="white", markeredgewidth=1.3,
        label="弹性应变",
    )

    ax.plot(
        x_plot, y_creep, color=COLOR_CREEP, lw=2.0, ls="-.", zorder=3,
        label="蠕变应变",
    )

    ax.plot(
        x_plot, y_total, color=COLOR_TOTAL, lw=2.4, zorder=4,
        marker="o", markevery=max(1, len(x_plot) // 12),
        markersize=4.5, markerfacecolor="white", markeredgewidth=1.2,
        label="总应变",
    )

    eps_e_val = float(y_elastic[0])
    ax.axhline(
        eps_e_val, color=COLOR_ELASTIC, lw=0.8, ls=":", alpha=0.5, zorder=2,
    )
    ax.annotate(
        f"ε_e = {eps_e_val:.3f}",
        xy=(x_plot[-1], eps_e_val),
        xytext=(-8, 6), textcoords="offset points",
        ha="right", va="bottom", fontsize=9, color=COLOR_ELASTIC,
        bbox=dict(boxstyle="round,pad=0.25", fc="white",
                  ec=COLOR_ELASTIC, lw=0.8, alpha=0.9),
    )

    ax.set_xlabel("时间 (h)", labelpad=8)
    ax.set_ylabel("轴向应变 (×10⁻³)", labelpad=8)
    ax.set_title(title, pad=12)

    if log_x:
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
        ax.xaxis.set_minor_locator(
            LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12)
        )
    if log_y:
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
        ax.yaxis.set_minor_locator(
            LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12)
        )

    ax.grid(True, which="major", color=COLOR_GRID, linewidth=0.8, alpha=0.9)
    if log_x or log_y:
        ax.grid(True, which="minor", color=COLOR_GRID, linewidth=0.4, alpha=0.5)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLOR_AXIS)
    ax.spines["bottom"].set_color(COLOR_AXIS)

    leg = ax.legend(
        loc="upper left", frameon=True, framealpha=0.95,
        edgecolor=COLOR_GRID, borderpad=0.8, handlelength=2.2,
    )
    leg.get_frame().set_linewidth(0.8)

    ax.text(
        0.985, 0.02, f"H = {height_mm:.0f} mm",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=8.5, color="#9CA3AF", style="italic",
    )

    return fig


# =====================================================
# 三维圆柱体几何生成（核心）
# =====================================================
def _cylinder_mesh_data(radius, height, circ_div, axial_div):
    """生成圆柱体网格顶点数据。"""
    theta = np.linspace(0.0, 2.0 * np.pi, circ_div + 1)
    z_levels = np.linspace(0.0, height, axial_div + 1)
    return theta, z_levels


def _build_cylinder_traces(
    radius, height, circ_div, axial_div,
    n_meridian=8,
    color_meridian="#2563EB",
    color_ring="#93C5FD",
    color_top="#10B981",
    color_bot="#EF4444",
    top_opacity=0.35,
):
    """构建一个圆柱体所有的 plotly trace（不含箭头和布局）。"""
    theta, z_levels = _cylinder_mesh_data(radius, height, circ_div, axial_div)

    traces = []

    # 母线（竖线）
    meridian_indices = np.linspace(0, circ_div, n_meridian + 1).astype(int)
    for k in meridian_indices:
        k = min(k, circ_div)
        traces.append(go.Scatter3d(
            x=[radius * np.cos(theta[k])] * len(z_levels),
            y=[radius * np.sin(theta[k])] * len(z_levels),
            z=z_levels,
            mode="lines",
            line=dict(color=color_meridian, width=2.5),
            showlegend=False,
            hoverinfo="skip",
        ))

    # 环线（每层一个圆）
    for z in z_levels:
        traces.append(go.Scatter3d(
            x=radius * np.cos(theta),
            y=radius * np.sin(theta),
            z=np.full_like(theta, z),
            mode="lines",
            line=dict(color=color_ring, width=1),
            showlegend=False,
            hoverinfo="skip",
        ))

    # 顶面边界
    traces.append(go.Scatter3d(
        x=radius * np.cos(theta),
        y=radius * np.sin(theta),
        z=np.full_like(theta, height),
        mode="lines",
        line=dict(color=color_top, width=4),
        name="顶面",
        hoverinfo="skip",
    ))

    # 底面边界
    traces.append(go.Scatter3d(
        x=radius * np.cos(theta),
        y=radius * np.sin(theta),
        z=np.zeros_like(theta),
        mode="lines",
        line=dict(color=color_bot, width=4),
        name="底面",
        hoverinfo="skip",
    ))

    # 顶面半透明填充
    n_theta = circ_div
    top_x = list(radius * np.cos(theta[:-1])) + [0.0]
    top_y = list(radius * np.sin(theta[:-1])) + [0.0]
    top_z = list(np.full(n_theta, height)) + [height]
    top_faces = [(i, (i + 1) % n_theta, n_theta) for i in range(n_theta)]

    traces.append(go.Mesh3d(
        x=top_x, y=top_y, z=top_z,
        i=[f[0] for f in top_faces],
        j=[f[1] for f in top_faces],
        k=[f[2] for f in top_faces],
        color=color_top,
        opacity=top_opacity,
        showlegend=False,
        hoverinfo="skip",
    ))

    # 底面半透明填充
    bot_x = list(radius * np.cos(theta[:-1])) + [0.0]
    bot_y = list(radius * np.sin(theta[:-1])) + [0.0]
    bot_z = list(np.zeros(n_theta)) + [0.0]
    bot_faces = [(i, (i + 1) % n_theta, n_theta) for i in range(n_theta)]

    traces.append(go.Mesh3d(
        x=bot_x, y=bot_y, z=bot_z,
        i=[f[0] for f in bot_faces],
        j=[f[1] for f in bot_faces],
        k=[f[2] for f in bot_faces],
        color=color_bot,
        opacity=0.20,
        showlegend=False,
        hoverinfo="skip",
    ))

    return traces


def _deformed_dims(radius_mm, height_mm, eps_z, scale_factor):
    """
    根据轴向应变计算变形后的可视半径与高度。
    假设近似不可压材料：eps_r ≈ -eps_z / 2。
    """
    eps_z_vis = eps_z * scale_factor
    eps_r_vis = -eps_z_vis * 0.5
    H = height_mm * (1.0 + eps_z_vis)
    R = radius_mm * (1.0 + eps_r_vis)
    return R, H


def _scene_layout(radius_mm, height_mm, xy_range):
    """统一的 3D 场景布局，避免各函数重复。"""
    return dict(
        xaxis=dict(title="X (mm)", range=[-xy_range, xy_range],
                   backgroundcolor="#F9FAFB"),
        yaxis=dict(title="Y (mm)", range=[-xy_range, xy_range],
                   backgroundcolor="#F9FAFB"),
        zaxis=dict(title="Z (mm)",
                   range=[-height_mm * 0.15, height_mm * 1.45],
                   backgroundcolor="#F9FAFB"),
        aspectmode="manual",
        aspectratio=dict(
            x=1.0, y=1.0,
            z=max(1.0, height_mm / max(radius_mm * 2.0, 1e-6)) * 0.6,
        ),
        camera=dict(eye=dict(x=1.6, y=1.6, z=0.9)),
    )


def _make_arrow_trace(R, H):
    """生成轴向荷载箭头 trace。"""
    return go.Cone(
        x=[0.0], y=[0.0], z=[H * 1.18],
        u=[0.0], v=[0.0], w=[-H * 0.13],
        colorscale=[[0.0, "#EF4444"], [1.0, "#EF4444"]],
        showscale=False,
        sizemode="absolute",
        sizeref=H * 0.09,
        name="轴向荷载",
        hoverinfo="skip",
    )


def make_3d_cylinder_figure(
    radius_mm, height_mm, strain_total, t_hour, frame_idx,
    circ_div=16, axial_div=20, scale_factor=1.0,
):
    """生成单个时刻的圆柱体三维图。"""
    eps_z = float(strain_total[frame_idx])
    R, H = _deformed_dims(radius_mm, height_mm, eps_z, scale_factor)

    traces = _build_cylinder_traces(
        R, H, circ_div=circ_div, axial_div=axial_div, n_meridian=8,
    )
    traces.append(_make_arrow_trace(R, H))

    fig = go.Figure(data=traces)

    xy_range = max(R * 2.0, radius_mm * 1.2)
    fig.update_layout(
        scene=_scene_layout(radius_mm, height_mm, xy_range),
        margin=dict(l=0, r=0, t=40, b=0),
        height=580,
        paper_bgcolor="#FFFFFF",
        title=dict(
            text=(
                f"t = {t_hour[frame_idx]:.3f} h | "
                f"ε_z = {eps_z * 1e3:.4f}×10⁻³ | "
                f"放大 {scale_factor:.0f}×"
            ),
            x=0.5,
            font=dict(size=13, color="#1F2937"),
        ),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.85)"),
        showlegend=True,
    )

    return fig


def make_3d_animation_figure(
    radius_mm, height_mm, strain_total, t_hour,
    circ_div=16, axial_div=20, scale_factor=1.0,
    n_frames=30, frame_duration=120,
):
    """
    生成带播放按钮的 plotly 动画图（Streamlit 兼容版）。
    关键修复：播放按钮显式列出所有帧名，避免 args=[None] 在 Streamlit 中失效。
    """
    n_pts = len(strain_total)
    frame_indices = np.unique(
        np.linspace(0, n_pts - 1, min(n_frames, n_pts)).astype(int)
    )

    # ---------- 构建初始帧 ----------
    eps0 = float(strain_total[frame_indices[0]])
    R0, H0 = _deformed_dims(radius_mm, height_mm, eps0, scale_factor)

    base_traces = _build_cylinder_traces(
        R0, H0, circ_div=circ_div, axial_div=axial_div, n_meridian=8,
    )
    base_traces.append(_make_arrow_trace(R0, H0))
    n_traces = len(base_traces)

    # ---------- 构建所有帧 ----------
    frames = []
    frame_names = []
    for idx in frame_indices:
        eps_z = float(strain_total[idx])
        R, H = _deformed_dims(radius_mm, height_mm, eps_z, scale_factor)

        frame_traces = _build_cylinder_traces(
            R, H, circ_div=circ_div, axial_div=axial_div, n_meridian=8,
        )
        frame_traces.append(_make_arrow_trace(R, H))

        fname = f"f{int(idx)}"
        frame_names.append(fname)
        frames.append(go.Frame(
            data=frame_traces,
            name=fname,
            traces=list(range(n_traces)),
        ))

    xy_range = max(radius_mm * 2.0, radius_mm * 1.2)

    fig = go.Figure(data=base_traces, frames=frames)

    # ---------- 关键修复：显式指定帧序列 ----------
    fig.update_layout(
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.05, y=1.15, xanchor="left",
            buttons=[
                dict(
                    label="▶️ 播放",
                    method="animate",
                    args=[
                        frame_names,                       # ← 显式帧列表
                        dict(
                            frame=dict(duration=frame_duration, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=0),
                            mode="immediate",
                        ),
                    ],
                ),
                dict(
                    label="⏸️ 暂停",
                    method="animate",
                    args=[
                        [None],
                        dict(
                            frame=dict(duration=0, redraw=False),
                            mode="immediate",
                            transition=dict(duration=0),
                        ),
                    ],
                ),
            ],
        )],
        scene=_scene_layout(radius_mm, height_mm, xy_range),
        margin=dict(l=0, r=0, t=70, b=0),
        height=620,
        paper_bgcolor="#FFFFFF",
        title=dict(
            text=(
                f"t = {t_hour[frame_indices[0]]:.3f} h | "
                f"ε_z = {float(strain_total[frame_indices[0]]) * 1e3:.4f}×10⁻³ | "
                f"放大 {scale_factor:.0f}×"
            ),
            x=0.5,
            font=dict(size=13, color="#1F2937"),
        ),
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.85)"),
        showlegend=True,
    )

    return fig


# =====================================================
# 命令流生成
# =====================================================
def build_flac_commands(
    geo, elastic, loading, model_key, creep_model_label,
    power=None, burgers=None, mesh=(6, 16, 20),
    solve_mode="自动", export_path="creep_axial_disp.csv",
    save_name="creep_cylinder",
):
    radial_div, circ_div, axial_div = mesh
    H, R = geo.height, geo.radius

    if model_key == "power":
        cmodel = "power"
        creep_props = (
            f"zone property power-constant-1 {power.A:.6e}\n"
            f"zone property power-exponent-1 {power.n:.4f}\n"
            f"zone property reference-stress {power.sigma_ref:.6e}"
        )
    else:
        cmodel = "burg"
        Gk = burgers.Gk_ratio * elastic.shear
        creep_props = (
            f"zone property maxwell-bulk {elastic.bulk:.6e}\n"
            f"zone property maxwell-shear {elastic.shear:.6e}\n"
            f"zone property maxwell-viscosity {burgers.eta_m:.6e}\n"
            f"zone property kelvin-shear {Gk:.6e}\n"
            f"zone property kelvin-viscosity {burgers.eta_k:.6e}"
        )

    if solve_mode == "自动":
        solve_block = (
            "model creep active on\n"
            "model creep timestep automatic on\n"
            f"model solve time-total {loading.total_time:.6g}"
        )
    else:
        solve_block = (
            "model creep active on\n"
            f"model creep timestep fix {loading.time_step:.6g}\n"
            f"model solve time-total {loading.total_time:.6g}"
        )

    return f"""; ============================================================
; FLAC3D 圆柱体单轴蠕变试验命令流（自动生成）
; 本构: {creep_model_label}
; 单位: SI (m, Pa, s)
; ============================================================

model new
model title "Cylinder Creep: D={2*R*1000:.0f}mm H={H*1000:.0f}mm"
model large-strain off
model gravity 0 0 0

; ---------- 1. 圆柱体网格 ----------
zone create cylinder point 0 (0,0,0) point 1 (0,0,{H:.6f}) ...
                    point 2 ({R:.6f},0,0) ...
                    size {radial_div} {circ_div} {axial_div}

; ---------- 2. 本构模型 ----------
zone cmodel assign {cmodel}
zone property density 2500

; ---------- 3. 材料参数 ----------
zone property bulk  {elastic.bulk:.6e}
zone property shear {elastic.shear:.6e}
{creep_props}

; ---------- 4. 边界条件（单轴压缩，侧向自由） ----------
zone gridpoint fix velocity-z range position-z 0
zone face apply stress-normal -{loading.stress:.6e} range position-z {H:.6f}

; ---------- 5. 蠕变求解 ----------
{solve_block}

; ---------- 6. 监测 ----------
history interval 20
zone history displacement-z position (0,0,{H:.6f})
history export 1 '{export_path}' truncate

; ---------- 7. 保存 ----------
model save '{save_name}'
"""


# =====================================================
# 侧边栏
# =====================================================
with st.sidebar:
    st.header("⚙️ 参数设置")

    with st.expander("① 几何与网格", expanded=True):
        diameter_mm = st.number_input("直径 D (mm)", 10.0, 200.0, 50.0, 1.0)
        height_mm = st.number_input("高度 H (mm)", 20.0, 300.0, 100.0, 5.0)
        c1, c2, c3 = st.columns(3)
        radial_div = c1.number_input("径向", 2, 20, 6, 1)
        axial_div = c2.number_input("轴向", 5, 60, 20, 1)
        circ_div = c3.number_input("周向", 8, 36, 16, 1)

    with st.expander("② 弹性参数", expanded=True):
        young_GPa = st.number_input("弹性模量 E (GPa)", 1.0, 100.0, 20.0, 0.5)
        poisson = st.number_input("泊松比 ν", 0.05, 0.45, 0.25, 0.01)

    with st.expander("③ 蠕变本构", expanded=True):
        creep_model = st.selectbox(
            "本构模型",
            ["power (Norton 幂律)", "burg (Burgers 粘弹性)"],
        )
        is_power = creep_model.startswith("power")

        if is_power:
            st.caption(r"Norton: $\dot\varepsilon = A\,(\sigma/\sigma_{ref})^n$")
            A_power = st.number_input(
                "蠕变常数 A (s⁻¹)", 1e-40, 1e-2, 1e-15,
                format="%.3e", step=1e-16,
            )
            n_power = st.number_input("应力指数 n", 1.0, 10.0, 3.0, 0.1)
            sigma_ref_MPa = st.number_input(
                "参考应力 σ_ref (MPa)", 0.01, 1000.0, 1.0, 0.1,
            )
            eta_m = eta_k = 1e15
            kelvin_ratio = 0.5
        else:
            st.caption("Burgers: Maxwell + Kelvin")
            eta_m = st.number_input(
                "Maxwell 粘度 η_m (Pa·s)", 1e10, 1e22, 1e15,
                format="%.3e", step=1e13,
            )
            eta_k = st.number_input(
                "Kelvin 粘度 η_k (Pa·s)", 1e10, 1e22, 1e14,
                format="%.3e", step=1e13,
            )
            kelvin_ratio = st.number_input(
                "G_k / G_m 比值", 0.05, 5.0, 0.5, 0.05,
            )
            A_power, n_power, sigma_ref_MPa = 1e-15, 3.0, 1.0

    with st.expander("④ 加载条件", expanded=True):
        axial_stress_MPa = st.number_input("轴向应力 σ (MPa)", 0.1, 200.0, 10.0, 0.5)
        total_time_hr = st.number_input("模拟总时长 (h)", 0.1, 10000.0, 24.0, 0.5)
        time_step_s = st.number_input("时间步长 Δt (s)", 0.1, 10000.0, 10.0, 0.1)

    with st.expander("⑤ 求解与输出", expanded=False):
        solve_mode = st.radio("时间步方式", ["自动", "固定"], index=0)
        export_path = st.text_input("history 导出文件名", "creep_axial_disp.csv")
        save_name = st.text_input("model save 文件名", "creep_cylinder")


# =====================================================
# 参数构建与校验
# =====================================================
geometry = Geometry(diameter_mm * MM / 2.0, height_mm * MM)
loading = Loading(axial_stress_MPa * MPA, total_time_hr * HOUR, time_step_s)

if not (0.0 < poisson < 0.5):
    st.error("❌ 泊松比 ν 必须满足 0 < ν < 0.5")
    st.stop()

elastic = ElasticParams(young_GPa * GPA, poisson)
if elastic.bulk <= 0 or elastic.shear <= 0:
    st.error("❌ 弹性参数非法：K 或 G ≤ 0，请检查 E 与 ν")
    st.stop()

power_params = PowerParams(A_power, n_power, sigma_ref_MPa * MPA)
burgers_params = BurgersParams(eta_m, eta_k, kelvin_ratio)

if loading.total_time <= 0 or loading.time_step <= 0:
    st.error("❌ 模拟总时长与时间步长必须为正")
    st.stop()


# =====================================================
# 计算曲线
# =====================================================
if is_power:
    t_curve, strain_total, strain_elastic, strain_creep, creep_rate = compute_power_curve(
        power_params, elastic.young, loading.stress, loading.total_time
    )
    curve_title = "Norton 幂律蠕变曲线"
    model_key = "power"
else:
    t_curve, strain_total, strain_elastic, strain_creep, creep_rate = compute_burgers_curve(
        burgers_params, elastic.bulk, elastic.shear, loading.stress, loading.total_time
    )
    curve_title = "Burgers 粘弹性蠕变曲线"
    model_key = "burg"

creep_rate_scalar = float(creep_rate[0])


# =====================================================
# 主区域（Tabs）
# =====================================================
st.divider()

tab_2d, tab_3d = st.tabs(["📈 二维蠕变曲线", "🧊 三维动态模拟"])

# -----------------------------------------------------
# Tab 1：二维曲线
# -----------------------------------------------------
with tab_2d:
    main_left, main_mid, main_right = st.columns([1.6, 0.95, 0.95], gap="large")

    with main_left:
        header_l, header_r = st.columns([3, 2])
        header_l.subheader("📈 " + curve_title)
        with header_r:
            opt1, opt2 = st.columns(2)
            log_x = opt1.checkbox("对数时间", value=False)
            log_y = opt2.checkbox("对数应变", value=False)

        fig = make_creep_figure(
            t_curve / HOUR, strain_total, strain_elastic, strain_creep,
            title=curve_title, log_x=log_x, log_y=log_y, height_mm=height_mm,
        )
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with main_mid:
        st.subheader("📊 关键指标")
        st.metric("稳态蠕变速率", f"{creep_rate_scalar:.3e} /s",
                  f"{creep_rate_scalar * HOUR:.3e} /h")
        st.metric("最终总应变", f"{strain_total[-1] * 1e3:.4f} ×10⁻³")
        st.metric("最终蠕变应变", f"{strain_creep[-1] * 1e3:.4f} ×10⁻³")

        if model_key == "power" and power_params.A > 0:
            t_crit = compute_characteristic_time(power_params, elastic.young, loading.stress)
            if np.isfinite(t_crit):
                st.info(f"⚠️ 特征时间 t* ≈ `{t_crit:.3e}` s\n\n建议 Δt ≤ t*/100")
                if loading.time_step > t_crit / 100 and solve_mode == "固定":
                    st.warning("固定时间步可能过大，建议切换为自动时间步")

    with main_right:
        st.subheader("📋 参数摘要")
        summary = pd.DataFrame({
            "参数": [
                "直径 D", "高度 H", "高径比 H/D",
                "弹性模量 E", "泊松比 ν",
                "体积模量 K", "剪切模量 G",
                "轴向应力 σ", "蠕变本构",
                "模拟时长", "时间步长",
            ],
            "数值": [
                f"{diameter_mm:.1f} mm",
                f"{height_mm:.1f} mm",
                f"{height_mm / diameter_mm:.2f}",
                f"{young_GPa:.2f} GPa",
                f"{poisson:.2f}",
                f"{elastic.bulk / GPA:.3f} GPa",
                f"{elastic.shear / GPA:.3f} GPa",
                f"{axial_stress_MPa:.2f} MPa",
                creep_model,
                f"{total_time_hr:.2f} h",
                f"{time_step_s:.2f} s",
            ],
        })
        st.dataframe(summary, hide_index=True, use_container_width=True, height=420)


# -----------------------------------------------------
# Tab 2：三维动态模拟
# -----------------------------------------------------
with tab_3d:
    st.subheader("🧊 圆柱体蠕变三维动态模拟")
    st.caption(
        "真实蠕变应变极小（10⁻³ 量级），通过「变形放大系数」可视化。"
        "径向变形按近似不可压假设 ε_r ≈ -ε_z/2 估算。"
    )

    # 控制面板
    ctrl1, ctrl2, ctrl3 = st.columns([2.2, 1.2, 1.4])

    with ctrl1:
        frame_idx = st.slider(
            "时间进度（拖动查看不同时刻）",
            min_value=0,
            max_value=len(t_curve) - 1,
            value=0,
            step=max(1, len(t_curve) // 100),
        )

    with ctrl2:
        scale_factor = st.number_input(
            "变形放大系数", min_value=1.0, max_value=5000.0,
            value=200.0, step=50.0,
            help="真实应变很小，放大后便于观察",
        )

    with ctrl3:
        mode_3d = st.radio(
            "显示模式",
            ["滑块查看", "Plotly 原生动画", "手动逐帧刷新"],
            index=0,
        )

    # ---------- 模式 A：滑块查看 ----------
    if mode_3d == "滑块查看":
        fig3d = make_3d_cylinder_figure(
            diameter_mm / 2.0,
            height_mm,
            strain_total,
            t_curve / HOUR,
            frame_idx=frame_idx,
            circ_div=circ_div,
            axial_div=axial_div,
            scale_factor=scale_factor,
        )
        st.plotly_chart(
            fig3d, use_container_width=True,
            key=f"single_{frame_idx}_{scale_factor}",
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("当前时刻", f"{t_curve[frame_idx] / HOUR:.3f} h")
        m2.metric("轴向总应变", f"{strain_total[frame_idx] * 1e3:.4f} ×10⁻³")
        m3.metric("蠕变应变", f"{strain_creep[frame_idx] * 1e3:.4f} ×10⁻³")
        m4.metric("弹性应变", f"{strain_elastic[frame_idx] * 1e3:.4f} ×10⁻³")

    # ---------- 模式 B：Plotly 原生动画 ----------
    elif mode_3d == "Plotly 原生动画":
        fig_anim = make_3d_animation_figure(
            diameter_mm / 2.0,
            height_mm,
            strain_total,
            t_curve / HOUR,
            circ_div=circ_div,
            axial_div=axial_div,
            scale_factor=scale_factor,
            n_frames=30,
            frame_duration=120,
        )
        st.plotly_chart(
            fig_anim,
            use_container_width=True,
            key=f"anim_{scale_factor}_{circ_div}_{axial_div}",
        )

        st.info(
            "💡 点击图表左上角的 **▶️ 播放** 按钮开始动画。"
            "若未动，请切换到「手动逐帧刷新」模式（100% 可靠）。"
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("起始时刻", f"{t_curve[0] / HOUR:.3f} h")
        m2.metric("结束时刻", f"{t_curve[-1] / HOUR:.3f} h")
        m3.metric("最终总应变", f"{strain_total[-1] * 1e3:.4f} ×10⁻³")
        m4.metric("最终蠕变应变", f"{strain_creep[-1] * 1e3:.4f} ×10⁻³")

    # ---------- 模式 C：手动逐帧刷新（100% 可靠）----------
    else:
        c1, c2 = st.columns([1.2, 3])
        with c1:
            play_speed = st.slider("播放速度 (秒/帧)", 0.02, 0.5, 0.08, 0.01)
            n_play_frames = st.slider("动画帧数", 10, 80, 40, 5)
        with c2:
            st.write("")
            st.write("")
            start_play = st.button("▶️ 开始播放动画", use_container_width=True)

        placeholder = st.empty()

        # 计算动画帧序列
        play_indices = np.unique(
            np.linspace(0, len(t_curve) - 1, n_play_frames).astype(int)
        )

        if start_play:
            progress = st.progress(0.0)
            for i, idx in enumerate(play_indices):
                fig_i = make_3d_cylinder_figure(
                    diameter_mm / 2.0,
                    height_mm,
                    strain_total,
                    t_curve / HOUR,
                    frame_idx=int(idx),
                    circ_div=circ_div,
                    axial_div=axial_div,
                    scale_factor=scale_factor,
                )
                placeholder.plotly_chart(
                    fig_i, use_container_width=True,
                    key=f"manual_frame_{i}_{scale_factor}",
                )
                progress.progress((i + 1) / len(play_indices))
                time.sleep(play_speed)
            progress.empty()
        else:
            # 未点击播放时，先展示初始帧
            fig_init = make_3d_cylinder_figure(
                diameter_mm / 2.0,
                height_mm,
                strain_total,
                t_curve / HOUR,
                frame_idx=0,
                circ_div=circ_div,
                axial_div=axial_div,
                scale_factor=scale_factor,
            )
            placeholder.plotly_chart(
                fig_init, use_container_width=True,
                key=f"manual_init_{scale_factor}",
            )

        st.info(
            "💡 点击「▶️ 开始播放动画」按钮后，图像会以设定速度逐帧刷新。"
            "播放过程中页面会短暂卡住属正常现象（Streamlit 同步刷新机制）。"
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("起始时刻", f"{t_curve[0] / HOUR:.3f} h")
        m2.metric("结束时刻", f"{t_curve[-1] / HOUR:.3f} h")
        m3.metric("最终总应变", f"{strain_total[-1] * 1e3:.4f} ×10⁻³")
        m4.metric("最终蠕变应变", f"{strain_creep[-1] * 1e3:.4f} ×10⁻³")


# =====================================================
# FLAC3D 命令流
# =====================================================
st.divider()
st.subheader("⚙️ FLAC3D 命令流 (.dat)")

flac_commands = build_flac_commands(
    geometry, elastic, loading, model_key, creep_model,
    power=power_params if model_key == "power" else None,
    burgers=burgers_params if model_key == "burg" else None,
    mesh=(radial_div, circ_div, axial_div),
    solve_mode=solve_mode, export_path=export_path, save_name=save_name,
)

cmd_col, btn_col = st.columns([4, 1])
with cmd_col:
    st.code(flac_commands, language="text")
with btn_col:
    st.write("")
    st.write("")
    st.download_button(
        "📥 下载 .dat",
        data=flac_commands,
        file_name="creep_test_cylinder.dat",
        mime="text/plain",
        use_container_width=True,
    )