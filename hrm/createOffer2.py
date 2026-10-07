import streamlit as st
import base64
import json
import logging
import time
import os
from io import BytesIO
from datetime import datetime
from typing import Optional, List, Dict
from logging.handlers import RotatingFileHandler

import ddddocr
import requests
from PIL import Image


# ============ 日志配置 ============
def setup_logging():
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hrm.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024,
                                       backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(file_handler)

    for name in ('urllib3', 'requests', 'ddddocr'):
        logging.getLogger(name).setLevel(logging.WARNING)

    return log_file


LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)


# ============ 用户账号配置 ============
USER_ACCOUNTS = [
    {"name": "涂晓帆", "username": "112054", "password": "algo1129", "default": True},
    {"name": "陈东", "username": "100001", "password": "Admin@123", "default": False},
    {"name": "杨林", "username": "100025", "password": "Admin@123", "default": False},
]

BASE_URL = "https://hrm-apitest.whrhkj.com"


# ============ 通用请求封装 ============
def _request(method: str, url: str, token: Optional[str] = None, **kwargs) -> dict:
    """统一请求入口，返回 {success, data/result, message}"""
    headers = kwargs.pop("headers", {})
    if token:
        headers["X-Access-Token"] = token
    headers.setdefault("Content-Type", "application/json")

    logger.info(f"请求 {method} {url}")
    if "json" in kwargs:
        logger.info(f"请求体: {json.dumps(kwargs['json'], ensure_ascii=False)}")

    start = time.time()
    try:
        response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    except requests.exceptions.RequestException as e:
        logger.exception(e)
        return {'success': False, 'message': f"网络请求异常: {e}"}

    elapsed = time.time() - start
    logger.info(f"响应状态码: {response.status_code}, 耗时: {elapsed:.3f}s")

    try:
        result = response.json()
    except Exception as e:
        logger.exception(e)
        return {'success': False, 'message': f"响应解析异常: {e}"}

    logger.info(f"响应内容: {json.dumps(result, ensure_ascii=False)}")
    return result


# ============ 认证服务 ============
class AuthService:

    @staticmethod
    def get_captcha() -> dict:
        check_key = str(int(time.time() * 1000))
        url = f"{BASE_URL}/sys/randomImage/{check_key}?_t={int(time.time())}"

        result = _request("GET", url)
        if result.get('code') == 0 and result.get('success'):
            img_data = result.get('result', '')
            if not img_data.startswith('data:image/jpg;base64,'):
                return {'success': False, 'message': "验证码接口返回格式异常"}

            img_base64 = img_data.split(',')[1]
            img = Image.open(BytesIO(base64.b64decode(img_base64)))

            ocr = ddddocr.DdddOcr(show_ad=False)
            captcha_text = ocr.classification(img)
            logger.info(f"OCR识别结果: {captcha_text}")

            return {
                'success': True,
                'checkKey': check_key,
                'captcha': captcha_text,
                'image_base64': img_base64,
                'message': "验证码获取成功"
            }
        return {'success': False, 'message': f"获取验证码失败：{result.get('message', '未知错误')}"}

    @staticmethod
    def login(username: str, password: str, captcha: str, check_key: str) -> dict:
        url = f"{BASE_URL}/user/login"
        payload = {
            "username": username,
            "password": password,
            "captcha": captcha,
            "checkKey": check_key
        }

        result = _request("POST", url, json=payload)
        if result.get('success', False):
            token = result.get('result', {}).get('token')
            user_info = result.get('result', {}).get('userInfo', {})
            if token:
                return {
                    'success': True,
                    'token': token,
                    'userInfo': user_info,
                    'message': f"登录成功，欢迎 {user_info.get('realname', username)}"
                }
            return {'success': False, 'message': "登录响应中未找到Token"}
        return {'success': False, 'message': result.get('message', '未知错误')}


