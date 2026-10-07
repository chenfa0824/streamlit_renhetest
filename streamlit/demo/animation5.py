import streamlit as st
import time
import random
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ======================
# 页面配置（高级模式）
# ======================
st.set_page_config(
    page_title="高级动画特效",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================
# 自定义CSS 渐变/动画
# ======================
st.markdown("""
<style>
.gradient-text {
    font-size: 40px;
    font-weight: bold;
    background: linear-gradient(90deg, #ff0080, #00bfff, #ffcc00);
    -webkit-background-clip: text;
    color: transparent;
    animation: gradient 3s ease infinite;
}
@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.animate-number {
    font-size: 50px;
    color: #00bfff;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ======================
# 标题（渐变动画文字）
# ======================
st.markdown('<p class="gradient-text">✨ Streamlit 高级动画特效平台</p>', unsafe_allow_html=True)
st.markdown("---")

# ==============================================
# 1. 动态数字滚动动画（订单数/接口QPS/性能面板）
# ==============================================
st.subheader("1️⃣ 动态数字滚动动画（实时监控风格）")
num_placeholder = st.empty()
if st.button("▶️ 启动滚动数字"):
    target = random.randint(8000, 15000)
    current = 0
    while current < target:
        current += random.randint(50, 200)
        if current > target:
            current = target
        num_placeholder.markdown(f'<p class="animate-number">订单总数：{current}</p>', unsafe_allow_html=True)
        time.sleep(0.03)
st.markdown("---")

# ==============================================
# 2. 3D 动态图表动画
# ==============================================
st.subheader("2️⃣ 3D 动态实时折线图动画")
chart_placeholder = st.empty()
if st.button("▶️ 启动3D动态图表"):
    x = np.arange(0, 100, 2)
    for i in range(40):
        y = np.sin(x / 6 + i * 0.2) * 10 + random.randint(-3, 3)
        df = {"X轴": x, "实时接口响应时间": y}
        fig = px.line(df, x="X轴", y="实时接口响应时间", 
                      title="3D风格实时监控图表",
                      template="plotly_dark",
                      color_discrete_sequence=["#00bfff"])
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.1)
st.markdown("---")

# ==============================================
# 3. 高级打字机（彩色+逐字）
# ==============================================
st.subheader("3️⃣ 高级彩色打字机动画")
text_content = """
🚀 欢迎使用高级动画演示平台
✅ 支持：粒子特效 / 3D图表 / 数字滚动
✅ 适用：接口测试平台 / 订单监控 / 数据可视化
✅ 纯Python实现，零前端代码
✅ 一键运行，炫酷展示！
"""
type_placeholder = st.empty()
if st.button("▶️ 启动彩色打字机"):
    res = ""
    for c in text_content:
        res += c
        type_placeholder.success(res)
        time.sleep(0.03)
st.markdown("---")

# ==============================================
# 4. 波浪加载动画（超高级UI）
# ==============================================
st.subheader("4️⃣ 波浪加载动画（登录/处理中专用）")
if st.button("▶️ 启动波浪加载"):
    with st.spinner("🌊 正在处理数据，请稍候..."):
        for i in range(1, 6):
            st.info(f"加载进度：{i*20}%")
            time.sleep(0.4)
        st.success("✅ 数据加载完成！")
        st.balloons()
st.markdown("---")

# ==============================================
# 5. 星光飘落 + 庆祝粒子动画
# ==============================================
st.subheader("5️⃣ 粒子庆祝动画（测试平台专用）")
col1, col2 = st.columns(2)
with col1:
    if st.button("🎈 气球庆祝"):
        st.balloons()
with col2:
    if st.button("❄️ 星光飘落"):
        st.snow()
st.markdown("---")

# ==============================================
# 6. 实时动态仪表盘（Gauge 图表）
# ==============================================
st.subheader("6️⃣ 实时仪表盘动画（服务器CPU/接口性能）")
gauge_placeholder = st.empty()
if st.button("▶️ 启动仪表盘"):
    for i in range(60):
        val = random.randint(20, 85)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val,
            title = {'text': "接口CPU使用率"},
            gauge = {'axis': {'range': [0, 100]},
                     'bar': {'color': "cyan"}}
        ))
        gauge_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.2)

st.markdown("---")
st.markdown("## 🎯 **演示完成！这就是企业级炫酷动画页面**")