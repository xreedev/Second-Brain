import sqlite3

class SQLiteService:

    def __init__(self, db_name="database.db"):
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()
        self.conn = conn

    def create_table(self, table_name):
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            page INTEGER,
            heading TEXT,
            sourceid TEXT
        )
        """)
        self.conn.commit()
        print(f"Table '{table_name}' created in SQLite database.")

    def store_sections_in_sqlite(self, sections):
        self.cursor.executemany(
            "INSERT INTO documents (content, page, heading, sourceid) VALUES (?, ?, ?, ?)",
            sections,
        )
        self.conn.commit()
        print("Sections stored in SQLite")

    def get_sections_from_sqlite(self):
        self.cursor.execute(
            "SELECT id, content, heading, page, sourceid FROM documents"
        )
        results = self.cursor.fetchall()
        return [dict(row) for row in results]
