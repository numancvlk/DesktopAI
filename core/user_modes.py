# LIBRARIES
import datetime
import json
import sqlite3
from difflib import get_close_matches
from typing import Any, Dict, List, Optional
from .config import get_settings


def get_db_path() -> str:
    return get_settings().memory_db_path


def init_modes_table() -> None:
    dbPath = get_db_path()
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_modes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                app_names_json TEXT NOT NULL,
                createdAt TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception:
        raise RuntimeError("User modes verıtabanı hatası")


def parse_app(app_names_json: str) -> List[str]:
    if not app_names_json or not app_names_json.strip():
        return []

    try:
        parsed = json.loads(app_names_json)

        if not isinstance(parsed, list):
            return []

        return [str(a).strip() for a in parsed if isinstance(a, str) and a.strip()]
   
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_app(app_names: List[str]) -> str:
    cleaned = [str(a).strip() for a in app_names if a and isinstance(a, str) and str(a).strip()]
    
    return json.dumps(cleaned, ensure_ascii=False)


def create_mode(name: str, app_names: List[str]) -> int:
    dbPath = get_db_path()
    createdAt = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    nameClean = (name or "").strip()
    if not nameClean:
        raise RuntimeError("Mod adi bos olamaz")

    appJson = serialize_app(app_names or [])

    try:
        conn = sqlite3.connect(dbPath)
        cursor = conn.execute(
            """
            INSERT INTO user_modes (name, app_names_json, createdAt)
            VALUES (?, ?, ?)
            """,
            (nameClean, appJson, createdAt),
        )
        modeId = cursor.lastrowid
        conn.commit()
        conn.close()
        return int(modeId)
    except Exception:
        raise RuntimeError("Mod kaydedilemedi")


def update_mode(modeId: int, name: str, app_names: List[str]) -> None:
    dbPath = get_db_path()
    nameClean = (name or "").strip()
    if not nameClean:
        raise RuntimeError("Mod adi bos olamaz")

    appJson = serialize_app(app_names or [])

    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            UPDATE user_modes
            SET name = ?, app_names_json = ?
            WHERE id = ?
            """,
            (nameClean, appJson, int(modeId)),
        )
        conn.commit()
        conn.close()
    except Exception:
        raise RuntimeError("Mod guncellenemedi")


def delete_mode(modeId: int) -> None:
    dbPath = get_db_path()
    try:
        conn = sqlite3.connect(dbPath)
        conn.execute(
            """
            DELETE FROM user_modes
            WHERE id = ?
            """,
            (int(modeId),),
        )
        conn.commit()
        conn.close()
    except Exception:
        raise RuntimeError("Mod silinemedi")


def get_modes(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    dbPath = get_db_path()
    query = """
        SELECT id, name, app_names_json, createdAt
        FROM user_modes
        ORDER BY name ASC
    """
    params: tuple = ()
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
                "name": row["name"],
                "app_names": parse_app(row["app_names_json"] or ""),
                "createdAt": row["createdAt"],
            }
            for row in rows
        ]
    except Exception:
        raise RuntimeError("Modlar listelenemedi")


def get_mode_id(modeId: int) -> Optional[Dict[str, Any]]:
    dbPath = get_db_path()
    try:
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, name, app_names_json, createdAt
            FROM user_modes
            WHERE id = ?
            """,
            (int(modeId),),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "app_names": parse_app(row["app_names_json"] or ""),
            "createdAt": row["createdAt"],
        }
    except Exception:
        raise RuntimeError("Mod okunamadi")


def get_mode_name(name: str) -> Optional[Dict[str, Any]]:
    if not name or not str(name).strip():
        return None

    nameClean = str(name).strip().lower()
    allModes = get_modes()

    if not allModes:
        return None

    for mode in allModes:
        if (mode.get("name") or "").strip().lower() == nameClean:
            return mode

    names = [(m.get("name") or "").strip() for m in allModes]
    matches = get_close_matches(nameClean, [n.lower() for n in names], n=1, cutoff=0.6)
    if not matches:
        return None

    matchedLower = matches[0]
    for mode in allModes:
        if (mode.get("name") or "").strip().lower() == matchedLower:
            return mode

    return None
