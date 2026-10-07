import streamlit as st
import requests
import json
from datetime import datetime
import psycopg2
import psycopg2.extras
import logging

# 导入配置文件
from config import CRM_TOKEN, DB_CONFIG, DEFAULT_SCHEMA,chufeng_upsertActivity

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 页面配置 - 改为宽布局
st.set_page_config(
    page_title="创建楚凤活动",
    page_icon="📝",
    layout="wide"
)

# ==================== 自定义CSS：统一按钮为深蓝色 (#004A99) ====================
st.markdown("""
<style>
    /* 所有按钮统一深蓝色 */
    .stButton > button {
        background-color: #004A99 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }

    /* 按钮悬停效果 - 颜色加深 */
    .stButton > button:hover {
        background-color: #003a7a !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(0, 74, 153, 0.4) !important;
        border: none !important;
        transform: translateY(-1px) !important;
    }

    /* 按钮点击/激活效果 */
    .stButton > button:active {
        background-color: #002b5c !important;
        color: #ffffff !important;
        border: none !important;
        transform: translateY(0px) !important;
    }

    /* 按钮聚焦效果 */
    .stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(0, 74, 153, 0.4) !important;
        border: none !important;
        outline: none !important;
    }

    /* 针对确认删除等特殊按钮 - 保持深蓝色 */
    .stButton > button[kind="primary"] {
        background-color: #004A99 !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #003a7a !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: #004A99 !important;
        color: #ffffff !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #003a7a !important;
        color: #ffffff !important;
    }

    /* 按钮禁用状态 */
    .stButton > button:disabled {
        background-color: #6688aa !important;
        color: #dddddd !important;
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 创建楚凤活动")

# 获取当前日期
current_date = datetime.now().strftime("%Y-%m-%d")
# 获取当前时间（用于课程时间）
current_time = datetime.now().strftime("%H:%M:%S")
# 获取当前时间的年月日时分秒格式（用于活动名称）
current_datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")


# 初始化session_state
if 'category_options' not in st.session_state:
    st.session_state.category_options = []
if 'category_mapping' not in st.session_state:
    st.session_state.category_mapping = {}
if 'selected_category_id' not in st.session_state:
    st.session_state.selected_category_id = None
if 'category_loaded' not in st.session_state:
    st.session_state.category_loaded = False
if 'show_delete_confirm' not in st.session_state:
    st.session_state.show_delete_confirm = False
if 'delete_logs' not in st.session_state:
    st.session_state.delete_logs = []
if 'show_activity_delete_confirm' not in st.session_state:
    st.session_state.show_activity_delete_confirm = False
if 'activity_delete_type' not in st.session_state:
    st.session_state.activity_delete_type = None


# 从数据库加载活动分类数据
def load_activity_categories():
    """从数据库加载活动分类数据"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cur = conn.cursor()

        # 查询 chufeng_activity_category 表的 secondLevel 和 activity_category_id
        cur.execute(f"""
            SELECT activity_category_id, second_level 
            FROM {DEFAULT_SCHEMA}.chufeng_activity_category 
            WHERE second_level IS NOT NULL 
            AND second_level != ''
            ORDER BY second_level
        """)

        results = cur.fetchall()
        cur.close()
        conn.close()

        if results:
            # 构建选项列表和映射
            options = []
            mapping = {}
            for activity_category_id, second_level in results:
                display_name = f"{second_level}"
                options.append(display_name)
                mapping[display_name] = activity_category_id

            st.session_state.category_options = options
            st.session_state.category_mapping = mapping
            st.session_state.category_loaded = True
            return True
        else:
            st.session_state.category_loaded = False
            return False

    except Exception as e:
        logger.error(f"加载活动分类失败: {str(e)}")
        st.session_state.category_loaded = False
        return False


# ==================== 活动分类和Token选择区域（合并到一行） ====================
# 加载活动分类数据（仅在第一次加载时执行）
if not st.session_state.category_loaded:
    with st.spinner("正在加载活动分类数据..."):
        load_activity_categories()

# 创建一行三列布局：分类选择、分类ID显示、Token输入
top_col1, top_col2 = st.columns([2, 2])

with top_col1:
    # 显示加载状态
    if st.session_state.category_loaded and st.session_state.category_options:
        # 下拉选择框
        selected_category_display = st.selectbox(
            "选择活动分类 (secondLevel)",
            options=st.session_state.category_options,
            index=0 if st.session_state.category_options else None,
            help="从下拉列表中选择活动分类，系统将自动获取对应的分类ID"
        )

        # 根据选择的分类获取对应的ID
        if selected_category_display:
            st.session_state.selected_category_id = st.session_state.category_mapping.get(selected_category_display)
    elif not st.session_state.category_loaded:
        st.warning("⚠️ 加载活动分类失败，请检查数据库连接")
        if st.button("🔄 重新加载分类数据"):
            with st.spinner("正在重新加载..."):
                st.session_state.category_loaded = False
                load_activity_categories()
                st.rerun()
    else:
        st.info("ℹ️ 暂无活动分类数据")

with top_col2:
    token = st.text_input(
        "请输入Token",
        type="password",
        placeholder="请输入您的认证Token",
        value=CRM_TOKEN,
        help="Token将用于接口认证"
    )

# 日期和时间信息显示（单独一行）
info_col1, info_col2 = st.columns(2)
with info_col1:
    st.info(f"📅 当前日期: {current_date}")
with info_col2:
    st.info(f"🕐 当前时间戳: {current_datetime_str}")

# 创建按钮 - 使用全宽
create_button = st.button(
    "创建楚凤活动",
    use_container_width=True
)

# 显示请求参数（可折叠）
with st.expander("查看请求参数"):
    st.json({
        "activityId": "",
        "activityCategoryId": st.session_state.selected_category_id if st.session_state.selected_category_id else "请从下拉框选择",
        "activityName": f"楚风活动{current_datetime_str}",
        "startDate": current_date,
        "endDate": current_date,
        "lecturer": "陈发123",
        "quota": 3,
        "closeDate": current_date,
        "coverUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415725506_1.jpeg",
        "detailUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415728971_2.png",
        "courseList": [
            {
                "courseId": "",
                "activityId": "",
                "courseName": f"课程名称{current_datetime_str}",
                "courseNo": 1,
                "mode": "线下",
                "lecturer": f"老师名称{current_datetime_str}",
                "lectureDate": current_date,
                "startTime": current_time,
                "endTime": current_time,
                "location": "地址"
            }
        ],
        "registerPage": "{\"top\":{\"bottom\":100,\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg\"},\"form\":[{\"type\":1,\"placeholder\":\"请输入手机号\",\"required\":1,\"label\":\"手机\",\"options\":[],\"id\":\"1\"}],\"bottom\":{\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png\",\"top\":100},\"btnList\":[{\"btType\":\"1\",\"url\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png\",\"locationType\":\"2\",\"width\":100,\"height\":100,\"left\":100,\"bottom\":100}]}",
        "registerPageForm": {
            "top": {
                "bottom": 100,
                "imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg"
            },
            "form": [
                {
                    "type": 1,
                    "placeholder": "请输入手机号",
                    "required": 1,
                    "label": "手机",
                    "options": [],
                    "id": "1"
                }
            ],
            "bottom": {
                "imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png",
                "top": 100
            },
            "btnList": [
                {
                    "btType": "1",
                    "url": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png",
                    "locationType": "2",
                    "width": 100,
                    "height": 100,
                    "left": 100,
                    "bottom": 100
                }
            ]
        },
        "status": 1
    })

# 点击按钮后的处理逻辑
if create_button:
    # 验证Token是否已输入
    if not token:
        st.error("❌ 请先输入Token")
        st.stop()

    # 验证是否选择了活动分类
    if not st.session_state.selected_category_id:
        st.error("❌ 请先选择活动分类")
        st.stop()

    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token
    }

    # 构建请求体 - 使用当前日期时间格式和选择的分类ID
    payload = {
        "activityId": "",
        "activityCategoryId": st.session_state.selected_category_id,
        "activityName": f"楚风活动{current_datetime_str}",
        "startDate": current_date,
        "endDate": current_date,
        "lecturer": "陈发123",
        "quota": 3,
        "closeDate": current_date,
        "coverUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415725506_1.jpeg",
        "detailUrl": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415728971_2.png",
        "courseList": [
            {
                "courseId": "",
                "activityId": "",
                "courseName": "课程123",
                "courseNo": 1,
                "mode": "线下",
                "lecturer": "老师名字",
                "lectureDate": current_date,
                "startTime": current_time,
                "endTime": current_time,
                "location": "地址"
            }
        ],
        "registerPage": "{\"top\":{\"bottom\":100,\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg\"},\"form\":[{\"type\":1,\"placeholder\":\"请输入手机号\",\"required\":1,\"label\":\"手机\",\"options\":[],\"id\":\"1\"}],\"bottom\":{\"imgPath\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png\",\"top\":100},\"btnList\":[{\"btType\":\"1\",\"url\":\"https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png\",\"locationType\":\"2\",\"width\":100,\"height\":100,\"left\":100,\"bottom\":100}]}",
        "registerPageForm": {
            "top": {
                "bottom": 100,
                "imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415752564_1.jpeg"
            },
            "form": [
                {
                    "type": 1,
                    "placeholder": "请输入手机号",
                    "required": 1,
                    "label": "手机",
                    "options": [],
                    "id": "1"
                }
            ],
            "bottom": {
                "imgPath": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415770755_2.png",
                "top": 100
            },
            "btnList": [
                {
                    "btType": "1",
                    "url": "https://renhe-platform-pre.oss-cn-shanghai.aliyuncs.com/2026-09-03/1788415777160_icon.png",
                    "locationType": "2",
                    "width": 100,
                    "height": 100,
                    "left": 100,
                    "bottom": 100
                }
            ]
        },
        "status": 1
    }

    # 显示请求信息
    with st.spinner("正在创建楚凤活动，请稍候..."):
        try:
            # 发送POST请求
            response = requests.post(
                url=chufeng_upsertActivity,
                headers=headers,
                json=payload,
                timeout=30
            )

            # 处理响应
            st.subheader("📊 响应结果")

            # 显示状态码
            st.info(f"**状态码:** {response.status_code}")

            # 尝试解析JSON响应
            try:
                response_data = response.json()
                st.json(response_data)

                # 根据状态码显示成功或失败信息
                if response.status_code == 200:
                    st.success("✅ 楚凤活动创建成功！")

                    # 如果返回的msg中包含activity_id，自动填充到查询输入框
                    if isinstance(response_data, dict) and "msg" in response_data:
                        activity_id = response_data["msg"]
                        # 保存到session_state以便后续使用
                        st.session_state['last_activity_id'] = activity_id
                        st.info(f"📌 活动ID: {activity_id}，可使用下方查询功能查看详情")
                else:
                    st.error(f"❌ 请求失败，状态码: {response.status_code}")

                    # 尝试显示错误信息
                    if isinstance(response_data, dict):
                        if "msg" in response_data:
                            st.warning(f"**错误信息:** {response_data['msg']}")
                        elif "message" in response_data:
                            st.warning(f"**错误信息:** {response_data['message']}")
            except json.JSONDecodeError:
                # 如果响应不是JSON格式，显示原始文本
                st.text(response.text)
                if response.status_code == 200:
                    st.success("✅ 请求成功（响应非JSON格式）")
                else:
                    st.error(f"❌ 请求失败，状态码: {response.status_code}")

        except requests.exceptions.Timeout:
            st.error("⏰ 请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            st.error("🔌 网络连接失败，请检查网络或接口地址")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 请求异常: {str(e)}")
        except Exception as e:
            st.error(f"❌ 未知错误: {str(e)}")

