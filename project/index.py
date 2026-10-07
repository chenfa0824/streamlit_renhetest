import streamlit as st

# -------------------------- 页面全局配置（必须放最顶部） --------------------------
st.set_page_config(
    page_title="系统管理平台",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局样式注入：统一美化字体、卡片、按钮
st.markdown("""
<style>
/* 全局字体 */
* {
    font-family: "Microsoft YaHei", sans-serif;
}
/* 主标题样式 */
.main-title {
    font-size: 36px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 8px;
}
/* 副标题 */
.sub-desc {
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 40px;
}
/* 功能卡片容器 */
.card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: all 0.25s ease;
    height: 100%;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
/* 卡片标题 */
.card-title {
    font-size: 20px;
    font-weight: 600;
    color: #111827;
    margin: 12px 0 8px 0;
}
/* 卡片描述 */
.card-text {
    color: #4b5563;
    font-size: 14px;
    line-height: 1.6;
}
/* 底部版权栏 */
.footer {
    margin-top: 60px;
    text-align: center;
    color: #9ca3af;
    font-size: 13px;
}
/* 侧边栏优化 */
.stSidebar {
    background-color: #f9fafb;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 侧边栏导航区 --------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/180x60/3b82f6/ffffff?text=SYSTEM", use_column_width=True)
    st.divider()
    st.subheader("功能导航")
    nav_home = st.button("🏠 首页", use_container_width=True, type="primary")
    nav_data = st.button("📊 数据看板", use_container_width=True)
    nav_user = st.button("👤 用户管理", use_container_width=True)
    nav_setting = st.button("⚙️ 系统设置", use_container_width=True)
    nav_log = st.button("📜 操作日志", use_container_width=True)

    st.divider()
    st.caption("当前登录：管理员 | 2026-07-14")

# -------------------------- 首页主体内容 --------------------------
# 顶部标题区域
st.markdown('<div class="main-title">欢迎使用管理系统</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-desc">一站式数据与业务管理平台 · 简洁高效后台系统</div>', unsafe_allow_html=True)
st.divider()

# 修复点：去掉 gap="2rem"，默认中等间距
col1, col2, col3 = st.columns(3)

# 卡片1：数据看板
with col1:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">📈</span>
        <div class="card-title">数据可视化看板</div>
        <div class="card-text">实时查看业务统计、趋势图表、营收报表，多维度数据分析。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("进入看板", key="btn1", use_container_width=True)

# 卡片2：用户管理
with col2:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">👥</span>
        <div class="card-title">账号权限管理</div>
        <div class="card-text">新增/编辑用户、角色分配、菜单权限控制、账号状态维护。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("用户管理", key="btn2", use_container_width=True)

# 卡片3：系统配置
with col3:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">🔧</span>
        <div class="card-title">基础系统设置</div>
        <div class="card-text">系统参数配置、字典管理、通知模板、文件存储配置。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("系统配置", key="btn3", use_container_width=True)

# 第二行功能卡片
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">📦</span>
        <div class="card-title">业务数据管理</div>
        <div class="card-text">业务单据录入、批量导入导出、数据检索与批量操作。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("业务管理", key="btn4", use_container_width=True)

with col5:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">📝</span>
        <div class="card-title">操作审计日志</div>
        <div class="card-text">记录全部用户操作行为，支持时间筛选、导出追溯。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("查看日志", key="btn5", use_container_width=True)

with col6:
    st.markdown("""
    <div class="card">
        <span style="font-size:40px;">❓</span>
        <div class="card-title">帮助中心</div>
        <div class="card-text">操作文档、常见问题、联系技术支持。</div>
    </div>
    """, unsafe_allow_html=True)
    st.button("查看文档", key="btn6", use_container_width=True)

# 系统概览简单统计模块
st.divider()
st.subheader("今日系统概览")
stat1, stat2, stat3, stat4 = st.columns(4)
stat1.metric("在线用户", value="128", delta="+12")
stat2.metric("今日新增数据", value="365", delta="+46")
stat3.metric("待处理任务", value="18", delta="-5")
stat4.metric("系统运行天数", value="426")

# 底部版权信息
st.markdown('<div class="footer">© 2026 管理系统 All Rights Reserved | 简洁版后台首页</div>', unsafe_allow_html=True)