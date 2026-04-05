from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from layout import render_page
from db import get_conn
from auth import current_user

router = APIRouter()

AVAILABLE_MODULES = [
    ("dashboard", "Dashboard"),
    ("clients", "Clients"),
    ("users", "Users"),
]

def build_users_content(message: str = "") -> str:
    conn = get_conn()

    users = conn.execute(
        "SELECT id, username, role FROM users ORDER BY id DESC"
    ).fetchall()

    user_rows = []
    for user in users:
        perms = conn.execute(
            "SELECT module_name FROM user_permissions WHERE username = ?",
            (user["username"],)
        ).fetchall()

        perms_text = ", ".join([p["module_name"] for p in perms]) if perms else "-"

        user_rows.append(f"""
            <tr>
                <td>{user["username"]}</td>
                <td>{user["role"]}</td>
                <td>{perms_text}</td>
            </tr>
        """)

    conn.close()

    checks = ""
    for key, label in AVAILABLE_MODULES:
        checks += f"""
            <label style="display:block; margin-bottom:8px;">
                <input type="checkbox" name="modules" value="{key}">
                {label}
            </label>
        """

    msg_html = ""
    if message:
        msg_html = f"""
            <div style="
                background:#dcfce7;
                color:#166534;
                padding:12px 14px;
                border-radius:12px;
                margin-bottom:18px;
                font-weight:600;
            ">
                {message}
            </div>
        """

    return f"""
        <h1>Users</h1>
        <p>Users and permissions module</p>

        {msg_html}

        <div style="display:grid; grid-template-columns: 380px 1fr; gap:24px; align-items:start;">

            <div class="card">
                <div class="card-title">Add User</div>
                <div class="card-desc" style="margin-bottom:16px;">Create user and choose modules</div>

                <form method="post" action="/ui/users/create">
                    <div style="margin-bottom:12px;">
                        <label style="display:block; margin-bottom:6px; font-weight:600;">Username</label>
                        <input name="username" required style="width:100%; padding:10px; border:1px solid #d1d5db; border-radius:10px;">
                    </div>

                    <div style="margin-bottom:12px;">
                        <label style="display:block; margin-bottom:6px; font-weight:600;">Password</label>
                        <input type="password" name="password" required style="width:100%; padding:10px; border:1px solid #d1d5db; border-radius:10px;">
                    </div>

                    <div style="margin-bottom:12px;">
                        <label style="display:block; margin-bottom:6px; font-weight:600;">Role</label>
                        <select name="role" style="width:100%; padding:10px; border:1px solid #d1d5db; border-radius:10px;">
                            <option value="user">user</option>
                            <option value="admin">admin</option>
                        </select>
                    </div>

                    <div style="margin-bottom:16px;">
                        <label style="display:block; margin-bottom:8px; font-weight:600;">Modules</label>
                        {checks}
                    </div>

                    <button type="submit" style="
                        background:#2563eb;
                        color:white;
                        border:none;
                        padding:12px 16px;
                        border-radius:10px;
                        font-weight:700;
                        cursor:pointer;
                        width:100%;
                    ">
                        Save User
                    </button>
                </form>
            </div>

            <div class="card">
                <div class="card-title">User List</div>
                <div class="card-desc" style="margin-bottom:16px;">All users and their permissions</div>

                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr>
                            <th style="text-align:left; padding:10px; border-bottom:1px solid #e5e7eb;">Username</th>
                            <th style="text-align:left; padding:10px; border-bottom:1px solid #e5e7eb;">Role</th>
                            <th style="text-align:left; padding:10px; border-bottom:1px solid #e5e7eb;">Modules</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(user_rows)}
                    </tbody>
                </table>
            </div>

        </div>
    """

@router.get("/ui/users", response_class=HTMLResponse)
def users_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    content = build_users_content()
    return HTMLResponse(render_page("Users", "users", content, user["username"]))

@router.post("/ui/users/create", response_class=HTMLResponse)
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    modules: list[str] = Form([])
):
    user = current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    conn = get_conn()
    cur = conn.cursor()

    username = username.strip()

    existing = cur.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        conn.close()
        content = build_users_content("Username already exists")
        return HTMLResponse(render_page("Users", "users", content, user["username"]))

    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, password, role)
    )

    for module in modules:
        cur.execute(
            "INSERT INTO user_permissions (username, module_name) VALUES (?, ?)",
            (username, module)
        )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/ui/users", status_code=303)