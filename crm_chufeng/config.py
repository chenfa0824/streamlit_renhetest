# 配置文件 - 存放所有配置项
CRM_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoiMDA1MjAyMjEzMEExRUYzbWIweHUiLCJ1c2VyX2tleSI6IjYyOTdmOWM1LTMxNWQtNDFmMS1iYWVjLTYzMDBhNzM5YTIyOSIsInNvdXJjZXR5cGUiOjEsInVzZXJuYW1lIjoiMTExMzU4In0.u5gMgy1no5jMHrxCgL9pq3wuMbeBFJ2F53r7zsL42GIwnjdDSD1tSvvQIwAXZ2esQz1x7WYZSSb-oqOW8rKNJQ"
HRM_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoiMSIsInVzZXJfa2V5IjoiNDExZjA3NGEtMjAwNC00YWNmLTg0MGItOTA4YmY0YTE3MmQ3Iiwic291cmNldHlwZSI6MSwidXNlcm5hbWUiOiJhZG1pbiJ9.WNgwUircvACryrP6iPKBQazar0wrCmp5c1jFk4-iRkl_aG-zbh715WR8WASA3klx-TuxHY8HEsH-O4rXwtHkwA"

# 数据库连接信息
DB_CONFIG = {
    "host": "pgm-uf6jv8kq7xfyu4fako.pg.rds.aliyuncs.com",
    "port": 5432,
    "database": "crmdb_test",
    "user": "renhe_test",
    "password": "B72TjV4xTU5wQpVK"
}
# 默认Schema
DEFAULT_SCHEMA = "cust_u_rhkj"

# CRM系统相关API接口地址
chufeng_upsertActivity = "https://centertest.rhkj.com/prod-api/finance/chufeng/activity/upsertActivity"

# HRM系统相关API接口地址