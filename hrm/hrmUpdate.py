import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import sql
import time
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import json
import base64
import ddddocr
from io import BytesIO
from PIL import Image
import traceback

load_dotenv()

# 全局日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hrm.log')


# 配置日志 - 只使用一个文件处理器
def setup_logging():
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 清除已有的处理器，避免重复
    if logger.handlers:
        logger.handlers.clear()

    # 文件处理器 - 追加模式，UTF-8编码
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    return logger


# 初始化日志
logger = setup_logging()


# 自定义日志函数 - 同时写入session_state和文件
def add_log(message, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"

    # 写入session_state（用于界面显示）
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    st.session_state.log_messages.append(log_entry)
    if len(st.session_state.log_messages) > 500:
        st.session_state.log_messages = st.session_state.log_messages[-500:]

    # 写入日志文件（只通过logger写入，不重复打印到控制台）
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)


# 仅写入文件的日志（不显示在界面）
def log_to_file_only(message, level="INFO"):
    """仅写入文件日志，不显示在界面，避免重复"""
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)


st.set_page_config(page_title="HRM修改员工绩效数据", page_icon="📊", layout="wide")

# CSS样式
st.markdown("""
    <style>
        .stDataFrame {width: 100% !important;}
        .stDataFrame table {width: 100% !important;}
        .stDataFrame th, .stDataFrame td {padding: 4px 8px !important; white-space: nowrap !important; font-size: 14px !important; text-align: center !important;}
        .stDataFrame th {background-color: #f0f2f6 !important;}
        .stDataFrame .col-user_id {display: none !important;}
        .stTextInput > div > div {background-color: transparent !important;}
        .stTextInput > div > div > input {background-color: white !important;}
    </style>
""", unsafe_allow_html=True)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('PG_HOST', 'pgm-uf6jv8kq7xfyu4fako.pg.rds.aliyuncs.com'),
    'port': int(os.getenv('PG_PORT', 5432)),
    'db': os.getenv('PG_DB', 'crmdb_test'),
    'user': os.getenv('PG_USER', 'renhe_test'),
    'pwd': os.getenv('PG_PWD', 'B72TjV4xTU5wQpVK'),
    'schema': os.getenv('PG_SCHEMA', 'cust_u_rhkj')
}

# HRM API配置
HRM_API_CONFIG = {
    'login_url': "https://hrm-apitest.whrhkj.com/user/login",
    'captcha_url': "https://hrm-apitest.whrhkj.com/sys/randomImage/",
    'performance_url': "https://hrm-apitest.whrhkj.com/employee/performance/list",
    'username': "112054",
    'password': "algo1129"
}


# 会话状态初始化
def init_session():
    defaults = {
        'pg_host': DB_CONFIG['host'],
        'pg_port': DB_CONFIG['port'],
        'pg_db': DB_CONFIG['db'],
        'pg_user': DB_CONFIG['user'],
        'pg_pwd': DB_CONFIG['pwd'],
        'pg_schema': DB_CONFIG['schema'],
        'table_list': [],
        'selected_table': 't_perf_deduction',
        'connection_status': False,
        'connection_error': None,
        'data_loaded': False,
        'log_messages': [],
        'save_status': None,
        'last_edited_data': None,
        'search_name': "",
        'search_post': "",
        # 接口调用相关状态
        'api_user_name': "",
        'api_month': "",
        'api_perf_level': "S",
        'api_result': None,
        # 批量校验相关状态
        'batch_user_name': "",
        'batch_result': None,
        # HRM API相关状态
        'hrm_jwt_token': None,
        'hrm_login_success': False,
        'hrm_user_info': None,
        'hrm_initialized': False,
        'hrm_query_result': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def log_separator(title="", char="=", length=80):
    """打印分隔线"""
    if title:
        padding = (length - len(title) - 2) // 2
        separator = char * padding + f" {title} " + char * (length - padding - len(title) - 2)
        if len(separator) < length:
            separator += char * (length - len(separator))
    else:
        separator = char * length
    add_log(separator, "INFO")


def log_request(url, method="POST", headers=None, data=None, level="INFO"):
    """打印请求日志"""
    add_log(f"🌐 {method} 请求: {url}", level)
    if headers:
        # 隐藏敏感信息
        safe_headers = headers.copy() if headers else {}
        if 'x-access-token' in safe_headers and safe_headers['x-access-token']:
            token = safe_headers['x-access-token']
            safe_headers['x-access-token'] = f"{token[:20]}..."
        add_log(f"  📋 请求头: {json.dumps(safe_headers, ensure_ascii=False)}", level)
    if data:
        add_log(f"  📦 请求体: {json.dumps(data, ensure_ascii=False, default=str)}", level)


def log_response(response, level="INFO"):
    """打印响应日志"""
    add_log(f"📥 响应状态码: {response.status_code}", level)
    try:
        result = response.json()
        # 隐藏敏感信息
        safe_result = result.copy() if isinstance(result, dict) else result
        if isinstance(safe_result, dict):
            if 'result' in safe_result and isinstance(safe_result['result'], dict):
                if 'token' in safe_result['result'] and safe_result['result']['token']:
                    safe_result['result']['token'] = f"{safe_result['result']['token'][:20]}..."
        add_log(f"  📄 响应体: {json.dumps(safe_result, ensure_ascii=False, default=str)[:2000]}", level)
        if len(json.dumps(safe_result, ensure_ascii=False)) > 2000:
            add_log(f"  📄 响应体长度: {len(json.dumps(safe_result, ensure_ascii=False))} 字符", level)
    except:
        add_log(f"  📄 响应体: {response.text[:500]}", level)


# 数据库连接
def get_connection():
    try:
        add_log("🔗 正在连接数据库...", "INFO")
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )
        add_log("✅ 数据库连接成功", "INFO")
        return conn, True, None
    except Exception as e:
        add_log(f"❌ 数据库连接失败: {e}", "ERROR")
        return None, False, str(e)


