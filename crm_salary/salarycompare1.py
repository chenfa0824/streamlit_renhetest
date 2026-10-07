import requests
import pandas
# 调用hrm测试环境接口查询，单个接口
# 1、接口基础配置
url = "https://hrm-apitest.whrhkj.com/salary/salesperson/summary/list"
headers = {
    "x-access-token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3ODE3NjYwODIsInVzZXJuYW1lIjoiMTEyMDU0In0.wY6Ar3Z-jMXVi-5nXn4cuubsuVZfpJYNMHJosA6RmcU",
    "Content-Type": "application/json"
}
# 请求体
body = {
    "salaryMonth": "2026-03",
    "username": "郭静"
}

# 2、发起post请求
try:
    res = requests.post(url, json=body, headers=headers, timeout=15)
    res.raise_for_status()  # 捕获4xx/5xx http错误
    res_json = res.json()
except requests.exceptions.RequestException as e:
    print(f"接口请求失败：{e}")
    exit()

# 3、校验接口返回状态，提取sfgz
if res_json.get("success") is not True:
    print(f"接口业务失败，提示：{res_json.get('message')}")
    exit()
result_list = res_json.get("result", [])

# 存储提取数据
data_rows = []
for item in result_list:
    # 逐个提取所有字段，item.get(key, "") 空值兼容（None/空字符串统一返回空）
    id = item.get("id", "")
    salaryMonth = item.get("1salary", "")
    userId = item.get("userId", "")
    qy = item.get("qy", "")
    xq = item.get("xq", "")
    gw = item.get("gw", "")
    ygzt = item.get("ygzt", "")
    gl = item.get("gl", "")
    xqrysfmb = item.get("xqrysfmb", "")
    xqzxszgrs = item.get("xqzxszgrs", "")
    ydsj = item.get("ydsj", "")
    cqts = item.get("cqts", "")
    jxts = item.get("jxts", "")
    zgts = item.get("zgts", "")
    cdcs = item.get("cdcs", "")
    qjts = item.get("qjts", "")
    txts = item.get("txts", "")
    qqts = item.get("qqts", "")
    zdgzbz = item.get("zdgzbz", "")
    qsgyzgssbgjj = item.get("qsgyzgssbgjj", "")
    sbgjjbz = item.get("sbgjjbz", "")
    zhgzjsfa = item.get("zhgzjsfa", "")
    zhgzbz = item.get("zhgzbz", "")
    zhgz = item.get("zhgz", "")
    jbgz = item.get("jbgz", "")
    gwjt = item.get("gwjt", "")
    jbjt = item.get("jbjt", "")
    bmjt = item.get("bmjt", "")
    clwcbt = item.get("clwcbt", "")
    txbt = item.get("txbt", "")
    sbbt = item.get("sbbt", "")
    gjjbt = item.get("gjjbt", "")
    jxgwxs = item.get("jxgwxs", "")
    jxgz = item.get("jxgz", "")
    bjfljgz = item.get("bjfljgz", "")
    glgz = item.get("glgz", "")
    jj = item.get("jj", "")
    jzgdgzgz = item.get("jzgdgzgz", "")
    gdgzhj = item.get("gdgzhj", "")
    bxqgrjtyj = item.get("bxqgrjtyj", "")
    fbxqgrjtyj = item.get("fbxqgrjtyj", "")
    bxqgrxksr = item.get("bxqgrxksr", "")
    fbxqgrxksr = item.get("fbxqgrxksr", "")
    yjtcd = item.get("yjtcd", "")
    kxtcd = item.get("kxtcd", "")
    gryjkxtc = item.get("gryjkxtc", "")
    grwxddyj = item.get("grwxddyj", "")
    grwxddyjyjtl = item.get("grwxddyjyjtl", "")
    trtgjkhyxstcfd = item.get("trtgjkhyxstcfd", "")
    gryjtcxhj = item.get("gryjtcxhj", "")
    xqwcl = item.get("xqwcl", "")
    xqjtyj = item.get("xqjtyj", "")
    xqkxsr = item.get("xqkxsr", "")
    xzyjtcd = item.get("xzyjtcd", "")
    xzkxtcd = item.get("xzkxtcd", "")
    xqtczkl = item.get("xqtczkl", "")
    xqyjkxtc = item.get("xqyjkxtc", "")
    yjtchj = item.get("yjtchj", "")
    qtjlbc = item.get("qtjlbc", "")
    tfyj = item.get("tfyj", "")
    tfxs = item.get("tfxs", "")
    tftc = item.get("tftc", "")
    xqsxrts = item.get("xqsxrts", "")
    xqxxrts = item.get("xqxxrts", "")
    yjsx = item.get("yjsx", "")
    yjxx = item.get("yjxx", "")
    kxxx = item.get("kxxx", "")
    gryjkxwdyqykjtc = item.get("gryjkxwdyqykjtc", "")
    tckthj = item.get("tckthj", "")
    sjtchj = item.get("sjtchj", "")
    jxdj = item.get("jxdj", "")
    jxfs = item.get("jxfs", "")
    jxxs = item.get("jxxs", "")
    jzgwjxdj = item.get("jzgwjxdj", "")
    jzgwjxfs = item.get("jzgwjxfs", "")
    jzgwjxxs = item.get("jzgwjxxs", "")
    jxkk = item.get("jxkk", "")
    jzgwjxkk = item.get("jzgwjxkk", "")
    sopjxkk = item.get("sopjxkk", "")
    jxjl = item.get("jxjl", "")
    jzgwjxjl = item.get("jzgwjxjl", "")
    bdgz = item.get("bdgz", "")
    bdbc = item.get("bdbc", "")
    sjbdbc = item.get("sjbdbc", "")
    bdbcshjg = item.get("bdbcshjg", "")
    grbc = item.get("grbc", "")
    hbgzgktsdyfjl = item.get("hbgzgktsdyfjl", "")
    gztebyfjl = item.get("gztebyfjl", "")
    gzte = item.get("gzte", "")
    bxkk = item.get("bxkk", "")
    gjjkk = item.get("gjjkk", "")
    qtdk = item.get("qtdk", "")
    cdkk = item.get("cdkk", "")
    qqzkk = item.get("qqzkk", "")
    qjkk = item.get("qjkk", "")
    qtkk = item.get("qtkk", "")
    kkhj = item.get("kkhj", "")
    yfgzbyfjl = item.get("yfgzbyfjl", "")
    ysgz = item.get("ysgz", "")
    yfgz = item.get("yfgz", "")
    ljzxckxj = item.get("ljzxckxj", "")
    bygskk = item.get("bygskk", "")
    sfgz = item.get("sfgz", "")
    cwqzsffgz = item.get("cwqzsffgz", "")
    gzsjd = item.get("gzsjd", "")
    xm = item.get("xm", "")
    phone = item.get("phone", "")
    rzrq = item.get("rzrq", "")
    zzrq = item.get("zzrq", "")
    lzrq = item.get("lzrq", "")

    row = {
        "姓名": xm,
        "区域": qy,
        "校区": xq,
        "岗位": gw,
        "实发工资sfgz": sfgz
    }
    data_rows.append(row)
    print(f"姓名：{xm}，实发工资sfgz：{sfgz}")
    print({jbgz})

# 4、导出Excel文件
# if data_rows:
#     df = pandas.DataFrame(data_rows)
#     df.to_excel("薪资实发工资提取结果.xlsx", index=False)
#     print("\n数据已导出至【薪资实发工资提取结果.xlsx】")
# else:
#     print("未查询到人员数据！")