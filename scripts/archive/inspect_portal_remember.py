import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'portal' AND section_key = 'portal_app'")
html = cursor.fetchone()[0]

for line in html.splitlines():
    if "remember" in line.lower() or "save for later" in line.lower():
        print("portal_app ->", line.strip()[:140])

conn.close()
