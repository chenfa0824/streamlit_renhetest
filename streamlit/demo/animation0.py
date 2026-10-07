import streamlit as st
import time

st.title("Streamlit 全部原生内置动画 Demo")

# ========== 1. st.progress 动态进度条 ==========
st.subheader("1. st.progress 进度条动画")
if st.button("运行进度条"):
    bar = st.progress(0, text="任务执行中...")
    for pct in range(100):
        time.sleep(0.03)
        bar.progress(pct + 1, text=f"已完成 {pct+1}%")
    st.success("进度完成")

# ========== 2. st.spinner 转圈加载动画 ==========
st.subheader("2. st.spinner 加载转圈")
if st.button("启动Spinner"):
    with st.spinner("正在查询数据，请等待...", show_time=True):
        time.sleep(2)
    st.success("加载完成！")

# ========== 3. st.status 任务状态面板（多步骤） ==========
st.subheader("3. st.status 任务状态面板")
if st.button("运行多步骤任务"):
    with st.status("开始处理任务...", expanded=True) as status:
        st.write("步骤1：读取文件")
        time.sleep(1)
        st.write("步骤2：清洗数据")
        time.sleep(1)
        st.write("步骤3：生成结果")
        time.sleep(1)
        status.update(label="✅任务完成", state="complete", expanded=False)

# ========== 4. st.skeleton 骨架屏加载动画 ==========
st.subheader("4. st.skeleton 骨架屏")
if st.button("展示骨架屏"):
    with st.skeleton(height=150):
        time.sleep(2)
    st.write("骨架屏消失，内容加载完毕")

# ========== 5. st.toast 右下角弹出通知动画 ==========
st.subheader("5. st.toast 弹窗通知")
if st.button("弹出Toast"):
    st.toast("操作成功！", icon="✅", duration=4)
    st.toast("警告提示", icon="⚠️", duration=4)

# ========== 6. st.balloons 气球全屏动画 ==========
st.subheader("6. st.balloons 气球庆祝")
if st.button("放气球🎈"):
    st.balloons()

# ========== 7. st.snow 雪花全屏动画 ==========
st.subheader("7. st.snow 雪花特效")
if st.button("下雪❄️"):
    st.snow()

# ========== 8. st.write_stream 打字机流式文本动画 ==========
st.subheader("8. st.write_stream 打字机动画")
def text_generator():
    text = "这是Streamlit原生打字机动画，适合大模型流式输出，逐字渲染。"
    for char in text:
        yield char
        time.sleep(0.06)

if st.button("开始打字"):
    st.write_stream(text_generator())

# ========== 9. 四种提示框入场动画 ==========
st.subheader("9. 提示框入场动画")
st.success("✅ Success 成功提示")
st.info("ℹ️ Info 信息提示")
st.warning("⚠️ Warning 警告提示")
st.error("❌ Error 错误提示")

# exception 异常提示
try:
    1/0
except Exception as e:
    st.exception(e)
