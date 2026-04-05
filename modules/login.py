from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from db import get_conn

router = APIRouter()

def login_page(error: str = ""):
    error_html = f"<div class='login-error'>{error}</div>" if error else ""
    return f"""
    <html>
    <head>
        <title>Login</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body class="login-body">
        <div class="login-shell">
            <div class="login-left">
                <div>
                    <div class="login-badge">Ultra Power Solutions</div>
                    <h1>UPS System</h1>
                    <p>Secure access to your ERP modules.</p>
                </div>
            </div>

            <div class="login-right">
                <div class="login-box">
                    <div class="login-logo">UPS</div>
                    <h2>Sign In</h2>
                    <p class="login-sub">Enter your account details</p>
                    {error_html}

                    <form method="post" action="/login">
                        <label>Username</label>
                        <input type="text" name="username" required>

                        <label>Password</label>
                        <input type="password" name="password" required>

                        <button type="submit">Login</button>
                    </form>

                    <div class="login-hint">Default admin: admin / admin123</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    username = request.cookies.get("ups_user")
    if username:
        return RedirectResponse(url="/ui", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
def login_get():
    return HTMLResponse(login_page())

@router.post("/login", response_class=HTMLResponse)
def login_post(username: str = Form(...), password: str = Form(...)):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.strip(), password)
    ).fetchone()
    conn.close()

    if not user:
        return HTMLResponse(login_page("Invalid username or password"), status_code=401)

    response = RedirectResponse(url="/ui", status_code=303)
    response.set_cookie("ups_user", user["username"], httponly=True, samesite="lax")
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("ups_user")
    return response