import streamlit as st
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from datetime import datetime
import re
import time

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
# 2. 初始化session_state
# ============================================================
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'table1' not in st.session_state:
    st.session_state.table1 = None
if 'table2' not in st.session_state:
    st.session_state.table2 = None
if 'col1' not in st.session_state:
    st.session_state.col1 = None
if 'col2' not in st.session_state:
    st.session_state.col2 = None
if 'count1' not in st.session_state:
    st.session_state.count1 = 0
if 'count2' not in st.session_state:
    st.session_state.count2 = 0
if 'db_name' not in st.session_state:
    st.session_state.db_name = None
if 'df1' not in st.session_state:
    st.session_state.df1 = None
if 'df2' not in st.session_state:
    st.session_state.df2 = None
if 'search_value' not in st.session_state:
    st.session_state.search_value = None
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None
if 'batch_complete' not in st.session_state:
    st.session_state.batch_complete = False

# ============================================================
# 3. 数据库连接配置（侧边栏）
# ============================================================
st.sidebar.header("📁 数据库连接配置")

with st.sidebar:
    db_host = st.text_input("主机地址", value="localhost", key="db_host_input")
    db_port = st.number_input("端口", value=3306, key="db_port_input")
    db_user = st.text_input("用户名", value="root", key="db_user_input")
    db_password = st.text_input("密码", value="root", type="password", key="db_password_input")
    db_name_input = st.text_input("数据库名", value="renhetest", key="db_name_input")

    st.markdown("---")

    table1_input = st.text_input("表1名称（财务表）", value="financial_salary", key="table1_input")
    table2_input = st.text_input("表2名称（HRM表）", value="employee_salary", key="table2_input")

    connect_btn = st.button("🔗 连接数据库", use_container_width=True, key="connect_btn")


# ============================================================
# 4. 数据库连接函数
# ============================================================
def connect_database():
    """连接数据库并保存状态"""
    try:
        host = st.session_state.db_host_input
        port = st.session_state.db_port_input
        user = st.session_state.db_user_input
        password = st.session_state.db_password_input
        database = st.session_state.db_name_input
        table1_name = st.session_state.table1_input
        table2_name = st.session_state.table2_input

        conn_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        engine = create_engine(conn_str)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

            tables = conn.execute(text("SHOW TABLES")).fetchall()
            table_list = [t[0] for t in tables]

            if table1_name not in table_list:
                st.sidebar.error(f"❌ 表 '{table1_name}' 不存在！")
                return False
            if table2_name not in table_list:
                st.sidebar.error(f"❌ 表 '{table2_name}' 不存在！")
                return False

            col1 = [c[0] for c in conn.execute(text(f"SHOW COLUMNS FROM {table1_name}")).fetchall()]
            col2 = [c[0] for c in conn.execute(text(f"SHOW COLUMNS FROM {table2_name}")).fetchall()]

            count1 = conn.execute(text(f"SELECT COUNT(*) FROM {table1_name}")).fetchone()[0]
            count2 = conn.execute(text(f"SELECT COUNT(*) FROM {table2_name}")).fetchone()[0]

            st.session_state.connected = True
            st.session_state.engine = engine
            st.session_state.table1 = table1_name
            st.session_state.table2 = table2_name
            st.session_state.col1 = col1
            st.session_state.col2 = col2
            st.session_state.count1 = count1
            st.session_state.count2 = count2
            st.session_state.db_name = database
            st.session_state.batch_complete = False
            st.session_state.batch_results = None

            st.sidebar.success(f"✅ 连接成功！\n表1: {count1}条\n表2: {count2}条")
            return True

    except Exception as e:
        st.sidebar.error(f"❌ 连接失败: {e}")
        st.session_state.connected = False
        return False


if connect_btn:
    connect_database()


# ============================================================
# 5. 辅助函数
# ============================================================
def find_name_column(cols):
    """查找姓名列"""
    name_keywords = ['姓名', 'name', 'employee_name', 'emp_name', 'staff_name', 'full_name', '员工姓名']
    for col in cols:
        for keyword in name_keywords:
            if keyword.lower() in col.lower():
                return col
    return None


