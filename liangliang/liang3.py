"""
分形处理自动化工具 (单文件版)
================================
功能:
  1. 单图生成 - Mandelbrot / Julia 交互式参数调节
  2. 批量参数扫描 - 自动生成 + ZIP 打包下载
  3. 动画帧序列 - 对数插值平滑缩放, 可合成视频

性能优化:
  - numba JIT 加速像素级循环 (带缓存)
  - 向量化颜色映射 (matplotlib colormap)
  - 内存复用与流式 ZIP 打包
  - 会话状态缓存, 避免重复计算
  - 预编译 + 编译提示

运行:
  pip install streamlit numpy pillow matplotlib numba
  streamlit run app.py
"""

import io
import time
import hashlib
import zipfile
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any

import numpy as np
import matplotlib
import matplotlib.cm as cm
import streamlit as st
from numba import njit
from PIL import Image


# ============================================================
# 分形核心算法 (numba 加速)
# ============================================================

@njit(cache=True, fastmath=True)
def _mandelbrot_kernel(width, height, max_iter, x_min, x_max, y_min, y_max):
    """Mandelbrot 集合计算核心"""
    result = np.zeros((height, width), dtype=np.int32)
    inv_w = 1.0 / (width - 1) if width > 1 else 0.0
    inv_h = 1.0 / (height - 1) if height > 1 else 0.0
    span_x = x_max - x_min
    span_y = y_max - y_min
    for i in range(height):
        y0 = y_min + span_y * i * inv_h
        for j in range(width):
            x0 = x_min + span_x * j * inv_w
            x = 0.0
            y = 0.0
            k = 0
            while x * x + y * y <= 4.0 and k < max_iter:
                xtemp = x * x - y * y + x0
                y = 2.0 * x * y + y0
                x = xtemp
                k += 1
            result[i, j] = k
    return result


@njit(cache=True, fastmath=True)
def _julia_kernel(width, height, max_iter, c_re, c_im, x_min, x_max, y_min, y_max):
    """Julia 集合计算核心"""
    result = np.zeros((height, width), dtype=np.int32)
    inv_w = 1.0 / (width - 1) if width > 1 else 0.0
    inv_h = 1.0 / (height - 1) if height > 1 else 0.0
    span_x = x_max - x_min
    span_y = y_max - y_min
    for i in range(height):
        zy0 = y_min + span_y * i * inv_h
        for j in range(width):
            zx = x_min + span_x * j * inv_w
            zy = zy0
            k = 0
            while zx * zx + zy * zy <= 4.0 and k < max_iter:
                xtemp = zx * zx - zy * zy + c_re
                zy = 2.0 * zx * zy + c_im
                zx = xtemp
                k += 1
            result[i, j] = k
    return result


# 颜色映射缓存
_CMAP_CACHE: Dict[str, Any] = {}


def _get_cmap(name: str):
    if name not in _CMAP_CACHE:
        try:
            _CMAP_CACHE[name] = matplotlib.colormaps.get_cmap(name)
        except Exception:
            _CMAP_CACHE[name] = matplotlib.colormaps.get_cmap("inferno")
    return _CMAP_CACHE[name]


def _colorize(iterations: np.ndarray, max_iter: int, colormap: str) -> np.ndarray:
    """向量化颜色映射, 输出 (H, W, 3) uint8"""
    norm = np.clip(iterations.astype(np.float32) / float(max_iter), 0.0, 1.0)
    cmap = _get_cmap(colormap)
    # cmap 接受 float 数组返回 (H, W, 4)
    colored = (cmap(norm)[:, :, :3] * 255).astype(np.uint8)
    # 集合内点 (达到 max_iter) 涂黑
    colored[iterations >= max_iter] = 0
    return colored


# ============================================================
# 参数配置
# ============================================================

@dataclass
class FractalParams:
    fractal_type: str = "mandelbrot"
    width: int = 800
    height: int = 600
    max_iter: int = 256
    zoom: float = 1.0
    center_x: float = -0.5
    center_y: float = 0.0
    julia_c: Tuple[float, float] = (-0.7, 0.27015)
    colormap: str = "inferno"

    def cache_key(self) -> str:
        raw = (
            f"{self.fractal_type}|{self.width}x{self.height}|{self.max_iter}|"
            f"{self.zoom:.6f}|{self.center_x:.8f}|{self.center_y:.8f}|"
            f"{self.julia_c[0]:.8f},{self.julia_c[1]:.8f}|{self.colormap}"
        )
        return hashlib.md5(raw.encode()).hexdigest()


