import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=== CHECKING ALL NON-ASCII IN page_sections ===")
cursor.execute("SELECT rowid, page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

non_ascii_stats = {}
weird_char_snippets = []

for rowid, page_slug, section_key, html in sections:
    if not html:
        continue
    for i, ch in enumerate(html):
        code = ord(ch)
        if code > 127:
            # Let's see what char it is
            # Common legitimate non-ASCII: Arabic characters, smart quotes, bullets, en-dash, em-dash, accented latin (é, etc.)
            # Weird: \ufffd (65533), â, €, ™, etc., or isolated diacritics
            if code == 65533: # \ufffd
                start = max(0, i - 30)
                end = min(len(html), i + 30)
                weird_char_snippets.append((page_slug, section_key, f"REPLACEMENT CHAR (\\ufffd, 65533)", html[start:end]))
            elif ch in ['â', '€', '™', 'œ', '˜', '’', '‘', '“', '”', '–', '—', '•']:
                # Check if it's mojibake sequence like 'â€“' or 'â€™'
                sub = html[i:i+3]
                if any(sub.startswith(m) for m in ['â€', 'â€™', 'â€˜', 'â€œ', 'â€', 'â€“', 'â€”', 'â€¢']):
                    start = max(0, i - 20)
                    end = min(len(html), i + 25)
                    weird_char_snippets.append((page_slug, section_key, f"MOJIBAKE ({repr(sub)})", html[start:end]))

print(f"Total weird snippets found: {len(weird_char_snippets)}")
for slug, key, desc, snip in weird_char_snippets:
    print(f"\n[{slug} :: {key}] - {desc}")
    print("  ", repr(snip))

conn.close()
