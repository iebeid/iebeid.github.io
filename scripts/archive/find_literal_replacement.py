import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

# Search for the literal character '' or code 65533
cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections WHERE content_html LIKE '%%'")
rows = cursor.fetchall()

print(f"Sections with literal '': {len(rows)}")
for slug, key, html in rows:
    count = html.count('')
    idx = html.find('')
    start = max(0, idx - 25)
    end = min(len(html), idx + 26)
    snippet = html[start:end].replace('\n', ' ')
    print(f"  [{slug} :: {key}] found {count}x '' -> ...{snippet}...")

# Also check other tables
for t in ['publications', 'courses', 'contacts_directory', 'portal_bookmarks', 'pages', 'site_meta']:
    cursor.execute(f"PRAGMA table_info({t})")
    cols = [c[1] for c in cursor.fetchall() if c[2] in ['TEXT', '']]
    for c in cols:
        cursor.execute(f"SELECT rowid, {c} FROM {t} WHERE {c} LIKE '%%'")
        r = cursor.fetchall()
        if r:
            print(f"  [{t}.{c}] found {len(r)} rows with ''")

conn.close()