# ============================================================
# 生成与缓存
# ============================================================

def generate_fractal(params: FractalParams) -> Image.Image:
    """根据参数生成分形图像"""
    span_x = 3.5 / params.zoom
    span_y = 3.0 / params.zoom
    x_min = params.center_x - span_x / 2
    x_max = params.center_x + span_x / 2
    y_min = params.center_y - span_y / 2
    y_max = params.center_y + span_y / 2

    if params.fractal_type == "mandelbrot":
        iters = _mandelbrot_kernel(
            int(params.width), int(params.height), int(params.max_iter),
            float(x_min), float(x_max), float(y_min), float(y_max),
        )
    elif params.fractal_type == "julia":
        iters = _julia_kernel(
            int(params.width), int(params.height), int(params.max_iter),
            float(params.julia_c[0]), float(params.julia_c[1]),
            float(x_min), float(x_max), float(y_min), float(y_max),
        )
    else:
        raise ValueError(f"未知分形类型: {params.fractal_type}")

    arr = _colorize(iters, int(params.max_iter), params.colormap)
    return Image.fromarray(arr)


def image_to_bytes(img: Image.Image, fmt: str = "PNG", **kwargs) -> bytes:
    """PIL.Image -> bytes (默认 PNG, 支持 compress_level 优化)"""
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=64)
def _cached_generate(cache_key: str, params: FractalParams) -> bytes:
    """按 cache_key 缓存生成的 PNG 字节 (可被 Streamlit 跨会话复用)"""
    img = generate_fractal(params)
    return image_to_bytes(img, compress_level=3)


def get_fractal_bytes(params: FractalParams) -> bytes:
    return _cached_generate(params.cache_key(), params)


# ============================================================
# 预热 numba (首次编译)
# ============================================================

def warmup_numba():
    """用小尺寸跑一次, 触发 JIT 编译, 避免用户等待"""
    _mandelbrot_kernel(4, 4, 8, -2.0, 1.0, -1.5, 1.5)
    _julia_kernel(4, 4, 8, -0.7, 0.27, -2.0, 1.0, -1.5, 1.5)


# ============================================================
# Streamlit UI
# ============================================================

