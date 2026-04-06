from fastapi import Request
from db import get_conn
from settings import COOKIE_NAME


def current_user(request: Request):
    username = request.cookies.get(COOKIE_NAME)
    if not username:
        return None

    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    return user


def get_user_modules(username: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT module_name FROM user_permissions WHERE username = ?",
        (username,)
    ).fetchall()
    conn.close()

    return [r["module_name"] for r in rows]