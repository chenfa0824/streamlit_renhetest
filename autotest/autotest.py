import streamlit as st
from playwright.sync_api import sync_playwright
import json
import os
import datetime
import traceback
import base64
import time
import re

# ===================== 全局配置 =====================
CONFIG_FILE = "user_config.json"
LOG_FILE = "automation_log.txt"
CAPTCHA_URL_REG = re.compile(r"/sys/randomImage/\d+")
# 初始化ddddocr
import ddddocr

ocr = ddddocr.DdddOcr(show_ad=False)

# 默认账号列表
default_users = [
    {"name": "boss", "account": "112054", "password": "algo1129"},
    {"name": "正式账号", "account": "110953", "password": "Rh@123456"},
    {"name": "测试管理员", "account": "admin", "password": "123456"},
    {"name": "普通员工A", "account": "user01", "password": "123123"},
]

# ===================== Session状态初始化 =====================
if "log_messages" not in st.session_state:
    st.session_state["log_messages"] = []
if "captcha_base64" not in st.session_state:
    st.session_state["captcha_base64"] = None
if "ocr_captcha_result" not in st.session_state:
    st.session_state["ocr_captcha_result"] = ""
if "page_instance" not in st.session_state:
    st.session_state["page_instance"] = None
if "browser_context" not in st.session_state:
    st.session_state["browser_context"] = None


# ===================== 日志工具 =====================
def write_log(level: str, msg: str):
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{time_str}] [{level}] {msg}"
    st.session_state["log_messages"].append(log_text)
    print(log_text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_text + "\n")


# ===================== 通用元素信息抓取 =====================
def get_element_tag_info(page, selector: str, desc: str, timeout=3000):
    try:
        locator = page.locator(selector)
        locator.wait_for(timeout=timeout, state="visible")
        tag_info = locator.evaluate("""
            el => {
                return {
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || "",
                    className: el.className || "",
                    placeholder: el.placeholder || "",
                    value: el.value || "",
                    innerText: el.innerText?.trim() || "",
                    disabled: el.disabled,
                    hidden: el.hidden,
                    outerHTML: el.outerHTML.substring(0, 400)
                }
            }
        """)
        write_log("ELEMENT", f"【{desc}】选择器:{selector} | 属性:{json.dumps(tag_info, ensure_ascii=False)}")
        return {
            "exist": True,
            "locator": locator,
            "info": tag_info,
            "value": tag_info["value"],
            "disabled": tag_info["disabled"],
            "hidden": tag_info["hidden"]
        }
    except Exception as e:
        write_log("ELEMENT", f"【{desc}】捕获失败:{str(e)}")
        return {"exist": False, "locator": None, "info": None}


