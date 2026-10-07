# postgresql1.py
import streamlit as st
import pandas as pd
import re
import time
import json
import os
import logging
import hashlib
from logging.handlers import RotatingFileHandler
from datetime import datetime
from sqlalchemy import create_engine, text
from concurrent.futures import ThreadPoolExecutor

# ===================== 页面配置 =====================
st.set_page_config(page_title="PostgreSQL数据库工具", menu_items=None,
                   layout="wide", page_icon="🐘")

# ===================== 日志 =====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "postgresql.log")


def setup_logger():
    logger = logging.getLogger('pg_tool')
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        logger.handlers.clear()
    fh = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024,
                             backupCount=5, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(fh)
    return logger


file_logger = setup_logger()

# ===================== CSS =====================
st.markdown("""
<style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
    .element-container { margin-bottom: 0.2rem !important; }
    hr { margin: 0.5rem 0 !important; }
    .streamlit-expanderHeader { padding: 0.3rem 0.5rem !important; font-size: 0.9rem !important; }
    .streamlit-expanderContent { padding: 0.3rem 0.5rem !important; }
    .stButton button { padding: 0.2rem 0.8rem !important; font-size: 0.85rem !important; }
    .stTextArea textarea { font-size: 0.85rem !important; padding: 0.3rem !important; }
    .stDataFrame { font-size: 0.8rem !important; }
    .stMarkdown { margin-bottom: 0 !important; }
    .row-widget.stColumns { gap: 0.3rem !important; }
    .stSelectbox label, .stTextInput label, .stNumberInput label {
        font-size: 0.8rem !important; margin-bottom: 0.1rem !important;
    }
    .stSelectbox > div, .stTextInput > div, .stNumberInput > div { margin-bottom: 0.1rem !important; }
    .stAlert { padding: 0.3rem 0.8rem !important; font-size: 0.85rem !important; margin-bottom: 0.2rem !important; }
    .stException button, .stAlert button, .stCache, .stTooltipIcon, .stCodeBlock button { display: none !important; }
    h1 { margin-top: -0.5rem !important; margin-bottom: 0.2rem !important; font-size: 1.8rem !important; }

    /* ---- 操作日志 ---- */
    .oplog {
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        font-size: 0.76rem; line-height: 1.6;
        max-height: 400px; overflow-y: auto;
        background: #fafbfc; border: 1px solid #e5e9ef; border-radius: 8px;
        padding: 0.5rem 0.8rem;
    }
    .oplog-row {
        display: flex; align-items: baseline; gap: 0.5rem;
        padding: 0.18rem 0; border-bottom: 1px solid #f0f2f5;
    }
    .oplog-row:last-child { border-bottom: none; }
    .oplog-t { color: #8a94a6; flex-shrink: 0; }
    .oplog-lv { flex-shrink: 0; font-weight: 600; width: 46px; display: inline-block; }
    .lv-info    { color: #3b82f6; }
    .lv-success { color: #10b981; }
    .lv-warning { color: #f59e0b; }
    .lv-error   { color: #ef4444; }
    .lv-sql     { color: #8b5cf6; }
    .oplog-m { color: #2d3748; flex: 1; word-break: break-all; }
    .oplog-s {
        color: #8b5cf6; background: #f3f0ff; padding: 0 0.4rem;
        border-radius: 3px; font-size: 0.72rem;
    }
    .oplog-empty { color: #a0aec0; text-align: center; padding: 1rem 0; font-size: 0.82rem; }

    /* ---- SQL 文件展示 ---- */
    .sqlfile {
        background: #0f1720; color: #dbe3ee;
        border-radius: 8px; padding: 0.9rem 1rem;
        font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        font-size: 0.78rem; line-height: 1.7;
        max-height: 500px; overflow: auto;
        white-space: pre-wrap; word-wrap: break-word;
        border: 1px solid #1f2a3a;
    }
    .sqlfile-empty { color: #a0aec0; text-align: center; padding: 1rem 0; font-size: 0.82rem; }

    /* ---- 按钮配色（按 kind） ---- */
    button[kind="primary"] {
        background-color: #10b981 !important;
        border-color: #10b981 !important;
        color: #fff !important;
    }
    button[kind="primary"]:hover {
        background-color: #059669 !important;
        border-color: #059669 !important;
    }
    button[kind="primary"]:disabled {
        background-color: #a7f3d0 !important;
        border-color: #a7f3d0 !important;
        color: #fff !important; opacity: 0.7 !important;
    }
    button[kind="secondary"] {
        background-color: #eef2f7 !important;
        border-color: #d5dde7 !important;
        color: #334155 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #e2e8f0 !important;
        border-color: #cbd5e1 !important;
    }
    button[kind="secondary"]:disabled {
        background-color: #f3f4f6 !important;
        border-color: #e5e7eb !important;
        color: #9ca3af !important; opacity: 0.7 !important;
    }

    /* ---- 语义色按钮 ---- */
    [class*="st-key-btn_reset"] button {
        background-color: #3b82f6 !important; border-color: #3b82f6 !important; color: #fff !important;
    }
    [class*="st-key-btn_reset"] button:hover { background-color: #2563eb !important; border-color: #2563eb !important; }
    [class*="st-key-btn_reset"] button:active { background-color: #1d4ed8 !important; border-color: #1d4ed8 !important; }
    [class*="st-key-btn_reset"] button:disabled { background-color: #bfdbfe !important; border-color: #bfdbfe !important; color: #fff !important; opacity: .7 !important; }

    [class*="st-key-btn_del_selected"] button {
        background-color: #ef4444 !important; border-color: #ef4444 !important; color: #fff !important;
    }
    [class*="st-key-btn_del_selected"] button:hover { background-color: #dc2626 !important; border-color: #dc2626 !important; }
    [class*="st-key-btn_del_selected"] button:active { background-color: #b91c1c !important; border-color: #b91c1c !important; }
    [class*="st-key-btn_del_selected"] button:disabled { background-color: #fecaca !important; border-color: #fecaca !important; color: #fff !important; opacity: .7 !important; }

    [class*="st-key-btn_sql_tpl_query"] button {
        background-color: #8b5cf6 !important; border-color: #8b5cf6 !important; color: #fff !important;
    }
    [class*="st-key-btn_sql_tpl_query"] button:hover { background-color: #7c3aed !important; border-color: #7c3aed !important; }
    [class*="st-key-btn_sql_tpl_query"] button:active { background-color: #6d28d9 !important; border-color: #6d28d9 !important; }
</style>
""", unsafe_allow_html=True)

