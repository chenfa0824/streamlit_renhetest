import streamlit as st
import requests
import json
import time
from datetime import datetime

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="接口自动化测试平台",
    layout="wide",
    page_icon="⚡"
)

# 初始化会话状态（保存用例列表）
if "case_list" not in st.session_state:
    st.session_state.case_list = []

# --------------------------
# 标题
# --------------------------
st.title("⚡ 接口自动化测试工具")
st.markdown("---")

# --------------------------
# 左侧：用例列表 | 右侧：执行接口
# --------------------------
col_left, col_right = st.columns([1, 2])

# ==========================
# 右侧：接口请求区域
# ==========================
with col_right:
    st.subheader("📥 接口请求配置")

    # 1. 请求信息
    url = st.text_input("请求 URL", placeholder="https://httpbin.org/post")
    method = st.selectbox("请求方法", ["GET", "POST", "PUT", "DELETE"])

    # 2. 请求参数（JSON 格式）
    st.markdown("#### 请求参数（JSON）")
    params = st.text_area(
        "输入 JSON 参数",
        value='{"username":"admin","password":"123456"}',
        height=140
    )

    # 3. 断言配置
    st.markdown("#### 响应断言")
    assert_code = st.number_input("预期状态码", value=200)
    assert_contains = st.text_input("响应包含文本（可不填）")
    assert_json_path = st.text_input("校验JSON字段（例：code=200）")

    # 4. 执行按钮
    run_btn = st.button("🚀 发送请求并保存用例", type="primary")

    # 执行请求
    if run_btn:
        if not url:
            st.error("请输入 URL！")
        else:
            try:
                with st.spinner("请求执行中..."):
                    # 发送请求
                    headers = {"Content-Type": "application/json"}
                    data_json = json.loads(params) if params.strip() else {}

                    if method == "GET":
                        res = requests.get(url, params=data_json, headers=headers, timeout=10)
                    else:
                        res = requests.request(method, url, json=data_json, headers=headers, timeout=10)

                    # 执行时间
                    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 断言结果
                    status = "通过✅"
                    reason = []

                    if res.status_code != assert_code:
                        status = "失败❌"
                        reason.append(f"状态码错误：预期{assert_code}，实际{res.status_code}")

                    if assert_contains and assert_contains not in res.text:
                        status = "失败❌"
                        reason.append(f"响应不包含文本：{assert_contains}")

                    if assert_json_path:
                        try:
                            key, expect_val = assert_json_path.split("=")
                            actual_val = str(res.json().get(key.strip(), ""))
                            if actual_val != expect_val.strip():
                                status = "失败❌"
                                reason.append(f"字段{key}校验失败：预期{expect_val}，实际{actual_val}")
                        except:
                            reason.append("JSON 校验格式错误，正确格式：key=value")

                    # 保存用例
                    case_data = {
                        "name": f"{method} {url}",
                        "time": run_time,
                        "status": status,
                        "reason": " | ".join(reason) if reason else "断言全部通过",
                        "url": url,
                        "method": method,
                        "req_data": data_json,
                        "res_status": res.status_code,
                        "res_text": res.text[:1000],
                        "res_json": res.json() if res.headers.get("Content-Type") == "application/json" else {}
                    }
                    st.session_state.case_list.append(case_data)
                    st.success(f"用例执行完成！结果：{status}")
                    time.sleep(0.5)
                    st.rerun()

            except Exception as e:
                st.error(f"请求失败：{str(e)}")

# ==========================
# 左侧：用例列表
# ==========================
with col_left:
    st.subheader("📋 用例列表")

    if not st.session_state.case_list:
        st.info("暂无用例，请执行接口...")
    else:
        for i, case in enumerate(st.session_state.case_list):
            btn_text = f"{case['method']} | {case['status']} | {case['time']}"
            if st.button(btn_text, key=i):
                st.session_state.current_case = case

# --------------------------
# 底部：展示选中用例详情
# --------------------------
st.markdown("---")
st.subheader("📊 用例执行详情")

if "current_case" in st.session_state:
    case = st.session_state.current_case

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"请求方法：{case['method']}")
    with c2:
        st.info(f"URL：{case['url']}")
    with c3:
        st.info(f"执行结果：**{case['status']}**")

    st.markdown("**请求数据：**")
    st.json(case["req_data"])

    st.markdown("**响应状态码：** " + str(case["res_status"]))
    st.markdown("**断言结果：** " + case["reason"])

    st.markdown("**响应数据：**")
    try:
        st.json(json.loads(case["res_text"]))
    except:
        st.text(case["res_text"])
else:
    st.info("👈 点击左侧用例查看详情")