def find_id_column(cols):
    """查找ID/工号列"""
    id_keywords = ['工号', 'id', 'employee_id', 'emp_id', 'staff_id', 'user_id', '编号']
    for col in cols:
        for keyword in id_keywords:
            if keyword.lower() in col.lower():
                return col
    return None


def query_by_name(conn, table_name, name_col, search_value, mode="fuzzy"):
    """根据姓名查询记录"""
    try:
        if mode == "exact":
            query = f"SELECT * FROM {table_name} WHERE {name_col} = :value"
            result = conn.execute(text(query), {"value": search_value}).fetchall()
        elif mode == "fuzzy":
            query = f"SELECT * FROM {table_name} WHERE {name_col} LIKE :value"
            result = conn.execute(text(query), {"value": f"%{search_value}%"}).fetchall()

            if not result:
                query = f"SELECT * FROM {table_name} WHERE REPLACE({name_col}, ' ', '') LIKE :value"
                result = conn.execute(text(query), {"value": f"%{search_value.replace(' ', '')}%"}).fetchall()

            if not result:
                query = f"SELECT * FROM {table_name} WHERE {name_col} = :value"
                result = conn.execute(text(query), {"value": search_value}).fetchall()
        else:
            return pd.DataFrame()

        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def query_by_id(conn, table_name, id_col, search_value):
    """根据ID查询记录"""
    try:
        query = f"SELECT * FROM {table_name} WHERE {id_col} = :value"
        result = conn.execute(text(query), {"value": search_value}).fetchall()
        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def find_best_match_by_name(conn, table_name, name_col, search_name):
    """在表中查找最匹配的记录"""
    try:
        # 精确匹配
        query = f"SELECT * FROM {table_name} WHERE {name_col} = :value"
        result = conn.execute(text(query), {"value": search_name}).fetchall()
        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)

        # 去空格匹配
        query = f"SELECT * FROM {table_name} WHERE REPLACE({name_col}, ' ', '') = :value"
        result = conn.execute(text(query), {"value": search_name.replace(' ', '')}).fetchall()
        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)

        # 模糊匹配
        query = f"SELECT * FROM {table_name} WHERE {name_col} LIKE :value LIMIT 1"
        result = conn.execute(text(query), {"value": f"%{search_name}%"}).fetchall()
        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)

        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def compare_records(row1, row2):
    """比对两条记录，返回差异列表"""
    differences = []
    all_cols = sorted(set(row1.index) | set(row2.index))

    for col in all_cols:
        val1 = row1.get(col, '') if col in row1.index else ''
        val2 = row2.get(col, '') if col in row2.index else ''

        # 处理NaN
        if pd.isna(val1) and pd.isna(val2):
            is_same = True
        elif pd.isna(val1):
            is_same = False
        elif pd.isna(val2):
            is_same = False
        else:
            try:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    is_same = abs(float(val1) - float(val2)) < 1e-9
                else:
                    is_same = str(val1).strip() == str(val2).strip()
            except:
                is_same = str(val1).strip() == str(val2).strip()

        if not is_same:
            differences.append({
                '字段名': col,
                '财务表值': str(val1) if not pd.isna(val1) else 'NULL',
                'HRM表值': str(val2) if not pd.isna(val2) else 'NULL'
            })

    return differences


def get_all_employees(conn, table_name, name_col, id_col=None, limit=None):
    """获取表中所有员工数据"""
    try:
        if limit:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
        else:
            query = f"SELECT * FROM {table_name}"

        result = conn.execute(text(query)).fetchall()
        if result:
            cols = conn.execute(text(f"SHOW COLUMNS FROM {table_name}")).fetchall()
            col_names = [c[0] for c in cols]
            return pd.DataFrame(result, columns=col_names)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return pd.DataFrame()