def execute_query(query_str):
    """执行查询返回DataFrame"""
    add_log(f"📊 执行SQL查询: {query_str[:200]}...", "INFO")
    try:
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )
        try:
            result = pd.read_sql_query(query_str, conn)
            add_log(f"✅ SQL查询成功，返回 {len(result)} 行数据", "INFO")
            return result
        finally:
            conn.close()
    except Exception as e:
        add_log(f"❌ SQL查询失败: {e}", "ERROR")
        return None


@st.cache_data(ttl=300)
def get_tables_in_schema():
    """获取schema下所有表"""
    add_log("📋 获取schema下的所有表...", "INFO")
    try:
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY table_name
            """, (st.session_state.pg_schema,))
            tables = [row[0] for row in cur.fetchall()]
            cur.close()
            add_log(f"✅ 获取到 {len(tables)} 个表", "INFO")
            return tables
        finally:
            conn.close()
    except Exception as e:
        add_log(f"❌ 获取表列表失败: {e}", "ERROR")
        return []


def get_table_columns(conn, table_name):
    """获取表的列信息"""
    add_log(f"📋 获取表 '{table_name}' 的列信息...", "INFO")
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position
    """, (st.session_state.pg_schema, table_name))
    columns = [row[0] for row in cur.fetchall()]
    cur.close()
    add_log(f"✅ 获取到 {len(columns)} 列: {columns}", "INFO")
    return columns


def check_table_exists(conn, table_name):
    """检查表是否存在（大小写不敏感）"""
    add_log(f"🔍 检查表 '{table_name}' 是否存在...", "INFO")
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (SELECT 1 FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s)
    """, (st.session_state.pg_schema, table_name))
    exists = cur.fetchone()[0]
    if exists:
        cur.close()
        add_log(f"✅ 表 '{table_name}' 存在", "INFO")
        return True, table_name

    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = %s AND LOWER(table_name) = LOWER(%s)
    """, (st.session_state.pg_schema, table_name))
    result = cur.fetchone()
    cur.close()
    if result:
        add_log(f"✅ 表 '{result[0]}' 存在（大小写不敏感匹配）", "INFO")
        return True, result[0]
    add_log(f"❌ 表 '{table_name}' 不存在", "WARNING")
    return False, None


def get_user_info(user_ids):
    """批量查询用户姓名和岗位"""
    add_log(f"👤 批量查询用户信息: {len(user_ids)} 个用户", "INFO")
    if not user_ids:
        return {}

    try:
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )
        try:
            exists, _ = check_table_exists(conn, 'sys_user')
            if not exists:
                add_log("⚠️ sys_user 表不存在", "WARNING")
                return {}

            columns = get_table_columns(conn, 'sys_user')

            # 字段映射
            id_field = next((f for f in ['user_id', 'id', 'userId'] if f in columns), None)
            name_field = next((f for f in ['name', 'user_name', 'username', 'real_name'] if f in columns), None)
            post_field = next(
                (f for f in ['position', 'post', 'post_name', 'job', 'job_title', '岗位', '职位'] if f in columns),
                None)

            if not id_field or not name_field:
                add_log(f"⚠️ 未找到ID或姓名字段", "WARNING")
                return {}

            # 构建查询
            placeholders = ','.join(['%s'] * len(user_ids))
            fields = [id_field, name_field]
            if post_field:
                fields.append(post_field)

            query = f'SELECT {", ".join(f"\"{f}\"" for f in fields)} FROM "{st.session_state.pg_schema}"."sys_user" WHERE "{id_field}" IN ({placeholders})'
            add_log(f"📊 查询用户SQL: {query[:200]}...", "INFO")
            add_log(f"📊 用户ID列表: {user_ids}", "INFO")

            cur = conn.cursor()
            cur.execute(query, user_ids)
            results = cur.fetchall()
            cur.close()

            user_info = {}
            for row in results:
                info = {'name': row[1], 'post': row[2] if post_field and len(row) > 2 and row[2] else ''}
                user_info[row[0]] = info

            add_log(f"✅ 查询到 {len(user_info)} 个用户信息", "INFO")
            for uid, info in user_info.items():
                add_log(f"  {uid}: {info['name']} ({info['post']})", "INFO")
            return user_info
        finally:
            conn.close()
    except Exception as e:
        add_log(f"❌ 查询用户信息失败: {e}", "ERROR")
        return {}


def update_single_record(user_id, month, perf_level, table_name):
    """更新单条绩效数据"""
    log_separator(f"更新单条绩效数据")
    add_log(f"📝 参数: user_id={user_id}, month={month}, perf_level={perf_level}, table={table_name}", "INFO")

    try:
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )
        try:
            cur = conn.cursor()
            query = sql.SQL('UPDATE {}.{} SET perf_level = %s WHERE user_id = %s AND month = %s').format(
                sql.Identifier(st.session_state.pg_schema),
                sql.Identifier(table_name)
            )
            add_log(f"📊 执行SQL: {query.as_string(conn)}", "INFO")
            add_log(f"📊 参数: perf_level={perf_level}, user_id={user_id}, month={month}", "INFO")

            cur.execute(query, (perf_level, user_id, month))
            affected = cur.rowcount
            conn.commit()
            cur.close()
            add_log(f"✅ 更新成功，影响行数: {affected}", "INFO")
            return True, affected
        except Exception as e:
            conn.rollback()
            add_log(f"❌ 更新失败: {e}", "ERROR")
            add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
            return False, str(e)
        finally:
            conn.close()
    except Exception as e:
        add_log(f"❌ 数据库连接失败: {e}", "ERROR")
        return False, str(e)


