import streamlit as st
from streamlit_option_menu import option_menu

# 侧边栏美化导航
with st.sidebar:
    selected = option_menu(
        menu_title="主菜单",  # 导航标题
        options=["首页", "数据解析", "可视化", "系统配置"],  # 选项
        icons=["house", "database", "bar-chart", "gear"], # 图标
        menu_icon="cast",
        default_index=0,
    )

# 根据选择渲染页面
if selected == "首页":
    st.title("首页")
elif selected == "数据解析":
    st.title("数据解析页面")