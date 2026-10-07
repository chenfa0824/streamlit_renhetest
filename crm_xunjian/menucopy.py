import time
import streamlit as st
from typing import List, Dict, Tuple
from crm_xunjian.elements import click_with_backup, wait_for_element_ready, wait_for_dom_ready
from apicopy import init_api_listener,validate_api_records

from crm_xunjian.log import add_log

# ===================== 导入配置文件 =====================
from config import (
    SCREENSHOT_DIR,
    LOG_DIR,
    Selectors,
    InspectionConfig,
    ElementLabels,
    BrowserConfig
)

def expand_menu_and_get_submenus(page, menu_name, timeout=5000):
    """
    展开菜单并获取子菜单列表（增强版，支持多种UI框架）
    返回: (是否成功, 子菜单列表)
    """
    add_log(f"📂 展开菜单: {menu_name}")

    try:
        # 1. 定位菜单元素 - 使用更精确的定位策略
        menu_element = None
        menu_found = False

        # 策略1: 通过文本精确定位（使用exact匹配）
        try:
            menu_element = page.get_by_text(menu_name, exact=True).first
            if menu_element.is_visible(timeout=1000):
                menu_found = True
                add_log(f"✅ 通过精确文本定位到菜单: {menu_name}")
        except:
            pass

        # 策略2: 通过包含文本定位（兜底）
        if not menu_found:
            try:
                menu_element = page.locator(f"li:has-text('{menu_name}'), div:has-text('{menu_name}')").first
                if menu_element.is_visible(timeout=1000):
                    menu_found = True
                    add_log(f"✅ 通过包含文本定位到菜单: {menu_name}")
            except:
                pass

        if not menu_found:
            add_log(f"❌ 未找到菜单: {menu_name}", "ERROR")
            return False, []

        # 2. 检查并展开菜单
        is_expanded = False

        # 检查是否已展开（多种属性检查）
        try:
            # 检查 aria-expanded
            aria_expanded = menu_element.get_attribute("aria-expanded")
            if aria_expanded == "true":
                is_expanded = True
                add_log(f"✅ 菜单 {menu_name} 已展开 (aria-expanded=true)")
        except:
            pass

        if not is_expanded:
            try:
                # 检查 class 是否包含展开状态
                class_attr = menu_element.get_attribute("class")
                if class_attr and any(keyword in class_attr for keyword in ["open", "expanded", "active"]):
                    is_expanded = True
                    add_log(f"✅ 菜单 {menu_name} 已展开 (class包含展开状态)")
            except:
                pass

        # 如果未展开，执行展开操作
        if not is_expanded:
            try:
                # 尝试点击菜单文本
                menu_element.click()
                add_log(f"🖱️ 点击展开菜单: {menu_name}")
                time.sleep(0.8)  # 等待动画
            except Exception as e:
                add_log(f"⚠️ 点击菜单失败: {str(e)}", "WARN")

                # 尝试点击展开箭头
                try:
                    arrow_selectors = [
                        f"xpath=//*[contains(text(), '{menu_name}')]/following-sibling::*[contains(@class, 'arrow')]",
                        f"xpath=//*[contains(text(), '{menu_name}')]/../*[contains(@class, 'arrow')]",
                        f"xpath=//*[contains(text(), '{menu_name}')]/parent::*//i[contains(@class, 'arrow')]",
                        f"xpath=//*[contains(text(), '{menu_name}')]/preceding-sibling::*[contains(@class, 'arrow')]"
                    ]

                    for selector in arrow_selectors:
                        try:
                            arrow = page.locator(selector).first
                            if arrow.count() > 0 and arrow.is_visible(timeout=500):
                                arrow.click()
                                add_log(f"🖱️ 通过箭头展开菜单: {menu_name}")
                                time.sleep(0.8)
                                break
                        except:
                            continue
                except:
                    pass

        # 等待菜单展开
        time.sleep(0.5)

        # 3. 获取子菜单 - 使用多种策略
        submenus = []
        parent_li = None

        # 获取父级li元素（用于限定范围）
        try:
            parent_li = menu_element.locator("xpath=./ancestor::li").first
            if not parent_li.count():
                parent_li = menu_element.locator("xpath=./..").first
        except:
            pass

        # 策略1: 通过父级限定获取子菜单（最精确）
        if parent_li and parent_li.count():
            try:
                # 各种UI框架的子菜单选择器
                sub_selector_templates = [
                    "./ul/li",  # 直接子级
                    "./ul//li",  # 所有后代li
                    "./div/ul/li",
                    "./div//ul//li",
                    ".//ul/li",
                    ".//div/ul/li",
                ]

                for selector_template in sub_selector_templates:
                    try:
                        elements = parent_li.locator(selector_template).all()
                        for elem in elements:
                            try:
                                text = elem.text_content()
                                if text and text.strip():
                                    # 过滤掉父菜单名称和空白
                                    cleaned = text.strip().replace('\n', '').replace('\t', '')
                                    if cleaned and cleaned != menu_name:
                                        submenus.append(cleaned)
                            except:
                                continue
                        if submenus:
                            add_log(f"✅ 通过父级限定获取到 {len(submenus)} 个子菜单")
                            break
                    except:
                        continue
            except Exception as e:
                add_log(f"⚠️ 父级限定获取子菜单异常: {str(e)}", "WARN")

        # 策略2: 通过CSS选择器获取（如果策略1失败）
        if not submenus:
            add_log("🔄 尝试CSS选择器获取子菜单...")
            try:
                # 先找到菜单项的li容器
                menu_li = menu_element.locator("xpath=./ancestor::li").first
                if menu_li.count():
                    # 在li容器内查找子菜单
                    sub_selectors = [
                        "ul li",
                        "div ul li",
                        "ul .menu-item",
                        "ul .el-menu-item",
                        "ul .ant-menu-item",
                        "ul .sub-menu li",
                        ".sub-menu li",
                        ".menu-item"
                    ]

                    for selector in sub_selectors:
                        try:
                            elements = menu_li.locator(selector).all()
                            for elem in elements:
                                try:
                                    text = elem.text_content()
                                    if text and text.strip():
                                        cleaned = text.strip().replace('\n', '').replace('\t', '')
                                        if cleaned and cleaned != menu_name:
                                            submenus.append(cleaned)
                                except:
                                    continue
                            if submenus:
                                add_log(f"✅ 通过CSS选择器获取到 {len(submenus)} 个子菜单")
                                break
                        except:
                            continue
            except Exception as e:
                add_log(f"⚠️ CSS选择器获取子菜单异常: {str(e)}", "WARN")

        # 策略3: 通过文本模式获取（兜底）
        if not submenus:
            add_log("🔄 尝试文本模式获取子菜单...")
            try:
                # 获取菜单附近的所有文本
                parent_element = menu_element.locator("xpath=./ancestor::li").first
                if parent_element.count():
                    all_text = parent_element.text_content()
                    # 按换行分割，过滤出可能的子菜单
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    for line in lines:
                        if line != menu_name and not line.startswith(' '):
                            # 检查是否是菜单项（通常不包含特殊字符）
                            if len(line) < 50 and not any(c in line for c in ['/', '\\', 'http']):
                                submenus.append(line)
            except:
                pass

        # 去重并过滤
        submenus = list(dict.fromkeys(submenus))

        # 过滤掉父菜单名称
        submenus = [s for s in submenus if s != menu_name]

        if submenus:
            add_log(f"✅ 菜单 {menu_name} 共有 {len(submenus)} 个子菜单: {', '.join(submenus)}")
        else:
            add_log(f"ℹ️ 菜单 {menu_name} 暂无子菜单或未展开")

        return True, submenus

    except Exception as e:
        add_log(f"❌ 展开菜单异常: {str(e)}", "ERROR")
        return False, []

