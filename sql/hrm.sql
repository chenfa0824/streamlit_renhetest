-- 查看表结构
desc sys_position
desc hrm_user_post
-- 查看详情，包含注释

select * from sys_position

SHOW FULL COLUMNS FROM hrm_user;
select post from hrm_user
select post from hrm_user  where id='116136'
select * from hrm_user  where id='100002'
select * from  hrm_offer
select * from hrm_user  where id='116136'or id='100001'
select * from rpt_userdata where sys_user_id='116136'
update hrm_user set post = 'POS1090' where id='116136';
update hrm_offer set status = 3 where code = 'OFFR202608120003';
-- 【HRM系统】【入职管理】创建offer
select * from hrm_offer order by create_time desc where position_id=
select * from hrm_offer where code = 'OFFR202608120001';
select * from hrm_offer where mobile='18792160002'
select * from hrm_offer where name='贾鸽'
-- 修改status员工状态【0待发送1待提交2审批中3待入职4已入职-1被动放弃-2主动放弃】
-- status变为4之后会在员工管理也就是sys_user插入一条数据，手动修改状态
update hrm_offer set status = 1 where code = 'OFFR202608270003';
select * from hrm_offer where code = 'OFFR202608250002';
-- 【用户管理-权限管理】
-- 1.【sys_user】 用户表
select * from sys_user
select user_id from sys_user where name='嘻哈5'
-- 课程内容库取值来源于新网校的rhkj表
select * from sys_user_post where user_id=
(select user_id from sys_user where name='单颖慧')

select * from sys_post
-- 2.【sys_role】角色表
select * from sys_role
select count(*) from sys_role
-- 3.【sys_user_role】 用户角色关联表（一个用户多个角色）
select * from sys_user_role
-- 4.【sys_depart】部门表 组织架构 部门级别depart_level 部门层级类型depart_level_type
select * from sys_depart where depart_level_type is not null
-- 5.【hrm_user_post】用户岗位关系表 position_id position_name
-- position_type岗位类型0全职1兼职、post_status岗位状态0正常1已到期、delete_fal删除标记0未删除1删除
select * from hrm_user_post order by create_time desc
-- 116242
select * from hrm_user_post where sys_user_id='116255' and post_status='0' and delete_flag='0'
select * from hrm_user_post where sys_user_id='103607'
select * from sys_position where id='POS1063'

select * from sys_position where name like '%咨询主管%'
select * from hrm_user_post where position_name ='分校长'
select * from hrm_user_post where position_name ='咨询'
select * from hrm_user_post where position_name ='咨询主管'

-- 【审批流程相关】
SELECT * from camunda.rpt_workflow where wf_name='调岗' order by create_time desc

-- 绩效数据crm_test  马欢 102418
-- 查询员工id
select count(*) from  t_perf_deduction
select user_id  from  sys_user where user_name='102418'
select * from  t_perf_deduction where user_id='00520199BA50C50sIAce' and month='2026-01'
-- 查询一个人的绩效数据
select * from  t_perf_deduction where user_id=(select user_id  from  sys_user where user_name='102418') and month='2026-02'
-- 更新某个人某月的绩效数据
UPDATE t_perf_deduction SET perf_level = 'S' WHERE id =
(select id from  t_perf_deduction where user_id=(select user_id  from  sys_user where user_name='102418') and month='2026-06')

select * from sys_user where user_name='102418'

-- 【绩效管理】 CRM后台导入的绩效数据  post_name岗位名称
-- 查询岗位后筛选人员数据
-- 查看注释
select * from  t_perf_deduction where post_name='区域总经理' and user_id=(select user_id  from  sys_user where user_name='102418')
SELECT * FROM camunda.rpt_workflow where approved_person_id ='116136'





select * FROM  hrm_user