# ==================== 🗑️ 删除活动记录（放在创建活动下面） ====================
st.divider()
st.subheader("🗑️ 删除活动记录")

# 获取当前选中的schema
current_schema = DEFAULT_SCHEMA

# 活动ID输入框
activity_id_for_delete = st.text_input(
    "活动ID",
    value=st.session_state.get('last_activity_id', '2095397849346129920'),
    placeholder="请输入活动ID，例如: 2095397849346129920",
    help="输入要删除报名/签到记录的活动ID",
    key="activity_id_for_delete"
)

# 两列布局显示两个按钮
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    delete_apply_button = st.button(
        "🗑️ 删除活动报名记录",
        use_container_width=True,
        key="delete_apply_btn"
    )

with col_btn2:
    delete_sign_button = st.button(
        "🗑️ 删除活动签到记录",
        use_container_width=True,
        key="delete_sign_btn"
    )

# 处理删除报名记录按钮点击
if delete_apply_button:
    if not activity_id_for_delete:
        st.error("❌ 请先输入活动ID")
    else:
        st.session_state.show_activity_delete_confirm = True
        st.session_state.activity_delete_type = "apply"
        st.session_state.activity_id_to_delete = activity_id_for_delete
        st.rerun()

# 处理删除签到记录按钮点击
if delete_sign_button:
    if not activity_id_for_delete:
        st.error("❌ 请先输入活动ID")
    else:
        st.session_state.show_activity_delete_confirm = True
        st.session_state.activity_delete_type = "sign"
        st.session_state.activity_id_to_delete = activity_id_for_delete
        st.rerun()

