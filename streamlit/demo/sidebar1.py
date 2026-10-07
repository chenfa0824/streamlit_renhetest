import streamlit as st

# 页面配置，侧边栏默认收起
st.set_page_config(
    page_title="侧边栏演示",
    initial_sidebar_state="collapsed"  # auto / expanded / collapsed
)

# 侧边栏标题
st.sidebar.title("系统导航")
st.sidebar.header("功能菜单")
st.sidebar.subheader("筛选参数")

# 侧边栏输入控件
username = st.sidebar.text_input("用户名")
age = st.sidebar.slider("年龄", 0, 100)
gender = st.sidebar.radio("性别", ["男", "女"])
upload = st.sidebar.file_uploader("上传文件")

# 侧边栏分割线、按钮
st.sidebar.divider()
submit_btn = st.sidebar.button("确认提交")

# 主页面内容
st.title("主页面内容")
st.write(f"用户：{username}，年龄：{age}")