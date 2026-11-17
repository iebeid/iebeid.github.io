import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT section_key, heading, content_html FROM page_sections WHERE page_slug='lab' ORDER BY display_order")
with open('scripts/archive/lab_sections_dump.txt', 'w', encoding='utf-8') as f:
    for key, heading, html in cur.fetchall():
        f.write(f"\n==================== {key} ({heading}) ====================\n")
        f.write(html + "\n")

conn.close()
print("[OK] Dumped all lab sections to scripts/archive/lab_sections_dump.txt")
