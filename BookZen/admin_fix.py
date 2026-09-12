
from flask import request, redirect, url_for, render_template, session
import sqlite3

DB_NAME = r"C:\Users\LENOVO\Desktop\BookZen\bookzen.db"


def setup_admin():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    admin = conn.execute(
        "SELECT id FROM admins WHERE email=?",
        ("admin@bookzen.com",)
    ).fetchone()

    if not admin:
        conn.execute(
            """
            INSERT INTO admins(name,email,password)
            VALUES(?,?,?)
            """,
            (
                "BookZen Admin",
                "admin@bookzen.com",
                "admin123"
            )
        )

    conn.commit()
    conn.close()


setup_admin()

print("====================================")
print("BOOKZEN ADMIN ACCOUNT READY")
print("====================================")
print("Email    : admin@bookzen.com")
print("Password : admin123")
print("Database : bookzen.db")
print("====================================")
