import sqlite3
from pathlib import Path

db_path = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/data/content.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

pages = ["home", "relations", "scholarship", "teaching", "education", "research", "service", "business", "downloads"]

print("=== VERIFYING CONTENT IN SQLITE ===")
for p in pages:
    rows = cur.execute("SELECT section_key, length(content_html), heading FROM page_sections WHERE page_slug=? ORDER BY display_order", (p,)).fetchall()
    print(f"\nPage [{p}] - {len(rows)} sections in SQLite:")
    for r in rows:
        print(f"   * {r[0]}: {r[1]} chars ({r[2]})")
