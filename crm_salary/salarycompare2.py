import requests
import pandas as pd
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 批量调用hrm测试环境接口查询，与财务提供的已发送工资进行比对
# ===================== 1. 可修改配置项 =====================
# 接口地址
API_URL = "https://hrm-apitest.whrhkj.com/salary/salesperson/summary/list"
# 接口认证Token
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODE3NjYwODIsInVzZXJuYW1lIjoiMTEyMDU0In0.wY6Ar3Z-jMXVi-5nXn4cuubsuVZfpJYNMHJosA6RmcU"
# 薪资查询月份
SALARY_MONTH = "2026-03"
# 原始Excel文件路径
ORIGINAL_EXCEL_PATH = "1.xlsx"
# 结果Excel文件输出路径
OUTPUT_EXCEL_PATH = "2.xlsx"
# 接口请求超时时间（秒）
REQUEST_TIMEOUT = 10
# 每次请求间隔时间（秒），避免接口限流
REQUEST_INTERVAL = 0.2
# 最大重试次数（接口异常时自动重试）
MAX_RETRIES = 2
# 处理行数限制（测试用，注释掉则处理全部数据）
# TEST_ROW_LIMIT = 100

# ===================== 2. 初始化请求Session（性能优化）=====================
# 复用TCP连接，大幅提升批量请求速度
session = requests.Session()
# 配置自动重试策略，处理接口临时异常
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)
# 设置全局请求头
session.headers.update({
    "x-access-token": ACCESS_TOKEN,
    "Content-Type": "application/json"
})

# ===================== 3. 读取原始Excel数据 =====================
df = pd.read_excel(ORIGINAL_EXCEL_PATH, sheet_name="3月人员工资总额")

# 测试模式：仅处理指定行数，本地运行可注释此行
# if 'TEST_ROW_LIMIT' in locals() and TEST_ROW_LIMIT:
#     df = df.head(TEST_ROW_LIMIT)

print(f"✅ 成功读取原始数据，共{len(df)}行人员信息")
print(f"📊 原始数据列：{df.columns.tolist()}")


# ===================== 4. 定义接口查询函数 =====================
def get_sfgz_by_name(username: str) -> str:
    """
    根据姓名调用接口查询实发工资sfgz
    :param username: 人员姓名
    :return: 成功返回sfgz数值，无数据/失败返回空字符串
    """
    request_body = {
        "salaryMonth": SALARY_MONTH,
        "username": username
    }
    try:
        # 发起POST请求
        response = session.post(API_URL, json=request_body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response_json = response.json()

        # 校验接口业务状态
        if not response_json.get("success"):
            return ""
        # 提取结果数据
        result_list = response_json.get("result", [])
        if not result_list:
            return ""
        # 返回sfgz字段
        return str(result_list[0].get("sfgz", ""))
    except Exception:
        # 所有异常统一返回空，不中断主流程
        return ""


# ===================== 5. 批量查询并写入结果 =====================
# 新增第三列，表头固定为【HRM查询实发工资】
df["HRM查询实发工资"] = ""
success_count = 0
total_count = len(df)

# 遍历所有人员
for index, row in df.iterrows():
    name = row["姓名"]
    # 跳过空姓名
    if pd.isna(name) or str(name).strip() == "":
        continue

    # 调用接口查询
    sfgz_value = get_sfgz_by_name(str(name).strip())
    # 有数据则写入，无数据不记录（保持空）
    if sfgz_value:
        df.at[index, "HRM查询实发工资"] = sfgz_value
        success_count += 1

    # 请求间隔，避免接口限流
    time.sleep(REQUEST_INTERVAL)

    # 每处理20行打印一次进度
    if (index + 1) % 20 == 0:
        print(f"⏳ 已处理{index + 1}/{total_count}行，成功查询{success_count}条数据")

# ===================== 6. 生成最终Excel文件 =====================
with pd.ExcelWriter(OUTPUT_EXCEL_PATH, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="3月人员工资总额_HRM查询结果", index=False)

# 输出最终统计结果
print(f"\n🎉 ===================== 处理完成 ===================== 🎉")
print(f"📌 总处理人数：{total_count}")
print(f"✅ 成功查询到实发工资的人数：{success_count}")
print(f"❌ 无数据/查询失败的人数：{total_count - success_count}")
print(f"📁 结果文件已保存至：{OUTPUT_EXCEL_PATH}")
print(f"\n💡 说明：第一列【姓名】、第二列【工资总额】完全保留原始数据，无任何修改")