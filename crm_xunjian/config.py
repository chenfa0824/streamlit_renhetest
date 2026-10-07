# config.py
# ===================== 全局目录常量 =====================
import os

SCREENSHOT_DIR = "/inspect_screenshot"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)
LOG_DIR = "/inspect_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
USERNAME = "admin"
PASSWORD = "Admin@rh@rV2!tK"
TARGET_URL = "https://maintest.whrhkj.com/cas/login"
LOCAL_LOG_FILE = None


# ===================== 巡检配置 =====================
class InspectionConfig:
    # 默认登录信息
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "Admin@rh@rV2!tK"
    DEFAULT_TARGET_URL = "https://maintest.whrhkj.com/cas/login"
    # 是否启用完整菜单巡检
    ENABLE_FULL_MENU_INSPECTION = True
    # 如果只想巡检部分菜单，可以指定（留空表示巡检所有）
    MENUS_TO_INSPECT = []  # 例如: ["学员教务中心", "数据报表中心"]
    # 每个子菜单点击后等待时间（秒）
    WAIT_AFTER_CLICK = 3
    # 是否在点击子菜单后返回工作台
    RETURN_TO_WORKBENCH = True
    # 超时配置（毫秒）
    TIMEOUT = {
        "page_load": 30000,
        "element_wait": 10000,
        "api_wait": 20000,
        "menu_expand": 5000,
        "submenu_click": 5000
    }
    # 是否跳过静态资源检查
    SKIP_STATIC_RESOURCES = True
    # 静态资源后缀
    STATIC_RESOURCE_SUFFIXES = (".png", ".jpg", ".jpeg", ".css", ".js", ".ico", ".svg", ".woff", ".gif")


# ===================== 选择器配置 =====================
class Selectors:
    """页面元素选择器配置 - 便于统一维护和修改"""
    # 登录页面 - 通过文本标签定位输入框（最稳定）
    USERNAME_LABEL = "用户名"
    PASSWORD_LABEL = "密码"
    LOGIN_TAB = {"type": "text", "value": "账号登录"}
    # 侧边栏菜单
    # SIDEBAR_MENUS = [
    #     "工作台", "运营管理"
    # ]

    # 侧边栏菜单
    SIDEBAR_MENUS = [
        "线索招生中心", "学员教务中心",
        "校区运营中心", "人资行政中心", "审批待办中心",
        "数据报表中心", "系统工具中心", "财务结算中心"
    ]

    USERNAME_INPUT_BACKUP = [
        {"type": "css", "value": "input[placeholder*='用户名']"},
        {"type": "css", "value": "input[placeholder*='账号']"},
        {"type": "css", "value": "input[type='text'][name*='username']"},
        {"type": "css", "value": "input[name='username']"},
        {"type": "css", "value": "input[name='user']"},
        {"type": "id", "value": "el-id-7995-8"},
        {"type": "css", "value": "input[type='text']:first-of-type"}
    ]

    PASSWORD_INPUT_BACKUP = [
        {"type": "css", "value": "input[placeholder*='密码']"},
        {"type": "css", "value": "input[type='password']"},
        {"type": "css", "value": "input[name='password']"},
        {"type": "css", "value": "input[name='pwd']"},
        {"type": "id", "value": "el-id-5980-33"},
        {"type": "css", "value": "input[type='password']"}
    ]

    # 登录按钮选择器
    LOGIN_BUTTON_SPAN = {"type": "css", "value": "button:has(span:has-text('登 录'))"}
    LOGIN_BUTTON_BACKUP = [
        {"type": "css", "value": "button[type='button']:has-text('登 录')"},
        {"type": "css", "value": "button[type='submit']:has-text('登 录')"},
        {"type": "css", "value": "button:has-text('登 录')"},
        {"type": "css", "value": ".el-button--primary"},
        {"type": "css", "value": ".ant-btn-primary"},
        {"type": "css", "value": "button span:has-text('登 录')"},
        {"type": "css", "value": ".el-button--primary span"},
        {"type": "css", "value": ".ant-btn-primary span"},
        {"type": "css", "value": "button span:first-child"},
        {"type": "text", "value": "登 录"},
        {"type": "css", "value": "input[type='submit'][value='登 录']"},
        {"type": "role", "value": "button|登 录"}
    ]


# ===================== 页面元素标签配置 =====================
class ElementLabels:
    """页面元素文本标签配置"""

    # 登录相关
    LOGIN_TAB_TEXT = "账号登录"
    USERNAME_LABEL = "用户名"
    PASSWORD_LABEL = "密码"
    LOGIN_BUTTON_TEXT = "登录"

    # CRM相关
    CRM_LINK_TEXT = "crm"
    CRM_TAB_TITLE = "仁和CRM"

    # 工作台相关
    WORKBENCH_TEXT = "工作台"


# ===================== 浏览器配置 =====================
class BrowserConfig:
    """浏览器配置"""

    # 启动参数
    LAUNCH_ARGS = [
        '--start-maximized',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-gpu'
    ]

    # Context配置
    CONTEXT_CONFIG = {
        "viewport": None,
        "locale": "zh-CN",
        "no_viewport": True,
        "ignore_https_errors": True
    }

    # 默认无头模式
    HEADLESS = True
