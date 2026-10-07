import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
import os

# 页面配置
st.set_page_config(page_title="接口自动化测试平台", page_icon="⚡", layout="wide")
st.title("⚡ 接口自动化测试用例生成 & 调试平台")

# 专家系统提示词
SYSTEM_PROMPT = """
你是顶级接口测试专家，根据接口文档生成标准接口测试用例。
输出规则：
1. 必须返回纯JSON数组，不要任何多余文字、解释、markdown
2. 每条用例包含：
   - case_id: 用例编号
   - module: 模块
   - title: 标题
   - method: 请求方法(GET/POST/PUT/DELETE)
   - url: 接口地址
   - headers: 请求头（字典）
   - params: 请求参数（字典）
   - body: 请求体（字典）
   - expect_code: 预期状态码
   - expect_msg: 预期提示
   - priority: 优先级
3. 覆盖：正常、必填缺参、类型错误、空值、边界、非法、权限异常
"""


# ----------------------
# 文件解析工具函数
# ----------------------
def parse_txt(file):
    return file.read().decode("utf-8")


def parse_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])


def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def parse_file(uploaded_file):
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".txt", ".md", ".json"]:
        return parse_txt(uploaded_file)
    elif ext in [".docx"]:
        return parse_docx(uploaded_file)
    elif ext in [".pdf"]:
        return parse_pdf(uploaded_file)
    else:
        st.error("不支持的文件格式")
        return ""


# ----------------------
# 1. 上传接口文档（支持PDF/DOCX/TXT）
# ----------------------
st.subheader("📁 上传接口文档")
upload_file = st.file_uploader(
    "支持格式：.pdf .docx .txt .md .json",
    type=["pdf", "docx", "txt", "md", "json"]
)
doc_text = ""

if upload_file:
    with st.spinner("正在解析文档..."):
        doc_text = parse_file(upload_file)
        st.success(f"✅ {upload_file.name} 解析成功！")

        with st.expander("查看文档内容"):
            st.text_area("文档内容", doc_text, height=300)

# ----------------------
# 2. 生成用例
# ----------------------
st.divider()
st.subheader("🚀 生成接口测试用例")

if st.button("开始生成用例", type="primary"):
    if not doc_text:
        st.warning("请先上传文档")
    else:
        with st.spinner("AI 生成测试用例中..."):
            # ======================
            # 真实环境替换成 LLM/Coze API
            # ======================
            mock_cases = [
                {
                    "case_id": "API_USER_001",
                    "module": "用户模块",
                    "title": "正常查询用户信息",
                    "method": "GET",
                    "url": "/api/user/info",
                    "headers": {"token": "your_token"},
                    "params": {"userId": 1001},
                    "body": {},
                    "expect_code": 200,
                    "expect_msg": "查询成功",
                    "priority": "高"
                },
                {
                    "case_id": "API_USER_002",
                    "module": "用户模块",
                    "title": "userId缺失",
                    "method": "GET",
                    "url": "/api/user/info",
                    "headers": {"token": "your_token"},
                    "params": {},
                    "body": {},
                    "expect_code": 400,
                    "expect_msg": "userId不能为空",
                    "priority": "高"
                },
                {
                    "case_id": "API_USER_003",
                    "module": "用户模块",
                    "title": "token无效/过期",
                    "method": "GET",
                    "url": "/api/user/info",
                    "headers": {"token": "invalid_token"},
                    "params": {"userId": 1001},
                    "body": {},
                    "expect_code": 401,
                    "expect_msg": "登录失效",
                    "priority": "高"
                }
            ]
            st.session_state["cases"] = mock_cases
            st.success("✅ 用例生成完成")

# ----------------------
# 3. 表格展示用例
# ----------------------
if "cases" in st.session_state:
    st.divider()
    st.subheader("📋 生成的测试用例列表")
    df = pd.DataFrame(st.session_state["cases"])
    st.dataframe(df, use_container_width=True)

    # ----------------------
    # 4. 选择用例调试（Postman风格）
    # ----------------------
    st.divider()
    st.subheader("🔧 用例调试（Postman 风格）")
    case_ids = [c["case_id"] for c in st.session_state["cases"]]
    selected = st.selectbox("选择要调试的用例", case_ids)

    current_case = next(c for c in st.session_state["cases"] if c["case_id"] == selected)

    col1, col2 = st.columns([1, 1])
    with col1:
        method = st.selectbox("请求方法", [current_case["method"]], disabled=True)
        url = st.text_input("接口地址", current_case["url"])
        headers = st.text_area("请求头（JSON）", json.dumps(current_case["headers"], indent=2, ensure_ascii=False),
                               height=120)
        params = st.text_area("URL参数（JSON）", json.dumps(current_case["params"], indent=2, ensure_ascii=False),
                              height=120)
        body = st.text_area("请求体（JSON）", json.dumps(current_case["body"], indent=2, ensure_ascii=False), height=120)

    with col2:
        st.markdown("#### 响应结果")
        send_btn = st.button("发送请求", type="primary")
        if send_btn:
            try:
                h = json.loads(headers)
                p = json.loads(params)
                b = json.loads(body)
                res = None

                if method.upper() == "GET":
                    res = requests.get(url, headers=h, params=p, timeout=8)
                elif method.upper() == "POST":
                    res = requests.post(url, headers=h, json=b, timeout=8)
                elif method.upper() == "PUT":
                    res = requests.put(url, headers=h, json=b, timeout=8)
                elif method.upper() == "DELETE":
                    res = requests.delete(url, headers=h, json=b, timeout=8)

                st.success(f"状态码：{res.status_code}")
                st.markdown("**响应内容**")
                st.json(res.json())

            except json.JSONDecodeError:
                st.error("JSON 格式错误，请检查")
            except Exception as e:
                st.error(f"请求失败：{str(e)}")

    # ----------------------
    # 5. 生成 pytest 代码
    # ----------------------
    st.divider()
    st.subheader("✅ 生成 pytest 测试代码")
    code_lines = [
        "import pytest",
        "import requests\n",
        "class TestApi:\n",
        "    host = \"http://localhost:8080\"\n"
    ]

    for c in st.session_state["cases"]:
        test_func = f"""
    def test_{c['case_id'].lower()}(self):
        url = self.host + "{c['url']}"
        headers = {c['headers']}
        params = {c['params']}
        json_data = {c['body']}

        response = requests.{c['method'].lower()}(
            url=url,
            headers=headers,
            params=params,
            json=json_data
        )

        assert response.status_code == {c['expect_code']}, "状态码不匹配"
        assert "{c['expect_msg']}" in response.text, "响应信息不匹配"
"""
        code_lines.append(test_func)

    pytest_code = "\n".join(code_lines)
    st.code(pytest_code, language="python")

    st.download_button("💾 下载 pytest 测试文件", pytest_code, file_name="test_api.py")

st.divider()
st.caption("基于 Streamlit + AI 接口自动化测试 | 支持PDF/DOCX解析、用例生成、调试、生成pytest代码")