# ===================== 会话状态 =====================
DEFAULT_STATE = {
    # 连接
    "pg_host": "pgm-uf6jv8kq7xfyu4fako.pg.rds.aliyuncs.com",
    "pg_port": 5432,
    "pg_user": "renhe_test",
    "pg_pwd": "B72TjV4xTU5wQpVK",
    "pg_db_list": ["crmdb_test"],
    "pg_db": "crmdb_test",
    "pg_db_input": "crmdb_test",
    "pg_schema": "public",
    "pg_schema_list": ["public"],
    "pg_schema_input": "public",
    # 加载
    "initialized": False,
    "loading": False,
    "connection_attempted": False,
    "db_list_fetched": False,
    "conn_timestamp": 0,
    "last_params": None,
    # 数据
    "table_list": [],
    "selected_table": "",
    "table_data": pd.DataFrame(),
    "schema_df": pd.DataFrame(),
    "current_page_size": 50,
    "current_page_num": 1,
    # 搜索
    "show_search_results": False,
    "search_result_df": pd.DataFrame(),
    "reset_search": False,
    # 删除
    "confirm_delete_main": False,
    "confirm_delete_search": False,
    "pending_delete": None,
    # 日志
    "op_logs": [],
    "op_log_counter": 0,
    # 编辑指纹
    "save_fingerprints": {},
    # SQL
    "sql_text": "",
    "sql_tpl_selected": "",
    "sql_tpl_result": pd.DataFrame(),
    "sql_tpl_executed": False,
    "sql_last_processed": "",
    "sql_result_target_table": "",
    "sql_result_pk_cols": [],
    "sql_result_editable_cols": [],
    "sql_result_edit_fingerprint": "",
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===================== 操作日志 =====================
_LEVEL_ICON = {"info": "INFO", "success": "OK", "warning": "WARN",
               "error": "ERR", "sql": "SQL"}


def add_op_log(log_type, message, detail="", sql=""):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.op_log_counter += 1
    st.session_state.op_logs.insert(0, {
        "id": st.session_state.op_log_counter,
        "time": ts, "type": log_type,
        "message": message, "detail": detail, "sql": sql,
    })
    if len(st.session_state.op_logs) > 500:
        st.session_state.op_logs = st.session_state.op_logs[:500]

    try:
        lv = _LEVEL_ICON.get(log_type, log_type.upper())
        parts = [f"{ts} [{lv}]", message]
        if detail:
            parts.append(f"- {detail}")
        if sql:
            parts.append(f"| {sql.strip()[:300]}")
        line = ' '.join(parts)
        print(line)
        file_logger.info(line)
    except Exception:
        pass


def render_op_logs(logs=None):
    logs = logs if logs is not None else st.session_state.op_logs
    if not logs:
        return '<div class="oplog"><div class="oplog-empty">📭 暂无操作日志</div></div>'

    rows = ['<div class="oplog">']
    for log in logs[:200]:
        t = log['type']
        msg = log['message']
        if log.get('detail'):
            msg += f' <span class="oplog-detail">· {log["detail"]}</span>'
        row = (f'<div class="oplog-row">'
               f'<span class="oplog-t">{log["time"]}</span>'
               f'<span class="oplog-lv lv-{t}">{_LEVEL_ICON.get(t, t.upper())}</span>'
               f'<span class="oplog-m">{msg}')
        if log.get('sql'):
            s = log['sql'][:200] + ('...' if len(log['sql']) > 200 else '')
            row += f' <span class="oplog-s">{s}</span>'
        row += '</span></div>'
        rows.append(row)
    rows.append('</div>')
    return ''.join(rows)


# ===================== 统一连接 =====================
def _build_url(host, port, db_name, user, pwd, timeout=10):
    return (f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db_name}"
            f"?connect_timeout={timeout}")


def _make_engine(host, port, db_name, user, pwd, timeout=10):
    if not host.strip():
        raise ValueError("PostgreSQL IP不能为空")
    if not db_name.strip():
        raise ValueError("PostgreSQL 数据库名不能为空")
    if not user.strip():
        raise ValueError("PostgreSQL 账号不能为空")
    return create_engine(
        _build_url(host, port, db_name, user, pwd, timeout),
        pool_pre_ping=True, pool_recycle=300,
        pool_size=5, max_overflow=10, pool_timeout=30,
        connect_args={'connect_timeout': timeout, 'keepalives': 1,
                      'keepalives_idle': 30, 'keepalives_interval': 10,
                      'keepalives_count': 3}
    )


def _conn_params():
    s = st.session_state
    return s.pg_host, s.pg_port, s.pg_db, s.pg_user, s.pg_pwd


# ===================== 元数据查询（缓存） =====================
@st.cache_data(ttl=600, show_spinner=False)
def get_all_databases(host, port, user, pwd):
    for default_db in ['postgres', 'crmdb_test', 'template1']:
        try:
            engine = create_engine(
                _build_url(host, port, default_db, user, pwd, timeout=5),
                pool_pre_ping=True, pool_recycle=300)
            with engine.connect() as conn:
                res = conn.execute(text("""
                    SELECT datname FROM pg_database
                    WHERE datistemplate = false
                    AND datname NOT IN ('postgres','azure_maintenance','template0','template1')
                    ORDER BY datname;
                """)).fetchall()
                db_list = [row[0] for row in res]
                if db_list:
                    return db_list
        except Exception:
            continue
    return ["crmdb_test"]


