import streamlit as st
from playwright.sync_api import sync_playwright
import time
import pandas as pd
from datetime import datetime
import io
import traceback

# ========== 抽离后的工具导入 ==========
from crm_xunjian.log import add_log, create_new_local_log_file, close_local_log_file
from crm_xunjian.elements import wait_for_dom_ready, wait_for_element_ready, fill_input_by_label, click_with_backup, \
    click_button_by_span
from crm_xunjian.utils import save_screenshot_to_local
from crm_xunjian.menu import get_all_menu_items_recursive, verify_all_submenus
from crm_xunjian.apicopy import capture_response
# ===================== 导入配置文件 =====================
from crm_xunjian.config import (
    SCREENSHOT_DIR,
    LOG_DIR,
    Selectors
)

# ===================== 多环境预设配置（统一管理） =====================
ENV_PRESET = {
    "测试环境": {
        "username": "admin",
        "password": "Admin@rh@rV2!tK",
        "target_url": "https://maintest.whrhkj.com"
    },
    "生产环境": {
        "username": "116136",
        "password": "Chenfa@132",
        "target_url": "https://whrhkj.com"
    }
}

# ===================== 页面全局配置 =====================
st.set_page_config(page_title="CRM自动化巡检工具", layout="wide", page_icon="🔍")