st.set_page_config(
    page_title="分形处理自动化工具",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌀 分形处理自动化工具")
st.caption("Mandelbrot / Julia 生成 · 批量参数扫描 · 动画序列导出")


# ---------------- 侧边栏: 全局参数 ----------------
st.sidebar.header("⚙️ 参数配置")

fractal_type = st.sidebar.selectbox("分形类型", ["mandelbrot", "julia"], index=0)
colormap = st.sidebar.selectbox(
    "配色方案",
    ["inferno", "viridis", "plasma", "magma", "cividis", "hot", "twilight"],
    index=0,
)
width = st.sidebar.slider("图像宽度", 200, 1600, 800, step=50)
height = st.sidebar.slider("图像高度", 200, 1200, 600, step=50)
max_iter = st.sidebar.slider("最大迭代次数", 32, 1024, 256, step=32)

with st.sidebar.expander("🎯 视图参数", expanded=True):
    zoom = st.slider("缩放倍数", 0.5, 20.0, 1.0, step=0.5)
    center_x = st.number_input("中心 X", value=-0.5, format="%.4f")
    center_y = st.number_input("中心 Y", value=0.0, format="%.4f")

if fractal_type == "julia":
    with st.sidebar.expander("Julia 参数 c", expanded=True):
        c_re = st.number_input("c 实部", value=-0.7, format="%.4f")
        c_im = st.number_input("c 虚部", value=0.27015, format="%.4f")
else:
    c_re, c_im = -0.7, 0.27015

base_params = FractalParams(
    fractal_type=fractal_type,
    width=width,
    height=height,
    max_iter=max_iter,
    zoom=zoom,
    center_x=center_x,
    center_y=center_y,
    julia_c=(c_re, c_im),
    colormap=colormap,
)


# ---------------- 首次启动预热 numba ----------------
if "numba_warmed" not in st.session_state:
    with st.spinner("首次启动: 正在编译加速内核 (仅需一次)..."):
        warmup_numba()
    st.session_state["numba_warmed"] = True


# ---------------- 主区域标签页 ----------------
tab_single, tab_auto, tab_anim = st.tabs(
    ["🖼️ 单图生成", "🔁 自动化批量处理", "🎞️ 动画序列"]
)


# ============================================================
# Tab 1: 单图生成
# ============================================================
with tab_single:
    st.subheader("单张分形图生成")
    col1, col2 = st.columns([1, 3])

    with col1:
        auto_update = st.checkbox("参数变化后自动更新", value=False)

        # 如果勾选自动更新, 参数变化时立即生成
        need_generate = st.button("🚀 生成图像", type="primary", use_container_width=True) or auto_update

        if need_generate:
            with st.spinner("计算中..."):
                t0 = time.time()
                data = get_fractal_bytes(base_params)
                st.session_state["single_img_bytes"] = data
                st.session_state["single_img_meta"] = {
                    "params": base_params,
                    "elapsed": time.time() - t0,
                    "from_cache": False,
                }
            # 简单判断: 若 5ms 内返回, 大概率是缓存命中
            meta = st.session_state["single_img_meta"]
            if meta["elapsed"] < 0.01:
                meta["from_cache"] = True

        if "single_img_bytes" in st.session_state:
            meta = st.session_state.get("single_img_meta", {})
            p: FractalParams = meta.get("params", base_params)
            info = f"⏱️ {meta.get('elapsed', 0):.3f}s"
            if meta.get("from_cache"):
                info += " (缓存)"
            st.caption(info)
            st.download_button(
                "💾 下载 PNG",
                data=st.session_state["single_img_bytes"],
                file_name=f"{p.fractal_type}_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True,
            )

    with col2:
        if "single_img_bytes" in st.session_state:
            st.image(st.session_state["single_img_bytes"], use_container_width=True)
        else:
            st.info("点击左侧按钮生成图像")


# ============================================================
# Tab 2: 自动化批量处理
# ============================================================
with tab_auto:
    st.subheader("批量参数扫描")
    st.markdown("指定参数范围, 自动生成多张图并打包下载")

    mode = st.radio(
        "扫描模式",
        ["缩放序列 (Zoom)", "迭代次数序列 (Iter)", "Julia c 值序列"],
        horizontal=True,
        key="batch_mode",
    )

    # 生成参数列表 (不使用 st.session_state, 每次 rerun 重建)
    param_list: List[Dict[str, Any]] = []

    if mode == "缩放序列 (Zoom)":
        z_min, z_max = st.slider("缩放范围", 0.5, 50.0, (1.0, 10.0), key="z_range")
        n_steps = st.number_input("步数", 2, 30, 8, key="z_steps")
        zooms = np.linspace(z_min, z_max, int(n_steps))
        param_list = [{"zoom": float(z)} for z in zooms]

    elif mode == "迭代次数序列 (Iter)":
        i_min, i_max = st.slider("迭代范围", 16, 1024, (64, 512), key="i_range")
        n_steps = st.number_input("步数", 2, 30, 8, key="i_steps")
        iters = np.linspace(i_min, i_max, int(n_steps)).astype(int)
        param_list = [{"max_iter": int(i)} for i in iters]

    else:
        c_re_range = st.slider("c 实部范围", -1.0, 1.0, (-0.8, 0.0), key="cr_range")
        c_im_range = st.slider("c 虚部范围", -1.0, 1.0, (0.0, 0.8), key="ci_range")
        n_steps = st.number_input("每维步数", 2, 10, 4, key="c_steps")
        for a in np.linspace(*c_re_range, int(n_steps)):
            for b in np.linspace(*c_im_range, int(n_steps)):
                param_list.append({"julia_c": (float(a), float(b))})

    st.write(f"📊 预计生成 **{len(param_list)}** 张图像")

    if st.button("▶️ 开始批量处理", type="primary", key="run_batch"):
        progress = st.progress(0)
        status = st.empty()
        preview_container = st.container()
        preview_cols = preview_container.columns(min(4, max(1, len(param_list))))

        # 批量时使用较小尺寸以加快速度
        batch_w = min(width, 800)
        batch_h = min(height, 600)

        zip_buf = io.BytesIO()
        t0 = time.time()
        total = len(param_list)

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, override in enumerate(param_list):
                status.text(f"处理 {idx + 1}/{total}: {override}")

                p = FractalParams(
                    fractal_type=base_params.fractal_type,
                    width=batch_w,
                    height=batch_h,
                    max_iter=override.get("max_iter", base_params.max_iter),
                    zoom=override.get("zoom", base_params.zoom),
                    center_x=base_params.center_x,
                    center_y=base_params.center_y,
                    julia_c=override.get("julia_c", base_params.julia_c),
                    colormap=base_params.colormap,
                )

                data = get_fractal_bytes(p)

                # 构建文件名
                suffix = "_".join(
                    f"{k}={v}" for k, v in override.items()
                ).replace("(", "").replace(")", "").replace(",", "_").replace(" ", "")
                name = f"{p.fractal_type}_{idx:03d}_{suffix}"

                # 直接写入 ZIP, 不再保留内存中的 PIL 对象
                zf.writestr(f"{name}.png", data)

                # 前 N 张预览
                if idx < len(preview_cols):
                    with preview_cols[idx % len(preview_cols)]:
                        st.image(data, caption=name[:44], use_container_width=True)

                progress.progress((idx + 1) / total)

        elapsed = time.time() - t0
        status.success(f"✅ 批量完成, 共 {total} 张, 用时 {elapsed:.2f}s")

        zip_buf.seek(0)
        st.download_button(
            "📦 下载全部 (ZIP)",
            data=zip_buf,
            file_name=f"fractals_batch_{int(time.time())}.zip",
            mime="application/zip",
            key="dl_batch",
        )


# ============================================================
# Tab 3: 动画序列
# ============================================================
with tab_anim:
    st.subheader("缩放动画帧生成")
    st.markdown("生成连续缩放的帧序列, 可用 ffmpeg 合成视频")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        n_frames = st.number_input("帧数", 5, 120, 20, key="anim_frames")
    with col_b:
        z_start = st.number_input("起始缩放", 0.5, 100.0, 1.0, key="z_start")
    with col_c:
        z_end = st.number_input("结束缩放", 1.0, 5000.0, 50.0, key="z_end")

    target_x = st.number_input(
        "缩放目标点 X", value=-0.743643887037151, format="%.12f", key="tx"
    )
    target_y = st.number_input(
        "缩放目标点 Y", value=0.13182590420533, format="%.12f", key="ty"
    )

    anim_w = st.slider("动画帧宽度", 200, 1200, min(width, 800), step=50, key="anim_w")
    anim_h = st.slider("动画帧高度", 200, 900, min(height, 600), step=50, key="anim_h")

    if st.button("🎬 生成动画帧", type="primary", key="run_anim"):
        progress = st.progress(0)
        status = st.empty()
        preview_holder = st.empty()
        zip_buf = io.BytesIO()

        total = int(n_frames)
        # 若首尾为 0 或负值则保护
        z_s = max(z_start, 1e-6)
        z_e = max(z_end, 1e-6)
        log_s = np.log(z_s)
        log_e = np.log(z_e)

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(total):
                t = i / (total - 1) if total > 1 else 0.0
                z = float(np.exp(log_s * (1 - t) + log_e * t))

                p = FractalParams(
                    fractal_type=base_params.fractal_type,
                    width=anim_w,
                    height=anim_h,
                    max_iter=base_params.max_iter,
                    zoom=z,
                    center_x=target_x,
                    center_y=target_y,
                    julia_c=base_params.julia_c,
                    colormap=base_params.colormap,
                )
                data = get_fractal_bytes(p)
                zf.writestr(f"frame_{i:04d}.png", data)

                step = max(1, total // 6)
                if i % step == 0 or i == total - 1:
                    preview_holder.image(
                        data,
                        caption=f"Frame {i} | zoom={z:.2f}",
                        use_container_width=True,
                    )

                progress.progress((i + 1) / total)
                status.text(f"生成帧 {i + 1}/{total} (zoom={z:.2f})")

        zip_buf.seek(0)
        status.success(f"✅ 完成 {total} 帧")
        st.download_button(
            "📦 下载帧序列 (ZIP)",
            data=zip_buf,
            file_name=f"fractal_frames_{int(time.time())}.zip",
            mime="application/zip",
            key="dl_anim",
        )
        st.info(
            "合成视频示例:\n\n"
            "```bash\n"
            "ffmpeg -framerate 24 -i frame_%04d.png "
            "-c:v libx264 -pix_fmt yuv420p fractal_zoom.mp4\n"
            "```"
        )