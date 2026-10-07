--【CRM系统】【用户管理-权限管理】
-- 1. `sys_user` 用户表
select * from sys_user
select * from sys_user where user_name='100001'
select count(*) from sys_user
-- 2. `sys_role` 角色表
select * from sys_role
select count(*) from sys_role
-- 3. `sys_user_role` 用户角色关联表（一个用户多个角色
select * from sys_user_role
-- 部门表
select * from sys_dept
-- 岗位表
select * from sys_post
-- 用户岗位关联表
select * from sys_user_post
--【字典管理】字典类型表
select * from sys_dict_type where dict_name='招聘会企业面试岗位'
select count(*) from sys_dict_type
--【字典管理】字典数据表
select * from sys_dict_data where dict_type=(select dict_type from sys_dict_type where dict_name='招聘会企业面试岗位')
-- crmdb_test
--【用户管理 角色管理】
select * from sys_user where user_name='100001'
select * from sys_role
select count(*) from sys_user
select count(*) from sys_role
-- 菜单表
select * from sys_menu WHERE menu_name='工作台'
select count(*) from sys_menu where parent_id=0
-- visible 0 显示菜单11 隐藏菜单,菜单类型menu_type（M目录 C菜单 F按钮） IS_FRAME 字段是否为外链（0是 1否）
select * from sys_menu where parent_id='0'  AND  menu_type='M' AND visible='0' AND IS_FRAME='1' order by order_num ASC
select count(*) from sys_menu where parent_id='0'  AND  menu_type='M' AND visible='0' AND IS_FRAME='1'
--如果只需要总合计（不分行展示每个一级菜单）
SELECT COUNT(menu_id) AS 所有指定一级菜单下直接子菜单总数
FROM sys_menu
WHERE parent_id IN (175,176,177,178); -- 填入一级菜单ID集合

--【定时任务】
select * from sys_job_group
--------------------------------------------------------------------
--------------------------------------------------------------------
-- 【银企直联需求】
-- 收款公司表
select * from financial_collecting_company order by create_time desc
select * from financial_collecting_company
select * from t_bank_merchant
-- 银行流水表（十分钟更新一次流水表，定时任务执行？）
select * from t_bank_transaction order by create_time desc
select count(*) from t_bank_transaction
-- 银行流水和收据匹配表（银行流水匹配）
select * from t_transaction_receipt
select count(*) from t_transaction_receipt
-- 日记帐（id为流水表对应的id）
select * from t_journal
-- 付款单
select * from t_eas_payment
-- 收款单
select * from t_eas_receiving


-- 【排课管理相关】
--kclx 课程类型字段
select * from pkb order by createdate desc



-- 【内容库相关】
select * from t_cloudstorage_file_path  order by  create_time desc
select * from t_cloudstorage_file_path  where storage_id='2092779173711241216'

select * from t_cloudstorage_file  where file_id='2092779173711241216'
select * from t_cloudstorage_file  where file_name='教学备课库'
select * from t_cloudstorage_file where parent_id='2092078830673223680'

select * from t_cloudstorage_file  order by  create_time desc

select * from lxjl where xymc='2085623028102004736'
select * from xymc


-- 【楚凤相关】
-- 活动管理
select * from chufeng_activity order by create_time desc
select * from chufeng_activity_course where activity_id='2096768261850185728'       order by create_time desc
-- account CRM报名学员表 17871678454  18792169903
select * from account WHERE name = '18792169903'
-- t_student_info CRM意向学员表
select * from t_student_info where phones='{18792169903}'
-- chufeng_user 楚凤用户表
select * from chufeng_user where mobile='18792169903'
-- 报名表
select * from chufeng_activity_apply order by create_time desc
select * from chufeng_activity_apply where user_id='2097153772603342848'
-- 签到表
select * from chufeng_activity_attendance order by attend_time desc
select * from chufeng_activity_attendance where create_by='2097153772603342848'


select * from chufeng_activity_category
-- 【人员应聘和模拟面试】 使用新网校数据库learningtrajectory_sync
select * from t_exam_stu_info where exam_id in (select  id from t_recruitment_management)  and create_time>='2026.07.14 00:00:00' ORDER BY create_time desc; --查询模拟面试记录，如果需要就删除数据
select  * from t_recruitment_management where phone='18792160016' ORDER BY create_time desc--人员应聘管理表

-- 就业企业管理 is_deleted=1代表已经逻辑删除
-- 人员应聘管理
select * from t_recruitment_management
select * from enterprise_management where name='湖北十堰人力资源有限公司'
select count(*) from enterprise_management where is_deleted='0'
-- 企业招聘岗位 enterprise_id企业id
select * from enterprise_management_job_info WHERE enterprise_id='2070783204706791424'
-- 岗位来源 字典表（招聘会企业面试岗位）
select * from sys_dict_data WHERE dict_type='zph_interview_post'
select count(*) from sys_dict_data WHERE dict_type='zph_interview_post'
select * from sys_dict_data WHERE dict_type='zph_interview_post' and dict_label='会计'
-- 岗位行业管理
select * from sys_industry
select count(*) from sys_industry
-- 能力点管理 status='0'草稿 1上架 2下架
select * from t_ability_config where name='业绩管理'
select count(*)  from t_ability_config where status='0'
select * from t_ability_config where name='业绩管理'