# 显示确认界面
if st.session_state.show_activity_delete_confirm:
    activity_id_to_delete = st.session_state.get('activity_id_to_delete', '')
    delete_type = st.session_state.get('activity_delete_type', '')

    if activity_id_to_delete and delete_type:
        # 根据类型设置标题和SQL
        if delete_type == "apply":
            delete_title = "活动报名记录"
            delete_sql = f"DELETE FROM {current_schema}.chufeng_activity_apply WHERE activity_id = '{activity_id_to_delete}'"
            table_name = "chufeng_activity_apply"
        else:  # sign
            delete_title = "活动签到记录"
            delete_sql = f"DELETE FROM {current_schema}.chufeng_activity_sign WHERE activity_id = '{activity_id_to_delete}'"
            table_name = "chufeng_activity_sign"

        st.warning(f"⚠️ 即将删除活动ID为 **{activity_id_to_delete}** 的{delete_title}，请确认！")
        st.info(f"📌 操作Schema: **{current_schema}**")
        st.info(f"📌 操作表: **{table_name}**")

        # 显示将要执行的SQL
        with st.expander("📝 将要执行的SQL语句", expanded=True):
            st.code(delete_sql, language="sql")

        # 确认和取消按钮
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("✅ 确认删除", use_container_width=True, key="confirm_activity_delete_btn"):
                # 执行删除操作
                with st.spinner(f"正在删除活动 {activity_id_to_delete} 的{delete_title}..."):
                    try:
                        # 记录日志
                        logs = []
                        logs.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始删除{delete_title}")
                        logs.append(f"📱 活动ID: {activity_id_to_delete}")
                        logs.append(f"📌 Schema: {current_schema}")
                        logs.append(f"📌 表名: {table_name}")

                        # 连接数据库
                        conn = psycopg2.connect(
                            host=DB_CONFIG["host"],
                            port=DB_CONFIG["port"],
                            database=DB_CONFIG["database"],
                            user=DB_CONFIG["user"],
                            password=DB_CONFIG["password"]
                        )
                        cur = conn.cursor()
                        logs.append("✅ 数据库连接成功")

                        # 执行删除SQL
                        logs.append(f"📝 执行SQL: {delete_sql}")

                        if delete_type == "apply":
                            cur.execute(f"DELETE FROM {current_schema}.chufeng_activity_apply WHERE activity_id = %s",
                                        (activity_id_to_delete,))
                        else:  # sign
                            cur.execute(f"DELETE FROM {current_schema}.chufeng_activity_sign WHERE activity_id = %s",
                                        (activity_id_to_delete,))

                        deleted_count = cur.rowcount
                        logs.append(f"✅ 删除记录数: {deleted_count} 条")

                        # 提交事务
                        conn.commit()
                        logs.append(f"✅ 事务提交成功")

                        # 保存日志到session_state
                        st.session_state.delete_logs = logs

                        # 显示删除结果
                        st.subheader("📊 删除结果")

                        if deleted_count > 0:
                            st.success(f"✅ 删除成功！共删除 {deleted_count} 条{delete_title}")
                            st.info(f"📊 影响行数: {deleted_count}")
                        else:
                            st.info(f"ℹ️ 未找到活动ID {activity_id_to_delete} 的{delete_title}，无需删除")

                        # 显示执行日志
                        with st.expander("📋 执行日志", expanded=True):
                            for log in logs:
                                st.text(log)

                        # 关闭连接
                        cur.close()
                        conn.close()
                        logs.append("🔌 数据库连接已关闭")

                        # 重置确认状态
                        st.session_state.show_activity_delete_confirm = False
                        st.session_state.activity_delete_type = None
                        st.session_state.activity_id_to_delete = ''
                        st.rerun()

                    except psycopg2.OperationalError as e:
                        error_msg = f"❌ 数据库连接失败: {str(e)}"
                        st.error(error_msg)
                        st.info("💡 请检查网络连接和数据库配置")
                        st.session_state.delete_logs.append(error_msg)
                    except psycopg2.ProgrammingError as e:
                        error_msg = f"❌ SQL执行错误: {str(e)}"
                        st.error(error_msg)
                        st.info("💡 请确认表是否存在，并检查schema名称是否正确")
                        st.session_state.delete_logs.append(error_msg)
                    except Exception as e:
                        error_msg = f"❌ 删除异常: {str(e)}"
                        st.error(error_msg)
                        st.session_state.delete_logs.append(error_msg)

        with confirm_col2:
            if st.button("❌ 取消删除", use_container_width=True, key="cancel_activity_delete_btn"):
                st.session_state.show_activity_delete_confirm = False
                st.session_state.activity_delete_type = None
                st.session_state.activity_id_to_delete = ''
                st.rerun()

