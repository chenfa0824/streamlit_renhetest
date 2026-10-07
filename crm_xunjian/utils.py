import os
from datetime import datetime
from crm_xunjian.log import add_log



def save_screenshot_to_local(buf: bytes, screenshot_dir: str, is_error: bool = False) -> str:
    """将二进制截图保存至本地文件夹"""
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_tag = "异常" if is_error else "正常"
    file_name = f"巡检_{time_str}_{file_tag}.png"
    full_path = os.path.join(screenshot_dir, file_name)
    with open(full_path, "wb") as f:
        f.write(buf)
    add_log(f"📷 页面截图已持久化保存至本地：{full_path}")
    return full_path