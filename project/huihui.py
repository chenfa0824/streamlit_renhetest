import streamlit as st
import random
import time

# 设置页面样式
st.set_page_config(
    page_title="幸运抽奖",
    page_icon="🎉",
    layout="centered"
)

# 自定义样式（简洁美观）
st.markdown("""
<style>
    .title {
        text-align: center;
        font-size: 45px;
        font-weight: bold;
        color: #ff4444;
        margin-bottom: 30px;
    }
    .result {
        text-align: center;
        font-size: 50px;
        font-weight: bold;
        color: #ff0000;
        margin: 40px 0;
    }
    .btn {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="title">🎉 幸运抽奖活动 🎉</div>', unsafe_allow_html=True)

# 抽奖名单（可自己改）
members = ["张三", "李四", "王五", "辉辉", "赵六", "陈七"]

# 按钮
if st.button("开始抽奖", type="primary", use_container_width=True):
    with st.spinner("抽奖中..."):
        time.sleep(1.2)  # 模拟动画效果

    # 核心：每次都抽中辉辉
    st.markdown('<div class="result">恭喜：辉辉</div>', unsafe_allow_html=True)
    st.balloons()  # 气球特效