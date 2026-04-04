import html
import sqlite3
import hashlib
from typing import Any

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="UPS System")

DB_FILE = "ups.db"

MODULES = [
    ("dashboard", "Dashboard"),
    ("clients", "Clients"),
    ("vendors", "Vendors"),
    ("technicians", "Technicians"),
    ("sites", "Sites"),
    ("tickets", "Tickets"),
    ("work_orders", "Work Orders"),
    ("trips", "Trips"),
    ("hr", "HR"),
    ("employees", "Employees"),
    ("payroll", "Payroll"),
    ("accounting", "Accounting"),
    ("journal", "Journal"),
    ("trial_balance", "Trial Balance"),
    ("income_statement", "Income Statement"),
    ("reports", "Reports"),
    ("users", "Users"),
    ("settings", "Settings"),
]

MODULE_LABELS = {key: label for key, label in MODULES}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            module_key TEXT NOT NULL
        )
        """
    )

    admin = cur.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",),
    ).fetchone()

    if not admin:
        cur.execute(
            "INSERT INTO users (username, full_name, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
            ("admin", "System Admin", hash_password("admin123"), "admin", 1),
        )

    admin_modules = cur.execute(
        "SELECT COUNT(*) FROM user_modules WHERE username = ?",
        ("admin",),
    ).fetchone()[0]

    if admin_modules == 0:
        for module_key, _ in MODULES:
            cur.execute(
                "INSERT INTO user_modules (username, module_key) VALUES (?, ?)",
                ("admin", module_key),
            )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


def current_user(request: Request):
    username = request.cookies.get("ups_user", "").strip()
    if not username:
        return None

    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username,),
    ).fetchone()
    conn.close()
    return user


def require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


def require_admin(request: Request):
    user = require_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def get_user_modules(username: str) -> list[str]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT module_key FROM user_modules WHERE username = ?",
        (username,),
    ).fetchall()
    conn.close()
    return [row["module_key"] for row in rows]


def user_has_module(user: sqlite3.Row, module_key: str) -> bool:
    if user["role"] == "admin":
        return True
    return module_key in get_user_modules(user["username"])


def require_module(request: Request, module_key: str):
    user = require_user(request)
    if not user_has_module(user, module_key):
        raise HTTPException(status_code=403, detail="Access denied")
    return user


def login_page_html(error: str = "") -> str:
    error_html = f'<div class="alert alert-error">{esc(error)}</div>' if error else ""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Login - UPS System</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                min-height: 100vh;
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #0f172a, #1d4ed8);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .shell {{
                width: 100%;
                max-width: 980px;
                min-height: 560px;
                display: grid;
                grid-template-columns: 1.1fr .9fr;
                background: #ffffff;
                border-radius: 26px;
                overflow: hidden;
                box-shadow: 0 28px 80px rgba(0,0,0,.28);
            }}
            .left {{
                background: linear-gradient(135deg, #1e3a8a, #0f172a);
                color: white;
                padding: 42px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .badge {{
                display: inline-block;
                background: rgba(255,255,255,.14);
                padding: 10px 14px;
                border-radius: 999px;
                font-size: 14px;
                margin-bottom: 18px;
            }}
            .title {{
                font-size: 42px;
                font-weight: 700;
                line-height: 1.15;
            }}
            .sub {{
                font-size: 18px;
                opacity: .92;
                margin-top: 14px;
            }}
            .right {{
                padding: 44px 38px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .logo {{
                width: 92px;
                height: 92px;
                border-radius: 20px;
                background: #e0e7ff;
                color: #1d4ed8;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 30px;
                font-weight: 700;
                margin-bottom: 20px;
            }}
            .form-title {{
                font-size: 30px;
                font-weight: 700;
                margin-bottom: 8px;
                color: #111827;
            }}
            .form-sub {{
                color: #6b7280;
                margin-bottom: 24px;
            }}
            .field {{
                margin-bottom: 14px;
            }}
            .field label {{
                display: block;
                margin-bottom: 6px;
                font-weight: 700;
                color: #374151;
            }}
            .field input {{
                width: 100%;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 13px 14px;
                font-size: 15px;
            }}
            .btn {{
                width: 100%;
                border: none;
                border-radius: 12px;
                padding: 14px;
                background: #2563eb;
                color: white;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                margin-top: 8px;
            }}
            .alert {{
                padding: 12px 14px;
                border-radius: 12px;
                margin-bottom: 16px;
            }}
            .alert-error {{
                background: #fee2e2;
                color: #991b1b;
            }}
            .hint {{
                margin-top: 18px;
                color: #6b7280;
                font-size: 14px;
            }}
            @media (max-width: 900px) {{
                .shell {{
                    grid-template-columns: 1fr;
                    margin: 18px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="shell">
            <div class="left">
                <div>
                    <div class="badge">Ultra Power Solutions</div>
                    <div class="title">UPS System</div>
                    <div class="sub">Login with your username and password to access your modules.</div>
                </div>
                <div style="font-size:14px;opacity:.9;">
                    Dashboard • Users • Permissions • Modules
                </div>
            </div>
            <div class="right">
                <div class="logo">UPS</div>
                <div class="form-title">Sign In</div>
                <div class="form-sub">Enter your account details.</div>
                {error_html}
                <form method="post" action="/login">
                    <div class="field">
                        <label>Username</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="field">
                        <label>Password</label>
                        <input type="password" name="password" required>
                    </div>
                    <button class="btn" type="submit">Login</button>
                </form>
                <div class="hint">Default admin: admin / admin123</div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    user = current_user(request)
    if user:
        return RedirectResponse(url="/ui", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_get():
    return HTMLResponse(login_page_html())


@app.post("/login", response_class=HTMLResponse)
def login_post(username: str = Form(...), password: str = Form(...)):
    conn = get_conn()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username.strip(),),
    ).fetchone()

    if not user or user["password_hash"] != hash_password(password):
        conn.close()
        return HTMLResponse(login_page_html("Invalid username or password"), status_code=401)

    response = RedirectResponse(url="/ui", status_code=303)
    response.set_cookie("ups_user", user["username"], httponly=True, samesite="lax")

    conn.close()
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("ups_user")
    return response
from fastapi import FastAPI

app = FastAPI()
def allowed_module_keys(user: sqlite3.Row) -> list[str]:
    if user["role"] == "admin":
        return [key for key, _ in MODULES]
    return get_user_modules(user["username"])


def nav_html(active: str, user: sqlite3.Row) -> str:
    allowed = set(allowed_module_keys(user))
    items = []

    if "dashboard" in allowed:
        cls = "side-link active" if active == "dashboard" else "side-link"
        items.append(f'<a class="{cls}" href="/ui">Dashboard</a>')

    for module_key, module_label in MODULES:
        if module_key in {"dashboard", "users", "settings"}:
            continue
        if module_key not in allowed:
            continue
        cls = "side-link active" if active == module_key else "side-link"
        items.append(f'<a class="{cls}" href="/ui/module/{module_key}">{esc(module_label)}</a>')

    if "users" in allowed or user["role"] == "admin":
        cls = "side-link active" if active == "users" else "side-link"
        items.append(f'<a class="{cls}" href="/ui/users">Users</a>')

    if "settings" in allowed:
        cls = "side-link active" if active == "settings" else "side-link"
        items.append(f'<a class="{cls}" href="/ui/module/settings">Settings</a>')

    items.append('<a class="side-link logout-link" href="/logout">Logout</a>')
    return "".join(items)


def page_html(title: str, body: str, user: sqlite3.Row, active: str = "dashboard") -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>{esc(title)}</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Inter, Arial, sans-serif;
                background: #f6f7fb;
                color: #1f2937;
            }}

            .app-shell {{
                display: flex;
                min-height: 100vh;
            }}

            .sidebar {{
                width: 250px;
                background: linear-gradient(180deg, #5b2c87 0%, #4a246f 100%);
                color: white;
                padding: 18px 14px;
                display: flex;
                flex-direction: column;
                gap: 14px;
                box-shadow: 2px 0 18px rgba(0,0,0,.08);
            }}

            .brand-box {{
                padding: 10px 12px 4px 12px;
            }}

            .brand-title {{
                font-size: 28px;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 4px;
            }}

            .brand-sub {{
                font-size: 13px;
                opacity: .88;
            }}

            .user-card {{
                background: rgba(255,255,255,.10);
                border: 1px solid rgba(255,255,255,.12);
                border-radius: 16px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.7;
            }}

            .side-nav {{
                display: flex;
                flex-direction: column;
                gap: 8px;
                overflow: auto;
                padding-right: 2px;
            }}

            .side-link {{
                display: block;
                text-decoration: none;
                color: white;
                padding: 12px 14px;
                border-radius: 12px;
                background: rgba(255,255,255,.06);
                transition: .2s ease;
                font-size: 14px;
                font-weight: 600;
            }}

            .side-link:hover {{
                background: rgba(255,255,255,.14);
                transform: translateX(2px);
            }}

            .side-link.active {{
                background: white;
                color: #4a246f;
            }}

            .logout-link {{
                margin-top: 10px;
                background: rgba(220,38,38,.18);
            }}

            .main-area {{
                flex: 1;
                display: flex;
                flex-direction: column;
                min-width: 0;
            }}

            .topbar {{
                height: 68px;
                background: white;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 24px;
                position: sticky;
                top: 0;
                z-index: 20;
            }}

            .topbar-left {{
                display: flex;
                align-items: center;
                gap: 14px;
            }}

            .apps-btn {{
                background: #f3e8ff;
                color: #6b21a8;
                border: none;
                border-radius: 12px;
                padding: 10px 14px;
                font-weight: 700;
                cursor: pointer;
            }}

            .breadcrumb {{
                font-size: 14px;
                color: #6b7280;
            }}

            .topbar-right {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}

            .lang-btn, .user-pill {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: 600;
                color: #374151;
            }}

            .content {{
                padding: 26px;
            }}

            .page-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 22px;
                flex-wrap: wrap;
            }}

            .page-title {{
                font-size: 34px;
                font-weight: 800;
                margin: 0;
                color: #111827;
            }}

            .page-sub {{
                color: #6b7280;
                margin-top: 6px;
                font-size: 14px;
            }}

            .apps-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                gap: 18px;
            }}

            .app-card {{
                background: white;
                border: 1px solid #ececf3;
                border-radius: 20px;
                padding: 22px;
                box-shadow: 0 10px 24px rgba(15,23,42,.05);
                transition: .2s ease;
                text-decoration: none;
                color: inherit;
            }}

            .app-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 16px 34px rgba(15,23,42,.09);
            }}

            .app-icon {{
                width: 54px;
                height: 54px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #ede9fe, #f3e8ff);
                color: #6b21a8;
                font-size: 20px;
                font-weight: 800;
                margin-bottom: 16px;
            }}

            .app-title {{
                font-size: 28px;
                font-weight: 800;
                line-height: 1.1;
                margin-bottom: 8px;
                color: #1f2937;
            }}

            .app-desc {{
                color: #6b7280;
                font-size: 14px;
            }}

            .module-panel {{
                background: white;
                border: 1px solid #ececf3;
                border-radius: 20px;
                padding: 26px;
                box-shadow: 0 10px 24px rgba(15,23,42,.05);
            }}

            .module-panel h2 {{
                margin-top: 0;
                font-size: 28px;
            }}

            .module-panel p {{
                color: #6b7280;
                font-size: 15px;
            }}

            .table-card, .form-box {{
                background: white;
                border-radius: 20px;
                border: 1px solid #ececf3;
                box-shadow: 0 10px 24px rgba(15,23,42,.05);
            }}

            .form-box {{
                max-width: 920px;
                padding: 24px;
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
                border-radius: 12px;
                padding: 11px 16px;
                text-decoration: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 700;
            }}

            .btn-primary {{
                background: #7c3aed;
                color: white;
            }}

            .btn-warning {{
                background: #f59e0b;
                color: white;
            }}

            .btn-danger {{
                background: #dc2626;
                color: white;
            }}

            .btn-light {{
                background: #f3f4f6;
                color: #111827;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 20px;
                overflow: hidden;
            }}

            th, td {{
                padding: 15px 14px;
                text-align: left;
                border-bottom: 1px solid #eef2f7;
                vertical-align: top;
                font-size: 14px;
            }}

            th {{
                background: #faf5ff;
                color: #5b21b6;
                font-weight: 800;
            }}

            .field {{
                margin-bottom: 15px;
            }}

            .field label {{
                display: block;
                margin-bottom: 6px;
                font-weight: 700;
                color: #374151;
            }}

            .field input, .field select {{
                width: 100%;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 12px 13px;
                font-size: 14px;
                background: #fff;
            }}

            .modules-box {{
                background: #fafafa;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
                padding: 14px;
                max-height: 320px;
                overflow: auto;
            }}

            .module-item {{
                display: block;
                margin-bottom: 10px;
                font-size: 14px;
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
                padding: 20px;
                background: white;
                border-radius: 18px;
                border: 1px solid #ececf3;
                box-shadow: 0 10px 24px rgba(15,23,42,.05);
            }}

            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 12px;
                background: #f3e8ff;
                color: #6b21a8;
                margin: 3px 4px 0 0;
                font-weight: 700;
            }}

            @media (max-width: 900px) {{
                .sidebar {{
                    display: none;
                }}
                .content {{
                    padding: 18px;
                }}
                .page-title {{
                    font-size: 28px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="app-shell">
            <aside class="sidebar">
                <div class="brand-box">
                    <div class="brand-title">UPS System</div>
                    <div class="brand-sub">Ultra Power Solutions</div>
                </div>

                <div class="user-card">
                    <div><b>User:</b> {esc(user["username"])}</div>
                    <div><b>Role:</b> {esc(user["role"])}</div>
                </div>

                <div class="side-nav">
                    {nav_html(active, user)}
                </div>
            </aside>

            <div class="main-area">
                <div class="topbar">
                    <div class="topbar-left">
                        <button class="apps-btn" type="button">Apps</button>
                        <div class="breadcrumb">Home / {esc(title)}</div>
                    </div>

                    <div class="topbar-right">
                        <div class="lang-btn">EN | AR</div>
                        <div class="user-pill">{esc(user["username"])}</div>
                    </div>
                </div>

                <div class="content">
                    <div class="page-header">
                        <div>
                            <h1 class="page-title">{esc(title)}</h1>
                            <div class="page-sub">ERP-style modular workspace</div>
                        </div>
                    </div>
                    {body}
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def dashboard_body(user: sqlite3.Row) -> str:
    allowed = allowed_module_keys(user)

    cards = []
    for module_key in allowed:
        label = MODULE_LABELS.get(module_key, module_key)
        icon = label[:2].upper()
        href = "/ui" if module_key == "dashboard" else f"/ui/module/{module_key}"
        cards.append(
            f"""
            <a class="app-card" href="{href}">
                <div class="app-icon">{esc(icon)}</div>
                <div class="app-title">{esc(label)}</div>
                <div class="app-desc">Open module workspace</div>
            </a>
            """
        )

    return f'<div class="apps-grid">{"".join(cards)}</div>'
@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=302)


def module_page_body(module_key: str) -> str:
    label = MODULE_LABELS.get(module_key, module_key)
    return f"""
    <div class="module-panel">
        <h2>{esc(label)}</h2>
        <p>This module is enabled and ready to be connected to its real screens.</p>
    </div>
    """
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Form, Request

@app.get("/login", response_class=HTMLResponse)
def login_get():
    return """
    <html>
    <head>
        <title>Login</title>
    </head>
    <body style="font-family:Arial; text-align:center; padding-top:100px;">
        <h2>UPS System Login</h2>
        <form method="post" action="/login">
            <input name="username" placeholder="Username"/><br><br>
            <input name="password" type="password" placeholder="Password"/><br><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin123":
        response = RedirectResponse(url="/ui", status_code=302)
        response.set_cookie("ups_user", username)
        return response

    return HTMLResponse("Invalid login", status_code=401)
@app.get("/ui", response_class=HTMLResponse)
def ui_dashboard(request: Request):
    username = request.cookies.get("ups_user")
    if not username:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if not user:
        return RedirectResponse(url="/login", status_code=302)

    body = dashboard_body(user)

    return HTMLResponse(
        page_html(
            title="Dashboard",
            body=body,
            user=user,
            active="dashboard"
        )
    )