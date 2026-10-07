from playwright.sync_api import sync_playwright
import json
from log import add_log
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import unicodedata

# 存储所有捕获到的接口列表
api_list = []

# -------------------------- Excel初始化与样式配置 --------------------------
# 初始化Excel工作簿
wb = Workbook()
ws = wb.active
ws.title = "捕获接口清单"

# 表头配置（严格匹配你的需求：接口名、请求方法、返回码）
headers = ["接口地址", "请求方法", "返回状态码"]
# 表头样式（符合专业Excel视觉规范）
header_fill = PatternFill('solid', fgColor='0070C0')  # 低饱和度蓝色背景
header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)  # 白色加粗字体
center_align = Alignment(horizontal='center', vertical='center')  # 居中对齐
left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)  # 左对齐+自动换行

# 写入表头
for col_idx, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col_idx, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center_align
ws.row_dimensions[1].height = 25  # 表头行高

# 已写入的接口唯一标识集合，用于去重（避免重复写入相同接口）
written_apis = set()


# 列宽自动适配函数：根据内容自动调整列宽，适配中文/长URL
def display_width(text):
    """计算文本显示宽度，中文/全角字符算2个宽度，其余算1个"""
    return sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in str(text or ''))


def auto_fit_columns(ws, min_w=8, max_w=80, padding=3):
    """自动适配列宽，设置合理的上下限，保证阅读体验"""
    for col_cells in ws.columns:
        letter = col_cells[0].column_letter
        max_width = max(
            (display_width(c.value) for c in col_cells
             if not isinstance(c, openpyxl.cell.cell.MergedCell) and c.value is not None),
            default=0
        )
        final_width = max(min_w, min(max_width * 1.1 + padding, max_w))
        ws.column_dimensions[letter].width = final_width


# -------------------------- 接口捕获核心逻辑 --------------------------
def capture_response(response):
    """监听响应，只抓取XHR/Fetch后台接口"""
    # 过滤只保留ajax接口，过滤静态资源（css/js/img）
    if response.request.resource_type in ["xhr", "fetch"]:
        req = response.request
        # 组装接口信息
        api_info = {
            "url": req.url,
            "method": req.method,
            "request_headers": req.headers,
            "response_status": response.status,
            "response_headers": response.headers,
            "query_params": req.url.split("?")[1] if "?" in req.url else "",
        }
        # 捕获请求入参（POST接口）
        if req.method == "POST":
            try:
                api_info["post_data"] = req.post_data
            except:
                api_info["post_data"] = None
        # 捕获返回JSON
        try:
            api_info["response_body"] = response.json()
        except Exception as e:
            api_info["response_body"] = response.text()
        api_list.append(api_info)
        # 日志输出
        add_log(f"捕获接口：{req.method} {req.url}")
        add_log(f"请求结果：{response.status}")

        # -------------------------- 写入Excel核心逻辑 --------------------------
        # 生成接口唯一标识，用于去重（请求方法+接口地址+返回状态码）
        api_unique_key = f"{req.method}_{req.url}_{response.status}"
        if api_unique_key not in written_apis:
            written_apis.add(api_unique_key)
            # 获取当前数据行号
            current_row = ws.max_row + 1
            # 写入接口地址（第一列）
            url_cell = ws.cell(row=current_row, column=1, value=req.url)
            url_cell.alignment = left_align
            # 写入请求方法（第二列）
            method_cell = ws.cell(row=current_row, column=2, value=req.method)
            method_cell.alignment = center_align
            # 写入返回状态码（第三列）
            status_cell = ws.cell(row=current_row, column=3, value=response.status)
            status_cell.alignment = center_align
            # 设置数据行高
            ws.row_dimensions[current_row].height = 20
            # 自动适配列宽
            auto_fit_columns(ws)
            # 实时保存Excel文件，避免程序崩溃导致数据丢失
            wb.save('/mnt/捕获接口清单.xlsx')


# -------------------------- 主运行逻辑 --------------------------
if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        # 绑定响应监听
        page.on("response", capture_response)
        # 这里替换为你要访问的目标页面
        page.goto("https://example.com")
        # 保持页面运行，可根据需要调整
        input("按回车键退出...")
        browser.close()
    # 程序退出前最终保存一次，确保所有数据都完整写入
    wb.save('/mnt/捕获接口清单.xlsx')
    print(f"✅ 程序运行结束，共捕获 {len(api_list)} 个接口，已去重后写入Excel {len(written_apis)} 个唯一接口")