import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'home'")
for key, html in cursor.fetchall():
    print(f"\n==================== SECTION: {key} ====================")
    for i, ch in enumerate(html):
        code = ord(ch)
        if code > 127:
            # Let's see context
            start = max(0, i - 15)
            end = min(len(html), i + 16)
            ctx = html[start:end].replace('\n', ' ')
            print(f"Char: {repr(ch)} (U+{code:04X}, dec {code}) in context: ...{ctx}...")

conn.close()
