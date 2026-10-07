
import os
from datetime import datetime
import streamlit as st
import time

# ===================== 导入配置文件 =====================
from crm_xunjian.config import (
    SCREENSHOT_DIR,
    LOG_DIR,
    USERNAME,
    TARGET_URL,
    LOCAL_LOG_FILE,
    BrowserConfig
)

def add_log(text: str, level: str = "INFO", exception_trace: str = None):
    """写入日志：内存日志+本地文件日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{now}] [{level}] {text}"
    st.session_state.run_logs.append(log_line)

    if LOCAL_LOG_FILE is not None:
        LOCAL_LOG_FILE.write(log_line + "\n")
        if exception_trace and len(exception_trace.strip()) > 0:
            LOCAL_LOG_FILE.write(f"[{now}] [TRACE] 异常堆栈详情：\n{exception_trace}\n")
        LOCAL_LOG_FILE.flush()

def create_new_local_log_file(log_dir: LOG_DIR, login_user: USERNAME, target_url: TARGET_URL, headless: bool) -> str:
    """创建全新日志文件，写入头部信息"""
    global LOCAL_LOG_FILE
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"巡检日志_{time_str}.log"
    full_log_path = os.path.join(log_dir, log_filename)
    file_handle = open(full_log_path, "a", encoding="utf-8")
    file_handle.write("=" * 80 + "\n")
    file_handle.write(f"巡检启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    file_handle.write(f"登录账号：{login_user}\n")
    file_handle.write(f"目标登录地址：{target_url}\n")
    file_handle.write(f"无头模式：{headless}\n")
    file_handle.write("=" * 80 + "\n")
    file_handle.flush()
    LOCAL_LOG_FILE = file_handle
    add_log(f"📄 本次巡检独立日志文件已创建，本地路径：{full_log_path}")
    return full_log_path

def close_local_log_file():
    """关闭日志文件并写入结束标记"""
    global LOCAL_LOG_FILE
    if LOCAL_LOG_FILE is not None:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        LOCAL_LOG_FILE.write("=" * 80 + "\n")
        LOCAL_LOG_FILE.write(f"巡检流程结束时间：{end_time}\n")
        LOCAL_LOG_FILE.write("=" * 80 + "\n\n")
        LOCAL_LOG_FILE.close()
        LOCAL_LOG_FILE = None
        add_log("📄 本地日志文件已正常关闭保存")