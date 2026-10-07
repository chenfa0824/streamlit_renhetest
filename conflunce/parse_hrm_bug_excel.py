#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HRM平台-绩效管理模块 Bug清单 Excel 解析工具
================================================
功能：
  1. 自动修复 WPS 生成的 xlsx 样式兼容性问题（空 <fill/> 导致 openpyxl 报错）
  2. 解析所有 Sheet，提取 Bug 清单数据
  3. Excel 日期序列号 → 标准日期字符串
  4. 自动过滤全空行
  5. 提取嵌入的问题截图图片
  6. 导出结构化 JSON / CSV / 统计摘要

依赖：pip install pandas openpyxl
用法：python parse_hrm_bug_excel.py <xlsx文件路径>
"""

import os
import sys
import re
import json
import shutil
import zipfile
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

# ============================================================
# 常量
# ============================================================
NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXCEL_EPOCH = datetime(1899, 12, 30)  # Excel 日期基准（含1900闰年bug修正）

# Bug清单标准列名映射（表头可能存在合并单元格/空列，这里做归一化）
COLUMN_MAP = {
    "A": "序号",
    "B": "测试时间",
    "C": "所属模块/前置条件",
    "D": "bug标题",
    "E": "用例步骤",
    "F": "预期结果",
    "G": "实际结果",
    "H": "bug分类",
    "I": "问题截图1",
    "J": "问题截图2",
    "K": "备注",
    "L": "开发确认bug",
    "M": "开发人员",
    "N": "开发处理状态",
    "O": "复测时间",
    "P": "复测结果",
    "Q": "一轮复测问题+截图",
    "W": "相应系统",
    "X": "需求名称",
    "Y": "产品",
    "Z": "优先级",
    "AA": "严重程度",
    "AB": "缺陷类型",
}


# ============================================================
# 第一步：修复 WPS 样式兼容性问题
# ============================================================
def fix_wps_styles(xlsx_path: str, output_path: str) -> str:
    """
    修复 WPS 生成的 xlsx 中 styles.xml 的空 <fill/> 元素。
    openpyxl 要求每个 <fill> 必须包含 <patternFill> 子元素，
    而 WPS 可能生成空的 <fill/>，导致 TypeError: Fill() takes no arguments。

    返回修复后的文件路径。
    """
    with zipfile.ZipFile(xlsx_path, "r") as zin:
        names = zin.namelist()
        styles_xml = zin.read("xl/styles.xml").decode("utf-8")

        # 检查是否存在空 <fill/> 或 <fill></fill>
        has_empty_fill = bool(re.search(r"<fill\s*/>|<fill>\s*</fill>", styles_xml))

        if not has_empty_fill:
            # 无需修复，直接返回原文件
            return xlsx_path

        print(f"[修复] 检测到 WPS 空 <fill/> 样式，正在修复 styles.xml ...")

        # 将空 fill 替换为默认 patternFill（none 模式）
        fixed_styles = re.sub(
            r"<fill\s*/>|<fill>\s*</fill>",
            '<fill><patternFill patternType="none"/></fill>',
            styles_xml,
        )

        # 重新打包
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in names:
                if item == "xl/styles.xml":
                    zout.writestr(item, fixed_styles)
                else:
                    zout.writestr(item, zin.read(item))

    print(f"[修复] 已输出修复后的文件: {output_path}")
    return output_path


# ============================================================
# 第二步：Excel 日期序列号转换
# ============================================================
def excel_serial_to_date(serial) -> str:
    """将 Excel 日期序列号 / datetime 对象转换为 YYYY-MM-DD 字符串。"""
    if pd.isna(serial) or serial == "":
        return ""
    # pandas 可能已自动转为 datetime 对象
    if isinstance(serial, datetime):
        return serial.strftime("%Y-%m-%d")
    if hasattr(serial, "strftime"):
        return serial.strftime("%Y-%m-%d")
    try:
        serial = float(serial)
        if serial < 1:
            return ""
        dt = EXCEL_EPOCH + timedelta(days=int(serial))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(serial)


# ============================================================
# 第三步：读取并解析 Sheet 数据
# ============================================================
def parse_bug_sheet(xlsx_path: str, sheet_name: str = None) -> pd.DataFrame:
    """
    读取指定 Sheet，返回清洗后的 Bug 清单 DataFrame。
    - 自动识别表头行
    - 日期列转换
    - 过滤全空行
    - 列名归一化
    """
    # 读取原始数据（不设 header，自己处理）
    df_raw = pd.read_excel(
        xlsx_path,
        sheet_name=sheet_name if sheet_name else 0,
        header=None,
        engine="openpyxl",
        dtype=object,
    )

    if df_raw.empty:
        return pd.DataFrame()

    # 第1行是表头（可能有合并单元格导致部分列为NaN）
    header_row = df_raw.iloc[0].tolist()
    data_df = df_raw.iloc[1:].copy()
    data_df.columns = range(len(header_row))

    # 用标准列名映射重命名（按列位置 A, B, C...）
    col_letters = []
    for i in range(len(header_row)):
        col_letters.append(_col_index_to_letter(i))

    rename_dict = {}
    for i, letter in enumerate(col_letters):
        if letter in COLUMN_MAP:
            rename_dict[i] = COLUMN_MAP[letter]
        else:
            rename_dict[i] = f"未命名列_{letter}"

    data_df = data_df.rename(columns=rename_dict)

    # 日期列转换
    date_cols = ["测试时间", "复测时间"]
    for col in date_cols:
        if col in data_df.columns:
            data_df[col] = data_df[col].apply(excel_serial_to_date)

    # 过滤全空行（所有核心字段都为空）
    core_cols = [c for c in ["bug标题", "用例步骤", "实际结果", "bug分类"] if c in data_df.columns]
    if core_cols:
        mask = data_df[core_cols].apply(
            lambda row: all(pd.isna(v) or str(v).strip() == "" for v in row), axis=1
        )
        data_df = data_df[~mask].reset_index(drop=True)

    # 重置序号
    if "序号" in data_df.columns:
        data_df["序号"] = range(1, len(data_df) + 1)

    # 去除全空列
    data_df = data_df.dropna(axis=1, how="all")

    return data_df


def _col_index_to_letter(index: int) -> str:
    """0-based 列索引转 Excel 列字母（0→A, 25→Z, 26→AA）。"""
    result = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


# ============================================================
# 第四步：提取嵌入图片
# ============================================================
def extract_images(xlsx_path: str, output_dir: str) -> list:
    """
    从 xlsx 中提取所有嵌入图片，返回图片路径列表。
    兼容标准路径 xl/media/ 和 WPS 路径 xl/drawings/media/。
    """
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    image_exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wmf", ".emf", ".tiff")
    extracted = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        media_files = [
            n for n in z.namelist()
            if n.lower().endswith(image_exts) and not n.endswith("/")
        ]
        for mf in sorted(media_files):
            fname = os.path.basename(mf)
            out_path = os.path.join(img_dir, fname)
            with z.open(mf) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(out_path)

    print(f"[图片] 共提取 {len(extracted)} 张嵌入图片 → {img_dir}")
    return extracted


# ============================================================
# 第五步：数据统计摘要
# ============================================================
def generate_stats(df: pd.DataFrame) -> dict:
    """生成 Bug 数据统计摘要。"""
    stats = {
        "总Bug数": len(df),
        "按bug分类统计": {},
        "按开发人员统计": {},
        "按复测结果统计": {},
        "按严重程度统计": {},
        "按优先级统计": {},
    }

    for col, key in [
        ("bug分类", "按bug分类统计"),
        ("开发人员", "按开发人员统计"),
        ("复测结果", "按复测结果统计"),
        ("严重程度", "按严重程度统计"),
        ("优先级", "按优先级统计"),
    ]:
        if col in df.columns:
            vc = df[col].dropna()
            vc = vc[vc.astype(str).str.strip() != ""]
            stats[key] = vc.value_counts().to_dict()

    return stats


# ============================================================
# 主流程
# ============================================================
def main(xlsx_path: str):
    if not os.path.exists(xlsx_path):
        print(f"[错误] 文件不存在: {xlsx_path}")
        sys.exit(1)

    base_name = Path(xlsx_path).stem
    output_dir = os.path.join(os.path.dirname(os.path.abspath(xlsx_path)), f"{base_name}_解析输出")
    os.makedirs(output_dir, exist_ok=True)

    # ---------- 1. 修复样式 ----------
    fixed_path = os.path.join(output_dir, f"{base_name}_fixed.xlsx")
    safe_xlsx = fix_wps_styles(xlsx_path, fixed_path)

    # ---------- 2. 获取所有 Sheet 名 ----------
    xls = pd.ExcelFile(safe_xlsx, engine="openpyxl")
    sheet_names = xls.sheet_names
    print(f"\n[信息] 文件包含 {len(sheet_names)} 个 Sheet: {sheet_names}")

    all_results = {}

    for sheet_name in sheet_names:
        print(f"\n{'='*60}")
        print(f"[解析] Sheet: {sheet_name}")
        print(f"{'='*60}")

        # ---------- 3. 解析数据 ----------
        df = parse_bug_sheet(safe_xlsx, sheet_name)
        all_results[sheet_name] = df

        print(f"[结果] 有效 Bug 记录数: {len(df)}")
        print(f"[结果] 列: {list(df.columns)}")

        # ---------- 4. 打印预览 ----------
        if not df.empty:
            print(f"\n[数据预览] 前 {min(5, len(df))} 条:")
            preview_cols = [c for c in ["序号", "测试时间", "bug标题", "bug分类", "开发人员", "复测结果"] if c in df.columns]
            print(df[preview_cols].to_string(index=False, max_colwidth=50))

        # ---------- 5. 导出 CSV ----------
        csv_path = os.path.join(output_dir, f"{sheet_name}_bug清单.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n[导出] CSV: {csv_path}")

        # ---------- 6. 导出 JSON ----------
        json_path = os.path.join(output_dir, f"{sheet_name}_bug清单.json")
        records = df.where(pd.notna(df), "").to_dict(orient="records")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"[导出] JSON: {json_path}")

    # ---------- 7. 提取图片 ----------
    extract_images(safe_xlsx, output_dir)

    # ---------- 8. 统计摘要 ----------
    print(f"\n{'='*60}")
    print("[统计摘要]")
    print(f"{'='*60}")
    for sheet_name, df in all_results.items():
        if df.empty:
            continue
        stats = generate_stats(df)
        print(f"\n--- Sheet: {sheet_name} ---")
        print(json.dumps(stats, ensure_ascii=False, indent=2))

        stats_path = os.path.join(output_dir, f"{sheet_name}_统计摘要.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n[完成] 所有输出已保存至: {output_dir}")
    return all_results


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python parse_hrm_bug_excel.py <xlsx文件路径>")
        sys.exit(1)

    main(sys.argv[1])
