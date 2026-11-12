import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug='home'")
for key, html in cur.fetchall():
    print(f"\n--- Section: {key} ---")
    for line in html.split('\n')[:25]:
        print(" ", line)
