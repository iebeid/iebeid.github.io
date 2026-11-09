import sqlite3
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT rowid, page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

# Find all Tailwind color classes like text-*, bg-*, border-*, from-*, to-*, via-*
tw_color_pattern = re.compile(r'\b(?:text|bg|border|from|to|via)-([a-z]+)-([0-9]{2,3})\b')

non_palette_colors = ['amber', 'yellow', 'orange', 'red', 'rose', 'pink', 'purple', 'violet', 'fuchsia', 'lime']

findings = []

for rowid, page_slug, section_key, html in sections:
    if not html:
        continue
    matches = tw_color_pattern.findall(html)
    found_non_palette = [f"{c}-{s}" for c, s in matches if c in non_palette_colors]
    if found_non_palette:
        findings.append((rowid, page_slug, section_key, Counter(found_non_palette)))

print(f"Total sections with non-palette colors (amber, yellow, red, etc.): {len(findings)}")
for rowid, slug, key, counts in findings:
    print(f"\n[rowid={rowid}] {slug} :: {key}")
    for c, cnt in counts.most_common():
        print(f"   {c}: {cnt}")

conn.close()