# ==================== 🗑️ 删除老学员数据（放在删除活动记录下面） ====================
st.divider()
st.subheader("🗑️ 删除老学员数据")

# 显示需要执行的SQL语句（折叠面板）
with st.expander("📝 查看需要执行的SQL语句"):
    st.markdown(f"**当前Schema: `{current_schema}`**")
    st.markdown("**删除SQL:**")
    st.code(f"""
-- 1. 删除 account 表数据
DELETE FROM {current_schema}.account WHERE dianhua = '{{mobile}}';

-- 2. 删除 t_student_info 表数据
DELETE FROM {current_schema}.t_student_info WHERE phones = '{{"{{mobile}}"}}';

-- 3. 删除 chufeng_user 表数据
DELETE FROM {current_schema}.chufeng_user WHERE mobile = '{{mobile}}';
    """.replace('{{mobile}}', '{mobile}'), language="sql")

    st.warning("⚠️ 注意：此操作将直接删除数据，请谨慎操作！")

# 手机号输入
mobile_input = st.text_input(
    "手机号",
    value="18792169903",
    placeholder="请输入要删除数据的手机号",
    help="输入需要删除数据的手机号"
)

# 删除按钮 - 点击后显示确认界面
delete_button = st.button(
    "🗑️ 删除老学员数据",
    use_container_width=True
)

