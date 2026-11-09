import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT rowid, style_key, css_content FROM stylesheets")
for r, k, css in cursor.fetchall():
    lines = [l.strip() for l in css.splitlines() if 'purple' in l or 'orange' in l or 'violet' in l or 'fuchsia' in l]
    if lines:
        print(f"=== rowid={r} {k} ===")
        for l in lines:
            print("  ", l[:120])

conn.close()
