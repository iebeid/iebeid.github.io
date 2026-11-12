import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug='scholarship' AND section_key='poetry'")
row = cur.fetchone()
print(f"Key: {row[0]}")
print(row[1])