# ===================== 自定义CSS实现紧凑布局 =====================
st.markdown("""
<style>
    /* 整体紧凑 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    /* 标题紧凑 */
    h1, h2, h3, h4 {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* 主标题特殊处理 */
    h1 {
        font-size: 1.8rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
    }
    h3 {
        font-size: 1rem !important;
    }
    /* 分割线紧凑 */
    hr {
        margin: 0.3rem 0 !important;
    }
    /* 列间距 */
    .row-widget.stColumns {
        gap: 0.3rem !important;
    }
    /* 输入框紧凑 */
    .stTextInput > div {
        margin-bottom: 0.1rem !important;
    }
    .stTextInput input {
        padding: 0.3rem 0.5rem !important;
        font-size: 0.85rem !important;
    }
    /* 按钮紧凑 */
    .stButton button {
        padding: 0.3rem 0.8rem !important;
        font-size: 0.85rem !important;
    }
    /* 选择框紧凑 */
    .stSelectbox > div {
        margin-bottom: 0.1rem !important;
    }
    .stSelectbox select {
        padding: 0.2rem 0.5rem !important;
        font-size: 0.85rem !important;
    }
    /* 复选框紧凑 */
    .stCheckbox > label {
        font-size: 0.85rem !important;
        margin-bottom: 0 !important;
    }
    /* 信息框紧凑 */
    .stAlert {
        padding: 0.3rem 0.8rem !important;
        margin-bottom: 0.2rem !important;
        font-size: 0.85rem !important;
    }
    /* 数据框紧凑 */
    .stDataFrame {
        margin-bottom: 0.2rem !important;
    }
    /* 文本域紧凑 */
    .stTextArea textarea {
        font-size: 0.8rem !important;
        padding: 0.3rem !important;
    }
    .stTextArea > div {
        margin-bottom: 0.1rem !important;
    }
    /* tabs紧凑 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.2rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.3rem 0.8rem !important;
        font-size: 0.85rem !important;
    }
    /* 下载按钮紧凑 */
    .stDownloadButton button {
        padding: 0.2rem 0.6rem !important;
        font-size: 0.8rem !important;
    }
    /* 图片容器 */
    .stImage {
        margin-bottom: 0.2rem !important;
    }
    /* 列内边距 */
    .css-1r6slb0, .css-1offfwp {
        padding: 0.2rem !important;
    }
    /* 容器内边距 */
    .stContainer {
        padding: 0.2rem 0.3rem !important;
    }
    /* 标签文本 */
    .stTextInput label, .stSelectbox label, .stCheckbox label {
        font-size: 0.8rem !important;
        margin-bottom: 0 !important;
    }
    /* 分隔线颜色淡化 */
    hr {
        opacity: 0.3 !important;
    }
    /* 行间距 */
    .row-widget {
        margin-bottom: 0.1rem !important;
    }
    /* 进度条紧凑 */
    .stProgress > div {
        height: 0.5rem !important;
    }
    /* 指标卡紧凑 */
    [data-testid="metric-container"] {
        padding: 0.3rem !important;
        margin-bottom: 0.1rem !important;
    }
    /* tabs内容紧凑 */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 0.2rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 CRM自动化巡检工具")

# ===================== 会话状态初始化 =====================
def init_state():
    state_defaults = {
        "current_env": "测试环境",
        "env_switch_trigger": False,
        "env_config": {k: v.copy() for k, v in ENV_PRESET.items()},
        "headless": False,
        "run_logs": [],
        "report_data": [],
        "api_error_list": [],
        "screenshot_bytes": None,
        "local_log_file": None,
        "is_running": False,
        "active_tab": "日志"
    }
    for key, default_val in state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_val

init_state()

# ===================== 配置区域 =====================
with st.container():
    # 使用更紧凑的列布局 - 4列
    col1, col2, col3, col4 = st.columns([0.8, 1, 1, 0.5], gap="small")

    with col1:
        def switch_env_callback():
            st.session_state.current_env = st.session_state.env_selector
            st.session_state.env_switch_trigger = True

        env_list = list(ENV_PRESET.keys())
        st.selectbox(
            "环境",
            options=env_list,
            index=env_list.index(st.session_state.current_env),
            key="env_selector",
            on_change=switch_env_callback,
            label_visibility="collapsed"
        )

        if st.session_state.env_switch_trigger:
            st.session_state.env_switch_trigger = False
            st.rerun()

    curr_env = st.session_state.current_env
    curr_cfg = st.session_state.env_config[curr_env]
    dyn_key_prefix = curr_env

    with col2:
        st.text_input(
            "账号",
            value=curr_cfg["username"],
            key=f"user_input_{dyn_key_prefix}",
            label_visibility="collapsed",
            placeholder="登录账号"
        )
        st.text_input(
            "密码",
            value=curr_cfg["password"],
            type="password",
            key=f"pwd_input_{dyn_key_prefix}",
            label_visibility="collapsed",
            placeholder="登录密码"
        )

    with col3:
        st.text_input(
            "地址",
            value=curr_cfg["target_url"],
            key=f"url_input_{dyn_key_prefix}",
            label_visibility="collapsed",
            placeholder="登录地址"
        )
        # 复选框和按钮放同一行
        col3a, col3b = st.columns([1, 1], gap="small")
        with col3a:
            headless_flag = st.checkbox("无头模式", value=st.session_state.headless, key="headless_box")
            st.session_state.headless = headless_flag
        with col3b:
            run_btn = st.button("🚀 一键巡检", type="primary", use_container_width=True,
                              disabled=st.session_state.is_running)

    with col4:
        clear_log_btn = st.button("🗑️ 清空", use_container_width=True)

    # 同步配置
    st.session_state.env_config[curr_env]["username"] = st.session_state[f"user_input_{dyn_key_prefix}"]
    st.session_state.env_config[curr_env]["password"] = st.session_state[f"pwd_input_{dyn_key_prefix}"]
    st.session_state.env_config[curr_env]["target_url"] = st.session_state[f"url_input_{dyn_key_prefix}"]

# 分割线
st.divider()

# 同步全局配置
active_cfg = st.session_state.env_config[st.session_state.current_env]
st.session_state.login_user = active_cfg["username"]
st.session_state.login_pwd = active_cfg["password"]
st.session_state.target_url = active_cfg["target_url"]

# ===================== 浏览器执行函数 =====================
def run_browser_task(user, pwd, target_url, headless_flag) -> tuple:
    report_list = []
    api_error_list = []
    screenshot_buf = None
    browser = None
    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless_flag,
                args=['--start-maximized', '--no-sandbox', '--disable-dev-shm-usage']
            )
            add_log("Chromium浏览器进程启动成功（窗口已最大化）")
            context = browser.new_context(
                viewport=None,
                locale="zh-CN",
                no_viewport=True
            )
            add_log("注册响应监听，页面所有接口都会触发")
            context.on("response", capture_response)
            page = context.new_page()
            add_log("新建空白页面Tab完成")
            add_log(f"第一步：访问CAS登录地址：{target_url}，超时限制10秒")
            page.goto(target_url, timeout=10000)
            wait_for_dom_ready(page, timeout=10000)
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            add_log("登录页面DOM完全加载并渲染完成")
            add_log("第二步：定位【账号登录】Tab标签并点击切换登录面板")
            if not click_with_backup(
                    page,
                    Selectors.LOGIN_TAB,
                    [{"type": "text", "value": "账号登录"}],
                    description="账号登录Tab"
            ):
                raise Exception("无法定位【账号登录】Tab")
            time.sleep(1)
            add_log("✅ 已成功切换至账号登录标签面板")
            screenshot_buf1 = page.screenshot(full_page=True)
            save_screenshot_to_local(screenshot_buf1, SCREENSHOT_DIR, is_error=True)
            add_log("第三步：填充用户名与密码（通过文本标签定位）")
            if not fill_input_by_label(
                    page,
                    Selectors.USERNAME_LABEL,
                    user,
                    backup_selectors=Selectors.USERNAME_INPUT_BACKUP,
                    timeout=10000
            ):
                try:
                    page.locator("#el-id-7995-8").fill(user)
                    add_log(f"✅ 通过ID紧急备用定位填充成功：{user}")
                except Exception as e:
                    raise Exception(f"无法定位用户名输入框：{str(e)}")
            add_log(f"用户名输入完成：{user}")
            if not fill_input_by_label(
                    page,
                    Selectors.PASSWORD_LABEL,
                    pwd,
                    backup_selectors=Selectors.PASSWORD_INPUT_BACKUP,
                    timeout=10000
            ):
                try:
                    page.locator("#el-id-5980-33").fill(pwd)
                    add_log("✅ 通过ID紧急备用定位填充成功")
                except Exception as e:
                    raise Exception(f"无法定位密码输入框：{str(e)}")
            add_log("密码输入完成（已脱敏不记录明文）")
            add_log("第四步：点击登录按钮（优先原生<button type>标签定位）")
            screenshot_buf2 = page.screenshot(full_page=True)
            save_screenshot_to_local(screenshot_buf2, SCREENSHOT_DIR, is_error=True)
            if not click_button_by_span(page, "登 录", timeout=10000):
                if not click_with_backup(
                        page,
                        Selectors.LOGIN_BUTTON_SPAN,
                        Selectors.LOGIN_BUTTON_BACKUP,
                        description="登录按钮"
                ):
                    try:
                        page.get_by_text("登 录", exact=True).click()
                        add_log("✅ 通过文本紧急备用定位点击成功")
                    except Exception as e:
                        raise Exception(f"无法定位登录按钮：{str(e)}")
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(2)
            login_pass = True
            try:
                wait_for_dom_ready(page, timeout=10000)
                login_indicator = {"type": "text", "value": user}
                success, _ = wait_for_element_ready(page, login_indicator, timeout=6000)
                if success:
                    add_log(f"✅ CAS登录校验通过")
                    report_list.append({"模块": "CAS登录模块", "状态": "正常", "异常描述": ""})
                else:
                    raise Exception(f"未找到用户标识：{user}")
            except Exception as e:
                err_trace = traceback.format_exc()
                add_log(f"❌ CAS登录失败：{str(e)}", "ERROR", exception_trace=err_trace)
                report_list.append({"模块": "CAS登录模块", "状态": "异常", "异常描述": f"{str(e)}"})
                login_pass = False
            if not login_pass:
                screenshot_buf = page.screenshot(full_page=True)
                browser.close()
                return report_list, screenshot_buf, api_error_list
            wait_for_dom_ready(page, timeout=10000)
            time.sleep(2)
            add_log("开始切换页面")
            add_log("点击CRM跳转到CRM系统")
            with context.expect_page() as crm_page_info:
                page.locator('p:has-text("crm")').click()
                add_log("已点击CRM链接，等待新页面打开...")
                time.sleep(2)
            crm_page = crm_page_info.value
            add_log(f"新页面已打开，当前URL: {crm_page.url}")
            crm_page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)
            page = crm_page
            add_log("已切换到CRM页面，继续后续巡检...")
            add_log("第五步：巡检左侧导航菜单（含多级子菜单，按从上到下顺序验证）")
            menu_err = ""
            menu_normal = True
            menu_verify_results = {}
            total_submenus_checked = 0
            total_submenus_failed = 0
            menu_structure = get_all_menu_items_recursive(page)
            for menu_name in Selectors.SIDEBAR_MENUS:
                if menu_name not in menu_structure:
                    menu_normal = False
                    menu_err += f"{menu_name}(主菜单缺失) "
                    add_log(f"❌ 缺失主菜单: {menu_name}", "ERROR")
                    continue
                menu_info = menu_structure[menu_name]
                submenus = menu_info["submenus"]
                if submenus:
                    success_list, failed_list = verify_all_submenus(page, menu_name, submenus, timeout=10000)
                    menu_verify_results[menu_name] = {
                        "success": success_list,
                        "failed": failed_list,
                        "total": len(submenus),
                        "success_count": len(success_list),
                        "failed_count": len(failed_list)
                    }
                    total_submenus_checked += len(submenus)
                    total_submenus_failed += len(failed_list)
                    if failed_list:
                        menu_normal = False
                        failed_names = [f["子菜单"] for f in failed_list]
                        menu_err += f"{menu_name}(子菜单验证失败: {', '.join(failed_names)}) "
                        add_log(f"❌ 菜单 {menu_name} 有 {len(failed_list)} 个子菜单验证失败: {', '.join(failed_names)}",
                                "ERROR")
            if menu_normal:
                report_list.append({"模块": "侧边导航菜单（含多级子菜单）", "状态": "正常",
                                    "异常描述": f"共验证 {total_submenus_checked} 个子菜单"})
                add_log(f"✅ 全部侧边栏菜单验证通过，共验证 {total_submenus_checked} 个子菜单")
            else:
                report_list.append({"模块": "侧边导航菜单（含多级子菜单）", "状态": "异常",
                                    "异常描述": f"问题: {menu_err}（失败 {total_submenus_failed}/{total_submenus_checked}）"})
                add_log(f"❌ 侧边栏菜单验证异常: {menu_err}", "ERROR")
            st.session_state.menu_structure = menu_structure
            add_log("第六步：批量校验所有业务接口")
            browser.close()
    except Exception as browser_err:
        err_trace = traceback.format_exc()
        add_log(f"❌ 浏览器全局操作异常：{str(browser_err)}", "FATAL", exception_trace=err_trace)
        report_list.append({"模块": "浏览器全局", "状态": "异常", "异常描述": f"{str(browser_err)}"})
        if page is not None:
            try:
                screenshot_buf = page.screenshot(full_page=True)
                save_screenshot_to_local(screenshot_buf, SCREENSHOT_DIR, is_error=True)
            except:
                pass
        if browser is not None:
            browser.close()
    return report_list, screenshot_buf, api_error_list

# ===================== 巡检入口函数 =====================
def run_inspect_task():
    if st.session_state.is_running:
        st.warning("巡检正在执行，请勿重复点击！")
        return
    curr_env = st.session_state.current_env
    cfg = st.session_state.env_config[curr_env]
    user = cfg["username"]
    pwd = cfg["password"]
    target_url = cfg["target_url"]
    headless_flag = st.session_state.headless

    st.session_state.api_error_list = []
    st.session_state.report_data = []
    st.session_state.screenshot_bytes = None
    st.session_state.run_logs = []
    st.session_state.is_running = True
    try:
        create_new_local_log_file(LOG_DIR, user, target_url, True)
        add_log(f"🚀 开始一键自动化巡检任务 | 当前运行环境：{curr_env}")
        report_data, screenshot_bytes, api_error_list = run_browser_task(user, pwd, target_url, headless_flag)
        st.session_state.report_data = report_data
        st.session_state.api_error_list = api_error_list
        st.session_state.screenshot_bytes = screenshot_bytes
        add_log("🎉 全部巡检流程执行完毕！")
    except Exception as e:
        trace = traceback.format_exc()
        add_log(f"💥 巡检入口执行失败：{str(e)}", "FATAL", exception_trace=trace)
    finally:
        close_local_log_file()
        st.session_state.is_running = False
        st.rerun()

# 清空日志按钮逻辑
if clear_log_btn:
    st.session_state.run_logs = []
    st.session_state.report_data = []
    st.session_state.api_error_list = []
    st.session_state.screenshot_bytes = None
    st.success("已清空所有日志、报告、截图缓存")
    st.rerun()

if run_btn:
    run_inspect_task()

# ===================== Tab切换展示（紧凑布局） =====================
tab1, tab2, tab3, tab4 = st.tabs(["📝 日志", "📊 UI报告", "🌐 API异常", "📷 截图"])

with tab1:
    if st.session_state.run_logs:
        log_text = "\n".join(st.session_state.run_logs)
        st.text_area("运行日志", log_text, height=280, key="log_area")
        log_bytes = log_text.encode("utf-8")
        st.download_button("📥 下载日志", log_bytes,
                           file_name=f"巡检日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                           use_container_width=True)
    else:
        st.info("暂无日志，点击「一键巡检」启动任务")

with tab2:
    if st.session_state.report_data:
        df = pd.DataFrame(st.session_state.report_data)
        def color_err(row):
            return ["background:#ffeeee" if row["状态"] == "异常" else "" for _ in row]
        st.dataframe(df.style.apply(color_err, axis=1), use_container_width=True, hide_index=True, height=200)
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button("📥 下载UI报告CSV", buf.getvalue(),
                           file_name=f"UI巡检报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                           use_container_width=True)
    else:
        st.info("暂无UI巡检数据")

with tab3:
    if st.session_state.api_error_list:
        df_api = pd.DataFrame(st.session_state.api_error_list)
        st.dataframe(df_api, use_container_width=True, hide_index=True, height=200)
        buf = io.StringIO()
        df_api.to_csv(buf, index=False, encoding="utf-8-sig")
        st.download_button("📥 下载API异常CSV", buf.getvalue(),
                           file_name=f"API异常报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                           use_container_width=True)
    else:
        if st.session_state.run_logs:
            st.success("✅ 所有接口请求正常，无异常")
        else:
            st.info("暂无接口校验数据")

with tab4:
    if st.session_state.screenshot_bytes:
        st.image(st.session_state.screenshot_bytes, caption="巡检页面截图", use_container_width=True)
        st.download_button("📥 下载截图", st.session_state.screenshot_bytes,
                           file_name=f"巡检截图_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                           mime="image/png", use_container_width=True)
    else:
        st.info("暂无截图，执行巡检后自动生成")

# ===================== 底部状态栏（紧凑） =====================
st.divider()
status_col1, status_col2, status_col3 = st.columns([1, 1, 1], gap="small")
with status_col1:
    st.caption(f"📍 当前环境: **{st.session_state.current_env}**")
with status_col2:
    status_text = "🟢 空闲" if not st.session_state.is_running else "🔄 运行中..."
    st.caption(f"⏳ 状态: {status_text}")
with status_col3:
    log_count = len(st.session_state.run_logs)
    st.caption(f"📊 日志条数: **{log_count}** | 报告: **{len(st.session_state.report_data)}** 条")