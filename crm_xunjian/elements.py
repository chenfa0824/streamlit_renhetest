from crm_xunjian.log import add_log, create_new_local_log_file, close_local_log_file
import time


# ===================== 元素定位辅助函数 =====================
def wait_for_dom_ready(page, timeout=30000):
    add_log("⏳ 等待DOM完全加载...")
    try:
        page.wait_for_function(
            "document.readyState === 'complete'",
            timeout=timeout
        )
        add_log("✅ DOM已完全加载 (document.readyState = 'complete')")
    except Exception as e:
        add_log(f"⚠️ DOM加载等待超时，但继续执行：{str(e)}", "WARN")

def wait_for_element_ready(page, selector_config, timeout=10000, retry_interval=500):
    selector_type = selector_config["type"]
    selector_value = selector_config["value"]
    add_log(f"⏳ 等待元素就绪：{selector_type} = '{selector_value}'")
    time.sleep(2)
    start_time = time.time()
    element = None
    success = False
    while time.time() - start_time < timeout / 1000:
        try:
            element = get_element_by_selector(page, selector_config)
            if element.is_visible(timeout=100):
                success = True
                add_log(f"✅ 元素就绪：{selector_type} = '{selector_value}'")
                add_log(f"✅ 点击子菜单：{selector_value}")
                element.click()

                # data=page.get_element_by_selector(page, selector_config).click()
                # add_log(data.url)


                time.sleep(3)
                return success, element
        except Exception:
            pass
        time.sleep(retry_interval / 1000)
    add_log(f"⚠️ 元素等待超时：{selector_type} = '{selector_value}'", "WARN")
    return success, element



def get_element_by_selector(page, selector_config):
    selector_type = selector_config["type"]
    selector_value = selector_config["value"]
    if selector_type == "text":
        return page.get_by_text(selector_value, exact=True)
    elif selector_type == "role":
        parts = selector_value.split("|")
        role_name = parts[0]
        name = parts[1] if len(parts) > 1 else None
        if name:
            return page.get_by_role(role_name, name=name)
        else:
            return page.get_by_role(role_name)
    elif selector_type == "id":
        return page.locator(f"#{selector_value}")
    elif selector_type == "css":
        return page.locator(selector_value)
    else:
        return page.locator(selector_value)


def get_page_state_after_click(page):
    """点击后获取页面状态数据"""
    data = {
        "url": page.url,                    # 当前URL
        "title": page.title(),              # 页面标题
        "content_length": len(page.content()),  # HTML长度
        "text_content": page.text_content("body")[:500],  # 部分文本内容
        "page_info": page.evaluate("""
            () => ({
                readyState: document.readyState,
                scrollY: window.scrollY,
                innerHeight: window.innerHeight,
                outerHeight: window.outerHeight
            })
        """)
    }
    return data

def find_input_by_label(page, label_text, timeout=10000):
    add_log(f"🔍 通过标签文本定位输入框：'{label_text}'")
    try:
        label_element = page.get_by_text(label_text, exact=True).first
        if label_element and label_element.is_visible(timeout=1000):
            for_id = label_element.get_attribute("for")
            if for_id:
                input_element = page.locator(f"#{for_id}")
                if input_element.is_visible(timeout=1000):
                    add_log(f"✅ 通过 label[for='{for_id}'] 定位成功")
                    return True, input_element
        xpath = f"//label[contains(text(), '{label_text}')]//input"
        input_element = page.locator(f"xpath={xpath}")
        if input_element.is_visible(timeout=1000):
            add_log(f"✅ 通过包裹式 label 定位成功")
            return True, input_element
        input_element = page.locator(f"[aria-label='{label_text}']")
        if input_element.is_visible(timeout=1000):
            add_log(f"✅ 通过 aria-label 定位成功")
            return True, input_element
        input_element = page.locator(f"input[placeholder*='{label_text}']")
        if input_element.is_visible(timeout=1000):
            add_log(f"✅ 通过 placeholder 定位成功")
            return True, input_element
        xpath = f"//*[contains(text(), '{label_text}')]/following-sibling::input[1]"
        input_element = page.locator(f"xpath={xpath}")
        if input_element.is_visible(timeout=1000):
            add_log(f"✅ 通过相邻兄弟元素定位成功")
            return True, input_element
        xpath = f"//*[contains(text(), '{label_text}')]/ancestor::*[1]//input"
        input_element = page.locator(f"xpath={xpath}")
        if input_element.is_visible(timeout=1000):
            add_log(f"✅ 通过父级定位成功")
            return True, input_element
        name_map = {
            "用户名": ["username", "user_name", "user", "account"],
            "密码": ["password", "pwd", "pass"]
        }
        possible_names = name_map.get(label_text, [])
        for name in possible_names:
            input_element = page.locator(f"input[name='{name}']")
            if input_element.is_visible(timeout=500):
                add_log(f"✅ 通过 name 属性定位成功：{name}")
                return True, input_element
    except Exception as e:
        add_log(f"⚠️ 标签定位失败：{str(e)}", "WARN")
    add_log(f"❌ 无法通过标签文本 '{label_text}' 定位输入框", "WARN")
    return False, None

