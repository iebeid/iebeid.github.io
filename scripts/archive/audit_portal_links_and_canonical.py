import os
import sqlite3

print("=== 1. Scanning SQLite data/content.db for 'portal.html' or 'PORTAL_HREF' ===")
conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

for tbl, cols in [
    ('pages', ['slug', 'head_html', 'body_template_html', 'inline_scripts']),
    ('page_sections', ['page_slug', 'section_key', 'content_html']),
    ('html_templates', ['template_key', 'html_content']),
    ('navigation_menu', ['nav_key', 'label', 'rel_path']),
]:
    cur.execute(f"SELECT {', '.join(cols)} FROM {tbl}")
    for row in cur.fetchall():
        key = row[0]
        for idx, val in enumerate(row[1:], 1):
            if val and ('portal.html' in str(val) or 'PORTAL_HREF' in str(val)):
                print(f"  DB {tbl} ({key}) col={cols[idx]}:")
                for line in str(val).splitlines():
                    if 'portal.html' in line or 'PORTAL_HREF' in line:
                        print(f"    {line.strip()[:160]}")

conn.close()
