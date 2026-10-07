import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time

# ========== 页面配置（必须是第一个 Streamlit 命令） ==========
st.set_page_config(
    page_title="Streamlit 基本 UI 演示",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========== 标题与文本 ==========
st.title("🌟 Streamlit 基本 UI 演示")
st.caption("一个涵盖常用组件的入门示例")

st.header("📝 文本与 Markdown")
st.markdown("""
Streamlit 支持 **Markdown** 语法，例如：
- 列表项 1
- 列表项 2
- `行内代码`
""")
st.write("这是 `st.write()`，可以输出文本、数据、图表等。")
st.text("这是 st.text()，显示纯文本。")

st.latex(r"e^{i\pi} + 1 = 0")
# 爱因斯坦质能方程
st.latex(r'E = mc^2')
# 带求和和分数的公式（注意 r 前缀）
st.latex(r'''
    a + ar + ar^2 + \cdots + ar^{n-1} =
    \sum_{k=0}^{n-1} ar^k =
    a \left(\frac{1-r^{n}}{1-r}\right)
''')
st.divider()  # 分隔线

# ========== 输入组件 ==========
st.header("🎛️ 输入组件")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("请输入你的名字", value="", placeholder="例如：小明")
    age = st.number_input("请输入年龄", min_value=0, max_value=120, value=25, step=1)
    birthday = st.date_input("选择生日", value=datetime(2000, 1, 1))
    meeting_time = st.time_input("选择时间", value=time(9, 0))

with col2:
    bio = st.text_area("个人简介", height=100, placeholder="介绍一下自己...")
    gender = st.radio("性别", ["男", "女", "其他"], horizontal=True)
    hobby = st.multiselect(
        "爱好",
        ["阅读", "运动", "音乐", "旅行", "游戏", "编程"],
        default=["阅读", "编程"],
    )
    agree = st.checkbox("我同意用户协议")

# 滑块
level = st.slider("选择熟练程度", 0, 100, 50)
price_range = st.slider("价格区间", 0.0, 100.0, (20.0, 80.0))

# 选择框
fruit = st.selectbox("选择你喜欢的水果", ["苹果", "香蕉", "樱桃", "榴莲"])

# 文件上传
uploaded_file = st.file_uploader("上传文件", type=["csv", "txt", "png", "jpg"])

# 颜色选择器
color = st.color_picker("选择一个颜色", "#FF4B4B")

st.divider()

# ========== 按钮与交互 ==========
st.header("🔘 按钮与交互")

bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("主要按钮", type="primary", use_container_width=True):
        st.success("主要按钮被点击了！")
with bcol2:
    if st.button("次要按钮", use_container_width=True):
        st.info("次要按钮被点击了！")
with bcol3:
    with st.popover("打开弹窗"):
        st.write("这是一个 popover 弹窗内容")
        st.button("弹窗内的按钮")

# 下载按钮
if name:
    st.download_button(
        label="下载问候语",
        data=f"你好，{name}！",
        file_name="greeting.txt",
        mime="text/plain",
    )

# 表单（避免每次输入都刷新）
with st.form("my_form"):
    st.subheader("表单示例")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        form_name = st.text_input("姓名")
    with fcol2:
        form_email = st.text_input("邮箱")
    submitted = st.form_submit_button("提交表单")
    if submitted:
        st.success(f"提交成功：{form_name} - {form_email}")

st.divider()

# ========== 数据展示 ==========
st.header("📊 数据展示")

# 数据框
df = pd.DataFrame(
    np.random.randn(10, 4),
    columns=["A", "B", "C", "D"],
    index=[f"行{i+1}" for i in range(10)],
)

tab1, tab2, tab3 = st.tabs(["DataFrame", "指标", "JSON"])

with tab1:
    st.dataframe(df, use_container_width=True)
    st.caption("st.dataframe —— 可交互的表格")

with tab2:
    m1, m2, m3 = st.columns(3)
    m1.metric("月活跃用户", "12.4K", "12%")
    m2.metric("转化率", "3.8%", "-0.6%")
    m3.metric("平均时长", "4m 32s", "8s")

with tab3:
    st.json({"姓名": "小明", "年龄": 25, "爱好": ["阅读", "编程"]})

# 静态表格
st.table(df.head(3))
st.caption("st.table —— 静态表格")

st.divider()

# ========== 图表 ==========
st.header("📈 图表")

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=["A", "B", "C"],
)

