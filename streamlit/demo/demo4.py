import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time

# --------------------------
# 页面配置（必须放在第一行）
# --------------------------
st.set_page_config(
    page_title="数据大屏展示",
    layout="wide",        # 全屏宽布局（大屏必备）
    initial_sidebar_state="collapsed"
)

# --------------------------
# 自定义样式（美化大屏）
# --------------------------
st.markdown("""
<style>
/* 整体背景 */
.stApp {
    background-color: #0E1117;
    color: white;
}

/* 标题样式 */
.main-title {
    font-size: 40px !important;
    text-align: center;
    font-weight: 800;
    color: #00CCFF;
    margin-bottom: 20px;
}

/* 卡片样式 */
.card {
    background-color: #1A1C23;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    margin-bottom: 20px;
}
.card-title {
    font-size: 18px;
    color: #AAAAAA;
}
.card-value {
    font-size: 32px;
    font-weight: bold;
    color: #00FFAA;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# 生成模拟数据（可替换为你的真实数据）
# --------------------------
def generate_data():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    df = pd.DataFrame({
        '日期': dates,
        '访问量': np.random.randint(200, 1000, size=30),
        '销售额': np.random.uniform(1000, 5000, size=30).round(2),
        '转化率': np.random.uniform(0.05, 0.3, size=30).round(3)
    })

    # 地区数据
    regions = ['北京', '上海', '广州', '深圳', '杭州', '成都', '重庆']
    region_df = pd.DataFrame({
        '地区': regions,
        '用户数': np.random.randint(500, 3000, size=7)
    })

    # 类型占比
    types = ['移动端', 'PC端', '小程序', 'API']
    type_df = pd.DataFrame({
        '来源': types,
        '占比': np.random.dirichlet(np.ones(4), size=1)[0]
    })

    return df, region_df, type_df

# --------------------------
# 大屏标题
# --------------------------
st.markdown('<p class="main-title">📊 企业实时数据可视化大屏</p>', unsafe_allow_html=True)

# 显示当前时间
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"<div style='text-align:center; font-size:20px; margin-bottom:30px'>🕒 更新时间：{now}</div>", unsafe_allow_html=True)

# --------------------------
# 生成数据
# --------------------------
df, region_df, type_df = generate_data()

# --------------------------
# 第一行：4个数据卡片
# --------------------------
col1, col2, col3, col4 = st.columns(4)
total_visit = df['访问量'].sum()
total_sales = df['销售额'].sum()
avg_cvr = df['转化率'].mean()
total_user = region_df['用户数'].sum()

with col1:
    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>总访问量</div>
        <div class='card-value'>{total_visit:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>总销售额</div>
        <div class='card-value'>¥{total_sales:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>平均转化率</div>
        <div class='card-value'>{avg_cvr:.1%}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>总用户数</div>
        <div class='card-value'>{total_user:,}</div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# 第二行：图表区域
# --------------------------
left_col, mid_col, right_col = st.columns([3, 2, 2])

# 左：趋势图
with left_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📈 访问量趋势")
    fig = px.line(df, x='日期', y='访问量', template='plotly_dark')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 中：地区柱状图
with mid_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🌍 各地区用户数")
    fig = px.bar(region_df, x='地区', y='用户数', color='用户数', template='plotly_dark')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 右：来源饼图
with right_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📦 流量来源占比")
    fig = px.pie(type_df, values='占比', names='来源', template='plotly_dark')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 第三行：数据表格
# --------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📋 近30日明细数据")
st.dataframe(df.style.format({
    "销售额": "¥{:.2f}",
    "转化率": "{:.1%}"
}), height=260, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 自动刷新（5秒）
# --------------------------
time.sleep(5)
st.rerun()