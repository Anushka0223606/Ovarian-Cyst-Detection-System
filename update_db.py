import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS predictions")

cursor.execute("""
CREATE TABLE predictions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    image_path TEXT,
    result TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

conn.close()

print("Predictions table updated!")