# ===================== 核心：JS递归遍历所有DIV，自动抓取包含【登 录】的span =====================
def scan_all_div_find_login_span(page):
    """
    注入JS递归遍历页面全部div容器，查找innerText匹配 登 录（1或2个空格）的span
    返回层级数据：目标span、父div列表、最外层button元素信息
    """
    scan_js = """
    function scanDomForLoginSpan() {
        let result = null;
        // 使用正则匹配：登 + 1或2个空格 + 录
        const loginRegex = /^登\\s{1,2}录$/;

        function traverse(node, parentDivList) {
            if (!node) return false;

            // 当前节点是span且文本匹配（1或2个空格）
            if (node.tagName?.toLowerCase() === 'span') {
                const text = node.innerText?.trim();
                if (text && loginRegex.test(text)) {
                    // 向上回溯收集所有父级div
                    let divParents = [...parentDivList];
                    // 向上找最近button
                    let btnNode = node;
                    while(btnNode && btnNode.tagName?.toLowerCase() !== 'button') {
                        btnNode = btnNode.parentElement;
                    }
                    result = {
                        spanOuterHtml: node.outerHTML.substring(0,400),
                        spanText: node.innerText.trim(),
                        parentDivCount: divParents.length,
                        parentDivOuterHtmlList: divParents.map(d => d.outerHTML.substring(0,300)),
                        hasButton: !!btnNode,
                        buttonOuterHtml: btnNode ? btnNode.outerHTML.substring(0,400) : null
                    };
                    return true;
                }
            }

            // 记录div父容器
            let newDivList = [...parentDivList];
            if(node.tagName?.toLowerCase() === 'div') {
                newDivList.push(node);
            }

            // 递归子节点
            for(let child of node.children) {
                if(traverse(child, newDivList)) return true;
            }
            return false;
        }

        try {
            traverse(document.body, []);
        } catch(err) {
            return {error: err.message};
        }
        return result;
    }
    return scanDomForLoginSpan()
    """

    # 调试：打印所有包含"登"的span文本
    debug_js = """
    function debugSpans() {
        const spans = document.querySelectorAll('span');
        const texts = [];
        spans.forEach(s => {
            const text = s.innerText?.trim();
            if (text && text.includes('登')) {
                texts.push({
                    text: text,
                    textLength: text.length,
                    html: s.outerHTML.substring(0, 200),
                    hasButton: !!s.closest('button')
                });
            }
        });
        return texts;
    }
    return debugSpans();
    """

    try:
        debug_result = page.evaluate(debug_js)
        if debug_result:
            write_log("DEBUG", f"包含'登'的span列表：{json.dumps(debug_result, ensure_ascii=False)}")
    except Exception as e:
        write_log("WARNING", f"调试信息获取失败：{str(e)}")

    # 执行JS全页面div扫描
    scan_result = page.evaluate(scan_js)
    if scan_result and "error" in scan_result:
        raise Exception(f"DOM递归扫描异常: {scan_result['error']}")
    if not scan_result:
        raise Exception("遍历全部DIV容器，未找到文本为【登 录】（1或2个空格）的span标签")

    # 打印DOM层级日志
    write_log("ELEMENT", "========== 自动解析DIV容器，抓取登录标签层级信息 ==========")
    write_log("ELEMENT", f"目标Span完整HTML：{scan_result['spanOuterHtml']}")
    write_log("ELEMENT", f"目标Span文本：{scan_result['spanText']}")
    write_log("ELEMENT", f"span上层DIV容器总数：{scan_result['parentDivCount']}")
    for idx, div_html in enumerate(scan_result["parentDivOuterHtmlList"]):
        write_log("ELEMENT", f"上层第{idx + 1}层DIV：{div_html}")
    if scan_result["hasButton"]:
        write_log("ELEMENT", f"span上层绑定Button完整HTML：{scan_result['buttonOuterHtml']}")
    else:
        write_log("WARNING", "span上层未找到button点击容器")
    write_log("ELEMENT", "========== DIV层级解析完成 ==========\n")

    # 使用正则定位span（兼容1或2个空格）
    try:
        # 尝试多种定位方式
        span_locator = page.locator('span:text-matches("登\\s{1,2}录", "g")')
        btn_locator = span_locator.locator("xpath=ancestor::button[1]")
        # 验证定位器是否有效
        btn_locator.wait_for(timeout=3000, state="visible")
        return btn_locator
    except Exception as e:
        write_log("WARNING", f"正则定位span失败：{str(e)}，尝试备选定位方式")
        # 备选：直接查找包含对应文本的span
        span_locator = page.locator('span:has-text("登")')
        # 过滤出匹配的span
        spans = span_locator.all()
        for span in spans:
            text = span.inner_text().strip()
            if re.match(r'^登\s{1,2}录$', text):
                btn_locator = span.locator("xpath=ancestor::button[1]")
                btn_locator.wait_for(timeout=3000, state="visible")
                write_log("SUCCESS", f"备选定位成功，找到span文本：{text}")
                return btn_locator
        raise Exception("所有定位方式均失败")


# ===================== 批量捕获输入框标签 =====================
def capture_input_tags(page):
    write_log("ELEMENT", "========== 捕获登录输入框标签 ==========")
    get_element_tag_info(page, 'input[placeholder="请输入工号"]', "工号输入框")
    get_element_tag_info(page, 'input[placeholder="请输入密码"]', "密码输入框")
    get_element_tag_info(page, 'input[placeholder="请输入验证码"]', "验证码输入框")
    write_log("ELEMENT", "========== 输入框标签捕获完成 ==========\n")


# ===================== OCR验证码识别 =====================
def captcha_ocr_recognize(base64_img_str: str) -> str:
    try:
        base64_raw = base64_img_str.split(",")[1] if "," in base64_img_str else base64_img_str
        img_byte_data = base64.b64decode(base64_raw)
        return ocr.classification(img_byte_data).strip()
    except Exception as e:
        write_log("ERROR", f"OCR识别异常：{str(e)}")
        return ""


# ===================== 验证码接口监听 =====================
captcha_caught = False


def handle_network_response(response):
    global captcha_caught
    url = response.url
    if CAPTCHA_URL_REG.search(url) and response.request.method == "GET" and not captcha_caught:
        captcha_caught = True
        write_log("API", "==================== 捕获验证码图片接口 ====================")
        write_log("API", f"接口地址：{url}")
        write_log("API", f"状态码：{response.status}")
        try:
            resp_json = response.json()
            img_b64 = resp_json.get("result", "")
            if img_b64.startswith("data:image/"):
                st.session_state["captcha_base64"] = img_b64
                ocr_code = captcha_ocr_recognize(img_b64)
                st.session_state["ocr_captcha_result"] = ocr_code
                if ocr_code:
                    write_log("SUCCESS", f"OCR识别验证码：{ocr_code}，自动填充")
                    auto_fill_captcha_input(ocr_code)
                else:
                    write_log("WARNING", "OCR识别失败，请手动输入验证码")
        except Exception as e:
            write_log("ERROR", f"解析验证码接口失败：{str(e)}")


