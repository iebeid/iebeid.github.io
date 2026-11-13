import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("PRAGMA table_info(portal_vault)")
print("portal_vault schema:", cur.fetchall())

cur.execute("SELECT key, description, updated_at FROM portal_vault")
print("portal_vault rows:", cur.fetchall())

cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html = cur.fetchone()[0]
print("portal_app length:", len(html))

# Check tabs in portal_app
for line in html.split('\n'):
    if 'tab-' in line or 'switchTab' in line or 'vault' in line.lower():
        print(" ", line.strip()[:140])
