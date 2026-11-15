# 云通讯录 Cloud Address Book

软件工程（FZU–MU）极限编程作业：一个支持**收藏联系人**、**多重联系方式**与 **Excel 导入导出**的 Web 通讯录。

## 功能清单

| 功能 | 说明 | 对应评分项 |
| --- | --- | --- |
| 收藏联系人 | 点击星标收藏为常用联系人，页面顶部"常用联系人"区一键直达 | Bookmark Contacts (25 pts) |
| 多重联系方式 | 每个联系人可添加任意多条 电话 / 邮箱 / 社交媒体 / 地址，支持动态增删 | Multiple Contact Methods (10 pts) |
| Excel 导出 | 每个联系人一行、每类信息一列，自动扩展列数，附带导入模板工作表 | Import & Export (25 pts) |
| Excel 导入 | 识别表头（姓名 / 收藏 / 备注 / 电话\* / 邮箱\* / 社交\* / 地址\*），逐行入库 | Import & Export (25 pts) |
| 搜索 | 按姓名、备注及任意联系方式模糊搜索 | 附加功能 |
| 页面样式 | 渐变主题、卡片化布局、头像配色、响应式设计 | Page Style (10 pts) |

## 技术栈

- 后端：Python 3 + Flask + SQLite（`sqlite3` 标准库）
- Excel：openpyxl
- 前端：原生 HTML / CSS / JavaScript（无框架依赖）

## 运行方式

```bash
pip install -r requirements.txt
python app.py
# 浏览器访问 http://127.0.0.1:5000
```

## 目录结构

```
addressbook/
├── app.py               # Flask 后端：CRUD、收藏、Excel 导入导出
├── requirements.txt     # 依赖清单
├── templates/
│   └── index.html       # 单页前端模板
├── static/
│   ├── css/style.css    # 页面样式
│   └── js/app.js        # 前端交互逻辑
└── data/                # SQLite 数据库（自动创建，不入库）
```

## Excel 导入导出格式

- 第 1 列 `姓名` 必填；`收藏` 列取值 `是/1/true/★` 视为收藏；`备注` 列可选。
- `电话1、电话2…`、`邮箱1、邮箱2…`、`社交1…`、`地址1…`：同一类信息按序号分列，导入时按表头关键字（电话/手机、邮箱、社交/微信/QQ、地址）自动识别，列数不限。
- 导出文件含两个工作表：`通讯录`（数据）与 `导入模板`（格式示例）。
