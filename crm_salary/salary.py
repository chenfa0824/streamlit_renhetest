import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# ============================================================
# 1. 页面配置
# ============================================================
st.set_page_config(
    page_title="仁和会计工资数据比对工具",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 仁和会计工资数据比对工具")
st.markdown("---")

# ============================================================
# 2. Session State 统一初始化
# ============================================================
defaults = {
    'connected': False,
    'engine': None,
    'table1': None, 'table2': None,
    'col1': None, 'col2': None,
    'count1': 0, 'count2': 0,
    'db_name': None,
    'df1': None, 'df2': None,
    'search_value': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# 3. 数据库工具函数
# ============================================================
def run_query(conn, sql, params=None):
    """执行查询并返回 DataFrame"""
    return pd.read_sql(text(sql), conn, params=params or {})


def get_columns(conn, table):
    return [c[0] for c in conn.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()]


def get_count(conn, table):
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]


def connect_database(host, port, user, password, database, table1_name, table2_name):
    """连接数据库并保存状态"""
    try:
        conn_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        engine = create_engine(conn_str)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            table_list = [t[0] for t in conn.execute(text("SHOW TABLES")).fetchall()]

            if table1_name not in table_list:
                st.error(f"❌ 表 '{table1_name}' 不存在！")
                return False
            if table2_name not in table_list:
                st.error(f"❌ 表 '{table2_name}' 不存在！")
                return False

            st.session_state.connected = True
            st.session_state.engine = engine
            st.session_state.table1 = table1_name
            st.session_state.table2 = table2_name
            st.session_state.col1 = get_columns(conn, table1_name)
            st.session_state.col2 = get_columns(conn, table2_name)
            st.session_state.count1 = get_count(conn, table1_name)
            st.session_state.count2 = get_count(conn, table2_name)
            st.session_state.db_name = database

            st.success(
                f"✅ 连接成功！表1: {st.session_state.count1}条 | 表2: {st.session_state.count2}条"
            )
            return True
    except Exception as e:
        st.error(f"❌ 连接失败: {e}")
        st.session_state.connected = False
        return False


# ============================================================
# 4. 辅助函数
# ============================================================
def find_column(cols, keywords):
    """通用列名查找"""
    for col in cols:
        for kw in keywords:
            if kw.lower() in col.lower():
                return col
    return None


def find_name_column(cols):
    return find_column(cols, ['姓名', 'name', 'employee_name', 'emp_name', 'staff_name', 'full_name', '员工姓名'])


def find_id_column(cols):
    return find_column(cols, ['工号', 'id', 'employee_id', 'emp_id', 'staff_id', 'user_id', '编号'])


def query_by_name(conn, table_name, name_col, search_value, mode="fuzzy"):
    """根据姓名查询记录"""
    try:
        if mode == "exact":
            sql = f"SELECT * FROM {table_name} WHERE {name_col} = :value"
            result = conn.execute(text(sql), {"value": search_value}).fetchall()
        elif mode == "fuzzy":
            sql = f"SELECT * FROM {table_name} WHERE {name_col} LIKE :value"
            result = conn.execute(text(sql), {"value": f"%{search_value}%"}).fetchall()

            if not result:
                sql = f"SELECT * FROM {table_name} WHERE REPLACE({name_col}, ' ', '') LIKE :value"
                result = conn.execute(text(sql),
                                      {"value": f"%{search_value.replace(' ', '')}%"}).fetchall()
            if not result:
                sql = f"SELECT * FROM {table_name} WHERE {name_col} = :value"
                result = conn.execute(text(sql), {"value": search_value}).fetchall()
        else:
            return pd.DataFrame()

        if result:
            col_names = get_columns(conn, table_name)
            return pd.DataFrame(result, columns=col_names)
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"查询表 {table_name} 时出错: {e}")
        return pd.DataFrame()


