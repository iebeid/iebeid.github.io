import sqlite3
import sys

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=== global_base CSS ===")
cursor.execute("SELECT css_content FROM stylesheets WHERE style_key = 'global_base'")
print(cursor.fetchone()[0])

print("\n=== style_scholarship CSS ===")
cursor.execute("SELECT css_content FROM stylesheets WHERE style_key = 'style_scholarship'")
print(cursor.fetchone()[0])

print("\n=== SCHOLARSHIP SECTION HERO BANNER ===")
cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'scholarship' AND section_key = 'hero_banner'")
print(cursor.fetchone()[0])

print("\n=== SCHOLARSHIP SECTION JURISPRUDENCE (First 1000 chars) ===")
cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'scholarship' AND section_key = 'jurisprudence'")
print(cursor.fetchone()[0][:1000])

conn.close()
