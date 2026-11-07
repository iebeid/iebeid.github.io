import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'catalog'")
catalog_html = cursor.fetchone()[0]

for line in catalog_html.splitlines():
    if "VISUALIZATION" in line or "REPORTING" in line or "filterSystem" in line:
        print(line.strip())

conn.close()
