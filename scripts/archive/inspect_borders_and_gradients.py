import sqlite3
import re

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT page_slug, section_key, heading, content_html FROM page_sections")
all_sections = cursor.fetchall()

print(f"Total sections: {len(all_sections)}")

sections_by_page = {}
for slug, key, heading, html in all_sections:
    if slug not in sections_by_page:
        sections_by_page[slug] = []
    
    # Find border colors like border-l-4 border-*-*
    borders = re.findall(r'border-(?:l-4\s+border-)?([a-z]+-\d+)', html)
    # Find gradients like from-*-* to-*-*
    gradients = re.findall(r'from-([a-z]+-\d+)\s+(?:via-([a-z]+-\d+)\s+)?to-([a-z]+-\d+)', html)
    
    sections_by_page[slug].append({
        'key': key,
        'heading': heading,
        'borders': borders[:5],
        'gradients': gradients[:2]
    })

for slug, secs in sections_by_page.items():
    print(f"\n==================== PAGE: {slug} ({len(secs)} sections) ====================")
    for s in secs:
        b_str = ", ".join(s['borders']) if s['borders'] else "none"
        g_str = ", ".join([f"{g[0]}->{g[1]}->{g[2]}" for g in s['gradients']]) if s['gradients'] else "none"
        print(f"  [{s['key']}] {s['heading']} | Borders: {b_str} | Gradients: {g_str}")

conn.close()
