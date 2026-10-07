import pandas as pd
import pymysql
from pymysql.err import OperationalError, ProgrammingError
from datetime import datetime

# ===================== 配置项（必须修改为你的实际信息） =====================
# 数据库配置
DB_CONFIG = {
    "host": "localhost",       # 数据库地址
    "port": 3306,              # 端口
    "user": "root",            # 用户名
    "password": "root", # 你的数据库密码
    "database": "renhetest", # 你的数据库名（需提前创建）
    "charset": "utf8mb4"       # 固定，支持中文
}

# Excel文件配置
EXCEL_FILE_PATH = "财务数据简化版.xlsx"
EXCEL_SHEET_NAME = "Sheet1"  # 你的Excel工作表名，必须正确！
EXCEL_HEADER_ROW = 0          # 表头所在行（Excel第1行=0，第2行=1，以此类推）
# 数据库表配置
TABLE_NAME = "financial_salary_data_202603"
BATCH_SIZE = 50  # 批次大小，降低避免内存溢出
# ============================================================================

# 1. 数据库连接函数
def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        return conn
    except OperationalError as e:
        print(f"❌ 数据库连接失败：{str(e)}")
        raise

# 2. 自动创建表函数（与Excel列名100%对齐）
def create_salary_table(conn, df_columns):
    """根据Excel列名自动创建表，避免字段名不匹配"""
    # 字段类型映射规则
    def get_column_type(col_name):
        col_name_lower = col_name.lower()
        if any(key in col_name_lower for key in ["序号", "天数", "次数", "人头数"]):
            return "INT"
        elif any(key in col_name_lower for key in ["金额", "工资", "提成", "补贴", "奖金", "率", "点"]):
            return "DECIMAL(12,2)"
        elif any(key in col_name_lower for key in ["时间", "日期"]):
            return "DATE"
        elif any(key in col_name_lower for key in ["详情", "情况", "备注"]):
            return "TEXT"
        else:
            return "VARCHAR(255)"

    # 生成建表SQL
    column_defs = []
    column_defs.append("`id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键'")
    for col in df_columns:
        # 处理列名中的特殊字符、空格
        col_clean = col.strip().replace("\n", "").replace("\r", "")
        col_type = get_column_type(col_clean)
        column_defs.append(f"`{col_clean}` {col_type} COMMENT '{col_clean}'")
    # 工号唯一索引
    column_defs.append("UNIQUE KEY `uk_job_number` (`工号`) COMMENT '工号唯一索引'")

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
        {', '.join(column_defs)}
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='2026年3月财务薪资数据';
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            conn.commit()
        print(f"✅ 表【{TABLE_NAME}】创建成功/已存在，共{len(df_columns)}个业务字段")
    except ProgrammingError as e:
        print(f"❌ 表创建失败：{str(e)}")
        print(f"建表SQL：{create_table_sql}")
        raise

