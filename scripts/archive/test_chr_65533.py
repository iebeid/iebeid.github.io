import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

replacement_char = chr(0xFFFD) # 65533

cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections WHERE instr(content_html, ?) > 0", (replacement_char,))
rows = cursor.fetchall()

print(f"Sections with instr(content_html, chr(0xFFFD)): {len(rows)}")
for slug, key, html in rows:
    count = html.count(replacement_char)
    print(f"  [{slug} :: {key}] found {count}x chr(0xFFFD)")

conn.close()
