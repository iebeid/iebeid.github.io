import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug = 'home' AND section_key = 'about'")
row = cursor.fetchone()

if not row:
    print("Error: home::about section not found")
    sys.exit(1)

html, text = row

html_count = html.count('â€“')
text_count = text.count('â€“') if text else 0

print(f"Found {html_count} occurrences in content_html, {text_count} in content_text")

fixed_html = html.replace('â€“', '–')
fixed_text = text.replace('â€“', '–') if text else None

cursor.execute(
    "UPDATE page_sections SET content_html = ?, content_text = ? WHERE page_slug = 'home' AND section_key = 'about'",
    (fixed_html, fixed_text)
)

conn.commit()
print("[SUCCESS] Updated home::about in SQLite database")

# Verify
cursor.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug = 'home' AND section_key = 'about'")
v_html, v_text = cursor.fetchone()

print(f"Verification: remaining in content_html = {v_html.count('â€“')}, in content_text = {v_text.count('â€“') if v_text else 0}")

conn.close()