def hrm_login():
    """HRM系统登录 - 页面初始化时自动调用"""
    log_separator("HRM系统登录")
    add_log("🔐 开始HRM系统自动登录", "INFO")

    try:
        # 获取验证码
        check_key = str(int(time.time() * 1000))
        captcha_url = f"{HRM_API_CONFIG['captcha_url']}{check_key}?_t={int(time.time())}"
        log_request(captcha_url, "GET", data=None)

        response = requests.get(captcha_url, timeout=10)
        log_response(response)
        result = response.json()

        if result.get('code') == 0 and result.get('success'):
            img_data = result.get('result', '')
            if img_data.startswith('data:image/jpg;base64,'):
                img_base64 = img_data.split(',')[1]
                img_bytes = base64.b64decode(img_base64)
                img = Image.open(BytesIO(img_bytes))
                ocr = ddddocr.DdddOcr(show_ad=False)
                captcha_text = ocr.classification(img)
                add_log(f"🔢 验证码识别结果: {captcha_text}", "INFO")

                # 登录
                login_data = {
                    "username": HRM_API_CONFIG['username'],
                    "password": HRM_API_CONFIG['password'],
                    "captcha": captcha_text,
                    "checkKey": check_key
                }
                log_request(HRM_API_CONFIG['login_url'], "POST", data=login_data)

                login_response = requests.post(HRM_API_CONFIG['login_url'], json=login_data, timeout=10)
                log_response(login_response)
                login_result = login_response.json()

                if login_response.status_code == 200 and login_result.get('success', False):
                    token = login_result.get('result', {}).get('token')
                    if token:
                        st.session_state.hrm_jwt_token = token
                        st.session_state.hrm_login_success = True
                        st.session_state.hrm_user_info = login_result.get('result', {}).get('userInfo', {})
                        add_log(f"✅ HRM登录成功: {st.session_state.hrm_user_info.get('realname', '未知')}", "INFO")
                        add_log(f"✅ Token: {token[:20]}...", "INFO")
                        log_separator("登录完成")
                        return True, "登录成功"
                add_log(f"❌ 登录失败: {login_result.get('message', '未知错误')}", "ERROR")
                return False, f"登录失败: {login_result.get('message', '未知错误')}"
            add_log("❌ 验证码格式异常", "ERROR")
            return False, "验证码格式异常"
        add_log(f"❌ 获取验证码失败: {result.get('message', '未知错误')}", "ERROR")
        return False, f"获取验证码失败: {result.get('message', '未知错误')}"
    except Exception as e:
        add_log(f"❌ HRM登录异常: {e}", "ERROR")
        add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
        return False, f"登录异常: {e}"


def hrm_query_performance(key_point, start_month, end_month):
    """
    查询HRM绩效数据 - 使用全局token
    解析并打印judgmentResult字段
    """
    log_separator(f"HRM绩效查询")
    add_log(f"🔍 开始查询绩效数据: 工号={key_point}, 开始月份={start_month}, 结束月份={end_month}", "INFO")

    try:
        # 检查登录状态
        if not st.session_state.hrm_login_success or not st.session_state.hrm_jwt_token:
            add_log("❌ HRM未登录，无法查询", "ERROR")
            return None, "HRM未登录"

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
            "x-access-token": st.session_state.hrm_jwt_token,
            "Content-Type": "application/json"
        }

        log_request(HRM_API_CONFIG['performance_url'], "POST", headers=headers, data=request_data)

        response = requests.post(
            HRM_API_CONFIG['performance_url'],
            json=request_data,
            headers=headers,
            timeout=10
        )
        log_response(response)
        result = response.json()

        if result.get('code') == 200 and result.get('success', False):
            add_log("✅ 绩效查询成功", "INFO")

            # 解析并打印详细结果
            result_data = result.get('result', {})
            if isinstance(result_data, dict):
                user_list = result_data.get('userList', [])
                add_log(f"📊 查询到 {len(user_list)} 条用户数据", "INFO")

                for idx, user in enumerate(user_list, 1):
                    add_log(f"\n--- 用户 {idx} ---", "INFO")
                    realname = user.get('realname', 'N/A')
                    position = user.get('position', 'N/A')
                    add_log(f"  👤 姓名: {realname}", "INFO")
                    add_log(f"  💼 岗位: {position}", "INFO")

                    # 获取并判断 judgmentResult
                    judgment_result = user.get('judgmentResult', 'N/A')
                    add_log(f"  📋 judgmentResult: {judgment_result}", "INFO")

                    # 判断是否为"节点职级上调"
                    is_promotion = (judgment_result == '节点职级上调')
                    if is_promotion:
                        add_log(f"  ✅ judgmentResult 是 '节点职级上调'", "INFO")
                    else:
                        add_log(f"  ❌ judgmentResult 不是 '节点职级上调' (当前值: {judgment_result})", "INFO")

                    # 绩效明细
                    deduction_list = user.get('deductionEntityList', [])
                    add_log(f"  📊 绩效明细 ({len(deduction_list)} 条):", "INFO")
                    for deduction in deduction_list:
                        ded_month = deduction.get('month', 'N/A')
                        perf_level = deduction.get('perfLevel', 'N/A')
                        add_log(f"    {ded_month}: {perf_level}", "INFO")

                    add_log(f"  📋 判定结果: {judgment_result}", "INFO")
                    add_log(f"  📋 是否职级上调: {'是 ✅' if is_promotion else '否 ❌'}", "INFO")

            log_separator("查询完成")
            return result_data, None
        else:
            error_msg = result.get('message', '未知错误')
            add_log(f"❌ 绩效查询失败: {error_msg}", "ERROR")
            log_separator("查询失败")
            return None, error_msg

    except Exception as e:
        add_log(f"❌ 查询异常: {e}", "ERROR")
        add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
        return None, f"查询异常: {e}"


