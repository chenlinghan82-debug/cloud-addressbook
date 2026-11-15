# -*- coding: utf-8 -*-
"""把 app.py 中的中文错误信息替换为英文"""
import io

path = r"D:\软工极限\addressbook\app.py"
text = io.open(path, encoding="utf-8").read()

pairs = [
    ('"姓名不能为空"', '"Name is required"'),
    ('"联系人不存在"', '"Contact not found"'),
    ('"请选择要导入的 Excel 文件"', '"Please choose an Excel file to import"'),
    ('"仅支持 .xlsx 格式的 Excel 文件"', '"Only .xlsx Excel files are supported"'),
    ('"文件解析失败，请确认为合法的 Excel 文件"', '"Failed to parse the file. Please make sure it is a valid Excel file"'),
    ('"表格为空，至少需要表头和一行数据"', '"The sheet is empty: at least a header row and one data row are required"'),
    ('"表头缺少“姓名”列，无法导入"', '"Header is missing the Name column; cannot import"'),
]

for old, new in pairs:
    if old not in text:
        print("MISS:", old[:40])
    text = text.replace(old, new)

io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("done")
