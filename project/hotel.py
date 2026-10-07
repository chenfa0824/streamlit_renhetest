import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import time
import plotly.express as px

# --------------------------
# 页面配置（全屏酷炫模式）
# --------------------------
st.set_page_config(
    page_title="酒店数据大屏",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# 超酷炫科技风 CSS
# --------------------------
st.markdown("""
<style>
    .main {
        background-color: #0a0a0a;
        color: #ffffff;
    }
    .title {
        font-size: 50px;
        text-align: center;
        font-weight: bold;
        color: #00e0ff;
        text-shadow: 0 0 15px #00e0ff;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #ffffff;
        font-size: 20px;
        margin-bottom: 30px;
    }
    .card {
        background: #121212;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0,224,255,0.2);
        border: 1px solid #00e0ff;
        margin-bottom: 20px;
    }
    .city-label {
        color: #00ff9d;
        font-size: 24px;
        font-weight: bold;
    }
    div[data-testid="stTextInput"] input {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #00e0ff !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------
# 模拟酒店数据（真实场景可替换为爬虫/API）
# --------------------------
def get_hotel_data(city):
    brands = ["希尔顿", "万豪", "洲际", "全季", "汉庭", "如家", "7天", "维也纳", "亚朵", "丽枫"]
    platforms = ["携程", "美团", "飞猪"]
    
    data = []
    for i in range(1, 51):
        price = random.randint(150, 1200)
        score = round(random.uniform(4.2, 5.0), 1)
        sales = random.randint(20, 2000)
        brand = random.choice(brands)
        platform = random.choice(platforms)
        
        data.append({
            "酒店名称": f"{city}{brand}酒店{i}号店",
            "城市": city,
            "价格(元)": price,
            "评分": score,
            "月销量": sales,
            "平台": platform,
            "推荐指数": round((score * 0.6) + (sales / 2000 * 40), 1)
        })
    return pd.DataFrame(data)

# --------------------------
# 标题
# --------------------------
st.markdown('<p class="title">🏨 全国酒店实时数据大屏</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle">🕒 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)

# --------------------------
# 侧边栏：城市选择 + 筛选
# --------------------------
with st.sidebar:
    st.markdown("## 🎯 城市选择")
    city = st.text_input("输入当前城市", "北京")
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("## 🔍 筛选条件")
    min_price = st.slider("最低价格", 0, 1500, 200)
    max_price = st.slider("最高价格", 0, 1500, 1000)
    score_limit = st.slider("最低评分", 0.0, 5.0, 4.2)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("## 📊 排序方式")
    sort_type = st.radio("", ["价格↑", "价格↓", "评分↓", "销量↓", "推荐指数↓"])

# --------------------------
# 加载数据
# --------------------------
with st.spinner(f"正在获取 {city} 酒店数据..."):
    time.sleep(0.8)
    df = get_hotel_data(city)

# --------------------------
# 数据筛选
# --------------------------
df = df[(df["价格(元)"] >= min_price) & 
        (df["价格(元)"] <= max_price) & 
        (df["评分"] >= score_limit)]

# 排序
if sort_type == "价格↑": df = df.sort_values("价格(元)", ascending=True)
if sort_type == "价格↓": df = df.sort_values("价格(元)", ascending=False)
if sort_type == "评分↓": df = df.sort_values("评分", ascending=False)
if sort_type == "销量↓": df = df.sort_values("月销量", ascending=False)
if sort_type == "推荐指数↓": df = df.sort_values("推荐指数", ascending=False)

# --------------------------
# 顶部统计卡片
# --------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="card">
        <div style='color:#aaa'>当前城市</div>
        <div class='city-label'>{city}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        <div style='color:#aaa'>酒店总数</div>
        <div style='font-size:32px; color:#00ff9d'>{len(df)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card">
        <div style='color:#aaa'>平均价格</div>
        <div style='font-size:32px; color:#ffcc00'>{int(df['价格(元)'].mean())} 元</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="card">
        <div style='color:#aaa'>平均评分</div>
        <div style='font-size:32px; color:#ff5e5e'>{df['评分'].mean():.1f} 分</div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# 图表区域
# --------------------------
g1, g2 = st.columns(2)

with g1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 各平台酒店数量")
    fig = px.bar(df, x="平台", color="平台", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with g2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("💰 价格分布区间")
    fig = px.histogram(df, x="价格(元)", nbins=20, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 酒店数据表格
# --------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader(f"🏨 {city} 酒店实时数据列表")
st.dataframe(
    df.style
    .highlight_max(subset=["评分", "月销量", "推荐指数"], color="#265c4e")
    .format({"价格(元)": "{}", "评分": "{:.1f}", "推荐指数": "{:.1f}"}),
    height=400,
    use_container_width=True
)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 导出功能
# --------------------------
col_a, col_b = st.columns([1, 4])
with col_a:
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 导出数据CSV",
        data=csv,
        file_name=f"{city}酒店数据_{datetime.now().strftime('%Y%m%d%H%M')}.csv",
        mime="text/csv",
        type="primary"
    )

st.success(f"✅ 成功加载 {city} 酒店数据！")