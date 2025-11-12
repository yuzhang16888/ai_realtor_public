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

def list_property_evals(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with _conn() as cx:
        rows = cx.execute(
            "SELECT id, status, created_at, payload FROM property_evals WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    res = []
    for r in rows:
        res.append({
            "id": r[0],
            "status": r[1],
            "created_at": r[2],
            "payload": json.loads(r[3]),
        })
    return res
