import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(navigation_menu)")
print("navigation_menu columns:", cursor.fetchall())

cursor.execute("SELECT * FROM navigation_menu LIMIT 2")
for r in cursor.fetchall():
    print(r)

conn.close()
