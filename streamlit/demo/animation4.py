import streamlit as st
import time
import random

# ----------------------
# 页面配置
# ----------------------
st.set_page_config(
    page_title="Streamlit 动画特效 Demo",
    page_icon="🎉",
    layout="wide"
)

st.title("🎉 Streamlit 超酷动画效果演示")
st.markdown("---")

# ----------------------
# 1. 自带特效
# ----------------------
st.subheader("1. Streamlit 自带魔法特效")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🎈 飘气球"):
        st.balloons()

with col2:
    if st.button("🎉 撒彩带"):
        st.snow()

with col3:
    if st.button("🔥 庆祝"):
        st.success("庆祝成功！")
        st.balloons()

with col4:
    if st.button("ℹ️ 提示消息"):
        st.info("这是一条提示消息")

st.markdown("---")

# ----------------------
# 2. 进度条动画
# ----------------------
st.subheader("2. 进度条动画")
progress_bar = st.progress(0)
status_text = st.empty()

if st.button("▶️ 启动进度条"):
    for i in range(101):
        progress_bar.progress(i)
        status_text.text(f"进度：{i}%")
        time.sleep(0.05)
    status_text.text("✅ 加载完成！")

st.markdown("---")

# ----------------------
# 3. 文字打字机效果
# ----------------------
st.subheader("3. 打字机动画效果")
text = """
大家好，我是 Streamlit！
我不需要前端知识，
纯 Python 就能做出炫酷页面～
我可以做：
✅ 接口测试工具
✅ 数据可视化
✅ 自动化测试平台
✅ 订单查询工具
"""

if st.button("⌨️ 启动打字机"):
    typed_text = st.empty()
    t = ""
    for char in text:
        t += char
        typed_text.markdown(f"`{t}`")
        time.sleep(0.02)

st.markdown("---")

# ----------------------
# 4. 数字动态刷新
# ----------------------
st.subheader("4. 实时数据动画（模拟监控）")
real_time_num = st.empty()

if st.button("📊 启动实时数字刷新"):
    for i in range(30):
        num = random.randint(10, 100)
        real_time_num.metric("实时接口QPS", f"{num} 请求/秒")
        time.sleep(0.3)

st.markdown("---")

# ----------------------
# 5. 表单提交动画
# ----------------------
st.subheader("5. 表单提交成功动画")
with st.form("test_form"):
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    submit = st.form_submit_button("登录")

if submit:
    with st.spinner("🔄 正在登录中..."):
        time.sleep(1.5)
    st.success("✅ 登录成功！")
    st.balloons()

st.markdown("---")
st.markdown("### 🔥 更多炫酷效果，我可以继续给你写！")