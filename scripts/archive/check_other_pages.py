import sqlite3
import re

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

for slug in ['home', 'education', 'teaching', 'service']:
    cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = ?", (slug,))
    print(f"\n==================== PAGE: {slug} ====================")
    for key, html in cursor.fetchall():
        non_blues = re.findall(r'\b(amber|purple|rose|indigo|pink|orange|red)-[0-9]{2,3}\b', html)
        if non_blues:
            print(f"  [{key}] Non-palette colors: {set(non_blues)}")

conn.close()
