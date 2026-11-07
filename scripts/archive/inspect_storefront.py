import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, heading, subheading, content_html FROM page_sections WHERE page_slug = 'storefront'")
for r in cursor.fetchall():
    print("=" * 60)
    print("KEY:", r[0])
    print("HEADING:", r[1])
    print("SUBHEADING:", r[2])
    print("CONTENT PREVIEW (up to 500 chars):")
    print(r[3][:500] if r[3] else "EMPTY")

conn.close()
