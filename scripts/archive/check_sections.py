import sqlite3
import sys
from pathlib import Path

db_path = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/data/content.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

page = sys.argv[1] if len(sys.argv) > 1 else None

if page:
    rows = cur.execute("SELECT section_key, length(content_html), heading FROM page_sections WHERE page_slug=?", (page,)).fetchall()
    print(f"=== Sections for page '{page}' ===")
    for r in rows:
        print(f"  [{r[0]}] ({r[1]} bytes) - {r[2]}")
else:
    rows = cur.execute("SELECT page_slug, count(*), sum(length(content_html)) FROM page_sections GROUP BY page_slug").fetchall()
    print("=== All Pages in DB ===")
    for r in rows:
        print(f"  {r[0]}: {r[1]} sections, {r[2]} total bytes")
