import streamlit as st
import pandas as pd
import numpy as np
import time

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Streamlit Tabs 完整 Demo",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 初始化 session_state ====================
if "result" not in st.session_state:
    st.session_state.result = None
if "history" not in st.session_state:
    st.session_state.history = []
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = None


# ==================== 工具函数 ====================
@st.cache_data
def generate_data(rows: int, seed: int) -> pd.DataFrame:
    """生成示例数据（带缓存）"""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    df = pd.DataFrame(
        {
            "日期": dates,
            "销售额": rng.integers(100, 1000, rows),
            "订单量": rng.integers(10, 100, rows),
            "客单价": rng.normal(50, 10, rows).round(2),
            "地区": rng.choice(["北京", "上海", "广州", "深圳"], rows),
        }
    )
    return df


def heavy_computation(n: int) -> int:
    """模拟耗时计算"""
    time.sleep(2)
    return sum(range(n))


# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚙️ 控制面板")
    rows = st.slider("数据行数", 10, 500, 100, step=10)
    seed = st.number_input("随机种子", 0, 9999, 42)
    st.divider()
    st.caption("💡 所有 Tab 内容都会执行，切换不重新计算（有缓存）")


# ==================== 标题 ====================
st.title("📑 Streamlit Tabs 完整 Demo")
st.caption("演示 Tabs 的各种用法：数据、图表、表单、状态、嵌套")

# ==================== 主 Tabs ====================
tab_data, tab_chart, tab_form, tab_state, tab_nested = st.tabs(
    ["📋 数据表", "📊 可视化", "📝 表单", "🔄 状态管理", "🗂️ 嵌套示例"]
)


# ---------- Tab 1: 数据表 ----------
with tab_data:
    st.subheader("数据预览")

    df = generate_data(rows, seed)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总销售额", f"¥{df['销售额'].sum():,}")
    col2.metric("总订单量", f"{df['订单量'].sum():,}")
    col3.metric("平均客单价", f"¥{df['客单价'].mean():.2f}")
    col4.metric("地区数", df["地区"].nunique())

    st.divider()

    # 筛选
    regions = st.multiselect(
        "筛选地区",
        options=df["地区"].unique().tolist(),
        default=df["地区"].unique().tolist(),
    )
    filtered = df[df["地区"].isin(regions)]

    st.dataframe(filtered, use_container_width=True, height=400)

    # 下载
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ 下载 CSV",
        data=csv,
        file_name="data.csv",
        mime="text/csv",
    )


# ---------- Tab 2: 可视化 ----------
with tab_chart:
    st.subheader("数据可视化")

    df = generate_data(rows, seed)

    chart_type = st.radio(
        "选择图表类型",
        ["折线图", "柱状图", "面积图", "散点图"],
        horizontal=True,
    )

    if chart_type == "折线图":
        st.line_chart(df.set_index("日期")[["销售额", "订单量"]])
    elif chart_type == "柱状图":
        st.bar_chart(df.set_index("日期")["销售额"])
    elif chart_type == "面积图":
        st.area_chart(df.set_index("日期")[["销售额", "订单量"]])
    else:
        st.scatter_chart(df, x="客单价", y="销售额", color="地区")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.write("**各地区的销售额总和**")
        region_sum = df.groupby("地区")["销售额"].sum()
        st.bar_chart(region_sum)
    with col2:
        st.write("**客单价分布**")
        st.bar_chart(np.histogram(df["客单价"], bins=20)[0])


# ---------- Tab 3: 表单 ----------
with tab_form:
    st.subheader("表单示例")

    st.markdown("使用 `st.form` 可以批量提交，避免每次输入都触发重跑。")

    with st.form("user_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("姓名", placeholder="请输入姓名")
            age = st.number_input("年龄", 1, 120, 25)
        with col2:
            email = st.text_input("邮箱", placeholder="example@mail.com")
            gender = st.selectbox("性别", ["男", "女", "其他"])

        bio = st.text_area("个人简介", placeholder="简单介绍一下自己...")
        agree = st.checkbox("我同意条款和条件")

        submitted = st.form_submit_button("✅ 提交", use_container_width=True)

    if submitted:
        if not agree:
            st.error("请先同意条款和条件")
        elif not name:
            st.warning("请填写姓名")
        else:
            st.session_state.form_submitted = {
                "姓名": name,
                "年龄": age,
                "邮箱": email,
                "性别": gender,
                "简介": bio,
            }
            st.success("提交成功！")

    if st.session_state.form_submitted:
        st.divider()
        st.write("**最近一次提交：**")
        st.json(st.session_state.form_submitted)


# ---------- Tab 4: 状态管理 ----------
with tab_state:
    st.subheader("跨 Tab 状态管理")
    st.markdown(
        "演示：在 Tab A 中触发耗时计算，结果显示在 Tab B 中。"
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.write("**触发计算**")
        n = st.number_input("计算规模 (n)", 1000, 10_000_000, 1_000_000, step=1000)

        if st.button("🚀 开始计算", type="primary", use_container_width=True):
            with st.spinner("计算中（约 2 秒）..."):
                st.session_state.result = heavy_computation(n)
                st.session_state.history.append(
                    {"n": n, "result": st.session_state.result, "time": time.strftime("%H:%M:%S")}
                )
            st.rerun()

        if st.button("🗑️ 清空历史", use_container_width=True):
            st.session_state.result = None
            st.session_state.history = []
            st.rerun()

    with col2:
        st.write("**计算结果**")
        if st.session_state.result is not None:
            st.metric("计算结果", f"{st.session_state.result:,}")
        else:
            st.info("暂无结果，请在左侧触发计算")

        if st.session_state.history:
            st.write("**历史记录**")
            st.dataframe(
                pd.DataFrame(st.session_state.history),
                use_container_width=True,
                hide_index=True,
            )


# ---------- Tab 5: 嵌套示例 ----------
with tab_nested:
    st.subheader("嵌套 Tabs")

    top_tab1, top_tab2 = st.tabs(["📦 主分类 1", "📦 主分类 2"])

    with top_tab1:
        sub1, sub2, sub3 = st.tabs(["子页 A", "子页 B", "子页 C"])
        with sub1:
            st.success("这是 主分类1 → 子页A 的内容")
            st.write("可以在这里放置任何 Streamlit 组件")
        with sub2:
            st.info("这是 主分类1 → 子页B 的内容")
            st.line_chart(np.random.randn(20, 3))
        with sub3:
            st.warning("这是 主分类1 → 子页C 的内容")

    with top_tab2:
        sub1, sub2 = st.tabs(["子页 X", "子页 Y"])
        with sub1:
            st.success("这是 主分类2 → 子页X 的内容")
        with sub2:
            st.info("这是 主分类2 → 子页Y 的内容")
            st.dataframe(
                pd.DataFrame(
                    {"名称": ["A", "B", "C"], "数值": [1, 2, 3]}
                ),
                use_container_width=True,
            )


# ==================== 页脚 ====================
st.divider()
st.caption("📑 Streamlit Tabs Demo · 使用 st.tabs() 组织内容")