# ============================================================
# 6. 核心功能（仅在连接成功后显示）
# ============================================================
if st.session_state.connected and st.session_state.engine:
    try:
        engine = st.session_state.engine
        table1 = st.session_state.table1
        table2 = st.session_state.table2
        col1 = st.session_state.col1
        col2 = st.session_state.col2

        with engine.connect() as conn:
            st.success(f"✅ 已连接到数据库: {st.session_state.db_name}")
            st.info(f"📊 表1 '{table1}' 共 {st.session_state.count1} 条记录，{len(col1)} 列")
            st.info(f"📊 表2 '{table2}' 共 {st.session_state.count2} 条记录，{len(col2)} 列")

            # 识别姓名列
            name_col1 = find_name_column(col1)
            name_col2 = find_name_column(col2)
            id_col1 = find_id_column(col1)
            id_col2 = find_id_column(col2)

            with st.expander("📌 识别的关键字段", expanded=True):
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown(f"**表1 (财务表): {table1}**")
                    st.caption(f"• 姓名列: `{name_col1 if name_col1 else '未识别'}`")
                    st.caption(f"• ID列: `{id_col1 if id_col1 else '未识别'}`")
                with col_info2:
                    st.markdown(f"**表2 (HRM表): {table2}**")
                    st.caption(f"• 姓名列: `{name_col2 if name_col2 else '未识别'}`")
                    st.caption(f"• ID列: `{id_col2 if id_col2 else '未识别'}`")

            # 手动选择姓名列
            st.markdown("#### ⚙️ 字段配置")
            col_config1, col_config2 = st.columns(2)
            with col_config1:
                name_col1 = st.selectbox(
                    f"表1的姓名列",
                    options=col1,
                    index=col1.index(name_col1) if name_col1 in col1 else 0,
                    key="name_col1_select"
                )
            with col_config2:
                name_col2 = st.selectbox(
                    f"表2的姓名列",
                    options=col2,
                    index=col2.index(name_col2) if name_col2 in col2 else 0,
                    key="name_col2_select"
                )

            # ============================================================
            # 功能选择
            # ============================================================
            st.markdown("---")
            st.markdown("### 🎯 选择功能")

            func_tab1, func_tab2, func_tab3 = st.tabs([
                "🔍 单条查询比对",
                "📊 批量比对（按财务表）",
                "📋 查看全部数据"
            ])

            # ============================================================
            # Tab 1: 单条查询比对
            # ============================================================
            with func_tab1:
                st.markdown("#### 👤 输入员工姓名进行查询比对")

                # 获取姓名列表
                @st.cache_data(ttl=60)
                def get_all_names(_conn, _table1, _name_col1, _table2, _name_col2):
                    names = []
                    try:
                        if _name_col1:
                            query1 = f"SELECT DISTINCT {_name_col1} FROM {_table1} WHERE {_name_col1} IS NOT NULL AND {_name_col1} != '' LIMIT 500"
                            result1 = _conn.execute(text(query1)).fetchall()
                            names.extend([str(r[0]) for r in result1 if r[0]])

                        if _name_col2:
                            query2 = f"SELECT DISTINCT {_name_col2} FROM {_table2} WHERE {_name_col2} IS NOT NULL AND {_name_col2} != '' LIMIT 500"
                            result2 = _conn.execute(text(query2)).fetchall()
                            names.extend([str(r[0]) for r in result2 if r[0]])
                    except Exception as e:
                        st.warning(f"获取姓名列表失败: {e}")
                    names = list(set(names))
                    names.sort()
                    return names

                all_names = get_all_names(conn, table1, name_col1, table2, name_col2)

                search_method = st.radio(
                    "选择输入方式",
                    ["✏️ 手动输入", "📋 从列表选择"],
                    horizontal=True,
                    key="search_method_single"
                )

                employee_name = ""
                search_mode = "fuzzy"

                if search_method == "✏️ 手动输入":
                    employee_name = st.text_input(
                        "输入员工姓名",
                        placeholder="请输入完整或部分姓名",
                        key="employee_name_input_single"
                    )
                    search_mode = "fuzzy"
                else:
                    if all_names:
                        employee_name = st.selectbox(
                            "从列表中选择姓名",
                            options=[""] + all_names,
                            key="employee_name_select_single"
                        )
                        search_mode = "exact"
                    else:
                        st.warning("⚠️ 暂无姓名数据，请手动输入")
                        employee_name = st.text_input(
                            "输入员工姓名",
                            placeholder="请输入完整或部分姓名",
                            key="employee_name_input_single_fallback"
                        )
                        search_mode = "fuzzy"

                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    search_btn = st.button("🔍 查询比对", use_container_width=True, type="primary", key="search_btn_single")

                if search_btn and employee_name:
                    st.markdown("---")
                    st.markdown(f"### 📋 查询结果比对")
                    st.caption(f"🔍 搜索条件: {employee_name}")

                    with st.spinner("正在查询数据..."):
                        df1 = query_by_name(conn, table1, name_col1, employee_name, search_mode)
                        df2 = query_by_name(conn, table2, name_col2, employee_name, search_mode)

                        st.info(f"📊 表1 找到 {len(df1)} 条 | 表2 找到 {len(df2)} 条")

                        if df1.empty and df2.empty:
                            st.warning(f"⚠️ 在两张表中均未找到记录")
                        elif df1.empty:
                            st.warning(f"⚠️ 在表1中未找到记录")
                            st.dataframe(df2, use_container_width=True)
                        elif df2.empty:
                            st.warning(f"⚠️ 在表2中未找到记录")
                            st.dataframe(df1, use_container_width=True)
                        else:
                            # 显示比对结果
                            tab1, tab2, tab3 = st.tabs([
                                f"📄 表1 ({len(df1)}条)",
                                f"📄 表2 ({len(df2)}条)",
                                "🔗 记录比对"
                            ])

                            df1_selected = df1.iloc[[0]] if len(df1) > 0 else None
                            df2_selected = df2.iloc[[0]] if len(df2) > 0 else None

                            with tab1:
                                st.dataframe(df1, use_container_width=True)
                                if len(df1) > 1:
                                    selected_idx1 = st.selectbox(
                                        "选择要参与比对的记录",
                                        options=df1.index.tolist(),
                                        format_func=lambda x: f"{df1.loc[x, name_col1]} (行{x+1})",
                                        key="select1_single"
                                    )
                                    df1_selected = df1.loc[[selected_idx1]]

                            with tab2:
                                st.dataframe(df2, use_container_width=True)
                                if len(df2) > 1:
                                    selected_idx2 = st.selectbox(
                                        "选择要参与比对的记录",
                                        options=df2.index.tolist(),
                                        format_func=lambda x: f"{df2.loc[x, name_col2]} (行{x+1})",
                                        key="select2_single"
                                    )
                                    df2_selected = df2.loc[[selected_idx2]]

                            with tab3:
                                if df1_selected is not None and df2_selected is not None:
                                    # 使用显示比对函数
                                    from streamlit.runtime.scriptrunner import add_script_run_ctx
                                    # 直接在这里展示比对结果
                                    row1 = df1_selected.iloc[0]
                                    row2 = df2_selected.iloc[0]

                                    diff = compare_records(row1, row2)

                                    st.markdown(f"#### 📊 比对统计")
                                    c1, c2, c3 = st.columns(3)
                                    total_cols = len(set(row1.index) | set(row2.index))
                                    with c1:
                                        st.metric("总字段数", total_cols)
                                    with c2:
                                        st.metric("差异字段", len(diff), delta_color="inverse")
                                    with c3:
                                        consistency = (total_cols - len(diff)) / total_cols * 100 if total_cols else 0
                                        st.metric("一致性", f"{consistency:.1f}%")

                                    if diff:
                                        st.markdown(f"#### 🔴 差异字段详情 ({len(diff)}个)")
                                        diff_df = pd.DataFrame(diff)
                                        st.dataframe(diff_df, use_container_width=True, hide_index=True)

                                        # 导出差异
                                        st.download_button(
                                            label="📥 下载差异报告 (CSV)",
                                            data=diff_df.to_csv(index=False, encoding='utf-8-sig'),
                                            file_name=f"比对差异_{employee_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            key="download_single"
                                        )
                                    else:
                                        st.success("🎉 两条记录完全一致！")

            # ============================================================
            # Tab 2: 批量比对
            # ============================================================
            with func_tab2:
                st.markdown("#### 📊 批量比对（以财务表为基准）")
                st.caption("将遍历财务表中的每一条记录，在HRM表中查找匹配项并进行比对")

                # 批量比对配置
                col_batch1, col_batch2 = st.columns(2)
                with col_batch1:
                    batch_limit = st.number_input(
                        "限制比对数量（0表示全部）",
                        min_value=0,
                        max_value=10000,
                        value=0,
                        step=100,
                        key="batch_limit"
                    )
                with col_batch2:
                    match_mode = st.selectbox(
                        "匹配方式",
                        ["按姓名精确匹配", "按姓名模糊匹配", "按工号匹配"],
                        key="match_mode"
                    )

                # 匹配方式说明
                st.info("💡 匹配方式说明：\n"
                        "• 按姓名精确匹配：姓名必须完全一致\n"
                        "• 按姓名模糊匹配：HRM表中包含财务表姓名即可\n"
                        "• 按工号匹配：用工号进行匹配（需要工号列）")

                # 是否显示详细进度
                show_detail = st.checkbox("显示详细进度", value=True, key="show_detail")

                # 开始批量比对
                if st.button("🚀 开始批量比对", use_container_width=True, type="primary", key="batch_btn"):
                    st.markdown("---")
                    st.markdown("### 📊 批量比对进行中")

                    # 获取财务表所有数据
                    with st.spinner("正在加载财务表数据..."):
                        limit = None if batch_limit == 0 else batch_limit
                        df_financial = get_all_employees(conn, table1, name_col1, id_col1, limit)

                        if df_financial.empty:
                            st.error("❌ 财务表无数据，请检查")
                        else:
                            total = len(df_financial)
                            st.success(f"✅ 已加载财务表 {total} 条记录")

                            # 判断使用哪种匹配方式
                            use_id = match_mode == "按工号匹配" and id_col1 and id_col2

                            # 进度条
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # 存储结果
                            results = []
                            matched_count = 0
                            unmatched_count = 0
                            diff_details = []

                            # 遍历每条记录
                            for idx, row in df_financial.iterrows():
                                status_text.text(f"正在处理: {idx+1}/{total} - {row.get(name_col1, '未知')}")

                                # 查找匹配
                                df_hrm = pd.DataFrame()

                                if use_id:
                                    # 用工号匹配
                                    id_value = row.get(id_col1, '')
                                    if id_value and not pd.isna(id_value):
                                        df_hrm = query_by_id(conn, table2, id_col2, str(id_value))
                                else:
                                    # 用姓名匹配
                                    name_value = row.get(name_col1, '')
                                    if name_value and not pd.isna(name_value):
                                        if match_mode == "按姓名精确匹配":
                                            df_hrm = query_by_name(conn, table2, name_col2, str(name_value), "exact")
                                        else:
                                            df_hrm = find_best_match_by_name(conn, table2, name_col2, str(name_value))

                                # 记录结果
                                record_result = {
                                    '序号': idx + 1,
                                    '财务表_姓名': row.get(name_col1, ''),
                                    '工号': row.get(id_col1, '') if id_col1 else '',
                                    '匹配状态': '✅ 已匹配' if not df_hrm.empty else '❌ 未匹配'
                                }

                                if not df_hrm.empty:
                                    matched_count += 1
                                    hrm_row = df_hrm.iloc[0]
                                    record_result['HRM表_姓名'] = hrm_row.get(name_col2, '')
                                    if id_col2:
                                        record_result['HRM表_工号'] = hrm_row.get(id_col2, '')

                                    # 比对差异
                                    diff = compare_records(row, hrm_row)
                                    diff_count = len(diff)
                                    record_result['差异字段数'] = diff_count

                                    if diff:
                                        for d in diff:
                                            d['财务表_姓名'] = row.get(name_col1, '')
                                            d['HRM表_姓名'] = hrm_row.get(name_col2, '')
                                            d['工号'] = row.get(id_col1, '') if id_col1 else ''
                                            diff_details.append(d)
                                else:
                                    unmatched_count += 1
                                    record_result['HRM表_姓名'] = '未找到'
                                    record_result['差异字段数'] = 'N/A'

                                results.append(record_result)

                                # 更新进度
                                progress_bar.progress((idx + 1) / total)

                            # 完成
                            status_text.text("✅ 比对完成！")

                            # 保存结果到session
                            st.session_state.batch_results = {
                                'results': results,
                                'diff_details': diff_details,
                                'total': total,
                                'matched': matched_count,
                                'unmatched': unmatched_count
                            }
                            st.session_state.batch_complete = True

                            # ============================================================
                            # 显示结果
                            # ============================================================
                            st.markdown("---")
                            st.markdown("### 📊 比对结果汇总")

                            # 统计卡片
                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                            with col_stat1:
                                st.metric("总记录数", total)
                            with col_stat2:
                                st.metric("✅ 已匹配", matched_count, delta=f"{matched_count/total*100:.1f}%" if total > 0 else "0%")
                            with col_stat3:
                                st.metric("❌ 未匹配", unmatched_count, delta=f"{unmatched_count/total*100:.1f}%" if total > 0 else "0%")
                            with col_stat4:
                                if matched_count > 0:
                                    total_diff_fields = sum([r.get('差异字段数', 0) for r in results if isinstance(r.get('差异字段数'), int)])
                                    avg_diff = total_diff_fields / matched_count
                                    st.metric("平均差异字段", f"{avg_diff:.1f}")
                                else:
                                    st.metric("平均差异字段", "N/A")

                            # 匹配状态汇总
                            tab_result1, tab_result2, tab_result3 = st.tabs([
                                "📋 匹配汇总",
                                "🔴 差异详情",
                                "❌ 未匹配列表"
                            ])

                            with tab_result1:
                                df_results = pd.DataFrame(results)
                                st.dataframe(df_results, use_container_width=True, hide_index=True)

                                # 导出汇总
                                st.download_button(
                                    label="📥 下载匹配汇总 (CSV)",
                                    data=df_results.to_csv(index=False, encoding='utf-8-sig'),
                                    file_name=f"批量比对汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    key="download_batch_summary"
                                )

                            with tab_result2:
                                if diff_details:
                                    df_diff = pd.DataFrame(diff_details)
                                    st.dataframe(df_diff, use_container_width=True, hide_index=True)

                                    # 统计差异字段频次
                                    if '字段名' in df_diff.columns:
                                        st.markdown("#### 📊 差异字段频次统计")
                                        field_counts = df_diff['字段名'].value_counts().reset_index()
                                        field_counts.columns = ['字段名', '差异次数']
                                        st.dataframe(field_counts, use_container_width=True, hide_index=True)

                                    st.download_button(
                                        label="📥 下载差异详情 (CSV)",
                                        data=df_diff.to_csv(index=False, encoding='utf-8-sig'),
                                        file_name=f"差异详情_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                        key="download_batch_diff"
                                    )
                                else:
                                    st.success("🎉 所有已匹配的记录完全一致，无差异！")

                            with tab_result3:
                                unmatched_list = [r for r in results if r.get('匹配状态') == '❌ 未匹配']
                                if unmatched_list:
                                    df_unmatched = pd.DataFrame(unmatched_list)
                                    st.dataframe(df_unmatched, use_container_width=True, hide_index=True)

                                    st.download_button(
                                        label="📥 下载未匹配列表 (CSV)",
                                        data=df_unmatched.to_csv(index=False, encoding='utf-8-sig'),
                                        file_name=f"未匹配列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv",
                                        key="download_batch_unmatched"
                                    )
                                else:
                                    st.success("✅ 所有记录均成功匹配！")

                # 显示历史批量比对结果
                if st.session_state.batch_complete and st.session_state.batch_results:
                    with st.expander("📌 查看上次批量比对结果", expanded=False):
                        br = st.session_state.batch_results
                        st.metric("总记录", br['total'])
                        st.metric("已匹配", br['matched'])
                        st.metric("未匹配", br['unmatched'])

            # ============================================================
            # Tab 3: 查看全部数据
            # ============================================================
            with func_tab3:
                st.markdown("#### 📋 查看表数据")

                view_limit = st.number_input("显示条数", min_value=10, max_value=500, value=100, step=50, key="view_limit")

                col_view1, col_view2 = st.columns(2)
                with col_view1:
                    if st.button("📄 查看财务表", use_container_width=True, key="view_financial"):
                        df = get_all_employees(conn, table1, name_col1, id_col1, view_limit)
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"显示前 {len(df)} 条记录")
                with col_view2:
                    if st.button("📄 查看HRM表", use_container_width=True, key="view_hrm"):
                        df = get_all_employees(conn, table2, name_col2, id_col2, view_limit)
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"显示前 {len(df)} 条记录")

    except Exception as e:
        st.error(f"❌ 操作失败: {e}")
        st.info("请重新连接数据库")

else:
    st.info("👈 请先在左侧配置数据库连接并点击连接按钮")

# ============================================================
# 7. 页脚
# ============================================================
st.markdown("---")
st.caption(f"🕐 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")