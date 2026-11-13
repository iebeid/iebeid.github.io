import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("PRAGMA table_info(portal_bookmarks)")
cols = [c[1] for c in cur.fetchall()]
print("Cols:", cols)
if 'description' not in cols:
    cur.execute("ALTER TABLE portal_bookmarks ADD COLUMN description TEXT")
    print("[OK] Added description column to portal_bookmarks")
else:
    print("[INFO] description column already exists")

conn.commit()
conn.close()
