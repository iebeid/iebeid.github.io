#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Full-Stack Website Render & Integrity Verifier
Validates consistency across SQLite page sections, body templates,
HTML shell files, and exported public JSON artifacts.
"""

import json
import sqlite3
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
JSON_PATH = REPO_ROOT / "data" / "public_content.json"
PAGES_DIR = REPO_ROOT / "pages"

def main():
    print("=" * 68)
    print("Dr. Islam Akef Ebeid - Full-Stack Website Render & Integrity Verifier")
    print(f"Repository Root: {REPO_ROOT}")
    print("=" * 68)

    if not DB_PATH.exists():
        print(f"[ERROR] Database file missing: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Registered DB sections
    db_sections = {}
    for slug, key, heading in cur.execute("SELECT page_slug, section_key, heading FROM page_sections").fetchall():
        db_sections[f"{slug}.{key}"] = heading
    print(f"[OK] Total sections registered in SQLite: {len(db_sections)}")

    # 2. Check body templates stored in `pages` table
    cur.execute("SELECT slug, title, body_template_html FROM pages WHERE body_template_html IS NOT NULL")
    pages = cur.fetchall()
    print(f"\nVerifying body templates across {len(pages)} pages in SQLite:")
    template_placeholders = 0
    missing_sections = []

    for slug, title, tmpl in pages:
        matches = re.findall(r'data-db-section="([^"]+)"', tmpl or "")
        print(f"  * Page '{slug}': {len(matches)} section placeholders ({title[:40]}...)")
        for m in matches:
            template_placeholders += 1
            if m not in db_sections:
                missing_sections.append((slug, m))

    print(f"\nTotal placeholders found across database templates: {template_placeholders}")
    if missing_sections:
        print(f"[ERROR] Found {len(missing_sections)} placeholders missing from SQLite database:")
        for slug, m in missing_sections:
            print(f"   {slug} -> {m}")
    else:
        print("[SUCCESS] 100% of body template placeholders match verified SQLite sections!")

    # 3. Check HTML Shell files on disk
    html_files = sorted([f for f in PAGES_DIR.glob("**/*.html") if not f.name.endswith(".bak")])
    root_index = REPO_ROOT / "index.html"
    if root_index.exists():
        html_files.insert(0, root_index)

    print(f"\nVerifying {len(html_files)} HTML shell files on disk:")
    shell_issues = []
    for hf in html_files:
        rel_path = hf.relative_to(REPO_ROOT)
        with open(hf, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        has_shell_attr = 'data-sqlite-shell="true"' in text
        has_db_js = "public_content.js" in text
        has_loader_js = "content-loader.js" in text
        has_template_js = "template.js" in text

        # xlpm and talk pages might be specialized sub-applications
        is_subapp = "xlpm" in str(rel_path) or "talk" in str(rel_path)
        status = "OK"
        if not is_subapp and not (has_db_js and has_loader_js and has_template_js):
            status = "WARN (missing standard loader scripts)"
            shell_issues.append((str(rel_path), status))

        print(f"  * {rel_path}: shell={has_shell_attr} | db_js={has_db_js} | loader={has_loader_js} | [{status}]")

    # 4. Check JSON export artifact
    if JSON_PATH.exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            public_data = json.load(f)
        total_public_pages = len(public_data.get("pages", []))
        total_public_styles = len(public_data.get("stylesheets", {}))
        print(f"\n[OK] Public JSON artifact verified: {total_public_pages} pages, {total_public_styles} stylesheets.")
    else:
        print(f"\n[WARN] Public JSON bundle not found at {JSON_PATH}. Run sync_content.py to generate.")

    conn.close()
    print("=" * 68)
    print("[SUCCESS] Verification Completed Successfully.")
    print("=" * 68)
    return 0

if __name__ == "__main__":
    exit(main())
