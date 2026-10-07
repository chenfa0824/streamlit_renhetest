import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import io
import requests
import json
import re

# 设置页面配置
st.set_page_config(
    page_title="API调用工具",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============ 压缩顶部空白，让标题上移 ============
st.markdown("""
    <style>
        /* 主内容区顶部内边距 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        /* 头部区域高度 */
        header[data-testid="stHeader"] {
            height: 0rem !important;
        }
        /* 隐藏顶部装饰条 */
        div[data-testid="stDecoration"] {
            display: none !important;
        }
        /* 标题上边距 */
        h1 {
            margin-top: -1rem !important;
            padding-top: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)
# ============ 压缩顶部空白结束 ============

# ============ 常量配置 ============
DEFAULT_FILE = "hrm.xlsx"
DEFAULT_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoiMSIsInVzZXJfa2V5IjoiZGQ2ZGI0YzgtMWRiMi00OTQ0LTk3MTQtMzU1NjAyYzcxZTVkIiwic291cmNldHlwZSI6MSwidXNlcm5hbWUiOiJhZG1pbiJ9.FKmRHIQXvxt8oya_YQEtTPYjmNrLqmOa8QP2yVcZiixi5sQdRsRu8O6GFRSOrprYCGHR0xsQlXuGav8J9ZIihw"


# 初始化session_state
def init_session_state():
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None
    if 'file_loaded' not in st.session_state:
        st.session_state.file_loaded = False
    if 'current_file' not in st.session_state:
        st.session_state.current_file = DEFAULT_FILE
    if 'file_history' not in st.session_state:
        st.session_state.file_history = []
    if 'save_count' not in st.session_state:
        st.session_state.save_count = 0
    if 'file_exists' not in st.session_state:
        st.session_state.file_exists = False
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None
    if 'api_response' not in st.session_state:
        st.session_state.api_response = None
    if 'search_keyword' not in st.session_state:
        st.session_state.search_keyword = ""
    if 'filtered_options' not in st.session_state:
        st.session_state.filtered_options = []
    if 'token' not in st.session_state:
        st.session_state.token = DEFAULT_TOKEN


init_session_state()

# 顶部标题
st.title("🔌 API调用工具")

# ============ 核心功能函数 ============

def check_file_exists(file_path):
    """检查文件是否存在"""
    return os.path.exists(file_path)


def load_excel(file_path):
    """加载Excel文件（自动识别格式）"""
    try:
        if not os.path.exists(file_path):
            return None, f"文件 '{file_path}' 不存在！请确保文件在程序同级目录下。"

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.xls':
            df = pd.read_excel(file_path, engine='xlrd')
        elif file_ext in ['.xlsx', '.xlsm']:
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            return None, f"不支持的文件格式: {file_ext}"

        if df.empty:
            return None, "Excel文件为空！"

        if df.columns.isnull().any():
            df.columns = [f'Column_{i}' if pd.isna(col) else col for i, col in enumerate(df.columns)]

        return df, None
    except Exception as e:
        return None, f"读取文件失败: {str(e)}"


def save_excel(df, file_path):
    """保存数据到Excel文件（自动识别格式）"""
    try:
        if df is None or df.empty:
            return False, "数据为空，无法保存！"

        if os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{file_path}.backup_{timestamp}"
            os.rename(file_path, backup_file)
            st.session_state.file_history.append(backup_file)
            if len(st.session_state.file_history) > 10:
                old_backup = st.session_state.file_history.pop(0)
                if os.path.exists(old_backup):
                    os.remove(old_backup)

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.xls':
            df.to_excel(file_path, index=False, engine='xlwt')
        elif file_ext in ['.xlsx', '.xlsm']:
            df.to_excel(file_path, index=False, engine='openpyxl')
        else:
            return False, f"不支持的文件格式: {file_ext}"

        st.session_state.save_count += 1
        return True, "保存成功！"
    except Exception as e:
        if st.session_state.file_history:
            latest_backup = st.session_state.file_history[-1]
            if os.path.exists(latest_backup):
                os.rename(latest_backup, file_path)
        return False, f"保存失败: {str(e)}"


def export_as(df, export_format):
    """导出为其他格式"""
    try:
        if export_format == 'csv':
            return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'), "csv"
        elif export_format == 'json':
            return df.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8'), "json"
        elif export_format == 'html':
            return df.to_html(index=False).encode('utf-8'), "html"
        return None, None
    except:
        return None, None


def auto_load_file():
    """自动加载默认文件"""
    file_path = DEFAULT_FILE
    if check_file_exists(file_path):
        st.session_state.file_exists = True
        if not st.session_state.file_loaded:
            df, error = load_excel(file_path)
            if df is not None:
                st.session_state.df = df
                st.session_state.edited_df = df.copy()
                st.session_state.file_loaded = True
                st.session_state.current_file = file_path
                return True, None
            return False, error
    else:
        st.session_state.file_exists = False
        return False, f"文件 '{file_path}' 不存在"


def format_json_string(json_str):
    """格式化JSON字符串"""
    if not json_str or pd.isna(json_str):
        return "{}"

    json_str = str(json_str).strip()

    if not json_str:
        return "{}"

    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, ensure_ascii=False)
    except:
        try:
            fixed_str = json_str.replace("'", '"')
            parsed = json.loads(fixed_str)
            return json.dumps(parsed, ensure_ascii=False)
        except:
            return json_str


def parse_headers(headers_str):
    """解析请求头"""
    if not headers_str or pd.isna(headers_str):
        return {}

    headers_str = str(headers_str).strip()
    if not headers_str:
        return {}

    formatted = format_json_string(headers_str)

    try:
        parsed = json.loads(formatted)
        return parsed if isinstance(parsed, dict) else {}
    except:
        return {}


def parse_body(body_str):
    """解析请求体"""
    if not body_str or pd.isna(body_str):
        return {}

    body_str = str(body_str).strip()
    if not body_str:
        return {}

    formatted = format_json_string(body_str)

    try:
        parsed = json.loads(formatted)
        return parsed
    except:
        return body_str


def call_api(method, url, headers_str, body_str, token):
    """调用API接口"""
    try:
        headers_dict = parse_headers(headers_str)

        if token and token.strip():
            has_auth = False
            for key in headers_dict.keys():
                if key.lower() == 'authorization':
                    headers_dict[key] = token.strip()
                    has_auth = True
                    break
            if not has_auth:
                headers_dict['Authorization'] = token.strip()

        body_data = parse_body(body_str)

        if isinstance(body_data, str) and body_data.strip():
            try:
                body_data = json.loads(body_data)
            except:
                pass

        method = method.upper()
        start_time = time.time()

        if method == "GET":
            response = requests.get(url, headers=headers_dict, timeout=30)
        elif method == "POST":
            if isinstance(body_data, dict):
                response = requests.post(url, headers=headers_dict, json=body_data, timeout=30)
            else:
                response = requests.post(url, headers=headers_dict, data=body_data, timeout=30)
        elif method == "PUT":
            if isinstance(body_data, dict):
                response = requests.put(url, headers=headers_dict, json=body_data, timeout=30)
            else:
                response = requests.put(url, headers=headers_dict, data=body_data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers_dict, timeout=30)
        else:
            return None, f"不支持的HTTP方法: {method}"

        elapsed_time = time.time() - start_time
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "elapsed_time": f"{elapsed_time:.2f}s",
            "url": url,
            "method": method
        }
        try:
            result["json_body"] = response.json()
        except:
            pass

        return result, None
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.ConnectionError:
        return None, "连接错误，请检查URL是否正确"
    except Exception as e:
        return None, f"请求失败: {str(e)}"


# ============ 自动加载 ============
if not st.session_state.file_loaded:
    auto_load_file()

# ============ 主界面 ============
if st.session_state.file_loaded and st.session_state.df is not None:

    # Token输入
    st.subheader("🔑 Token配置")
    token_input = st.text_input(
        "Token",
        value=st.session_state.token,
        placeholder="请输入您的Token...",
        key="token_input",
        type="password",
        label_visibility="collapsed"
    )
    if token_input != st.session_state.token:
        st.session_state.token = token_input

    # API调用区域
    st.subheader("🚀 API调用")

    first_column = st.session_state.df.columns[0]
    all_options = st.session_state.df[first_column].dropna().astype(str).tolist()

    col_search, col_button = st.columns([4, 1])
    with col_search:
        search_keyword = st.text_input(
            "搜索接口",
            value=st.session_state.search_keyword,
            placeholder="输入关键词搜索...",
            key="search_input",
            label_visibility="collapsed"
        )

        if search_keyword:
            filtered_options = [opt for opt in all_options if search_keyword.lower() in opt.lower()]
        else:
            filtered_options = all_options

        st.session_state.filtered_options = filtered_options
        display_options = filtered_options[:200]
        total_matches = len(filtered_options)

        if display_options:
            selected_value = st.selectbox("选择接口", display_options, key="api_selector", label_visibility="collapsed")
            if search_keyword and total_matches > 200:
                st.caption(f"显示前200个结果，共 {total_matches} 个匹配")
            elif search_keyword:
                st.caption(f"找到 {total_matches} 个匹配结果")
        else:
            selected_value = None
            st.selectbox("选择接口", ["无匹配结果"], key="api_selector", label_visibility="collapsed")

    with col_button:
        st.write("")
        call_button = st.button("🚀 调用", use_container_width=True, type="primary")

    if selected_value and selected_value != "无匹配结果":
        selected_row = st.session_state.df[st.session_state.df[first_column].astype(str) == selected_value]
        if not selected_row.empty:
            row_data = selected_row.iloc[0]

            with st.expander("📋 请求详情", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("接口", row_data.iloc[0] if len(row_data) > 0 else "N/A")
                with col2:
                    st.metric("方法", row_data.iloc[1] if len(row_data) > 1 else "N/A")
                with col3:
                    st.metric("URL", row_data.iloc[2][:50] + "..." if len(row_data) > 2 and len(
                        str(row_data.iloc[2])) > 50 else str(row_data.iloc[2]) if len(row_data) > 2 else "N/A")
                with col4:
                    st.metric("请求头", "已配置" if len(row_data) > 3 and row_data.iloc[3] else "未配置")

                if len(row_data) > 4 and row_data.iloc[4]:
                    st.text_area("请求体", str(row_data.iloc[4]), height=100, disabled=True)

                if st.session_state.token:
                    st.info(f"Token: {st.session_state.token[:20]}...")

            if call_button:
                method = str(row_data.iloc[1]) if len(row_data) > 1 else "GET"
                url = str(row_data.iloc[2]) if len(row_data) > 2 else ""
                headers = str(row_data.iloc[3]) if len(row_data) > 3 else "{}"
                body = str(row_data.iloc[4]) if len(row_data) > 4 else "{}"

                if not url:
                    st.error("❌ URL不能为空")
                else:
                    with st.spinner(f"正在调用 {method} {url}..."):
                        response, error = call_api(method, url, headers, body, st.session_state.token)

                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.session_state.api_response = response
                            st.success(f"✅ 请求成功！状态码: {response['status_code']}")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("状态码", response['status_code'])
                            with col2:
                                st.metric("耗时", response['elapsed_time'])
                            with col3:
                                st.metric("请求方式", response['method'])

                            st.markdown("**响应体:**")
                            try:
                                if 'json_body' in response:
                                    st.json(response['json_body'])
                                else:
                                    st.code(response['body'],
                                            language="json" if response['body'].startswith('{') or response[
                                                'body'].startswith('[') else "text")
                            except:
                                st.code(response['body'])

                            with st.expander("查看响应头"):
                                st.json(response['headers'])
        else:
            st.warning("⚠️ 未找到选中的行数据")
    elif call_button:
        st.warning("⚠️ 请先选择一个有效的接口")

    # 配置编辑器
    st.subheader("✏️ 配置编辑器")

    col_save, col_export_label, col_export_btn = st.columns([1, 1, 1])
    with col_save:
        if st.button("💾 保存配置", use_container_width=True, type="primary"):
            if st.session_state.edited_df is not None and st.session_state.file_loaded:
                success, msg = save_excel(st.session_state.edited_df, st.session_state.current_file)
                if success:
                    st.session_state.df = st.session_state.edited_df.copy()
                    st.success(f"✅ {msg}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    with col_export_label:
        export_format = st.selectbox("导出格式:", ["CSV", "JSON", "HTML"], key="export_format",
                                     label_visibility="collapsed")

    with col_export_btn:
        if st.button("📥 导出配置", use_container_width=True):
            if st.session_state.edited_df is not None and st.session_state.file_loaded:
                data, ext = export_as(st.session_state.edited_df, export_format.lower())
                if data is not None:
                    file_name = f"api_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                    st.download_button(label="📥 点击下载", data=data, file_name=file_name,
                                       mime="application/octet-stream", key="download_btn")
                else:
                    st.error("❌ 导出失败")

    edited_data = st.data_editor(
        st.session_state.edited_df,
        use_container_width=True,
        height=400,
        num_rows="dynamic",
        key="data_editor",
        column_config={},
        hide_index=False,
        column_order=None
    )
    if not edited_data.equals(st.session_state.edited_df):
        st.session_state.edited_df = edited_data

else:
    # 未加载数据时的界面
    if st.session_state.file_exists:
        st.error("❌ 文件加载失败，请检查文件是否损坏")
    else:
        st.warning(f"""
        ### 📂 未找到配置文件
        请将 Excel 配置文件放在程序同级目录下，并命名为 **`{DEFAULT_FILE}`**

        **支持的文件格式：** .xlsx, .xls, .xlsm
        """)
        files = os.listdir('.')
        excel_files = [f for f in files if f.endswith(('.xlsx', '.xls', '.xlsm'))]
        if excel_files:
            st.write("**当前目录的Excel文件：**")
            st.code('\n'.join(excel_files))
        else:
            st.info("当前目录没有找到任何 Excel 文件")

    with st.expander("📖 使用指南", expanded=True):
        st.markdown(f"""
        ### 🚀 快速开始
        1. 将 Excel 文件命名为 `{DEFAULT_FILE}` 并放在程序同级目录
        2. 程序启动后会自动加载配置文件
        3. 在API调用区域搜索并选择接口，点击调用

        ### 📋 Excel格式要求
        | 列 | 说明 | 示例 |
        |---|---|---|
        | 第1列 | 接口名称 | 获取用户信息 |
        | 第2列 | 请求方法 | GET, POST, PUT, DELETE |
        | 第3列 | 请求URL | https://api.example.com/user |
        | 第4列 | 请求头 (JSON) | {{"Authorization": "Bearer token"}} |
        | 第5列 | 请求体 (JSON) | {{"id": 123}} |
        """)