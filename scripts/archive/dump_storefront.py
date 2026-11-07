import sqlite3, json

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, heading, subheading, content_html FROM page_sections WHERE page_slug = 'storefront'")
rows = cursor.fetchall()

sections = {}
for r in rows:
    sections[r[0]] = {
        "heading": r[1],
        "subheading": r[2],
        "html": r[3]
    }

with open('scripts/archive/storefront_sections.json', 'w', encoding='utf-8') as f:
    json.dump(sections, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(sections)} sections: {list(sections.keys())}")
conn.close()
