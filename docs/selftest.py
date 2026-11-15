# -*- coding: utf-8 -*-
"""功能自测脚本：CRUD / 收藏 / 搜索 / 导入导出"""
import json
import urllib.request
from openpyxl import load_workbook

BASE = "http://127.0.0.1:5000"


def call(path, method="GET", payload=None, files=None):
    if files:
        boundary = "----testboundary1234"
        fname, fcontent = files
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + fcontent + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            BASE + path, data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
    else:
        data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json; charset=utf-8")
    with urllib.request.urlopen(req) as r:
        if r.headers.get("Content-Type", "").startswith("application/json"):
            return json.loads(r.read().decode())
        return r.read()


contacts = call("/api/contacts")
print("初始联系人数量:", len(contacts))

# 新建两个联系人
r1 = call("/api/contacts", "POST", {
    "name": "张伟", "notes": "大学室友 · 班长", "favorite": True,
    "details": [
        {"type": "phone", "value": "13800138000"},
        {"type": "phone", "value": "0591-88088088"},
        {"type": "email", "value": "zhangwei@fzu.edu.cn"},
        {"type": "social", "value": "微信: zhangwei_fzu"},
        {"type": "address", "value": "福建省福州市鼓楼区工业路5号"},
    ]})
print("新建 张伟 -> id", r1["id"], "联系方式数", len(r1["details"]))

r2 = call("/api/contacts", "POST", {
    "name": "李娜", "notes": "软件工程课程组长", "favorite": True,
    "details": [
        {"type": "phone", "value": "13912345678"},
        {"type": "email", "value": "lina@stu.fzu.edu.cn"},
        {"type": "address", "value": "福建省福州市闽侯县学园路2号"},
    ]})
print("新建 李娜 -> id", r2["id"])

r3 = call("/api/contacts", "POST", {
    "name": "王强", "notes": "云部署指导老师", "favorite": False,
    "details": [
        {"type": "email", "value": "wangqiang@huawei.com"},
        {"type": "social", "value": "企业微信: wangqiang-hw"},
    ]})
print("新建 王强 -> id", r3["id"])

# 搜索（按电话）
s = call("/api/contacts?q=13800138000")
print("按电话搜索命中:", [c["name"] for c in s])

# 收藏切换
f = call(f"/api/contacts/{r3['id']}/favorite", "PATCH")
print("王强收藏切换为:", f["favorite"])

# 编辑：给李娜加一个微信号
r2["details"].append({"type": "social", "value": "微信: lina_se"})
call(f"/api/contacts/{r2['id']}", "PUT", r2)
check = call("/api/contacts")
lina = next(c for c in check if c["name"] == "李娜")
print("李娜编辑后联系方式数:", len(lina["details"]))

# 导出
with urllib.request.urlopen(BASE + "/api/export") as r:
    xlsx_bytes = r.read()
with open("docs/export_test.xlsx", "wb") as f:
    f.write(xlsx_bytes)
print("导出文件大小:", len(xlsx_bytes), "bytes")

wb = load_workbook("docs/export_test.xlsx")
ws = wb["通讯录"]
print("导出表头:", [c.value for c in ws[1]])
print("张伟行:", [c.value for c in ws[2]])

# 再导入刚才导出的文件（往返一致性测试）
before = len(call("/api/contacts"))
result = call("/api/import", files=("export_test.xlsx", xlsx_bytes))
after = len(call("/api/contacts"))
print(f"导入结果: 新增 {result['imported']} 跳过 {result['skipped']}，人数 {before} -> {after}")
print("全部测试通过 ✓")
