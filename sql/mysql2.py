import streamlit as st
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime, date
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="MySQL 数据库连接工具", page_icon="🐬", layout="wide")

# ============================================================
# 日志文件配置
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "mysql.log")


def setup_logger():
    logger = logging.getLogger('mysql_tool')
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        logger.handlers.clear()
    fh = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024,
                             backupCount=5, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S.%f'[:-3]))
    logger.addHandler(fh)
    return logger


file_logger = setup_logger()

# ============================================================
# 常量
# ============================================================
IP_PRESETS = ["47.116.211.247", "localhost", "127.0.0.1"]
DEFAULT_LIMIT = 1000
DEFAULT_HOST = "47.116.211.247"
DEFAULT_PORT = 3306
DEFAULT_DB = "hrm"
DEFAULT_USER = "root"
DEFAULT_PWD = "RHKJ@rh2025"

# 统一默认状态（只在这里维护一份）
DEFAULT_STATE = {
    # 连接配置
    "mysql_host": DEFAULT_HOST, "mysql_port": DEFAULT_PORT,
    "mysql_db": DEFAULT_DB, "mysql_user": DEFAULT_USER, "mysql_pwd": DEFAULT_PWD,
    # 连接状态
    "database_list": [], "databases_loaded": False, "connection_ok": False,
    "error_message": "", "show_error": False, "connect_attempted": False,
    "config_hash": "", "auto_connect_done": False,
    # 表相关
    "table_list": [], "tables_loaded": False, "mysql_table": "",
    "table_schema": None, "schema_loaded": False,
    "table_columns": [], "primary_key": None, "column_types": {},
    # 数据相关
    "table_data": None, "table_data_loaded": False, "table_total_count": None,
    "filter_conditions": {}, "selected_rows": [],
    # 缓存 key
    "schema_cache_key": "", "data_cache_key": "",
    # SQL 面板
    "sql_query": "SELECT * FROM information_schema.TABLES LIMIT 10;",
    "query_result": None, "query_success": False,
    "query_error": "", "query_rows": 0, "query_executed": False,
    # 日志
    "operation_logs": [], "log_counter": 0,
    # 弹窗
    "_dialog_delete_rows": None, "_show_delete_dialog": False,
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    .main > div { padding-top: 0rem !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { margin-top: 0 !important; }
    .main-header { font-size: 2rem; font-weight: 600; color: #0b1e33; margin-bottom: 0.5rem; margin-top: 0 !important; }
    .sql-panel-title { font-size: 1.1rem; font-weight: 600; color: #0b1e33; margin-bottom: 0.6rem; margin-top: 0 !important; }
    .stTextArea textarea {
        border-radius: 10px !important; font-family: 'Monaco', 'Menlo', monospace !important;
        font-size: 0.9rem !important; line-height: 1.6 !important;
        background: #0b1e33 !important; color: #e8edf4 !important; border: 1px solid #1f3a5f !important;
    }
    .stButton button { border-radius: 40px !important; font-weight: 500 !important; padding: 0.3rem 1.5rem !important; }

    div.st-key-btn_query button {
        background: #16a34a !important; border-color: #16a34a !important; color: #ffffff !important;
    }
    div.st-key-btn_query button:hover { background: #15803d !important; border-color: #15803d !important; }
    div.st-key-btn_query button:focus { box-shadow: 0 0 0 0.2rem rgba(22,163,74,0.35) !important; }

    div.st-key-btn_reset button {
        background: #2563eb !important; border-color: #2563eb !important; color: #ffffff !important;
    }
    div.st-key-btn_reset button:hover { background: #1d4ed8 !important; border-color: #1d4ed8 !important; }
    div.st-key-btn_reset button:focus { box-shadow: 0 0 0 0.2rem rgba(37,99,235,0.35) !important; }

    div.st-key-btn_delete_selected button {
        background: #dc2626 !important; border-color: #dc2626 !important; color: #ffffff !important;
    }
    div.st-key-btn_delete_selected button:hover { background: #b91c1c !important; border-color: #b91c1c !important; }
    div.st-key-btn_delete_selected button:focus { box-shadow: 0 0 0 0.2rem rgba(220,38,38,0.35) !important; }

    div.st-key-btn_delete_selected_disabled button {
        background: #f3a5a5 !important; border-color: #f3a5a5 !important;
        color: #ffffff !important; opacity: 0.65 !important;
    }

    .error-box {
        background: #fef3f2; border-left: 4px solid #d43f34; border-radius: 10px;
        padding: 0.8rem 1.2rem; color: #7a2e27; font-size: 0.9rem; margin: 0.3rem 0;
    }
    .stSelectbox [data-baseweb="select"] > div { border-radius: 40px !important; }
    .stSelectbox [data-baseweb="input"] input { border-radius: 40px !important; }
    .stColumns { gap: 0.5rem !important; }
    .stTextInput > div, .stNumberInput > div, .stSelectbox > div { margin-top: 0 !important; }
    .element-container { margin-top: 0 !important; margin-bottom: 0.2rem !important; }
    .stSpinner > div { display: none !important; }
    .stSpinner > div + div { display: none !important; }
    .sql-file-content {
        background: #0b1e33; color: #e8edf4; border-radius: 10px; padding: 1.2rem;
        font-family: 'Monaco', 'Menlo', monospace; font-size: 0.85rem; line-height: 1.8;
        overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
        max-height: 600px; overflow-y: auto; border: 1px solid #1f3a5f;
    }
    .log-container {
        background: #1a1a2e; border-radius: 10px; padding: 0.8rem 1rem;
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 0.78rem;
        line-height: 1.8; max-height: 450px; overflow-y: auto; border: 1px solid #2d2d44;
    }
    .log-entry {
        padding: 0.1rem 0; border-bottom: 1px solid rgba(255,255,255,0.03);
        display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.3rem 0.6rem;
    }
    .log-entry:last-child { border-bottom: none; }
    .log-time { color: #868e96; font-size: 0.7rem; min-width: 100px; flex-shrink: 0; }
    .log-badge {
        font-size: 0.65rem; font-weight: 600; padding: 0.05rem 0.5rem;
        border-radius: 20px; flex-shrink: 0; letter-spacing: 0.3px;
    }
    .log-badge-info { color: #64ffda; background: rgba(100, 255, 218, 0.12); border: 1px solid rgba(100, 255, 218, 0.2); }
    .log-badge-success { color: #69db7c; background: rgba(105, 219, 124, 0.12); border: 1px solid rgba(105, 219, 124, 0.2); }
    .log-badge-error { color: #ff6b6b; background: rgba(255, 107, 107, 0.12); border: 1px solid rgba(255, 107, 107, 0.2); }
    .log-badge-warning { color: #ffd93d; background: rgba(255, 217, 61, 0.12); border: 1px solid rgba(255, 217, 61, 0.2); }
    .log-badge-sql { color: #74b9ff; background: rgba(116, 185, 255, 0.12); border: 1px solid rgba(116, 185, 255, 0.2); }
    .log-badge-data { color: #fd79a8; background: rgba(253, 121, 168, 0.12); border: 1px solid rgba(253, 121, 168, 0.2); }
    .log-message { color: #e8edf4; flex: 1; min-width: 120px; }
    .log-detail { color: #6c7a8a; font-size: 0.7rem; word-break: break-all; }
    .log-sql {
        color: #74b9ff; font-size: 0.7rem; word-break: break-all;
        background: rgba(116, 185, 255, 0.05); padding: 0.1rem 0.4rem; border-radius: 4px;
    }
    .log-data {
        color: #fd79a8; font-size: 0.7rem; word-break: break-all;
        background: rgba(253, 121, 168, 0.05); padding: 0.1rem 0.4rem; border-radius: 4px;
    }
    .log-empty { color: #6c7a8a; text-align: center; padding: 1.5rem 0; font-size: 0.9rem; }
    .log-stats { display: flex; gap: 1.2rem; flex-wrap: wrap; padding: 0.3rem 0; margin-bottom: 0.5rem; }
    .log-stat-item { color: #a0aec0; font-size: 0.8rem; }
    .log-stat-item span { font-weight: 600; }
    .log-stat-info span { color: #64ffda; }
    .log-stat-success span { color: #69db7c; }
    .log-stat-error span { color: #ff6b6b; }
    .log-stat-warning span { color: #ffd93d; }
    .log-stat-sql span { color: #74b9ff; }
    .log-stat-data span { color: #fd79a8; }
    .delete-warning {
        background: #fff5f5; border: 1px solid #ffc9c9; border-radius: 10px;
        padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .delete-warning-title { color: #c92a2a; font-weight: 600; font-size: 1.05rem; margin-bottom: 0.6rem; }
    .delete-warning-text { color: #7a2e27; font-size: 0.88rem; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 统一状态重置
# ============================================================
def reset_connection_state():
    """连接信息变化后重置所有下游状态。"""
    for k in ("databases_loaded", "connection_ok", "show_error",
              "connect_attempted", "auto_connect_done", "tables_loaded",
              "schema_loaded", "table_data_loaded"):
        st.session_state[k] = False
    for k in ("database_list", "table_list", "selected_rows", "table_columns"):
        st.session_state[k] = []
    for k in ("table_schema", "table_data", "table_total_count", "primary_key"):
        st.session_state[k] = None
    st.session_state.column_types = {}
    st.session_state.filter_conditions = {}
    st.session_state.schema_cache_key = ""
    st.session_state.data_cache_key = ""
    st.session_state["_dialog_delete_rows"] = None
    st.session_state["_show_delete_dialog"] = False
    for key in ("_delete_result", "_delete_result_ok",
                "_update_result", "_update_result_ok"):
        st.session_state.pop(key, None)
    try:
        fetch_databases_cached.clear()
        fetch_tables_cached.clear()
        get_table_total_count_cached.clear()
    except Exception:
        pass


def reset_table_state():
    """切换表/库时重置表相关状态。"""
    for k in ("schema_loaded", "table_data_loaded"):
        st.session_state[k] = False
    for k in ("table_schema", "table_data", "table_total_count", "primary_key"):
        st.session_state[k] = None
    for k in ("selected_rows", "table_columns"):
        st.session_state[k] = []
    st.session_state.column_types = {}
    st.session_state.filter_conditions = {}
    st.session_state.schema_cache_key = ""
    st.session_state.data_cache_key = ""


def reset_query_state():
    """SQL 查询面板重置。"""
    st.session_state.query_result = None
    st.session_state.query_executed = False
    st.session_state.query_success = False
    st.session_state.query_error = ""


# ============================================================
# 日志函数
# ============================================================
def add_log(log_type, message, detail="", sql="", data=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    st.session_state.log_counter += 1
    data_str = ""
    if data:
        try:
            data_str = json.dumps(data, ensure_ascii=False, default=str) \
                if isinstance(data, dict) else str(data)
        except Exception:
            data_str = str(data)
    log_entry = {
        "id": st.session_state.log_counter, "time": timestamp, "type": log_type,
        "message": message, "detail": detail, "sql": sql, "data": data_str,
    }
    st.session_state.operation_logs.insert(0, log_entry)
    if len(st.session_state.operation_logs) > 1000:
        st.session_state.operation_logs = st.session_state.operation_logs[:1000]
    try:
        type_icons = {
            "info": "📘 INFO", "success": "✅ SUCCESS", "error": "❌ ERROR",
            "warning": "⚠️ WARNING", "sql": "💾 SQL", "data": "📊 DATA",
        }
        parts = [f"[{type_icons.get(log_type, log_type.upper())}]", message]
        if detail:
            parts.append(f"→ {detail}")
        if sql:
            parts.append(f"\n  SQL: {sql.strip()}")
        if data_str:
            parts.append(f"\n  DATA: {data_str[:500]}")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} | {' '.join(parts)}\n")
    except Exception as e:
        print(f"写入日志文件失败: {e}")
    return log_entry


def render_logs():
    if not st.session_state.operation_logs:
        return '<div class="log-empty">📭 暂无操作日志</div>'
    stats = {k: 0 for k in ("info", "success", "error", "warning", "sql", "data")}
    for log in st.session_state.operation_logs:
        if log['type'] in stats:
            stats[log['type']] += 1
    html = ['<div class="log-container">', '<div class="log-stats">']
    for t, label in [("info", "📘 INFO"), ("success", "✅ SUCCESS"), ("error", "❌ ERROR"),
                     ("warning", "⚠️ WARNING"), ("sql", "💾 SQL"), ("data", "📊 DATA")]:
        html.append(f'<span class="log-stat-item log-stat-{t}">{label}: <span>{stats[t]}</span></span>')
    html.append(f'<span class="log-stat-item" style="color:#868e96;">📋 TOTAL: '
                f'<span>{len(st.session_state.operation_logs)}</span></span>')
    html.append('</div>')
    for log in st.session_state.operation_logs[:100]:
        t = log['type']
        type_display = {"sql": "SQL", "data": "DATA"}.get(t, t.upper())
        html.append(f'<div class="log-entry"><span class="log-time">{log["time"]}</span>')
        html.append(f'<span class="log-badge log-badge-{t}">{type_display}</span>')
        html.append(f'<span class="log-message">{log["message"]}</span>')
        if log.get('sql'):
            sql_display = log['sql'][:300] + ('...' if len(log['sql']) > 300 else '')
            html.append(f'<span class="log-sql">SQL: {sql_display}</span>')
        if log.get('data'):
            data_display = log['data'][:300] + ('...' if len(log['data']) > 300 else '')
            html.append(f'<span class="log-data">DATA: {data_display}</span>')
        if log.get('detail'):
            html.append(f'<span class="log-detail">→ {log["detail"]}</span>')
        html.append('</div>')
    html.append('</div>')
    return ''.join(html)


# ============================================================
# 数据库连接辅助函数
# ============================================================
def get_config_hash(host, port, user, password):
    return f"{host}:{port}:{user}:{password}"


@st.cache_resource(show_spinner=False)
def get_engine(host, port, user, password, database=None):
    safe_pwd = quote_plus(password)
    db_part = f"/{database}" if database else ""
    url = f"mysql+pymysql://{user}:{safe_pwd}@{host}:{port}{db_part}"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600,
                         connect_args={'connect_timeout': 5})


def get_connection(host, port, user, password, database=None):
    return get_engine(host, port, user, password, database).connect()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_databases_cached(host, port, user, password):
    sql = """SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA
             WHERE SCHEMA_NAME NOT IN ('information_schema','mysql','performance_schema','sys')
             ORDER BY SCHEMA_NAME"""
    conn = get_connection(host, port, user, password)
    with conn:
        return [r[0] for r in conn.execute(text(sql)).fetchall()]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_tables_cached(host, port, user, password, database):
    conn = get_connection(host, port, user, password, database)
    with conn:
        return [r[0] for r in conn.execute(text(f"SHOW TABLES FROM `{database}`")).fetchall()]


@st.cache_data(ttl=30, show_spinner=False)
def get_table_total_count_cached(host, port, user, password, database, table_name, filters_tuple):
    filters = dict(filters_tuple) if filters_tuple else None
    conn = get_connection(host, port, user, password, database)
    with conn:
        where_clause = build_where_clause(filters)
        sql = f"SELECT COUNT(*) FROM `{database}`.`{table_name}` {where_clause}"
        return conn.execute(text(sql)).fetchone()[0]


def test_mysql_connection(host, port, user, password, database=None):
    try:
        add_log("info", "测试连接", f"host={host}, port={port}, database={database or '(default)'}")
        conn = get_connection(host, port, user, password, database)
        with conn:
            row = conn.execute(text("SELECT 1")).fetchone()
            if row and row[0] == 1:
                add_log("success", "连接成功", f"host={host}, database={database or '(default)'}")
                return True, None, conn
            return False, "Unexpected result from test query", None
    except (OperationalError, SQLAlchemyError) as e:
        add_log("error", "连接失败", str(e))
        return False, str(e), None
    except Exception as e:
        add_log("error", "连接异常", str(e))
        return False, str(e), None


def fetch_databases(host, port, user, password):
    try:
        add_log("info", "获取数据库列表")
        databases = fetch_databases_cached(host, port, user, password)
        add_log("success", f"获取到 {len(databases)} 个数据库")
        return True, databases, None
    except Exception as e:
        add_log("error", "获取数据库列表失败", str(e))
        return False, [], str(e)


def fetch_tables(host, port, user, password, database):
    try:
        add_log("info", "获取表列表", f"database={database}")
        tables = fetch_tables_cached(host, port, user, password, database)
        add_log("success", f"获取到 {len(tables)} 个表", f"database={database}")
        return True, tables, None
    except Exception as e:
        add_log("error", "获取表列表失败", f"database={database}, error={str(e)}")
        return False, [], str(e)


def fetch_table_schema(host, port, user, password, database, table_name):
    try:
        add_log("info", "获取表结构", f"database={database}, table={table_name}")
        sql = f"DESCRIBE `{database}`.`{table_name}`"
        add_log("sql", "执行查询", f"table={table_name}", sql)
        conn = get_connection(host, port, user, password, database)
        with conn:
            result = conn.execute(text(sql))
            columns = result.keys()
            df = pd.DataFrame(result.fetchall(), columns=columns)
        pk_cols = df[df['Key'] == 'PRI']['Field'].tolist()
        col_types = dict(zip(df['Field'], df['Type']))
        add_log("success", "获取表结构成功", f"table={table_name}, 字段数={len(df)}")
        return True, df, pk_cols, col_types
    except Exception as e:
        add_log("error", "获取表结构失败", f"table={table_name}, error={str(e)}")
        return False, None, [], {}


def build_where_clause(filters):
    if not filters:
        return ""
    conditions = []
    for col, value in filters.items():
        if value and str(value).strip():
            if isinstance(value, (int, float)):
                conditions.append(f"`{col}` = {value}")
            else:
                conditions.append(f"`{col}` = '{value}'")
    return "WHERE " + " AND ".join(conditions) if conditions else ""


def fetch_table_data_with_filters(host, port, user, password, database, table_name,
                                  filters=None, limit=DEFAULT_LIMIT):
    try:
        add_log("info", "查询表数据", f"database={database}, table={table_name}, limit={limit}")
        conn = get_connection(host, port, user, password, database)
        with conn:
            where_clause = build_where_clause(filters)
            if where_clause:
                add_log("info", "应用筛选条件", where_clause)
            sql = f"SELECT * FROM `{database}`.`{table_name}` {where_clause} LIMIT {limit}"
            add_log("sql", "执行查询", f"table={table_name}", sql)
            result = conn.execute(text(sql))
            columns = result.keys()
            df = pd.DataFrame(result.fetchall(), columns=columns)
        add_log("success", "查询数据成功", f"table={table_name}, 行数={len(df)}")
        return True, df, None
    except Exception as e:
        add_log("error", "查询数据失败", f"table={table_name}, error={str(e)}")
        return False, None, str(e)


def update_table_data(host, port, user, password, database, table_name,
                      primary_key_col, primary_key_value, update_data):
    try:
        set_clause = ", ".join([f"`{col}` = :{col}" for col in update_data.keys()])
        sql = (f"UPDATE `{database}`.`{table_name}` SET {set_clause} "
               f"WHERE `{primary_key_col}` = :pk_value")
        add_log("info", "执行表数据更新", f"table={table_name}")
        add_log("sql", "执行UPDATE语句", f"table={table_name}", sql)
        conn = get_connection(host, port, user, password, database)
        with conn:
            params = {**update_data, "pk_value": primary_key_value}
            result = conn.execute(text(sql), params)
            conn.commit()
            add_log("success", "更新数据成功",
                    f"table={table_name}, 影响行数={result.rowcount}")
        try:
            get_table_total_count_cached.clear()
        except Exception:
            pass
        return True, result.rowcount
    except Exception as e:
        add_log("error", "更新数据失败", f"table={table_name}, error={str(e)}")
        return False, str(e)


def delete_table_rows(host, port, user, password, database, table_name,
                      primary_key_col, primary_key_values):
    if not primary_key_values:
        return False, 0, "未提供要删除的主键值"
    try:
        placeholders = ", ".join([f":pk_{i}" for i in range(len(primary_key_values))])
        sql = (f"DELETE FROM `{database}`.`{table_name}` "
               f"WHERE `{primary_key_col}` IN ({placeholders})")
        add_log("info", "执行删除操作", f"table={table_name}, 待删除行数={len(primary_key_values)}")
        add_log("sql", "执行DELETE语句", f"table={table_name}", sql)
        conn = get_connection(host, port, user, password, database)
        with conn:
            params = {f"pk_{i}": v for i, v in enumerate(primary_key_values)}
            result = conn.execute(text(sql), params)
            conn.commit()
            deleted = result.rowcount
            add_log("success", "删除数据成功", f"table={table_name}, 实际删除行数={deleted}")
        try:
            get_table_total_count_cached.clear()
        except Exception:
            pass
        return True, deleted, None
    except Exception as e:
        add_log("error", "删除数据失败", f"table={table_name}, error={str(e)}")
        return False, 0, str(e)


def detect_column_type(mysql_type):
    t = mysql_type.lower()
    if any(x in t for x in ('int', 'decimal', 'float', 'double')):
        return st.column_config.NumberColumn
    if 'date' in t and 'datetime' not in t:
        return st.column_config.DateColumn
    if 'datetime' in t or 'timestamp' in t:
        return st.column_config.DatetimeColumn
    if 'time' in t:
        return st.column_config.TimeColumn
    if 'bool' in t or 'tinyint(1)' in t:
        return st.column_config.CheckboxColumn
    return st.column_config.TextColumn


def auto_connect_and_load(host, port, user, password):
    success, error_msg, _ = test_mysql_connection(host, port, user, password)
    if success:
        st.session_state.connection_ok = True
        st.session_state.show_error = False
        st.session_state.error_message = ""
        st.session_state.connect_attempted = True
        load_success, databases, error = fetch_databases(host, port, user, password)
        if load_success:
            st.session_state.database_list = databases
            st.session_state.databases_loaded = True
            if databases and (not st.session_state.mysql_db
                              or st.session_state.mysql_db not in databases):
                st.session_state.mysql_db = databases[0]
            reset_table_state()
            st.session_state.tables_loaded = False
            st.session_state.table_list = []
            return True, databases, None
        st.session_state.databases_loaded = False
        return False, [], f"获取数据库列表失败: {error}"
    st.session_state.connection_ok = False
    st.session_state.show_error = True
    st.session_state.error_message = error_msg
    st.session_state.connect_attempted = True
    reset_connection_state()
    return False, [], error_msg


def load_tables_for_database(host, port, user, password, database):
    if not database:
        st.session_state.table_list = []
        st.session_state.tables_loaded = False
        return False, []
    success, tables, error = fetch_tables(host, port, user, password, database)
    if success:
        st.session_state.table_list = tables
        st.session_state.tables_loaded = True
        if st.session_state.mysql_table and st.session_state.mysql_table not in tables:
            st.session_state.mysql_table = tables[0] if tables else ""
        reset_table_state()
        return True, tables
    st.session_state.table_list = []
    st.session_state.tables_loaded = False
    return False, []


def load_table_schema(host, port, user, password, database, table_name):
    if not table_name or not database:
        reset_table_state()
        return False, None

    cache_key = f"{host}:{port}:{database}:{table_name}"
    if st.session_state.schema_cache_key == cache_key and st.session_state.schema_loaded:
        return True, st.session_state.table_schema

    success, schema_df, pk_cols, col_types = fetch_table_schema(
        host, port, user, password, database, table_name)
    if success:
        st.session_state.table_schema = schema_df
        st.session_state.schema_loaded = True
        st.session_state.table_columns = schema_df['Field'].tolist() \
            if 'Field' in schema_df.columns else []
        st.session_state.primary_key = pk_cols[0] if pk_cols else None
        st.session_state.column_types = col_types
        st.session_state.schema_cache_key = cache_key
        return True, schema_df
    reset_table_state()
    return False, None


def filter_empty_rows(df):
    if df is None or df.empty:
        return df
    df = df.copy()
    df = df.replace(r'^\s*$', pd.NA, regex=True)
    df = df.dropna(axis=0, how='all').reset_index(drop=True)
    return df


def load_table_data(host, port, user, password, database, table_name,
                    filters=None, limit=DEFAULT_LIMIT):
    if not table_name or not database:
        st.session_state.table_data_loaded = False
        st.session_state.table_data = None
        st.session_state.table_total_count = None
        return False, None

    filters_tuple = tuple(sorted(filters.items())) if filters else ()
    cache_key = f"{host}:{port}:{database}:{table_name}:{filters_tuple}:{limit}"
    if st.session_state.data_cache_key == cache_key and st.session_state.table_data_loaded:
        return True, st.session_state.table_data

    success, df, error = fetch_table_data_with_filters(
        host, port, user, password, database, table_name, filters, limit)
    if success:
        if df is not None and not df.empty:
            original_rows = len(df)
            df = filter_empty_rows(df)
            removed = original_rows - len(df)
            if removed > 0:
                add_log("info", f"已过滤 {removed} 个全空行",
                        f"table={table_name}, 剩余行数={len(df)}")
        st.session_state.table_data = df
        st.session_state.table_data_loaded = True
        st.session_state.table_total_count = get_table_total_count_cached(
            host, port, user, password, database, table_name, filters_tuple)
        st.session_state.data_cache_key = cache_key
        st.session_state.selected_rows = []
        return True, df
    st.session_state.table_data = None
    st.session_state.table_data_loaded = False
    st.session_state.table_total_count = None
    st.session_state.data_cache_key = ""
    return False, None


def execute_sql_query(host, port, user, password, database, query):
    try:
        add_log("info", "执行SQL查询", f"database={database}")
        add_log("sql", "执行SQL语句", f"database={database}", query)
        engine = get_engine(host, port, user, password, database) if database \
            else get_engine(host, port, user, password)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if query.strip().upper().startswith('SELECT'):
                columns = result.keys()
                data = result.fetchall()
                df = pd.DataFrame(data, columns=columns)
                if df is not None and not df.empty:
                    original_rows = len(df)
                    df = filter_empty_rows(df)
                    removed = original_rows - len(df)
                    if removed > 0:
                        add_log("info", f"已过滤 {removed} 个全空行", "SQL查询结果")
                add_log("success", "查询执行成功", f"返回 {len(data)} 行")
                return True, df, None, len(data)
            conn.commit()
            rowcount = result.rowcount if hasattr(result, 'rowcount') else 0
            add_log("success", "SQL执行成功", f"影响 {rowcount} 行")
            return True, None, f"执行成功，影响 {rowcount} 行", rowcount
    except OperationalError as e:
        add_log("error", "数据库错误", str(e))
        return False, None, f"数据库错误: {str(e)}", 0
    except SQLAlchemyError as e:
        add_log("error", "SQL错误", str(e))
        return False, None, f"SQL错误: {str(e)}", 0
    except Exception as e:
        add_log("error", "执行错误", str(e))
        return False, None, f"执行错误: {str(e)}", 0


def build_column_config(df, pk_col=None, include_select=False):
    column_config = {}
    if include_select:
        column_config["☑️ 选择"] = st.column_config.CheckboxColumn(
            "选择", help="勾选要删除的行", default=False, width="small")
        column_config["_原始主键值"] = None
    if st.session_state.column_types:
        for col in df.columns:
            if col in ("☑️ 选择", "_原始主键值"):
                continue
            mysql_type = st.session_state.column_types.get(col, 'varchar')
            col_type_class = detect_column_type(mysql_type)
            if col_type_class == st.column_config.DateColumn:
                column_config[col] = st.column_config.DateColumn(col, format="YYYY-MM-DD")
            elif col_type_class == st.column_config.DatetimeColumn:
                column_config[col] = st.column_config.DatetimeColumn(col, format="YYYY-MM-DD HH:mm:ss")
            elif col_type_class == st.column_config.TimeColumn:
                column_config[col] = st.column_config.TimeColumn(col, format="HH:mm:ss")
            elif col_type_class == st.column_config.NumberColumn:
                column_config[col] = st.column_config.NumberColumn(col)
            elif col_type_class == st.column_config.CheckboxColumn:
                column_config[col] = st.column_config.CheckboxColumn(col)
            else:
                column_config[col] = st.column_config.TextColumn(col)
    return column_config


def calc_table_height(df, min_height=100, max_height=520):
    """根据 DataFrame 行数动态计算表格高度。"""
    if df is None:
        return min_height
    try:
        n = len(df)
    except Exception:
        n = 0
    if n <= 0:
        return min_height
    height = 38 + n * 35
    return max(min_height, min(max_height, height))


# ============================================================
# 删除确认弹窗
# ============================================================
@st.dialog("⚠️ 删除确认")
def confirm_delete_dialog():
    pk_col = st.session_state.primary_key
    table_name = st.session_state.mysql_table
    delete_pk_values = st.session_state.get("_dialog_delete_rows") or []
    row_count = len(delete_pk_values)
    mode_text = "批量删除" if row_count > 1 else "删除"

    st.markdown(
        f'<div class="delete-warning">'
        f'<div class="delete-warning-title">⚠️ {mode_text}确认</div>'
        f'<div class="delete-warning-text">'
        f'您即将从表 <b>{table_name}</b> 中删除 <b>{row_count}</b> 条记录。<br>'
        f'主键列：<code>{pk_col}</code><br>'
        f'主键值：<code>{", ".join(str(v) for v in delete_pk_values[:20])}'
        f'{"..." if len(delete_pk_values) > 20 else ""}</code><br><br>'
        f'<b style="color:#c92a2a;">此操作不可撤销，数据将被永久删除！</b>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ 确认删除", type="primary", use_container_width=True,
                     key="dialog_btn_confirm"):
            success, deleted_count, error_msg = delete_table_rows(
                st.session_state.mysql_host, st.session_state.mysql_port,
                st.session_state.mysql_user, st.session_state.mysql_pwd,
                st.session_state.mysql_db, st.session_state.mysql_table,
                pk_col, delete_pk_values)
            if success:
                st.session_state["_delete_result"] = f"✅ 成功删除 {deleted_count} 条数据"
                st.session_state["_delete_result_ok"] = True
            else:
                st.session_state["_delete_result"] = f"❌ 删除失败：{error_msg}"
                st.session_state["_delete_result_ok"] = False
            st.session_state.selected_rows = []
            st.session_state.table_data_loaded = False
            st.session_state.data_cache_key = ""
            st.session_state["_dialog_delete_rows"] = None
            st.session_state["_show_delete_dialog"] = False
            st.rerun()
    with col_cancel:
        if st.button("❌ 取消删除", use_container_width=True, key="dialog_btn_cancel"):
            st.session_state["_dialog_delete_rows"] = None
            st.session_state["_show_delete_dialog"] = False
            st.rerun()


# ============================================================
# 顶部配置区
# ============================================================
st.markdown('<div class="main-header">🐬 MySQL 数据库连接工具</div>', unsafe_allow_html=True)

with st.container():
    col_ip, col_port, col_user, col_pwd, col_db, col_table = st.columns(6)

    with col_ip:
        current_host = st.session_state.mysql_host
        options = [current_host] + IP_PRESETS if current_host not in IP_PRESETS else IP_PRESETS.copy()
        selected_host = st.selectbox(
            "IP", options=options,
            index=options.index(current_host) if current_host in options else 0,
            key="host_select")
        if selected_host != st.session_state.mysql_host:
            st.session_state.mysql_host = selected_host
            if selected_host in ["localhost", "127.0.0.1"]:
                st.session_state.mysql_user = "root"
                st.session_state.mysql_pwd = "root"
            reset_connection_state()
            st.rerun()

    with col_port:
        st.number_input("端口", value=st.session_state.mysql_port,
                        key="mysql_port_input", step=1, min_value=1, max_value=65535)
        if st.session_state.mysql_port_input != st.session_state.mysql_port:
            st.session_state.mysql_port = int(st.session_state.mysql_port_input)
            reset_connection_state()

    with col_user:
        st.text_input("账号", value=st.session_state.mysql_user,
                      key="mysql_user_input", placeholder="root")
        if st.session_state.mysql_user_input != st.session_state.mysql_user:
            st.session_state.mysql_user = st.session_state.mysql_user_input
            reset_connection_state()

    with col_pwd:
        st.text_input("密码", value=st.session_state.mysql_pwd,
                      key="mysql_pwd_input", placeholder="**********", type="password")
        if st.session_state.mysql_pwd_input != st.session_state.mysql_pwd:
            st.session_state.mysql_pwd = st.session_state.mysql_pwd_input
            reset_connection_state()

    with col_db:
        if st.session_state.databases_loaded and st.session_state.database_list:
            current_db = st.session_state.mysql_db
            if current_db not in st.session_state.database_list:
                current_db = st.session_state.database_list[0]
                st.session_state.mysql_db = current_db
            selected_db = st.selectbox(
                "数据库", options=st.session_state.database_list,
                index=st.session_state.database_list.index(current_db)
                if current_db in st.session_state.database_list else 0,
                placeholder="🔍 搜索...", key="db_select")
            if selected_db != st.session_state.mysql_db:
                st.session_state.mysql_db = selected_db
                st.session_state.tables_loaded = False
                st.session_state.table_list = []
                st.session_state.mysql_table = ""
                reset_table_state()
                load_tables_for_database(
                    st.session_state.mysql_host, st.session_state.mysql_port,
                    st.session_state.mysql_user, st.session_state.mysql_pwd, selected_db)
                st.rerun()
        else:
            st.selectbox("数据库", options=["请先连接..."], disabled=True,
                         key="db_select_disabled")

    with col_table:
        if st.session_state.tables_loaded and st.session_state.table_list:
            current_table = st.session_state.mysql_table
            if current_table not in st.session_state.table_list:
                current_table = st.session_state.table_list[0]
                st.session_state.mysql_table = current_table
            selected_table = st.selectbox(
                "表", options=st.session_state.table_list,
                index=st.session_state.table_list.index(current_table)
                if current_table in st.session_state.table_list else 0,
                placeholder="🔍 搜索表...", key="table_select")
            if selected_table != st.session_state.mysql_table:
                st.session_state.mysql_table = selected_table
                reset_table_state()
                st.rerun()
        else:
            st.selectbox("表", options=["请先选择数据库..."], disabled=True,
                         key="table_select_disabled")


# ============================================================
# 表结构 + 数据展示
# ============================================================
if st.session_state.mysql_table and st.session_state.tables_loaded:
    if not st.session_state.schema_loaded:
        load_table_schema(st.session_state.mysql_host, st.session_state.mysql_port,
                          st.session_state.mysql_user, st.session_state.mysql_pwd,
                          st.session_state.mysql_db, st.session_state.mysql_table)

    # ---------- 表结构 ----------
    if st.session_state.schema_loaded and st.session_state.table_schema is not None:
        with st.expander(f"📐 表结构: {st.session_state.mysql_table}", expanded=False):
            df = st.session_state.table_schema
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("字段数", len(df))
            with col2:
                pk_count = len(df[df['Key'] == 'PRI']) if 'Key' in df.columns else 0
                st.metric("主键字段", pk_count)
            with col3:
                not_null_count = len(df[df['Null'] == 'NO']) if 'Null' in df.columns else 0
                st.metric("非空字段", not_null_count)
            st.dataframe(
                df, use_container_width=True,
                height=calc_table_height(df, max_height=300),
                column_config={"Field": "字段名", "Type": "数据类型", "Null": "是否为空",
                               "Key": "键类型", "Default": "默认值", "Extra": "额外信息"})
            st.download_button("📥 导出表结构 CSV", data=df.to_csv(index=False),
                               file_name=f"{st.session_state.mysql_table}_schema.csv",
                               mime="text/csv", use_container_width=True)
    elif st.session_state.schema_loaded and st.session_state.table_schema is None:
        st.warning(f"⚠️ 无法加载表 {st.session_state.mysql_table} 的结构信息")

    # ---------- 条件筛选区 ----------
    if st.session_state.schema_loaded and st.session_state.table_schema is not None:
        schema_df = st.session_state.table_schema
        filter_columns = schema_df['Field'].head(10).tolist() \
            if 'Field' in schema_df.columns else []

        _df_pre = st.session_state.table_data if st.session_state.table_data is not None else None
        _pk_pre = st.session_state.primary_key
        _can_delete_pre = (_df_pre is not None and _pk_pre is not None
                           and _pk_pre in _df_pre.columns)
        _selected_count_pre = len(st.session_state.selected_rows) if _can_delete_pre else 0

        # 标题 + 按钮组
        col_title, col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1, 1.2])
        with col_title:
            st.markdown("### 🔍 条件筛选")
        with col_btn1:
            query_clicked = st.button("🔍 查询", use_container_width=True,
                                      type="primary", key="btn_query")
        with col_btn2:
            reset_clicked = st.button("🔄 重置", use_container_width=True, key="btn_reset")
        with col_btn3:
            if _can_delete_pre:
                if _selected_count_pre == 0:
                    delete_label, delete_help = "🗑️ 删除选中行", "请先在表格中勾选要删除的行"
                elif _selected_count_pre == 1:
                    delete_label, delete_help = "🗑️ 删除选中行 (1)", "删除勾选的这 1 行数据"
                else:
                    delete_label = f"🗑️ 批量删除 ({_selected_count_pre})"
                    delete_help = f"批量删除勾选的 {_selected_count_pre} 行数据"
                delete_clicked = st.button(delete_label, use_container_width=True,
                                           disabled=False, help=delete_help,
                                           key="btn_delete_selected")
            else:
                delete_clicked = st.button(
                    "🗑️ 删除选中行", use_container_width=True, disabled=True,
                    help="该表没有主键，无法删除", key="btn_delete_selected_disabled")

        # 筛选卡片
        filter_values = {}
        filter_cols = st.columns(min(len(filter_columns), 5))
        for idx, col_name in enumerate(filter_columns):
            with filter_cols[idx % 5]:
                col_type = schema_df[schema_df['Field'] == col_name]['Type'].iloc[0] \
                    if 'Type' in schema_df.columns else 'varchar'
                is_numeric = any(x in col_type.lower()
                                 for x in ('int', 'decimal', 'float'))
                current_value = st.session_state.filter_conditions.get(col_name, "")
                if is_numeric:
                    filter_values[col_name] = st.number_input(
                        f"{col_name}",
                        value=float(current_value) if current_value else None,
                        step=1, key=f"filter_{col_name}")
                else:
                    filter_values[col_name] = st.text_input(
                        f"{col_name}",
                        value=current_value if current_value else "",
                        key=f"filter_{col_name}")

        if query_clicked:
            st.session_state.filter_conditions = {
                k: v for k, v in filter_values.items() if v and str(v).strip()}
            st.session_state.table_data_loaded = False
            st.session_state.data_cache_key = ""
            st.session_state.selected_rows = []
            st.rerun()
        if reset_clicked:
            st.session_state.filter_conditions = {}
            st.session_state.table_data_loaded = False
            st.session_state.data_cache_key = ""
            st.session_state.selected_rows = []
            st.rerun()
        if delete_clicked and _can_delete_pre:
            if _selected_count_pre == 0:
                st.warning("⚠️ 请先在表格中勾选要删除的行")
            else:
                st.session_state["_dialog_delete_rows"] = list(st.session_state.selected_rows)
                st.session_state["_show_delete_dialog"] = True
                st.rerun()

    # ---------- 数据展示 ----------
    if st.session_state.schema_loaded and st.session_state.table_schema is not None:
        if not st.session_state.table_data_loaded:
            load_table_data(
                st.session_state.mysql_host, st.session_state.mysql_port,
                st.session_state.mysql_user, st.session_state.mysql_pwd,
                st.session_state.mysql_db, st.session_state.mysql_table,
                st.session_state.filter_conditions
                if st.session_state.filter_conditions else None)

        if st.session_state.table_data_loaded and st.session_state.table_data is not None:
            # ---- 顶部提示（删除/更新结果）----
            if "_delete_result" in st.session_state:
                if st.session_state.get("_delete_result_ok"):
                    st.success(st.session_state["_delete_result"])
                else:
                    st.error(st.session_state["_delete_result"])
                st.session_state.pop("_delete_result", None)
                st.session_state.pop("_delete_result_ok", None)

            if "_update_result" in st.session_state:
                if st.session_state.get("_update_result_ok"):
                    st.success(st.session_state["_update_result"])
                else:
                    st.error(st.session_state["_update_result"])
                st.session_state.pop("_update_result", None)
                st.session_state.pop("_update_result_ok", None)

            df = st.session_state.table_data.copy()
            pk_col = st.session_state.primary_key
            can_delete = pk_col is not None and pk_col in df.columns

            # ---- 统计信息 ----
            if st.session_state.table_total_count is not None:
                total = st.session_state.table_total_count
                shown = len(df)
                st.caption(
                    f"📌 显示前 {shown} 条 (共 {total} 条记录)"
                    if shown < total else f"📌 共 {total} 条记录")
            else:
                st.caption(f"📌 共 {len(df)} 行数据")

            # ---- 数据编辑器 ----
            edited_df = None
            if can_delete:
                display_df = df.copy()
                display_df.insert(0, "☑️ 选择", False)
                display_df["_原始主键值"] = df[pk_col].values

                column_config = build_column_config(display_df, pk_col=pk_col,
                                                    include_select=True)
                dynamic_height = calc_table_height(display_df)

                edited_df = st.data_editor(
                    display_df, use_container_width=True, height=dynamic_height,
                    key="data_editor", disabled=False, num_rows="fixed",
                    column_config=column_config)

                # 提取勾选
                try:
                    mask = edited_df["☑️ 选择"] == True
                    pk_values = edited_df.loc[mask, "_原始主键值"].tolist()
                    seen, unique = set(), []
                    for v in pk_values:
                        try:
                            if pd.isna(v):
                                continue
                        except Exception:
                            pass
                        if v not in seen:
                            seen.add(v)
                            unique.append(v)
                    st.session_state.selected_rows = unique
                except Exception:
                    st.session_state.selected_rows = []
            else:
                st.info("ℹ️ 该表没有主键，无法进行删除或编辑操作")
                column_config = build_column_config(df, pk_col=None, include_select=False)
                st.dataframe(df, use_container_width=True,
                             height=calc_table_height(df), column_config=column_config)

            # ---- 单元格编辑检测（向量化比较）----
            if can_delete and edited_df is not None:
                data_cols = [c for c in df.columns if c in edited_df.columns]
                orig_display = df.copy()
                orig_display.insert(0, "☑️ 选择", False)
                orig_display["_原始主键值"] = df[pk_col].values

                if not orig_display[data_cols].equals(edited_df[data_cols]):
                    # 一次性比较，找出有变化的行
                    changed_mask = ~(orig_display[data_cols].fillna("__NA__")
                                     .astype(str)
                                     .eq(edited_df[data_cols].fillna("__NA__")
                                         .astype(str))
                                     .all(axis=1))

                    changes = []
                    for idx in edited_df.index[changed_mask]:
                        pk_value = edited_df.loc[idx, "_原始主键值"]
                        if pd.isna(pk_value):
                            continue
                        update_data = {}
                        changed_fields = {}
                        for col in data_cols:
                            if col == pk_col:
                                continue
                            old_val = orig_display.loc[idx, col]
                            new_val = edited_df.loc[idx, col]
                            try:
                                same = (pd.isna(old_val) and pd.isna(new_val)) or \
                                       (str(old_val) == str(new_val))
                            except Exception:
                                same = (old_val == new_val)
                            if not same:
                                if isinstance(new_val, (datetime, date, pd.Timestamp)):
                                    update_data[col] = str(new_val)
                                else:
                                    update_data[col] = new_val
                                changed_fields[col] = {"old": old_val, "new": new_val}
                        if update_data:
                            changes.append({
                                'pk_col': pk_col, 'pk_value': pk_value,
                                'update_data': update_data,
                                'changed_fields': changed_fields})

                    if changes:
                        success_count, error_messages = 0, []
                        for change in changes:
                            add_log("data", "前端数据变更",
                                    f"table={st.session_state.mysql_table}, "
                                    f"pk={change['pk_col']}={change['pk_value']}",
                                    data=change['changed_fields'])
                            success, result = update_table_data(
                                st.session_state.mysql_host, st.session_state.mysql_port,
                                st.session_state.mysql_user, st.session_state.mysql_pwd,
                                st.session_state.mysql_db, st.session_state.mysql_table,
                                change['pk_col'], change['pk_value'], change['update_data'])
                            if success:
                                success_count += 1
                            else:
                                error_messages.append(
                                    f"更新失败 (主键: {change['pk_value']}): {result}")

                        if success_count > 0:
                            st.session_state["_update_result"] = f"✅ 成功更新 {success_count} 条数据"
                            st.session_state["_update_result_ok"] = True
                        if error_messages:
                            st.session_state["_update_result"] = "❌ " + "；".join(error_messages)
                            st.session_state["_update_result_ok"] = False

                        st.session_state.table_data_loaded = False
                        st.session_state.data_cache_key = ""
                        st.rerun()

        elif st.session_state.table_data_loaded and st.session_state.table_data is None:
            st.warning(f"⚠️ 无法加载表 {st.session_state.mysql_table} 的数据")

# ---- 删除确认弹窗（末尾渲染一次）----
if st.session_state.get("_show_delete_dialog") and st.session_state.get("_dialog_delete_rows"):
    confirm_delete_dialog()

# ============================================================
# SQL 统计文件面板
# ============================================================
with st.expander("📊 SQL(hrm.sql)", expanded=False):
    sql_file_path = os.path.join("sql", "hrm.sql")
    if os.path.exists(sql_file_path):
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            st.markdown(f'<div class="sql-file-content">{content}</div>',
                        unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ 读取文件失败: {str(e)}")
    else:
        st.warning(f"⚠️ 文件不存在: {sql_file_path}")
        st.info("💡 请确保 'sql/hrm.sql' 文件存在")

# ============================================================
# 操作日志面板
# ============================================================
with st.expander("📋 操作日志", expanded=False):
    log_filter = st.selectbox(
        "筛选", options=["全部", "信息", "成功", "警告", "错误", "SQL", "数据"],
        key="log_filter_select")

    if st.session_state.operation_logs:
        filter_map = {"全部": None, "信息": "info", "成功": "success", "警告": "warning",
                      "错误": "error", "SQL": "sql", "数据": "data"}
        filter_type = filter_map.get(log_filter)
        filtered_logs = st.session_state.operation_logs
        if filter_type:
            filtered_logs = [log for log in filtered_logs if log['type'] == filter_type]
        if not filtered_logs:
            st.info(f"📭 暂无 {log_filter} 类型的日志")
        else:
            st.markdown(render_logs(), unsafe_allow_html=True)
            stats = {k: 0 for k in ("info", "success", "error", "warning", "sql", "data")}
            for log in st.session_state.operation_logs:
                if log['type'] in stats:
                    stats[log['type']] += 1
            cols = st.columns(6)
            for col_widget, (label, key) in zip(cols, [
                    ("📘 信息", "info"), ("✅ 成功", "success"),
                    ("❌ 错误", "error"), ("⚠️ 警告", "warning"),
                    ("💾 SQL", "sql"), ("📊 数据", "data")]):
                with col_widget:
                    st.metric(label, stats[key])
    else:
        st.info("📭 暂无操作日志")

# ============================================================
# 启动日志 + 自动连接
# ============================================================
if not st.session_state.auto_connect_done:
    add_log("info", "🚀 MySQL数据库连接工具启动", f"日志文件: {LOG_FILE}")

current_hash = get_config_hash(st.session_state.mysql_host, st.session_state.mysql_port,
                               st.session_state.mysql_user, st.session_state.mysql_pwd)
if ((not st.session_state.auto_connect_done
     or current_hash != st.session_state.config_hash)
        and st.session_state.mysql_pwd):
    st.session_state.config_hash = current_hash
    success, databases, error = auto_connect_and_load(
        st.session_state.mysql_host, st.session_state.mysql_port,
        st.session_state.mysql_user, st.session_state.mysql_pwd)
    if success:
        st.session_state.auto_connect_done = True
        if databases and not st.session_state.mysql_db:
            st.session_state.mysql_db = databases[0]
        if st.session_state.mysql_db:
            load_tables_for_database(
                st.session_state.mysql_host, st.session_state.mysql_port,
                st.session_state.mysql_user, st.session_state.mysql_pwd,
                st.session_state.mysql_db)
            if st.session_state.table_list:
                st.session_state.mysql_table = st.session_state.table_list[0]
                load_table_schema(
                    st.session_state.mysql_host, st.session_state.mysql_port,
                    st.session_state.mysql_user, st.session_state.mysql_pwd,
                    st.session_state.mysql_db, st.session_state.mysql_table)
        st.rerun()

# ============================================================
# 错误信息
# ============================================================
if st.session_state.show_error and st.session_state.error_message:
    st.markdown(f'<div class="error-box">❌ {st.session_state.error_message}</div>',
                unsafe_allow_html=True)

# ============================================================
# SQL 执行面板
# ============================================================
if st.session_state.connection_ok and st.session_state.mysql_db:
    st.markdown('<div class="sql-panel-title">⚡ SQL 执行</div>', unsafe_allow_html=True)
    col_sql, col_btn = st.columns([5, 1])
    with col_sql:
        sql_query = st.text_area("SQL", value=st.session_state.sql_query, height=120,
                                 key="sql_editor", label_visibility="collapsed",
                                 placeholder="SELECT * FROM your_table LIMIT 10;")
        if sql_query != st.session_state.sql_query:
            st.session_state.sql_query = sql_query
            st.session_state.query_executed = False
    with col_btn:
        st.write("")
        execute_clicked = st.button("▶ 执行", type="primary", use_container_width=True)
        clear_clicked = st.button("✕ 清空", use_container_width=True)

    if execute_clicked and st.session_state.sql_query.strip():
        with st.spinner("执行中..."):
            success, result, message, rowcount = execute_sql_query(
                st.session_state.mysql_host, st.session_state.mysql_port,
                st.session_state.mysql_user, st.session_state.mysql_pwd,
                st.session_state.mysql_db, st.session_state.sql_query)
            if success:
                st.session_state.query_success = True
                st.session_state.query_error = ""
                st.session_state.query_rows = rowcount
                st.session_state.query_executed = True
                if isinstance(result, pd.DataFrame):
                    st.session_state.query_result = result
                else:
                    st.session_state.query_result = None
                    st.success(f"✅ {message}")
            else:
                st.session_state.query_success = False
                st.session_state.query_error = message
                st.session_state.query_executed = True
                st.session_state.query_result = None
                st.error(f"❌ {message}")
    if clear_clicked:
        reset_query_state()
        st.rerun()

    if st.session_state.query_executed:
        if st.session_state.query_success and st.session_state.query_result is not None:
            df = st.session_state.query_result
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.metric("行数", len(df))
            with col_stats2:
                st.metric("列数", len(df.columns))
            st.dataframe(df, use_container_width=True, height=calc_table_height(df))
            col_export1, col_export2 = st.columns(2)
            with col_export1:
                st.download_button(
                    "📥 下载 CSV", data=df.to_csv(index=False),
                    file_name=f"query_result_{st.session_state.mysql_db}.csv",
                    mime="text/csv", use_container_width=True)
            with col_export2:
                with st.expander("📝 SQL"):
                    st.code(st.session_state.sql_query, language="sql")
        elif not st.session_state.query_success and st.session_state.query_error:
            st.markdown(
                f'<div class="error-box">❌ {st.session_state.query_error}</div>',
                unsafe_allow_html=True)