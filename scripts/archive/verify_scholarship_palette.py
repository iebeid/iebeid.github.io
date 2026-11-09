import sqlite3, re

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'scholarship'")
for key, html in cursor.fetchall():
    colors = set(re.findall(r'\b(sky|blue|cyan|teal|emerald|gray|slate)-[0-9]{2,3}\b', html))
    print(f"[{key}]:")
    print("  ", sorted(list(colors)))

conn.close()
