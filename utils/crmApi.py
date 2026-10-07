import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import io
import requests
import json


# 导入配置文件
from config import CRM_TOKEN

# 设置页面配置
st.set_page_config(
    page_title="API调用工具",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 精简CSS样式 - 移除标题背景，消除顶部空白
st.markdown("""
<style>
    /* 消除 Streamlit 顶部默认留白 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: 0rem !important;
    }
    header[data-testid="stHeader"] {
        height: 0rem;
        background: transparent;
    }
    div[data-testid="stAppViewContainer"] > .main {
        padding-top: 0rem;
    }
    /* 顶部标题 - 无背景 */
    .main-header {
        text-align: center;
        padding: 0;
        margin: 0 0 0.5rem 0;
        background: transparent;
        border-radius: 0;
    }
    .main-header h1 {
        color: #4CAF50;
        margin: 0;
        font-size: 1.8rem;
    }
    .main-header p {
        color: #666;
        margin: 0.2rem 0 0 0;
        font-size: 0.9rem;
    }
    .control-section,.api-section {padding:1.5rem;border-radius:10px;margin-bottom:1rem;}
    .control-section {background:#f8f9fa;border:1px solid #dee2e6;}
    .control-section h3,.api-section h3 {margin-top:0;padding-bottom:0.5rem;}
    .control-section h3 {color:#333;border-bottom:2px solid #4CAF50;}
    .api-section {background:#e3f2fd;border:1px solid #90caf9;}
    .api-section h3 {color:#1565c0;border-bottom:2px solid #42a5f5;}
    .token-section,.variable-section {padding:0.8rem 1rem;border-radius:8px;margin-bottom:1rem;}
    .token-section {background:#fff3cd;border-left:4px solid #ffc107;}
    .variable-section {background:#e8f5e9;border-left:4px solid #4CAF50;}
    .response-box {background:#1e1e1e;color:#d4d4d4;padding:1rem;border-radius:5px;font-family:'Courier New',monospace;max-height:300px;overflow-y:auto;margin-top:0.5rem;}
    .editor-toolbar {display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;padding:0.5rem;background:#f8f9fa;border-radius:5px;}
</style>
""", unsafe_allow_html=True)

# ============ 常量配置 ============
DEFAULT_FILE = "crm.xlsx"

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
        st.session_state.token = CRM_TOKEN
    if 'current_datetime_str' not in st.session_state:
        st.session_state.current_datetime_str = ""
    if 'current_date_str' not in st.session_state:
        st.session_state.current_date_str = ""


init_session_state()

# 获取当前日期
current_date = datetime.now().strftime("%Y-%m-%d")
# 获取当前时间（用于课程时间）
current_time = datetime.now().strftime("%H:%M:%S")
# 获取当前时间的年月日时分秒格式（用于活动名称）
current_datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

st.session_state.current_date = current_date
st.session_state.current_datetime_str = current_datetime_str

# 顶部标题 - 已移动到页面最上方，无背景
st.markdown("""
<div class="main-header">
    <h1>🔌 API调用工具</h1>
</div>
""", unsafe_allow_html=True)


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


def replace_variables(text):
    """替换文本中的所有变量（增强版）"""
    if not text:
        return text

    # 确保是字符串
    if not isinstance(text, str):
        text = str(text)

    # 替换当前时间变量（年月日时分秒）
    if '{{current_datetime}}' in text:
        text = text.replace('{{current_datetime}}', st.session_state.current_datetime_str)
        print(f"🔄 替换时间变量: {{current_datetime}} -> {st.session_state.current_datetime_str}")

    # 替换当前日期变量（年月日）
    if '{{current_date}}' in text:
        text = text.replace('{{current_date}}', st.session_state.current_date_str)
        print(f"🔄 替换日期变量: {{current_date}} -> {st.session_state.current_date_str}")

    return text


def deep_replace_variables(obj):
    """递归替换对象中的所有变量"""
    if isinstance(obj, str):
        return replace_variables(obj)
    elif isinstance(obj, dict):
        return {key: deep_replace_variables(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [deep_replace_variables(item) for item in obj]
    else:
        return obj


def format_json_string(json_str):
    """格式化JSON字符串"""
    if not json_str or pd.isna(json_str):
        return "{}"

    json_str = str(json_str).strip()

    if not json_str:
        return "{}"

    # 先替换变量
    json_str = replace_variables(json_str)

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
    """解析请求头（增强版）"""
    if not headers_str or pd.isna(headers_str):
        return {}

    headers_str = str(headers_str).strip()
    if not headers_str:
        return {}

    # 先替换变量
    headers_str = replace_variables(headers_str)
    print(f"📋 替换后的Headers: {headers_str}")

    # 格式化JSON
    formatted = format_json_string(headers_str)

    try:
        parsed = json.loads(formatted)
        return parsed if isinstance(parsed, dict) else {}
    except:
        return {}


def parse_body(body_str):
    """解析请求体（增强版）"""
    if not body_str or pd.isna(body_str):
        return {}

    body_str = str(body_str).strip()
    if not body_str:
        return {}

    # 先替换变量
    body_str = replace_variables(body_str)
    print(f"📦 替换后的Body: {body_str}")

    # 格式化JSON
    formatted = format_json_string(body_str)

    try:
        parsed = json.loads(formatted)
        # 递归替换解析后的对象中的变量（处理嵌套的JSON字符串）
        return deep_replace_variables(parsed)
    except:
        # 如果解析失败，返回替换变量后的原始字符串
        return body_str


def call_api(method, url, headers_str, body_str, token):
    """调用API接口（增强版）"""
    try:
        print(f"🚀 开始调用API: {method} {url}")
        print(f"📅 当前日期: {st.session_state.current_date_str}")
        print(f"🕐 当前时间: {st.session_state.current_datetime_str}")

        # ✅ 第1步：替换URL中的变量
        url = replace_variables(url) if url else url
        print(f"🌐 替换后的URL: {url}")

        # ✅ 第2步：先替换headers中的变量，再解析
        if headers_str:
            headers_str = replace_variables(str(headers_str))
            print(f"📋 替换后的Headers原始: {headers_str}")

        # ✅ 第3步：先替换body中的变量，再解析
        if body_str:
            body_str = replace_variables(str(body_str))
            print(f"📦 替换后的Body原始: {body_str}")

        # 解析headers
        headers_dict = parse_headers(headers_str)
        print(f"📋 解析后的Headers: {headers_dict}")

        # 如果提供了token，替换Authorization头
        if token and token.strip():
            has_auth = False
            for key in headers_dict.keys():
                if key.lower() == 'authorization':
                    headers_dict[key] = token.strip()
                    has_auth = True
                    break
            if not has_auth:
                headers_dict['Authorization'] = token.strip()
            print(f"🔑 应用Token: {token[:20]}...")

        # 解析body
        body_data = parse_body(body_str)
        print(f"📦 解析后的Body: {body_data}")

        # 如果body_data是字符串，尝试解析为JSON
        if isinstance(body_data, str) and body_data.strip():
            try:
                body_data = json.loads(body_data)
                print(f"📦 Body解析为JSON: {body_data}")
            except:
                pass

        method = method.upper()
        start_time = time.time()

        print(f"📤 最终请求: {method} {url}")
        print(f"📋 最终Headers: {headers_dict}")
        print(f"📦 最终Body: {body_data}")

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

        print(f"✅ 请求完成，状态码: {response.status_code}")
        return result, None
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.ConnectionError:
        return None, "连接错误，请检查URL是否正确"
    except Exception as e:
        return None, f"请求失败: {str(e)}"


def show_variable_info():
    """显示变量信息"""
    st.info(f"📅 当前日期: {st.session_state.current_date_str} | 🕐 当前时间: {st.session_state.current_datetime_str}")
    # st.caption("💡 使用 {{current_date}} 或 {{current_datetime}} 在请求中插入变量")


# ============ 自动加载 ============
if not st.session_state.file_loaded:
    auto_load_file()

# ============ 主界面 ============
if st.session_state.file_loaded and st.session_state.df is not None:
    # 变量显示区域
    # st.markdown('<div class="variable-section">', unsafe_allow_html=True)
    col_var1, col_var2 = st.columns([3, 1])
    with col_var1:
        show_variable_info()
    with col_var2:
        if st.button("🔄 刷新时间", use_container_width=True):
            st.session_state.current_datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.current_date_str = datetime.now().strftime("%Y%m%d")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Token输入区域
    # st.markdown('<div class="token-section">', unsafe_allow_html=True)
    col_token1, col_token2 = st.columns([3, 1])
    with col_token1:
        token_input = st.text_input(
            "🔑 请输入Token",
            value=st.session_state.token,
            placeholder="请输入您的Token...",
            key="token_input",
            type="password"
        )
        if token_input != st.session_state.token:
            st.session_state.token = token_input
    with col_token2:
        st.write("")
        if st.button("🔄 清除Token", use_container_width=True):
            st.session_state.token = ""
            st.rerun()
    # st.markdown('</div>', unsafe_allow_html=True)

    # API调用区域
    # st.markdown('<div class="api-section">', unsafe_allow_html=True)
    # st.markdown("### 🚀 API调用工具")

    first_column = st.session_state.df.columns[0]
    all_options = st.session_state.df[first_column].dropna().astype(str).tolist()

    col_search, col_button = st.columns([3, 1])
    with col_search:
        search_keyword = st.text_input(
            "🔍 输入关键词搜索接口",
            value=st.session_state.search_keyword,
            placeholder="输入接口名称关键词...",
            key="search_input"
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
                st.caption(f"⚠️ 显示前200个结果，共 {total_matches} 个匹配")
            elif search_keyword:
                st.caption(f"✅ 找到 {total_matches} 个匹配结果")
        else:
            selected_value = None
            st.selectbox("选择接口", ["无匹配结果"], key="api_selector", label_visibility="collapsed")
            st.warning("⚠️ 没有找到匹配的接口")

    with col_button:
        st.write("")
        st.write("")
        call_button = st.button("🚀 调用接口", use_container_width=True, type="primary")

    if selected_value and selected_value != "无匹配结果":
        selected_row = st.session_state.df[st.session_state.df[first_column].astype(str) == selected_value]
        if not selected_row.empty:
            row_data = selected_row.iloc[0]

            with st.expander("📋 查看请求详情", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("接口名称", row_data.iloc[0] if len(row_data) > 0 else "N/A")
                with col2:
                    st.metric("请求方法", row_data.iloc[1] if len(row_data) > 1 else "N/A")
                with col3:
                    st.metric("请求URL", row_data.iloc[2] if len(row_data) > 2 else "N/A")
                with col4:
                    st.metric("请求头", "已配置" if len(row_data) > 3 and row_data.iloc[3] else "未配置")
                if len(row_data) > 4:
                    st.text_area("请求体", str(row_data.iloc[4]), height=100, disabled=True)

                # 显示变量替换预览
                if len(row_data) > 2 and row_data.iloc[2]:
                    original_url = str(row_data.iloc[2])
                    replaced_url = replace_variables(original_url)
                    if original_url != replaced_url:
                        st.info(f"📝 URL变量替换: {original_url} → {replaced_url}")

                if len(row_data) > 3 and row_data.iloc[3]:
                    original_headers = str(row_data.iloc[3])
                    replaced_headers = replace_variables(original_headers)
                    if original_headers != replaced_headers:
                        st.info(f"📝 请求头变量替换: {original_headers} → {replaced_headers}")

                if len(row_data) > 4 and row_data.iloc[4]:
                    original_body = str(row_data.iloc[4])
                    replaced_body = replace_variables(original_body)
                    if original_body != replaced_body:
                        st.info(f"📝 请求体变量替换: {original_body} → {replaced_body}")

                if st.session_state.token:
                    st.info(f"🔑 当前Token: {st.session_state.token[:20]}... (已应用)")
                else:
                    st.warning("⚠️ 未配置Token")

            if call_button:
                method = str(row_data.iloc[1]) if len(row_data) > 1 else "GET"
                url = str(row_data.iloc[2]) if len(row_data) > 2 else ""
                headers = str(row_data.iloc[3]) if len(row_data) > 3 else "{}"
                body = str(row_data.iloc[4]) if len(row_data) > 4 else "{}"

                if not url:
                    st.error("❌ URL不能为空，请检查Excel第三列数据")
                else:
                    # 显示详细的变量替换信息
                    with st.expander("📝 变量替换详情", expanded=True):
                        st.info(f"📅 当前日期: {st.session_state.current_date_str}")
                        st.info(f"🕐 当前时间: {st.session_state.current_datetime_str}")

                        st.markdown("**原始数据:**")
                        st.code(f"URL: {url}\nHeaders: {headers}\nBody: {body}")

                        # 显示替换后的数据
                        replaced_url = replace_variables(url)
                        replaced_headers = replace_variables(headers)
                        replaced_body = replace_variables(body)

                        st.markdown("**替换变量后:**")
                        st.code(f"URL: {replaced_url}\nHeaders: {replaced_headers}\nBody: {replaced_body}")

                        # 检查变量是否被正确替换
                        if '{{current_date}}' in replaced_url or '{{current_datetime}}' in replaced_url:
                            st.warning("⚠️ URL中仍有未替换的变量！")
                        if '{{current_date}}' in replaced_headers or '{{current_datetime}}' in replaced_headers:
                            st.warning("⚠️ 请求头中仍有未替换的变量！")
                        if '{{current_date}}' in replaced_body or '{{current_datetime}}' in replaced_body:
                            st.warning("⚠️ 请求体中仍有未替换的变量！")

                        # 尝试格式化并显示JSON
                        try:
                            if headers and headers != "{}":
                                formatted_headers = format_json_string(headers)
                                st.success("✅ 请求头格式化成功")
                                st.json(json.loads(formatted_headers))
                        except Exception as e:
                            st.warning(f"⚠️ 请求头格式化失败: {str(e)}")

                        try:
                            if body and body != "{}":
                                formatted_body = format_json_string(body)
                                st.success("✅ 请求体格式化成功")
                                st.json(json.loads(formatted_body))
                        except Exception as e:
                            st.warning(f"⚠️ 请求体格式化失败: {str(e)}")

                        if st.session_state.token:
                            st.info(f"🔑 应用Token: {st.session_state.token[:20]}...")

                    with st.spinner(f"正在调用 {method} {replaced_url}..."):
                        # 传递原始数据，让call_api内部处理变量替换
                        response, error = call_api(method, url, headers, body, st.session_state.token)

                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.session_state.api_response = response
                            st.success(f"✅ 请求成功！状态码: {response['status_code']}")

                            st.markdown("### 📤 响应结果")
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

                            with st.expander("📋 查看响应头"):
                                st.json(response['headers'])
        else:
            st.warning("⚠️ 未找到选中的行数据")
    elif call_button:
        st.warning("⚠️ 请先选择一个有效的接口")

    st.markdown('</div>', unsafe_allow_html=True)

    # 配置编辑器
    st.subheader("✏️ 配置编辑器")
    st.caption("💡 双击单元格编辑 | 右键菜单更多选项 | 支持添加/删除行")
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
        **当前目录文件列表：**
        """)
        files = os.listdir('.')
        excel_files = [f for f in files if f.endswith(('.xlsx', '.xls', '.xlsm'))]
        if excel_files:
            st.code('\n'.join(excel_files))
        else:
            st.info("当前目录没有找到任何 Excel 文件")

    with st.expander("📖 使用指南", expanded=True):
        st.markdown(f"""
        ### 🚀 快速开始
        1. 将 Excel 文件命名为 `{DEFAULT_FILE}` 并放在程序同级目录
        2. 程序启动后会自动加载配置文件
        3. 在API调用区域搜索并选择接口，点击调用

        ### 📅 变量功能
        - `{{current_date}}` - 当前日期 (格式: YYYYMMDD)
        - `{{current_datetime}}` - 当前时间 (格式: YYYYMMDDHHMMSS)
        - 支持在URL、请求头、请求体中使用
        - 变量会在JSON解析前被替换

        ### 📋 Excel格式要求
        | 列 | 说明 | 示例 |
        |---|---|---|
        | 第1列 | 接口名称 | 获取用户信息 |
        | 第2列 | 请求方法 | GET, POST, PUT, DELETE |
        | 第3列 | 请求URL | https://api.example.com/user?date={{current_date}} |
        | 第4列 | 请求头 (JSON) | {{"Authorization": "Bearer token"}} |
        | 第5列 | 请求体 (JSON) | {{"id": 123, "date": "{{current_date}}", "time": "{{current_datetime}}"}} |
        """)