def update_perf_by_user_name(user_name, month, perf_level):
    """
    通过工号更新绩效数据
    入参: user_name - 工号, month - 月份, perf_level - 绩效等级
    返回: (success, message)
    """
    log_separator(f"更新绩效数据")
    add_log(f"📝 工号={user_name}, 月份={month}, 绩效={perf_level}", "INFO")

    try:
        conn = psycopg2.connect(
            host=st.session_state.pg_host,
            port=st.session_state.pg_port,
            database=st.session_state.pg_db,
            user=st.session_state.pg_user,
            password=st.session_state.pg_pwd,
            connect_timeout=5
        )

        try:
            cur = conn.cursor()

            # 首先检查 t_perf_deduction 表是否存在
            exists, actual_table = check_table_exists(conn, 't_perf_deduction')
            if not exists:
                add_log("❌ 表 t_perf_deduction 不存在", "ERROR")
                return False, "表 t_perf_deduction 不存在"

            # 检查 sys_user 表是否存在
            exists, _ = check_table_exists(conn, 'sys_user')
            if not exists:
                add_log("❌ 表 sys_user 不存在", "ERROR")
                return False, "表 sys_user 不存在"

            # 先查询要更新的记录ID
            select_query = f'''
                SELECT id FROM "{st.session_state.pg_schema}"."t_perf_deduction" 
                WHERE user_id = (
                    SELECT user_id FROM "{st.session_state.pg_schema}"."sys_user" 
                    WHERE user_name = %s
                ) 
                AND month = %s
            '''
            add_log(f"📊 查询记录SQL: {select_query}", "INFO")
            add_log(f"📊 参数: user_name={user_name}, month={month}", "INFO")

            cur.execute(select_query, (user_name, month))
            result = cur.fetchone()

            if not result:
                add_log(f"❌ 未找到匹配记录: 工号={user_name}, 月份={month}", "WARNING")
                return False, "未找到匹配的记录，请检查工号和月份是否正确"

            record_id = result[0]
            add_log(f"✅ 找到记录ID: {record_id}", "INFO")

            # 构建完整的更新SQL
            update_query = f'''
                UPDATE "{st.session_state.pg_schema}"."t_perf_deduction" 
                SET perf_level = %s 
                WHERE id = %s
            '''
            add_log(f"📊 更新SQL: {update_query}", "INFO")
            add_log(f"📊 参数: perf_level={perf_level}, id={record_id}", "INFO")

            cur.execute(update_query, (perf_level, record_id))
            affected = cur.rowcount
            conn.commit()

            if affected > 0:
                add_log(f"✅ 数据库更新成功: 工号={user_name}, 月份={month}, 绩效={perf_level}, 影响行数: {affected}",
                        "INFO")
                log_separator("更新完成")
                return True, f"成功更新记录ID {record_id}"
            else:
                add_log(f"❌ 数据库更新失败: 工号={user_name}, 月份={month}", "ERROR")
                return False, "更新失败"

        except Exception as e:
            conn.rollback()
            error_msg = f"更新失败: {str(e)}"
            add_log(f"❌ {error_msg}", "ERROR")
            add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
            return False, error_msg
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        error_msg = f"数据库连接失败: {str(e)}"
        add_log(f"❌ {error_msg}", "ERROR")
        add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
        return False, error_msg


