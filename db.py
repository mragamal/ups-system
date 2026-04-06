import sqlite3
from settings import DB_NAME

DB = DB_NAME


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            module_name TEXT NOT NULL
        )
    """)

    admin = cur.execute(
        "SELECT * FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    default_modules = ["dashboard", "clients", "inventory", "users", "accounting"]

    for module_name in default_modules:
        exists = cur.execute(
            "SELECT id FROM user_permissions WHERE username = ? AND module_name = ?",
            ("admin", module_name)
        ).fetchone()

        if not exists:
            cur.execute(
                "INSERT INTO user_permissions (username, module_name) VALUES (?, ?)",
                ("admin", module_name)
            )

    conn.commit()
    conn.close()