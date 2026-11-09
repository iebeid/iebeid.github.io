import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

rowids = [2, 9, 10, 11, 12, 13, 14, 19, 20, 31, 34, 35, 41, 45, 64, 165, 166, 167, 168, 171, 243]

non_palette_pattern = re.compile(r'\b(?:text|bg|border|from|to|via)-(?:amber|yellow|red|rose|pink)-[0-9]{2,3}\b')

for r in rowids:
    cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections WHERE rowid = ?", (r,))
    res = cursor.fetchone()
    if not res:
        continue
    slug, key, html = res
    print(f"\n==================== rowid={r} [{slug} :: {key}] ====================")
    for line in html.splitlines():
        if non_palette_pattern.search(line):
            print("  ", line.strip()[:140])

conn.close()