def batch_update_performance(user_name):
    """
    批量更新5、6、7月绩效数据
    按照指定的组合轮流调用
    每次更新成功后等待1s，然后调用HRM查询接口验证
    """
    log_separator(f"批量更新绩效数据")
    add_log(f"📝 工号: {user_name}", "INFO")
    add_log(f"📝 月份: 2026-05, 2026-06, 2026-07", "INFO")

    # 定义月份和绩效组合
    months = ['2026-05', '2026-06', '2026-07']

    # 绩效组合列表
    perf_combinations = [
        ('S', 'S', 'S'),
        ('S', 'S', 'A'),
        ('S', 'A', 'S'),
        ('A', 'S', 'S')
    ]

    add_log(f"📋 绩效组合列表: {perf_combinations}", "INFO")

    results = []
    total_success = 0
    total_failed = 0

    # 检查HRM登录状态
    if not st.session_state.hrm_login_success:
        add_log("⚠️ HRM未登录，跳过查询验证", "WARNING")
    else:
        add_log(f"✅ HRM已登录，将进行查询验证", "INFO")

    # 轮流执行每种组合
    for idx, (perf_5, perf_6, perf_7) in enumerate(perf_combinations, 1):
        log_separator(f"第 {idx} 组组合", "-")
        add_log(f"📋 组合 {idx}: 5月={perf_5}, 6月={perf_6}, 7月={perf_7}", "INFO")

        # 构建该组的绩效数据
        month_perf_pairs = [
            ('2026-05', perf_5),
            ('2026-06', perf_6),
            ('2026-07', perf_7)
        ]

        group_result = {
            'combination': f"5月:{perf_5}, 6月:{perf_6}, 7月:{perf_7}",
            'details': [],
            'success_count': 0,
            'failed_count': 0,
            'hrm_queries': []
        }

        # 执行该组的3个月份更新
        for month, perf_level in month_perf_pairs:
            add_log(f"\n📌 执行更新: 月份={month}, 绩效={perf_level}", "INFO")

            # 更新数据库
            success, message = update_perf_by_user_name(user_name, month, perf_level)

            detail = {
                'month': month,
                'perf_level': perf_level,
                'success': success,
                'message': message
            }
            group_result['details'].append(detail)

            if success:
                group_result['success_count'] += 1
                total_success += 1

                # 更新成功后，等待1秒
                add_log(f"⏳ 等待1秒后查询HRM接口验证...", "INFO")
                time.sleep(1)

                # 查询HRM绩效数据验证
                if st.session_state.hrm_login_success:
                    add_log(f"🔍 开始查询HRM验证: 工号={user_name}, 目标月份={month}", "INFO")

                    # 计算查询月份范围（目标月份前后3个月）
                    target_date = datetime.strptime(month, "%Y-%m")
                    start_date = target_date - timedelta(days=90)
                    end_date = target_date + timedelta(days=90)
                    start_month = start_date.strftime("%Y-%m")
                    end_month = end_date.strftime("%Y-%m")

                    result_data, error = hrm_query_performance(user_name, start_month, end_month)

                    hrm_query_record = {
                        'month': month,
                        'perf_level': perf_level,
                        'success': result_data is not None,
                        'data': result_data,
                        'error': error
                    }
                    group_result['hrm_queries'].append(hrm_query_record)

                    if result_data:
                        add_log(f"✅ HRM查询验证成功: 月份={month}", "INFO")
                        # 提取目标月份的绩效和judgmentResult
                        if isinstance(result_data, dict):
                            user_list = result_data.get('userList', [])
                            for user in user_list:
                                # 获取judgmentResult
                                judgment_result = user.get('judgmentResult', 'N/A')
                                is_promotion = (judgment_result == '节点职级上调')
                                add_log(f"  📌 judgmentResult: {judgment_result}", "INFO")
                                add_log(f"  📌 是否节点职级上调: {'是 ✅' if is_promotion else '否 ❌'}", "INFO")

                                # 获取绩效明细
                                deduction_list = user.get('deductionEntityList', [])
                                for deduction in deduction_list:
                                    ded_month = deduction.get('month', '')
                                    if ded_month == month:
                                        perf_level_result = deduction.get('perfLevel', 'N/A')
                                        add_log(f"  ✅ 目标月份 {month} 绩效值: {perf_level_result}", "INFO")
                                        add_log(
                                            f"  ✅ 期望值: {perf_level}, 实际值: {perf_level_result}, 匹配: {'✅' if perf_level_result == perf_level else '❌'}",
                                            "INFO")
                    else:
                        add_log(f"❌ HRM查询验证失败: {error}", "ERROR")
                else:
                    add_log(f"⚠️ HRM未登录，跳过查询验证", "WARNING")

            else:
                group_result['failed_count'] += 1
                total_failed += 1
                add_log(f"❌ 更新失败，跳过HRM查询", "ERROR")

            # 添加短暂延迟，避免数据库压力
            time.sleep(0.3)

        results.append(group_result)

        # 打印该组结果
        add_log(f"\n📊 第 {idx} 组完成", "INFO")
        add_log(f"  ✅ 数据库更新: 成功={group_result['success_count']}, 失败={group_result['failed_count']}", "INFO")
        for detail in group_result['details']:
            status = "✅ 成功" if detail['success'] else "❌ 失败"
            add_log(f"    {detail['month']} -> {detail['perf_level']}: {status} - {detail['message']}", "INFO")

        # 打印HRM查询结果
        if group_result.get('hrm_queries'):
            add_log(f"  🔍 HRM查询验证: {len(group_result['hrm_queries'])} 次", "INFO")
            for hrm_query in group_result['hrm_queries']:
                status = "✅ 成功" if hrm_query['success'] else "❌ 失败"
                add_log(f"    {hrm_query['month']}: {status} {hrm_query.get('error', '')}", "INFO")

    # 打印汇总结果
    log_separator("批量更新汇总结果")
    add_log(f"📊 工号: {user_name}", "INFO")
    add_log(f"📊 总成功: {total_success}", "INFO")
    add_log(f"📊 总失败: {total_failed}", "INFO")
    add_log(f"📊 总记录数: {total_success + total_failed}", "INFO")

    # 详细结果
    add_log("\n📋 详细结果:", "INFO")
    for idx, group in enumerate(results, 1):
        add_log(f"  组合 {idx}: {group['combination']}", "INFO")
        add_log(f"    数据库更新: 成功={group['success_count']}, 失败={group['failed_count']}", "INFO")
        for detail in group['details']:
            status = "✅" if detail['success'] else "❌"
            add_log(f"      {detail['month']} -> {detail['perf_level']}: {status} {detail['message']}", "INFO")
        if group.get('hrm_queries'):
            add_log(f"    HRM查询验证:", "INFO")
            for hrm_query in group['hrm_queries']:
                status = "✅" if hrm_query['success'] else "❌"
                add_log(f"      {hrm_query['month']}: {status}", "INFO")

    log_separator("批量更新完成")

    return {
        'total_success': total_success,
        'total_failed': total_failed,
        'total_records': total_success + total_failed,
        'results': results
    }


