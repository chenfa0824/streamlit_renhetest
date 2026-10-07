-- 建班管理建班开启时间管理表
select * from t_class_schedule_time


-- 人员应聘和模拟面试 使用新网校数据库
-- 就业企业管理 is_deleted=1代表已经逻辑删除
select * from enterprise_management where name='湖北十堰人力资源有限公司'
select count(*) from enterprise_management where is_deleted='0'
-- 企业招聘岗位
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




-- 菜单表
select *  from sys_menu WHERE menu_name='工作台'
select count(*)  from sys_menu where parent_id=0

-- visible 0 显示菜单11 隐藏菜单,菜单类型menu_type（M目录 C菜单 F按钮） IS_FRAME 字段是否为外链（0是 1否）
select * from sys_menu where parent_id='0'  AND  menu_type='M' AND visible='0' AND IS_FRAME='1' order by order_num ASC
select count(*) from sys_menu where parent_id='0'  AND  menu_type='M' AND visible='0' AND IS_FRAME='1' 


--如果只需要总合计（不分行展示每个一级菜单）
SELECT COUNT(menu_id) AS 所有指定一级菜单下直接子菜单总数
FROM sys_menu
WHERE parent_id IN (175,176,177,178); -- 填入一级菜单ID集合

--如果只需要总合计（不分行展示每个一级菜单）
SELECT COUNT(menu_id) AS 所有指定一级菜单下直接子菜单总数
FROM sys_menu
WHERE parent_id IN (175); -- 填入一级菜单ID集合

SELECT *
FROM sys_menu
WHERE parent_id IN (175)

-- 人员应聘管理
select * from t_recruitment_management


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
select lx from dd where id='2065254575763709952'
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
select state from cpxx where name='chenfa产品002' 
select state from cpxx where name='chenfa产品002' 
UPDATE cpxx SET state = '草稿' WHERE name = 'chenfa产品002';




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

