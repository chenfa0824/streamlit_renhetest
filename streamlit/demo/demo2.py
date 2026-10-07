# Streamlit 是 Python 中最易用的 Web 应用开发库，
# 能让你用纯 Python 代码快速搭建交互式数据可视化页面，无需前端知识
import os

# 导入 streamlit 库，简写为 st（行业惯例）
import streamlit as st
import pandas as pd

# 设置页面的配置项
st.set_page_config(
    page_title="我的第一个Streamlit应用",
    page_icon=":smiley:",
    # 占满整个区域
    layout="wide",
    initial_sidebar_state="auto"
)

# 1. 标题/文本类组件（页面基础布局）
st.title("我的第一个Streamlit应用")  # 主标题
st.header("这是一级标题")  # 一级标题
st.subheader("这是二级标题")  # 二级标题
st.text("这是普通文本")  # 普通文本
st.markdown("**这是Markdown文本**")  # 支持Markdown语法

# 引入图片 音频 视频
# st.image("../images/1.jpg")
st.text("这是图片")
st.image("static/images/1.jpg")
st.text("这是音频")
st.audio("static/videos/1.m4a")
st.text("这是视频")
st.video("static/videos/1.mp4", width=1200)

st.text("用 st.markdown 嵌入原生 <video>")
# 将视频放在 .streamlit/static/ 目录下
video_path = ".streamlit/static/videos/1.mp4"  # 或 ".streamlit/static/videos/1.mp4"
video_html = f"""
<video width="600" height="400" controls>
    <source src="{video_path}" type="video/mp4">
</video>
"""
st.markdown(video_html, unsafe_allow_html=True)

# 测试用的在线视频
test_video = "https://www.w3schools.com/html/mov_bbb.mp4"
video_html = f"""
<video width="600" height="400" controls>
    <source src="{test_video}" type="video/mp4">
</video>
"""
st.markdown(video_html, unsafe_allow_html=True)

# st插入表格
# ---------------------- 2. 构造测试数据 ----------------------
data = {
    "姓名": ["张三", "李四", "王五", "赵六"],
    "年龄": [22, 25, 30, 28],
    "城市": ["北京", "上海", "广州", "深圳"],
    "职业": ["学生", "工程师", "设计师", "产品经理"]
}
df = pd.DataFrame(data)

# ---------------------- 3. 最简单表格（静态） ----------------------
st.subheader("1. 基础静态表格 st.table()")
st.table(df)

# ---------------------- 4. 带排序、搜索的表格（推荐） ----------------------
st.subheader("2. 交互式数据表格 st.dataframe()")
st.dataframe(df, use_container_width=True)

# ---------------------- 5. 可编辑表格 ----------------------
st.subheader("3. 可编辑表格 st.data_editor()")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)


# 2. 交互式组件（按钮、输入框）
name = st.text_input("请输入你的名字")  # 文本输入框
age = st.slider("请选择你的年龄", 0, 100, 20)  # 滑块
# 3. 条件渲染（根据输入展示内容）
if st.button("提交"):  # 按钮组件
    st.success(f"你好 {name}，你的年龄是 {age} 岁！")
    # 展示数据（表格/图表）
    st.dataframe({
        "姓名": [name],
        "年龄": [age]
    })
st.checkbox("记住密码")