# ============ 岗位服务 ============
class PositionService:
    """从 sys_position 表查询岗位"""

    POSITION_LIST_URL = f"{BASE_URL}/sys/position/list"

    @staticmethod
    def get_position_list(token: str) -> dict:
        params = {"pageNo": 1, "pageSize": 1000}
        result = _request("GET", PositionService.POSITION_LIST_URL, token=token, params=params)

        if not result.get('success', False):
            return {
                'success': False,
                'positions': [],
                'message': f"获取岗位列表失败: {result.get('message', '未知错误')}"
            }

        raw = result.get('result', {})
        if isinstance(raw, dict):
            records = raw.get('records') or raw.get('list') or raw.get('rows') or []
        elif isinstance(raw, list):
            records = raw
        else:
            records = []

        positions = []
        for item in records:
            pos_id = item.get('id') or item.get('positionId')
            pos_name = item.get('name') or item.get('positionName')
            if pos_id and pos_name:
                positions.append({'id': pos_id, 'name': pos_name})

        logger.info(f"获取到 {len(positions)} 个岗位")
        return {
            'success': True,
            'positions': positions,
            'message': f"成功获取 {len(positions)} 个岗位"
        }


# ============ 定时任务服务 ============
class TaskService:

    TASK_URLS = {
        "转正": f"{BASE_URL}/work/flow/proof/approval/hrmProofOfApproval/job",
        "调薪": f"{BASE_URL}/work/flow/salary/transfer/hrmSalaryTransfer/job",
        "调岗": f"{BASE_URL}/work/flow/job/transfer/hrmJobTransfer/job",
        "离职": f"{BASE_URL}/work/flow/resign/transfer/hrmResignTransfer/job",
    }

    @staticmethod
    def trigger_task(task_name: str, token: str) -> dict:
        url = TaskService.TASK_URLS.get(task_name)
        if not url:
            return {'success': False, 'message': f"未知的任务类型: {task_name}"}

        result = _request("GET", url, token=token)
        if result.get('success', False):
            return {'success': True, 'data': result, 'message': f"{task_name}任务触发成功"}
        return {'success': False, 'message': f"{task_name}任务触发失败: {result.get('message', '未知错误')}"}


# ============ Offer 服务 ============
class OfferService:

    @staticmethod
    def create_offer(token: str, name: str, mobile: str, position_name: str, position_id: str) -> dict:
        url = f"{BASE_URL}/offer/hrmOffer/offerDetails/add"

        payload = {
            "offer": {
                "reload": True,
                "name": name,
                "mobile": mobile,
                "email": "18792169903@163.com",
                "sex": 1,
                "birthday": "2026-08-01T17:08:58.328Z",
                "age": 0,
                "positionId": position_id,
                "position": position_name,
                "levelId": "4136c6471a064fd3916c01cf287ac4e8",
                "level": "技术序列 1级",
                "resumeRequired": False,
                "degreeRequired": False,
                "certificateRequired": False,
                "discRequired": False,
                "departName": "信息中心",
                "departId": "ZB08",
                "leaderId": "111358",
                "leaderName": "成豪",
                "systemId": "0",
                "psnCategory": "0",
                "planentryDate": "2026-08-31T17:09:29.837Z",
                "probationPeriod": "6",
                "userSalary": {
                    "generalList": [],
                    "probationList": [],
                    "salaryGroupId": "3",
                    "probationAmountTotal": "12345",
                    "generalAmountTotal": "12345"
                }
            },
            "contractDocs": [
                {
                    "contract": {
                        "date": [
                            "2026-08-01T17:08:40.420Z",
                            "2026-09-30T17:08:40.420Z"
                        ],
                        "companyName": "上海优财方略财务管理有限责任公司",
                        "corporation": "石现",
                        "corporationPhone": "19986888218",
                        "corporationAddress": "上海市浦东新区张杨路3611弄6号702室",
                        "startDate": "2026-08-01",
                        "endDate": "2026-09-30",
                        "signType": "劳动合同",
                        "signDesc": "初次签订",
                        "breachRule": "履行中"
                    },
                    "docs": []
                }
            ],
            "userFiles": [
                {
                    "newFile": True,
                    "fileName": "屏幕截图 2026-07-31 091113.png",
                    "url": "https://renhe-hrm-test.oss-cn-hangzhou.aliyuncs.com/hrm/92210e5fbb78714eb685316ebdb618cd/屏幕截图2026-07-31091113.png",
                    "path": "hrm/92210e5fbb78714eb685316ebdb618cd/屏幕截图2026-07-31091113.png",
                    "sysUserId": None,
                    "offerId": None,
                    "type": "user_doc_type_Onboarding_5"
                }
            ],
            "userSalaryCurrentList": [
                {
                    "amountTotal": "12345",
                    "salaryGroupId": "3",
                    "type": 0,
                    "userSalaryDescList": []
                },
                {
                    "amountTotal": "12345",
                    "salaryGroupId": "3",
                    "type": 1,
                    "userSalaryDescList": []
                }
            ]
        }

        result = _request("POST", url, token=token, json=payload)
        if result.get('success', False):
            return {'success': True, 'data': result.get('result', {}), 'message': "Offer创建成功"}
        return {'success': False, 'message': f"创建Offer失败: {result.get('message', '未知错误')}"}