# ===================== 填充输入并同步前端表单事件 =====================
def fill_input_trigger(page, selector: str, value: str, desc: str):
    locator = page.locator(selector)
    locator.wait_for(timeout=6000, state="visible")
    locator.fill(value)
    locator.evaluate("el => { el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); }")
    write_log("INFO", f"{desc}填充完成：{value}，触发表单同步事件")
    get_element_tag_info(page, selector, f"{desc}-填充后校验")


# ===================== 自动填充验证码 =====================
def auto_fill_captcha_input(code: str):
    page = st.session_state.get("page_instance")
    if not page:
        write_log("WARNING", "页面未初始化，无法填充验证码")
        return
    sel = 'input[placeholder="请输入验证码"]'
    get_element_tag_info(page, sel, "验证码输入框-填充前")
    fill_input_trigger(page, sel, code, "验证码输入框")


# ===================== 登录核心函数：自动遍历DIV抓取登录按钮并点击 =====================
def execute_login():
    page = st.session_state.get("page_instance")
    if not page:
        st.error("❌ 请先点击一键启动打开浏览器页面")
        write_log("ERROR", "登录拦截：无页面实例")
        return

    # 验证码前置校验
    captcha_sel = 'input[placeholder="请输入验证码"]'
    try:
        captcha_val = page.locator(captcha_sel).evaluate("el => el.value").strip()
        write_log("INFO", f"登录前置校验，当前验证码：{captcha_val}")
        if not captcha_val:
            st.warning("⚠️ 验证码为空，禁止提交登录")
            write_log("WARNING", "登录拦截：验证码无有效内容")
            return
    except Exception as e:
        write_log("WARNING", f"获取验证码值失败：{str(e)}")

    try:
        # 关键逻辑：自动遍历页面所有div容器，递归查找登录span
        login_btn_locator = scan_all_div_find_login_span(page)
        # 校验locator有效
        if not login_btn_locator:
            raise Exception("DIV扫描返回空按钮定位器")
        login_btn_locator.scroll_into_view_if_needed()
        # 点击逻辑，常规失败则强制穿透点击
        try:
            login_btn_locator.click(timeout=3000)
        except Exception as click_err:
            write_log("WARNING", f"常规点击失败：{str(click_err)}，执行force强制点击")
            login_btn_locator.click(force=True, timeout=3000)
        write_log("SUCCESS", "✅ 自动解析DIV容器抓取【登 录】span（1或2个空格），成功点击登录按钮")
        st.success("✅ 登录按钮已点击，等待页面跳转")
        time.sleep(1)
    except Exception as scan_err:
        write_log("ERROR", f"DIV自动遍历抓取登录标签失败：{str(scan_err)}，启用备用模糊匹配")
        # ========== 备用方案：正则匹配按钮 ==========
        try:
            # 正则匹配按钮文本（兼容1或2个空格）
            backup_btn = page.locator('button:text-matches("登\\s{1,2}录", "g")')
            backup_btn.wait_for(state="visible", timeout=4000)
            backup_btn.scroll_into_view_if_needed()
            backup_btn.click(force=True, timeout=3000)
            write_log("SUCCESS", "备用正则匹配按钮点击成功")
            st.success("✅ 备用方案完成登录点击")
            time.sleep(1)
        except Exception as err2:
            # 第二备用方案：查找包含"登"和"录"的任意按钮
            try:
                write_log("WARNING", "正则匹配失败，尝试第二备用方案：模糊匹配")
                # 查找包含"登"和"录"的按钮
                all_buttons = page.locator('button').all()
                for btn in all_buttons:
                    btn_text = btn.inner_text().strip()
                    if '登' in btn_text and '录' in btn_text:
                        btn.scroll_into_view_if_needed()
                        btn.click(force=True, timeout=3000)
                        write_log("SUCCESS", f"第二备用方案成功，按钮文本：{btn_text}")
                        st.success("✅ 第二备用方案完成登录点击")
                        time.sleep(1)
                        return
                raise Exception("所有备用方案均失败")
            except Exception as err3:
                write_log("ERROR", f"所有备用方案均失败：{str(err3)}")
                st.error(f"❌ 页面所有DIV容器内未找到【登 录】（1或2个空格）登录标签，无法执行登录")
                return


