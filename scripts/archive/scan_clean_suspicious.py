import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

suspicious_targets = ['â€“', 'â€”', 'â€™', 'â€˜', 'â€œ', 'â€', 'â€¢', 'â€¦', 'Ã©', 'Ã', 'Â', '\ufffd', 'ΓÇ', 'ï¿½']

findings = []

for page_slug, section_key, html in sections:
    if not html:
        continue
    for target in suspicious_targets:
        if target in html:
            count = html.count(target)
            idx = html.find(target)
            start = max(0, idx - 25)
            end = min(len(html), idx + len(target) + 25)
            snippet = html[start:end].replace('\n', ' ')
            findings.append((page_slug, section_key, target, count, snippet))

print(f"Total sections with suspicious sequences: {len(findings)}")
for slug, key, target, count, snip in findings:
    print(f"[{slug} :: {key}] found {count}x {repr(target)} -> ...{snip}...")

conn.close()
