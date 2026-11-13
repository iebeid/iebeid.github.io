import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()
cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html = cur.fetchone()[0]

lines = html.split('\n')
print(f"Total lines in portal_app: {len(lines)}")
for i in range(max(0, len(lines)-40), len(lines)):
    print(f"{i+1}: {lines[i]}")
