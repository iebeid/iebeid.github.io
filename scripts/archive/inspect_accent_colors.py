import sqlite3
import re

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

pages_to_check = ['scholarship', 'education', 'business', 'downloads', 'relations', 'research']

for slug in pages_to_check:
    cursor.execute("SELECT section_key, heading, content_html FROM page_sections WHERE page_slug = ?", (slug,))
    print(f"\n==================== PAGE: {slug} ====================")
    for key, heading, html in cursor.fetchall():
        borders = re.findall(r'border-(?:l-4\s+border-)?([a-z]+-[0-9]{2,3})', html)
        bg_colors = re.findall(r'bg-([a-z]+-[0-9]{2,3})', html)
        text_colors = re.findall(r'text-([a-z]+-[0-9]{2,3})', html)
        non_neutral_bgs = [b for b in bg_colors if not any(n in b for n in ['gray', 'slate', 'zinc', 'white', 'black'])]
        non_neutral_borders = [b for b in borders if not any(n in b for n in ['gray', 'slate', 'zinc', 'white', 'black', 'l-4', 'b-2', 't-4'])]
        print(f"  [{key}] {heading}")
        if non_neutral_borders:
            print(f"    Accent borders: {list(set(non_neutral_borders))}")
        if non_neutral_bgs:
            print(f"    Accent bgs: {list(set(non_neutral_bgs))[:6]}")

conn.close()
