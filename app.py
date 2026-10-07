# streamlit_app.py
import streamlit as st

# hrm系统
hrmUpdate = st.Page("hrm/hrmUpdate.py", title="绩效修改", icon="🏠")
hrmCheck = st.Page("hrm/hrmCheck.py", title="绩效预警", icon="⚙️")
createOffer = st.Page("hrm/createOffer.py", title="创建Offer", icon="⚙️")
createOffer2 = st.Page("hrm/createOffer2.py", title="创建Offer2", icon="⚙️")

# crm系统
xunjian = st.Page("crm_xunjian/xunjian.py", title="自动化巡检", icon="🏠")
xunjian2 = st.Page("crm_xunjian/xunjian2.py", title="自动化巡检2", icon="🏠")
salary = st.Page("crm_salary/salary.py", title="工资比对", icon="🏠")
chufeng1 = st.Page("crm_chufeng/chufeng1.py", title="楚凤活动1", icon="🏠")
chufeng2 = st.Page("crm_chufeng/chufeng2.py", title="楚凤活动2", icon="🏠")
chufeng3 = st.Page("crm_chufeng/chufeng3.py", title="楚凤活动3", icon="🏠")

# sql
mysql1 = st.Page("sql/mysql1.py", title="mysql1", icon="🏠")
mysql2 = st.Page("sql/mysql2.py", title="mysql2", icon="🏠")
postgresql1 = st.Page("sql/postgresql1.py", title="postgresql1", icon="🏠")
postgresql2 = st.Page("sql/postgresql2.py", title="postgresql2", icon="🏠")

# 工具：定义所有页面
xmind1 = st.Page("utils/xmind1.py", title="xmind1", icon="📊")
xmind2 = st.Page("utils/xmind2.py", title="xmind2", icon="📊")
crm_api = st.Page("utils/crmApi.py", title="crm_api", icon="📊")
hrm_api = st.Page("utils/hrmApi.py", title="hrm_api", icon="📊")
git_branch = st.Page("utils/git_branch.py", title="git_branch", icon="📊")

# streamlit DEMO演示
demo0 = st.Page("streamlit/demo/demo0.py", title="demo0", icon="🏠")
demo1 = st.Page("streamlit/demo/demo1.py", title="demo1", icon="🏠")
demo2 = st.Page("streamlit/demo/demo2.py", title="demo2", icon="🏠")
demo3 = st.Page("streamlit/demo/demo3.py", title="demo3", icon="🏠")
demo4 = st.Page("streamlit/demo/demo4.py", title="demo4", icon="🏠")
sidebar1 = st.Page("streamlit/demo/sidebar1.py", title="sidebar1", icon="🏠")
sidebar2 = st.Page("streamlit/demo/sidebar2.py", title="sidebar2", icon="🏠")
tab1 = st.Page("streamlit/demo/tab1.py", title="tab1", icon="🏠")
tab2 = st.Page("streamlit/demo/tab2.py", title="tab2", icon="🏠")
table1 = st.Page("streamlit/demo/table1.py", title="table1", icon="🏠")
table2 = st.Page("streamlit/demo/table2.py", title="table2", icon="🏠")
# 动画
animation0 = st.Page("streamlit/demo/animation0.py", title="animation0", icon="🏠")
animation1 = st.Page("streamlit/demo/animation1.py", title="animation1", icon="🏠")
animation2 = st.Page("streamlit/demo/animation2.py", title="animation2", icon="🏠")
animation3 = st.Page("streamlit/demo/animation3.py", title="animation3", icon="🏠")
animation4 = st.Page("streamlit/demo/animation4.py", title="animation4", icon="🏠")
animation5 = st.Page("streamlit/demo/animation5.py", title="animation5", icon="🏠")
animation6 = st.Page("streamlit/demo/animation6.py", title="animation6", icon="🏠")

ui1 = st.Page("streamlit/ui/ui1.py", title="ui1", icon="📊")
ui2 = st.Page("streamlit/ui/ui2.py", title="ui2", icon="📊")
ui3 = st.Page("streamlit/ui/ui3.py", title="ui3", icon="📊")
elementui1 = st.Page("streamlit/ui/elementui1.py", title="elementui1", icon="🏠")
elementui2 = st.Page("streamlit/ui/elementui2.py", title="elementui2", icon="🏠")
elementui3 = st.Page("streamlit/ui/elementui3.py", title="elementui3", icon="🏠")

# 项目
liang1 = st.Page("liangliang/liang1.py", title="liang1", icon="🏠")
liang2 = st.Page("liangliang/liang2.py", title="liang2", icon="🏠")
liang3 = st.Page("liangliang/liang3.py", title="liang3", icon="🏠")
# mock
mock1 = st.Page("mock/mock1.py", title="mock1", icon="📊")
mock2 = st.Page("mock/mock2.py", title="mock2", icon="📈")

# 配置导航（可以分组）
pg = st.navigation({
    # "Demo": [demo0, demo1, demo2, demo3, demo4, animation0, animation1, animation2, animation3, animation4,
    #          animation5, animation6, sidebar1, sidebar2, tab1, tab2, table1, table2
    #          ],
    # "UI": [ui1, ui2, ui3, elementui1, elementui2, elementui3
    #        ],
    "SQL": [mysql1, mysql2, postgresql1, postgresql2],
    "CRM": [chufeng3, chufeng1, chufeng2,xunjian, xunjian2, salary],
    "HRM": [createOffer, createOffer2, hrmUpdate, hrmCheck],


})

# 执行当前选中的页面
pg.run()
