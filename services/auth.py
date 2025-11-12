# services/auth.py
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from pathlib import Path
import bcrypt
from typing import Optional, Dict, Any

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "users.db"

@dataclass
class User:
    id: int
    email: str
    name: str | None

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db() -> None:
    with _conn() as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT
            )
        """)
        cx.commit()

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def get_user_by_email(email: str) -> Optional[User]:
    with _conn() as cx:
        row = cx.execute("SELECT id, email, name FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        return None
    return User(id=row[0], email=row[1], name=row[2])

def create_user(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Returns {'ok': bool, 'error': str|None}."""
    if not email or not password:
        return {"ok": False, "error": "Email and password required"}
    if get_user_by_email(email):
        return {"ok": False, "error": "Email already registered"}
    pw_hash = _hash_password(password)
    try:
        with _conn() as cx:
            cx.execute(
                "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
                (email.lower().strip(), pw_hash, name),
            )
            cx.commit()
        return {"ok": True, "error": None}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Email already registered"}

def verify_credentials(email: str, password: str) -> Dict[str, Any]:
    """Returns {'ok': bool, 'user': User|None, 'error': str|None}."""
    with _conn() as cx:
        row = cx.execute(
            "SELECT id, email, name, password_hash FROM users WHERE email = ?",
            (email.lower().strip(),)
        ).fetchone()
    if not row:
        return {"ok": False, "user": None, "error": "No account for this email"}
    user = User(id=row[0], email=row[1], name=row[2])
    if _check_password(password, row[3]):
        return {"ok": True, "user": user, "error": None}
    return {"ok": False, "user": None, "error": "Incorrect password"}

# --- New helper functions for Profile update ---
def get_user_by_id(user_id: int) -> Optional[User]:
    """Return user info by id."""
    with _conn() as cx:
        row = cx.execute("SELECT id, email, name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    return User(id=row[0], email=row[1], name=row[2])


def update_user_name(user_id: int, name: Optional[str]) -> Dict[str, Any]:
    """Update the user's name field."""
    try:
        with _conn() as cx:
            cx.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            cx.commit()
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}


