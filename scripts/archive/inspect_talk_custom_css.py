import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT style_key, css_content FROM stylesheets WHERE rowid = 2")
key, css = cursor.fetchone()
print(f"=== {key} ===")
for line in css.splitlines():
    if 'purple' in line or 'orange' in line:
        print("  ", line.strip())

conn.close()
