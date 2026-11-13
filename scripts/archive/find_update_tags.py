import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug='portal'")
for key, html in cur.fetchall():
    if 'update tags' in html.lower() or 'tags' in html.lower():
        lines = html.split('\n')
        for i, l in enumerate(lines):
            if 'update tags' in l.lower() or 'tag' in l.lower() and 'button' in l.lower():
                print(f"Key: {key} | Line {i+1}: {l.strip()}")
