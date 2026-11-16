"""Build reproducible Excel samples and HTML views of actual exported data."""
import html
from pathlib import Path
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
artifacts = ROOT / 'artifacts'
artifacts.mkdir(exist_ok=True)
wb = Workbook()
ws = wb.active
ws.title = 'Import demo'
ws.append(['Notes', 'Name', 'Favorite', 'Phone1', 'Phone2', 'Email1', 'Social1', 'Address1'])
ws.append([None, 'Imported Student', True, '00110022', '0591-00000000', 'import@example.com', 'WeChat: imported', 'Demo campus'])
ws.append(['Excel import demo', 'Imported Friend', False, '00990011', None, 'friend@example.com', None, None])
for row in ws.iter_rows(min_row=2):
    for cell in row:
        if isinstance(cell.value, str):
            cell.data_type = 's'
            cell.number_format = '@'
wb.save(ROOT / 'docs' / 'sample_import_template.xlsx')

def table_view(source, target, title):
    book = load_workbook(source, data_only=False)
    sheet = book.active
    rows = list(sheet.values)
    contents = ''.join('<tr>' + ''.join('<th>' + html.escape(str(x or '')) + '</th>' for x in rows[0]) + '</tr>')
    contents += ''.join('<tr>' + ''.join('<td>' + html.escape('' if x is None else str(x)) + '</td>' for x in row) + '</tr>' for row in rows[1:])
    target.write_text('<!doctype html><meta charset="utf-8"><style>body{font:16px Segoe UI,Microsoft YaHei;padding:40px;background:#fff8f0;color:#443740}h1{font-size:28px}table{border-collapse:collapse;background:white}td,th{border:1px solid #d8c9ce;padding:12px;text-align:left;white-space:nowrap}th{background:#ffe0e8}p{line-height:1.8}</style>'
        + '<h1>' + html.escape(title) + '</h1><p>实际 .xlsx 文件内容预览 · openpyxl 读取原文件生成 · 不是 Excel 软件截图</p><p>文件：'
        + html.escape(source.name) + '</p><table>' + contents + '</table>', encoding='utf-8')
    book.close()

table_view(ROOT / 'docs/sample_import_template.xlsx', artifacts / 'import_preview.html', '导入样例：英文表头、姓名列换位、首列为空')
exported = artifacts / 'export_verified.xlsx'
if exported.exists():
    table_view(exported, artifacts / 'export_preview.html', '实际导出结果：一位联系人一行，多个电话分列')
