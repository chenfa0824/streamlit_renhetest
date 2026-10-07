import streamlit as st

# 定义标签名称列表
tab1, tab2, tab3 = st.tabs(["首页", "数据看板", "设置"])

with tab1:
    st.header("首页页面")
    st.write("这里是首页内容")

with tab2:
    st.header("数据看板")
    st.line_chart([1,3,2,5])

with tab3:
    st.header("系统设置")
    st.slider("调节参数", 0, 100)