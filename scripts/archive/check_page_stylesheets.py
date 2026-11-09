import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT style_key, css_content FROM stylesheets WHERE style_key LIKE 'style_%'")
for key, css in cursor.fetchall():
    print(f"\n=== {key} ({len(css)} chars) ===")
    lines = [l.strip() for l in css.splitlines() if l.strip() and not l.strip().startswith('/*')]
    for l in lines[:10]:
        print("  ", l[:100])

conn.close()
