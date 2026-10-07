import streamlit as st
import time

# 1. 进度条 st.progress
progress_bar = st.progress(0)
for i in range(101):
    progress_bar.progress(i)
    time.sleep(0.03)

# 2. 加载转圈 spinner
with st.spinner("处理数据中，请稍候..."):
    time.sleep(2)

# 3. 多阶段状态容器 status
with st.status("正在执行任务", expanded=True) as s:
    st.write("第一步：读取数据")
    time.sleep(1)
    st.write("第二步：计算")
    time.sleep(1)
    s.update(label="✅任务完成", state="complete")

# 4. 骨架屏（占位加载）
with st.skeleton(height=150):
    time.sleep(2)

# 5. 庆祝特效
st.balloons()  # 气球
st.snow()    # 雪花

# 6. 右下角轻提示 toast
st.toast("操作成功！", icon="✅")
