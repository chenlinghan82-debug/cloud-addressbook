# -*- coding: utf-8 -*-
"""初始化演示数据"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"


def call(path, method="GET", payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    return json.loads(urllib.request.urlopen(req).read().decode())


DEMO = [
    {"name": "张伟", "notes": "大学室友 · 班长", "favorite": True, "details": [
        {"type": "phone", "value": "13800138000"},
        {"type": "phone", "value": "0591-88088088"},
        {"type": "email", "value": "zhangwei@fzu.edu.cn"},
        {"type": "social", "value": "微信: zhangwei_fzu"},
        {"type": "address", "value": "福建省福州市鼓楼区工业路5号"},
    ]},
    {"name": "李娜", "notes": "软件工程课程组长", "favorite": True, "details": [
        {"type": "phone", "value": "13912345678"},
        {"type": "email", "value": "lina@stu.fzu.edu.cn"},
        {"type": "address", "value": "福建省福州市闽侯县学园路2号"},
    ]},
    {"name": "王强", "notes": "云部署指导老师", "favorite": False, "details": [
        {"type": "email", "value": "wangqiang@huawei.com"},
        {"type": "social", "value": "企业微信: wangqiang-hw"},
    ]},
    {"name": "陈晓明", "notes": "球友 · 周末篮球", "favorite": False, "details": [
        {"type": "phone", "value": "13766668888"},
        {"type": "social", "value": "QQ: 987654321"},
    ]},
]

if len(call("/api/contacts")) == 0:
    for c in DEMO:
        call("/api/contacts", "POST", c)
print("当前联系人数量:", len(call("/api/contacts")))
