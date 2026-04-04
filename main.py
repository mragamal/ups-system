import os
import html
import sqlite3
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="UPS System")

DB_FILE = "ups.db"


SECTIONS: dict[str, dict[str, Any]] = {
    "clients": {
        "title": "Clients",
        "table": "clients",
        "fields": [
            ("name", "Name", "text"),
            ("phone", "Phone", "text"),
            ("address", "Address", "text"),
        ],
    },
    "vendors": {
        "title": "Vendors",
        "table": "vendors",
        "fields": [
            ("name", "Name", "text"),
            ("phone", "Phone", "text"),
            ("address", "Address", "text"),
        ],
    },
    "accounts": {
        "title": "Accounts",
        "table": "accounts",
        "fields": [
            ("code", "Code", "text"),
            ("name", "Name", "text"),
            ("account_type", "Type", "text"),
            ("balance", "Balance", "number"),
        ],
    },
    "sites": {
        "title": "Sites",
        "table": "sites",
        "fields": [
            ("name", "Name", "text"),
            ("location", "Location", "text"),
            ("status", "Status", "text"),
        ],
    },
    "tickets": {
        "title": "Tickets",
        "table": "tickets",
        "fields": [
            ("title", "Title", "text"),
            ("client_name", "Client", "text"),
            ("site_name", "Site", "text"),
            ("status", "Status", "text"),
            ("description", "Description", "textarea"),
        ],
    },
    "work_orders": {
        "title": "Work Orders",
        "table": "work_orders",
        "fields": [
            ("ticket_id", "Ticket ID", "number"),
            ("description", "Description", "textarea"),
            ("status", "Status", "text"),
        ],
    },
    "trips": {
        "title": "Trips",
        "table": "trips",
        "fields": [
            ("title", "Title", "text"),
            ("from_location", "From", "text"),
            ("to_location", "To", "text"),
            ("status", "Status", "text"),
            ("cost", "Cost", "number"),
        ],
    },
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT DEFAULT '',
            balance REAL DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT DEFAULT '',
            status TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            client_name TEXT DEFAULT '',
            site_name TEXT DEFAULT '',
            status TEXT DEFAULT '',
            description TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            status TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            from_location TEXT DEFAULT '',
            to_location TEXT DEFAULT '',
            status TEXT DEFAULT '',
            cost REAL DEFAULT 0
        )
        """
    )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def section_exists(section: str) -> None:
    if section not in SECTIONS:
        raise HTTPException(status_code=404, detail="Section not found")


def get_row(section: str, row_id: int) -> sqlite3.Row:
    section_exists(section)
    table = SECTIONS[section]["table"]
    conn = get_conn()
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return row


def get_counts() -> dict[str, int]:
    conn = get_conn()
    counts = {}
    for key, cfg in SECTIONS.items():
        counts[key] = conn.execute(f"SELECT COUNT(*) FROM {cfg['table']}").fetchone()[0]
    conn.close()
    return counts


def nav_html(active: str = "dashboard") -> str:
    links = [
        ("dashboard", "Dashboard", "/ui"),
        ("clients", "Clients", "/ui/clients"),
        ("vendors", "Vendors", "/ui/vendors"),
        ("accounts", "Accounts", "/ui/accounts"),
        ("sites", "Sites", "/ui/sites"),
        ("tickets", "Tickets", "/ui/tickets"),
        ("work_orders", "Work Orders", "/ui/work_orders"),
        ("trips", "Trips", "/ui/trips"),
        ("docs", "API Docs", "/docs"),
    ]
    items = []
    for key, label, href in links:
        cls = "nav-link active" if key == active else "nav-link"
        items.append(f'<a class="{cls}" href="{href}">{label}</a>')
    return "".join(items)


def page_html(title: str, body: str, active: str = "dashboard") -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{esc(title)}</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f3f6fb;
                color: #1f2937;
            }}
            .layout {{
                display: flex;
                min-height: 100vh;
            }}
            .sidebar {{
                width: 250px;
                background: #16335b;
                color: white;
                padding: 24px 18px;
            }}
            .brand {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 24px;
            }}
            .brand small {{
                display: block;
                font-size: 14px;
                font-weight: 400;
                opacity: .85;
                margin-top: 6px;
            }}
            .nav-link {{
                display: block;
                color: white;
                text-decoration: none;
                padding: 12px 14px;
                border-radius: 10px;
                margin-bottom: 8px;
                background: rgba(255,255,255,.05);
            }}
            .nav-link:hover, .nav-link.active {{
                background: rgba(255,255,255,.15);
            }}
            .content {{
                flex: 1;
                padding: 28px;
            }}
            .page-title {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 20px;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 18px;
                margin-bottom: 24px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                padding: 22px;
                box-shadow: 0 8px 20px rgba(0,0,0,.06);
            }}
            .card-number {{
                font-size: 34px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .toolbar {{
                display: flex;
                gap: 10px;
                margin-bottom: 16px;
                flex-wrap: wrap;
            }}
            .btn {{
                display: inline-block;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                text-decoration: none;
                cursor: pointer;
                font-size: 14px;
            }}
            .btn-primary {{ background: #2563eb; color: white; }}
            .btn-warning {{ background: #f59e0b; color: white; }}
            .btn-danger {{ background: #dc2626; color: white; }}
            .btn-light {{ background: #e5e7eb; color: #111827; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 20px rgba(0,0,0,.06);
            }}
            th, td {{
                padding: 14px;
                text-align: left;
                border-bottom: 1px solid #e5e7eb;
                vertical-align: top;
            }}
            th {{
                background: #eef3fb;
            }}
            .form-box {{
                max-width: 760px;
                background: white;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 8px 20px rgba(0,0,0,.06);
            }}
            .field {{
                margin-bottom: 14px;
            }}
            .field label {{
                display: block;
                margin-bottom: 6px;
                font-weight: 700;
            }}
            .field input, .field textarea {{
                width: 100%;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 14px;
            }}
            .field textarea {{
                min-height: 110px;
                resize: vertical;
            }}
            .actions {{
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }}
            .inline-form {{
                display: inline;
            }}
            .empty {{
                padding: 18px;
                background: white;
                border-radius: 14px;
                box-shadow: 0 8px 20px rgba(0,0,0,.06);
            }}
        </style>
    </head>
    <body>
        <div class="layout">
            <aside class="sidebar">
                <div class="brand">
                    UPS System
                    <small>Ultra Power Solutions</small>
                </div>
                {nav_html(active)}
            </aside>
            <main class="content">
                <div class="page-title">{esc(title)}</div>
                {body}
            </main>
        </div>
    </body>
    </html>
    """


