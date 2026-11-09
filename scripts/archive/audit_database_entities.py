import sqlite3
import re
import html
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=" * 70)
print("COMPREHENSIVE AUDIT FOR STRANGE PATTERNS IN DATABASE")
print("=" * 70)

# Check double escaped entities like &amp;amp;, &amp;lt;, &amp;gt;, etc.
cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections")
sections = cursor.fetchall()

issues = []

for page_slug, section_key, content in sections:
    if not content:
        continue
    # Double escapes
    for double_ent in ['&amp;amp;', '&amp;quot;', '&amp;apos;', '&amp;lt;', '&amp;gt;', '&amp;nbsp;']:
        if double_ent in content:
            issues.append((page_slug, section_key, f"Double-escaped entity {double_ent}"))
    
    # Missing semicolon on &nbsp
    if re.search(r'&nbsp(?![a-zA-Z0-9;])', content):
        issues.append((page_slug, section_key, "Missing semicolon on &nbsp"))

    # Stray backslashes before quotes
    if r'\"' in content or r"\'" in content:
        issues.append((page_slug, section_key, "Escaped quotes \\\" or \\\' in HTML"))

    # Mojibake
    mojibake_matches = re.findall(r'(?:â€[™œ –—•˜]|â[€™˜]|Ã[\x80-\xbf]|Â[\xa0-\xbf]|ΓÇ[óö])', content)
    if mojibake_matches:
        issues.append((page_slug, section_key, f"Mojibake found: {set(mojibake_matches)}"))

print(f"Total section issues found: {len(issues)}")
for page_slug, section_key, desc in issues:
    print(f"  [{page_slug} :: {section_key}] - {desc}")

conn.close()