@st.cache_data(ttl=600, show_spinner=False)
def get_all_schemas(host, port, db_name, user, pwd):
    try:
        engine = _make_engine(host, port, db_name, user, pwd, timeout=5)
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT DISTINCT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast','pg_temp_1','pg_temp_2')
                AND schema_name NOT LIKE 'pg_temp_%'
                AND schema_name NOT LIKE 'pg_toast%'
                ORDER BY schema_name;
            """)).fetchall()
            schema_list = [row[0] for row in res]
            if not schema_list:
                res2 = conn.execute(text("""
                    SELECT DISTINCT nspname FROM pg_namespace
                    WHERE nspname NOT IN ('pg_catalog','information_schema','pg_toast')
                    AND nspname NOT LIKE 'pg_temp_%'
                    AND nspname NOT LIKE 'pg_toast%'
                    ORDER BY nspname;
                """)).fetchall()
                schema_list = [row[0] for row in res2]
            return schema_list if schema_list else ["public"]
    except Exception:
        return ["public"]


@st.cache_data(ttl=300, show_spinner=False)
def get_all_tables(host, port, db_name, user, pwd, schema):
    try:
        engine = _make_engine(host, port, db_name, user, pwd, timeout=5)
        with engine.connect() as conn:
            res = conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = :schema_name AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """), {"schema_name": schema}).fetchall()
            return [row[0] for row in res]
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def load_table_page(host, port, db_name, user, pwd, schema, table_name, limit, offset):
    try:
        engine = _make_engine(host, port, db_name, user, pwd, timeout=5)
        sql = text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT :limit OFFSET :offset')
        with engine.connect() as conn:
            return pd.read_sql(sql, conn, params={"limit": limit, "offset": offset})
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def get_table_schema(host, port, db_name, user, pwd, schema, table_name):
    try:
        engine = _make_engine(host, port, db_name, user, pwd, timeout=5)
        sql = text("""
            SELECT
                c.column_name AS "名称",
                c.data_type AS "类型",
                c.character_maximum_length AS "长度",
                c.numeric_scale AS "小数点",
                CASE WHEN c.is_nullable = 'NO' THEN '是' ELSE '否' END AS "非空",
                CASE WHEN EXISTS (
                    SELECT 1 FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                    WHERE kcu.table_schema = :schema_name
                        AND kcu.table_name = :tbl
                        AND kcu.column_name = c.column_name
                        AND tc.constraint_type = 'PRIMARY KEY'
                ) THEN '主键' ELSE '' END AS "键",
                c.column_default AS "默认值",
                d.description AS "注释"
            FROM information_schema.columns c
            LEFT JOIN pg_description d
                ON d.objoid = (
                    SELECT oid FROM pg_class
                    WHERE relname = :tbl AND relnamespace = (
                        SELECT oid FROM pg_namespace WHERE nspname = :schema_name
                    )
                )
                AND d.objsubid = c.ordinal_position
            WHERE c.table_schema = :schema_name AND c.table_name = :tbl
            ORDER BY c.ordinal_position;
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"schema_name": schema, "tbl": table_name})
        return df.fillna("")
    except Exception:
        return pd.DataFrame()


# ===================== 工具函数 =====================
def calc_editor_height(df, row_height=35, header=38, min_h=60, max_h=450):
    if df is None or df.empty:
        return min_h
    return max(min_h, min(max_h, header + row_height * len(df) + 6))


def auto_add_pg_schema(sql, schema):
    if not sql:
        return sql
    pattern = re.compile(r'(FROM|JOIN)\s+([`"\w]+)(?![.\w])', re.IGNORECASE)
    wrap_schema = f'"{schema}".'

    def _repl(m):
        kw, tbl = m.group(1), m.group(2)
        if "." in tbl:
            return f"{kw} {tbl}"
        return f'{kw} {wrap_schema}"{tbl}"'

    return pattern.sub(_repl, sql)


def get_default_schema(schema_list):
    if not schema_list:
        return "public"
    for p in ["cust_u_rhkj", "public"]:
        if p in schema_list:
            return p
    return schema_list[0]


def parallel_load_data(host, port, db_name, user, pwd, schema, table_name, page_size):
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(get_table_schema, host, port, db_name, user, pwd, schema, table_name)
        f2 = ex.submit(load_table_page, host, port, db_name, user, pwd, schema,
                       table_name, page_size, 0)
        return f1.result(), f2.result()


def get_primary_keys(schema_df):
    if schema_df is None or schema_df.empty or "键" not in schema_df.columns:
        return []
    return schema_df[schema_df["键"] == "主键"]["名称"].tolist()


def _build_type_map(schema_df):
    tmap = {}
    if schema_df is None or schema_df.empty:
        return tmap
    if "名称" in schema_df.columns and "类型" in schema_df.columns:
        for _, r in schema_df.iterrows():
            tmap[str(r["名称"])] = str(r["类型"]).lower()
    return tmap


def _cast_value(val, db_type):
    if val is None:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    t = (db_type or "").lower()
    try:
        if "int" in t and "point" not in t:
            return int(val)
        if "numeric" in t or "decimal" in t or "real" in t or "double" in t:
            return float(val)
        if t == "boolean" or t.endswith("bool"):
            return str(val).strip().lower() in ("true", "1", "t", "yes", "y", "是")
        if "json" in t:
            return val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
        return val
    except Exception:
        return val


def _to_display_str(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v)


def _df_fingerprint(df):
    if df is None or df.empty:
        return ""
    try:
        data_cols = [c for c in df.columns if c != "选择"]
        content = df[data_cols].fillna("").astype(str).values.tolist()
        raw = json.dumps(content, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    except Exception:
        return ""


# ===================== SQL 模板 =====================
SQL_XLS_PATH = os.path.join(SCRIPT_DIR, "sql.xls")


@st.cache_data(ttl=600, show_spinner=False)
def load_sql_templates(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        try:
            df = pd.read_excel(path, header=0, dtype=str)
        except Exception:
            df = pd.read_csv(path, header=0, dtype=str)
        if df.shape[1] < 2:
            return pd.DataFrame()
        df.columns = [f"col{i}" for i in range(df.shape[1])]
        df = df.fillna("")
        df = df[df["col0"].astype(str).str.strip() != ""].reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()


def get_template_param_count(row, df):
    count = sum(1 for c in df.columns[2:] if str(row.get(c, "")).strip() != "")
    sql = str(row.get("col1", ""))
    if count == 0:
        ph = re.findall(r"\{(\d+)(?::raw)?\}", sql)
        if ph:
            count = max(int(x) for x in ph) + 1
    if count == 0 and "%s" in sql:
        count = sql.count("%s")
    return count


def get_template_param_labels(row, df, param_count):
    labels = [str(row.get(c, "")).strip() for c in df.columns[2:]
              if str(row.get(c, "")).strip() != ""]
    while len(labels) < param_count:
        labels.append(f"参数 {len(labels)}")
    return labels[:param_count]


def _quote_sql_value(v):
    s = "" if v is None else str(v)
    return f"'{s.replace(chr(39), chr(39)*2)}'"


def apply_sql_params(sql, param_values):
    if not param_values:
        return sql, "", None

    if re.search(r"\{\d+(:raw)?\}", sql):
        errors = []

        def _repl(m):
            idx = int(m.group(1))
            is_raw = bool(m.group(2))
            if idx >= len(param_values):
                errors.append(f"缺少参数 {{{idx}}}")
                return m.group(0)
            val = param_values[idx]
            return str(val) if is_raw else _quote_sql_value(val)

        new_sql = re.sub(r"\{(\d+)(:raw)?\}", _repl, sql)
        if errors:
            return sql, "；".join(errors), None
        return new_sql, "", None

    if "%s" in sql:
        n = sql.count("%s")
        if n != len(param_values):
            return sql, f"SQL 需要 {n} 个 %s 参数，但前端提供了 {len(param_values)} 个", None
        return sql, "", tuple(param_values)

    return sql, "SQL 中未找到 {0} 或 %s 占位符，参数未替换", None


# ===================== 回写（核心） =====================
def _write_back(df_orig, df_edit, target_table, pk_cols, editable_cols,
                schema, log_prefix="回写"):
    """通用回写：diff → UPDATE。返回 (has_change, ok, msg, new_df)"""
    if not target_table or not pk_cols:
        return False, False, "缺少目标表或主键列", df_orig

    schema_df = get_table_schema(*_conn_params(), schema, target_table)
    type_map = _build_type_map(schema_df)

    changed = []
    for idx in df_orig.index:
        diff = {}
        for col in editable_cols:
            if col not in df_orig.columns or col not in df_edit.columns:
                continue
            if _to_display_str(df_orig.at[idx, col]) != _to_display_str(df_edit.at[idx, col]):
                diff[col] = _to_display_str(df_edit.at[idx, col])
        if diff:
            pk = {c: df_orig.at[idx, c] for c in pk_cols if c in df_orig.columns}
            if len(pk) != len(pk_cols):
                return False, False, f"行 {idx} 缺少主键", df_orig
            changed.append((pk, diff))

    if not changed:
        return False, True, "", df_orig

    try:
        engine = _make_engine(*_conn_params())
        total_fields = sum(len(d) for _, d in changed)
        with engine.begin() as conn:
            for i, (pk, diff) in enumerate(changed):
                sets, wheres, params = [], [], {}
                for col, val in diff.items():
                    k = f"s_{i}_{col}"
                    sets.append(f'"{col}" = :{k}')
                    params[k] = _cast_value(val, type_map.get(col, "")) if val != "" else None
                for col, val in pk.items():
                    k = f"w_{i}_{col}"
                    wheres.append(f'"{col}" = :{k}')
                    params[k] = val
                sql = (f'UPDATE "{schema}"."{target_table}" '
                       f'SET {", ".join(sets)} WHERE {" AND ".join(wheres)}')
                add_op_log("sql", f"{log_prefix} UPDATE · {pk}", sql=sql)
                conn.execute(text(sql), params)
        return True, True, f"{log_prefix} {len(changed)} 行 / {total_fields} 字段", df_edit
    except Exception as e:
        add_op_log("error", f"{log_prefix} 失败", str(e))
        return True, False, str(e), df_orig


def auto_save_edited_rows(df_orig, df_edit, schema_df, schema, table):
    pk = get_primary_keys(schema_df)
    if not pk:
        return False, False, "该表没有主键，无法自动保存"
    editable = [c for c in df_orig.columns if c != "选择" and c not in pk]
    return _write_back(df_orig, df_edit, table, pk, editable, schema, "自动保存")


def auto_update_sql_rows(df_orig, df_edit, table, pk, editable, schema):
    has_change, ok, msg, new_df = _write_back(
        df_orig, df_edit, table, pk, editable, schema, "SQL结果回写")
    return has_change, ok, msg, new_df


# ===================== 删除 =====================
def delete_selected_rows(df_original, selected_indices, schema_df,
                         schema, table_name):
    pk_cols = get_primary_keys(schema_df)
    if not pk_cols:
        return False, 0, "该表没有主键，无法定位删除目标，请手动执行 SQL"
    if not selected_indices:
        return False, 0, "未勾选任何行"

    placeholders, params = [], {}
    for i, idx in enumerate(selected_indices):
        pk_vals = []
        for c in pk_cols:
            key = f"pk_{i}_{c}"
            placeholders.append(f":{key}")
            params[key] = df_original.loc[idx, c]
            pk_vals.append(f"{c}={df_original.loc[idx, c]}")
        add_op_log("info", f"待删除行主键: {' & '.join(pk_vals)}")

    if len(pk_cols) == 1:
        pk = pk_cols[0]
        where_sql = f'"{pk}" IN ({", ".join(placeholders)})'
    else:
        cols_sql = ", ".join([f'"{c}"' for c in pk_cols])
        n = len(selected_indices)
        group = "(" + ", ".join([f":{f'pk_{i}_{c}'}" for c in pk_cols]) + ")"
        where_sql = f'({cols_sql}) IN ({", ".join([group] * n)})'

    delete_sql = f'DELETE FROM "{schema}"."{table_name}" WHERE {where_sql}'
    add_op_log("sql", f"执行 DELETE · {len(selected_indices)} 行", sql=delete_sql)

    try:
        engine = _make_engine(*_conn_params())
        with engine.begin() as conn:
            result = conn.execute(text(delete_sql), params)
            deleted = result.rowcount
        return True, deleted, f"成功删除 {deleted} 行"
    except Exception as e:
        add_op_log("error", "DELETE 执行失败", str(e))
        return False, 0, str(e)


def reload_current_data():
    load_table_page.clear()
    try:
        st.session_state.table_data = load_table_page(
            *_conn_params(), st.session_state.pg_schema,
            st.session_state.selected_table,
            st.session_state.current_page_size, 0)
    except Exception:
        pass


# ===================== 删除确认弹窗 =====================
@st.dialog("⚠️ 确认删除")
def confirm_delete_dialog(pending):
    df_original = pending["df_original"]
    indices = pending["indices"]
    pk_cols = pending["pk_cols"]
    key_prefix = pending["key_prefix"]

    st.warning(f"即将删除 **{len(indices)}** 行数据，此操作不可撤销！")

    if pk_cols:
        preview_cols = [c for c in pk_cols if c in df_original.columns]
        preview_df = df_original.loc[indices, preview_cols].head(10).copy()
        preview_df.columns = [f"🔑 {c}" for c in preview_df.columns]
        st.markdown("**待删除主键**（最多预览 10 条）：")
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
        if len(indices) > 10:
            st.caption(f"... 还有 {len(indices) - 10} 行未展示")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ 确认删除", type="primary", use_container_width=True):
            ok, deleted, msg = delete_selected_rows(
                df_original=df_original, selected_indices=indices,
                schema_df=st.session_state.schema_df,
                schema=st.session_state.pg_schema,
                table_name=st.session_state.selected_table)
            st.session_state.pending_delete = None
            st.session_state.confirm_delete_main = False
            st.session_state.confirm_delete_search = False
            if ok:
                add_op_log("success", f"删除成功 · {deleted} 行")
                st.session_state["_del_toast"] = f"✅ {msg}"
                reload_current_data()
                if key_prefix == "search":
                    st.session_state.search_result_df = pd.DataFrame()
                    st.session_state.show_search_results = False
            else:
                st.session_state["_del_toast"] = f"❌ 删除失败：{msg}"
            st.rerun()
    with c2:
        if st.button("❌ 取消", use_container_width=True):
            st.session_state.pending_delete = None
            st.session_state.confirm_delete_main = False
            st.session_state.confirm_delete_search = False
            st.rerun()


# ===================== 状态变更 =====================
def _reset_table_state():
    st.session_state.table_list = []
    st.session_state.selected_table = ""
    st.session_state.schema_df = pd.DataFrame()
    st.session_state.table_data = pd.DataFrame()
    st.session_state.show_search_results = False
    st.session_state.search_result_df = pd.DataFrame()
    st.session_state.save_fingerprints = {}
    st.session_state.conn_timestamp = 0


def _on_db_change(new_db):
    add_op_log("info", f"切换数据库 {st.session_state.pg_db} → {new_db}")
    st.session_state.pg_db = new_db
    st.session_state.pg_db_input = new_db
    st.session_state.initialized = False
    st.session_state.connection_attempted = False
    _reset_table_state()
    st.rerun()


def _on_schema_change(new_schema):
    add_op_log("info", f"切换 Schema {st.session_state.pg_schema} → {new_schema}")
    st.session_state.pg_schema = new_schema
    st.session_state.selected_table = ""
    st.session_state.schema_df = pd.DataFrame()
    st.session_state.table_data = pd.DataFrame()
    st.session_state.show_search_results = False
    st.session_state.search_result_df = pd.DataFrame()
    st.session_state.save_fingerprints = {}
    try:
        tables = get_all_tables(*_conn_params(), new_schema)
        st.session_state.table_list = tables
        add_op_log("success", f"表列表 · {len(tables)} 个")
        if tables:
            st.session_state.selected_table = tables[0]
            schema_df, df_data = parallel_load_data(
                *_conn_params(), new_schema, tables[0],
                st.session_state.current_page_size)
            st.session_state.schema_df = schema_df
            st.session_state.table_data = df_data
            add_op_log("success", f"加载表 {new_schema}.{tables[0]}",
                       f"{len(schema_df)} 字段 / {len(df_data)} 行")
    except Exception as e:
        add_op_log("error", "切换 Schema 后加载失败", str(e))
        st.error(f"加载表失败：{str(e)}")
    st.rerun()


def _on_table_change(new_table):
    add_op_log("info", f"切换表 {st.session_state.selected_table} → {new_table}")
    st.session_state.selected_table = new_table
    st.session_state.current_page_num = 1
    st.session_state.show_search_results = False
    st.session_state.search_result_df = pd.DataFrame()
    st.session_state.save_fingerprints = {}
    try:
        schema_df, df_data = parallel_load_data(
            *_conn_params(), st.session_state.pg_schema, new_table,
            st.session_state.current_page_size)
        st.session_state.schema_df = schema_df
        st.session_state.table_data = df_data
        add_op_log("success", f"加载表 {st.session_state.pg_schema}.{new_table}",
                   f"{len(schema_df)} 字段 / {len(df_data)} 行")
        st.rerun()
    except Exception as e:
        add_op_log("error", f"加载表 {new_table} 失败", str(e))
        st.error(f"加载表数据失败：{str(e)}")


def quick_connect_and_load():
    host, port = st.session_state.pg_host, st.session_state.pg_port
    user, pwd = st.session_state.pg_user, st.session_state.pg_pwd
    add_op_log("info", "开始连接", f"{host}:{port}/{st.session_state.pg_db}")

    try:
        if not st.session_state.db_list_fetched:
            db_list = get_all_databases(host, port, user, pwd)
            st.session_state.pg_db_list = db_list
            if st.session_state.pg_db not in db_list and db_list:
                st.session_state.pg_db = db_list[0]
            st.session_state.db_list_fetched = True
            add_op_log("success", f"数据库列表 · {len(db_list)} 个")

        schema_list = get_all_schemas(host, port, st.session_state.pg_db, user, pwd)
        st.session_state.pg_schema_list = schema_list
        default_schema = get_default_schema(schema_list)
        st.session_state.pg_schema = default_schema
        st.session_state.pg_schema_input = default_schema
        add_op_log("success", f"Schema 列表 · {len(schema_list)} 个 · 默认 {default_schema}")

        table_list = get_all_tables(host, port, st.session_state.pg_db, user, pwd,
                                    default_schema)
        st.session_state.table_list = table_list
        add_op_log("success", f"表列表 · {len(table_list)} 个")

        if table_list:
            st.session_state.selected_table = table_list[0]
            schema_df, df_data = parallel_load_data(
                host, port, st.session_state.pg_db, user, pwd,
                default_schema, table_list[0], st.session_state.current_page_size)
            st.session_state.schema_df = schema_df
            st.session_state.table_data = df_data
            add_op_log("success", f"加载表 {default_schema}.{table_list[0]}",
                       f"{len(schema_df)} 字段 / {len(df_data)} 行")

        st.session_state.connection_attempted = True
        st.session_state.initialized = True
        st.session_state.conn_timestamp = time.time()
        add_op_log("success", "连接完成")
        return True
    except Exception as e:
        st.session_state.table_list = []
        st.session_state.connection_attempted = True
        add_op_log("error", "连接失败", str(e))
        st.error(f"连接失败: {str(e)}")
        return False


# ===================== 页面标题 =====================
st.markdown("# 🐘 PostgreSQL数据库连接")


# ===================== 分区：连接栏 =====================
def render_connection_bar():
    c1, c2 = st.columns([2, 1.4])
    with c1:
        st.session_state.pg_host = st.text_input(
            "🌐 IP地址", value=st.session_state.pg_host)
    with c2:
        db_list = st.session_state.pg_db_list
        cur_db = st.session_state.pg_db
        if cur_db not in db_list and db_list:
            cur_db = db_list[0]
            st.session_state.pg_db = cur_db
            st.session_state.pg_db_input = cur_db
        selected_db = st.selectbox(
            "🗄️ 数据库", options=db_list,
            index=db_list.index(cur_db) if cur_db in db_list else 0,
            key="db_selector", help="选择或搜索数据库")
        if selected_db != st.session_state.pg_db:
            _on_db_change(selected_db)


# ===================== 分区：Schema/表/分页 =====================
def render_table_selector():
    c_s, c_t, c_ps, c_pn = st.columns([1.4, 2, 1, 1])

    with c_s:
        schema_list = st.session_state.pg_schema_list
        cur = st.session_state.pg_schema_input
        opts = [cur] + schema_list if cur not in schema_list else schema_list
        sel = st.selectbox("📂 Schema", options=opts,
                           index=opts.index(cur) if cur in opts else 0,
                           key="schema_selector")
        st.session_state.pg_schema_input = sel
        if sel != st.session_state.pg_schema and sel in schema_list:
            _on_schema_change(sel)

    with c_t:
        tables = st.session_state.table_list
        cur_t = st.session_state.selected_table or (tables[0] if tables else "")
        if cur_t not in tables:
            cur_t = tables[0] if tables else ""
            st.session_state.selected_table = cur_t
        sel_t = st.selectbox("📊 数据表", options=tables,
                             index=tables.index(cur_t) if cur_t in tables else 0)
        if sel_t != st.session_state.selected_table:
            _on_table_change(sel_t)

    with c_ps:
        sizes = [10, 20, 30, 50, 100, 200]
        ps = st.selectbox("📄 行数", sizes,
                          index=sizes.index(st.session_state.current_page_size))
        if ps != st.session_state.current_page_size:
            st.session_state.current_page_size = ps
            st.session_state.current_page_num = 1
            st.session_state.save_fingerprints = {}
            try:
                st.session_state.table_data = load_table_page(
                    *_conn_params(), st.session_state.pg_schema,
                    st.session_state.selected_table, ps, 0)
                add_op_log("success", f"重新加载 · {len(st.session_state.table_data)} 行")
                st.rerun()
            except Exception as e:
                add_op_log("error", "加载数据失败", str(e))
                st.error(f"加载数据失败：{str(e)}")

    with c_pn:
        st.number_input("页码", min_value=1,
                        value=st.session_state.current_page_num, step=1,
                        key="page_num_input",
                        disabled=st.session_state.table_data.empty)


# ===================== 分区：数据表 + 搜索 =====================
def render_table_viewer():
    if st.session_state.schema_df.empty:
        return

    with st.expander("📋 表结构", expanded=False):
        st.dataframe(st.session_state.schema_df, use_container_width=True,
                     height=calc_editor_height(st.session_state.schema_df, max_h=250))

    search_columns = st.session_state.schema_df['名称'].head(10).tolist()
    pk_cols = get_primary_keys(st.session_state.schema_df)

    c_title, c_b1, c_b2, c_b3 = st.columns([5, 1, 1, 1], vertical_alignment="center")
    with c_title:
        st.markdown("### 🔍 条件搜索")
    with c_b1:
        search_btn = st.button("🔍 查询", type="primary",
                               use_container_width=True, key="btn_search")
    with c_b2:
        reset_btn = st.button("🔄 重置", use_container_width=True, key="btn_reset")
    with c_b3:
        del_btn = st.button("🗑️ 删除选中", use_container_width=True,
                            disabled=not pk_cols, key="btn_del_selected")

    if pk_cols:
        st.caption(f"📌 主键：{', '.join(pk_cols)} | ✨ 表格可直接编辑，**修改单元格后自动写回数据库**")
    else:
        st.caption("⚠️ 当前表没有主键，无法执行删除 / 更新操作")

    # 搜索输入区
    for row_i in range(2):
        start = row_i * 5
        end = min(start + 5, len(search_columns))
        cols_names = search_columns[start:end]
        if not cols_names:
            continue
        cols = st.columns(len(cols_names))
        for i, col_name in enumerate(cols_names):
            with cols[i]:
                key = f"search_{col_name}"
                if st.session_state.reset_search and key in st.session_state:
                    st.session_state[key] = ""
                if key not in st.session_state:
                    st.session_state[key] = ""
                st.text_input(col_name, value=st.session_state[key],
                              placeholder=f"输入{col_name}", key=key)

    if reset_btn:
        add_op_log("info", "重置搜索条件")
        st.session_state.reset_search = True
        st.session_state.show_search_results = False
        st.session_state.search_result_df = pd.DataFrame()
        st.rerun()

    if search_btn:
        st.session_state.reset_search = False
        search_values = {col: st.session_state.get(f"search_{col}", "")
                         for col in search_columns}
        conditions, params = [], {}
        for col_name, value in search_values.items():
            value = value.strip()
            if value:
                conditions.append(f'"{col_name}"::text LIKE :{col_name}')
                params[col_name] = f'%{value}%'

        if conditions:
            try:
                schema = st.session_state.pg_schema
                table_name = st.session_state.selected_table
                where_clause = " AND ".join(conditions)
                query_sql = (f'SELECT * FROM "{schema}"."{table_name}" '
                             f'WHERE {where_clause} LIMIT 1000')
                add_op_log("sql", "执行条件搜索", sql=query_sql)

                engine = _make_engine(*_conn_params())
                with engine.connect() as conn:
                    df_result = pd.read_sql(text(query_sql), conn, params=params)
                df_result = df_result.reset_index(drop=True)
                st.session_state.search_result_df = df_result
                st.session_state.show_search_results = True
                add_op_log("success", f"搜索命中 · {len(df_result)} 条")
            except Exception as e:
                add_op_log("error", "搜索失败", str(e))
                st.error(f"搜索失败：{str(e)}")
                st.session_state.show_search_results = False
        else:
            add_op_log("warning", "搜索时未输入任何条件")
            st.warning("请至少输入一个搜索条件")

    # 显示区
    current_df, key_prefix = None, "main"
    if st.session_state.show_search_results and not st.session_state.search_result_df.empty:
        st.markdown(f"**📊 搜索结果（{len(st.session_state.search_result_df)} 条）**")
        current_df = st.session_state.search_result_df
        key_prefix = "search"
    elif (not st.session_state.show_search_results) and (not st.session_state.table_data.empty):
        current_df = st.session_state.table_data
        key_prefix = "main"
    elif st.session_state.show_search_results and st.session_state.search_result_df.empty:
        st.info("未找到匹配的记录")

    if current_df is not None:
        _render_editable_table(current_df, pk_cols, key_prefix, del_btn)

    if st.session_state.get("confirm_delete_main") or st.session_state.get("confirm_delete_search"):
        pending = st.session_state.pending_delete
        if pending:
            confirm_delete_dialog(pending)
        else:
            st.session_state.confirm_delete_main = False
            st.session_state.confirm_delete_search = False

    if "_del_toast" in st.session_state:
        toast = st.session_state.pop("_del_toast")
        (st.success if toast.startswith("✅") else st.error)(toast)


def _render_editable_table(current_df, pk_cols, key_prefix, del_btn):
    df_show = current_df.copy().reset_index(drop=True)
    for col in df_show.columns:
        df_show[col] = df_show[col].apply(_to_display_str).astype("string")
    if "选择" not in df_show.columns:
        df_show.insert(0, "选择", False)

    column_config = {"选择": st.column_config.CheckboxColumn(
        "☑", help="勾选要删除的行", default=False, width="small")}
    for col in df_show.columns:
        if col == "选择":
            continue
        if col in pk_cols:
            column_config[col] = st.column_config.TextColumn(
                f"🔑 {col}", help="主键（不可修改）", disabled=True, width="medium")
        else:
            column_config[col] = st.column_config.TextColumn(
                col, help="可编辑，修改后自动写回数据库", disabled=False, width="medium")

    editor_key = f"editor_{key_prefix}_{st.session_state.selected_table}"
    edited_df = st.data_editor(
        df_show, use_container_width=True,
        height=calc_editor_height(df_show), key=editor_key,
        column_config=column_config, hide_index=True)

    selected_mask = edited_df["选择"] == True
    selected_count = int(selected_mask.sum())
    if selected_count > 0:
        st.info(f"✅ 已勾选 {selected_count} 行")

    if pk_cols and not st.session_state.get("confirm_delete_main") \
            and not st.session_state.get("confirm_delete_search"):
        cur_fp = _df_fingerprint(edited_df)
        saved_fp = st.session_state.save_fingerprints.get(editor_key, "")
        if cur_fp != saved_fp:
            has_change, ok, msg = auto_save_edited_rows(
                df_orig=df_show, df_edit=edited_df,
                schema_df=st.session_state.schema_df,
                schema=st.session_state.pg_schema,
                table=st.session_state.selected_table)
            if has_change and ok:
                add_op_log("success", msg)
                st.toast(f"✅ {msg}", icon="✅")
                new_data = edited_df.drop(columns=["选择"], errors="ignore").copy()
                if key_prefix == "search":
                    st.session_state.search_result_df = new_data
                else:
                    st.session_state.table_data = new_data
                st.session_state.save_fingerprints[editor_key] = cur_fp
            elif has_change and not ok:
                st.toast(f"❌ 自动保存失败：{msg}", icon="❌")
                st.error(f"❌ 自动保存失败：{msg}")

    if del_btn and selected_count > 0:
        indices = edited_df.index[selected_mask].tolist()
        st.session_state.pending_delete = {
            "df_original": df_show, "indices": indices,
            "pk_cols": pk_cols, "key_prefix": key_prefix}
        st.session_state[f"confirm_delete_{key_prefix}"] = True
        st.rerun()


# ===================== 分区：SQL 查询 =====================
def render_sql_panel():
    st.divider()
    st.markdown("### 📝 SQL查询")

    sql_tpl_df = load_sql_templates(SQL_XLS_PATH)
    is_tpl_mode = False
    selected_tpl = "— 手动输入 —"
    param_values = []

    if not sql_tpl_df.empty:
        template_names = ["— 手动输入 —"] + sql_tpl_df["col0"].astype(str).tolist()
        if st.session_state.sql_tpl_selected not in template_names:
            first = sql_tpl_df["col0"].astype(str).iloc[0].strip()
            st.session_state.sql_tpl_selected = first if first else "— 手动输入 —"

        tpl_idx = template_names.index(st.session_state.sql_tpl_selected)

        # 预取参数信息
        preview_tpl = st.session_state.sql_tpl_selected
        preview_pc, preview_pl = 0, []
        if preview_tpl != "— 手动输入 —":
            prow = sql_tpl_df[sql_tpl_df["col0"].astype(str) == preview_tpl].iloc[0]
            preview_pc = get_template_param_count(prow, sql_tpl_df)
            preview_pl = get_template_param_labels(prow, sql_tpl_df, preview_pc)

        weights = [1.4] + [1] * preview_pc if preview_pc > 0 else [1]
        tpl_cols = st.columns(weights, vertical_alignment="bottom")

        with tpl_cols[0]:
            selected_tpl = st.selectbox("📚 SQL模板", options=template_names,
                                        index=tpl_idx, key="sql_tpl_selector")

        # 首次进入自动填充 SQL
        if selected_tpl != "— 手动输入 —" and not st.session_state.get("sql_textarea", "").strip():
            _r = sql_tpl_df[sql_tpl_df["col0"].astype(str) == selected_tpl].iloc[0]
            _init_sql = str(_r.get("col1", ""))
            st.session_state.sql_text = _init_sql
            st.session_state["sql_textarea"] = _init_sql

        # 参数框
        if preview_pc > 0:
            for i in range(preview_pc):
                with tpl_cols[i + 1]:
                    pkey = f"sql_param_{i}_{selected_tpl}"
                    if pkey not in st.session_state:
                        st.session_state[pkey] = ""
                    label = preview_pl[i] if i < len(preview_pl) else f"参数{i}"
                    v = st.text_input(f"{label} ({{{i}}})",
                                      value=st.session_state[pkey],
                                      key=pkey, placeholder=f"替换 {{{i}}}")
                    param_values.append(v)

        # 切换模板
        if selected_tpl != st.session_state.sql_tpl_selected:
            st.session_state.sql_tpl_selected = selected_tpl
            for k in list(st.session_state.keys()):
                if k.startswith("sql_param_"):
                    del st.session_state[k]
            if selected_tpl != "— 手动输入 —":
                r = sql_tpl_df[sql_tpl_df["col0"].astype(str) == selected_tpl].iloc[0]
                new_sql = str(r.get("col1", ""))
                st.session_state.sql_text = new_sql
                st.session_state["sql_textarea"] = new_sql
            else:
                st.session_state.sql_text = ""
                st.session_state["sql_textarea"] = ""
            st.session_state.sql_tpl_result = pd.DataFrame()
            st.session_state.sql_tpl_executed = False
            st.session_state.sql_last_processed = ""
            st.session_state.sql_result_edit_fingerprint = ""
            st.rerun()

        if selected_tpl != "— 手动输入 —":
            is_tpl_mode = True
            row = sql_tpl_df[sql_tpl_df["col0"].astype(str) == selected_tpl].iloc[0]
            if get_template_param_count(row, sql_tpl_df) == 0:
                st.caption("ℹ️ 该模板无参数")
    else:
        if os.path.exists(SQL_XLS_PATH):
            st.warning("⚠️ sql.xls 格式不正确（至少需要两列：名称、SQL）")
        else:
            st.caption(f"ℹ️ 未找到模板文件 `{SQL_XLS_PATH}`，可手动输入 SQL")

    c_sql, c_exec = st.columns([5, 0.8])
    with c_sql:
        if "sql_textarea" not in st.session_state:
            st.session_state["sql_textarea"] = st.session_state.sql_text
        sql_input = st.text_area(
            "输入SQL", height=80,
            placeholder="SELECT * FROM your_table LIMIT 10",
            key="sql_textarea", label_visibility="collapsed")
    with c_exec:
        st.write("")
        if is_tpl_mode:
            exec_btn = st.button("🔍 查询", type="primary",
                                 use_container_width=True, key="btn_sql_tpl_query")
        else:
            exec_btn = st.button("▶ 执行", type="primary",
                                 use_container_width=True, key="btn_sql_manual_exec")

    if exec_btn and sql_input.strip():
        _execute_sql(sql_input, is_tpl_mode, selected_tpl, param_values)

    if st.session_state.sql_tpl_executed and not st.session_state.sql_tpl_result.empty:
        _render_sql_result_editable(st.session_state.sql_tpl_result)


def _execute_sql(sql_input, is_tpl_mode, selected_tpl, param_values):
    final_sql = sql_input
    bind_params = None
    if is_tpl_mode and param_values:
        final_sql, err, bind_params = apply_sql_params(sql_input, param_values)
        if err:
            st.error(f"❌ 参数替换失败：{err}")
            add_op_log("error", "参数替换失败", err)
            st.stop()
        mode_desc = "绑定参数模式（%s）" if bind_params is not None else "字符串拼接模式（{n} 已加引号）"
        add_op_log("info", f"模板参数替换完成 · {selected_tpl}",
                   f"参数={param_values} | {mode_desc}")

    with st.expander("🔎 替换后的 SQL（点击展开核对）", expanded=True):
        st.code(final_sql, language="sql")
        if bind_params is not None:
            st.caption(f"🔗 绑定参数（按顺序）：{list(bind_params)}")

    try:
        processed_sql = final_sql if bind_params is not None else \
            auto_add_pg_schema(final_sql, st.session_state.pg_schema)

        st.session_state.sql_last_processed = processed_sql
        add_op_log("sql", f"执行SQL · {selected_tpl}", sql=processed_sql)

        engine = _make_engine(*_conn_params())
        with engine.connect() as conn:
            if bind_params is not None:
                df_result = pd.read_sql(text(processed_sql), conn, params=bind_params)
            else:
                df_result = pd.read_sql(text(processed_sql), conn)

        add_op_log("success",
                   f"SQL 执行 · {len(df_result)} 行" if not df_result.empty else "SQL 执行 · 空结果")
        st.session_state.sql_result_edit_fingerprint = ""
        st.session_state.sql_tpl_result = df_result
        st.session_state.sql_tpl_executed = True
    except Exception as e:
        add_op_log("error", "SQL 执行失败", str(e))
        st.error(f"❌ {str(e)}")
        st.session_state.sql_tpl_executed = False
        st.session_state.sql_tpl_result = pd.DataFrame()


def _render_sql_result_editable(df_result):
    if df_result.empty:
        st.info("空结果")
        return

    st.success(f"✅ {len(df_result)} 条")

    with st.expander("⚙️ 回写配置（编辑后自动 UPDATE 数据库）", expanded=False):
        table_opts = st.session_state.table_list or []
        default_tbl = st.session_state.sql_result_target_table
        if default_tbl not in table_opts:
            _, guess = extract_first_table_from_sql(st.session_state.sql_last_processed)
            default_tbl = guess if guess in table_opts else (table_opts[0] if table_opts else "")

        all_cols = list(df_result.columns)
        c_tbl, c_pk, c_edit = st.columns([1, 1.4, 1.4])
        with c_tbl:
            tbl_options = [""] + table_opts
            idx = tbl_options.index(default_tbl) if default_tbl in tbl_options else 0
            target_table = st.selectbox("🎯 目标表", tbl_options, index=idx,
                                        key="sql_result_target_table_selector",
                                        help="编辑后 UPDATE 的目标表")
            st.session_state.sql_result_target_table = target_table
        with c_pk:
            default_pk = st.session_state.sql_result_pk_cols or []
            if not default_pk:
                if target_table and st.session_state.selected_table == target_table:
                    default_pk = get_primary_keys(st.session_state.schema_df)
                if not default_pk:
                    default_pk = [c for c in all_cols
                                  if str(c).lower() in ("id", "pk", "code")
                                  or str(c).lower().endswith("_id")
                                  or str(c).lower().endswith("_code")][:2]
            pk_sel = st.multiselect("🔑 主键列（用于 WHERE 定位）",
                                    options=all_cols,
                                    default=[c for c in default_pk if c in all_cols],
                                    key="sql_result_pk_multiselect")
            st.session_state.sql_result_pk_cols = pk_sel
        with c_edit:
            default_edit = [c for c in all_cols if c not in pk_sel]
            edit_sel = st.multiselect("✏️ 可编辑列", options=all_cols,
                                      default=st.session_state.sql_result_editable_cols or default_edit,
                                      key="sql_result_edit_multiselect")
            st.session_state.sql_result_editable_cols = edit_sel

        if not target_table or not pk_sel:
            st.warning("⚠️ 未选择目标表或主键列 → 表格只读")
            can_edit = False
        else:
            can_edit = True
            st.caption(f"✏️ 编辑以下列会 UPDATE 到 **{st.session_state.pg_schema}.{target_table}**：{edit_sel or '（未选）'}")

    df_show = df_result.copy().reset_index(drop=True)
    for col in df_show.columns:
        df_show[col] = df_show[col].apply(_to_display_str).astype("string")

    column_config = {}
    for col in df_show.columns:
        if can_edit and col in edit_sel:
            column_config[col] = st.column_config.TextColumn(
                col, help="可编辑，修改后自动写回数据库", disabled=False, width="medium")
        elif col in pk_sel:
            column_config[col] = st.column_config.TextColumn(
                f"🔑 {col}", help="主键（不可修改）", disabled=True, width="medium")
        else:
            column_config[col] = st.column_config.TextColumn(
                col, help="只读", disabled=True, width="medium")

    key_sig = hashlib.md5(
        (str(tuple(df_show.columns.tolist())) + "|" + str(len(df_show))).encode("utf-8")
    ).hexdigest()[:10]
    editor_key = f"sql_result_editor_{key_sig}"

    edited_df = st.data_editor(
        df_show, use_container_width=True,
        height=calc_editor_height(df_show), key=editor_key,
        column_config=column_config, hide_index=True, disabled=not can_edit)

    if can_edit and edit_sel:
        fp = _df_fingerprint(edited_df)
        saved_fp = st.session_state.sql_result_edit_fingerprint
        orig_fp = _df_fingerprint(df_show)
        if fp != orig_fp and fp != saved_fp:
            has_change, ok, msg, new_df = auto_update_sql_rows(
                df_orig=df_show, df_edit=edited_df,
                table=target_table, pk=pk_sel, editable=edit_sel,
                schema=st.session_state.pg_schema)
            if has_change and ok:
                add_op_log("success", msg)
                st.toast(f"✅ {msg}", icon="✅")
                st.session_state.sql_tpl_result = new_df
                st.session_state.sql_tpl_executed = True
                st.session_state.sql_result_edit_fingerprint = fp
                time.sleep(0.15)
                st.rerun()
            elif has_change and not ok:
                add_op_log("error", "SQL结果回写失败", msg)
                st.toast(f"❌ 回写失败：{msg}", icon="❌")
                st.error(f"❌ 回写失败：{msg}")
        elif fp == saved_fp and fp != orig_fp:
            st.caption("✅ 已同步到数据库")


def extract_first_table_from_sql(sql):
    if not sql:
        return None, None
    m = re.search(r'\bFROM\s+([`"\w]+(?:\.[`"\w]+)?)', sql, re.IGNORECASE)
    if not m:
        return None, None
    full = m.group(1).strip('`"')
    if "." in full:
        parts = full.split(".")
        return parts[0].strip('"'), parts[1].strip('"')
    return None, full.strip('"')


# ===================== 分区：底部面板 =====================
def render_footer_panels():
    st.divider()
    with st.expander("📊 crm.sql 文件", expanded=False):
        sql_file_path = os.path.join("sql", "crm.sql")
        if os.path.exists(sql_file_path):
            try:
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.markdown(f'<div class="sqlfile">{content}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ 读取文件失败: {str(e)}")
        else:
            st.markdown(
                f'<div class="sqlfile"><div class="sqlfile-empty">⚠️ 文件不存在: {sql_file_path}</div></div>',
                unsafe_allow_html=True)

    with st.expander("📋 操作日志", expanded=False):
        log_filter = st.selectbox(
            "筛选", options=["全部", "信息", "成功", "警告", "错误", "SQL"],
            key="oplog_filter", label_visibility="collapsed")
        if st.session_state.op_logs:
            fmap = {"全部": None, "信息": "info", "成功": "success",
                    "警告": "warning", "错误": "error", "SQL": "sql"}
            ftype = fmap.get(log_filter)
            logs = st.session_state.op_logs
            if ftype:
                logs = [log for log in logs if log['type'] == ftype]
            if not logs:
                st.info(f"📭 暂无 {log_filter} 类型的日志")
            else:
                st.markdown(render_op_logs(logs), unsafe_allow_html=True)
        else:
            st.info("📭 暂无操作日志")


# ===================== 主流程 =====================
render_connection_bar()

# 初始化加载
if not st.session_state.initialized and not st.session_state.loading:
    st.session_state.loading = True
    with st.spinner("🔄 正在连接数据库..."):
        success = quick_connect_and_load()
    st.session_state.loading = False
    if success:
        st.rerun()

if st.session_state.loading:
    st.info("⏳ 正在加载数据，请稍候...")
    st.stop()

# 连接参数变化检测
current_params = (st.session_state.pg_host, st.session_state.pg_db)
if st.session_state.last_params is None:
    st.session_state.last_params = current_params
elif current_params != st.session_state.last_params:
    add_op_log("warning", "连接参数变化，重置")
    st.session_state.connection_attempted = False
    st.session_state.initialized = False
    st.session_state.last_params = current_params
    st.session_state.db_list_fetched = False
    _reset_table_state()
    st.rerun()

if not st.session_state.initialized:
    st.warning("⏳ 正在初始化连接...")
    st.stop()

if not st.session_state.table_list:
    st.warning("当前数据库没有数据表")
    st.stop()

render_table_selector()
st.divider()
render_table_viewer()
render_sql_panel()
render_footer_panels()