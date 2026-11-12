import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT content_html FROM page_sections WHERE page_slug='scholarship' AND section_key='poetry'")
html = cur.fetchone()[0]

idx = html.find("Personal Epigraph")
if idx != -1:
    print(html[idx:])
else:
    print("Not found")