c1, c2 = st.columns(2)
with c1:
    st.line_chart(chart_data, height=250)
    st.caption("st.line_chart 折线图")
with c2:
    st.bar_chart(chart_data, height=250)
    st.caption("st.bar_chart 柱状图")

c3, c4 = st.columns(2)
with c3:
    st.area_chart(chart_data, height=250)
    st.caption("st.area_chart 面积图")
with c4:
    map_data = pd.DataFrame(
        np.random.randn(100, 2) / [50, 50] + [30.6, 104.06],  # 成都附近
        columns=["lat", "lon"],
    )
    st.map(map_data, height=250)
    st.caption("st.map 地图")

st.divider()

# ========== 状态与提示 ==========
st.header("💬 状态与提示")

st.success("✅ 这是一个成功提示")
st.info("ℹ️ 这是一个信息提示")
st.warning("⚠️ 这是一个警告提示")
st.error("❌ 这是一个错误提示")
st.exception(RuntimeError("这是一个异常示例"))

with st.spinner("加载中..."):
    import time as _time
    _time.sleep(1)
st.success("加载完成！")

# 进度条
progress = st.progress(0, text="进度演示")
if st.button("启动进度条动画"):
    for i in range(100):
        _time.sleep(0.01)
        progress.progress(i + 1, text=f"进度 {i+1}%")
    st.balloons()  # 气球动画

# 占位符
placeholder = st.empty()
placeholder.text("这是占位符的初始文本")
if st.button("更新占位符"):
    placeholder.text("占位符内容已更新！")

st.divider()

# ========== 布局 ==========
st.header("🧱 布局组件")

# 列
st.subheader("列布局 st.columns")
lcol1, lcol2, lcol3 = st.columns([2, 1, 1])
lcol1.write("宽度 2")
lcol2.write("宽度 1")
lcol3.write("宽度 1")

# 容器
st.subheader("容器 st.container")
with st.container(border=True):
    st.write("这是一个带边框的容器")
    st.write("里面可以放任意组件")

# 展开器
st.subheader("展开器 st.expander")
with st.expander("点击展开查看更多"):
    st.write("这里是隐藏的内容")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)

# 侧边栏
with st.sidebar:
    st.header("⚙️ 侧边栏")
    st.write("这里放全局设置")
    sidebar_option = st.selectbox("选择模式", ["模式 A", "模式 B", "模式 C"])
    sidebar_slider = st.slider("侧边栏滑块", 0, 10, 5)
    st.caption(f"当前选择：{sidebar_option}，数值：{sidebar_slider}")

st.divider()

# ========== 缓存示例 ==========
st.header("⚡ 缓存")

@st.cache_data
def expensive_computation(n):
    _time.sleep(2)  # 模拟耗时操作
    return sum(i * i for i in range(n))

if st.button("执行耗时计算（首次约2秒，之后缓存）"):
    result = expensive_computation(1000000)
    st.success(f"计算结果：{result}")

st.divider()

# ========== 会话状态 ==========
st.header("🗂️ 会话状态 st.session_state")

if "count" not in st.session_state:
    st.session_state.count = 0

s1, s2, s3 = st.columns(3)
with s1:
    if st.button("➕ 增加"):
        st.session_state.count += 1
with s2:
    if st.button("➖ 减少"):
        st.session_state.count -= 1
with s3:
    if st.button("🔄 重置"):
        st.session_state.count = 0

st.write(f"当前计数：**{st.session_state.count}**")

# ========== 页脚 ==========
st.divider()
st.caption("🌟 Streamlit 基本 UI 演示 —— 运行 `streamlit run app.py` 启动")