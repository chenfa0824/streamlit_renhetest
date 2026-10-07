import pandas as pd
import pymysql
from sqlalchemy import create_engine, text, types
from datetime import datetime
import numpy as np

# ============================================================
# 1. 数据库配置
# ============================================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'renhetest',
    'charset': 'utf8mb4'
}

# ============================================================
# 2. 定义表结构
# ============================================================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS employee_salary (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    区域 VARCHAR(50) COMMENT '区域',
    校区 VARCHAR(100) COMMENT '校区',
    姓名 VARCHAR(50) COMMENT '姓名',
    工号 VARCHAR(50) COMMENT '工号',
    手机号码 VARCHAR(20) COMMENT '手机号码',
    岗位 VARCHAR(50) COMMENT '岗位',
    入职时间 DATE COMMENT '入职时间',
    转正时间 DATE COMMENT '转正时间',
    离职时间 DATE COMMENT '离职时间',
    出勤天数 DECIMAL(10,2) DEFAULT 0 COMMENT '出勤天数',
    计薪天数 DECIMAL(10,2) DEFAULT 0 COMMENT '计薪天数',
    在岗天数 DECIMAL(10,2) DEFAULT 0 COMMENT '在岗天数',
    迟到次数 DECIMAL(10,2) DEFAULT 0 COMMENT '迟到次数',
    请假天数 DECIMAL(10,2) DEFAULT 0 COMMENT '请假天数',
    调休天数 DECIMAL(10,2) DEFAULT 0 COMMENT '调休天数',
    缺勤天数 DECIMAL(10,2) DEFAULT 0 COMMENT '缺勤天数',
    最低工资标准 DECIMAL(10,2) DEFAULT 0 COMMENT '最低工资标准',
    前三个月是否在公司缴纳社保公积金 VARCHAR(10) COMMENT '前三个月是否在公司缴纳社保公积金',
    综合工资计算方案 VARCHAR(50) COMMENT '综合工资计算方案',
    综合工资标准 DECIMAL(10,2) DEFAULT 0 COMMENT '综合工资标准',
    综合工资 DECIMAL(10,2) DEFAULT 0 COMMENT '综合工资',
    基本工资 DECIMAL(10,2) DEFAULT 0 COMMENT '基本工资',
    岗位津贴 DECIMAL(10,2) DEFAULT 0 COMMENT '岗位津贴',
    加班津贴 DECIMAL(10,2) DEFAULT 0 COMMENT '加班津贴',
    保密津贴 DECIMAL(10,2) DEFAULT 0 COMMENT '保密津贴',
    差旅误餐补贴 DECIMAL(10,2) DEFAULT 0 COMMENT '差旅误餐补贴',
    通讯补贴 DECIMAL(10,2) DEFAULT 0 COMMENT '通讯补贴',
    社保补贴 DECIMAL(10,2) DEFAULT 0 COMMENT '社保补贴',
    公积金补贴 DECIMAL(10,2) DEFAULT 0 COMMENT '公积金补贴',
    绩效岗位系数 DECIMAL(10,4) DEFAULT 0 COMMENT '绩效岗位系数',
    绩效工资 DECIMAL(10,2) DEFAULT 0 COMMENT '绩效工资',
    病假福利假工资 DECIMAL(10,2) DEFAULT 0 COMMENT '病假/福利假工资',
    工龄工资 DECIMAL(10,2) DEFAULT 0 COMMENT '工龄工资',
    奖金 DECIMAL(10,2) DEFAULT 0 COMMENT '奖金',
    兼职岗位固定工资 DECIMAL(10,2) DEFAULT 0 COMMENT '兼职岗位固定工资',
    固定工资合计 DECIMAL(10,2) DEFAULT 0 COMMENT '固定工资合计',
    本校区个人计提业绩 DECIMAL(10,2) DEFAULT 0 COMMENT '本校区个人计提业绩',
    非本校区个人计提业绩 DECIMAL(10,2) DEFAULT 0 COMMENT '非本校区个人计提业绩',
    本校区个人课消收入 DECIMAL(10,2) DEFAULT 0 COMMENT '本校区个人课消收入',
    非本校区个人课消收入 DECIMAL(10,2) DEFAULT 0 COMMENT '非本校区个人课消收入',
    业绩提成点 DECIMAL(10,4) DEFAULT 0 COMMENT '业绩提成点',
    课消提成点 DECIMAL(10,4) DEFAULT 0 COMMENT '课消提成点',
    个人业绩课消提成 DECIMAL(10,2) DEFAULT 0 COMMENT '个人业绩课消提成',
    个人网校订单业绩 DECIMAL(10,2) DEFAULT 0 COMMENT '个人网校订单业绩',
    个人网校订单业绩奖励提成 DECIMAL(10,2) DEFAULT 0 COMMENT '个人网校订单业绩奖励提成',
    他人提供开发客户销售提成分单 DECIMAL(10,2) DEFAULT 0 COMMENT '他人提供开发客户销售提成分单',
    个人业绩提成项合计 DECIMAL(10,2) DEFAULT 0 COMMENT '个人业绩提成项合计',
    校区完成率 VARCHAR(10) COMMENT '校区完成率',
    校区计提业绩 DECIMAL(10,2) DEFAULT 0 COMMENT '校区计提业绩',
    校区课消收入 DECIMAL(10,2) DEFAULT 0 COMMENT '校区课消收入',
    校长业绩提成点 DECIMAL(10,4) DEFAULT 0 COMMENT '校长业绩提成点',
    校长课消提成点 DECIMAL(10,4) DEFAULT 0 COMMENT '校长课消提成点',
    校区提成折扣率 DECIMAL(10,2) DEFAULT 0 COMMENT '校区提成折扣率',
    校区业绩课消提成 DECIMAL(10,2) DEFAULT 0 COMMENT '校区业绩课消提成',
    业绩提成合计 DECIMAL(10,2) DEFAULT 0 COMMENT '业绩提成合计',
    其他奖励补助 DECIMAL(10,2) DEFAULT 0 COMMENT '其他奖励补助',
    退费业绩 DECIMAL(10,2) DEFAULT 0 COMMENT '退费业绩',
    退费系数 DECIMAL(10,2) DEFAULT 0 COMMENT '退费系数',
    退费提成 DECIMAL(10,2) DEFAULT 0 COMMENT '退费提成',
    校区上限人头数 int DEFAULT 0 COMMENT '校区上限人头数',
    校区下限人头数 int DEFAULT 0 COMMENT '校区下限人头数',
    业绩上限 DECIMAL(10,2) DEFAULT 0 COMMENT '业绩上限',
    业绩下限 DECIMAL(10,2) DEFAULT 0 COMMENT '业绩下限',
    课消下限 DECIMAL(10,2) DEFAULT 0 COMMENT '课消下限',
    个人业绩课消未达限制要求扣减提成 DECIMAL(10,2) DEFAULT 0 COMMENT '个人业绩课消未达限制要求扣减提成',
    提成扣款合计 DECIMAL(10,2) DEFAULT 0 COMMENT '提成扣款合计',
    实际提成合计 DECIMAL(10,2) DEFAULT 0 COMMENT '实际提成合计',
    绩效等级 VARCHAR(10) COMMENT '绩效等级',
    绩效分数 DECIMAL(10,2) DEFAULT 0 COMMENT '绩效分数',
    绩效系数 DECIMAL(10,4) DEFAULT 0 COMMENT '绩效系数',
    兼职岗位绩效等级 VARCHAR(10) COMMENT '兼职岗位绩效等级',
    兼职岗位绩效分数 DECIMAL(10,2) DEFAULT 0 COMMENT '兼职岗位绩效分数',
    兼职岗位绩效系数 DECIMAL(10,4) DEFAULT 0 COMMENT '兼职岗位绩效系数',
    绩效扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '绩效扣款',
    兼职岗位绩效扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '兼职岗位绩效扣款',
    sop绩效扣款 DECIMAL(10,2) DEFAULT 0 COMMENT 'sop绩效扣款',
    绩效奖励 DECIMAL(10,2) DEFAULT 0 COMMENT '绩效奖励',
    兼职岗位绩效奖励 DECIMAL(10,2) DEFAULT 0 COMMENT '兼职岗位绩效奖励',
    保底工资 DECIMAL(10,2) DEFAULT 0 COMMENT '保底工资',
    保底补差 DECIMAL(10,2) DEFAULT 0 COMMENT '保底补差',
    实际保底补差 DECIMAL(10,2) DEFAULT 0 COMMENT '实际保底补差',
    保底补差审批结果 VARCHAR(20) COMMENT '保底补差审批结果',
    个人补差 DECIMAL(10,2) DEFAULT 0 COMMENT '个人补差',
    合并工资扣个税的已发奖励 DECIMAL(10,2) DEFAULT 0 COMMENT '合并工资扣个税的已发奖励',
    工资总额不含已发奖励 DECIMAL(10,2) DEFAULT 0 COMMENT '工资总额（不含已发奖励）',
    工资总额 DECIMAL(10,2) DEFAULT 0 COMMENT '工资总额',
    保险扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '保险扣款',
    公积金扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '公积金扣款',
    其他代扣 DECIMAL(10,2) DEFAULT 0 COMMENT '其他代扣',
    迟到扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '迟到扣款',
    缺勤总扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '缺勤总扣款',
    全勤扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '全勤扣款',
    其他扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '其他扣款',
    扣款合计 DECIMAL(10,2) DEFAULT 0 COMMENT '扣款合计',
    应发工资不含已发奖励 DECIMAL(10,2) DEFAULT 0 COMMENT '应发工资（不含已发奖励）',
    应税工资 DECIMAL(10,2) DEFAULT 0 COMMENT '应税工资',
    应发工资 DECIMAL(10,2) DEFAULT 0 COMMENT '应发工资',
    累计专项扣除小计 DECIMAL(10,2) DEFAULT 0 COMMENT '累计专项扣除小计',
    本月个税扣款 DECIMAL(10,2) DEFAULT 0 COMMENT '本月个税扣款',
    实发工资 DECIMAL(10,2) DEFAULT 0 COMMENT '实发工资',
    财务取整实发工资 DECIMAL(10,2) DEFAULT 0 COMMENT '财务取整实发工资',
    统计月份 VARCHAR(10) COMMENT '统计月份',
    INDEX idx_姓名 (姓名),
    INDEX idx_工号 (工号),
    INDEX idx_统计月份 (统计月份)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工资比对数据表';
