import streamlit as st
import git
from git import Repo
import tempfile
import os
import hashlib
from pathlib import Path
from datetime import timedelta

# ===================== 页面全局配置 =====================
st.set_page_config(
    page_title="Git分支比对工具",
    layout="wide",
    initial_sidebar_state="auto"
)

# 精简优雅CSS
custom_css = """
<style>
.block-container {padding: 1rem 2rem; max-width:1650px;}
/* Diff代码区域 */
.diff-wrap {
    font-family: "Consolas","Monaco",monospace;
    white-space: pre-wrap;
    font-size:14px;
    line-height:1.45;
    border-radius:6px;
    overflow-x:auto;
    padding:4px 0;
}
.diff-line-add {
    background-color:#e6ffec;
    color:#116329;
    padding:2px 8px;
    display:block;
}
.diff-line-del {
    background-color:#ffebe9;
    color:#cf222e;
    padding:2px 8px;
    display:block;
}
.diff-line-normal {
    padding:2px 8px;
    display:block;
}
/* 文件状态标签 */
.badge-new {background:#2da44e;color:#fff;padding:2px 6px;border-radius:3px;font-size:12px;margin-right:6px;}
.badge-del {background:#cf222e;color:#fff;padding:2px 6px;border-radius:3px;font-size:12px;margin-right:6px;}
.badge-mod {background:#8c959f;color:#fff;padding:2px 6px;border-radius:3px;font-size:12px;margin-right:6px;}
.badge-rename {background:#0969da;color:#fff;padding:2px 6px;border-radius:3px;font-size:12px;margin-right:6px;}
/* 单选组件美化 */
.stRadio [data-testid="stWidgetLabel"] {display:none;}
.stRadio > div {gap:2px !important;}
.stRadio label {padding:4px 6px;border-radius:4px;margin:1px 0;cursor:pointer;}
.stRadio label:hover {background:#f3f4f6;}
.commit-card{
    border:1px solid #e5e7eb;
    border-radius:6px;
    padding:12px 16px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.title("🔍 Git 分支代码比对工具")

# ========== 时间格式化工具：转为北京时间 UTC+8 ==========
def format_beijing_time(datetime_obj):
    """git提交时间默认UTC，转换北京时间并格式化字符串"""
    bj_time = datetime_obj + timedelta(hours=8)
    return bj_time.strftime("%Y-%m-%d %H:%M:%S")

# 根据仓库地址生成独立临时文件夹
def get_repo_local_path(git_url: str):
    temp_root = tempfile.gettempdir()
    hash_str = hashlib.md5(git_url.encode("utf-8")).hexdigest()[:12]
    folder_name = f"git_compare_{hash_str}"
    return os.path.join(temp_root, folder_name)

@st.cache_resource(show_spinner="正在克隆/加载仓库...")
def load_git_repo(git_url: str):
    local_path = get_repo_local_path(git_url)
    try:
        if os.path.exists(local_path) and os.path.exists(Path(local_path) / ".git"):
            repo = Repo(local_path)
            repo.remote().fetch()
        else:
            repo = Repo.clone_from(git_url, local_path)
        return repo
    except Exception as e:
        st.error(f"仓库加载失败：{str(e)}")
        return None

def get_all_branches(repo: Repo):
    branches = []
    for ref in repo.remote().refs:
        branch_name = ref.name.replace("origin/", "")
        if branch_name != "HEAD":
            branches.append(branch_name)
    return sorted(list(set(branches)))

def compare_branch(repo: Repo, base_branch: str, compare_branch: str):
    base_ref = f"origin/{base_branch}"
    compare_ref = f"origin/{compare_branch}"

    base_commit = repo.rev_parse(base_ref)
    compare_commit = repo.rev_parse(compare_ref)

    merge_base = repo.merge_base(base_commit, compare_commit)[0]
    ahead_commits = list(repo.iter_commits(f"{merge_base}..{compare_ref}"))
    behind_commits = list(repo.iter_commits(f"{merge_base}..{base_ref}"))
    file_diffs = base_commit.diff(compare_commit, create_patch=True)
    return base_commit, compare_commit, ahead_commits, behind_commits, list(file_diffs)

def render_color_diff(diff_raw: bytes):
    html_lines = []
    try:
        text = diff_raw.decode("utf-8", errors="replace")
    except Exception:
        text = str(diff_raw)

    for line in text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            html_lines.append(f'<span class="diff-line-add">{line}</span>')
        elif line.startswith("-") and not line.startswith("---"):
            html_lines.append(f'<span class="diff-line-del">{line}</span>')
        else:
            html_lines.append(f'<span class="diff-line-normal">{line}</span>')
    full_html = '<div class="diff-wrap">' + "\n".join(html_lines) + "</div>"
    st.markdown(full_html, unsafe_allow_html=True)

def build_file_info(diff_obj):
    if diff_obj.new_file:
        status_text = "新增"
        badge_class = "badge-new"
        filepath = diff_obj.b_path
    elif diff_obj.deleted_file:
        status_text = "删除"
        badge_class = "badge-del"
        filepath = diff_obj.a_path
    elif diff_obj.renamed:
        status_text = "重命名"
        badge_class = "badge-rename"
        filepath = diff_obj.b_path
    else:
        status_text = "修改"
        badge_class = "badge-mod"
        filepath = diff_obj.b_path
    return {
        "path": filepath,
        "status": status_text,
        "badge": badge_class,
        "diff": diff_obj
    }

# ===================== 会话状态 =====================
if "file_list" not in st.session_state:
    st.session_state.file_list = []
if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = -1
if "base_latest_commit" not in st.session_state:
    st.session_state.base_latest_commit = None
if "target_latest_commit" not in st.session_state:
    st.session_state.target_latest_commit = None

# ===================== 顶部控制区域【紧凑布局】 =====================
# 默认Git地址
DEFAULT_GIT_URL = "http://gitlab.whrhkj.com/chenfa/demo01.git"
git_repo_url = st.text_input("📦 Git仓库地址", value=DEFAULT_GIT_URL, placeholder="https://xxx.git 或 git@xxx:xxx.git")

repo = None
if git_repo_url.strip():
    repo = load_git_repo(git_repo_url.strip())

if repo:
    branch_list = get_all_branches(repo)
    c1, c2 = st.columns([2, 2])
    with c1:
        branch_base = st.selectbox("基准分支(Base)", options=branch_list, index=0)
    with c2:
        branch_target = st.selectbox("对比分支(Target)", options=branch_list, index=1)
    # 开始比对按钮独占一行
    start_btn = st.button("开始对比", type="primary", use_container_width=True)

    if start_btn:
        if branch_base == branch_target:
            st.warning("基准分支与对比分支不能相同！")
            st.session_state.file_list = []
            st.session_state.selected_idx = -1
        else:
            with st.spinner("正在计算代码差异..."):
                base_commit, target_commit, ahead, behind, diff_objs = compare_branch(repo, branch_base, branch_target)
                # 保存两个分支最新提交信息
                st.session_state.base_latest_commit = base_commit
                st.session_state.target_latest_commit = target_commit

                file_info_list = [build_file_info(d) for d in diff_objs]
                st.session_state.file_list = file_info_list
                st.session_state.selected_idx = 0 if len(file_info_list) > 0 else -1
                st.session_state.ahead_commits = ahead
                st.session_state.behind_commits = behind

    # ========== 展示两个分支最新版本信息 ==========
    if st.session_state.base_latest_commit and st.session_state.target_latest_commit:
        st.divider()
        st.subheader("📌 分支最新版本信息")
        col_base, col_target = st.columns(2)
        base_c = st.session_state.base_latest_commit
        target_c = st.session_state.target_latest_commit

        base_time_str = format_beijing_time(base_c.authored_datetime)
        target_time_str = format_beijing_time(target_c.authored_datetime)

        with col_base:
            st.markdown(f"""
            <div class="commit-card">
                <strong>基准分支：{branch_base}</strong>
                <p>提交ID：{base_c.hexsha}</p>
                <p>提交人：{base_c.author.name} &lt;{base_c.author.email}&gt;</p>
                <p>提交时间（北京时间）：{base_time_str}</p>
                <p>提交备注：{base_c.summary}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_target:
            st.markdown(f"""
            <div class="commit-card">
                <strong>对比分支：{branch_target}</strong>
                <p>提交ID：{target_c.hexsha}</p>
                <p>提交人：{target_c.author.name} &lt;{target_c.author.email}&gt;</p>
                <p>提交时间（北京时间）：{target_time_str}</p>
                <p>提交备注：{target_c.summary}</p>
            </div>
            """, unsafe_allow_html=True)

    # 存在变更文件
    if len(st.session_state.file_list) > 0:
        st.divider()
        # 统计信息
        stat_col1, stat_col2 = st.columns(2)
        with stat_col1:
            st.metric(f"{branch_target} 新增提交", len(st.session_state.ahead_commits))
        with stat_col2:
            st.metric(f"{branch_base} 独有提交", len(st.session_state.behind_commits))

        # 提交记录折叠展示，不占用主视觉
        with st.expander("📜 查看提交记录"):
            tab_a, tab_b = st.tabs(["Target新增提交", "Base独有提交"])
            with tab_a:
                if st.session_state.ahead_commits:
                    for commit in st.session_state.ahead_commits:
                        t_str = format_beijing_time(commit.authored_datetime)
                        st.code(f"{commit.hexsha[:10]} | {t_str} | {commit.summary}", language="text")
                else:
                    st.info("无提交")
            with tab_b:
                if st.session_state.behind_commits:
                    for commit in st.session_state.behind_commits:
                        t_str = format_beijing_time(commit.authored_datetime)
                        st.code(f"{commit.hexsha[:10]} | {t_str} | {commit.summary}", language="text")
                else:
                    st.info("无提交")

        st.divider()
        # ========== 核心布局：左侧文件列表｜右侧Diff详情 ==========
        left, right = st.columns([0.30, 0.70])
        file_list = st.session_state.file_list

        with left:
            st.subheader(f"📁 变更文件（共{len(file_list)}个）")
            radio_items = []
            for idx, item in enumerate(file_list):
                radio_items.append(f'[{idx}] {item["path"]}')

            selected_str = st.radio("", options=radio_items, index=st.session_state.selected_idx)
            selected_index = int(selected_str.split("]")[0].strip("["))
            st.session_state.selected_idx = selected_index

        with right:
            selected_file = file_list[selected_index]
            st.subheader(selected_file["path"])
            st.markdown(f'<span class="{selected_file["badge"]}">{selected_file["status"]}</span>', unsafe_allow_html=True)
            st.divider()
            diff_data = selected_file["diff"]
            if diff_data.diff:
                render_color_diff(diff_data.diff)
            else:
                st.warning("未读取到代码变更")

    elif start_btn and len(st.session_state.file_list) == 0:
        st.success("✅ 两个分支代码完全一致，无任何变更！")

else:
    st.info("请输入有效的Git仓库地址，等待仓库加载完成")

# 底部图例
st.divider()
legend = """
<span style="background:#e6ffec;color:#116329;padding:3px 8px;border-radius:4px;">绿色=新增代码</span>
&nbsp;&nbsp;
<span style="background:#ffebe9;color:#cf222e;padding:3px 8px;border-radius:4px;">红色=删除代码</span>
"""
st.markdown(legend, unsafe_allow_html=True)
st.caption("提示：本地需要安装Git并配置仓库访问权限 | 首次克隆仓库耗时较长")