def get_month_options():
    """生成月份选项列表（最近24个月）"""
    months = []
    current = datetime.now()
    for i in range(24):
        date = current - timedelta(days=i * 30)
        month_str = date.strftime("%Y-%m")
        if month_str not in months:
            months.append(month_str)
    return sorted(months)


def initialize_connection_and_data():
    """初始化连接并加载数据"""
    if st.session_state.data_loaded:
        return

    log_separator("系统初始化")
    add_log("🚀 开始初始化系统...", "INFO")

    with st.spinner("正在连接数据库，请稍候..."):
        conn, status, error = get_connection()
        if not status:
            st.session_state.connection_status = False
            st.session_state.connection_error = error
            st.error("❌ 数据库连接失败，请检查网络或联系管理员")
            add_log("❌ 数据库初始化失败", "ERROR")
            return

        st.session_state.connection_status = True
        st.session_state.connection_error = None
        st.session_state.table_list = get_tables_in_schema()

        if st.session_state.table_list:
            # 匹配选中表
            for table in st.session_state.table_list:
                if table.lower() == st.session_state.selected_table.lower():
                    st.session_state.selected_table = table
                    break
            else:
                st.session_state.selected_table = st.session_state.table_list[0]
            add_log(f"📋 当前选中表: {st.session_state.selected_table}", "INFO")

        conn.close()
        st.session_state.data_loaded = True
        add_log("✅ 数据库初始化完成", "INFO")

    # 初始化HRM登录
    if not st.session_state.hrm_initialized:
        with st.spinner("正在初始化HRM登录，请稍候..."):
            add_log("🔐 开始初始化HRM系统登录", "INFO")
            success, message = hrm_login()
            st.session_state.hrm_initialized = True
            if success:
                st.success("✅ HRM系统登录成功")
                add_log("✅ HRM系统登录成功", "INFO")
            else:
                st.warning(f"⚠️ HRM系统登录失败: {message}，批量校验将跳过查询验证")
                add_log(f"⚠️ HRM系统登录失败: {message}", "WARNING")

    log_separator("初始化完成")


