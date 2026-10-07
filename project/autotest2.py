import streamlit as st
import pandas as pd
from docx import Document
import io
import re

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="智能测试用例生成器",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------
# 酷炫样式
# --------------------------
st.markdown("""
<style>
    .title {
        font-size: 42px;
        text-align: center;
        font-weight: bold;
        color: #00CCFF;
        text-shadow: 0 0 10px #00CCFF;
        margin-bottom: 30px;
    }
    .card {
        background-color: #1A1C23;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,204,255,0.2);
        margin-bottom: 20px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------
# 文档读取工具
# --------------------------
def read_txt(file):
    return file.read().decode("utf-8")

def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# --------------------------
# 智能生成测试用例（核心）
# --------------------------
def generate_test_cases(content):
    lines = [l.strip() for l in content.split("\n") if l.strip() and len(l.strip()) > 5]
    cases = []
    
    for idx, line in enumerate(lines[:15]):  # 最多生成15条，避免过多
        case_id = f"TC_{idx+1:03d}"
        module = "功能模块"
        title = f"验证：{line[:20]}..."
        pre_condition = "正常进入系统，页面加载完成"
        step = f"1. 打开对应页面\n2. 查看/操作：{line}\n3. 确认功能正常"
        expect = "功能正常，界面无异常，数据显示正确"

        cases.append({
            "用例编号": case_id,
            "模块": module,
            "用例标题": title,
            "前置条件": pre_condition,
            "测试步骤": step,
            "预期结果": expect
        })
    return pd.DataFrame(cases)

# --------------------------
# 界面标题
# --------------------------
st.markdown('<p class="title">🧪 智能测试用例自动生成器</p>', unsafe_allow_html=True)

# --------------------------
# 上传区域
# --------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📤 上传需求文档（.txt / .docx）")
upload_file = st.file_uploader("支持：需求说明、功能描述、业务逻辑文档", type=["txt", "docx"])

content = ""
if upload_file:
    try:
        if upload_file.name.endswith(".txt"):
            content = read_txt(upload_file)
        elif upload_file.name.endswith(".docx"):
            content = read_docx(upload_file)
        
        st.success("✅ 文件读取成功！")
    except:
        st.error("❌ 文件读取失败")
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 生成按钮
# --------------------------
if content:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 生成的测试用例")
    
    if st.button("🚀 自动生成测试用例", type="primary", use_container_width=True):
        with st.spinner("正在分析需求、生成测试用例..."):
            df = generate_test_cases(content)
        
        # 展示用例
        st.dataframe(df, height=400, use_container_width=True)

        # 导出Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="测试用例")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 导出 Excel 测试用例",
            data=excel_data,
            file_name="测试用例.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👆 请上传文件后生成用例")