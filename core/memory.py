# LIBRARIES
import datetime
import sqlite3
from pathlib import Path
from typing import List
from .config import get_settings
from . import user_modes


def get_db_path() -> str: #DATABASE yolunu configden aliyoruz
    return get_settings().memory_db_path


def init_db() -> None: #UI gelirken bunu cagiricaz ki database tablosu olussun
    dbPath = get_db_path()
    Path(dbPath).parent.mkdir(parents=True, exist_ok=True) #db dosyasi yoksa olusturuyoruz

    try:
        conn = sqlite3.connect(dbPath)
        conn.execute( #sohbet gecmisi tablosu
            """
            CREATE TABLE IF NOT EXISTS conversations ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                createdAt TEXT NOT NULL
            )
            """
        )
        conn.execute( #hatirlatici tablosu
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

        user_modes.init_modes_table()

    except:
        raise RuntimeError("Database error")


def get_last_messages(limit: int = 5) -> List[dict]: #SON 5 MESAJI CEKIYORUZ
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
        result = [ #burda reverse yapmazsam son mesaj en basa geliyor 
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]
        return result
    except:
        return [] #hata olursa bos liste donucem uygulama cokmesin yikilmadim ayaktayimmm


def append_message(role: str, content: str) -> None: #YENI SOHBETLER GELDIKCE DATABASE E EKLIYOZ
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
