import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

# Example query
cur.execute("SELECT * FROM tasks WHERE id=16;")
print(cur.fetchall())

conn.close()