if delete_button:
    if not mobile_input:
        st.error("❌ 请先输入手机号")
    else:
        st.session_state.show_delete_confirm = True
        st.session_state.mobile_to_delete = mobile_input
        st.session_state.delete_logs = []  # 清空旧日志
        st.rerun()

# 显示确认界面
if st.session_state.show_delete_confirm:
    mobile_to_delete = st.session_state.get('mobile_to_delete', '')

    if mobile_to_delete:
        st.warning(f"⚠️ 即将删除手机号为 **{mobile_to_delete}** 的学员数据，请确认！")
        st.info(f"📌 操作Schema: **{current_schema}**")

        # 显示将要执行的SQL
        with st.expander("📝 将要执行的SQL语句", expanded=True):
            st.code(f"""
-- 1. 删除 account 表数据
DELETE FROM {current_schema}.account WHERE dianhua = '{mobile_to_delete}';

-- 2. 删除 t_student_info 表数据
DELETE FROM {current_schema}.t_student_info WHERE phones = '{{"{mobile_to_delete}"}}';

-- 3. 删除 chufeng_user 表数据
DELETE FROM {current_schema}.chufeng_user WHERE mobile = '{mobile_to_delete}';
            """, language="sql")

        # 确认和取消按钮
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("✅ 确认删除", use_container_width=True, key="confirm_delete_btn"):
                # 执行删除操作
                with st.spinner(f"正在删除手机号 {mobile_to_delete} 的数据..."):
                    try:
                        # 记录日志
                        logs = []
                        logs.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始删除操作")
                        logs.append(f"📱 手机号: {mobile_to_delete}")
                        logs.append(f"📌 Schema: {current_schema}")

                        # 连接数据库
                        conn = psycopg2.connect(
                            host=DB_CONFIG["host"],
                            port=DB_CONFIG["port"],
                            database=DB_CONFIG["database"],
                            user=DB_CONFIG["user"],
                            password=DB_CONFIG["password"]
                        )
                        cur = conn.cursor()
                        logs.append("✅ 数据库连接成功")

                        # 统计删除记录数
                        deleted_count = 0
                        delete_results = []

                        # 1. 删除 account 表数据
                        sql1 = f"DELETE FROM {current_schema}.account WHERE dianhua = %s"
                        logs.append(f"📝 执行SQL1: {sql1}")
                        logs.append(f"📝 参数: dianhua = {mobile_to_delete}")
                        cur.execute(sql1, (mobile_to_delete,))
                        account_deleted = cur.rowcount
                        deleted_count += account_deleted
                        delete_results.append(f"account 表: 删除 {account_deleted} 条记录")
                        logs.append(f"✅ account表删除: {account_deleted} 条记录")

                        # 2. 删除 t_student_info 表数据
                        phones_json = f'{{"{mobile_to_delete}"}}'
                        sql2 = f"DELETE FROM {current_schema}.t_student_info WHERE phones = %s"
                        logs.append(f"📝 执行SQL2: {sql2}")
                        logs.append(f"📝 参数: phones = {phones_json}")
                        cur.execute(sql2, (phones_json,))
                        student_deleted = cur.rowcount
                        deleted_count += student_deleted
                        delete_results.append(f"t_student_info 表: 删除 {student_deleted} 条记录")
                        logs.append(f"✅ t_student_info表删除: {student_deleted} 条记录")

                        # 3. 删除 chufeng_user 表数据
                        sql3 = f"DELETE FROM {current_schema}.chufeng_user WHERE mobile = %s"
                        logs.append(f"📝 执行SQL3: {sql3}")
                        logs.append(f"📝 参数: mobile = {mobile_to_delete}")
                        cur.execute(sql3, (mobile_to_delete,))
                        chufeng_deleted = cur.rowcount
                        deleted_count += chufeng_deleted
                        delete_results.append(f"chufeng_user 表: 删除 {chufeng_deleted} 条记录")
                        logs.append(f"✅ chufeng_user表删除: {chufeng_deleted} 条记录")

                        # 提交事务
                        conn.commit()
                        logs.append(f"✅ 事务提交成功")
                        logs.append(f"📊 总计删除: {deleted_count} 条记录")

                        # 保存日志到session_state
                        st.session_state.delete_logs = logs

                        # 显示删除结果
                        st.subheader("📊 删除结果")

                        # 显示各表删除情况
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📋 account表", f"{account_deleted} 条")
                        with col2:
                            st.metric("📋 t_student_info表", f"{student_deleted} 条")
                        with col3:
                            st.metric("📋 chufeng_user表", f"{chufeng_deleted} 条")

                        # 显示详细结果
                        if deleted_count > 0:
                            st.success(f"✅ 删除成功！共删除 {deleted_count} 条记录")
                            for result in delete_results:
                                st.info(f"✅ {result}")
                        else:
                            st.info(f"ℹ️ 未找到手机号 {mobile_to_delete} 的相关数据，无需删除")

                        # 显示执行日志
                        with st.expander("📋 执行日志", expanded=True):
                            for log in logs:
                                st.text(log)

                        # 关闭连接
                        cur.close()
                        conn.close()
                        logs.append("🔌 数据库连接已关闭")

                        # 重置确认状态
                        st.session_state.show_delete_confirm = False
                        st.session_state.mobile_to_delete = ''
                        st.rerun()

                    except psycopg2.OperationalError as e:
                        error_msg = f"❌ 数据库连接失败: {str(e)}"
                        st.error(error_msg)
                        st.info("💡 请检查网络连接和数据库配置")
                        st.session_state.delete_logs.append(error_msg)
                    except psycopg2.ProgrammingError as e:
                        error_msg = f"❌ SQL执行错误: {str(e)}"
                        st.error(error_msg)
                        st.info("💡 请确认表是否存在，并检查schema名称是否正确")
                        st.session_state.delete_logs.append(error_msg)
                    except Exception as e:
                        error_msg = f"❌ 删除异常: {str(e)}"
                        st.error(error_msg)
                        st.session_state.delete_logs.append(error_msg)

        with confirm_col2:
            if st.button("❌ 取消删除", use_container_width=True, key="cancel_delete_btn"):
                st.session_state.show_delete_confirm = False
                st.session_state.mobile_to_delete = ''
                st.session_state.delete_logs = []
                st.rerun()

