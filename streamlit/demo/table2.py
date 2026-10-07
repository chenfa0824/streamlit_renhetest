import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Streamlit 表格高级 Demo", layout="wide")
st.title("📊 Streamlit 表格高级用法 Demo")

# ==================== 缓存数据 ====================
@st.cache_data
def load_data(n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    names = [f"成员 {i:02d}" for i in range(n)]
    return pd.DataFrame({
        "成员": names,
        "周活跃趋势": [rng.integers(0, 100, size=12).tolist() for _ in range(n)],
        "近30天分布": [rng.integers(0, 50, size=30).tolist() for _ in range(n)],
        "完成率": np.round(rng.uniform(0, 1, n), 2),
        "经验值": rng.integers(100, 9999, n),
        "个人主页": [f"https://github.com/user{i}" for i in range(n)],
        "头像": [f"https://i.pravatar.cc/150?img={i % 70}" for i in range(n)],
        "简介": ["**Streamlit** 爱好者\n\n热爱数据可视化"] * n,
    })

df = load_data()

# ==================== Tab 1: Column Config 可视化列 ====================
tab_viz, tab_select, tab_edit = st.tabs(["🎨 可视化列配置", "🖱️ 行选择交互", "✏️ 可编辑表格"])

with tab_viz:
    st.subheader("column_config：把普通列变成可视化组件")

    st.markdown("""
    下面的表格使用了多种 `column_config` 列类型，**点击单元格**可以查看详情：
    """)

    st.dataframe(
        df,
        column_config={
            "成员": st.column_config.TextColumn("成员姓名", width="small", help="用户名称"),
            "周活跃趋势": st.column_config.LineChartColumn(
                "周活跃趋势", y_min=0, y_max=100, width="large",
                help="最近 12 周的活跃度变化",
            ),
            "近30天分布": st.column_config.BarChartColumn(
                "近30天分布", y_min=0, y_max=50, width="medium",
                help="最近 30 天的每日活动量",
            ),
            "完成率": st.column_config.ProgressColumn(
                "任务完成率", min_value=0, max_value=1, format="%.0f%%",
                width="small", help="已完成任务占总任务的比例",
            ),
            "经验值": st.column_config.NumberColumn(
                "经验值", min_value=0, format="%d 分",
                width="small", help="累计经验分数",
            ),
            "个人主页": st.column_config.LinkColumn(
                "个人主页", display_text="访问",
                width="small", help="点击跳转",
            ),
            "头像": st.column_config.ImageColumn(
                "头像", width="small", help="用户头像预览",
            ),
            "简介": st.column_config.MarkdownColumn(
                "简介", width="medium", help="Markdown 格式的个人简介",
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=500,
    )

    st.caption("💡 列类型包括：LineChart / BarChart / Progress / Link / Image / Markdown 等")


# ==================== Tab 2: 行选择交互 ====================
with tab_select:
    st.subheader("行选择：点击行即可获取选中数据")

    st.markdown("**点击任意一行**，下方会显示该行的详细趋势图。")

    event = st.dataframe(
        df,
        column_config={
            "成员": st.column_config.TextColumn("成员", width="small"),
            "周活跃趋势": st.column_config.LineChartColumn("趋势", y_min=0, y_max=100, width="medium"),
            "完成率": st.column_config.ProgressColumn("完成率", min_value=0, max_value=1, format="%.0f%%", width="small"),
            "经验值": st.column_config.NumberColumn("经验值", format="%d", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="row_select_table",
    )

    selected_rows = event.selection.rows

    if selected_rows:
        idx = selected_rows[0]
        row = df.iloc[idx]
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("选中成员", row["成员"])
        col2.metric("完成率", f"{row['完成率']:.0%}")
        col3.metric("经验值", f"{row['经验值']} 分")

        st.write("**该成员的周活跃趋势：**")
        trend_df = pd.DataFrame(
            {"活跃度": row["周活跃趋势"]},
            index=[f"第{i+1}周" for i in range(12)],
        )
        st.line_chart(trend_df)
    else:
        st.info("👆 点击上表中的任意一行查看详情")


# ==================== Tab 3: 可编辑表格 ====================
with tab_edit:
    st.subheader("data_editor：构建可交互的电子表格")

    st.markdown("""
    下面的表格是**可编辑的**：
    - 勾选复选框选择行
    - 修改数字列（会立即重新计算平均值）
    - 使用 `num_rows="dynamic"` 可以增删行
    """)

    edit_df = df[["成员", "经验值", "完成率"]].head(8).copy()

    edited = st.data_editor(
        edit_df,
        column_config={
            "成员": st.column_config.TextColumn("成员", disabled=True, width="small"),
            "经验值": st.column_config.NumberColumn(
                "经验值", min_value=0, max_value=99999, format="%d 分", width="small",
            ),
            "完成率": st.column_config.ProgressColumn(
                "完成率", min_value=0, max_value=1, format="%.0f%%", width="small",
            ),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="editable_table",
    )

    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("当前平均经验值", f"{edited['经验值'].mean():.0f}")
    col2.metric("当前平均完成率", f"{edited['完成率'].mean():.0%}")

    st.write("**编辑后的数据：**")
    st.dataframe(edited, hide_index=True, use_container_width=True)