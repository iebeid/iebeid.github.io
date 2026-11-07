import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'architecture'")
arch_html = cursor.fetchone()[0]
print(arch_html)

conn.close()