# ============ Streamlit 页面逻辑 ============
def init_session_state():
    defaults = {
        "token": None,
        "user_info": None,
        "login_success": False,
        "offer_created": False,
        "offer_result": None,
        "task_result": None,
        "selected_user": "涂晓帆",
        "position_list": [],
        "position_loaded": False,
        "selected_position_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_user_by_name(name: str) -> Optional[Dict]:
    return next((u for u in USER_ACCOUNTS if u["name"] == name), None)


def get_position_by_name(name: str) -> Optional[Dict]:
    if not name:
        return None
    return next((p for p in st.session_state.get("position_list", []) if p["name"] == name), None)


def load_positions() -> bool:
    if not st.session_state.token:
        return False

    result = PositionService.get_position_list(st.session_state.token)
    if result.get('success'):
        st.session_state.position_list = result.get('positions', [])
        st.session_state.position_loaded = True
        if st.session_state.position_list:
            st.session_state.selected_position_name = st.session_state.position_list[0]["name"]
        return True

    st.session_state.position_list = []
    st.session_state.position_loaded = False
    st.session_state.selected_position_name = None
    logger.error(f"岗位列表加载失败: {result.get('message')}")
    return False


def perform_auto_login() -> bool:
    user = get_user_by_name(st.session_state.selected_user)
    if not user:
        st.error(f"❌ 未找到用户: {st.session_state.selected_user}")
        return False

    captcha_result = AuthService.get_captcha()
    if not captcha_result.get('success'):
        st.error(f"❌ {captcha_result.get('message')}")
        return False

    login_result = AuthService.login(
        user["username"], user["password"],
        captcha_result['captcha'], captcha_result['checkKey']
    )
    if not login_result.get('success'):
        st.error(f"❌ {login_result.get('message')}")
        return False

    st.session_state.token = login_result['token']
    st.session_state.user_info = login_result.get('userInfo', {})
    st.session_state.login_success = True
    st.session_state.offer_created = False
    st.session_state.task_result = None

    load_positions()

    st.success(f"✅ 登录成功，欢迎 {st.session_state.user_info.get('realname', user['name'])}")
    return True


def trigger_task(task_name: str):
    if not st.session_state.token:
        st.error("❌ 未登录，请先登录")
        return

    result = TaskService.trigger_task(task_name, st.session_state.token)
    st.session_state.task_result = {
        'task_name': task_name,
        'success': result.get('success'),
        'message': result.get('message'),
        'data': result.get('data')
    }
    if result.get('success'):
        st.success(f"✅ {result.get('message')}")
    else:
        st.error(f"❌ {result.get('message')}")


def create_offer(name: str, mobile: str, position_name: str, position_id: str) -> bool:
    if not st.session_state.token:
        st.error("❌ 未登录，请先登录")
        return False
    if not name or not mobile:
        st.warning("⚠️ 请输入姓名和手机号")
        return False
    if not position_name or not position_id:
        st.warning("⚠️ 请选择岗位")
        return False

    result = OfferService.create_offer(st.session_state.token, name, mobile, position_name, position_id)
    if result.get('success'):
        st.session_state.offer_created = True
        st.session_state.offer_result = result.get('data')
        st.success(f"✅ {result.get('message')}")
        return True

    st.error(f"❌ {result.get('message')}")
    return False


def display_user_info():
    if not (st.session_state.login_success and st.session_state.user_info):
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("👤 用户名", st.session_state.user_info.get("username", "-"))
    with col2:
        st.metric("📛 真实姓名", st.session_state.user_info.get("realname", "-"))

    with st.expander("🔑 查看Token"):
        st.code(st.session_state.token, language="text")

    # ============ Offer 创建表单 ============
    st.subheader("📄 创建Offer")
    st.markdown("**💼 岗位信息**")

    if not st.session_state.position_loaded:
        st.warning("⚠️ 岗位列表未加载")
        if st.button("🔄 重新加载岗位列表", key="reload_positions"):
            load_positions()
            st.rerun()
        position_names = []
    else:
        position_names = [pos["name"] for pos in st.session_state.position_list]

    if position_names:
        if st.session_state.selected_position_name not in position_names:
            st.session_state.selected_position_name = position_names[0]

        selected_position_name = st.selectbox(
            "选择岗位",
            options=position_names,
            index=position_names.index(st.session_state.selected_position_name),
            key="selected_position_name_widget",
            help="岗位列表来自 sys_position 表"
        )
        st.session_state.selected_position_name = selected_position_name

        selected_pos = get_position_by_name(selected_position_name)
        if selected_pos:
            st.info(f"📋 当前岗位ID: `{selected_pos['id']}`")
        else:
            st.warning("⚠️ 未找到对应的岗位ID")
    else:
        st.warning("⚠️ 暂无可选岗位，请先重新加载岗位列表")

    with st.form("offer_form"):
        col1, col2 = st.columns(2)
        with col1:
            offer_name = st.text_input("👤 姓名", placeholder="请输入候选人姓名", key="offer_name_input")
        with col2:
            offer_mobile = st.text_input("📱 手机号", placeholder="请输入手机号", key="offer_mobile_input")

        submit_offer = st.form_submit_button("📄 创建Offer", use_container_width=True, type="primary")

        if submit_offer:
            current_pos = get_position_by_name(st.session_state.selected_position_name)
            if current_pos:
                create_offer(offer_name, offer_mobile, current_pos["name"], current_pos["id"])
            else:
                st.error("❌ 请选择有效的岗位")
            st.rerun()

    if st.session_state.offer_created and st.session_state.offer_result:
        st.success("✅ Offer创建成功！")
        with st.expander("📋 查看Offer详情"):
            st.json(st.session_state.offer_result)

    # ============ 定时任务 ============
    st.subheader("⚙️ 定时任务手动触发")
    st.caption("点击按钮手动触发对应的定时任务")

    col1, col2, col3, col4 = st.columns(4)
    tasks = [("🔄 转正", "转正", "task_proof"), ("💰 调薪", "调薪", "task_salary"),
             ("📋 调岗", "调岗", "task_transfer"), ("🚪 离职", "离职", "task_resign")]

    for col, (label, task_name, key) in zip([col1, col2, col3, col4], tasks):
        with col:
            if st.button(label, use_container_width=True, key=key):
                trigger_task(task_name)
                st.rerun()

    if st.session_state.task_result:
        result = st.session_state.task_result
        if result.get('success'):
            st.success(f"✅ {result.get('message')}")
            with st.expander("📋 查看任务详情"):
                st.json(result.get('data', {}))
        else:
            st.error(f"❌ {result.get('message')}")


def main():
    logger.info("HRM系统启动")
    st.set_page_config(page_title="HRM 系统", page_icon="🏢", layout="wide")
    init_session_state()

    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
        <span style="font-size: 42px;">🏢</span>
        <div>
            <h1 style="margin: 0; color: #1f77b4; font-weight: 700;">HRM 人力资源管理系统</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.login_success:
        display_user_info()
        return

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 12px; padding: 30px; color: white; text-align: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: white;">🤖 自动登录</h2>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">选择用户后点击按钮自动完成登录</p>
            </div>
            """, unsafe_allow_html=True)

            user_names = [user["name"] for user in USER_ACCOUNTS]
            selected_user = st.selectbox(
                "👤 选择登录用户",
                options=user_names,
                index=0,
                key="user_selector",
                help="下拉选择要登录的用户"
            )
            if selected_user != st.session_state.selected_user:
                st.session_state.selected_user = selected_user

            current_user = get_user_by_name(selected_user)
            if current_user:
                st.info(f"📋 当前选中: **{current_user['name']}** (账号: {current_user['username']})")

            st.write("点击下方按钮自动获取验证码并登录")

            if st.button("🚀 开始自动登录", use_container_width=True, type="primary"):
                perform_auto_login()
                st.rerun()


if __name__ == "__main__":
    main()