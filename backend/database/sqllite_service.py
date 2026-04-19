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

        # Enable foreign keys (important in SQLite)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # SOURCE TABLE
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS source (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL
            )
            """
        )

        # DOCUMENTS TABLE
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                page INTEGER,
                heading TEXT,
                sourceid INTEGER,
                FOREIGN KEY (sourceid) REFERENCES source(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


# Initialize DB on import
_initialize_database()


class SQLiteService:
    def __init__(self, db_name=Config.SOURCE_DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Enable foreign keys here too (per connection)
        self.cursor.execute("PRAGMA foreign_keys = ON;")


    # ----------------------------
    # CREATE SOURCE
    # ----------------------------
    def create_source(self, file_name):
        self.cursor.execute(
            "INSERT INTO source (file_name) VALUES (?)",
            (file_name,)
        )
        self.conn.commit()

        return self.cursor.lastrowid


    # ----------------------------
    # STORE SECTIONS
    # ----------------------------
    def store_sections_in_sqlite(self, sections, source_id):
        normalized_sections = []

        for section in sections:
            if isinstance(section, dict):
                normalized_sections.append(
                    (
                        section.get("content", ""),
                        section.get("page"),
                        section.get("heading", ""),
                        source_id,  # enforce consistency
                    )
                )
            else:
                normalized_sections.append(section)

        self.cursor.executemany(
            """
            INSERT INTO documents (content, page, heading, sourceid)
            VALUES (?, ?, ?, ?)
            """,
            normalized_sections,
        )

        self.conn.commit()
        print(f"Stored {len(normalized_sections)} sections for source_id={source_id}")


    # ----------------------------
    # GET SECTIONS
    # ----------------------------
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


    # ----------------------------
    # OPTIONAL: GET SOURCE
    # ----------------------------
    def get_source(self, source_id):
        self.cursor.execute(
            "SELECT * FROM source WHERE id = ?",
            (source_id,),
        )
        result = self.cursor.fetchone()
        return dict(result) if result else None


    # ----------------------------
    # CLEANUP
    # ----------------------------
    def close(self):
        self.conn.close()