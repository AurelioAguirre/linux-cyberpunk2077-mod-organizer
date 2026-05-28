from __future__ import annotations
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "resources" / "mods.db"

_CREATE_MODS = """
CREATE TABLE IF NOT EXISTS mods (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    install_date TEXT NOT NULL,
    active       INTEGER NOT NULL DEFAULT 1
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(_CREATE_MODS)
    log.debug("Database ready at %s", DB_PATH)


def record_mod(name: str) -> int:
    """Insert a mod record and return its new id."""
    install_date = datetime.now().isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO mods (name, install_date, active) VALUES (?, ?, 1)",
            (name, install_date),
        )
        mod_id = cursor.lastrowid
    log.debug("Recorded mod '%s' (id=%d)", name, mod_id)
    return mod_id


def set_active(mod_id: int, active: bool) -> None:
    with _connect() as conn:
        conn.execute("UPDATE mods SET active = ? WHERE id = ?", (int(active), mod_id))
    log.debug("Mod id=%d active=%s", mod_id, active)


def get_all_mods() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT id, name, install_date, active FROM mods ORDER BY install_date DESC"
        ).fetchall()


def remove_mod(mod_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM mods WHERE id = ?", (mod_id,))
    log.debug("Removed mod id=%d", mod_id)
