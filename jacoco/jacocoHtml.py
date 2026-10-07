import streamlit as st
from bs4 import BeautifulSoup
import io

# 页面基础配置
st.set_page_config(page_title="HTML解析工具", layout="wide")
st.title("📄 HTML文件上传&解析工具")
st.divider()

# 1. 文件上传模块
uploaded_file = st.file_uploader("上传HTML文件", type=["html", "htm"])

if uploaded_file is not None:
    # 读取文件内容
    file_bytes = uploaded_file.read()
    html_str = file_bytes.decode("utf-8", errors="ignore")

    # 初始化BeautifulSoup解析器
    soup = BeautifulSoup(html_str, "html.parser")

    # 分栏布局
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 原始HTML源码")
        st.code(html_str, language="html", height=400)

    with col2:
        st.subheader("2. HTML实时预览")
        st.components.v1.html(html_str, height=420, scrolling=True)

    st.divider()
    st.subheader("3. 解析提取数据")

    # 3.1 提取纯文本
    pure_text = soup.get_text(strip=False)
    with st.expander("提取页面纯文本内容", expanded=True):
        st.text_area("文本内容", pure_text, height=200)
        st.button("复制纯文本", on_click=lambda: st.write(st.code(pure_text)))

    # 3.2 提取所有a标签链接
    links = []
    for a in soup.find_all("a", href=True):
        links.append(a["href"])
    with st.expander("提取全部超链接（a标签href）"):
        if links:
            for idx, link in enumerate(links, 1):
                st.write(f"{idx}. {link}")
            link_text = "\n".join(links)
            st.button("复制所有链接", on_click=lambda: st.code(link_text))
        else:
            st.info("页面未找到任何超链接")

    # 3.3 提取所有图片地址
    imgs = []
    for img in soup.find_all("img", src=True):
        imgs.append(img["src"])
    with st.expander("提取全部图片地址（img标签src）"):
        if imgs:
            for idx, src in enumerate(imgs, 1):
                st.write(f"{idx}. {src}")
            img_text = "\n".join(imgs)
            st.button("复制所有图片地址", on_click=lambda: st.code(img_text))
        else:
            st.info("页面未找到图片")

    # 3.4 统计所有HTML标签
    tag_count = {}
    for tag in soup.find_all():
        tag_name = tag.name
        tag_count[tag_name] = tag_count.get(tag_name, 0) + 1
    with st.expander("页面标签统计（标签名:数量）"):
        tag_str = ""
        for tag, cnt in sorted(tag_count.items()):
            st.write(f"<{tag}> : {cnt} 个")
            tag_str += f"<{tag}> : {cnt} 个\n"
        st.button("复制标签统计", on_click=lambda: st.code(tag_str))

else:
    # 未上传文件提示
    st.info("请上传 .html / .htm 格式文件进行解析")
    # 示例演示文本
    with st.expander("测试用示例HTML"):
        demo_html = """
        <html>
            <body>
                <h1>测试页面</h1>
                <a href="https://www.baidu.com">百度</a>
                <img src="test.jpg"/>
                <p>一段测试文字</p>
            </body>
        </html>
        """
        st.code(demo_html, language="html")
