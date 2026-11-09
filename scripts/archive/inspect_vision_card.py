import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'home'")
for key, html in cursor.fetchall():
    if "Vision" in html or "vision" in html:
        print(f"=== FOUND VISION IN SECTION: {key} ===")
        for line in html.splitlines():
            if "vision" in line.lower() or "mission" in line.lower() or "amber" in line or "yellow" in line or "orange" in line:
                print("  ", line.strip())

conn.close()
