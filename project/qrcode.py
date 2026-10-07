import streamlit as st
import pages.qrcode
from PIL import Image
import io

# 页面配置
st.set_page_config(
    page_title="二维码生成器",
    page_icon="📱",
    layout="centered"
)

# 标题
st.title("📱 在线二维码生成器")
st.markdown("输入文本、网址、链接，一键生成可扫描二维码")

# 输入框
user_input = st.text_input("请输入要生成二维码的内容：", placeholder="例如：https://www.baidu.com 或 任意文字")

# 生成按钮
if st.button("✨ 生成二维码", type="primary"):
    if user_input.strip() != "":
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(user_input)
        qr.make(fit=True)

        # 转为图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 保存到内存
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        # 显示二维码
        st.success("✅ 二维码生成成功！")
        st.image(buf, caption="扫描二维码查看内容", use_column_width=False, width=300)

        # 下载按钮
        st.download_button(
            label="💾 下载二维码图片",
            data=buf,
            file_name="qrcode.png",
            mime="image/png"
        )
    else:
        st.warning("⚠️ 请输入内容后再生成！")