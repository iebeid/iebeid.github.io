import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

for key in ['hero_banner', 'section_6']:
    cursor.execute("SELECT section_key, heading, content_html FROM page_sections WHERE page_slug = 'business' AND section_key = ?", (key,))
    r = cursor.fetchone()
    if r:
        print("="*60)
        print(r[0], r[1])
        print(r[2])

conn.close()