def fill_input_by_label(page, label_text, value, backup_selectors=None, timeout=10000):
    add_log(f"✏️ 通过标签 '{label_text}' 填充输入框")
    success, element = find_input_by_label(page, label_text, timeout)
    if success and element:
        element.fill(value)
        add_log(f"✅ 通过标签定位填充成功")
        return True
    if backup_selectors:
        for idx, backup_selector in enumerate(backup_selectors, 1):
            try:
                add_log(f"🔄 尝试备用选择器 #{idx}：{backup_selector['value']}")
                success, element = wait_for_element_ready(page, backup_selector, timeout=3000)
                if success and element:
                    element.fill(value)
                    add_log(f"✅ 填充成功（备用选择器 #{idx}）")
                    return True
            except Exception:
                continue
    add_log(f"❌ 所有定位方式均失败", "ERROR")
    return False

# ========== 优化：登录按钮点击函数优先匹配原生button标签 ==========
def click_button_by_span(page, span_text="登 录", timeout=10000):
    add_log(f"🖱️【优先原生button】定位按钮：'{span_text}'")
    try:
        # 策略1：最高优先级 匹配原生<button type="button/submit">包含登录文本
        btn_all = page.locator(f"button:has-text('登 录')")
        if btn_all.count() > 0:
            # 优先 type="button"
            btn_normal = page.locator(f"button[type='button']:has-text('{span_text}')")
            if btn_normal.count() > 0 and btn_normal.first.is_visible(timeout=timeout):
                btn_normal.first.click()
                add_log(f"✅ 优先匹配 type='button' 原生按钮点击成功")
                return True
            # 其次 type="submit"
            btn_submit = page.locator(f"button[type='submit']:has-text('{span_text}')")
            if btn_submit.count() > 0 and btn_submit.first.is_visible(timeout=timeout):
                btn_submit.first.click()
                add_log(f"✅ 匹配 type='submit' 原生按钮点击成功")
                return True
            # 通用button兜底
            btn_all.first.click()
            add_log(f"✅ 通用<button>标签按钮点击成功")
            return True
    except Exception as e:
        add_log(f"⚠️ 通过span文本定位按钮失败：{str(e)}", "WARN")
    add_log(f"❌ 无法通过原生<button>定位按钮 '{span_text}'", "WARN")
    return False

# 备用元素定位
def click_with_backup(page, primary_selector, backup_selectors, timeout=10000, description=""):
    add_log(f"🖱️ 尝试点击：{description or primary_selector['value']}")
    success, element = wait_for_element_ready(page, primary_selector, timeout=timeout)
    if success and element:
        element.click()
        add_log(f"✅ 点击成功（主选择器）")
        return True
    for idx, backup_selector in enumerate(backup_selectors, 1):
        try:
            add_log(f"🔄 尝试备用选择器 #{idx}：{backup_selector['value']}")
            success, element = wait_for_element_ready(page, backup_selector, timeout=3000)
            if success and element:
                element.click()
                add_log(f"✅ 点击成功（备用选择器 #{idx}）")
                return True
        except Exception:
            continue
    add_log(f"❌ 所有选择器均点击失败", "ERROR")
    return False