# 显示历史日志（如果有）
if st.session_state.delete_logs:
    with st.expander("📋 历史执行日志", expanded=False):
        for log in st.session_state.delete_logs:
            st.text(log)

# ==================== 页面分隔线 ====================
st.subheader("🔧 数据库查询工具")

# ==================== 数据库查询部分 ====================
# 初始化session_state（数据库相关）
if 'schemas' not in st.session_state:
    st.session_state.schemas = []
if 'selected_schema' not in st.session_state:
    st.session_state.selected_schema = DEFAULT_SCHEMA
if 'tables' not in st.session_state:
    st.session_state.tables = []
if 'selected_table' not in st.session_state:
    st.session_state.selected_table = 't_cloudstorage_file_path'
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# 自动连接数据库（仅在未初始化时执行一次）
if not st.session_state.db_initialized:
    with st.spinner("正在连接数据库..."):
        try:
            # 连接数据库
            conn = psycopg2.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
            cur = conn.cursor()

            # 获取所有Schema
            cur.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
                ORDER BY schema_name
            """)
            schemas = [row[0] for row in cur.fetchall()]

            cur.close()
            conn.close()

            st.session_state.schemas = schemas
            st.session_state.db_connected = True

            # 检查默认Schema是否存在
            if DEFAULT_SCHEMA in schemas:
                st.session_state.selected_schema = DEFAULT_SCHEMA
            elif schemas:
                # 如果默认Schema不存在，选择第一个
                st.session_state.selected_schema = schemas[0]
                st.warning(f"⚠️ 默认Schema '{DEFAULT_SCHEMA}' 不存在，已切换到 '{schemas[0]}'")

            # 加载选中Schema的表
            selected_schema = st.session_state.selected_schema
            if selected_schema in schemas:
                try:
                    conn = psycopg2.connect(
                        host=DB_CONFIG["host"],
                        port=DB_CONFIG["port"],
                        database=DB_CONFIG["database"],
                        user=DB_CONFIG["user"],
                        password=DB_CONFIG["password"]
                    )
                    cur = conn.cursor()

                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (selected_schema,))
                    tables = [row[0] for row in cur.fetchall()]

                    cur.close()
                    conn.close()

                    st.session_state.tables = tables
                    if tables and st.session_state.selected_table not in tables:
                        st.session_state.selected_table = tables[0]
                except Exception as e:
                    st.error(f"❌ 加载表失败: {str(e)}")
            else:
                st.warning(f"⚠️ Schema '{selected_schema}' 不存在，请选择其他Schema")

            st.session_state.db_initialized = True

        except psycopg2.OperationalError as e:
            st.session_state.db_connected = False
            st.session_state.db_initialized = True
            st.error(f"❌ 数据库连接失败: {str(e)}")
            st.info("💡 请检查网络连接和数据库配置")
        except Exception as e:
            st.session_state.db_connected = False
            st.session_state.db_initialized = True
            st.error(f"❌ 连接异常: {str(e)}")

# 使用两列布局显示数据库连接信息和Schema/表选择
col_left, col_right = st.columns([1, 2])

with col_left:
    # 显示数据库连接状态 - 默认折叠
    with st.expander("📊 数据库连接信息", expanded=False):
        st.markdown("**🔌 连接配置**")
        st.markdown(f"- **主机:** `{DB_CONFIG['host']}`")
        st.markdown(f"- **端口:** `{DB_CONFIG['port']}`")
        st.markdown(f"- **数据库:** `{DB_CONFIG['database']}`")
        st.markdown(f"- **用户:** `{DB_CONFIG['user']}`")
        st.markdown(f"- **默认Schema:** `{DEFAULT_SCHEMA}`")
        st.markdown("---")

        st.markdown("**📊 连接状态**")
        if st.session_state.db_connected:
            st.success("✅ 数据库已连接")
            st.metric("📋 Schema数量", len(st.session_state.schemas))
            if st.session_state.tables:
                st.metric("📊 表数量", len(st.session_state.tables))
            st.info(f"📌 当前Schema: `{st.session_state.selected_schema}`")
        else:
            st.error("❌ 数据库未连接")

with col_right:
    # Schema和表选择区域
    if st.session_state.db_connected and st.session_state.schemas:
        col_schema, col_table = st.columns(2)

        with col_schema:
            st.markdown("**📋 选择Schema**")
            # Schema下拉选择（支持搜索）
            current_index = st.session_state.schemas.index(
                st.session_state.selected_schema) if st.session_state.selected_schema in st.session_state.schemas else 0
            selected_schema = st.selectbox(
                "Schema",
                options=st.session_state.schemas,
                index=current_index,
                key="schema_select",
                help="选择要查询的Schema"
            )

            # 如果Schema发生变化，重新加载表
            if selected_schema != st.session_state.selected_schema:
                st.session_state.selected_schema = selected_schema
                st.session_state.tables = []
                st.session_state.selected_table = None
                with st.spinner(f"正在加载Schema '{selected_schema}' 的表..."):
                    try:
                        conn = psycopg2.connect(
                            host=DB_CONFIG["host"],
                            port=DB_CONFIG["port"],
                            database=DB_CONFIG["database"],
                            user=DB_CONFIG["user"],
                            password=DB_CONFIG["password"]
                        )
                        cur = conn.cursor()

                        # 获取当前Schema的所有表
                        cur.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = %s 
                            AND table_type = 'BASE TABLE'
                            ORDER BY table_name
                        """, (selected_schema,))
                        tables = [row[0] for row in cur.fetchall()]

                        cur.close()
                        conn.close()

                        st.session_state.tables = tables
                        if tables:
                            st.session_state.selected_table = tables[0]
                        st.success(f"✅ 找到 {len(tables)} 个表")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 加载表失败: {str(e)}")

        with col_table:
            if st.session_state.tables:
                st.markdown("**📊 选择表**")
                # 表下拉选择（支持搜索）
                current_table_index = st.session_state.tables.index(
                    st.session_state.selected_table) if st.session_state.selected_table in st.session_state.tables else 0
                selected_table = st.selectbox(
                    "表名",
                    options=st.session_state.tables,
                    index=current_table_index,
                    key="table_select",
                    help="选择要查询的表"
                )
                st.session_state.selected_table = selected_table
            else:
                st.warning("⚠️ 当前Schema下没有找到表")
                st.session_state.selected_table = None
    else:
        if not st.session_state.db_connected:
            st.info("💡 正在连接数据库...")

