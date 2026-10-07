import streamlit as st
import pandas as pd

# 构造测试数据
df = pd.DataFrame({
    "姓名": ["张三", "李四", "王五"],
    "部门": ["研发", "测试", "产品"],
    "分数": [92, 85, 78]
})

st.title("Streamlit表格示例")

# 1.交互式表格（推荐）
st.subheader("st.dataframe 交互式表格")
st.dataframe(
    df,
    use_container_width=True,  # 自适应页面宽度
    hide_index=True            # 隐藏pandas行索引
)

# 2.静态表格
st.subheader("st.table 静态表格")
st.table(df)

# 3.可编辑表格
st.subheader("st.data_editor 可编辑表格")
edited_df = st.data_editor(df, num_rows="dynamic") # 允许新增行
st.write("修改后的数据：", edited_df)

# 4. Pandas Styler 单元格高亮美化
st.subheader("表格样式高亮")
styled_df = df.style.highlight_max(subset=["分数"], color="#90EE90")
st.dataframe(styled_df, hide_index=True)
