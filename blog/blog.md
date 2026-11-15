# Software Engineering Assignment 4: Extreme Programming — Cloud Address Book — Chen Linghan 832401201

| Item | Content |
| --- | --- |
| Name / Student ID | Chen Linghan 832401201 |
| Course | Software Engineering (FZU–MU) |
| Assignment Requirement | [Extreme Programming (Deadline: November 17, 2026, 23:59)](https://bbs.csdn.net/topics/620593436) |
| Deadline | November 17, 2026, 23:59 |
| Deployment (cloud) | [https://addressbook-zeta.vercel.app](https://addressbook-zeta.vercel.app) |
| Demo API | [https://addressbook-zeta.vercel.app/api/contacts](https://addressbook-zeta.vercel.app/api/contacts) |
| GitHub repository | [https://github.com/chenlinghan82-debug/cloud-addressbook](https://github.com/chenlinghan82-debug/cloud-addressbook) |
| Code standard | [docs/CODE_STANDARD.md](https://github.com/chenlinghan82-debug/cloud-addressbook/blob/main/docs/CODE_STANDARD.md) — follows PEP 8 for Python, Airbnb style for JavaScript, Google style for commit messages |
| Team | Individual project — all work and commits by Chen Linghan (contribution ratio 100%) |

## Table of Contents

1. Background and objectives
2. Requirements
3. Design and implementation
4. Technology choices
5. Finished product
6. Code explanation
7. Database design
8. Tests
9. Deployment and access
10. PSP table
11. Personal summary
12. References

## 1. Background and objectives

This assignment applies **Extreme Programming (XP)** practices to build a web **Cloud Address Book**. The goals are:

- Practice the full XP loop: requirement analysis → simple design → small releases → testing → deployment → retrospective.
- Implement three graded functions: **Bookmark Contacts (25 pts)**, **Multiple Contact Methods (10 pts)** and **Excel Import/Export (25 pts)**, plus **Page Style (10 pts)**.
- Deploy the finished product to the cloud so it can be used from anywhere.

Everything was developed in small commits on GitHub (11 commits at the time of writing, all by me) and deployed to Vercel from the connected repository.

## 2. Requirements

### 2.1 Required functions

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Bookmark contacts (25 pts) | A star on every card toggles `favorite`; bookmarked people appear in the golden "Frequent Contacts" quick-access area and are listed first | Figure 1 |
| Multiple contact methods (10 pts) | Each contact holds any number of phone / email / social / address entries; the edit dialog adds or removes rows dynamically | Figure 2 |
| Import & export (25 pts) | Export: one row per contact, one column per piece of information with auto-expanded headers; Import: header keywords are recognized by regex | Figure 4 |
| Page style (10 pts) | Kawaii sticker-style UI: pastel palette, cartoon mascot, hand-drawn borders, bouncy cards, responsive layout | Figure 1 |

### 2.2 Extensions

- **Fuzzy search** across the name, notes and every contact method (Figure 3).
- **Import template worksheet** shipped inside every exported Excel file.
- **Demo seeding** on the cloud instance so reviewers see live data immediately.
- **Round-trip self test** (`docs/selftest.py`) proving export → import consistency.

## 3. Design and implementation

The system is a classic three-layer architecture. The frontend is a single page talking to a JSON API; the backend owns all business rules and persistence.

```
Browser (index.html + app.js + style.css)
        │  fetch /api/...  (JSON)
        ▼
Flask app.py
 ├─ Contact CRUD + favorite toggle      → contacts table
 ├─ Multiple contact methods (1:N)      → contact_details table
 └─ Excel import/export (openpyxl)      → .xlsx file stream
        │
        ▼
   SQLite contacts.db  (local) / /tmp on Vercel
```

| Module | Responsibility |
| --- | --- |
| `app.py` | All REST endpoints, favorite toggling, Excel build/parse, database bootstrap and demo seeding |
| `templates/index.html` | Single-page layout: hero, frequent-contacts area, card grid, edit dialog |
| `static/css/style.css` | Kawaii sticker theme: pastel variables, sticker cards, mascot drawn in pure CSS |
| `static/js/app.js` | Rendering, search debounce, dynamic detail rows, clipboard import/export glue |
| `api/index.py` | Vercel serverless entry (routes every request to the Flask app) |

## 4. Technology choices

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | Flask + SQLite | Zero configuration, `ON DELETE CASCADE` removes details automatically |
| Excel | openpyxl | Full control of headers, styles and column widths |
| Frontend | Vanilla HTML/CSS/JS | No framework dependency; fast and a good fundamentals exercise |
| Deployment | Vercel (Python serverless) | Connected to GitHub — every push deploys automatically |
| Testing | Python self-test script | API-level round-trip regression before each release |

## 5. Finished product

### 5.1 Home page and bookmark contacts

Figure 1 shows the home page: the kawaii mascot header, the "Frequent Contacts" quick-access cards (Zhang Wei, Li Na, Zhao Yun) and all six contacts as sticker cards. Clicking a star toggles the bookmark instantly.

![Figure 1. Home page with the frequent-contacts quick-access area and all contact cards](IMG_HOME)

### 5.2 Multiple contact methods

Figure 2 shows the edit dialog of Zhang Wei: two phones, one email, one WeChat and one address, plus a freshly added empty Email row created by the "＋Email" chip. Any number of rows can be added; empty rows are dropped on save.

![Figure 2. Edit dialog holding multiple contact methods with dynamic add/remove](IMG_EDIT)

### 5.3 Search across every field

Figure 3 shows searching "微信": the query matches Zhang Wei's WeChat, Zhao Yun's WeChat and Wang Qiang's WeCom, although none of the names contain the keyword.

![Figure 3. Fuzzy search matches social accounts as well as names](IMG_SEARCH)

### 5.4 Excel import and export

Figure 4 shows the address book after importing an Excel file containing two new people (Zhao Yun and Sun Shangxiang); Zhao Yun's favorite flag was read from the "收藏" column. The exported workbook contains one row per contact and one column per piece of information, e.g. `Phone1, Phone2, Email1, Social1, Address1` for Zhang Wei.

![Figure 4. Two imported contacts appear with their favorite flags recognized](IMG_IMPORT)

## 6. Code explanation

CODE 1 — bookmark toggle (`app.py`). One SQL flip, then the frontend re-sorts by `favorite DESC`:

```python
@app.patch("/api/contacts/<int:contact_id>/favorite")
def toggle_favorite(contact_id):
    ...
    new_value = 0 if row["favorite"] else 1
    conn.execute("UPDATE contacts SET favorite = ? WHERE id = ?", (new_value, contact_id))
```

CODE 2 — multiple contact methods are rewritten atomically per save (`app.py`). Unknown types and blank values are dropped, so the frontend can send whatever the user typed:

```python
def save_details(conn, contact_id, details):
    conn.execute("DELETE FROM contact_details WHERE contact_id = ?", (contact_id,))
    for item in details or []:
        dtype, value = item.get("type"), str(item.get("value", "")).strip()
        if dtype in DETAIL_TYPES and value:
            conn.execute(
                "INSERT INTO contact_details (contact_id, type, value) VALUES (?, ?, ?)",
                (contact_id, dtype, value))
```

CODE 3 — export builds dynamic columns: it first counts the maximum entries per type across all contacts, then emits `Phone1…PhoneN` style headers so every contact fits in one row:

```python
max_per_type = {t: 1 for t in DETAIL_TYPES}
for c in contacts:
    counter = {t: 0 for t in DETAIL_TYPES}
    for d in c["details"]:
        if d["type"] in counter:
            counter[d["type"]] += 1
    for t in max_per_type:
        max_per_type[t] = max(max_per_type[t], counter[t])
```

CODE 4 — import classifies header cells by regex instead of fixed column positions, so files with any reasonable header layout can be imported:

```python
HEADER_TYPE_PATTERNS = [
    (re.compile(r"电话|手机|tel|phone", re.I), "phone"),
    (re.compile(r"邮箱|email|邮件", re.I), "email"),
    (re.compile(r"社交|微信|qq|social", re.I), "social"),
    (re.compile(r"地址|address", re.I), "address"),
]
```

CODE 5 — search joins the detail table so any stored value is searchable:

```sql
SELECT DISTINCT c.* FROM contacts c
LEFT JOIN contact_details d ON d.contact_id = c.id
WHERE c.name LIKE ? OR c.notes LIKE ? OR d.value LIKE ?
ORDER BY c.favorite DESC, c.name COLLATE NOCASE
```

CODE 6 — every rendered string passes through `escapeHtml` to prevent XSS (`static/js/app.js`):

```javascript
function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
}
```

## 7. Database design

| Table | Columns | Notes |
| --- | --- | --- |
| `contacts` | id, name, favorite, notes, created_at | One row per person; `favorite` drives the quick-access area |
| `contact_details` | id, contact_id (FK), type, value | 1:N contact methods; `type` CHECK-limited to phone/email/social/address; cascading delete |

## 8. Tests

`docs/selftest.py` runs an end-to-end API regression against a live server:

| Group | Checks |
| --- | --- |
| CRUD | Create 3 contacts with multi-method details, update one, read back |
| Bookmark | Toggle favorite and verify the flag flips |
| Search | Find a contact by a fragment of its phone number |
| Export | Download the workbook and assert headers and Zhang Wei's row content |
| Round trip | Re-import the exported file; assert all rows are recreated intact |

All checks passed before the deployment commit.

## 9. Deployment and access

- **Cloud deployment**: <https://addressbook-zeta.vercel.app> — Flask runs as a Vercel Python serverless function; the SQLite database lives in the function's `/tmp` with demo data seeded automatically on cold start, so reviewers always see a populated address book.
- **GitHub**: <https://github.com/chenlinghan82-debug/cloud-addressbook> — the repository is connected to Vercel, so every push triggers a production deployment.

![Figure 5. GitHub commit history: 11 commits during development, all by Chen Linghan](IMG_COMMITS)

**Complete running video** (16 s, covering bookmark toggle, dynamic multi-contact editing and search): [blog/screenshots/demo_video.webm](https://github.com/chenlinghan82-debug/cloud-addressbook/blob/main/blog/screenshots/demo_video.webm)

## 10. PSP table

| Stage | Planned (h) | Actual (h) |
| --- | --- | --- |
| Reading and planning | 1.5 | 2.0 |
| Requirements and design | 2.0 | 1.5 |
| Back-end | 4.0 | 4.5 |
| Front-end and UI redesign | 5.0 | 6.0 |
| Testing | 1.5 | 2.0 |
| Deployment | 1.0 | 1.5 |
| Report | 1.5 | 2.0 |
| **Total** | **16.5** | **19.5** |

Planned hours were estimated before development; actual hours were recorded afterwards.

## 11. Personal summary

The three graded functions taught me three different lessons. Bookmark contacts showed how a one-column schema change plus one PATCH endpoint can produce a whole feature. Multiple contact methods forced a clean 1:N data model instead of cramming fields into the contacts row. Excel import/export was the hardest: "one row per contact, one column per piece of information" breaks when people have different numbers of phone numbers, and the dynamic-header design (scan first, then emit `Phone1…PhoneN`) was the key insight.

Two real-world bugs were valuable too. A CSS rule (`display: grid`) silently overrode the HTML `hidden` attribute, which taught me to respect the priority of browser default styles; and Vercel's read-only filesystem refused to create my SQLite file, which taught me to check the runtime environment instead of assuming my laptop's layout. The round-trip self-test caught a potential data-loss bug before it ever shipped — writing tests really does pay for itself.

If I continue this project, I would add avatar upload, vCard export and a proper login system, and move from serverless SQLite to a managed database for persistent cloud storage.

## 12. References

- Assignment requirement: <https://bbs.csdn.net/topics/620593436>
- Flask documentation: <https://flask.palletsprojects.com/>
- openpyxl documentation: <https://openpyxl.readthedocs.io/>
- PEP 8 – Style Guide for Python Code: <https://peps.python.org/pep-0008/>
- Vercel Python runtime: <https://vercel.com/docs/functions/runtimes/python>

---

*Thanks for reviewing!*
