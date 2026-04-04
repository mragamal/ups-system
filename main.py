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