def get_all_submenu_items(page, parent_menu, timeout=5000):
    """
    递归获取菜单的所有子菜单项（支持多级）
    返回: 子菜单列表（扁平化）
    """
    add_log(f"📋 递归获取菜单 '{parent_menu}' 的所有子菜单...")

    all_submenus = []
    visited = set()

    def _get_submenus_recursive(menu_name, level=0):
        """递归获取子菜单"""
        indent = "  " * level
        add_log(f"{indent}🔍 检查菜单: {menu_name}")

        # 展开当前菜单
        success, submenus = expand_menu_and_get_submenus(page, menu_name, timeout)

        if not success:
            add_log(f"{indent}❌ 无法展开菜单: {menu_name}", "WARN")
            return

        for sub in submenus:
            if sub in visited:
                continue
            visited.add(sub)
            all_submenus.append({
                "name": sub,
                "parent": menu_name,
                "level": level + 1
            })
            add_log(f"{indent}  📄 子菜单: {sub}")

            # 递归检查子菜单是否还有下级
            # 先尝试展开查看是否有下级
            try:
                sub_selector = {"type": "text", "value": sub}
                success_sub, sub_element = wait_for_element_ready(page, sub_selector, timeout=2000)
                if success_sub:
                    # 尝试点击展开
                    try:
                        # 检查是否有展开图标
                        has_arrow = page.locator(f"//*[contains(text(), '{sub}')]/following-sibling::*[contains(@class, 'arrow')]").count() > 0
                        if has_arrow:
                            sub_element.click()
                            time.sleep(0.3)
                            # 递归获取下级
                            _get_submenus_recursive(sub, level + 1)
                    except:
                        pass
            except:
                pass

    # 开始递归
    _get_submenus_recursive(parent_menu)

    add_log(f"✅ 菜单 '{parent_menu}' 共发现 {len(all_submenus)} 个子菜单（含多级）")
    return all_submenus

