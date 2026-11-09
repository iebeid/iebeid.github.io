import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

# 1. hobbies::section_1
cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'hobbies' AND section_key = 'section_1'")
h = cursor.fetchone()[0]
h = h.replace('hover:bg-rose-100', 'hover:bg-teal-100')
cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'hobbies' AND section_key = 'section_1'", (h,))

# 2. xlpm::section_1
cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'xlpm' AND section_key = 'section_1'")
h = cursor.fetchone()[0]
h = h.replace('bg-amber-400/15', 'bg-emerald-400/15').replace('border-amber-400/30', 'border-emerald-400/30')
cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'xlpm' AND section_key = 'section_1'", (h,))

conn.commit()
conn.close()
print("[OK] Cleaned remaining strays")
