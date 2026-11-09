import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(html_templates)")
print(cursor.fetchall())

cursor.execute("SELECT * FROM html_templates LIMIT 3")
for r in cursor.fetchall():
    print(r)

conn.close()
