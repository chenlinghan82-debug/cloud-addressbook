# -*- coding: utf-8 -*-
"""生成导入演示 Excel，执行导入，并生成导出文件"""
import json
import urllib.request

from openpyxl import Workbook

BASE = "http://127.0.0.1:5000"

# 1. 生成导入演示文件
wb = Workbook()
ws = wb.active
ws.title = "通讯录"
ws.append(["姓名", "收藏", "备注", "电话1", "电话2", "邮箱1", "社交1", "地址1"])
ws.append(["赵云", "是", "项目小组长", "13555556666", None, "zhaoyun@fzu.edu.cn", "微信: zhaoyun", "福建省福州市仓山区金山大道"])
ws.append(["孙尚香", None, "同班同学", "13677778888", "0591-62228888", "sunshx@stu.fzu.edu.cn", None, None])
wb.save("docs/import_demo.xlsx")
print("演示文件已生成 docs/import_demo.xlsx")

# 2. 上传导入
content = open("docs/import_demo.xlsx", "rb").read()
boundary = "----demo1234"
body = (
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="import_demo.xlsx"\r\n'
    f"Content-Type: application/octet-stream\r\n\r\n"
).encode() + content + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(
    BASE + "/api/import", data=body, method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
print("导入结果:", json.loads(urllib.request.urlopen(req).read().decode()))

# 3. 导出
with urllib.request.urlopen(BASE + "/api/export") as r:
    data = r.read()
open("docs/export_demo.xlsx", "wb").write(data)
print("导出文件大小:", len(data))
