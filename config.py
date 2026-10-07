# 配置文件 - 存放所有配置项
CRM_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjoiMSIsInVzZXJfa2V5IjoiODFmYWZhMWYtN2FkZi00MWJkLTlkNDQtZDAzYjQ3ODZjOTUyIiwic291cmNldHlwZSI6MSwidXNlcm5hbWUiOiJhZG1pbiJ9.2Vtrx3eXv-9AWAieoUppFxhYW6vjnmXpn9DOa6d9_F3lCJMAfoIGuGSfESVZmOOgXREi1-B0qSakxrs4Y9vFgg"
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