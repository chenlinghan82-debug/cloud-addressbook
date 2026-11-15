"""云通讯录 Cloud Address Book.

Software Engineering (FZU-MU) Extreme Programming assignment.
Flask + SQLite backend, openpyxl powered Excel import/export.
"""
import io
import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_file
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "contacts.db")

# 联系方式的四类信息：key -> Excel 列前缀
DETAIL_TYPES = {
    "phone": "电话",
    "email": "邮箱",
    "social": "社交媒体",
    "address": "地址",
}
FAVORITE_TRUE = {"是", "1", "true", "y", "yes", "★", "√", "v"}

app = Flask(__name__)


# ---------------------------------------------------------------- database
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                favorite INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS contact_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
                type TEXT NOT NULL CHECK (type IN ('phone','email','social','address')),
                value TEXT NOT NULL
            );
            """
        )


def load_contact(conn, contact_id):
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        return None
    details = [
        {"id": d["id"], "type": d["type"], "value": d["value"]}
        for d in conn.execute(
            "SELECT * FROM contact_details WHERE contact_id = ? ORDER BY id",
            (contact_id,),
        )
    ]
    return {
        "id": row["id"],
        "name": row["name"],
        "favorite": bool(row["favorite"]),
        "notes": row["notes"],
        "created_at": row["created_at"],
        "details": details,
    }


def save_details(conn, contact_id, details):
    """整体重写联系人的多重联系方式。空值与未知类型直接丢弃。"""
    conn.execute("DELETE FROM contact_details WHERE contact_id = ?", (contact_id,))
    for item in details or []:
        dtype = str(item.get("type", "")).strip()
        value = str(item.get("value", "")).strip()
        if dtype in DETAIL_TYPES and value:
            conn.execute(
                "INSERT INTO contact_details (contact_id, type, value) VALUES (?, ?, ?)",
                (contact_id, dtype, value),
            )


# ------------------------------------------------------------------- pages
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------------------------------------------- api: crud
@app.get("/api/contacts")
def list_contacts():
    keyword = (request.args.get("q") or "").strip()
    with get_db() as conn:
        if keyword:
            like = f"%{keyword}%"
            rows = conn.execute(
                """
                SELECT DISTINCT c.* FROM contacts c
                LEFT JOIN contact_details d ON d.contact_id = c.id
                WHERE c.name LIKE ? OR c.notes LIKE ? OR d.value LIKE ?
                ORDER BY c.favorite DESC, c.name COLLATE NOCASE
                """,
                (like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY favorite DESC, name COLLATE NOCASE"
            ).fetchall()
        contacts = [load_contact(conn, row["id"]) for row in rows]
    return jsonify(contacts)


@app.post("/api/contacts")
def create_contact():
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO contacts (name, favorite, notes) VALUES (?, ?, ?)",
            (name, 1 if data.get("favorite") else 0, str(data.get("notes", "")).strip()),
        )
        contact_id = cur.lastrowid
        save_details(conn, contact_id, data.get("details"))
    return jsonify(load_contact(get_db(), contact_id)), 201


@app.put("/api/contacts/<int:contact_id>")
def update_contact(contact_id):
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    with get_db() as conn:
        row = conn.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Contact not found"}), 404
        conn.execute(
            "UPDATE contacts SET name = ?, notes = ? WHERE id = ?",
            (name, str(data.get("notes", "")).strip(), contact_id),
        )
        save_details(conn, contact_id, data.get("details"))
    return jsonify(load_contact(get_db(), contact_id))


@app.delete("/api/contacts/<int:contact_id>")
def delete_contact(contact_id):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Contact not found"}), 404
        conn.execute("DELETE FROM contact_details WHERE contact_id = ?", (contact_id,))
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    return jsonify({"deleted": contact_id})


@app.patch("/api/contacts/<int:contact_id>/favorite")
def toggle_favorite(contact_id):
    with get_db() as conn:
        row = conn.execute("SELECT favorite FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Contact not found"}), 404
        new_value = 0 if row["favorite"] else 1
        conn.execute("UPDATE contacts SET favorite = ? WHERE id = ?", (new_value, contact_id))
    return jsonify({"id": contact_id, "favorite": bool(new_value)})


# ------------------------------------------------------------ api: excel io
def build_sheet(contacts, wb=None):
    """把联系人列表写成一个工作表：每个联系人一行，每类信息若干列。"""
    ws = (wb or Workbook()).active
    ws.title = "通讯录"

    # 统计每类信息需要的最大列数
    max_per_type = {t: 1 for t in DETAIL_TYPES}
    for c in contacts:
        counter = {t: 0 for t in DETAIL_TYPES}
        for d in c["details"]:
            if d["type"] in counter:
                counter[d["type"]] += 1
        for t in max_per_type:
            max_per_type[t] = max(max_per_type[t], counter[t])

    headers = ["姓名", "收藏", "备注"]
    for t, prefix in DETAIL_TYPES.items():
        headers += [f"{prefix}{i}" for i in range(1, max_per_type[t] + 1)]

    thin = Side(style="thin", color="D9E2EC")
    header_fill = PatternFill("solid", fgColor="4F6DF5")
    header_font = Font(bold=True, color="FFFFFF")
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for c in contacts:
        grouped = {t: [] for t in DETAIL_TYPES}
        for d in c["details"]:
            if d["type"] in grouped:
                grouped[d["type"]].append(d["value"])
        row = [c["name"], "是" if c["favorite"] else "", c["notes"] or ""]
        for t in DETAIL_TYPES:
            values = grouped[t] + [""] * (max_per_type[t] - len(grouped[t]))
            row += values
        ws.append(row)

    widths = {"姓名": 14, "收藏": 6, "备注": 24}
    for idx, header in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = widths.get(header, 18)
    ws.freeze_panes = "A2"
    return ws


@app.get("/api/export")
def export_excel():
    with get_db() as conn:
        rows = conn.execute("SELECT id FROM contacts ORDER BY favorite DESC, name").fetchall()
        contacts = [load_contact(conn, row["id"]) for row in rows]

    wb = Workbook()
    build_sheet(contacts, wb)

    # 第二张表：空模板，说明导入格式
    tpl = wb.create_sheet("导入模板")
    tpl.append(["姓名", "收藏", "备注", "电话1", "电话2", "邮箱1", "社交1", "地址1"])
    tpl["A2"] = "张三"
    tpl["B2"] = "是"
    tpl["C2"] = "示例行，导入时会被忽略说明，可删除"
    tpl["D2"] = "13800138000"
    tpl["E2"] = "0591-88088088"
    tpl["F2"] = "zhangsan@example.com"
    tpl["G2"] = "微信: zhangsan"
    tpl["H2"] = "福建省福州市大学城"

    filename = f"通讯录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


HEADER_TYPE_PATTERNS = [
    (re.compile(r"电话|手机|tel|phone", re.I), "phone"),
    (re.compile(r"邮箱|email|邮件", re.I), "email"),
    (re.compile(r"社交|微信|qq|social", re.I), "social"),
    (re.compile(r"地址|address", re.I), "address"),
]


def classify_header(text):
    text = str(text or "").strip()
    if not text:
        return None
    if text == "姓名":
        return "name"
    if text == "收藏":
        return "favorite"
    if text == "备注":
        return "notes"
    for pattern, dtype in HEADER_TYPE_PATTERNS:
        if pattern.search(text):
            return dtype
    return None


def to_bool(value):
    return str(value or "").strip().lower() in FAVORITE_TRUE or str(value or "").strip() in {"是", "★", "√"}


@app.post("/api/import")
def import_excel():
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "Please choose an Excel file to import"}), 400
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        return jsonify({"error": "Only .xlsx Excel files are supported"}), 400

    try:
        wb = load_workbook(file, read_only=True, data_only=True)
    except Exception:
        return jsonify({"error": "Failed to parse the file. Please make sure it is a valid Excel file"}), 400

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if len(rows) < 2:
        return jsonify({"error": "The sheet is empty: at least a header row and one data row are required"}), 400

    types = [classify_header(cell) for cell in rows[0]]
    if "name" not in types:
        return jsonify({"error": "Header is missing the Name column; cannot import"}), 400

    imported, skipped = 0, 0
    with get_db() as conn:
        for raw in rows[1:]:
            if raw is None or not str(raw[0] or "").strip():
                skipped += 1
                continue
            record = {"name": "", "favorite": False, "notes": "", "details": []}
            for cell, ctype in zip(raw, types):
                if ctype is None:
                    continue
                value = str(cell or "").strip()
                if not value:
                    continue
                if ctype == "name":
                    record["name"] = value
                elif ctype == "favorite":
                    record["favorite"] = to_bool(value)
                elif ctype == "notes":
                    record["notes"] = value
                else:
                    record["details"].append({"type": ctype, "value": value})
            if not record["name"]:
                skipped += 1
                continue
            cur = conn.execute(
                "INSERT INTO contacts (name, favorite, notes) VALUES (?, ?, ?)",
                (record["name"], 1 if record["favorite"] else 0, record["notes"]),
            )
            save_details(conn, cur.lastrowid, record["details"])
            imported += 1
    return jsonify({"imported": imported, "skipped": skipped})


@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "接口不存在"}), 404
    return render_template("index.html")


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
