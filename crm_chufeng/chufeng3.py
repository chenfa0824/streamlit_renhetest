import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import logging

from config import DB_CONFIG, DEFAULT_SCHEMA, chufeng_upsertActivity

# ==================== 本地 Token 配置 ====================
CRM_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoiMSIsInVzZXJfa2V5IjoiNGI4YTBlODEtZWU0Yi00ZGM1LThiMWEtY2EyMzQ4ZjhkNDI2Iiwic291cmNldHlwZSI6MSwidXNlcm5hbWUiOiJhZG1pbiJ9.TRh9yVHxCSHZ6hCfK7UzU9SCytv5_A2vdA1zyEup-GmDqjSu20ZgUURkpfcnVSSXeWeDXXZtvH65yGQWFeEs3g"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(page_title="CRM系统测试工具集", page_icon="🧰", layout="wide")

# ==================== 全局CSS（含顶部留白压缩） ====================
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { height: 0rem !important; background: transparent !important; }
    div[data-testid="stToolbar"] { right: 0.5rem !important; top: 0.3rem !important; }
    h1 { margin-top: 0 !important; margin-bottom: 0.3rem !important; padding-top: 0 !important; font-size: 1.6rem !important; }
    h3 { margin-top: 0.4rem !important; margin-bottom: 0.3rem !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }

    .stButton > button {
        background-color: #004A99 !important; color: #fff !important;
        border: none !important; border-radius: 6px !important;
        padding: 0.5rem 1rem !important; font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #003a7a !important;
        box-shadow: 0 4px 12px rgba(0, 74, 153, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active { background-color: #002b5c !important; transform: translateY(0) !important; }
    .stButton > button:focus { box-shadow: 0 0 0 3px rgba(0, 74, 153, 0.4) !important; outline: none !important; }
    .stButton > button:disabled { background-color: #6688aa !important; color: #ddd !important; opacity: 0.6 !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 标题 ====================
st.markdown(
    "<h2 style='margin:0 0 0.4rem 0;padding:0;'>🧰 CRM系统测试工具集 "
    "<span style='font-size:0.75rem;color:#888;font-weight:400;'>"
    "🔑 全局 Token（所有 Tab 共用）</span></h2>",
    unsafe_allow_html=True
)

# ==================== 接口地址 ====================
XJJH_API_URL = "https://centertest.rhkj.com/prod-api/system/xjjh"
CLASS_SAVE_API_URL = "https://centertest.rhkj.com/prod-api/system/class/new/save"
TOKEN_CHECK_API_URL = "https://centertest.rhkj.com/prod-api/system/user/profile"

# 「总部活动」识别关键字
HQ_CATEGORY_KEYWORDS = ["总部活动", "总部"]


# ==================== 公共工具函数 ====================
def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"], port=DB_CONFIG["port"],
        database=DB_CONFIG["database"], user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


def execute_delete(sql, params=None):
    """执行删除SQL，返回 (影响行数, 日志列表)"""
    logs = []
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        logs.append(f"📝 执行SQL: {sql}")
        cur.execute(sql, params)
        count = cur.rowcount
        conn.commit()
        logs.append(f"✅ 影响行数: {count}")
        return count, logs
    finally:
        conn.close()
        logs.append("🔌 数据库连接已关闭")


def show_logs(logs, title="📋 执行日志"):
    if logs:
        with st.expander(title, expanded=True):
            for log in logs:
                st.text(log)


def render_delete_confirm(key_prefix, description, sql_preview, on_confirm):
    """通用删除确认界面"""
    st.warning(description)
    with st.expander("📝 将要执行的SQL语句", expanded=True):
        st.code(sql_preview, language="sql")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 确认删除", use_container_width=True, key=f"{key_prefix}_confirm"):
            with st.spinner("正在执行删除..."):
                try:
                    success, message, logs = on_confirm()
                    st.session_state[f"{key_prefix}_logs"] = logs
                    (st.success if success else st.info)(message)
                    show_logs(logs)
                    st.session_state[f"{key_prefix}_show"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 删除异常: {e}")
    with c2:
        if st.button("❌ 取消删除", use_container_width=True, key=f"{key_prefix}_cancel"):
            st.session_state[f"{key_prefix}_show"] = False
            st.rerun()


def normalize_token(raw_token):
    """清洗 token：去空白/引号，去掉 Bearer 前缀"""
    if raw_token is None:
        return ""
    t = str(raw_token).strip().strip('"').strip("'").strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t


def build_auth_headers(raw_token):
    """RuoYi 风格接口只传原始 token"""
    return {
        "Content-Type": "application/json",
        "Authorization": normalize_token(raw_token),
    }


def render_api_response(response, success_hint="✅ 请求成功！"):
    """统一渲染接口响应"""
    st.subheader("📊 响应结果")
    st.info(f"**状态码:** {response.status_code}")
    try:
        data = response.json()
        st.json(data)
        if response.status_code == 200:
            st.success(success_hint)
        elif response.status_code == 401:
            st.error("❌ 401 未授权 / 登录状态已过期")
            st.markdown(
                "**排查建议：**\n"
                "1. RuoYi 风格接口通常只接受**原始 token**（不带 `Bearer ` 前缀）。\n"
                "2. 检查 token 是否夹带引号、空格、换行。\n"
                "3. token 可能已过期，重新登录复制新 token。"
            )
        else:
            st.error(f"❌ 请求失败，状态码: {response.status_code}")
            if isinstance(data, dict):
                msg = data.get("msg") or data.get("message")
                if msg:
                    st.warning(f"**错误信息:** {msg}")
        return data
    except json.JSONDecodeError:
        st.text(response.text)
        (st.success if response.status_code == 200 else st.error)(
            "✅ 请求成功（响应非JSON格式）" if response.status_code == 200
            else f"❌ 请求失败，状态码: {response.status_code}"
        )
        return None


def post_api(url, payload, token, success_hint):
    """统一 POST：发请求 + 渲染响应 + 异常兜底，返回 response_data"""
    if not normalize_token(token):
        st.error("❌ 请先在页面顶部输入 Token")
        return None
    try:
        with st.spinner("请求中，请稍候..."):
            resp = requests.post(url=url, headers=build_auth_headers(token),
                                 json=payload, timeout=30)
            return render_api_response(resp, success_hint)
    except requests.exceptions.Timeout:
        st.error("⏰ 请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        st.error("🔌 网络连接失败，请检查网络或接口地址")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 请求异常: {e}")
    except Exception as e:
        st.error(f"❌ 未知错误: {e}")
    return None


def validate_token(raw_token):
    """调用轻量接口验证 token，返回 (ok, message)"""
    clean = normalize_token(raw_token)
    if not clean:
        return False, "Token 为空"
    try:
        resp = requests.get(url=TOKEN_CHECK_API_URL,
                            headers=build_auth_headers(clean), timeout=15)
    except requests.exceptions.RequestException as e:
        return False, f"请求异常: {e}"

    if resp.status_code == 200:
        try:
            data = resp.json()
            if isinstance(data, dict) and data.get("code") == 401:
                return False, f"token 无效/已过期: {data.get('msg')}"
            return True, "token 有效（HTTP 200）"
        except json.JSONDecodeError:
            return True, "token 有效（响应非 JSON，但 HTTP 200）"
    if resp.status_code == 401:
        try:
            data = resp.json()
            return False, f"401 未授权: {data.get('msg', '登录状态已过期')}"
        except json.JSONDecodeError:
            return False, "401 未授权（响应非 JSON）"
    return False, f"HTTP {resp.status_code}"


def match_hq_category_name(options):
    """从分类选项里找出「总部活动」名称：先精确，再模糊"""
    if not options:
        return None
    for kw in HQ_CATEGORY_KEYWORDS:
        if kw in options:
            return kw
    for kw in HQ_CATEGORY_KEYWORDS:
        for name in options:
            if kw in name:
                return name
    return None


# ==================== 日期时间 ====================
current_date = datetime.now().strftime("%Y-%m-%d")
current_time = datetime.now().strftime("%H:%M:%S")
current_datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
default_start_date = datetime.now().date()
default_end_date = default_start_date + timedelta(days=7)

# ==================== Session State ====================
defaults = {
    'category_options': [], 'category_mapping': {},
    'selected_category_id': None, 'selected_category_display': None,
    'category_loaded': False,
    'last_activity_id': '2095397849346129920',
    'act_del_show': False, 'act_del_type': None, 'act_del_id': '',
    'stu_del_show': False, 'stu_del_mobile': '',
    'token_check_msg': None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ==================== 全局 Token ====================
gt_col1, gt_col2 = st.columns([5, 1], vertical_alignment="bottom")
with gt_col1:
    global_token = st.text_input(
        "Token", type="password", value=CRM_TOKEN,
        placeholder="粘贴原始 token（无需 Bearer 前缀）",
        label_visibility="collapsed", key="global_token_input",
    )
with gt_col2:
    check_token_btn = st.button("🔍 校验 Token", use_container_width=True, key="check_token_btn")

if check_token_btn:
    with st.spinner("正在调用验证接口..."):
        st.session_state['token_check_msg'] = validate_token(global_token)

if st.session_state.get('token_check_msg'):
    ok, msg = st.session_state['token_check_msg']
    (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")


# ==================== 活动分类加载 ====================
def load_activity_categories():
    """加载分类，并把「总部活动」排到第一位；返回是否成功"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT activity_category_id, second_level
            FROM {DEFAULT_SCHEMA}.chufeng_activity_category
            WHERE second_level IS NOT NULL AND second_level != ''
            ORDER BY second_level
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()

        if not results:
            st.session_state.category_loaded = False
            return False

        options = [r[1] for r in results]
        mapping = {r[1]: r[0] for r in results}

        hq_name = match_hq_category_name(options)
        if hq_name:
            options.remove(hq_name)
            options.insert(0, hq_name)

        st.session_state.category_options = options
        st.session_state.category_mapping = mapping
        st.session_state.category_loaded = True

        default_name = hq_name or (options[0] if options else None)
        if default_name:
            st.session_state.selected_category_display = default_name
            st.session_state.selected_category_id = mapping.get(default_name)
        return True
    except Exception as e:
        logger.error(f"加载活动分类失败: {e}")
        st.session_state.category_loaded = False
        return False


if not st.session_state.category_loaded:
    with st.spinner("正在加载活动分类数据..."):
        load_activity_categories()

# ==================== Tabs ====================
tab_create, tab_delete, tab_xj, tab_class, tab_ygkj, tab_query = st.tabs([
    "📝 新增楚凤活动",
    "🗑️ 删除楚凤报名和签到数据",
    "📢 新增宣讲计划",
    "🏫 新增班级-训练营",
    "🧮 新增班级-运管课",
    "🔍 数据库查询"
])

# ------------------------------------------------------------------
# TAB 1: 创建活动
# ------------------------------------------------------------------
with tab_create:
    if st.session_state.category_loaded and st.session_state.category_options:
        options = st.session_state.category_options
        hq_name = match_hq_category_name(options)
        default_index = options.index(hq_name) if hq_name and hq_name in options else 0

        selected_category_display = st.selectbox(
            "选择活动分类 (secondLevel)",
            options=options, index=default_index,
            help="默认选中「总部活动」，可手动切换。"
        )
        st.session_state.selected_category_display = selected_category_display
        st.session_state.selected_category_id = st.session_state.category_mapping.get(selected_category_display)
    elif not st.session_state.category_loaded:
        st.warning("⚠️ 加载活动分类失败，请检查数据库连接")
        if st.button("🔄 重新加载分类数据"):
            st.session_state.category_loaded = False
            load_activity_categories()
            st.rerun()
    else:
        st.info("ℹ️ 暂无活动分类数据")

    def is_hq_category():
        name = st.session_state.get("selected_category_display") or ""
        hq_name = match_hq_category_name(st.session_state.get("category_options") or [])
        return bool(hq_name) and name == hq_name

    def build_payload():
        hq = is_hq_category()
        end_date = (datetime.now().date() + timedelta(days=7)).strftime("%Y-%m-%d") if hq else current_date
        return {
            "activityId": "",
            "activityCategoryId": st.session_state.selected_category_id,
            "activityName": f"楚风活动{current_datetime_str}",
            "startDate": current_date,
            "endDate": end_date,
            "lecturer": "陈发123",
            "quota": 100 if hq else 3,
            "closeDate": end_date,
            "coverUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415725506_1.jpeg",
            "detailUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415728971_2.png",
            "courseList": [{
                "courseId": "", "activityId": "", "courseName": "课程123",
                "courseNo": 1, "mode": "线下", "lecturer": "老师名字",
                "lectureDate": current_date, "startTime": current_time,
                "endTime": current_time, "location": "地址"
            }],
            "registerPage": "{\"top\":{\"bottom\":100,\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg\"},\"form\":[{\"type\":1,\"placeholder\":\"请输入手机号\",\"required\":1,\"label\":\"手机\",\"options\":[],\"id\":\"1\"}],\"bottom\":{\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png\",\"top\":100},\"btnList\":[{\"btType\":\"1\",\"url\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png\",\"locationType\":\"2\",\"width\":100,\"height\":100,\"left\":100,\"bottom\":100}]}",
            "registerPageForm": {
                "top": {"bottom": 100, "imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg"},
                "form": [{"type": 1, "placeholder": "请输入手机号", "required": 1, "label": "手机", "options": [], "id": "1"}],
                "bottom": {"imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png", "top": 100},
                "btnList": [{"btType": "1", "url": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png", "locationType": "2", "width": 100, "height": 100, "left": 100, "bottom": 100}]
            },
            "status": 1
        }

    info_col1, info_col2 = st.columns(2)
    info_col1.info(f"📅 当前日期: {current_date}")
    info_col2.info(f"🕐 当前时间戳: {current_datetime_str}")

    if st.button("创建楚凤活动", use_container_width=True, key="create_activity_btn"):
        if not st.session_state.selected_category_id:
            st.error("❌ 请先选择活动分类")
        else:
            data = post_api(chufeng_upsertActivity, build_payload(), global_token,
                            "✅ 楚凤活动创建成功！")
            if isinstance(data, dict) and data.get("msg"):
                aid = data["msg"]
                st.session_state['last_activity_id'] = aid
                st.info(f"📌 活动ID: {aid}，可切换到「删除数据」或「数据库查询」Tab 使用")

    with st.expander("查看请求参数"):
        preview = build_payload()
        preview["activityCategoryId"] = st.session_state.selected_category_id or "请从下拉框选择"
        st.json(preview)

# ------------------------------------------------------------------
# TAB 2: 删除数据
# ------------------------------------------------------------------
with tab_delete:
    del_col1, del_col2 = st.columns(2)

    with del_col1:
        st.subheader("🗑️ 删除活动记录")
        aid_input = st.text_input(
            "活动ID", value=st.session_state.get('last_activity_id', ''),
            placeholder="请输入活动ID", key="activity_id_for_delete"
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("删除报名记录", use_container_width=True, key="delete_apply_btn"):
                if not aid_input:
                    st.error("❌ 请先输入活动ID")
                else:
                    st.session_state.update(act_del_show=True, act_del_type="apply", act_del_id=aid_input)
                    st.rerun()
        with c2:
            if st.button("删除签到记录", use_container_width=True, key="delete_sign_btn"):
                if not aid_input:
                    st.error("❌ 请先输入活动ID")
                else:
                    st.session_state.update(act_del_show=True, act_del_type="sign", act_del_id=aid_input)
                    st.rerun()

        if st.session_state.act_del_show:
            aid = st.session_state.act_del_id
            dtype = st.session_state.act_del_type
            title, table = ("活动报名记录", "chufeng_activity_apply") if dtype == "apply" \
                else ("活动签到记录", "chufeng_activity_sign")
            sql = f"DELETE FROM {DEFAULT_SCHEMA}.{table} WHERE activity_id = '{aid}'"

            def do_delete_activity():
                logs = [f"🕐 {datetime.now():%Y-%m-%d %H:%M:%S} - 开始删除{title}",
                        f"📱 活动ID: {aid}", f"📌 Schema: {DEFAULT_SCHEMA}", f"📌 表名: {table}"]
                count, more = execute_delete(
                    f"DELETE FROM {DEFAULT_SCHEMA}.{table} WHERE activity_id = %s", (aid,))
                logs.extend(more)
                if count > 0:
                    return True, f"✅ 删除成功！共删除 {count} 条{title}", logs
                return False, f"ℹ️ 未找到活动ID {aid} 的{title}", logs

            render_delete_confirm("act_del",
                                  f"⚠️ 即将删除活动ID为 **{aid}** 的{title}，请确认！",
                                  sql, do_delete_activity)

    with del_col2:
        st.subheader("🗑️ 删除老学员记录")
        with st.expander("📝 查看需要执行的SQL语句"):
            st.markdown(f"**当前Schema: `{DEFAULT_SCHEMA}`**")
            st.code(f"""
DELETE FROM {DEFAULT_SCHEMA}.account WHERE dianhua = '{{mobile}}';
DELETE FROM {DEFAULT_SCHEMA}.t_student_info WHERE phones = '{{"{{mobile}}"}}';
DELETE FROM {DEFAULT_SCHEMA}.chufeng_user WHERE mobile = '{{mobile}}';
""", language="sql")
            st.warning("⚠️ 此操作将直接删除数据，请谨慎操作！")

        mobile_input = st.text_input("手机号", value="18792169903",
                                     placeholder="请输入要删除数据的手机号", key="mobile_input")
        if st.button("删除老学员数据", use_container_width=True, key="delete_student_btn"):
            if not mobile_input:
                st.error("❌ 请先输入手机号")
            else:
                st.session_state.update(stu_del_show=True, stu_del_mobile=mobile_input)
                st.rerun()

        if st.session_state.stu_del_show:
            mobile = st.session_state.stu_del_mobile
            sql_preview = f"""
DELETE FROM {DEFAULT_SCHEMA}.account WHERE dianhua = '{mobile}';
DELETE FROM {DEFAULT_SCHEMA}.t_student_info WHERE phones = '{{"{mobile}"}}';
DELETE FROM {DEFAULT_SCHEMA}.chufeng_user WHERE mobile = '{mobile}';
"""

            def do_delete_student():
                logs = [f"🕐 {datetime.now():%Y-%m-%d %H:%M:%S} - 开始删除操作",
                        f"📱 手机号: {mobile}", f"📌 Schema: {DEFAULT_SCHEMA}"]
                conn = get_db_connection()
                try:
                    cur = conn.cursor()
                    cur.execute(f"DELETE FROM {DEFAULT_SCHEMA}.account WHERE dianhua = %s", (mobile,))
                    n_account = cur.rowcount
                    cur.execute(f"DELETE FROM {DEFAULT_SCHEMA}.t_student_info WHERE phones = %s",
                                (f'{{"{mobile}"}}',))
                    n_stu = cur.rowcount
                    cur.execute(f"DELETE FROM {DEFAULT_SCHEMA}.chufeng_user WHERE mobile = %s", (mobile,))
                    n_user = cur.rowcount
                    conn.commit()
                    logs += [f"✅ account: {n_account} 条",
                             f"✅ t_student_info: {n_stu} 条",
                             f"✅ chufeng_user: {n_user} 条",
                             "🔌 数据库连接已关闭"]
                    total = n_account + n_stu + n_user
                    if total > 0:
                        return True, f"✅ 删除成功！共 {total} 条 (account:{n_account}, student:{n_stu}, user:{n_user})", logs
                    return False, f"ℹ️ 未找到手机号 {mobile} 的相关数据", logs
                finally:
                    conn.close()

            render_delete_confirm("stu_del",
                                  f"⚠️ 即将删除手机号为 **{mobile}** 的学员数据，请确认！",
                                  sql_preview, do_delete_student)

    for prefix, label in [("act_del", "活动删除日志"), ("stu_del", "学员删除日志")]:
        logs = st.session_state.get(f"{prefix}_logs")
        if logs:
            show_logs(logs, f"📋 {label}")

# ------------------------------------------------------------------
# TAB 3: 宣讲计划
# ------------------------------------------------------------------
with tab_xj:
    st.subheader("📢 创建宣讲计划")
    xj = {}

    c1, c2, c3 = st.columns(3)
    with c1:
        xj['spzt'] = st.selectbox("审批状态 (spzt)", ["草稿", "待审批", "已审批"], index=0)
        xj['name'] = st.text_input("计划名称 (name)",
                                   value=st.session_state.get('xj_plan_name') or f"宣讲计划{current_datetime_str}")
        xj_xjrq = st.date_input("宣讲日期 (xjrq)", value=datetime.now().date())
    with c2:
        xj['kssj'] = st.text_input("开始时间 (kssj)", value="00:00:00")
        xj['jssj'] = st.text_input("结束时间 (jssj)", value="23:30:00")
        xj['hdzt'] = st.text_input("活动主题 (hdzt)", value="宣讲活动")
        xj['xjlx'] = st.text_input("宣讲类型 (xjlx)", value="校区")
    with c3:
        xj['jsname'] = st.text_input("讲师姓名 (jsname)", value="王明兰")
        xj['lssj'] = st.text_input("联系手机 (lssj)", value="185****4323")
        xj['skjs'] = st.text_input("授课教室 (skjs)", value="a2820191E70F441mqW3c")
        xj['ssxq'] = st.text_input("所属校区 (ssxq)", value="a102019ACD817F81nqg5")

    st.markdown("---")
    st.markdown("**🏢 区域 / 管理信息**")
    c4, c5, c6 = st.columns(3)
    with c4:
        xj['qyName'] = st.text_input("区域名称 (qyName)", value="湖北中部区域")
        xj['qy'] = st.text_input("区域ID (qy)", value="1865396876958654464")
    with c5:
        xj['gljl'] = st.text_input("管理经理ID (gljl)", value="0052019C90A999AhSwUu")
        xj['gljlName'] = st.text_input("管理经理名称 (gljlName)", value="胡英_已禁")
    with c6:
        xj['xz'] = st.text_input("校长ID (xz)", value="0052021E788EFF1x7Rks")
        xj['xzName'] = st.text_input("校长名称 (xzName)", value="卫春")

    st.markdown("---")
    st.markdown("**📌 其他信息**")
    c7, c8, c9 = st.columns(3)
    with c7:
        xj['hddz'] = st.text_input("活动地址 (hddz)", value="活动地址")
        xj['hdfy'] = st.text_input("活动费用 (hdfy)", value="100")
    with c8:
        xj['xjmb'] = st.number_input("宣讲目标 (xjmb)", value=10000, step=1)
        xj['attendCampusNumType'] = st.text_input("参会校区数量类型 (attendCampusNumType)", value="1")
    with c9:
        xj['glqdbj'] = st.text_input("关联渠道标记 (glqdbj)", value="")
        xj['glqdbjName'] = st.text_input("关联渠道标记名称 (glqdbjName)", value="")

    def build_xj_payload():
        return {
            **xj,
            "xjrq": xj_xjrq.strftime("%Y-%m-%d"),
            "isPresidentPreach": None,
            "hotelTeacherName": "", "hotelTeacherId": "",
        }

    with st.expander("查看请求参数"):
        st.json(build_xj_payload())

    if st.button("📢 创建宣讲计划", use_container_width=True, key="create_xj_btn"):
        post_api(XJJH_API_URL, build_xj_payload(), global_token, "✅ 宣讲计划创建成功！")

# ------------------------------------------------------------------
# TAB 4: 训练营班级
# ------------------------------------------------------------------
with tab_class:
    st.subheader("🏫 新增班级-训练营")
    cls = {}

    c1, c2, c3 = st.columns(3)
    with c1:
        cls['className'] = st.text_input("班级名称 (className)",
                                         value="2026上海松江校区全面预算实战（训练营）白班1006期")
        cls['courseType'] = st.selectbox("课程类型 (courseType)", ["面授", "线上", "直播"], index=0)
        cls['subjectId'] = st.text_input("科目ID (subjectId)", value="a37202073A0E06CVCQ4u")
    with c2:
        cls_start = st.date_input("开始日期 (startTime)", value=default_start_date)
        cls_end = st.date_input("结束日期 (endTime)", value=default_end_date)
        cls['campusId'] = st.text_input("校区ID (campusId)", value="a102019135623F0K8AVB")
    with c3:
        cls['classType'] = st.selectbox("班级类型 (classType)", ["面授", "线上", "直播"], index=0)
        cls['classroomId'] = st.text_input("教室ID (classroomId)", value="a402019DC01FDF6NVk65")
        cls['attendClassTypeKey'] = st.text_input("上课班型 (attendClassTypeKey)", value="白班")

    st.markdown("---")
    st.markdown("**👨‍🏫 讲师 / 项目信息**")
    c4, c5, c6 = st.columns(3)
    with c4:
        cls['teacherId'] = st.text_input("讲师ID (teacherId)", value="a282019E8E4B844EGwfj")
        cls['teacherNo'] = st.text_input("讲师工号 (teacherNo)", value="101551")
    with c5:
        cls['project'] = st.text_input("项目 (project)", value="全面预算实战训练营项目")
        cls['classEnabled'] = st.selectbox("班级启用状态 (classEnabled)", ["启用", "禁用"], index=0)
    with c6:
        cls['arrangeClassStatusKey'] = st.selectbox("排课状态", ["已排课", "未排课"], index=0)
        cls['attendClassStatusKey'] = st.selectbox("上课状态", ["已结课", "未结课", "进行中"], index=0)

    st.markdown("---")
    st.markdown("**🏢 审批 / 区域信息**")
    c7, c8, c9 = st.columns(3)
    with c7:
        cls['approvalStatus'] = st.selectbox("审批状态", ["审批通过", "待审批", "审批拒绝"], index=0)
        cls['areaType'] = st.text_input("区域类型 (areaType)", value="0")
    with c8:
        cls['involvedRegionIds'] = st.text_input("涉及区域ID", value="1865396533650677760")
        cls['attendCampusNumType'] = st.text_input("参会校区数量类型", value="")
    with c9:
        cls_city_list_input = st.text_input("城市/校区列表 (逗号分隔)", value="a102019135623F0K8AVB")

    st.markdown("---")
    st.markdown("**🏨 酒店 / 坐标**")
    ch1, ch2, ch3 = st.columns(3)
    with ch1:
        cls['hotelName'] = st.text_input("酒店名称", value="北京朝阳站")
    with ch2:
        cls['longitude'] = st.text_input("经度", value="116.505577")
    with ch3:
        cls['latitude'] = st.text_input("纬度", value="39.944695")

    st.markdown("---")
    st.markdown("**⏰ 上课时间**")
    c10, c11, c12 = st.columns(3)
    with c10:
        cls['week'] = st.text_input("上课星期（分号分隔）",
                                    value="星期日;星期一;星期二;星期三;星期四;星期五;星期六")
    with c11:
        cls['firstClassStartTime'] = st.text_input("第一节开始", value="09:00:00")
        cls['secondClassStartTime'] = st.text_input("第二节开始", value="14:00:00")
    with c12:
        cls['firstClassEndTime'] = st.text_input("第一节结束", value="11:30:00")
        cls['secondClassEndTime'] = st.text_input("第二节结束", value="16:30:00")

    c13, c14 = st.columns(2)
    with c13:
        cls['thirdClassStartTime'] = st.text_input("第三节开始", value="")
    with c14:
        cls['thirdClassEndTime'] = st.text_input("第三节结束", value="")

    def build_class_payload():
        return {
            **cls,
            "startTime": cls_start.strftime("%Y-%m-%d"),
            "endTime": cls_end.strftime("%Y-%m-%d"),
            "salesPlanNum": None,
            "isSaveAsTemplate": "0",
            "classHolidayVos": [],
            "cityList": [s.strip() for s in cls_city_list_input.split(",") if s.strip()],
            "bindOneToOneOrderId": "", "bindOneToOneOrderNo": "",
            "isRepeat": "0",
            "liveStreamRoom": {},
        }

    with st.expander("查看请求参数"):
        st.json(build_class_payload())

    if st.button("🏫 创建班级", use_container_width=True, key="create_class_btn"):
        if not cls['className']:
            st.error("❌ 请填写班级名称")
        else:
            post_api(CLASS_SAVE_API_URL, build_class_payload(), global_token,
                     "✅ 班级创建成功！")

# ------------------------------------------------------------------
# TAB 5: 运管课班级
# ------------------------------------------------------------------
with tab_ygkj:
    st.subheader("🧮 新增班级-运管课")

    ygkj_class_name = st.text_input("班级名称 (className)",
                                    value="2026武汉软件园校区运营管理会计I白班1008期",
                                    key="ygkj_class_name")
    c1, c2 = st.columns(2)
    with c1:
        ygkj_start = st.date_input("开始日期 (startTime)", value=default_start_date, key="ygkj_start_date")
    with c2:
        ygkj_end = st.date_input("结束日期 (endTime)", value=default_end_date, key="ygkj_end_date")

    def build_ygkj_payload():
        return {
            "className": ygkj_class_name,
            "courseType": "面授",
            "subjectId": "a372019F27B1E4A493wM",
            "startTime": ygkj_start.strftime("%Y-%m-%d"),
            "campusId": "a102019712DE14FcsULm",
            "endTime": ygkj_end.strftime("%Y-%m-%d"),
            "classType": "面授",
            "classroomId": "a4020195AACE4B1qUIwL",
            "teacherId": "a2820197F783E10rcnhq",
            "teacherNo": "100608",
            "attendClassTypeKey": "白班",
            "project": None,
            "classEnabled": "启用",
            "arrangeClassStatusKey": "已排课",
            "attendClassStatusKey": "开课中",
            "approvalStatus": "审批通过",
            "salesPlanNum": None,
            "attendCampusNumType": "",
            "involvedRegionIds": "",
            "areaType": "0",
            "isSaveAsTemplate": "0",
            "classHolidayVos": [],
            "cityList": ["a102019712DE14FcsULm"],
            "hotelName": None, "longitude": None, "latitude": None,
            "bindOneToOneOrderId": "", "bindOneToOneOrderNo": "",
            "isRepeat": "0",
            "week": "星期一;星期二;星期三;星期四;星期五;星期六",
            "firstClassStartTime": "09:00:00", "firstClassEndTime": "11:30:00",
            "secondClassStartTime": "14:00:00", "secondClassEndTime": "16:30:00",
            "thirdClassStartTime": "", "thirdClassEndTime": "",
            "liveStreamRoom": {},
        }

    with st.expander("查看请求参数", expanded=False):
        st.json(build_ygkj_payload())

    if st.button("🧮 一键创建运管课班级", use_container_width=True, key="create_ygkj_btn"):
        if not ygkj_class_name:
            st.error("❌ 请填写班级名称")
        else:
            post_api(CLASS_SAVE_API_URL, build_ygkj_payload(), global_token,
                     "✅ 运管课班级创建成功！")

# ------------------------------------------------------------------
# TAB 6: 数据库查询
# ------------------------------------------------------------------
with tab_query:
    for k, v in {'schemas': [], 'selected_schema': DEFAULT_SCHEMA,
                 'tables': [], 'selected_table': 't_cloudstorage_file_path',
                 'db_connected': False, 'db_initialized': False}.items():
        st.session_state.setdefault(k, v)

    def load_tables(schema):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema,))
        tables = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return tables

    if not st.session_state.db_initialized:
        with st.spinner("正在连接数据库..."):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema','pg_catalog','pg_toast','pg_temp_1','pg_toast_temp_1')
                    ORDER BY schema_name
                """)
                schemas = [r[0] for r in cur.fetchall()]
                cur.close()
                conn.close()

                st.session_state.schemas = schemas
                st.session_state.db_connected = True
                if DEFAULT_SCHEMA in schemas:
                    st.session_state.selected_schema = DEFAULT_SCHEMA
                elif schemas:
                    st.session_state.selected_schema = schemas[0]
                    st.warning(f"⚠️ 默认Schema '{DEFAULT_SCHEMA}' 不存在，已切换到 '{schemas[0]}'")

                if st.session_state.selected_schema in schemas:
                    tables = load_tables(st.session_state.selected_schema)
                    st.session_state.tables = tables
                    if tables and st.session_state.selected_table not in tables:
                        st.session_state.selected_table = tables[0]
                st.session_state.db_initialized = True
            except Exception as e:
                st.session_state.db_connected = False
                st.session_state.db_initialized = True
                st.error(f"❌ 数据库连接失败: {e}")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        with st.expander("📊 数据库连接信息", expanded=False):
            st.markdown(f"- **主机:** `{DB_CONFIG['host']}`")
            st.markdown(f"- **端口:** `{DB_CONFIG['port']}`")
            st.markdown(f"- **数据库:** `{DB_CONFIG['database']}`")
            st.markdown(f"- **用户:** `{DB_CONFIG['user']}`")
            st.markdown(f"- **默认Schema:** `{DEFAULT_SCHEMA}`")
            st.markdown("---")
            if st.session_state.db_connected:
                st.success("✅ 数据库已连接")
                st.metric("📋 Schema数量", len(st.session_state.schemas))
                if st.session_state.tables:
                    st.metric("📊 表数量", len(st.session_state.tables))
                st.info(f"📌 当前Schema: `{st.session_state.selected_schema}`")
            else:
                st.error("❌ 数据库未连接")

    with col_right:
        if st.session_state.db_connected and st.session_state.schemas:
            col_s, col_t = st.columns(2)
            with col_s:
                st.markdown("**📋 选择Schema**")
                cur_idx = st.session_state.schemas.index(st.session_state.selected_schema) \
                    if st.session_state.selected_schema in st.session_state.schemas else 0
                new_schema = st.selectbox("Schema", options=st.session_state.schemas,
                                          index=cur_idx, key="schema_select")
                if new_schema != st.session_state.selected_schema:
                    st.session_state.selected_schema = new_schema
                    with st.spinner(f"正在加载 '{new_schema}' 的表..."):
                        try:
                            st.session_state.tables = load_tables(new_schema)
                            if st.session_state.tables:
                                st.session_state.selected_table = st.session_state.tables[0]
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 加载表失败: {e}")

            with col_t:
                if st.session_state.tables:
                    st.markdown("**📊 选择表**")
                    cur_t_idx = st.session_state.tables.index(st.session_state.selected_table) \
                        if st.session_state.selected_table in st.session_state.tables else 0
                    st.session_state.selected_table = st.selectbox(
                        "表名", options=st.session_state.tables, index=cur_t_idx, key="table_select")
                else:
                    st.warning("⚠️ 当前Schema下没有找到表")

    if st.session_state.db_connected and st.session_state.selected_table:
        st.subheader("🔍 数据查询")
        q1, q2 = st.columns([3, 1])
        with q1:
            activity_id_input = st.text_input(
                "活动ID (查询条件)",
                value=st.session_state.get('last_activity_id', ''),
                placeholder="请输入活动ID"
            )
        with q2:
            st.markdown("<br>", unsafe_allow_html=True)
            query_button = st.button("🔍 查询数据", use_container_width=True, key="query_btn")

        if query_button:
            if not activity_id_input:
                st.error("❌ 请先输入活动ID")
            else:
                with st.spinner("正在查询..."):
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                        sql = (f"SELECT * FROM {st.session_state.selected_schema}."
                               f"{st.session_state.selected_table} WHERE activity_id = %s")
                        cur.execute(sql, (activity_id_input,))
                        results = cur.fetchall()
                        cur.close()
                        conn.close()

                        c1, c2, c3 = st.columns(3)
                        c1.metric("📋 Schema", st.session_state.selected_schema)
                        c2.metric("📊 表名", st.session_state.selected_table)
                        c3.metric("🔍 条件", f"activity_id = {activity_id_input}")

                        st.subheader("📊 查询结果")
                        if results:
                            st.success(f"✅ 查询成功，共 {len(results)} 条记录")
                            for idx, row in enumerate(results, 1):
                                with st.expander(f"📄 记录 {idx}"):
                                    st.json(dict(row))
                            st.markdown("**表格视图:**")
                            st.dataframe(results, use_container_width=True)
                            st.markdown("**📋 字段列表:**")
                            st.write(", ".join(f"`{f}`" for f in results[0].keys()))
                        else:
                            st.warning(f"⚠️ 未找到 activity_id={activity_id_input} 的记录")
                    except Exception as e:
                        st.error(f"❌ 查询异常: {e}")

st.caption("💡 提示: 请确保 Token 有效，且具有相应操作权限")