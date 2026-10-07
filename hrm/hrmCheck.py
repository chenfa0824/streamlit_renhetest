import streamlit as st
import requests
import json
import base64
import ddddocr
from io import BytesIO
from PIL import Image
import time
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="绩效数据查询",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式 - 紧凑布局
st.markdown("""
<style>
    /* 减少整体间距 */
    .main > div {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }

    /* 减少标题间距 */
    h1, h2, h3 {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }

    /* 减少容器间距 */
    .stContainer {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* 减少表单间距 */
    .stForm {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* 减少子标题间距 */
    .stSubheader {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }

    /* 减少列间距 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.3rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* 减少输入框间距 */
    .stTextInput > div {
        margin-bottom: 0.1rem !important;
    }

    /* 减少按钮间距 */
    .stButton > button {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
        padding: 0.3rem 0.5rem !important;
    }

    /* 减少选择框间距 */
    .stSelectbox > div {
        margin-bottom: 0.1rem !important;
    }

    /* 减少分割线间距 */
    hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* 减少成功消息间距 */
    .stAlert {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }

    /* 减少dataframe间距 */
    .stDataFrame {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 HRM查询员工绩效数据")

# 初始化session_state
if 'jwt_token' not in st.session_state:
    st.session_state.jwt_token = None
if 'login_success' not in st.session_state:
    st.session_state.login_success = False
if 'check_key' not in st.session_state:
    st.session_state.check_key = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'query_result' not in st.session_state:
    st.session_state.query_result = None
if 'auto_login_triggered' not in st.session_state:
    st.session_state.auto_login_triggered = False
if 'captcha_img' not in st.session_state:
    st.session_state.captcha_img = None
if 'captcha_text' not in st.session_state:
    st.session_state.captcha_text = ""


def auto_login(username, password, captcha, check_key):
    """自动登录"""
    login_url = "https://hrm-apitest.whrhkj.com/user/login"
    login_data = {
        "username": username,
        "password": password,
        "captcha": captcha,
        "checkKey": check_key
    }
    try:
        response = requests.post(login_url, json=login_data, timeout=10)
        result = response.json()
        if response.status_code == 200 and result.get('success', False):
            token = result.get('result', {}).get('token')
            if token:
                st.session_state.jwt_token = token
                st.session_state.login_success = True
                st.session_state.user_info = result.get('result', {}).get('userInfo', {})
                return True, f"登录成功，欢迎 {st.session_state.user_info.get('realname', username)}"
            return False, "登录响应中未找到Token"
        return False, result.get('message', '未知错误')
    except Exception as e:
        return False, f"登录异常: {e}"


def parse_performance_data(data):
    """解析绩效数据"""
    parsed_results = []
    items = []

    if isinstance(data, dict) and "userList" in data and isinstance(data["userList"], list):
        items = data["userList"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        list_fields = ['list', 'records', 'items', 'data', 'rows', 'resultList']
        for field in list_fields:
            if field in data and isinstance(data[field], list):
                items = data[field]
                break
        if not items:
            for key, value in data.items():
                if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                    items = value
                    break
        if not items:
            key_fields = ['realname', 'position', 'judgmentResult', 'deductionEntityList']
            if any(field in data for field in key_fields):
                items = [data]

    if not items:
        return []

    for item in items:
        if not isinstance(item, dict):
            continue
        realname = item.get('realname', 'N/A')
        position = item.get('position', item.get('positon', 'N/A'))
        judgment_result = item.get('judgmentResult', 'N/A')
        deduction_list = item.get('deductionEntityList', [])

        perf_details = {}
        if isinstance(deduction_list, list):
            for deduction in deduction_list:
                if isinstance(deduction, dict):
                    month = deduction.get('month') or deduction.get('mouth', 'N/A')
                    perf_level = deduction.get('perfLevel', 'N/A')
                    if month != 'N/A':
                        perf_details[month] = perf_level

        parsed_results.append({
            "姓名": realname,
            "岗位名称": position,
            "判定结果": judgment_result,
            "绩效明细": perf_details
        })

    return parsed_results


def display_results(parsed_data):
    """展示数据"""
    if not parsed_data:
        return

    # 收集所有月份
    all_months = set()
    for record in parsed_data:
        all_months.update(record["绩效明细"].keys())
    sorted_months = sorted(list(all_months))

    st.subheader(f"📋 绩效数据列表（共 {len(parsed_data)} 条）")

    # 构建表格数据
    display_data = []
    for record in parsed_data:
        judgment = record["判定结果"]
        icon = "✅" if judgment in ['通过', '合格'] else "❌" if judgment in ['不通过', '不合格'] else "📊"

        row = {
            "姓名": record["姓名"],
            "岗位名称": record["岗位名称"],
            "判定结果": f"{icon} {judgment}"
        }
        # 添加每个月份的绩效数据
        for month in sorted_months:
            row[month] = record["绩效明细"].get(month, "-")
        display_data.append(row)

    # 创建列配置 - 姓名和岗位名称使用相同宽度
    column_config = {
        "姓名": st.column_config.TextColumn("姓名", width="small"),
        "岗位名称": st.column_config.TextColumn("岗位名称", width="small"),
        "判定结果": st.column_config.TextColumn("判定结果", width="small"),
    }
    # 为月份列添加配置
    for month in sorted_months:
        column_config[month] = st.column_config.TextColumn(month, width="small")

    st.dataframe(
        display_data,
        column_config=column_config,
        use_container_width=True,
        height=400
    )


def generate_month_options():
    """生成月份选项列表"""
    months = []
    current = datetime.now()
    # 从当前月份往前推24个月
    for i in range(24):
        year = current.year
        month = current.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}-{month:02d}")
    return months


# ===================== 主页面 =====================

# 登录区域 - 紧凑布局
st.header("🔐 用户登录")

if st.session_state.login_success:
    user_info = st.session_state.user_info
    st.success(f"✅ 当前已登录: {user_info.get('realname', '未知')} ({user_info.get('username', '')})")

# 用户名和密码两列布局
col1, col2 = st.columns(2)

with col1:
    username = st.text_input("👤 用户名", value="112054", key="login_username", label_visibility="collapsed")

with col2:
    password = st.text_input("🔒 密码", value="algo1129", type="password", key="login_password",
                             label_visibility="collapsed")

# 获取验证码按钮单独一行
col_center = st.columns([2, 1, 2])
with col_center[1]:
    if st.button("📷 获取验证码", use_container_width=True, key="get_captcha_btn"):
        check_key = str(int(time.time() * 1000))
        captcha_url = f"https://hrm-apitest.whrhkj.com/sys/randomImage/{check_key}?_t={int(time.time())}"
        try:
            response = requests.get(captcha_url, timeout=10)
            result = response.json()
            if result.get('code') == 0 and result.get('success'):
                img_data = result.get('result', '')
                if img_data.startswith('data:image/jpg;base64,'):
                    img_base64 = img_data.split(',')[1]
                    img_bytes = base64.b64decode(img_base64)
                    img = Image.open(BytesIO(img_bytes))
                    ocr = ddddocr.DdddOcr(show_ad=False)
                    captcha_text = ocr.classification(img)
                    st.session_state.check_key = check_key
                    st.session_state.captcha_text = captcha_text
                    st.session_state.captcha_img = img
                    st.session_state.auto_login_triggered = False
                else:
                    st.error("❌ 验证码接口返回格式异常")
            else:
                st.error(f"❌ 获取失败：{result.get('message', '未知错误')}")
        except Exception as e:
            st.error(f"❌ 请求异常: {e}")

# 自动登录触发器
if (not st.session_state.login_success and st.session_state.check_key and
        st.session_state.captcha_text and not st.session_state.auto_login_triggered):
    st.session_state.auto_login_triggered = True
    success, message = auto_login(
        st.session_state.get('login_username', '112054'),
        st.session_state.get('login_password', 'algo1129'),
        st.session_state.captcha_text,
        st.session_state.check_key
    )
    if success:
        st.rerun()
    else:
        st.session_state.auto_login_triggered = False

st.markdown("---")

# 绩效数据查询 - 紧凑布局
st.header("📋 绩效数据查询")
with st.form(key="query_form"):
    # 生成月份选项
    month_options = generate_month_options()

    cols = st.columns(3)
    with cols[0]:
        key_point = st.text_input("姓名/工号", value="102418", label_visibility="collapsed", placeholder="姓名/工号")
    with cols[1]:
        start_month = st.selectbox(
            "开始月份",
            options=month_options,
            index=month_options.index("2026-02") if "2026-02" in month_options else 0,
            key="start_month_select",
            label_visibility="collapsed"
        )
    with cols[2]:
        end_month = st.selectbox(
            "结束月份",
            options=month_options,
            index=month_options.index("2026-07") if "2026-07" in month_options else 0,
            key="end_month_select",
            label_visibility="collapsed"
        )

    cols = st.columns([2, 1, 2])
    with cols[1]:
        submitted = st.form_submit_button("🔍 查询", use_container_width=True)

if submitted:
    if not st.session_state.login_success:
        st.warning("⚠️ 请等待自动登录完成")
    else:
        request_data = {
            "keyPoint": key_point,
            "startMonth": start_month,
            "endMonth": end_month,
            "departIds": [],
            "hrName": "",
            "judgmentTypeList": [],
            "julyResultApplicationList": [],
            "pageNo": "1",
            "pageSize": "100",
            "perfLevels": [],
            "resultMonth": datetime.now().strftime("%Y-%m"),
            "status": ""
        }
        headers = {
            "x-access-token": st.session_state.jwt_token,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                "https://hrm-apitest.whrhkj.com/employee/performance/list",
                json=request_data,
                headers=headers,
                timeout=10
            )
            result = response.json()
            if result.get('code') == 200 and result.get('success', False):
                parsed_data = parse_performance_data(result.get('result', {}))
                st.session_state.query_result = parsed_data
                if parsed_data:
                    display_results(parsed_data)
            else:
                st.error(f"❌ 数据获取失败：{result.get('message', '未知错误')}")
        except Exception as e:
            st.error(f"❌ 请求异常: {e}")