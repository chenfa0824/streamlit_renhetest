import streamlit as st
import pandas as pd
from datetime import datetime

# ====================== 页面配置 ======================
st.set_page_config(
    page_title="婚礼宴会管理系统",
    layout="wide",
    page_icon="💒"
)

# ====================== 初始化数据 ======================
# 桌台数据：桌号、最大人数、已坐人数
if "tables" not in st.session_state:
    st.session_state.tables = [
        {"table_id": "1号桌", "max_num": 10, "used_num": 0, "remain": 10},
        {"table_id": "2号桌", "max_num": 10, "used_num": 0, "remain": 10},
        {"table_id": "3号桌", "max_num": 8, "used_num": 0, "remain": 8},
    ]

# 人员数据：姓名、电话、备注、分配桌号、落座状态
if "guests" not in st.session_state:
    st.session_state.guests = []

# ====================== 样式美化 ======================
st.markdown("""
<style>
    .title {font-size: 32px; color: red; text-align: center; font-weight:bold;}
    .card {background-color:red; padding:15px; border-radius:10px; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">💒 婚礼宴会管理系统</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ====================== 顶部菜单 ======================
tab1, tab2, tab3 = st.tabs(["📋 总览看板", "🪑 桌台管理", "👤 宾客管理"])

# ====================== TAB1：总览看板 ======================
with tab1:
    st.subheader("📊 宴会总览")
    col1, col2, col3, col4 = st.columns(4)

    total_tables = len(st.session_state.tables)
    total_guests = len(st.session_state.guests)
    seated_guests = len([g for g in st.session_state.guests if g["table_id"] != "未分配"])
    unseated_guests = total_guests - seated_guests

    with col1:
        st.metric("总桌数", f"{total_tables} 桌")
    with col2:
        st.metric("总宾客", f"{total_guests} 人")
    with col3:
        st.metric("已落座", f"{seated_guests} 人")
    with col4:
        st.metric("未分配", f"{unseated_guests} 人")

    st.markdown("#### 🪑 桌台使用情况")
    df_tables = pd.DataFrame(st.session_state.tables)
    st.dataframe(df_tables, use_container_width=True, hide_index=True)

# ====================== TAB2：桌台管理 ======================
with tab2:
    st.subheader("🪑 桌台管理")

    # 新增桌台
    with st.expander("➕ 新增桌台"):
        new_table_id = st.text_input("桌号", placeholder="例如：4号桌")
        new_max_num = st.number_input("最大座位数", min_value=1, max_value=20, value=10)
        if st.button("保存桌台"):
            if new_table_id:
                st.session_state.tables.append({
                    "table_id": new_table_id,
                    "max_num": new_max_num,
                    "used_num": 0,
                    "remain": new_max_num
                })
                st.success(f"✅ {new_table_id} 添加成功！")
                st.rerun()

    # 桌台列表
    st.markdown("#### 桌台列表")
    df_t = pd.DataFrame(st.session_state.tables)
    st.dataframe(df_t, use_container_width=True, hide_index=True)

# ====================== TAB3：宾客管理 ======================
with tab3:
    st.subheader("👤 宾客管理 & 落座分配")

    # 新增宾客
    with st.expander("➕ 添加宾客"):
        name = st.text_input("姓名")
        phone = st.text_input("电话")
        remark = st.text_input("备注（亲友/同事等）")
        table_list = [t["table_id"] for t in st.session_state.tables]
        table_list.append("未分配")
        assign_table = st.selectbox("分配桌台", table_list)

        if st.button("保存宾客"):
            if name:
                # 更新桌台已坐人数
                if assign_table != "未分配":
                    for t in st.session_state.tables:
                        if t["table_id"] == assign_table and t["remain"] > 0:
                            t["used_num"] += 1
                            t["remain"] -= 1

                st.session_state.guests.append({
                    "name": name,
                    "phone": phone,
                    "remark": remark,
                    "table_id": assign_table,
                    "create_time": datetime.now().strftime("%m-%d %H:%M")
                })
                st.success(f"✅ {name} 添加成功！")
                st.rerun()

    # 宾客列表
    st.markdown("#### 宾客列表（可查看落座情况）")
    if st.session_state.guests:
        df_g = pd.DataFrame(st.session_state.guests)
        st.dataframe(df_g, use_container_width=True, hide_index=True)
    else:
        st.info("暂无宾客，请先添加宾客")

# ====================== 底部 ======================
st.markdown("<hr>", unsafe_allow_html=True)
st.caption("💒 婚礼宴会管理系统 | 便捷管理桌台、宾客、落座情况")