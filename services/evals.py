# services/evals.py
from __future__ import annotations
import sqlite3, json, uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "users.db"   # reuse same DB file

#----------------------
#admin dash
#-------------------------

def _column_exists(cx, table: str, col: str) -> bool:
    rows = ccx.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == col for r in rows)

def migrate_eval_db() -> None:
    with _conn() as cx:
        if not _column_exists(cx, "property_evals", "admin_notes"):
            cx.execute("ALTER TABLE property_evals ADD COLUMN admin_notes TEXT")
        if not _column_exists(cx,"property_evals","update_at"):
            cx.execute("ALTER TABLE property_evals ADD COLUMN updated_at TEXT")
        cx.commit
            


def list_all_property_evals(limit: int = 100, status: str | None = None):
    with _conn() as cx:
        if status:
            rows = cx.execute(
                "SELECT id, user_id, status, created_at, payload, admin_notes "
                "FROM property_evals WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = cx.execute(
                "SELECT id, user_id, status, created_at, payload, admin_notes "
                "FROM property_evals ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [
        {
            "id": r[0],
            "user_id": r[1],
            "status": r[2],
            "created_at": r[3],
            "payload": json.loads(r[4]),
            "admin_notes": r[5] or "",
        }
        for r in rows
    ]


def update_property_eval_status(eval_id: int, status: str):
    try:
        with _conn() as cx:
            cx.execute("UPDATE property_evals SET status = ? WHERE id = ?", (status, eval_id))
            cx.commit()
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def update_property_eval_notes(eval_id: int, notes: str):
    try:
        with _conn() as cx:
            cx.execute("UPDATE property_evals SET admin_notes = ? WHERE id = ?", (notes, eval_id))
            cx.commit()
        return {"ok": True, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}



def _conn():
    return sqlite3.connect(DB_PATH)

def init_eval_db() -> None:
    with _conn() as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS property_evals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',     -- new / in_progress / done
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL                   -- JSON blob (address, toggles, notes, upload paths)
            )
        """)
        cx.commit()

migrate_eval_db()


def save_uploads(files: List) -> List[str]:
    """Save uploaded files to data/uploads/<uuid>_<orig_name>; return relative paths."""
    saved = []
    for f in files or []:
        if f is None:
            continue
        suffix = f.name.split(".")[-1] if "." in f.name else ""
        fname = f"{uuid.uuid4().hex}_{f.name}"
        target = UPLOAD_DIR / fname
        with open(target, "wb") as out:
            out.write(f.getvalue())
        saved.append(str(target))
    return saved

def create_property_eval(user_id: int, payload: Dict[str, Any], uploaded_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return {'ok': bool, 'id': int|None, 'error': str|None}."""
    payload = dict(payload)  # shallow copy
    if uploaded_paths:
        payload["uploads"] = uploaded_paths
    try:
        with _conn() as cx:
            cx.execute(
                "INSERT INTO property_evals (user_id, status, created_at, payload) VALUES (?, ?, ?, ?)",
                (user_id, "new", datetime.utcnow().isoformat(), json.dumps(payload)),
            )
            eval_id = cx.execute("SELECT last_insert_rowid()").fetchone()[0]
            cx.commit()
        return {"ok": True, "id": eval_id, "error": None}
    except Exception as e:
        return {"ok": False, "id": None, "error": str(e)}

def list_property_evals(user_id: int, limit: int = 20):
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, status, created_at, payload, admin_notes, updated_at "
            "FROM property_evals WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [
        {
            "id": r[0],
            "status": r[1],
            "created_at": r[2],
            "payload": json.loads(r[3]),
            "admin_notes": r[4] or "",
            "updated_at": r[5] or "",
        }
        for r in rows
    ]

