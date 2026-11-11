import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'portal' AND section_key = 'portal_app'")
html = cursor.fetchone()[0]

m = re.search(r'(<!-- Remember / Save for Later Section -->[\s\S]*?<!-- Top 10 Favorites Section -->)', html)
if m:
    print(m.group(1))

conn.close()
