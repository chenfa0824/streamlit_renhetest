# db_utils.py
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    "host": "pgm-uf6jv8kq7xfyu4fako.pg.rds.aliyuncs.com",
    "port": 5432,
    "database": "crmdb_test",
    "user": "renhe_test",
    "password": "B72TjV4xTU5wQpVK"
}

DEFAULT_SCHEMA = "cust_u_rhkj"


class DatabaseManager:
    """数据库管理工具类"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置字典，如果不提供则使用默认配置
        """
        self.config = config or DB_CONFIG.copy()
        self._connection = None
        self._cursor = None

    def get_connection(self):
        """
        获取数据库连接

        Returns:
            psycopg2.connection: 数据库连接对象
        """
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
        return self._connection

    def get_cursor(self, cursor_factory=None):
        """
        获取数据库游标

        Args:
            cursor_factory: 游标工厂类，默认为None（使用普通游标）

        Returns:
            psycopg2.cursor: 数据库游标对象
        """
        conn = self.get_connection()
        if cursor_factory:
            self._cursor = conn.cursor(cursor_factory=cursor_factory)
        else:
            self._cursor = conn.cursor()
        return self._cursor

    def close(self):
        """关闭数据库连接"""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """上下文管理器入口"""
        self.get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def execute_query(self, query: str, params: tuple = None, fetch_all: bool = True):
        """
        执行查询并返回结果

        Args:
            query: SQL查询语句
            params: 参数元组
            fetch_all: 是否返回所有结果，False则返回单条

        Returns:
            查询结果列表或单条结果
        """
        try:
            cursor = self.get_cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params or ())

            if fetch_all:
                return cursor.fetchall()
            else:
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            raise
        finally:
            # 注意：不要在这里关闭cursor，因为可能还会使用
            pass

    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新操作（INSERT, UPDATE, DELETE）

        Args:
            query: SQL语句
            params: 参数元组

        Returns:
            int: 影响的行数
        """
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            self._connection.rollback()
            logger.error(f"执行更新失败: {str(e)}")
            raise
        finally:
            pass

    def execute_updates(self, queries: List[Tuple[str, tuple]]) -> List[int]:
        """
        批量执行更新操作

        Args:
            queries: (SQL语句, 参数元组) 的列表

        Returns:
            List[int]: 每条语句影响的行数列表
        """
        results = []
        try:
            cursor = self.get_cursor()
            for query, params in queries:
                cursor.execute(query, params or ())
                results.append(cursor.rowcount)
            self._connection.commit()
            return results
        except Exception as e:
            self._connection.rollback()
            logger.error(f"批量执行更新失败: {str(e)}")
            raise
        finally:
            pass

    def get_schemas(self) -> List[str]:
        """
        获取所有Schema

        Returns:
            List[str]: Schema名称列表
        """
        query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
            ORDER BY schema_name
        """
        results = self.execute_query(query)
        return [row['schema_name'] for row in results]

    def get_tables(self, schema: str) -> List[str]:
        """
        获取指定Schema下的所有表

        Args:
            schema: Schema名称

        Returns:
            List[str]: 表名列表
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        results = self.execute_query(query, (schema,))
        return [row['table_name'] for row in results]

    def get_activity_categories(self, schema: str = None) -> List[Dict[str, Any]]:
        """
        获取活动分类数据

        Args:
            schema: Schema名称，默认使用DEFAULT_SCHEMA

        Returns:
            List[Dict]: 活动分类列表，包含 activity_category_id 和 second_level
        """
        schema = schema or DEFAULT_SCHEMA
        query = f"""
            SELECT activity_category_id, second_level 
            FROM {schema}.chufeng_activity_category 
            WHERE second_level IS NOT NULL 
            AND second_level != ''
            ORDER BY second_level
        """
        return self.execute_query(query)

    def delete_activity_apply(self, activity_id: str, schema: str = None) -> int:
        """
        删除活动报名记录

        Args:
            activity_id: 活动ID
            schema: Schema名称

        Returns:
            int: 删除的记录数
        """
        schema = schema or DEFAULT_SCHEMA
        query = f"DELETE FROM {schema}.chufeng_activity_apply WHERE activity_id = %s"
        return self.execute_update(query, (activity_id,))

    def delete_activity_sign(self, activity_id: str, schema: str = None) -> int:
        """
        删除活动签到记录

        Args:
            activity_id: 活动ID
            schema: Schema名称

        Returns:
            int: 删除的记录数
        """
        schema = schema or DEFAULT_SCHEMA
        query = f"DELETE FROM {schema}.chufeng_activity_sign WHERE activity_id = %s"
        return self.execute_update(query, (activity_id,))

    def delete_student_data(self, mobile: str, schema: str = None) -> Dict[str, int]:
        """
        删除老学员数据

        Args:
            mobile: 手机号
            schema: Schema名称

        Returns:
            Dict[str, int]: 各表删除记录数
        """
        schema = schema or DEFAULT_SCHEMA
        phones_json = f'{{"{mobile}"}}'

        queries = [
            (f"DELETE FROM {schema}.account WHERE dianhua = %s", (mobile,)),
            (f"DELETE FROM {schema}.t_student_info WHERE phones = %s", (phones_json,)),
            (f"DELETE FROM {schema}.chufeng_user WHERE mobile = %s", (mobile,))
        ]

        results = self.execute_updates(queries)
        return {
            "account": results[0],
            "t_student_info": results[1],
            "chufeng_user": results[2]
        }

    def query_by_activity_id(self, table: str, activity_id: str, schema: str = None) -> List[Dict[str, Any]]:
        """
        根据活动ID查询表数据

        Args:
            table: 表名
            activity_id: 活动ID
            schema: Schema名称

        Returns:
            List[Dict]: 查询结果列表
        """
        schema = schema or DEFAULT_SCHEMA
        query = f"SELECT * FROM {schema}.{table} WHERE activity_id = %s"
        return self.execute_query(query, (activity_id,))


# 便捷函数
def get_db_manager(config: Optional[Dict] = None) -> DatabaseManager:
    """
    获取数据库管理器实例

    Args:
        config: 数据库配置

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    return DatabaseManager(config)


def test_connection(config: Optional[Dict] = None) -> bool:
    """
    测试数据库连接

    Args:
        config: 数据库配置

    Returns:
        bool: 连接是否成功
    """
    try:
        db = DatabaseManager(config)
        conn = db.get_connection()
        return conn is not None and not conn.closed
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False