def click_submenu(page, parent_menu, submenu_name, timeout=5000):
    """
    点击指定的子菜单
    返回: 是否成功
    """
    add_log(f"🖱️ 点击子菜单: {submenu_name}")

    try:
        # 先确保父菜单已展开
        expand_menu_and_get_submenus(page, parent_menu, timeout)

        # 尝试多种方式定位子菜单
        submenu_selectors = [
            {"type": "text", "value": submenu_name},
            {"type": "css", "value": f"li:has-text('{submenu_name}')"},
            {"type": "css", "value": f"xpath=//*[contains(text(), '{parent_menu}')]/ancestor::li//*[contains(text(), '{submenu_name}')]"},
            {"type": "role", "value": f"menuitem|{submenu_name}"}
        ]

        for selector in submenu_selectors:
            try:
                success, element = wait_for_element_ready(page, selector, timeout=2000)
                if success and element:
                    element.click()
                    add_log(f"✅ 成功点击子菜单: {submenu_name}")
                    page.wait_for_load_state("networkidle", timeout=10000)
                    time.sleep(1)
                    return True
            except Exception as e:
                continue

        add_log(f"❌ 无法点击子菜单: {submenu_name}", "ERROR")
        return False

    except Exception as e:
        add_log(f"❌ 点击子菜单异常: {str(e)}", "ERROR")
        return False

def click_and_verify_submenu(page, parent_menu, submenu_name, timeout=10000):
    """
    点击子菜单并验证页面是否正常加载
    返回: (是否成功, 页面截图, 错误信息)
    """
    add_log(f"🔍 验证子菜单: {parent_menu} -> {submenu_name}")

    try:
        current_url = page.url

        if click_submenu(page, parent_menu, submenu_name):
            time.sleep(1)
            new_url = page.url

            if new_url != current_url:
                add_log(f"✅ 子菜单 {submenu_name} 跳转成功: {new_url}")
                return True, None, None
            else:
                # 检查是否有新内容加载
                page.wait_for_load_state("networkidle", timeout=5000)
                add_log(f"ℹ️ 子菜单 {submenu_name} 在当前页面加载内容")
                return True, None, None
        else:
            error_msg = f"点击子菜单 {submenu_name} 失败"
            add_log(f"❌ {error_msg}", "ERROR")
            return False, None, error_msg

    except Exception as e:
        error_msg = str(e)
        add_log(f"❌ 验证子菜单异常: {error_msg}", "ERROR")
        try:
            screenshot = page.screenshot(full_page=True)
            return False, screenshot, error_msg
        except:
            return False, None, error_msg