def render_record_selector(df, name_col, table_label, key):
    """
    通用：从多条记录中选择一条参与比对
    返回选中的单行 DataFrame，若只有一条则直接返回
    """
    if len(df) <= 1:
        return df

    display_cols = [name_col] + [c for c in ['工号', 'id', '部门', 'department'] if c in df.columns]
    display_cols = list(set(display_cols) & set(df.columns)) or df.columns[:2].tolist()

    df_display = df[display_cols].copy()
    df_display['_display'] = df_display.apply(
        lambda row: ' | '.join(f"{col}: {row[col]}" for col in display_cols if pd.notna(row[col])),
        axis=1
    )

    selected = st.selectbox(
        f"选择{table_label}中要参与比对的记录",
        options=df_display['_display'].tolist(),
        key=key
    )
    if selected:
        idx = df_display[df_display['_display'] == selected].index[0]
        return df.loc[[idx]]
    return df.iloc[[0]]


def display_comparison(row1, row2, table1, table2, search_value=None):
    """显示两条记录的详细比对（逻辑保持不变）"""
    all_cols = sorted(set(row1.index) | set(row2.index))

    diff_count = 0
    compare_data = []
    diff_fields = []

    for col in all_cols:
        val1 = row1.get(col, '') if col in row1.index else ''
        val2 = row2.get(col, '') if col in row2.index else ''

        if pd.isna(val1) and pd.isna(val2):
            is_same, val1_str, val2_str = True, '', ''
        elif pd.isna(val1):
            is_same, val1_str = False, 'NULL'
            val2_str = str(val2) if not pd.isna(val2) else 'NULL'
        elif pd.isna(val2):
            is_same = False
            val1_str = str(val1) if not pd.isna(val1) else 'NULL'
            val2_str = 'NULL'
        else:
            try:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    is_same = abs(float(val1) - float(val2)) < 1e-9
                else:
                    is_same = str(val1).strip() == str(val2).strip()
            except Exception:
                is_same = str(val1).strip() == str(val2).strip()
            val1_str, val2_str = str(val1), str(val2)

        if not is_same:
            diff_count += 1
            diff_fields.append(col)

        compare_data.append({
            "字段名": col,
            f"表1: {table1}": val1_str,
            f"表2: {table2}": val2_str,
            "是否一致": "✅" if is_same else "❌"
        })

    df_compare = pd.DataFrame(compare_data)

    # 统计
    st.markdown("#### 📊 比对统计")
    consistency = (len(all_cols) - diff_count) / len(all_cols) * 100 if all_cols else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总字段数", len(all_cols))
    c2.metric("一致字段", len(all_cols) - diff_count)
    c3.metric("差异字段", diff_count, delta_color="inverse")
    c4.metric("一致性", f"{consistency:.1f}%")
    st.progress(consistency / 100)

    # 详细比对
    st.markdown("#### 📋 字段详细比对")

    def highlight_diff(row):
        if row['是否一致'] == '❌':
            return ['background-color: #ffcccc; font-weight: bold'] * len(row)
        return [''] * len(row)

    st.dataframe(df_compare.style.apply(highlight_diff, axis=1),
                 use_container_width=True, hide_index=True)

    if diff_fields:
        st.markdown(f"#### 🔴 差异字段详情 ({len(diff_fields)}个字段)")
        diff_df = df_compare[df_compare['是否一致'] == '❌']
        if not diff_df.empty:
            st.dataframe(diff_df, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 两条记录完全一致！")

    # 数据摘要
    with st.expander("📈 数据摘要"):
        col1_s, col2_s = st.columns(2)
        with col1_s:
            st.markdown(f"**表1: {table1}**")
            st.json(row1.to_dict())
        with col2_s:
            st.markdown(f"**表2: {table2}**")
            st.json(row2.to_dict())

    # 导出
    if diff_fields:
        with st.expander("📤 导出差异报告"):
            export_data = df_compare[df_compare['是否一致'] == '❌'].copy()
            st.download_button(
                label="📥 下载差异报告 (CSV)",
                data=export_data.to_csv(index=False, encoding='utf-8-sig'),
                file_name=f"比对差异_{search_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )


def get_all_names(conn, table1, name_col1, table2, name_col2):
    """获取两张表中的所有姓名（合并去重）"""
    names = []
    try:
        if name_col1:
            q1 = f"SELECT DISTINCT {name_col1} FROM {table1} WHERE {name_col1} IS NOT NULL AND {name_col1} != '' LIMIT 500"
            names.extend([str(r[0]) for r in conn.execute(text(q1)).fetchall() if r[0]])
        if name_col2:
            q2 = f"SELECT DISTINCT {name_col2} FROM {table2} WHERE {name_col2} IS NOT NULL AND {name_col2} != '' LIMIT 500"
            names.extend([str(r[0]) for r in conn.execute(text(q2)).fetchall() if r[0]])
    except Exception as e:
        st.warning(f"获取姓名列表失败: {e}")
    names = sorted(set(names))
    return names


# ============================================================
# 5. 使用 Tab 分组
# ============================================================
tab_config, tab_query = st.tabs(["⚙️ 数据库配置", "🔎 数据查询比对"])

# ------------------------------------------------------------
# TAB 1: 数据库配置
# ------------------------------------------------------------
with tab_config:
    st.markdown("### 📁 数据库连接配置")
    col_cfg1, col_cfg2 = st.columns(2)

    with col_cfg1:
        db_host = st.text_input("主机地址", value="localhost", key="db_host_input")
        db_user = st.text_input("用户名", value="root", key="db_user_input")
        db_name_input = st.text_input("数据库名", value="renhetest", key="db_name_input")

    with col_cfg2:
        db_port = st.number_input("端口", value=3306, key="db_port_input")
        db_password = st.text_input("密码", value="root", type="password", key="db_password_input")
        table1_input = st.text_input("表1名称", value="financial_salary", key="table1_input")
        table2_input = st.text_input("表2名称", value="employee_salary", key="table2_input")

    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        connect_btn = st.button("🔗 连接数据库", use_container_width=True, key="connect_btn")

    if connect_btn:
        connect_database(
            st.session_state.db_host_input,
            st.session_state.db_port_input,
            st.session_state.db_user_input,
            st.session_state.db_password_input,
            st.session_state.db_name_input,
            st.session_state.table1_input,
            st.session_state.table2_input,
        )

    # 连接状态
    if st.session_state.connected:
        st.markdown("---")
        st.success(f"✅ 已连接到数据库: {st.session_state.db_name}")
        c1, c2 = st.columns(2)
        c1.info(f"📊 表1 `{st.session_state.table1}` 共 {st.session_state.count1} 条 / {len(st.session_state.col1)} 列")
        c2.info(f"📊 表2 `{st.session_state.table2}` 共 {st.session_state.count2} 条 / {len(st.session_state.col2)} 列")

        with st.expander("📋 查看表结构"):
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**表1: {st.session_state.table1}**")
                st.write(st.session_state.col1)
            with cc2:
                st.markdown(f"**表2: {st.session_state.table2}**")
                st.write(st.session_state.col2)

# ------------------------------------------------------------
# TAB 2: 数据查询比对
# ------------------------------------------------------------
with tab_query:
    if not (st.session_state.connected and st.session_state.engine):
        st.info("👈 请先在「数据库配置」Tab 中连接数据库")
    else:
        try:
            engine = st.session_state.engine
            table1 = st.session_state.table1
            table2 = st.session_state.table2
            col1 = st.session_state.col1
            col2 = st.session_state.col2

            with engine.connect() as conn:
                # 识别关键列
                name_col1_auto = find_name_column(col1)
                name_col2_auto = find_name_column(col2)
                id_col1 = find_id_column(col1)
                id_col2 = find_id_column(col2)

                # ---------- 字段配置 ----------
                st.markdown("### ⚙️ 字段配置")
                with st.expander("📌 识别的关键字段", expanded=False):
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        st.markdown(f"**表1: {table1}**")
                        st.caption(f"• 姓名列: `{name_col1_auto or '未识别'}`")
                        st.caption(f"• ID列: `{id_col1 or '未识别'}`")
                    with ci2:
                        st.markdown(f"**表2: {table2}**")
                        st.caption(f"• 姓名列: `{name_col2_auto or '未识别'}`")
                        st.caption(f"• ID列: `{id_col2 or '未识别'}`")

                cfg1, cfg2 = st.columns(2)
                with cfg1:
                    name_col1 = st.selectbox(
                        "表1的姓名列", options=col1,
                        index=col1.index(name_col1_auto) if name_col1_auto in col1 else 0,
                        key="name_col1_select"
                    )
                with cfg2:
                    name_col2 = st.selectbox(
                        "表2的姓名列", options=col2,
                        index=col2.index(name_col2_auto) if name_col2_auto in col2 else 0,
                        key="name_col2_select"
                    )

                st.markdown("---")

                # ---------- 搜索区域 ----------
                st.markdown("### 👤 查询员工")
                all_names = get_all_names(conn, table1, name_col1, table2, name_col2)

                search_method = st.radio(
                    "选择输入方式",
                    ["✏️ 手动输入", "📋 从列表选择", "🔍 查看全部数据"],
                    horizontal=True,
                    key="search_method"
                )

                employee_name = ""
                search_mode = "fuzzy"

                if search_method == "✏️ 手动输入":
                    employee_name = st.text_input(
                        "输入员工姓名",
                        placeholder="请输入完整或部分姓名，例如：胡少林",
                        help="支持模糊搜索，输入部分姓名即可",
                        key="employee_name_input"
                    )
                    search_mode = "fuzzy"
                    if employee_name:
                        st.caption(f"💡 将搜索包含 '{employee_name}' 的记录")

                elif search_method == "📋 从列表选择":
                    if all_names:
                        employee_name = st.selectbox(
                            "从列表中选择姓名",
                            options=[""] + all_names,
                            key="employee_name_select"
                        )
                        search_mode = "exact"
                    else:
                        st.warning("⚠️ 暂无姓名数据，请手动输入")
                        employee_name = st.text_input(
                            "输入员工姓名", key="employee_name_input_fallback"
                        )
                        search_mode = "fuzzy"

                else:  # 查看全部
                    st.info("📊 将显示两张表的前100条记录")
                    employee_name = "__all__"
                    search_mode = "all"

                cb1, cb2, _ = st.columns([1, 1, 3])
                with cb1:
                    search_btn = st.button("🔍 查询比对", use_container_width=True,
                                           type="primary", key="search_btn")
                with cb2:
                    if st.button("🔄 重置", use_container_width=True, key="reset_btn"):
                        st.session_state.df1 = None
                        st.session_state.df2 = None
                        st.session_state.search_value = None
                        st.rerun()

                # ---------- 执行查询 ----------
                if search_btn and employee_name:
                    st.markdown("---")

                    if employee_name == "__all__":
                        st.markdown("### 📋 显示全部数据")
                        try:
                            df1 = run_query(conn, f"SELECT * FROM {table1} LIMIT 100")
                            df2 = run_query(conn, f"SELECT * FROM {table2} LIMIT 100")
                            st.session_state.df1, st.session_state.df2 = df1, df2
                            st.session_state.search_value = "全部数据"

                            st.success(f"✅ 表1 '{table1}' 显示 {len(df1)} 条记录")
                            st.success(f"✅ 表2 '{table2}' 显示 {len(df2)} 条记录")

                            t1, t2 = st.tabs([f"📄 表1: {table1}", f"📄 表2: {table2}"])
                            with t1:
                                st.dataframe(df1, use_container_width=True)
                            with t2:
                                st.dataframe(df2, use_container_width=True)
                        except Exception as e:
                            st.error(f"查询全部数据失败: {e}")

                    else:
                        st.markdown("### 📋 查询结果比对")
                        st.caption(f"🔍 搜索条件: 姓名包含 '{employee_name}'")

                        with st.spinner("正在查询数据..."):
                            df1 = query_by_name(conn, table1, name_col1, employee_name, search_mode)
                            df2 = query_by_name(conn, table2, name_col2, employee_name, search_mode)

                            st.session_state.df1, st.session_state.df2 = df1, df2
                            st.session_state.search_value = employee_name

                            st.info(
                                f"📊 表1 '{table1}' 找到 {len(df1)} 条记录 | 表2 '{table2}' 找到 {len(df2)} 条记录"
                            )

                            # ----- 结果处理 -----
                            if df1.empty and df2.empty:
                                st.warning(f"⚠️ 在两张表中均未找到包含 '{employee_name}' 的记录")
                                with st.expander("🔧 调试信息", expanded=True):
                                    st.caption(f"1. 表1姓名列: {name_col1}")
                                    st.caption(f"2. 表2姓名列: {name_col2}")
                                    st.caption(f"3. 搜索值: {employee_name}")
                                    try:
                                        s1 = run_query(conn, f"SELECT {name_col1} FROM {table1} LIMIT 5")
                                        s2 = run_query(conn, f"SELECT {name_col2} FROM {table2} LIMIT 5")
                                        st.caption("表1姓名列示例:")
                                        st.dataframe(s1)
                                        st.caption("表2姓名列示例:")
                                        st.dataframe(s2)
                                    except Exception as e:
                                        st.caption(f"获取示例数据失败: {e}")
                                if all_names:
                                    similar = [n for n in all_names if employee_name.lower() in n.lower()]
                                    if similar:
                                        st.info(f"💡 是否想查找这些姓名？: {', '.join(similar[:10])}")

                            elif df1.empty:
                                st.warning(f"⚠️ 在表1 '{table1}' 中未找到记录")
                                st.success(f"✅ 在表2 '{table2}' 中找到 {len(df2)} 条记录")
                                st.markdown(f"#### 📄 表2: {table2} 查询结果")
                                st.dataframe(df2, use_container_width=True)
                                if len(df2) == 1:
                                    with st.expander("📋 查看完整记录"):
                                        st.json(df2.iloc[0].to_dict())

                            elif df2.empty:
                                st.success(f"✅ 在表1 '{table1}' 中找到 {len(df1)} 条记录")
                                st.warning(f"⚠️ 在表2 '{table2}' 中未找到记录")
                                st.markdown(f"#### 📄 表1: {table1} 查询结果")
                                st.dataframe(df1, use_container_width=True)
                                if len(df1) == 1:
                                    with st.expander("📋 查看完整记录"):
                                        st.json(df1.iloc[0].to_dict())

                            else:
                                # 两张表都找到
                                st.success(f"✅ 两张表均找到记录 (表1: {len(df1)}条, 表2: {len(df2)}条)")

                                t1, t2, t3 = st.tabs([
                                    f"📄 表1: {table1} ({len(df1)}条)",
                                    f"📄 表2: {table2} ({len(df2)}条)",
                                    "🔗 记录比对"
                                ])

                                # 用 session_state 保存选择，跨 Tab 共享
                                with t1:
                                    st.dataframe(df1, use_container_width=True)
                                    st.markdown("#### 选择要比对的记录")
                                    sel1 = render_record_selector(
                                        df1, name_col1, "表1", key="select1"
                                    )
                                    st.session_state['df1_selected'] = sel1

                                with t2:
                                    st.dataframe(df2, use_container_width=True)
                                    st.markdown("#### 选择要比对的记录")
                                    sel2 = render_record_selector(
                                        df2, name_col2, "表2", key="select2"
                                    )
                                    st.session_state['df2_selected'] = sel2

                                with t3:
                                    sel1 = st.session_state.get('df1_selected')
                                    sel2 = st.session_state.get('df2_selected')
                                    if sel1 is not None and sel2 is not None:
                                        if len(sel1) == 1 and len(sel2) == 1:
                                            display_comparison(
                                                sel1.iloc[0], sel2.iloc[0],
                                                table1, table2, employee_name
                                            )
                                        else:
                                            st.info("请在上方选择要参与比对的记录")
                                    else:
                                        st.info("请在上方选择要参与比对的记录")

                elif not search_btn and employee_name and employee_name != "__all__":
                    st.info("💡 输入姓名后点击 '查询比对' 按钮进行搜索")
                elif not employee_name:
                    st.info("💡 请输入员工姓名进行查询比对")

                # 显示上次查询结果
                if st.session_state.df1 is not None and st.session_state.df2 is not None and not search_btn:
                    st.markdown("---")
                    st.info(f"📌 显示上次查询结果 (搜索值: {st.session_state.search_value})")
                    df1, df2 = st.session_state.df1, st.session_state.df2
                    if not df1.empty and not df2.empty:
                        st.success(f"✅ 表1: {len(df1)}条, 表2: {len(df2)}条")
                        t1, t2 = st.tabs([f"📄 表1: {table1}", f"📄 表2: {table2}"])
                        with t1:
                            st.dataframe(df1, use_container_width=True)
                        with t2:
                            st.dataframe(df2, use_container_width=True)

        except Exception as e:
            st.error(f"❌ 操作失败: {e}")
            st.info("请重新连接数据库")

# ============================================================
# 6. 页脚
# ============================================================
st.markdown("---")
