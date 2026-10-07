import streamlit as st
import json
import base64
from PIL import Image
import pandas as pd
import requests
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# ======================
# 页面配置
# ======================
st.set_page_config(page_title="LangChain 截图生成接口用例", page_icon="📸", layout="wide")
st.title("📸 截图 → LangChain + LLM → 自动生成接口测试用例")

# ======================
# 多模态大模型配置（必须填）
# ======================
llm = ChatOpenAI(
    model="gpt-4o",  # 多模态模型（支持图片）
    api_key="你的API_KEY",
    base_url="https://api.openai.com/v1",  # 国内可填中转地址
    temperature=0.1
)

# ======================
# 工具：图片转base64
# ======================
def image_to_base64(img):
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# ======================
# 步骤1：上传截图
# ======================
st.subheader("1 上传接口文档截图")
upload_file = st.file_uploader("上传 PNG / JPG 接口截图", type=["png", "jpg", "jpeg"])

if upload_file:
    image = Image.open(upload_file)
    st.image(image, caption="已上传截图", use_column_width=True)
    base64_img = image_to_base64(image)

    # ======================
    # 步骤2：LangChain 识别接口信息
    # ======================
    st.subheader("2 解析接口信息")
    if st.button("🔍 开始解析接口", type="primary"):
        with st.spinner("LangChain + 多模态LLM 解析中..."):
            messages = [
                SystemMessage(content="你是专业接口识别助手，从截图提取接口信息，只返回纯JSON，不要解释。"),
                HumanMessage(content=[
                    {"type": "text", "text": """
请提取：
1. 接口模块
2. 接口地址
3. 请求方法 GET/POST/PUT/DELETE
4. 请求头 headers
5. 请求参数 params
6. 请求体 body
7. 接口描述
返回JSON格式。
"""},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ])
            ]
            res = llm.invoke(messages)
            api_info = json.loads(res.content)
            st.session_state["api_info"] = api_info
            st.success("✅ 接口解析完成")
            st.json(api_info)

# ======================
# 步骤3：LangChain 生成测试用例
# ======================
if "api_info" in st.session_state:
    st.divider()
    st.subheader("3 生成接口测试用例")

    if st.button("✨ LLM 自动生成测试用例", type="primary"):
        with st.spinner("LLM 生成用例中..."):
            api_info = st.session_state["api_info"]
            messages = [
                SystemMessage(content="""
你是顶级接口测试专家，生成标准测试用例，只返回JSON数组，不要多余内容。
每条用例包含：
case_id, module, title, method, url, headers, params, body, expect_code, expect_msg, priority
覆盖：正常、必填缺参、空值、类型错误、边界、非法、权限。
"""),
                HumanMessage(content=f"根据接口信息生成用例：{json.dumps(api_info)}")
            ]
            res = llm.invoke(messages)
            cases = json.loads(res.content)
            st.session_state["cases"] = cases
            st.success("✅ 用例生成完成！")

# ======================
# 步骤4：表格展示用例
# ======================
if "cases" in st.session_state:
    st.divider()
    st.subheader("4 测试用例列表")
    df = pd.DataFrame(st.session_state["cases"])
    st.dataframe(df, use_container_width=True)

    # ======================
    # 步骤5：Postman风格调试
    # ======================
    st.divider()
    st.subheader("5 接口在线调试")
    case_ids = [c["case_id"] for c in st.session_state["cases"]]
    selected = st.selectbox("选择用例", case_ids)
    current = next(c for c in st.session_state["cases"] if c["case_id"] == selected)

    col1, col2 = st.columns(2)
    with col1:
        method = st.selectbox("请求方法", [current["method"]], disabled=True)
        url = st.text_input("接口地址", current["url"])
        headers = st.text_area("Headers", json.dumps(current["headers"], indent=2, ensure_ascii=False))
        params = st.text_area("Params", json.dumps(current["params"], indent=2, ensure_ascii=False))
        body = st.text_area("Body", json.dumps(current["body"], indent=2, ensure_ascii=False))

    with col2:
        st.markdown("### 响应结果")
        if st.button("📤 发送请求", type="primary"):
            try:
                h = json.loads(headers)
                p = json.loads(params)
                b = json.loads(body)
                res = None

                if method == "GET":
                    res = requests.get(url, headers=h, params=p, timeout=10)
                elif method == "POST":
                    res = requests.post(url, headers=h, json=b, timeout=10)
                elif method == "PUT":
                    res = requests.put(url, headers=h, json=b, timeout=10)
                elif method == "DELETE":
                    res = requests.delete(url, headers=h, json=b, timeout=10)

                st.success(f"状态码：{res.status_code}")
                st.json(res.json())
            except Exception as e:
                st.error(f"请求失败：{str(e)}")

st.divider()
st.caption("✅ 基于 Streamlit + LangChain + 多模态LLM 接口自动化测试平台")