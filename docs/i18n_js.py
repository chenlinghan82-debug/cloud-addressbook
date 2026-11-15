# -*- coding: utf-8 -*-
"""把 app.js 中的中文文案替换为英文"""
import io

path = r"D:\软工极限\addressbook\static\js\app.js"
text = io.open(path, encoding="utf-8").read()

pairs = [
    ('TYPE_LABEL = { phone: "电话", email: "邮箱", social: "社交", address: "地址" }',
     'TYPE_LABEL = { phone: "Phone", email: "Email", social: "Social", address: "Address" }'),
    ('"姓名不能为空"', '"Name is required"'),
    ('"联系人不存在"', '"Contact not found"'),
    ('"已保存修改"', '"Changes saved"'),
    ('"新建联系人成功"', '"Contact created"'),
    ('toast(r.favorite ? `已收藏「${state.contacts.find((c) => c.id === id)?.name ?? ""}」为常用联系人` : "已取消收藏");',
     'toast(r.favorite ? `Bookmarked "${state.contacts.find((c) => c.id === id)?.name ?? ""}" as a frequent contact` : "Removed from favorites");'),
    ('toast("已删除");', 'toast("Contact deleted");'),
    ("if (!confirm(`确定删除「${name}」吗？删除后无法恢复。`)) return;",
     'if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;'),
    ('toast("正在导出 Excel…");', 'toast("Exporting Excel…");'),
    ('toast(`导入成功：新增 ${r.imported} 人${r.skipped ? `，跳过 ${r.skipped} 行` : ""}`);',
     'toast(`Import succeeded: ${r.imported} contacts added${r.skipped ? `, ${r.skipped} rows skipped` : ""}`);'),
    ('`请求失败(${res.status})`', '`Request failed (${res.status})`'),
    ('"接口不存在"', '"API not found"'),
]

for old, new in pairs:
    if old not in text:
        print("MISS:", old[:60])
    text = text.replace(old, new)

io.open(path, "w", encoding="utf-8", newline="\n").write(text)
print("done")