"""


# ============================================================
# 3. 数据清洗和转换函数
# ============================================================
def clean_value(val):
    """清理数据值"""
    if pd.isna(val) or val == '':
        return None
    # 处理百分比字符串
    if isinstance(val, str) and val.endswith('%'):
        try:
            return float(val.replace('%', '')) / 100
        except:
            return val
    return val


def to_decimal(val):
    """转换为Decimal格式，保留两位小数"""
    if pd.isna(val) or val == '' or val is None:
        return 0.00
    try:
        # 如果是字符串，去除可能存在的逗号和空格
        if isinstance(val, str):
            val = val.replace(',', '').replace(' ', '').replace('%', '')
        return round(float(val), 2)
    except (ValueError, TypeError):
        return 0.00


def to_decimal_4(val):
    """转换为Decimal格式，保留四位小数（用于系数）"""
    if pd.isna(val) or val == '' or val is None:
        return 0.0000
    try:
        if isinstance(val, str):
            val = val.replace(',', '').replace(' ', '').replace('%', '')
        return round(float(val), 4)
    except (ValueError, TypeError):
        return 0.0000


def parse_date(val):
    """解析日期"""
    if pd.isna(val) or val == '' or val is None:
        return None
    try:
        if isinstance(val, str):
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']:
                try:
                    return datetime.strptime(val, fmt).date()
                except:
                    continue
        return val
    except:
        return None


# ============================================================
# 4. 插入数据函数
# ============================================================
def insert_salary_data(df):
    """插入工资数据到数据库"""

    # 创建连接
    conn_str = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    engine = create_engine(conn_str)

    with engine.connect() as conn:
        # 创建表
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()
        print("✅ 表创建成功")

        # 清空表（可选）
        conn.execute(text("TRUNCATE TABLE employee_salary"))
        conn.commit()

        # 准备插入数据
        insert_sql = """
        INSERT INTO employee_salary (
            区域, 校区, 姓名, 工号, 手机号码, 岗位, 入职时间, 转正时间, 离职时间,
            出勤天数, 计薪天数, 在岗天数, 迟到次数, 请假天数, 调休天数, 缺勤天数,
            最低工资标准, 前三个月是否在公司缴纳社保公积金, 综合工资计算方案,
            综合工资标准, 综合工资, 基本工资, 岗位津贴, 加班津贴, 保密津贴,
            差旅误餐补贴, 通讯补贴, 社保补贴, 公积金补贴, 绩效岗位系数,
            绩效工资, 病假福利假工资, 工龄工资, 奖金, 兼职岗位固定工资,
            固定工资合计, 本校区个人计提业绩, 非本校区个人计提业绩,
            本校区个人课消收入, 非本校区个人课消收入, 业绩提成点, 课消提成点,
            个人业绩课消提成, 个人网校订单业绩, 个人网校订单业绩奖励提成,
            他人提供开发客户销售提成分单, 个人业绩提成项合计, 校区完成率,
            校区计提业绩, 校区课消收入, 校长业绩提成点, 校长课消提成点,
            校区提成折扣率, 校区业绩课消提成, 业绩提成合计, 其他奖励补助,
            退费业绩, 退费系数, 退费提成, 校区上限人头数, 校区下限人头数,
            业绩上限, 业绩下限, 课消下限, 个人业绩课消未达限制要求扣减提成,
            提成扣款合计, 实际提成合计, 绩效等级, 绩效分数, 绩效系数,
            兼职岗位绩效等级, 兼职岗位绩效分数, 兼职岗位绩效系数,
            绩效扣款, 兼职岗位绩效扣款, sop绩效扣款, 绩效奖励,
            兼职岗位绩效奖励, 保底工资, 保底补差, 实际保底补差,
            保底补差审批结果, 个人补差, 合并工资扣个税的已发奖励,
            工资总额不含已发奖励, 工资总额, 保险扣款, 公积金扣款,
            其他代扣, 迟到扣款, 缺勤总扣款, 全勤扣款, 其他扣款,
            扣款合计, 应发工资不含已发奖励, 应税工资, 应发工资,
            累计专项扣除小计, 本月个税扣款, 实发工资, 财务取整实发工资,
            统计月份
        ) VALUES (
            :区域, :校区, :姓名, :工号, :手机号码, :岗位, :入职时间, :转正时间, :离职时间,
            :出勤天数, :计薪天数, :在岗天数, :迟到次数, :请假天数, :调休天数, :缺勤天数,
            :最低工资标准, :前三个月是否在公司缴纳社保公积金, :综合工资计算方案,
            :综合工资标准, :综合工资, :基本工资, :岗位津贴, :加班津贴, :保密津贴,
            :差旅误餐补贴, :通讯补贴, :社保补贴, :公积金补贴, :绩效岗位系数,
            :绩效工资, :病假福利假工资, :工龄工资, :奖金, :兼职岗位固定工资,
            :固定工资合计, :本校区个人计提业绩, :非本校区个人计提业绩,
            :本校区个人课消收入, :非本校区个人课消收入, :业绩提成点, :课消提成点,
            :个人业绩课消提成, :个人网校订单业绩, :个人网校订单业绩奖励提成,
            :他人提供开发客户销售提成分单, :个人业绩提成项合计, :校区完成率,
            :校区计提业绩, :校区课消收入, :校长业绩提成点, :校长课消提成点,
            :校区提成折扣率, :校区业绩课消提成, :业绩提成合计, :其他奖励补助,
            :退费业绩, :退费系数, :退费提成, :校区上限人头数, :校区下限人头数,
            :业绩上限, :业绩下限, :课消下限, :个人业绩课消未达限制要求扣减提成,
            :提成扣款合计, :实际提成合计, :绩效等级, :绩效分数, :绩效系数,
            :兼职岗位绩效等级, :兼职岗位绩效分数, :兼职岗位绩效系数,
            :绩效扣款, :兼职岗位绩效扣款, :sop绩效扣款, :绩效奖励,
            :兼职岗位绩效奖励, :保底工资, :保底补差, :实际保底补差,
            :保底补差审批结果, :个人补差, :合并工资扣个税的已发奖励,
            :工资总额不含已发奖励, :工资总额, :保险扣款, :公积金扣款,
            :其他代扣, :迟到扣款, :缺勤总扣款, :全勤扣款, :其他扣款,
            :扣款合计, :应发工资不含已发奖励, :应税工资, :应发工资,
            :累计专项扣除小计, :本月个税扣款, :实发工资, :财务取整实发工资,
            :统计月份
        )
        """

        # 列名映射（Excel列名 -> 数据库字段名）
        column_mapping = {
            '区域': '区域',
            '校区': '校区',
            '姓名': '姓名',
            '工号': '工号',
            '手机号码': '手机号码',
            '岗位': '岗位',
            '入职时间': '入职时间',
            '转正时间': '转正时间',
            '离职时间': '离职时间',
            '出勤天数': '出勤天数',
            '计薪天数': '计薪天数',
            '在岗天数': '在岗天数',
            '迟到次数': '迟到次数',
            '请假天数': '请假天数',
            '调休天数': '调休天数',
            '缺勤天数': '缺勤天数',
            '最低工资标准': '最低工资标准',
            '前三个月是否在公司缴纳社保公积金': '前三个月是否在公司缴纳社保公积金',
            '综合工资计算方案': '综合工资计算方案',
            '综合工资标准': '综合工资标准',
            '综合工资': '综合工资',
            '基本工资': '基本工资',
            '岗位津贴': '岗位津贴',
            '加班津贴': '加班津贴',
            '保密津贴': '保密津贴',
            '差旅误餐补贴': '差旅误餐补贴',
            '通讯补贴': '通讯补贴',
            '社保补贴': '社保补贴',
            '公积金补贴': '公积金补贴',
            '绩效岗位系数': '绩效岗位系数',
            '绩效工资': '绩效工资',
            '病假/福利假工资': '病假福利假工资',
            '工龄工资': '工龄工资',
            '奖金': '奖金',
            '兼职岗位固定工资': '兼职岗位固定工资',
            '固定工资合计': '固定工资合计',
            '本校区个人计提业绩': '本校区个人计提业绩',
            '非本校区个人计提业绩': '非本校区个人计提业绩',
            '本校区个人课消收入': '本校区个人课消收入',
            '非本校区个人课消收入': '非本校区个人课消收入',
            '业绩提成点': '业绩提成点',
            '课消提成点': '课消提成点',
            '个人业绩课消提成': '个人业绩课消提成',
            '个人网校订单业绩': '个人网校订单业绩',
            '个人网校订单业绩奖励提成': '个人网校订单业绩奖励提成',
            '他人提供开发客户销售提成分单': '他人提供开发客户销售提成分单',
            '个人业绩提成项合计': '个人业绩提成项合计',
            '校区完成率': '校区完成率',
            '校区计提业绩': '校区计提业绩',
            '校区课消收入': '校区课消收入',
            '校长业绩提成点': '校长业绩提成点',
            '校长课消提成点': '校长课消提成点',
            '校区提成折扣率': '校区提成折扣率',
            '校区业绩课消提成': '校区业绩课消提成',
            '业绩提成合计': '业绩提成合计',
            '其他奖励补助': '其他奖励补助',
            '退费业绩': '退费业绩',
            '退费系数': '退费系数',
            '退费提成': '退费提成',
            '校区上限人头数': '校区上限人头数',
            '校区下限人头数': '校区下限人头数',
            '业绩上限': '业绩上限',
            '业绩下限': '业绩下限',
            '课消下限': '课消下限',
            '个人业绩课消未达限制要求扣减提成': '个人业绩课消未达限制要求扣减提成',
            '提成扣款合计': '提成扣款合计',
            '实际提成合计': '实际提成合计',
            '绩效等级': '绩效等级',
            '绩效分数': '绩效分数',
            '绩效系数': '绩效系数',
            '兼职岗位绩效等级': '兼职岗位绩效等级',
            '兼职岗位绩效分数': '兼职岗位绩效分数',
            '兼职岗位绩效系数': '兼职岗位绩效系数',
            '绩效扣款': '绩效扣款',
            '兼职岗位绩效扣款': '兼职岗位绩效扣款',
            'sop绩效扣款': 'sop绩效扣款',
            '绩效奖励': '绩效奖励',
            '兼职岗位绩效奖励': '兼职岗位绩效奖励',
            '保底工资': '保底工资',
            '保底补差': '保底补差',
            '实际保底补差': '实际保底补差',
            '保底补差审批结果': '保底补差审批结果',
            '个人补差': '个人补差',
            '合并工资扣个税的已发奖励': '合并工资扣个税的已发奖励',
            '工资总额（不含已发奖励）': '工资总额不含已发奖励',
            '工资总额': '工资总额',
            '保险扣款': '保险扣款',
            '公积金扣款': '公积金扣款',
            '其他代扣': '其他代扣',
            '迟到扣款': '迟到扣款',
            '缺勤总扣款': '缺勤总扣款',
            '全勤扣款': '全勤扣款',
            '其他扣款': '其他扣款',
            '扣款合计': '扣款合计',
            '应发工资（不含已发奖励）': '应发工资不含已发奖励',
            '应税工资': '应税工资',
            '应发工资': '应发工资',
            '累计专项扣除小计': '累计专项扣除小计',
            '本月个税扣款': '本月个税扣款',
            '实发工资': '实发工资',
            '财务取整实发工资': '财务取整实发工资',
            '统计月份': '统计月份'
        }

        # 数值字段列表（需要保留两位小数的字段）
        decimal_fields = [
            '出勤天数', '计薪天数', '在岗天数', '迟到次数', '请假天数',
            '调休天数', '缺勤天数', '最低工资标准', '综合工资标准', '综合工资',
            '基本工资', '岗位津贴', '加班津贴', '保密津贴', '差旅误餐补贴',
            '通讯补贴', '社保补贴', '公积金补贴', '绩效工资', '病假福利假工资',
            '工龄工资', '奖金', '兼职岗位固定工资', '固定工资合计',
            '本校区个人计提业绩', '非本校区个人计提业绩', '本校区个人课消收入',
            '非本校区个人课消收入', '个人业绩课消提成', '个人网校订单业绩',
            '个人网校订单业绩奖励提成', '他人提供开发客户销售提成分单',
            '个人业绩提成项合计', '校区计提业绩', '校区课消收入',
            '校区业绩课消提成', '业绩提成合计', '其他奖励补助',
            '退费业绩', '退费提成', '校区上限人头数', '校区下限人头数',
            '业绩上限', '业绩下限', '课消下限',
            '个人业绩课消未达限制要求扣减提成', '提成扣款合计', '实际提成合计',
            '绩效分数', '绩效扣款', '兼职岗位绩效扣款', 'sop绩效扣款',
            '绩效奖励', '兼职岗位绩效奖励', '保底工资', '保底补差',
            '实际保底补差', '个人补差', '合并工资扣个税的已发奖励',
            '工资总额不含已发奖励', '工资总额', '保险扣款', '公积金扣款',
            '其他代扣', '迟到扣款', '缺勤总扣款', '全勤扣款', '其他扣款',
            '扣款合计', '应发工资不含已发奖励', '应税工资', '应发工资',
            '累计专项扣除小计', '本月个税扣款', '实发工资', '财务取整实发工资'
        ]

        # 系数字段（保留四位小数）
        decimal_4_fields = [
            '绩效岗位系数', '业绩提成点', '课消提成点', '校长业绩提成点',
            '校长课消提成点', '绩效系数', '兼职岗位绩效系数', '校区提成折扣率'
        ]

        # 日期字段
        date_fields = ['入职时间', '转正时间', '离职时间']

        # 统计数据
        total_rows = len(df)
        success_count = 0
        error_count = 0

        print(f"📊 开始插入 {total_rows} 条数据...")

        # 逐行插入
        for idx, row in df.iterrows():
            try:
                data = {}

                # 处理每个字段
                for excel_col, db_col in column_mapping.items():
                    if excel_col in row.index:
                        val = row[excel_col]

                        # 处理日期字段
                        if excel_col in date_fields:
                            data[db_col] = parse_date(val)
                        # 处理数值字段（两位小数）
                        elif excel_col in decimal_fields:
                            data[db_col] = to_decimal(val)
                        # 处理系数字段（四位小数）
                        elif excel_col in decimal_4_fields:
                            data[db_col] = to_decimal_4(val)
                        # 处理其他字段
                        else:
                            data[db_col] = clean_value(val)
                    else:
                        data[db_col] = None

                # 执行插入
                conn.execute(text(insert_sql), data)
                success_count += 1

                # 每100条打印进度
                if success_count % 100 == 0:
                    print(f"  已插入 {success_count} 条记录...")

            except Exception as e:
                error_count += 1
                if error_count <= 10:  # 只打印前10条错误
                    print(f"❌ 第 {idx + 1} 行插入失败: {e}")
                continue

        # 提交事务
        conn.commit()
        print(f"\n✅ 数据插入完成！成功: {success_count} 条，失败: {error_count} 条")


# ============================================================
# 5. 主程序
# ============================================================
if __name__ == "__main__":
    try:
        # 读取Excel数据
        excel_path = "1_处理后.xlsx"
        print(f"📂 正在读取文件: {excel_path}")

        # 读取Excel，跳过前2行元数据
        df = pd.read_excel(excel_path, header=0)

        print(f"📊 共读取 {len(df)} 行, {len(df.columns)} 列")
        print(f"📋 列名: {df.columns.tolist()}")

        # 显示前几行预览
        print("\n📋 数据预览:")
        print(df.head(3))

        # 插入数据
        insert_salary_data(df)

        print("\n🎉 数据导入完成！")

    except FileNotFoundError:
        print(f"❌ 文件未找到: {excel_path}")
        print("请确保文件路径正确")
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback

        traceback.print_exc()