import streamlit as st
import pandas as pd
import random
import time
import io

# ====================== 页面配置 ======================
st.set_page_config(
    page_title="现场抽奖系统",
    layout="wide",
    page_icon="🎉"
)

# ====================== 初始化数据 ======================
if "all_users" not in st.session_state:
    st.session_state.all_users = []

if "winner_list" not in st.session_state:
    st.session_state.winner_list = []

# ====================== 标题 ======================
st.markdown("""
    <h1 style='text-align: center; color: #ff2a6d; font-size: 50px;'>🎉 现场抽奖系统</h1>
    <hr>
""", unsafe_allow_html=True)

# ====================== 左侧：上传名单 ======================
with st.sidebar:
    st.header("📋 抽奖名单")

    # 1. 上传文件
    uploaded_file = st.file_uploader("上传 Excel / CSV 名单", type=["xlsx", "csv"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 取第一列作为名单
        names = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        st.session_state.all_users = names
        st.success(f"✅ 加载成功：{len(names)} 人")

    # 2. 手动输入名单
    with st.expander("✏️ 手动输入名单"):
        input_names = st.text_area("一行一个名字", height=200)
        if st.button("确认导入"):
            if input_names:
                names = [n.strip() for n in input_names.split("\n") if n.strip()]
                st.session_state.all_users = names
                st.success(f"✅ 导入成功：{len(names)} 人")

    # 3. 基础信息
    st.markdown(f"**总人数：{len(st.session_state.all_users)}**")
    st.markdown(f"**已中奖：{len(st.session_state.winner_list)}**")

    # 4. 清空按钮
    if st.button("🔄 重置抽奖"):
        st.session_state.winner_list = []
        st.rerun()

# ====================== 中间：抽奖区域 ======================
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    # 抽取数量
    draw_count = st.number_input("🎯 本次抽取人数", min_value=1, max_value=20, value=1)

    # 抽奖按钮
    start = st.button("🎉 开始抽奖", type="primary", use_container_width=True)

    # 抽奖动画展示
    show_area = st.empty()

    if start:
        # 过滤已中奖
        candidates = [n for n in st.session_state.all_users if n not in st.session_state.winner_list]

        if not candidates:
            show_area.error("🎉 所有人员已全部中奖！")
        elif len(candidates) < draw_count:
            show_area.error(f"剩余人数不足，仅剩 {len(candidates)} 人")
        else:
            # 滚动效果
            for i in range(20):
                temp = random.sample(candidates, min(draw_count, len(candidates)))
                show_area.markdown(f"""
                    <div style='text-align:center; font-size:30px; color:red;'>
                    {' ｜ '.join(temp)}
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(0.08)

            # 最终中奖名单
            winners = random.sample(candidates, draw_count)
            st.session_state.winner_list.extend(winners)

            show_area.markdown(f"""
                <div style='text-align:center; padding:30px; background:#ff2a6d; color:white; font-size:40px; border-radius:15px;'>
                🎉 恭喜中奖：<br/>{'　｜　'.join(winners)}
                </div>
            """, unsafe_allow_html=True)

# ====================== 中奖名单展示 ======================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("🏆 中奖名单")

if st.session_state.winner_list:
    df_win = pd.DataFrame({
        "排名": range(1, len(st.session_state.winner_list) + 1),
        "中奖人员": st.session_state.winner_list
    })

    st.dataframe(df_win, use_container_width=True, hide_index=True)

    # 导出中奖名单
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_win.to_excel(writer, sheet_name="中奖名单", index=False)

    st.download_button(
        label="📥 导出中奖名单",
        data=excel_buffer,
        file_name="中奖名单.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("🎯 暂无人中奖，点击开始抽奖")