import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ========== 1. 文本、标题组件 ==========
st.title("Streamlit 完整入门教程")  # 大标题
st.header("一级子标题")
st.subheader("二级小标题")
st.write("普通文本，支持自动渲染表格、数字、字符串")
st.markdown("## Markdown语法：**加粗**、*斜体*、[链接](https://streamlit.io)")
st.code("print('Python代码块展示')", language="python")
st.code("print('Python代码块展示')", language="java")
st.divider()  # 分割线

# ========== 2. 数据展示 ==========
st.header("数据表格展示")
df = pd.DataFrame({
    "姓名": ["小明", "小红", "小刚"],
    "分数": [88, 95, 76],
    "班级": ["一班", "二班", "一班"]
})
st.dataframe(df)  # 可交互表格（排序、拖拽列）
st.table(df)      # 静态表格
st.metric(label="平均分", value=df["分数"].mean(), delta="+5.2")  # 指标卡片

# ========== 3. 交互控件（核心：实现页面动态变化） ==========
st.header("交互式输入控件")
# 文本输入
name = st.text_input("请输入姓名：")
st.write(f"你输入的名字：{name}")

# 数字滑块
score = st.slider("选择分数", min_value=0, max_value=100, value=60)
st.write(f"当前分数：{score}")

# 下拉选择
cls = st.selectbox("选择班级", ["一班", "二班", "三班"])

# 多选框
hobby = st.multiselect("兴趣", ["篮球", "画画", "游戏"])

# 单选按钮
gender = st.radio("性别", ["男", "女"])

# 勾选框
agree = st.checkbox("同意用户协议")
if agree:
    st.success("已同意！")

# 按钮
if st.button("点击提交"):
    st.info("提交成功")

st.divider()

# ========== 4. 文件上传（常用数据分析功能） ==========
st.header("CSV文件上传解析")
upload_file = st.file_uploader("上传csv文件", type="csv")
if upload_file is not None:
    upload_df = pd.read_csv(upload_file)
    st.dataframe(upload_df)

# ========== 5. 绘图支持 ==========
st.header("图表绘制")
x = np.linspace(0, 10, 100)
y = np.sin(x)

# matplotlib图
fig, ax = plt.subplots()
ax.plot(x, y)
st.pyplot(fig)

# 内置简易折线图
st.line_chart(pd.DataFrame({"sin": y, "cos": np.cos(x)}))

# ========== 6. 布局优化（侧边栏、多列） ==========
st.header("页面布局")
# 侧边栏控件
with st.sidebar:
    st.slider("侧边栏滑块", 0, 100)
    st.selectbox("侧边栏下拉", ["hhh", "123"])

# 多列并排
col1, col2, col3 = st.columns(3)
with col1:
    st.button("按钮1")
with col2:
    st.button("按钮2")
with col3:
    st.button("按钮3")

# 折叠容器
with st.expander("点击展开详情"):
    st.write("隐藏内容")

# ========== 7. 提示状态 ==========
st.success("成功提示")
st.warning("警告提示")
st.error("错误提示")
st.info("普通信息")