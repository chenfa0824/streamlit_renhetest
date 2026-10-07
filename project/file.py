import streamlit as st
import os
import zipfile
from pathlib import Path
import pandas as pd
from io import BytesIO, StringIO

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="文件拆分工具",
    page_icon="📂",
    layout="wide"
)
st.title("📂 文件夹上传 & 文件拆分工具")

# --------------------------
# 临时目录（存储上传/拆分文件）
# --------------------------
UPLOAD_FOLDER = "uploaded_files"
SPLIT_FOLDER = "split_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SPLIT_FOLDER, exist_ok=True)

# --------------------------
# 清空目录工具函数
# --------------------------
def clear_directory(folder_path):
    """清空指定目录下的所有文件"""
    for f in Path(folder_path).glob("*"):
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass

# --------------------------
# 文件拆分核心函数
# --------------------------
def split_large_file(file_path, output_dir, max_lines=1000, max_size_mb=10):
    """
    拆分文件：按行数 / 按大小
    :param file_path: 原文件路径
    :param output_dir: 输出目录
    :param max_lines: 每个文件最大行数
    :param max_size_mb: 每个文件最大大小(MB)
    :return: 拆分后的文件列表
    """
    split_files = []
    file_name = Path(file_path).stem
    file_ext = Path(file_path).suffix.lower()
    max_size_bytes = max_size_mb * 1024 * 1024

    # 1. 处理 文本/CSV 文件
    if file_ext in [".txt", ".csv", ".log"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        total = len(lines)
        part_num = 1

        for i in range(0, total, max_lines):
            chunk = lines[i:i + max_lines]
            part_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            
            with open(part_path, "w", encoding="utf-8") as f:
                f.writelines(chunk)
            
            split_files.append(part_path)
            part_num += 1

    # 2. 处理 Excel 文件
    elif file_ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
        total = len(df)
        part_num = 1

        for i in range(0, total, max_lines):
            chunk = df.iloc[i:i + max_lines]
            part_path = os.path.join(output_dir, f"{file_name}_part{part_num}{file_ext}")
            chunk.to_excel(part_path, index=False)
            split_files.append(part_path)
            part_num += 1

    return split_files

# --------------------------
# 打包下载 ZIP
# --------------------------
def create_zip(files):
    """将文件列表打包为 ZIP"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(file, arcname=os.path.basename(file))
    zip_buffer.seek(0)
    return zip_buffer

# --------------------------
# 主界面逻辑
# --------------------------
st.subheader("1. 上传文件夹")
uploaded_files = st.file_uploader(
    "选择一个文件夹（支持多文件、子文件夹）",
    accept_multiple_files=True,
    type=["txt", "csv", "xlsx", "xls", "log"]
)

# 拆分参数
st.subheader("2. 拆分设置")
col1, col2 = st.columns(2)
with col1:
    max_lines = st.number_input("每个文件最大行数", min_value=100, value=1000, step=100)
with col2:
    max_size_mb = st.number_input("每个文件最大大小(MB)", min_value=1, value=10, step=1)

# 执行按钮
run_split = st.button("▶️ 开始拆分", type="primary")

# 执行流程
if run_split and uploaded_files:
    # 清空旧文件
    clear_directory(UPLOAD_FOLDER)
    clear_directory(SPLIT_FOLDER)

    st.success("✅ 开始处理...")
    progress_bar = st.progress(0)
    all_split_files = []

    # 遍历上传文件
    for idx, file in enumerate(uploaded_files):
        # 保存上传文件
        save_path = os.path.join(UPLOAD_FOLDER, file.name)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())

        # 拆分文件
        st.info(f"正在拆分：{file.name}")
        split_files = split_large_file(
            save_path,
            SPLIT_FOLDER,
            max_lines=int(max_lines),
            max_size_mb=int(max_size_mb)
        )
        all_split_files.extend(split_files)

        # 更新进度
        progress_bar.progress((idx + 1) / len(uploaded_files))

    # 完成
    st.success(f"🎉 拆分完成！共生成 {len(all_split_files)} 个文件")

    # 生成 ZIP 下载
    zip_data = create_zip(all_split_files)
    st.download_button(
        label="📥 下载所有拆分文件（ZIP）",
        data=zip_data,
        file_name="拆分文件包.zip",
        mime="application/zip"
    )

elif run_split and not uploaded_files:
    st.warning("⚠️ 请先上传文件夹！")

# 说明
st.markdown("---")
st.markdown("""
### 使用说明
1. 点击上传框，**选择整个文件夹**（支持多文件）
2. 设置拆分参数（行数/大小）
3. 点击「开始拆分」
4. 拆分完成后下载 ZIP 包
""")