def main():
    init_session()
    initialize_connection_and_data()

    st.title("📊 HRM修改绩效数据")

    # 连接状态
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.connection_status:
            st.success("✅ 数据库连接正常")
        else:
            st.error("❌ 数据库连接失败，请刷新页面重试或联系管理员")

    with col2:
        if st.session_state.hrm_login_success:
            user_info = st.session_state.hrm_user_info
            st.success(f"✅ HRM已登录: {user_info.get('realname', '未知')}")
        else:
            st.warning("⚠️ HRM未登录")

    # 表选择
    with st.container():
        if st.session_state.connection_status and st.session_state.table_list:
            current_idx = 0
            for i, table in enumerate(st.session_state.table_list):
                if table.lower() == st.session_state.selected_table.lower():
                    current_idx = i
                    st.session_state.selected_table = table
                    break

            selected = st.selectbox(
                "📋 选择数据表",
                options=st.session_state.table_list,
                index=current_idx,
                key="table_selector"
            )

            if selected != st.session_state.selected_table:
                add_log(f"📋 切换表: {st.session_state.selected_table} -> {selected}", "INFO")
                st.session_state.selected_table = selected
                st.cache_data.clear()
                st.session_state.data_loaded = False
                st.session_state.log_messages = []
                st.session_state.last_edited_data = None
                st.session_state.save_status = None
                st.session_state.search_name = ""
                st.session_state.search_post = ""
                st.rerun()
        else:
            st.selectbox("📋 选择数据表", options=["加载中..."], disabled=True, key="table_selector_disabled")

    # 搜索条件
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            search_name = st.text_input("👤 姓名", value=st.session_state.search_name,
                                        placeholder="请输入姓名...", key="search_name_input")
            if search_name != st.session_state.search_name:
                add_log(f"🔍 搜索姓名: {search_name}", "INFO")
                st.session_state.search_name = search_name
                st.session_state.last_edited_data = None
                st.rerun()
        with col2:
            search_post = st.text_input("💼 岗位", value=st.session_state.search_post,
                                        placeholder="请输入岗位名称...", key="search_post_input")
            if search_post != st.session_state.search_post:
                add_log(f"🔍 搜索岗位: {search_post}", "INFO")
                st.session_state.search_post = search_post
                st.session_state.last_edited_data = None
                st.rerun()

    # 保存状态
    if st.session_state.save_status:
        if "成功" in st.session_state.save_status:
            st.success(f"✅ {st.session_state.save_status}")
        elif "失败" in st.session_state.save_status:
            st.error(f"❌ {st.session_state.save_status}")
        else:
            st.info(f"ℹ️ {st.session_state.save_status}")

    # 主数据处理
    table_name = st.session_state.selected_table
    if not (table_name and st.session_state.connection_status):
        if not st.session_state.connection_status:
            st.error("❌ 数据库连接失败，请刷新页面重试或联系管理员")
        return

    conn, status, error = get_connection()
    if not status:
        st.error("❌ 数据库连接失败，请刷新页面重试")
        return

    try:
        exists, actual_name = check_table_exists(conn, table_name)
        if not exists:
            st.warning(f"表 '{table_name}' 不存在")
            return

        if actual_name and actual_name != table_name:
            st.session_state.selected_table = actual_name
            table_name = actual_name

        # 查询数据
        add_log(f"📊 查询表数据: {table_name}", "INFO")
        query = f'SELECT user_id, perf_level, month FROM "{st.session_state.pg_schema}"."{table_name}" ORDER BY user_id, month'
        df = execute_query(query)

        if df is None or df.empty:
            st.warning("表为空" if df is not None else "数据加载失败")
            return

        # 获取用户信息
        user_ids = df['user_id'].dropna().unique().tolist()
        user_info = {}
        if user_ids:
            with st.spinner("正在加载用户信息..."):
                user_info = get_user_info(user_ids)

        # 添加姓名和岗位
        df['user_name'] = df['user_id'].map(lambda x: user_info.get(x, {}).get('name', ''))
        df['user_post'] = df['user_id'].map(lambda x: user_info.get(x, {}).get('post', ''))

        # 搜索过滤
        filtered_df = df.copy()
        if st.session_state.search_name:
            filtered_df = filtered_df[
                filtered_df['user_name'].str.contains(st.session_state.search_name, case=False, na=False)]
        if st.session_state.search_post:
            filtered_df = filtered_df[
                filtered_df['user_post'].str.contains(st.session_state.search_post, case=False, na=False)]

        if filtered_df.empty:
            st.warning("没有找到匹配的记录")
            return

        # 透视数据
        pivot_df = filtered_df.pivot_table(
            index=['user_id', 'user_name', 'user_post'],
            columns='month',
            values='perf_level',
            aggfunc='first'
        ).reset_index()
        pivot_df.columns.name = None

        month_columns = [col for col in pivot_df.columns if col not in ['user_id', 'user_name', 'user_post']]
        month_columns.sort()

        st.info("💡 直接点击单元格修改绩效等级，修改后自动保存到数据库")

        # 列配置
        column_config = {
            "user_id": st.column_config.Column("user_id", width="small", disabled=True),
            "user_name": st.column_config.Column("姓名", width="small", disabled=True),
            "user_post": st.column_config.Column("岗位", width="small", disabled=True),
            **{month: st.column_config.Column(f"{month}月", width="small", disabled=False) for month in month_columns}
        }

        # 显示可编辑表格
        display_df = pivot_df.copy()
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            height=500,
            column_config=column_config,
            hide_index=True,
            key="perf_editor",
            disabled=False,
            num_rows="fixed",
            column_order=["user_name", "user_post"] + month_columns
        )

        # 检测变化并自动保存
        if edited_df is not None:
            if st.session_state.last_edited_data is None:
                st.session_state.last_edited_data = edited_df.copy()
            elif not edited_df.equals(st.session_state.last_edited_data):
                changes = []
                for idx in edited_df.index:
                    user_id = display_df.loc[idx, 'user_id'] if idx < len(display_df) else None
                    if user_id is None:
                        continue
                    for month in month_columns:
                        if month in display_df.columns and month in edited_df.columns:
                            old_val = display_df.loc[idx, month] if idx < len(display_df) else None
                            new_val = edited_df.loc[idx, month] if idx < len(edited_df) else None
                            if str(old_val) if pd.notna(old_val) else "None" != str(new_val) if pd.notna(
                                    new_val) else "None":
                                changes.append({'user_id': user_id, 'month': month,
                                                'perf_level': new_val if pd.notna(new_val) else None})

                if changes:
                    add_log(f"📝 检测到 {len(changes)} 处变化，开始保存...", "INFO")
                    for change in changes:
                        add_log(
                            f"  变化: user_id={change['user_id']}, month={change['month']}, perf_level={change['perf_level']}",
                            "INFO")

                    success_count = 0
                    for change in changes:
                        if change['perf_level'] is not None:
                            success, _ = update_single_record(change['user_id'], change['month'],
                                                              change['perf_level'], table_name)
                            if success:
                                success_count += 1

                    if success_count > 0:
                        st.session_state.save_status = f"成功更新 {success_count} 条记录"
                        st.session_state.last_edited_data = edited_df.copy()
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.session_state.save_status = "更新失败，请查看日志"
                else:
                    st.session_state.last_edited_data = edited_df.copy()

        # ============================================================
        # 单个更新接口区域
        # ============================================================
        st.markdown("---")
        st.subheader("🔧 按工号更新绩效接口")
        st.caption("通过工号、月份和绩效等级更新用户绩效数据")

        # 生成月份选项列表
        month_options = get_month_options()
        # 设置默认月份为当前月份
        default_month = datetime.now().strftime("%Y-%m")
        if default_month not in month_options:
            default_month = month_options[-1] if month_options else ""

        # 三个输入框
        col1, col2, col3 = st.columns(3)
        with col1:
            api_user_name = st.text_input(
                "🆔 工号",
                value=st.session_state.api_user_name,
                placeholder="请输入工号（如：102418）",
                key="api_user_name_input",
                help="请输入sys_user表中的user_name字段值（工号）"
            )
            st.session_state.api_user_name = api_user_name

        with col2:
            # 月份下拉选择
            api_month = st.selectbox(
                "📅 月份",
                options=month_options,
                index=month_options.index(default_month) if default_month in month_options else 0,
                key="api_month_select",
                help="选择要更新的月份"
            )
            st.session_state.api_month = api_month

        with col3:
            # 绩效等级下拉选择 - 只保留 S,A,B,C,D
            perf_options = ['S', 'A', 'B', 'C', 'D']
            current_perf = st.session_state.api_perf_level
            if current_perf not in perf_options:
                current_perf = 'S'

            api_perf_level = st.selectbox(
                "⭐ 绩效等级",
                options=perf_options,
                index=perf_options.index(current_perf),
                key="api_perf_level_select",
                help="选择要设置的绩效等级（S/A/B/C/D）"
            )
            st.session_state.api_perf_level = api_perf_level

        # 按钮和结果显示
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            api_button = st.button("🚀 执行更新", type="primary", use_container_width=True)

        # 显示API调用结果
        if st.session_state.api_result:
            if st.session_state.api_result.get('success', False):
                st.success(f"✅ {st.session_state.api_result.get('message', '更新成功')}")
            else:
                st.error(f"❌ {st.session_state.api_result.get('message', '更新失败')}")

        # 处理API调用
        if api_button:
            if not api_user_name:
                st.session_state.api_result = {'success': False, 'message': '请输入工号'}
            elif not api_month:
                st.session_state.api_result = {'success': False, 'message': '请选择月份'}
            elif not api_perf_level:
                st.session_state.api_result = {'success': False, 'message': '请选择绩效等级'}
            else:
                add_log(f"🚀 用户点击执行更新: 工号={api_user_name}, 月份={api_month}, 绩效={api_perf_level}", "INFO")
                with st.spinner("正在更新绩效数据..."):
                    success, message = update_perf_by_user_name(api_user_name, api_month, api_perf_level)
                    st.session_state.api_result = {'success': success, 'message': message}
                    if success:
                        # 更新成功后清除缓存并刷新数据
                        st.cache_data.clear()
                        st.session_state.data_loaded = False
                        st.session_state.last_edited_data = None
                        time.sleep(0.5)
                        st.rerun()

        # ============================================================
        # 批量校验接口区域
        # ============================================================
        st.markdown("---")
        st.subheader("📋 批量校验接口 - 5/6/7月绩效组合测试")
        st.caption("对指定工号，依次执行4种绩效组合更新5/6/7月数据，每次更新成功后自动查询HRM接口验证")

        # 显示组合说明
        with st.expander("📖 查看绩效组合说明"):
            st.markdown("""
            **4种绩效组合：**
            1. 5月S, 6月S, 7月S
            2. 5月S, 6月S, 7月A
            3. 5月S, 6月A, 7月S
            4. 5月A, 6月S, 7月S

            **执行流程：**
            - 轮流执行上述4种组合
            - 每种组合依次更新5月、6月、7月绩效
            - 每次更新成功后等待1秒
            - 自动调用HRM查询接口验证绩效数据
            - 完整日志记录，包括judgmentResult字段判断
            """)

        # 批量更新输入
        col1, col2 = st.columns([2, 1])
        with col1:
            batch_user_name = st.text_input(
                "🆔 工号",
                value=st.session_state.batch_user_name,
                placeholder="请输入要批量更新的工号",
                key="batch_user_name_input",
                help="输入工号，将对5/6/7月执行4种组合更新"
            )
            st.session_state.batch_user_name = batch_user_name

        with col2:
            batch_button = st.button("🔄 执行批量校验", type="primary", use_container_width=True)

        # 显示批量结果
        if st.session_state.batch_result:
            result = st.session_state.batch_result
            st.markdown("### 📊 批量执行结果")

            # 汇总信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总成功", result.get('total_success', 0))
            with col2:
                st.metric("总失败", result.get('total_failed', 0))
            with col3:
                st.metric("总记录", result.get('total_records', 0))

            # 详细结果
            with st.expander("📋 查看详细结果"):
                for idx, group in enumerate(result.get('results', []), 1):
                    st.markdown(f"**组合 {idx}: {group['combination']}**")
                    st.markdown(f"数据库更新: 成功={group['success_count']}, 失败={group['failed_count']}")

                    for detail in group['details']:
                        status_icon = "🟢" if detail['success'] else "🔴"
                        st.write(f"  {status_icon} {detail['month']} → {detail['perf_level']}: {detail['message']}")

                    # 显示HRM查询结果
                    if group.get('hrm_queries'):
                        st.markdown("**HRM查询验证:**")
                        for hrm_query in group['hrm_queries']:
                            status_icon = "🟢" if hrm_query['success'] else "🔴"
                            st.write(
                                f"  {status_icon} {hrm_query['month']}: {'成功' if hrm_query['success'] else hrm_query.get('error', '失败')}")
                    st.markdown("---")

        # 处理批量调用
        if batch_button:
            if not batch_user_name:
                st.warning("请输入工号")
            else:
                add_log(f"🚀 用户点击执行批量校验: 工号={batch_user_name}", "INFO")
                with st.spinner("正在执行批量校验，请等待..."):
                    result = batch_update_performance(batch_user_name)
                    st.session_state.batch_result = result
                    # 更新成功后清除缓存并刷新数据
                    st.cache_data.clear()
                    st.session_state.data_loaded = False
                    st.session_state.last_edited_data = None
                    time.sleep(0.5)
                    st.rerun()
        # ============================================================

        # 日志
        with st.expander("📋 操作日志", expanded=True):
            if st.session_state.log_messages:
                # 显示最后150条日志
                st.code("\n".join(st.session_state.log_messages[-150:]), language="text")
                # 显示日志文件路径
                st.caption(f"📁 完整日志已保存至: {LOG_FILE}")
            else:
                st.info("暂无日志")

    except Exception as e:
        st.error(f"操作失败: {e}")
        add_log(f"❌ 操作失败: {e}", "ERROR")
        add_log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
        st.code(traceback.format_exc())
    finally:
        conn.close()


if __name__ == "__main__":
    # 在程序启动时记录启动日志（只写入文件，不重复显示）
    log_to_file_only("=" * 80, "INFO")
    log_to_file_only("🚀 系统启动", "INFO")
    log_to_file_only(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    log_to_file_only(f"📁 日志文件: {LOG_FILE}", "INFO")
    log_to_file_only("=" * 80, "INFO")
    main()