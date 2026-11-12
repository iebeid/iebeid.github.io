import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# Find pages where buttons/links have hover:border or rounded tags
cur.execute("SELECT page_slug, section_key, content_html FROM page_sections WHERE content_html LIKE '%tag%' OR content_html LIKE '%badge%'")
rows = cur.fetchall()
print(f"Found {len(rows)} sections with tag/badge mentions")
for r in rows[:10]:
    print(f"  Page: {r[0]} | Key: {r[1]}")