# 重写verify_all_submenus函数（集成接口校验）
def verify_all_submenus(page, menu_name: str, submenus: List[str], timeout: int = 10000) -> Tuple[
    List[Dict], List[Dict]]:
    """
    批量验证子菜单（含接口校验）
    :return: (成功列表, 失败列表)
    """
    success_list = []
    failed_list = []

    for submenu in submenus:
        success, msg = verify_submenu_with_api(page, menu_name, submenu, timeout)
        if success:
            success_list.append({"子菜单": submenu, "信息": msg})
        else:
            failed_list.append({"子菜单": submenu, "错误信息": msg})

    return success_list, failed_list


# ===================== 子菜单验证增强（含接口校验） =====================
def verify_submenu_with_api(page, menu_name: str, submenu_name: str, timeout: int = 10000) -> Tuple[bool, str]:
    """
    验证子菜单点击+页面加载+接口校验
    :return: (是否成功, 错误信息/成功信息)
    """
    try:
        # 1. 点击子菜单
        add_log(f"🔍 验证子菜单：{menu_name} -> {submenu_name}")
        if not click_with_backup(
                page,
                f"//span[text()='{submenu_name}']",
                [{"type": "text", "value": submenu_name}],
                description=f"子菜单{submenu_name}"
        ):
            raise Exception("子菜单定位失败")

        # 2. 等待页面完全加载（DOM+网络空闲）
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        page.wait_for_load_state("networkidle", timeout=timeout)
        wait_for_dom_ready(page, timeout=timeout)
        time.sleep(1)  # 兜底等待
        add_log(f"✅ 子菜单[{submenu_name}]页面DOM+网络完全加载")

        # 3. 初始化接口监听并等待接口请求完成
        api_records = init_api_listener(page)
        time.sleep(2)  # 等待接口请求完成（可根据业务调整）

        # 4. 校验接口并记录异常
        api_errors = validate_api_records(api_records, menu_name, submenu_name)
        st.session_state.api_all_list.extend(api_records)  # 存储所有接口
        st.session_state.api_error_list.extend(api_errors)  # 存储异常接口

        return True, f"验证成功，检测到{len(api_records)}个接口，异常{len(api_errors)}个"

    except Exception as e:
        err_msg = f"子菜单[{submenu_name}]验证失败：{str(e)}"
        add_log(f"❌ {err_msg}", "ERROR")
        return False, err_msg

def get_all_menu_items_recursive(page, timeout=5000):
    """
    获取所有菜单项（包括多级子菜单）
    返回: 完整的菜单层级结构
    """
    add_log("📋 开始递归获取所有菜单项...")

    menu_structure = {}

    for menu in Selectors.SIDEBAR_MENUS:
        add_log(f"\n📂 处理主菜单: {menu}")

        # 递归获取所有子菜单
        submenus = get_all_submenu_items(page, menu, timeout)

        menu_structure[menu] = {
            "submenus": [s["name"] for s in submenus],
            "all_submenus": submenus  # 包含层级信息
        }

        add_log(f"✅ 主菜单 '{menu}' 共有 {len(submenus)} 个子菜单")

    add_log(f"✅ 获取到 {len(menu_structure)} 个主菜单")
    return menu_structure





# ========== 可选：逐个点击子菜单验证 ==========
def verify_submenu_click(page, parent_menu, submenu, timeout=10000):
    """
    验证子菜单点击是否正常工作
    """
    add_log(f"🔍 验证子菜单: {parent_menu} -> {submenu}")

    try:
        # 记录当前URL
        current_url = page.url

        # 点击子菜单
        if click_submenu(page, parent_menu, submenu):
            # 检查页面是否发生变化
            time.sleep(1)
            new_url = page.url

            if new_url != current_url:
                add_log(f"✅ 子菜单 {submenu} 跳转成功: {new_url}")
                return True
            else:
                # 可能是在同一页面加载内容
                # 检查是否有新内容加载
                page.wait_for_load_state("networkidle", timeout=5000)
                add_log(f"ℹ️ 子菜单 {submenu} 可能在当前页面加载内容")
                return True
        else:
            add_log(f"❌ 子菜单 {submenu} 点击失败", "ERROR")
            return False

    except Exception as e:
        add_log(f"❌ 验证子菜单异常: {str(e)}", "ERROR")
        return False

