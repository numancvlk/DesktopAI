# LIBRARIES
import datetime
import sqlite3
from pathlib import Path
from typing import List

from .config import get_settings


def get_db_path() -> str:
    return get_settings().memory_db_path


def init_db() -> None:
    dbPath = get_db_path()
    Path(dbPath).parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                createdAt TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    except:
        raise RuntimeError("Database error")


def get_last_messages(limit: int = 5) -> List[dict]:
    dbPath = get_db_path()
    try:
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT role, content
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        result = [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]
        return result
    except:
        return []


def append_message(role: str, content: str) -> None:
    dbPath = get_db_path()
    createdAt = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            INSERT INTO conversations (role, content, createdAt)
            VALUES (?, ?, ?)
            """,
            (role.strip(), content.strip(), createdAt),
        )
        conn.commit()
        conn.close()
    except:
        raise RuntimeError("Hafiza yazilmadi")
