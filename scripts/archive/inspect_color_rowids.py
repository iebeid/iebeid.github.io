import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

rowids = [4, 10, 11, 15, 18, 32, 35, 46, 167, 170, 275, 282, 295, 297, 300, 301]

for r in rowids:
    cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections WHERE rowid = ?", (r,))
    res = cursor.fetchone()
    if res:
        slug, key, html = res
        print(f"\n=== rowid={r} [{slug} :: {key}] ===")
        for line in html.splitlines():
            if any(c in line for c in ['purple', 'orange-', 'text-orange', 'bg-orange', 'border-orange', 'violet']):
                print("  ", line.strip()[:140])

conn.close()
