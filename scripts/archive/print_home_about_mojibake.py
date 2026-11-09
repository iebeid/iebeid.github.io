import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'home' AND section_key = 'about'")
html = cursor.fetchone()[0]

lines = html.splitlines()
for i, line in enumerate(lines):
    if 'â€“' in line or 'â€' in line:
        print(f"Line {i+1}: {line.strip()}")

conn.close()
