import sqlite3

with sqlite3.connect("biasbridge.db") as conn:
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE surveys ADD COLUMN debate_id INTEGER;")
    conn.commit()