def dashboard_body() -> str:
    counts = get_counts()
    cards = []
    for key, cfg in SECTIONS.items():
        cards.append(
            f"""
            <div class="card">
                <div class="card-number">{counts[key]}</div>
                <div>{esc(cfg["title"])}</div>
            </div>
            """
        )
    return f'<div class="cards">{"".join(cards)}</div>'


def list_body(section: str) -> str:
    cfg = SECTIONS[section]
    table = cfg["table"]

    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
    conn.close()

    headers = ["ID"] + [label for _, label, _ in cfg["fields"]] + ["Actions"]

    if not rows:
        return f"""
        <div class="toolbar">
            <a class="btn btn-primary" href="/ui/{section}/new">Add New</a>
        </div>
        <div class="empty">No data found.</div>
        """

    table_rows = []
    for row in rows:
        cols = [f"<td>{row['id']}</td>"]
        for name, _, _ in cfg["fields"]:
            cols.append(f"<td>{esc(row[name])}</td>")

        cols.append(
            f"""
            <td>
                <div class="actions">
                    <a class="btn btn-warning" href="/ui/{section}/{row['id']}/edit">Edit</a>
                    <form class="inline-form" method="post" action="/ui/{section}/{row['id']}/delete">
                        <button class="btn btn-danger" type="submit">Delete</button>
                    </form>
                </div>
            </td>
            """
        )
        table_rows.append("<tr>" + "".join(cols) + "</tr>")

    thead = "".join(f"<th>{esc(h)}</th>" for h in headers)

    return f"""
    <div class="toolbar">
        <a class="btn btn-primary" href="/ui/{section}/new">Add New</a>
    </div>
    <table>
        <thead><tr>{thead}</tr></thead>
        <tbody>
            {"".join(table_rows)}
        </tbody>
    </table>
    """