--能力点层级关系
select count(*) from t_competency_points where parent_id='0'
-- 人员应聘管理 name phone record_id面试报告id
select *  from "t_recruitment_management" where name='杨萍'
select *  from "t_recruitment_management" where phone='18792169903'
select record_id  from "t_recruitment_management" where phone='18792169903'
select *　FROM job_intention_apply

select * from "t_exam_stu_info"
-- 综合筛选
select interview_video_url,*from "t_exam_stu_info"  where  id in (select record_id from "t_recruitment_management" where "record_id"  is not null)  ORDER BY  "begin_time"  desc

select *from t_exam_stu_detail  where exam_stu_info_id= '2071524480526684160'
-- 建班管理建班开启时间管理表
select * from t_class_schedule_time

-- 楚凤活动
-- 活动类型
select * from chufeng_activity_category
-- screen_shot位置异常自拍签到图 sign_screen_shot签到截图
select screen_shot from chufeng_activity_attendance where screen_shot is not null

-- SQL 里字符串不能用双引号，标准 SQL/MySQL/Oracle 等主流数据库，字符串值必须用单引号 '
-- 校区表 总部校区a10201907435744MzUtW 后台状态（htzt）已关闭 已开业 筹建中
select * from xq where id='a10201907435744MzUtW'
select count(*) from xq where htzt='已关闭'
select count(*) from xq where htzt='筹建中'

select name from xq order BY createdate DESC
select count(*) from xq
-- 校区-归属公司/协议主体-签章（实时）8小时同步一次
-- seal_url ：oss签章图片地址，定时从E签宝同步，基于归属公司更新至校区属性
select id,name,gsgs,seal_id,seal_url from xq where is_deleted = '0'
-- 校区-账套映射（实时）账套-公司
select campus_id,eas_org_id,eas_dept_org_id from financial_campus
select count(*)  from financial_campus

-- 账套-公司 ZWH013
select org_number,org_name from eas_org
select count(*)  from eas_org
select  * from eas_org where org_number='ZWH013'

--校区账套映射修改记录表 修改日志记录
select * from financial_campus_change_log


-- 【订单管理】
-- dd 订单表
-- ddcp 订单明细表
-- skd 收款单
-- tkd 退款单
-- dd订单表 订单id 订单编号name 订单类型lx
-- eas_org_id账套编码   eas_dept_org_id账套部门id
select * from dd where name='20260617111131597520'
select count(*) from account
select eas_org_id,eas_dept_org_id from dd where id='2065254575763709952'
select * from dd where id='2066819934681591808'
-- ddcp 订单明细表
select * from ddcp where id='20260611115255610832'

-- xyxx 协议信息表
select * from xyxx where id='2065347414270988288'

-- skd 收款单
select * from skd limit 2
select * from skd order by  createdate desc limit 2
select * from skd  where id='2069227584404848640'


-- t_advance_account  --预收款账户表
-- t_advance_bill --预收款单表
-- t_advance_deposit --预收款单拆分明细表
-- t_advance_deposit_flow  --预收款单交易流水表
select *  from t_advance_account where phone='18792169903'
select *  from t_advance_bill limit 2


-- tkd　　　退款单表
-- tkd_approval　 退款单审批表
-- tkd_detail　 　退款单明细表
-- tkd_reject_log 退款单驳回记录日志
-- tkd 退款单 ddbh订单编号 实际对应的订单的id
select eas_org_id,eas_dept_org_id  from tkd where ddbh='2067082686247522304'
-- 账套ID eas_org_id
select eas_org_id,eas_dept_org_id from tkd_detail where tkd_id='2068867245335121920'


-- CRM后台课程表
select * from kcb where id = 'ee7aeb596fae486ab523042f6ce598de'
select count(*) from kcb
-- 产品表 state状态字段 启用（已上架） 禁用（已下架） 草稿
-- 产品ID 1b1761dc533d499f8f248ad203ca8eaa
select * from cpxx order BY createdate desc
select * from cpxx where name='chenfa产品004'
-- 课程表
select level_sort from kmxx where name='chenfa课程006'

UPDATE kmxx SET sfqy  = true WHERE name = 'chenfa课程006';

UPDATE kmxx SET sfqy  = true WHERE name = 'chenfa课程006';

select state from cpxx where name='chenfa产品004'
select state from cpxx where name='chenfa产品002'
UPDATE cpxx SET state = '草稿' WHERE name = 'chenfa产品002';

select status from kmxx where name='chenfa课程004'




-- 用户员工表
select * from sys_user 
select count(*) from sys_user 
-- t_student_info 意向学员表(id name phone)
select * from t_student_info WHERE phones = "18792169903"
select count(*) from t_student_info 
-- account 报名学员表
select * from account WHERE phones = "18792169903"
select count(*) from account WHERE phones = "18792169903"

-- 排课管理  pkb 排课表
select * from pkb
-- kcb 课程表
-- lskqb 老师考勤信息表
-- kmxx 课程信息表（课程交付）
-- cpxx 产品信息表
-- xq 校区信息表
-- szxx 师资信息表
select * from szxx 
select count(*) from szxx where enable='1'
-- sys_user 用户表（员工）

