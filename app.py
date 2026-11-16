"""云通讯录 Cloud Address Book.

Software Engineering (FZU-MU) Extreme Programming assignment.
Flask + SQLite backend, openpyxl powered Excel import/export.
"""
import io
import os
import re
from datetime import datetime

from flask import Flask, jsonify, render_template, request, send_file
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from werkzeug.exceptions import HTTPException

from database import connect, initialize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", "")
STORAGE_CONFIGURED = os.environ.get("VERCEL") != "1" or bool(DATABASE_URL)
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "data", "contacts.db"))

# 联系方式的四类信息：key -> Excel 列前缀
DETAIL_TYPES = {
    "phone": "电话",
    "email": "邮箱",
    "social": "社交媒体",
    "address": "地址",
}
FAVORITE_TRUE = {"是", "1", "true", "y", "yes", "★", "√", "v"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# ---------------------------------------------------------------- database
def get_db():
    return connect(DB_PATH, DATABASE_URL)


def init_db():
    with get_db() as conn:
        initialize(conn)
        # 云端演示实例（SEED_DEMO=1）在空库时灌入演示数据
        if os.environ.get("SEED_DEMO") == "1" and not conn.execute(
            "SELECT 1 FROM contacts LIMIT 1"
        ).fetchone():
            for item in DEMO_CONTACTS:
                contact_id = conn.insert_contact(item["name"], int(item["favorite"]), item["notes"])
                save_details(conn, contact_id, item["details"])


DEMO_CONTACTS = [
    {"name": "Zhang Wei", "notes": "College roommate · monitor", "favorite": True, "details": [
        {"type": "phone", "value": "13800138000"},
        {"type": "phone", "value": "0591-88088088"},
        {"type": "email", "value": "zhangwei@fzu.edu.cn"},
        {"type": "social", "value": "WeChat: zhangwei_fzu"},
        {"type": "address", "value": "No.5 Gongye Rd, Gulou, Fuzhou"},
    ]},
    {"name": "Li Na", "notes": "SE course leader", "favorite": True, "details": [
        {"type": "phone", "value": "13912345678"},
        {"type": "email", "value": "lina@stu.fzu.edu.cn"},
        {"type": "address", "value": "Xueyuan Rd, Minhou, Fuzhou"},
    ]},
    {"name": "Wang Qiang", "notes": "Cloud deployment mentor", "favorite": False, "details": [
        {"type": "email", "value": "wangqiang@huawei.com"},
        {"type": "social", "value": "WeCom: wangqiang-hw"},
    ]},
    {"name": "Chen Xiaoming", "notes": "Basketball buddy", "favorite": False, "details": [
        {"type": "phone", "value": "13766668888"},
        {"type": "social", "value": "QQ: 987654321"},
    ]},
]


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
    return render_template("index.html", storage_configured=STORAGE_CONFIGURED)


@app.before_request
def require_storage():
    if request.path.startswith("/api/") and request.path != "/api/health" and not STORAGE_CONFIGURED:
        return jsonify({"error": "Persistent database is not configured. Set DATABASE_URL in Vercel."}), 503


@app.get("/api/health")
def health():
    if not STORAGE_CONFIGURED:
        return jsonify({"status": "configuration_required", "persistent": False}), 503
    with get_db() as conn:
        conn.execute("SELECT 1").fetchone()
    return jsonify({"status": "ok", "storage": "postgresql" if DATABASE_URL else "sqlite", "persistent": True})


def contact_payload():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("Contact must be a JSON object")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        raise ValueError("Name is required")
    if len(data["name"].strip()) > 200:
        raise ValueError("Name must not exceed 200 characters")
    if not isinstance(data.get("notes", ""), str):
        raise ValueError("Notes must be text")
    if "favorite" in data and not isinstance(data["favorite"], bool):
        raise ValueError("Favorite must be true or false")
    details = data.get("details", [])
    if not isinstance(details, list) or len(details) > 100:
        raise ValueError("Details must be a list of at most 100 items")
    for item in details:
        if not isinstance(item, dict) or item.get("type") not in DETAIL_TYPES or not isinstance(item.get("value"), str):
            raise ValueError("Each detail needs a valid type and text value")
    return data


@app.errorhandler(ValueError)
def invalid_input(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify({"error": error.description}), error.code


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
                WHERE LOWER(c.name) LIKE LOWER(?) OR LOWER(c.notes) LIKE LOWER(?) OR LOWER(d.value) LIKE LOWER(?)
                ORDER BY c.favorite DESC, c.name
                """,
                (like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY favorite DESC, name"
            ).fetchall()
        contacts = [load_contact(conn, row["id"]) for row in rows]
    return jsonify(contacts)


@app.post("/api/contacts")
def create_contact():
    data = contact_payload()
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    with get_db() as conn:
        contact_id = conn.insert_contact(name, int(data.get("favorite", False)), data.get("notes", "").strip())
        save_details(conn, contact_id, data.get("details"))
        result = load_contact(conn, contact_id)
    return jsonify(result), 201


@app.put("/api/contacts/<int:contact_id>")
def update_contact(contact_id):
    data = contact_payload()
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
        result = load_contact(conn, contact_id)
    return jsonify(result)


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
        # Treat user content as text, including strings beginning with '='.
        for cell in ws[ws.max_row]:
            cell.data_type = "s"
            cell.number_format = "@"

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
    tpl["C2"] = "示例联系人：导入前请删除此行；导入会新增联系人，不自动去重"
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
    aliases = {"姓名": "name", "name": "name", "收藏": "favorite", "favorite": "favorite", "favourite": "favorite", "备注": "notes", "notes": "notes"}
    if text.lower() in aliases:
        return aliases[text.lower()]
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

    try:
        ws = wb.active
        rows = []
        for row in ws.iter_rows(values_only=True):
            if len(row) > 200 or len(rows) >= 10001:
                raise ValueError("Maximum 10000 contacts and 200 columns per import")
            rows.append(row)
    except ValueError:
        raise
    except Exception as error:
        raise ValueError("Failed to read the workbook") from error
    finally:
        wb.close()
    if len(rows) < 2:
        return jsonify({"error": "The sheet is empty: at least a header row and one data row are required"}), 400

    types = [classify_header(cell) for cell in rows[0]]
    if "name" not in types:
        return jsonify({"error": "Header is missing the Name column; cannot import"}), 400
    if any(types.count(kind) > 1 for kind in ("name", "favorite", "notes")):
        raise ValueError("Name, Favorite and Notes columns must not be duplicated")

    imported, skipped = 0, 0
    with get_db() as conn:
        for raw in rows[1:]:
            if raw is None or not str(raw[types.index("name")] or "").strip():
                skipped += 1
                continue
            record = {"name": "", "favorite": False, "notes": "", "details": []}
            for cell, ctype in zip(raw, types):
                if ctype is None:
                    continue
                value = "" if cell is None else str(cell).strip()
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
            if len(record["name"]) > 200:
                raise ValueError("Name must not exceed 200 characters; no rows were imported")
            contact_id = conn.insert_contact(record["name"], int(record["favorite"]), record["notes"])
            save_details(conn, contact_id, record["details"])
            imported += 1
    return jsonify({"imported": imported, "skipped": skipped})


@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "接口不存在"}), 404
    return jsonify({"error": "Page not found"}), 404


if STORAGE_CONFIGURED:
    init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
