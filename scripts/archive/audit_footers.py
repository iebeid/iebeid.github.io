import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

for skey in ('style_relations', 'style_scholarship', 'style_storefront'):
    cur.execute("SELECT css_content FROM stylesheets WHERE style_key=?", (skey,))
    css = cur.fetchone()[0]
    print(f"=== {skey} ===")
    lines = css.splitlines()
    for i, l in enumerate(lines):
        if any(k in l.lower() for k in ['justify', 'footer', 'text-align']):
            start = max(0, i-3)
            end = min(len(lines), i+6)
            for j in range(start, end):
                print(f"  {j+1}: {lines[j]}")
            print("  ---")

conn.close()
