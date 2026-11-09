import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

suspicious_chars = ['â', '€', 'Ã', 'Â', '\ufffd', 'Γ', '', 'ï¿½']

findings = []

for page_slug, section_key, html in sections:
    if not html:
        continue
    for ch in suspicious_chars:
        if ch in html:
            # find all occurrences
            idx = 0
            while True:
                idx = html.find(ch, idx)
                if idx == -1:
                    break
                start = max(0, idx - 25)
                end = min(len(html), idx + 25)
                snippet = html[start:end].replace('\n', ' ')
                findings.append((page_slug, section_key, ch, snippet))
                idx += 1

print(f"Total suspicious findings: {len(findings)}")
for slug, key, ch, snip in findings:
    print(f"[{slug} :: {key}] char {repr(ch)} -> ...{snip}...")

conn.close()
