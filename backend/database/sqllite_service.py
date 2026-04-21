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

        # SECTION INDEX TABLE
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS section_index (
                section_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                PRIMARY KEY (section_id, source_id)
            )
            """
        )

        # Add file_name column if it doesn't exist yet (safe on existing DBs)
        try:
            cursor.execute("ALTER TABLE section_index ADD COLUMN file_name TEXT")
        except sqlite3.OperationalError:
            pass

        # MESSAGES TABLE
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # MESSAGE SECTIONS TABLE
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS message_sections (
                message_id TEXT NOT NULL,
                section_id TEXT NOT NULL,
                PRIMARY KEY (message_id, section_id),
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
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


    def get_source_files_by_section_ids(self, section_ids):
        """
        Given a list of section IDs (documents.id),
        return unique source file names.
        """

        if not section_ids:
           return []

        # Normalize to integers
        section_ids = [int(sid) for sid in section_ids]

        placeholders = ",".join("?" for _ in section_ids)

        query = f"""
        SELECT DISTINCT s.file_name
        FROM documents d
        JOIN source s ON d.sourceid = s.id
        WHERE d.id IN ({placeholders})
        """

        self.cursor.execute(query, section_ids)

        results = self.cursor.fetchall()

        return [row["file_name"] for row in results]


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
    # MESSAGES
    # ----------------------------
    def create_message(self, message_id: str, query: str):
        self.cursor.execute(
            "INSERT INTO messages (id, query) VALUES (?, ?)",
            (message_id, query),
        )
        self.conn.commit()

    def update_message_response(self, message_id: str, response: str):
        self.cursor.execute(
            "UPDATE messages SET response = ? WHERE id = ?",
            (response, message_id),
        )
        self.conn.commit()

    def add_message_section(self, message_id: str, section_id: str):
        self.cursor.execute(
            "INSERT OR IGNORE INTO message_sections (message_id, section_id) VALUES (?, ?)",
            (message_id, section_id),
        )
        self.conn.commit()

    def get_sections_for_message(self, message_id: str):
        self.cursor.execute(
            "SELECT section_id FROM message_sections WHERE message_id = ?",
            (message_id,),
        )
        return [row["section_id"] for row in self.cursor.fetchall()]

    def get_sources_for_wiki_sections(self, section_ids: list):
        """Return distinct source rows for the given wiki section_ids via section_index."""
        if not section_ids:
            return []
        placeholders = ",".join("?" for _ in section_ids)
        query = f"""
            SELECT DISTINCT s.id, s.file_name
            FROM section_index si
            JOIN source s ON CAST(si.source_id AS INTEGER) = s.id
            WHERE si.section_id IN ({placeholders})
        """
        self.cursor.execute(query, section_ids)
        return [dict(row) for row in self.cursor.fetchall()]

    # ----------------------------
    # WIKI SECTION INDEX (IndexMapService)
    # ----------------------------
    def get_max_wiki_section_id(self) -> int:
        self.cursor.execute(
            "SELECT MAX(CAST(section_id AS INTEGER)) FROM section_index"
        )
        result = self.cursor.fetchone()[0]
        return result if result is not None else 0

    def insert_wiki_section(self, section_id: str, source_id: str, file_name: str):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO section_index (section_id, source_id, file_name)
            VALUES (?, ?, ?)
            """,
            (section_id, source_id, file_name),
        )
        self.conn.commit()

    def upsert_wiki_section(self, section_id: str, source_id: str, file_name: str):
        self.cursor.execute(
            """
            INSERT INTO section_index (section_id, source_id, file_name) VALUES (?, ?, ?)
            ON CONFLICT(section_id, source_id) DO UPDATE SET file_name = excluded.file_name
            """,
            (section_id, source_id, file_name),
        )
        self.conn.commit()

    def remap_section_ids(self, id_mapping: dict):
        """Rename section_ids in section_index according to {old_id: new_id}."""
        for old_id, new_id in id_mapping.items():
            self.cursor.execute(
                "UPDATE section_index SET section_id = ? WHERE section_id = ?",
                (str(new_id), str(old_id)),
            )
        self.conn.commit()

    def replace_all_section_entries(self, source_map: dict):
        """Replace the full section_index with the given {section_id: {sources, file_name}} dict."""
        self.cursor.execute("DELETE FROM section_index")
        for section_id, entry in source_map.items():
            file_name = entry.get("file_name") or ""
            for source_id in entry.get("sources", []):
                self.cursor.execute(
                    "INSERT OR IGNORE INTO section_index (section_id, source_id, file_name) VALUES (?, ?, ?)",
                    (str(section_id), str(source_id), file_name),
                )
        self.conn.commit()

    def get_wiki_section_entry(self, section_id: str) -> dict:
        self.cursor.execute(
            "SELECT source_id, file_name FROM section_index WHERE section_id = ?",
            (section_id,),
        )
        rows = self.cursor.fetchall()
        if not rows:
            return {}
        return {
            "sources": [row["source_id"] for row in rows],
            "file_name": rows[0]["file_name"],
        }

    def get_all_wiki_sections(self) -> dict:
        self.cursor.execute(
            "SELECT section_id, source_id, file_name FROM section_index"
        )
        result = {}
        for row in self.cursor.fetchall():
            sid = row["section_id"]
            if sid not in result:
                result[sid] = {"sources": [], "file_name": row["file_name"]}
            result[sid]["sources"].append(row["source_id"])
        return result

    # ----------------------------
    # SECTION INDEX (IndexService)
    # ----------------------------
    def get_source_ids_for_section(self, section_id: str):
        self.cursor.execute(
            "SELECT source_id FROM section_index WHERE section_id = ?",
            (section_id,),
        )
        return [row["source_id"] for row in self.cursor.fetchall()]

    def add_section_source_mapping(self, section_id: str, source_id: str):
        self.cursor.execute(
            "INSERT OR IGNORE INTO section_index (section_id, source_id) VALUES (?, ?)",
            (section_id, source_id),
        )
        self.conn.commit()

    # ----------------------------
    # CLEANUP
    # ----------------------------
    def close(self):
        self.conn.close()