# ===================== 打开页面初始化浏览器 =====================
def open_login_page(account: str, password: str):
    global captcha_caught
    login_url = "https://hrmtest.whrhkj.com/user/login"
    captcha_caught = False
    st.session_state["captcha_base64"] = None
    st.session_state["ocr_captcha_result"] = ""
    write_log("INFO", f"启动浏览器，登录账号：{account}")
    try:
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = browser.new_context(no_viewport=True)
        page = ctx.new_page()
        st.session_state["page_instance"] = page
        st.session_state["browser_context"] = {"pw": p, "browser": browser}
        page.evaluate("()=>{window.moveTo(0,0);window.resizeTo(screen.width,screen.height)}")
        write_log("INFO", "浏览器窗口最大化完成")
        page.on("response", handle_network_response)
        page.goto(login_url, timeout=15000)
        capture_input_tags(page)

        # 等待验证码接口捕获
        wait_times = 0
        while not captcha_caught and wait_times < 8:
            time.sleep(0.5)
            wait_times += 1
        if not captcha_caught:
            write_log("WARNING", "超时未捕获验证码接口")

        # 填充账号密码
        fill_input_trigger(page, 'input[placeholder="请输入工号"]', account, "工号输入框")
        fill_input_trigger(page, 'input[placeholder="请输入密码"]', password, "密码输入框")
        return True
    except Exception as e:
        err_stack = traceback.format_exc()
        write_log("ERROR", f"打开页面异常：{str(e)}")
        write_log("ERROR", f"堆栈：\n{err_stack}")
        return False


# ===================== 释放浏览器资源 =====================
def close_browser():
    global captcha_caught
    ctx = st.session_state.get("browser_context")
    if ctx:
        try:
            ctx["browser"].close()
            ctx["pw"].stop()
            write_log("INFO", "浏览器资源释放完成")
        except Exception:
            pass
    st.session_state["page_instance"] = None
    st.session_state["browser_context"] = None
    st.session_state["captcha_base64"] = None
    st.session_state["ocr_captcha_result"] = ""
    captcha_caught = False


# ===================== Streamlit UI =====================
def main():
    st.set_page_config(page_title="DIV自动解析抓取登录标签", layout="wide")
    st.title("🔐 HRM自动化登录 | 自动遍历页面DIV容器抓取【登 录】Span")
    st.subheader("逻辑：JS递归扫描全部div → 定位目标span（兼容1或2个空格）→ 回溯父级button → 自动点击登录")
    st.divider()

    user_list = default_users
    user_name_list = [u["name"] for u in user_list]
    sel_user_name = st.selectbox("👤 选择登录账号", user_name_list)
    sel_user = next(u for u in user_list if u["name"] == sel_user_name)

    col1, col2 = st.columns(2)
    with col1:
        acc_input = st.text_input("工号", value=sel_user["account"])
    with col2:
        pwd_input = st.text_input("密码", value=sel_user["password"], type="password")

    st.divider()

    # 操作按钮行
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    with col_btn1:
        start_btn = st.button("🌐 一键启动自动化流程", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("🔄 重新执行登录", use_container_width=True):
            execute_login()
            st.rerun()
    with col_btn3:
        if st.button("🛑 关闭浏览器", use_container_width=True):
            close_browser()
            st.rerun()

    if start_btn:
        page_ok = open_login_page(acc_input, pwd_input)
        if page_ok:
            time.sleep(1.2)
            execute_login()
        st.rerun()

    st.divider()
    captcha_b64 = st.session_state.get("captcha_base64")
    ocr_res = st.session_state.get("ocr_captcha_result", "")
    if captcha_b64:
        st.subheader("🖼️ 验证码图片")
        st.image(captcha_b64)
        if ocr_res:
            st.success(f"✅ OCR识别验证码：{ocr_res} 已自动填入")
        else:
            st.warning("⚠️ OCR识别失败，可手动输入")
        manual_code = st.text_input("手动输入验证码覆盖自动识别")
        fill_btn = st.button("强制填入手动验证码")
        if fill_btn and manual_code.strip():
            auto_fill_captcha_input(manual_code.strip())
            st.rerun()
    else:
        st.info("点击上方一键启动，自动解析DIV、识别验证码并登录")

    st.divider()
    st.subheader("📜 运行日志 | [ELEMENT]DIV层级抓取日志 | [API]接口抓包")

    col_log1, col_log2 = st.columns([4, 1])
    with col_log2:
        clear_log = st.button("🗑️ 清空日志", use_container_width=True)
    if clear_log:
        st.session_state["log_messages"] = []
        st.rerun()

    log_box = st.container(height=350)
    with log_box:
        logs = st.session_state["log_messages"]
        if not logs:
            st.info("暂无运行日志")
        else:
            for line in logs[-80:]:
                if "[SUCCESS]" in line:
                    st.success(line)
                elif "[ERROR]" in line:
                    st.error(line)
                elif "[WARNING]" in line:
                    st.warning(line)
                elif "[ELEMENT]" in line or "[API]" in line or "[DEBUG]" in line:
                    st.info(line)
                else:
                    st.text(line)


if __name__ == "__main__":
    main()