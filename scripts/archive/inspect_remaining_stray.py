import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'hobbies' AND section_key = 'section_1'")
html = cursor.fetchone()[0]

for line in html.splitlines():
    if "rose" in line:
        print("hobbies::section_1 ->", line.strip())

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'xlpm' AND section_key = 'section_1'")
html_xlpm = cursor.fetchone()[0]
for line in html_xlpm.splitlines():
    if "amber" in line:
        print("xlpm::section_1 ->", line.strip())

conn.close()
