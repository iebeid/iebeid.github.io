import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT slug, title, rel_path FROM pages")
for r in cursor.fetchall():
    print(r)

conn.close()