# 查询区域 - 全宽
if st.session_state.db_connected and st.session_state.selected_table:
    st.subheader("🔍 数据查询")

    # 使用列布局优化查询区域
    query_col1, query_col2 = st.columns([3, 1])

    with query_col1:
        # 获取上次创建的活动ID
        default_activity_id = st.session_state.get('last_activity_id', '2095397849346129920')

        # 活动ID输入框
        activity_id_input = st.text_input(
            "活动ID (查询条件)",
            value=default_activity_id,
            placeholder="请输入活动ID，例如: 2095397849346129920",
            help="输入要查询的活动ID"
        )

    with query_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 添加空行对齐
        # 查询按钮
        query_button = st.button(
            "🔍 查询数据",
            use_container_width=True
        )

    # 查询逻辑
    if query_button:
        if not activity_id_input:
            st.error("❌ 请先输入活动ID")
        else:
            with st.spinner(
                    f"正在查询 {st.session_state.selected_schema}.{st.session_state.selected_table} 中 activity_id={activity_id_input} 的记录..."):
                try:
                    # 连接数据库
                    conn = psycopg2.connect(
                        host=DB_CONFIG["host"],
                        port=DB_CONFIG["port"],
                        database=DB_CONFIG["database"],
                        user=DB_CONFIG["user"],
                        password=DB_CONFIG["password"]
                    )

                    # 创建游标
                    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                    # 构建查询SQL
                    query_sql = f"SELECT * FROM {st.session_state.selected_schema}.{st.session_state.selected_table} WHERE activity_id = %s"
                    cur.execute(query_sql, (activity_id_input,))

                    # 获取结果
                    results = cur.fetchall()

                    # 关闭连接
                    cur.close()
                    conn.close()

                    # 显示查询信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📋 Schema", st.session_state.selected_schema)
                    with col2:
                        st.metric("📊 表名", st.session_state.selected_table)
                    with col3:
                        st.metric("🔍 查询条件", f"activity_id = {activity_id_input}")

                    st.subheader("📊 查询结果")

                    if results:
                        st.success(f"✅ 查询成功，共找到 {len(results)} 条记录")

                        # 显示为JSON格式
                        for idx, row in enumerate(results, 1):
                            with st.expander(f"📄 记录 {idx}"):
                                st.json(dict(row))

                        # 同时以表格形式展示
                        st.markdown("**表格视图:**")
                        st.dataframe(results, use_container_width=True)

                        # 显示字段信息
                        if results:
                            st.markdown("**📋 字段列表:**")
                            fields = list(results[0].keys())
                            st.write(", ".join(f"`{field}`" for field in fields))
                    else:
                        st.warning(f"⚠️ 未找到 activity_id={activity_id_input} 的记录")

                except psycopg2.OperationalError as e:
                    st.error(f"❌ 数据库连接失败: {str(e)}")
                    st.info("💡 请检查网络连接和数据库配置")
                except psycopg2.ProgrammingError as e:
                    st.error(f"❌ SQL执行错误: {str(e)}")
                except Exception as e:
                    st.error(f"❌ 查询异常: {str(e)}")

# 底部提示
st.caption("💡 提示: 请确保Token有效，且具有创建活动的权限")