import streamlit as st
import requests
from streamlit_lottie import st_lottie

# 加载在线lottie json
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# 示例动画链接
lottie_data = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_V9t630.json")

# 渲染动画
st_lottie(
    lottie_data,
    speed=1,          # 播放速度
    reverse=False,    # 是否倒放
    loop=True,        # 是否循环播放
    height=300,       # 动画高度
    width=None,       # 宽度，None自适应
    key="anim1"       # key，防止streamlit渲染冲突
)
