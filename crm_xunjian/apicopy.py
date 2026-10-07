from playwright.sync_api import sync_playwright
import json
from crm_xunjian.log import add_log


# 存储所有捕获到的接口列表
api_list = []

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
        # print(f"捕获接口：{req.method} {req.url}")
        add_log(f"捕获接口：{req.method} {req.url}")
        add_log(f"请求结果：{response.json()}")