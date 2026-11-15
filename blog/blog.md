# Extreme Programming Assignment: Cloud Address Book (Bookmark Contacts · Multiple Contact Methods · Excel Import & Export)

> This assignment is completed individually. This blog records the whole process: requirement analysis, design, coding, testing and review.

| Item | Content |
| --- | --- |
| Course | Software Engineering (FZU–MU) |
| Team Name | Individual project (no team) |
| Assignment Requirements | [Extreme Programming (Deadline: November 17, 2026, 23:59)](https://bbs.csdn.net/topics/620593436) |
| Objectives of This Assignment | Build a web address book that supports **bookmark contacts**, **multiple contact methods** and **Excel import/export**, and experience the complete Extreme Programming workflow: design → coding → testing → deployment → blog review |
| Other References | [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/), [Flask Documentation](https://flask.palletsprojects.com/), [openpyxl Documentation](https://openpyxl.readthedocs.io/) |

## Table of Contents

<!-- CSDN generates the TOC automatically from headings -->

## 1. Project Address

| Item | Link |
| --- | --- |
| GitHub Repository | https://github.com/chenlinghan82-debug/cloud-addressbook |
| Code Standard | https://github.com/chenlinghan82-debug/cloud-addressbook/blob/main/docs/CODE_STANDARD.md |
| Local Access | http://127.0.0.1:5000 |
| Demo Video | See Section 7 (complete running video) |

## 2. GitHub Commit History

![GitHub commit history: 4 development commits, all by me](IMG_COMMITS)

There are **4 commits** during the development stage (see the screenshot above); the screenshots, demo video and blog draft were pushed to the repository later, so the repository contains 6 commits in total. All commits were made by me (**contribution ratio: 100%**):

| Commit | Content |
| --- | --- |
| `feat(backend)` | Flask + SQLite address book backend: bookmark, multiple contact methods and Excel import/export APIs |
| `feat(frontend)` | Single-page frontend with gradient theme, card layout, favorite star and dynamic multi-contact editing |
| `docs` | README usage guide, self-test and demo data scripts |
| `docs` | Code standard document |

## 3. Requirement Analysis & Technology Stack

### 3.1 Feature Breakdown

| Feature | Points | My Implementation |
| --- | --- | --- |
| Bookmark Contacts | 25 pts | A star button on each contact card; bookmarked contacts appear in the "⭐ Frequent Contacts" quick-access area at the top |
| Multiple Contact Methods | 10 pts | Each contact can hold any number of phone / email / social media / address entries, dynamically added and removed in the edit dialog |
| Import & Export | 25 pts | Export: one row per contact, one column per piece of information (columns auto-expand); Import: header keywords are recognized automatically and rows are inserted into the database |
| Page Style | 10 pts | Gradient theme, card-based layout, colored avatars, responsive design |
| Cloud Deployment (optional) | 15 pts | See Section 8 |

### 3.2 Technology Stack

- **Backend**: Python Flask + SQLite — lightweight, zero configuration, and SQLite natively supports `ON DELETE CASCADE` for contact details.
- **Excel**: openpyxl — direct control over header styles and column widths, so the exported file is human-readable.
- **Frontend**: vanilla HTML / CSS / JavaScript with no framework dependency — good practice of fundamentals and fast page loading.

### 3.3 System Architecture & Data Model

```
Browser (index.html + app.js + style.css)
        │  fetch /api/...  (JSON)
        ▼
Flask app.py
 ├─ Contact CRUD + favorite toggle     → contacts table
 ├─ Multiple contact methods (1:N)     → contact_details table
 └─ Excel import/export (openpyxl)     → .xlsx file stream
        │
        ▼
   SQLite data/contacts.db
```

`contacts(id, name, favorite, notes, created_at)` 1:N `contact_details(id, contact_id, type, value)`. The `type` column is constrained by a CHECK to `phone / email / social / address`, and deleting a contact cascades to all its details.

## 4. Implementation Ideas

### 4.1 Bookmark Contacts (25 points)

**Idea**: a 0/1 `favorite` field plus a star button on the frontend. Clicking the star sends `PATCH /api/contacts/<id>/favorite` to toggle the state, then the list is refreshed. The list is ordered by `favorite DESC`, and bookmarked contacts are shown in the golden "Frequent Contacts" quick-access cards at the top; clicking a card opens the edit dialog directly.

Key backend code:

```python
@app.patch("/api/contacts/<int:contact_id>/favorite")
def toggle_favorite(contact_id):
    ...
    new_value = 0 if row["favorite"] else 1
    conn.execute("UPDATE contacts SET favorite = ? WHERE id = ?", (new_value, contact_id))
```

![Home page: frequent-contacts quick-access area and all contact cards](IMG_HOME)

### 4.2 Multiple Contact Methods (10 points)

**Idea**: one contact maps to N rows of `contact_details` in four types (phone / email / social / address). The edit dialog adds rows dynamically via "＋Phone / ＋Email / ＋Social / ＋Address" chips; each row is a type dropdown + value input + delete button. On save, the frontend filters out empty rows and the backend rewrites all details of the contact via `save_details()`.

Key backend code:

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

![Edit dialog: dynamic multi-contact-method rows](IMG_EDIT)

### 4.3 Import and Export (25 points)

**Export idea**: before writing the sheet, scan all contacts and compute the maximum count of each contact-method type, then generate dynamic headers `Phone1, Phone2…, Email1…, Social1…, Address1…`. This guarantees "one row per contact, one column per piece of information" without wasting blank columns. An extra "Import Template" worksheet is generated with a sample row to reduce import mistakes.

**Import idea**: headers are classified by regular expressions (`电话|手机→phone`, `邮箱→email`, `社交|微信|QQ→social`, `地址→address`, plus `姓名 / 收藏 / 备注` handled separately), then rows are read one by one. The name is required; the favorite column accepts `是/1/true/★/√`; empty rows are skipped and counted as `skipped`.

Key code (header classification):

```python
HEADER_TYPE_PATTERNS = [
    (re.compile(r"电话|手机|tel|phone", re.I), "phone"),
    (re.compile(r"邮箱|email|邮件", re.I), "email"),
    (re.compile(r"社交|微信|qq|social", re.I), "social"),
    (re.compile(r"地址|address", re.I), "address"),
]
```

The exported Excel actually looks like this (opened after exporting):

| Name | Favorite | Notes | Phone1 | Phone2 | Email1 | Social1 | Address1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 张伟 (Zhang Wei) | Yes | College roommate · monitor | 13800138000 | 0591-88088088 | zhangwei@fzu.edu.cn | WeChat: zhangwei_fzu | No.5 Gongye Rd, Fuzhou |
| 李娜 (Li Na) | Yes | SE course leader | 13912345678 | | lina@stu.fzu.edu.cn | | Xueyuan Rd, Minhou |
| 孙尚香 (Sun Shangxiang) | | Classmate | 13677778888 | 0591-62228888 | sunshx@stu.fzu.edu.cn | | |

![After importing the Excel, Zhao Yun and Sun Shangxiang appear and the favorite flag is recognized](IMG_IMPORT)

### 4.4 Extra Feature: Search

Fuzzy search across the name, notes and **any contact method** (JOIN on the detail table). Typing a fragment of a phone number or a WeChat ID can locate the person:

```sql
SELECT DISTINCT c.* FROM contacts c
LEFT JOIN contact_details d ON d.contact_id = c.id
WHERE c.name LIKE ? OR c.notes LIKE ? OR d.value LIKE ?
ORDER BY c.favorite DESC, c.name COLLATE NOCASE
```

![Searching "微信" matches both WeChat and WeCom entries](IMG_SEARCH)

## 5. How to Run

```bash
git clone https://github.com/chenlinghan82-debug/cloud-addressbook
cd cloud-addressbook/addressbook
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000 in the browser
```

## 6. Screenshots

| Screenshot | Description |
| --- | --- |
| IMG_HOME | Home page: frequent-contacts area + all contact cards |
| IMG_EDIT | Edit dialog: dynamic multiple contact methods |
| IMG_SEARCH | Fuzzy search on any contact method |
| IMG_IMPORT | New contacts after Excel import |

## 7. Complete Running Video

**A 16-second demo video covering bookmark toggle, dynamic multi-contact editing and search:**

<!--VIDEO_NOTE-->

## 8. Individual Development Process & Difficulties Solved

This project was completed **individually** — no team division; my contribution ratio is 100%.

### 8.1 Difficulties Encountered and How They Were Resolved

1. **Dynamic columns for "one row per contact" in Excel**: different people have different numbers of contact methods, so fixed columns are either insufficient or wasted.
   Solution: before exporting, scan all contacts and compute the maximum count per type, then generate `Phone1…PhoneN` headers dynamically; on import, headers are classified by regex instead of fixed column positions.
2. **The modal was visible on page load**: the CSS rule `.modal-mask { display: grid }` overrode the HTML `hidden` attribute, so the dialog appeared immediately.
   Solution: a global `[hidden] { display: none !important; }` fallback rule (a classic browser-default-style priority pitfall).
3. **Round-trip consistency of import/export**: I worried that "export then import" would lose data.
   Solution: wrote an automated self-test script `docs/selftest.py` that re-imports the exported file and verifies that all 3 contacts are inserted and Zhang Wei's 5 contact details survive intact, before calling it done.
4. **Favorite ordering and Chinese sorting**: SQLite's default order is not friendly to Chinese names.
   Solution: `ORDER BY favorite DESC, name COLLATE NOCASE`; avatar colors are hashed from the name, so they stay stable across re-renders.

### 8.2 XP (Extreme Programming) Practice Reflections

- **Small releases**: 4 commits correspond to "backend → frontend → docs → standard"; every commit can build and run independently, which matches XP's continuous integration idea.
- **Test first**: after each feature I ran interface-level regression with `selftest.py` immediately instead of manual clicking at the end.
- **Simple design**: only two database tables and a zero-framework frontend — just enough for the current need ("do the simplest thing that could possibly work").
- **Coding standard**: wrote `docs/CODE_STANDARD.md` before coding; parameterized SQL and `escapeHtml` anti-XSS were agreed in the standard in advance.

## 9. PSP Table

| Personal Software Process Stages | Estimated Time (min) | Actual Time (min) |
| --- | --- | --- |
| Planning | 20 | 15 |
| · Estimate how much time this task will take | 20 | 15 |
| Development | 330 | 355 |
| · Requirement analysis (including learning new techniques) | 30 | 35 |
| · Generate design document (data model, API design) | 30 | 25 |
| · Design review (with teammate / self review) | 15 | 10 |
| · Coding standard (set up a suitable standard for this project) | 15 | 10 |
| · Detailed design | 25 | 30 |
| · Detailed coding | 150 | 175 |
| · Code review | 20 | 15 |
| · Testing (self test, fix code, commit changes) | 45 | 55 |
| Report | 60 | 70 |
| · Test report | 15 | 20 |
| · Size measurement (workload calculation) | 10 | 5 |
| · Postmortem and process improvement plan | 35 | 45 |
| **Total** | **410** | **440** |

## 10. Summary

In this assignment I built a complete address book with bookmark contacts, multiple contact methods and Excel import/export using Flask + SQLite + openpyxl + vanilla frontend, and went through the full workflow of design → coding → self-testing → committing → review. The biggest gain was **solving the "one row per contact" Excel structure problem with dynamic column design**, and I also hit the real-world pitfall of CSS `hidden` attribute priority. Next steps: deploy the project to a cloud server for the optional 15 points, and add avatar upload and vCard export.

---

*Thanks for reviewing!*