# 3. Excel数据读取与预处理（修复NaN核心问题）
def read_and_preprocess_excel(file_path, sheet_name, header_row):
    print(f"📥 开始读取Excel文件：{file_path}，工作表：{sheet_name}")
    # 1. 先读取Excel表头，确认列名
    df_header = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5, header=header_row)
    print(f"📋 读取到的表头列名：{df_header.columns.tolist()}")

    # 2. 读取全量数据
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    print(f"✅ 原始数据读取完成，共 {df.shape[0]} 行，{df.shape[1]} 列")

    # 3. 核心修复：处理空列名
    df.columns = [
        col.strip().replace("\n", "").replace("\r", "") if pd.notna(col) else f"未命名列_{i}"
        for i, col in enumerate(df.columns)
    ]
    print(f"✅ 空列名处理完成，最终列名：{df.columns.tolist()}")

    # 4. 核心修复：过滤全空行
    df = df.dropna(how="all").reset_index(drop=True)
    print(f"✅ 全空行过滤完成，剩余有效数据：{df.shape[0]} 行")

    # 5. 核心修复：工号列空值处理（必须有工号）
    if "工号" in df.columns:
        df = df.dropna(subset=["工号"]).reset_index(drop=True)
        df["工号"] = df["工号"].astype(str).str.strip()
        print(f"✅ 工号列处理完成，有效工号数据：{df.shape[0]} 行")
    else:
        print("⚠️ 警告：Excel中未找到【工号】列，已跳过唯一索引校验")

    # 6. 日期字段转换（兼容Excel序列号/文本日期）
    date_columns = [col for col in df.columns if "日期" in col or "时间" in col]
    for col in date_columns:
        print(f"📅 处理日期字段：{col}")
        # 先尝试Excel序列号转换
        try:
            df[col] = pd.to_datetime(df[col], unit="D", origin="1899-12-30", errors="coerce").dt.date
        except:
            # 序列号转换失败，尝试文本日期转换
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
        # 空日期填充为None
        df[col] = df[col].where(pd.notna(df[col]), None)

    # 7. 数值字段空值填充为0，文本字段空值填充为None
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].where(pd.notna(df[col]), None)

    print(f"🎉 数据预处理全部完成，最终有效数据：{df.shape[0]} 行，{df.shape[1]} 列")
    return df

# 4. 批量插入数据函数（修复列数不匹配问题）
def batch_insert_data(conn, df):
    total_rows = df.shape[0]
    if total_rows == 0:
        print("⚠️ 无有效数据可插入，程序退出")
        return 0

    print(f"📊 开始批量插入数据，共 {total_rows} 行")
    # 生成插入SQL（列名与DataFrame严格对齐）
    columns = df.columns.tolist()
    placeholders = ", ".join(["%s"] * len(columns))
    # 列名加反引号，避免特殊字符报错
    column_str = ", ".join([f"`{col}`" for col in columns])
    insert_sql = f"INSERT IGNORE INTO `{TABLE_NAME}` ({column_str}) VALUES ({placeholders})"
    print(f"📝 插入SQL：{insert_sql}")

    # 按批次插入
    success_count = 0
    for i in range(0, total_rows, BATCH_SIZE):
        batch_df = df.iloc[i:i+BATCH_SIZE]
        # 转换为列表，处理NaN
        batch_data = []
        for _, row in batch_df.iterrows():
            row_data = []
            for col in columns:
                val = row[col]
                # 处理NaN
                if pd.isna(val):
                    row_data.append(None)
                else:
                    row_data.append(val)
            batch_data.append(row_data)

        try:
            with conn.cursor() as cursor:
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                batch_success = cursor.rowcount
                success_count += batch_success
                print(f"✅ 批次 {i//BATCH_SIZE + 1} 插入成功：{batch_success} 行")
        except Exception as e:
            conn.rollback()
            print(f"❌ 批次 {i//BATCH_SIZE + 1} 插入失败：{str(e)}")
            print(f"失败批次数据行数：{len(batch_data)}，列数：{len(batch_data[0])}")
            raise

    print(f"🎉 全部数据插入完成，共成功插入 {success_count} 行数据")
    return success_count

# 5. 主程序
def main():
    try:
        # 1. 读取并预处理Excel数据
        df = read_and_preprocess_excel(EXCEL_FILE_PATH, EXCEL_SHEET_NAME, EXCEL_HEADER_ROW)
        if df.shape[0] == 0:
            print("❌ 无有效数据，程序终止")
            return

        # 2. 连接数据库
        conn = get_db_connection()

        # 3. 根据Excel列名自动创建表
        create_salary_table(conn, df.columns.tolist())

        # 4. 批量插入数据
        batch_insert_data(conn, df)

        # 5. 关闭连接
        conn.close()
        print("✅ 所有操作完成，数据库连接已关闭")
    except Exception as e:
        print(f"❌ 程序执行失败：{str(e)}")
        import traceback
        traceback.print_exc()

# 执行主程序
if __name__ == "__main__":
    main()