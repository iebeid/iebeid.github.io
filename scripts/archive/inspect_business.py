import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, heading, length(content_html) FROM page_sections WHERE page_slug = 'business'")
for r in cursor.fetchall():
    print(r)

conn.close()
