import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()
cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html = cur.fetchone()[0]

lines = html.split('\n')
for i, l in enumerate(lines):
    if 'tab-btn' in l or 'id="tab-' in l:
        print(f"Line {i+1}: {l.strip()}")
