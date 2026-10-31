import json
import sqlite3
import re
from pathlib import Path

REPO_ROOT = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io")
DB_PATH = REPO_ROOT / "data" / "content.db"
JSON_PATH = REPO_ROOT / "data" / "public_content.json"
PAGES_DIR = REPO_ROOT / "pages"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Load DB sections
db_sections = {}
for slug, key, heading in cur.execute("SELECT page_slug, section_key, heading FROM page_sections").fetchall():
    db_sections[f"{slug}.{key}"] = heading

print(f"Total sections registered in SQLite: {len(db_sections)}")

# 2. Check each HTML file
html_files = list(PAGES_DIR.glob("*/*.html"))
html_files = [f for f in html_files if not f.name.endswith(".bak")]

total_placeholders = 0
missing_in_db = []

print(f"\nChecking {len(html_files)} HTML pages:")
for hf in sorted(html_files):
    if hf.name in ["portal.html", "drop.html", "lab.html"]:
        continue
    with open(hf, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    matches = re.findall(r'data-db-section="([^"]+)"', text)
    has_db_js = "public_content.js" in text
    has_loader_js = "content-loader.js" in text
    print(f"  * {hf.parent.name}/{hf.name}: {len(matches)} placeholders | DB JS: {has_db_js} | Loader JS: {has_loader_js}")

    for m in matches:
        total_placeholders += 1
        if m not in db_sections:
            missing_in_db.append((str(hf), m))

print(f"\nTotal placeholders found across HTML templates: {total_placeholders}")
if missing_in_db:
    print(f"[ERROR] Found {len(missing_in_db)} placeholders missing from SQLite database:")
    for f, m in missing_in_db:
        print(f"   {f} -> {m}")
else:
    print("[SUCCESS] 100% of HTML placeholders match verified SQLite sections!")
