import sqlite3
import re
from collections import Counter

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

# Get all content_html
cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

page_colors = {}

tailwind_color_pattern = re.compile(r'\b(?:bg|text|border|from|to|via)-([a-z]+)-([0-9]{2,3})\b')
hex_pattern = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')

for page_slug, section_key, html in sections:
    if not html:
        continue
    if page_slug not in page_colors:
        page_colors[page_slug] = Counter()
    
    tw_matches = tailwind_color_pattern.findall(html)
    for color, shade in tw_matches:
        if color in ['sky', 'blue', 'cyan', 'teal', 'emerald', 'green', 'indigo', 'slate', 'gray', 'zinc', 'neutral', 'amber', 'purple', 'rose', 'red']:
            page_colors[page_slug][f"{color}-{shade}"] += 1

    hex_matches = hex_pattern.findall(html)
    for h in hex_matches:
        page_colors[page_slug][f"#{h.lower()}"] += 1

print("=== COLOR USAGE BY PAGE ===")
for slug, counter in page_colors.items():
    print(f"\n--- Page: {slug} ---")
    common = counter.most_common(10)
    for c, cnt in common:
        print(f"  {c}: {cnt}")

conn.close()
