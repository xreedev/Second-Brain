import sqlite3
import os
from core.config import Config


def _initialize_database(db_name=Config.SOURCE_DB_NAME):
    db_dir = os.path.dirname(db_name)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                page INTEGER,
                heading TEXT,
                sourceid TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


_initialize_database()


class SQLiteService:
    def __init__(self, db_name=Config.SOURCE_DB_NAME):
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()
        self.conn = conn

    def store_sections_in_sqlite(self, sections, source_id):
        normalized_sections = []
        for section in sections:
            if isinstance(section, dict):
                normalized_sections.append(
                    (
                        section.get("content", ""),
                        section.get("page"),
                        section.get("heading", ""),
                        section.get("sourceid") or source_id,
                    )
                )
            else:
                normalized_sections.append(section)

        self.cursor.executemany(
            "INSERT INTO documents (content, page, heading, sourceid) VALUES (?, ?, ?, ?)",
            normalized_sections,
        )
        self.conn.commit()
        print("Sections stored in SQLite")

    def get_sections_from_sqlite(self, source_id):
        self.cursor.execute(
            """
            SELECT id, content, heading, page, sourceid
            FROM documents
            WHERE sourceid = ?
            """,
            (source_id,),
        )
        results = self.cursor.fetchall()
        return [dict(row) for row in results]
