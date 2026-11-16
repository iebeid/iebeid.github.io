import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()
cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='portal' AND section_key='login_screen'")
html, text = cur.fetchone()
print("=== login_screen HTML ===")
print(html)
conn.close()
