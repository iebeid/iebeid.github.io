import sqlite3, re, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'catalog'")
catalog_html = cursor.fetchone()[0]

articles = re.findall(r'(<article\s+class="product-card"[\s\S]*?</article>)', catalog_html)
print(f"Total articles found: {len(articles)}")
for i, a in enumerate(articles):
    if "DataIntegrationToolkit" in a:
        print(f"Article {i} is DITK:")
        print(a)

conn.close()
