import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()
cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html = cur.fetchone()[0]

idx = html.find('dashboard-favorites-grid')
if idx != -1:
    start = max(0, idx - 1000)
    end = min(len(html), idx + 200)
    print(html[start:end])
