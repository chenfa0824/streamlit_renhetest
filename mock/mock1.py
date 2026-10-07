import streamlit as st
import requests
import json

st.set_page_config(page_title="Mock接口工具", layout="wide")
st.title("🛠️ Streamlit Mock 工具")

with st.expander("功能说明", expanded=True):
    st.markdown("""
- 输入：请求URL、请求方法、请求入参(JSON)
- 行为：会调用传入的URL接口
- 返回：**直接把你传入的入参原样返回给前端（mock效果，不使用真实接口返回数据）**
""")

# 表单区域
col1, col2 = st.columns([2, 3])
with col1:
    method = st.selectbox("请求方法", ["POST", "GET"])
    target_url = st.text_input("目标URL", value="http://127.0.0.1:8080/demo/api")
    request_body_text = st.text_area("请求入参(JSON)", height=220, value='''{
    "name": "test",
    "id": 1001
}''')

send_btn = st.button("🚀 发起Mock调用", type="primary")

# 保存请求历史
if "history" not in st.session_state:
    st.session_state.history = []

with col2:
    st.subheader("响应结果(Mock返回原始入参)")
    response_area = st.empty()

if send_btn:
    try:
        # 解析入参json
        req_body = json.loads(request_body_text)
        headers = {"Content-Type": "application/json"}

        # 调用传入的url真实接口
        if method == "POST":
            resp_real = requests.post(target_url, json=req_body, headers=headers, timeout=10)
        else:
            resp_real = requests.get(target_url, params=req_body, timeout=10)

        # =========核心mock逻辑：返回结果和入参一模一样=========
        mock_response_data = req_body

        info = {
            "url": target_url,
            "method": method,
            "request": req_body,
            "real_status_code": resp_real.status_code,
            "mock_response": mock_response_data
        }
        st.session_state.history.append(info)

        # 展示mock返回
        response_area.json(mock_response_data)

        st.divider()
        st.info(f"✅ 已真实调用URL，真实接口状态码：{resp_real.status_code}；Mock直接返回传入的入参作为结果")

    except json.JSONDecodeError:
        st.error("❌ JSON格式错误，请检查入参")
    except Exception as e:
        st.error(f"❌ 请求异常：{str(e)}")

# 请求历史
st.divider()
st.subheader("📋 请求历史记录")
for idx, item in enumerate(reversed(st.session_state.history[-10:])):
    with st.container(border=True):
        st.markdown(f"**{item['method']}** {item['url']} | 真实状态码：{item['real_status_code']}")
        c1, c2 = st.columns(2)
        with c1:
            st.code(json.dumps(item["request"], ensure_ascii=False, indent=2), language="json")
        with c2:
            st.code(json.dumps(item["mock_response"], ensure_ascii=False, indent=2), language="json")

if st.button("清空历史"):
    st.session_state.history.clear()
    st.rerun()
