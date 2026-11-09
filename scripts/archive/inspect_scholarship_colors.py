import sqlite3
import sys

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=== STYLESHEETS IN DB ===")
cursor.execute("SELECT id, style_key, length(css_content) FROM stylesheets")
for r in cursor.fetchall():
    print(r)

print("\n=== SCHOLARSHIP PAGE DETAILS ===")
cursor.execute("SELECT slug, title, html_classes, body_classes, head_html, body_template_html FROM pages WHERE slug = 'scholarship'")
page = cursor.fetchone()
if page:
    print(f"Slug: {page[0]}")
    print(f"Classes: {page[2]} / {page[3]}")
    print(f"Head: {page[4]}")
    print(f"Template:\n{page[5]}")

print("\n=== SCHOLARSHIP SECTIONS ===")
cursor.execute("SELECT section_key, heading, length(content_html) FROM page_sections WHERE page_slug = 'scholarship'")
for r in cursor.fetchall():
    print(r)

conn.close()
