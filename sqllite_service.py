import sqlite3

conn = sqlite3.connect("papers.db") 
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    page INTEGER,
    heading TEXT
)
""")

def store_sections_in_sqlite(sections):
    cursor.executemany(
    "INSERT INTO documents (content, page, heading) VALUES (?, ?, ?)",
    sections)
    conn.commit()
    print("Sections stored in SQLite")

def get_sections_from_sqlite():
    cursor.execute("SELECT id, content, heading, page FROM documents")
    results = cursor.fetchall()
    return [dict(row) for row in results]
