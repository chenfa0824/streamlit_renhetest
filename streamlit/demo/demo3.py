import streamlit as st
import pandas as pd
import numpy as np
import time

# ========= 页面配置，必须放在最顶部 =========
# 必须是第一条 Streamlit 命令。
# 如果你还import了其他库没关系，但在它之前不能出现st.write、st.title 等任何st.xxx调用
st.set_page_config(
    page_title="Streamlit综合Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== 缓存示例 =====================
@st.cache_data
def generate_sample_data(rows: int):
    """模拟生成测试数据，加缓存，不会重复计算"""
    df = pd.DataFrame({
        "序号": list(range(rows)),
        "销售额": np.random.randint(100, 1000, size=rows),
        "访问量": np.random.randint(50, 500, size=rows),
        "类别": np.random.choice(["A类","B类","C类"], size=rows)
    })
    return df

# ===================== 会话状态初始化 =====================
if "click_count" not in st.session_state:
    st.session_state.click_count = 0

# ===================== 侧边栏区域 =====================
with st.sidebar:
    st.title("📋 侧边栏控制面板")
    rows_num = st.slider("生成数据行数", min_value=10, max_value=200, value=50)
    select_category = st.multiselect("筛选类别", ["A类","B类","C类"], default=["A类","B类","C类"])
    uploaded_file = st.file_uploader("上传CSV文件", type=["csv"])

    st.divider()
    st.info(f"按钮点击次数：{st.session_state.click_count}")

# ===================== 主页面 =====================
st.title("🚀 Streamlit 综合演示案例")
st.markdown("**本demo包含常用全部基础组件，可直接复制运行**")

# 提示信息行
col_tip1, col_tip2, col_tip3, col_tip4 = st.columns(4)
with col_tip1:
    st.success("✅成功提示")
with col_tip2:
    st.info("ℹ️信息提示")
with col_tip3:
    st.warning("⚠️警告提示")
with col_tip4:
    st.error("❌错误提示")
st.divider()

# -------- 交互控件区域 --------
st.subheader("🎛️交互控件演示")
col1, col2, col3, col4 = st.columns(4)

with col1:
    user_name = st.text_input("请输入你的姓名", value="")
    btn_count = st.button("🔘点我计数")
    if btn_count:
        st.session_state.click_count += 1

with col2:
    age = st.number_input("输入年龄", min_value=0, max_value=120, value=25)
    agree = st.checkbox("我已阅读协议")

with col3:
    radio_opt = st.radio("单选选项", ["选项一", "选项二", "选项三"])
    slider_val = st.slider("滑块数值", 0, 100, 30)

with col4:
    select_opt = st.selectbox("下拉选择", ["苹果","香蕉","葡萄","西瓜"])
    input_area = st.text_area("多行文本", height=100)

st.write(f"你的输入：姓名={user_name}，年龄={age}，滑块={slider_val}，水果={select_opt}")

st.divider()

# -------- 折叠面板 --------
with st.expander("🔍点击展开查看代码示例"):
    st.code("""
import streamlit as st
st.title("hello streamlit")
""", language="python")
    st.latex(r"y = ax^2 + bx + c")

st.divider()

# -------- 数据 & 图表部分 --------
st.subheader("📊表格与图表")

# 获取缓存数据
df_raw = generate_sample_data(rows_num)
df_filter = df_raw[df_raw["类别"].isin(select_category)]

tab1, tab2, tab3 = st.tabs(["原始表格","指标卡片","图表"])
with tab1:
    st.dataframe(df_filter, use_container_width=True)
with tab2:
    m1, m2, m3 = st.columns(3)
    total_sale = df_filter["销售额"].sum()
    total_view = df_filter["访问量"].sum()
    avg_sale = df_filter["销售额"].mean()
    m1.metric("总销售额", f"{total_sale:,}")
    m2.metric("总访问量", f"{total_view:,}")
    m3.metric("平均销售额", f"{avg_sale:.1f}")
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(df_filter, x="序号", y="销售额", color="#ff4b4b")
    with c2:
        st.line_chart(df_filter, x="序号", y="访问量")

st.divider()

# -------- 文件上传处理 --------
st.subheader("📁文件上传处理")
if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        st.success("文件读取成功！")
        st.dataframe(df_upload.head(10), use_container_width=True)
    except Exception as e:
        st.error(f"读取失败：{e}")
else:
    st.info("请在左侧侧边栏上传csv文件")

st.divider()

# -------- 进度条&spinner演示 --------
st.subheader("⏳进度与加载动画演示")
if st.button("开始模拟任务"):
    with st.spinner("任务正在执行，请稍候..."):
        progress = st.progress(0)
        for i in range(100):
            progress.progress(i+1)
            time.sleep(0.02)
    st.balloons()
    st.success("🎉任务执行完成！")

st.divider()
st.markdown("*Demo结束，学习命令：streamlit run demo.py*")
