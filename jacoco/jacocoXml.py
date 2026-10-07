import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd

# 1. 解析 jacoco.xml，提取包、类级别的覆盖率
def parse_jacoco(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    data = []
    for pkg in root.findall('package'):
        pkg_name = pkg.get('name')
        for cls in pkg.findall('class'):
            cls_name = cls.get('name')
            # 提取关键覆盖率指标
            counters = {c.get('type'): (int(c.get('missed')), int(c.get('covered')))
                        for c in cls.findall('counter')}
            missed, covered = counters.get('LINE', (0, 0))
            line_coverage = covered / (missed + covered) if (missed + covered) > 0 else 0
            data.append({
                '包名': pkg_name,
                '类名': cls_name.split('/')[-1], # 简化类名展示
                '行覆盖率': f"{line_coverage:.1%}",
                'full_path': cls_name, # 用于定位
                'missed_lines': missed,
                'covered_lines': covered,
            })
    return pd.DataFrame(data)

# 2. Streamlit 主界面
st.title("📊 JaCoCo 覆盖率报告")

# 假设 jacoco.xml 在项目根目录的 target/site/jacoco/ 下
xml_path = "target/site/jacoco/jacoco.xml"
df = parse_jacoco(xml_path)

# 显示统计概览
total_missed = df['missed_lines'].sum()
total_covered = df['covered_lines'].sum()
st.metric("总体行覆盖率", f"{total_covered/(total_missed+total_covered):.1%}")

# 显示详细表格，并添加超链接
def make_link(row):
    # 方式1: 链接到本地 JaCoCo HTML 报告
    # HTML 报告结构与 XML 对应，路径需根据实际情况调整
    html_path = f"target/site/jacoco/{row['full_path'].replace('/', '.')}.html"
    # 方式2: 链接到远程 Git 仓库（需配置 base_url）
    # base_url = "https://github.com/your-repo/blob/main/src/main/java/"
    # git_link = f"{base_url}{row['full_path'].replace('.', '/')}.java"
    return f'<a href="{html_path}" target="_blank">🔍 查看</a>'

# 为了演示，这里使用本地 HTML 链接（需确保报告已生成）
df['详情'] = df.apply(make_link, axis=1)

# 用 st.dataframe 展示，并允许 HTML 渲染
st.dataframe(df[['包名', '类名', '行覆盖率', '详情']],
             column_config={"详情": st.column_config.TextColumn("详情")},
             unsafe_allow_html=True)