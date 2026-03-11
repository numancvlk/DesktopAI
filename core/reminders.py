#LIBRARIES
import datetime
import sqlite3
from typing import List, Optional, Dict, Any
from .memory import get_db_path


def init_reminders_table() -> None:
    dbPath = get_db_path()

    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                dueAt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                repeatRule TEXT,
                createdAt TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    except Exception:
        raise RuntimeError("Hatirlayici tablosu olusturulamadi")


def create_reminder(
    text: str,
    due_at: datetime.datetime,
    repeat_rule: Optional[str] = None,
) -> int:

    dbPath = get_db_path()

    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    due_at_str = due_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        conn = sqlite3.connect(dbPath)
        cursor = conn.execute(
            """
            INSERT INTO reminders (text, dueAt, status, repeatRule, createdAt)
            VALUES (?, ?, 'pending', ?, ?)
            """,
            (text.strip(), due_at_str, repeat_rule, created_at),
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return int(reminder_id)
    except Exception:
        raise RuntimeError("Hatirlayici kaydedilemedi")


def get_due_reminders(now: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
    if now is None:
        now = datetime.datetime.utcnow()

    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    dbPath = get_db_path()

    try:
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, text, dueAt, status, repeatRule, createdAt
            FROM reminders
            WHERE status = 'pending' AND dueAt <= ?
            ORDER BY dueAt ASC
            """,
            (now_str,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row["id"],
                "text": row["text"],
                "dueAt": row["dueAt"],
                "status": row["status"],
                "repeatRule": row["repeatRule"],
                "createdAt": row["createdAt"],
            }
            for row in rows
        ]
    except Exception:
        raise RuntimeError("Hatirlayicilar okunamadi")


def mark_reminder_done(reminder_id: int) -> None:
    dbPath = get_db_path()
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            UPDATE reminders
            SET status = 'done'
            WHERE id = ?
            """,
            (int(reminder_id),),
        )
        conn.commit()
        conn.close()
    except Exception:
        raise RuntimeError("Hatirlayici guncellenemedi")


def reschedule_reminder(reminder_id: int, new_due_at: datetime.datetime) -> None:
    dbPath = get_db_path()
    due_at_str = new_due_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            UPDATE reminders
            SET dueAt = ?, status = 'pending'
            WHERE id = ?
            """,
            (due_at_str, int(reminder_id)),
        )
        conn.commit()
        conn.close()
    except Exception:
        raise RuntimeError("Hatirlayici yeniden zamanlanamadi")

def get_all_reminders(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    dbPath = get_db_path()
    query = """
        SELECT id, text, dueAt, status, repeatRule, createdAt
        FROM reminders
        ORDER BY dueAt DESC
    """
    params: tuple[Any, ...] = ()

    if isinstance(limit, int) and limit > 0:
        query += " LIMIT ?"
        params = (limit,)

    try:
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "id": row["id"],
                "text": row["text"],
                "dueAt": row["dueAt"],
                "status": row["status"],
                "repeatRule": row["repeatRule"],
                "createdAt": row["createdAt"],
            }
            for row in rows
        ]
    except Exception:
        raise RuntimeError("Hatirlayicilar listelenemedi")

