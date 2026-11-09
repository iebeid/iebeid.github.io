import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'scholarship'")
for key, html in cursor.fetchall():
    print(f"\n=== SCHOLARSHIP SECTION: {key} ===")
    lines = html.splitlines()
    for line in lines[:15]:
        print("  ", line[:100])

conn.close()