def form_body(section: str, values: dict[str, Any] | None = None, edit_id: int | None = None) -> str:
    cfg = SECTIONS[section]
    values = values or {}
    title = f"Edit {cfg['title'][:-1]}" if edit_id else f"Add {cfg['title'][:-1]}"
    action = f"/ui/{section}/{edit_id}/edit" if edit_id else f"/ui/{section}/new"

    fields_html = []
    for name, label, field_type in cfg["fields"]:
        val = esc(values.get(name, ""))
        if field_type == "textarea":
            fields_html.append(
                f"""
                <div class="field">
                    <label>{esc(label)}</label>
                    <textarea name="{esc(name)}">{val}</textarea>
                </div>
                """
            )
        else:
            input_type = "number" if field_type == "number" else "text"
            step = ' step="0.01"' if field_type == "number" else ""
            fields_html.append(
                f"""
                <div class="field">
                    <label>{esc(label)}</label>
                    <input type="{input_type}" name="{esc(name)}" value="{val}"{step} />
                </div>
                """
            )

    return f"""
    <div class="form-box">
        <form method="post" action="{action}">
            {"".join(fields_html)}
            <div class="actions">
                <button class="btn btn-primary" type="submit">Save</button>
                <a class="btn btn-light" href="/ui/{section}">Back</a>
            </div>
        </form>
    </div>
    """


@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/ui", status_code=302)


@app.get("/ui", response_class=HTMLResponse)
def ui_dashboard():
    return HTMLResponse(page_html("Dashboard", dashboard_body(), "dashboard"))


@app.get("/ui/{section}", response_class=HTMLResponse)
def ui_list(section: str):
    section_exists(section)
    return HTMLResponse(page_html(SECTIONS[section]["title"], list_body(section), section))


@app.get("/ui/{section}/new", response_class=HTMLResponse)
def ui_new(section: str):
    section_exists(section)
    return HTMLResponse(page_html(f"Add {SECTIONS[section]['title'][:-1]}", form_body(section), section))


@app.post("/ui/{section}/new")
def ui_new_post(
    section: str,
    name: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    code: str = Form(""),
    account_type: str = Form(""),
    balance: float = Form(0),
    location: str = Form(""),
    status: str = Form(""),
    title: str = Form(""),
    client_name: str = Form(""),
    site_name: str = Form(""),
    description: str = Form(""),
    ticket_id: int = Form(0),
    from_location: str = Form(""),
    to_location: str = Form(""),
    cost: float = Form(0),
):
    section_exists(section)
    cfg = SECTIONS[section]
    table = cfg["table"]

    values_map = {
        "name": name,
        "phone": phone,
        "address": address,
        "code": code,
        "account_type": account_type,
        "balance": balance,
        "location": location,
        "status": status,
        "title": title,
        "client_name": client_name,
        "site_name": site_name,
        "description": description,
        "ticket_id": ticket_id,
        "from_location": from_location,
        "to_location": to_location,
        "cost": cost,
    }

    columns = [field_name for field_name, _, _ in cfg["fields"]]
    values = [values_map[col] for col in columns]
    placeholders = ",".join("?" for _ in columns)

    conn = get_conn()
    conn.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/ui/{section}", status_code=303)


@app.get("/ui/{section}/{row_id}/edit", response_class=HTMLResponse)
def ui_edit(section: str, row_id: int):
    row = get_row(section, row_id)
    return HTMLResponse(page_html(f"Edit {SECTIONS[section]['title'][:-1]}", form_body(section, dict(row), row_id), section))


@app.post("/ui/{section}/{row_id}/edit")
def ui_edit_post(
    section: str,
    row_id: int,
    name: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    code: str = Form(""),
    account_type: str = Form(""),
    balance: float = Form(0),
    location: str = Form(""),
    status: str = Form(""),
    title: str = Form(""),
    client_name: str = Form(""),
    site_name: str = Form(""),
    description: str = Form(""),
    ticket_id: int = Form(0),
    from_location: str = Form(""),
    to_location: str = Form(""),
    cost: float = Form(0),
):
    section_exists(section)
    cfg = SECTIONS[section]
    table = cfg["table"]

    values_map = {
        "name": name,
        "phone": phone,
        "address": address,
        "code": code,
        "account_type": account_type,
        "balance": balance,
        "location": location,
        "status": status,
        "title": title,
        "client_name": client_name,
        "site_name": site_name,
        "description": description,
        "ticket_id": ticket_id,
        "from_location": from_location,
        "to_location": to_location,
        "cost": cost,
    }

    columns = [field_name for field_name, _, _ in cfg["fields"]]
    assignments = ", ".join(f"{col} = ?" for col in columns)
    values = [values_map[col] for col in columns] + [row_id]

    conn = get_conn()
    conn.execute(
        f"UPDATE {table} SET {assignments} WHERE id = ?",
        values,
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/ui/{section}", status_code=303)


@app.post("/ui/{section}/{row_id}/delete")
def ui_delete(section: str, row_id: int):
    section_exists(section)
    table = SECTIONS[section]["table"]

    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/ui/{section}", status_code=303)