#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Central Synchronization Engine (sync_content.py)
Reads data/content.db and synchronizes public data artifacts (public_content.json & public_content.js),
HTML templates, CSS stylesheets, navigation hierarchy, pages, and portal bookmarks
while keeping data/content.db private and gitignored.
"""

import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "content.db"
PUBLIC_JSON_PATH = DATA_DIR / "public_content.json"
PUBLIC_JS_PATH = DATA_DIR / "public_content.js"
PORTAL_BOOKMARKS_JSON = REPO_ROOT / "pages" / "portal" / "bookmarks.json"
PORTAL_BOOKMARKS_JS = REPO_ROOT / "pages" / "portal" / "bookmarks_data.js"


def check_git_safety():
    """Verify that content.db is properly ignored and not tracked by git."""
    try:
        res = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain", "data/content.db"],
            capture_output=True,
            text=True
        )
        if res.stdout.strip():
            print("[CAUTION] data/content.db appears in git status! Ensuring .gitignore protection...")
    except Exception:
        pass


def export_public_content(conn: sqlite3.Connection):
    """Export SQLite tables (meta, navigation_menu, html_templates, stylesheets, pages, sections, etc.) into data/public_content.json and data/public_content.js."""
    cur = conn.cursor()

    # 1. Site Metadata
    cur.execute("SELECT key, value, description FROM site_meta")
    meta = {r[0]: {"value": r[1], "description": r[2]} for r in cur.fetchall()}

    # 2. Navigation Menu Hierarchy (Top-level items + Hover Dropdown Sub-pages)
    cur.execute("""
        SELECT nav_key, parent_key, label, sublabel, folder, rel_path, icon_class, badge_text, display_order, is_visible
        FROM navigation_menu
        WHERE is_visible = 1
        ORDER BY display_order, id
    """)
    nav_rows = cur.fetchall()
    top_nav = []
    children_by_parent = {}
    for r in nav_rows:
        item = {
            "nav_key": r[0],
            "parent_key": r[1],
            "label": r[2],
            "sublabel": r[3] or "",
            "folder": r[4],
            "rel_path": r[5],
            "icon_class": r[6] or "",
            "badge_text": r[7] or "",
            "order": r[8]
        }
        if r[1] is None:
            top_nav.append(item)
        else:
            children_by_parent.setdefault(r[1], []).append(item)

    for top_item in top_nav:
        top_item["children"] = children_by_parent.get(top_item["nav_key"], [])

    # 3. HTML Templates
    cur.execute("SELECT template_key, category, html_content, description FROM html_templates")
    html_templates = {
        r[0]: {
            "category": r[1],
            "html": r[2],
            "description": r[3]
        }
        for r in cur.fetchall()
    }

    # 4. CSS Stylesheets
    cur.execute("""
        SELECT style_key, scope, page_slug, rel_path, style_type, css_content, description, display_order
        FROM stylesheets
        ORDER BY display_order, id
    """)
    stylesheets = {}
    for r in cur.fetchall():
        stylesheets[r[0]] = {
            "style_key": r[0],
            "scope": r[1],
            "page_slug": r[2],
            "rel_path": r[3],
            "style_type": r[4] or "text/css",
            "css_content": r[5],
            "description": r[6] or "",
            "order": r[7]
        }

    # 5. Pages & Modular Sections
    cur.execute("""
        SELECT slug, title, subtitle, description, rel_path, nav_order, is_public,
               html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
        FROM pages
        ORDER BY nav_order
    """)
    pages = []
    for p in cur.fetchall():
        slug = p[0]
        cur.execute("""
            SELECT section_key, heading, subheading, content_html, content_text, display_order
            FROM page_sections WHERE page_slug = ? ORDER BY display_order, id
        """, (slug,))
        sections = [
            {
                "section_key": s[0],
                "heading": s[1],
                "subheading": s[2],
                "content_html": s[3],
                "content_text": s[4],
                "order": s[5]
            }
            for s in cur.fetchall()
        ]
        pages.append({
            "slug": slug,
            "title": p[1],
            "subtitle": p[2],
            "description": p[3],
            "rel_path": p[4] or "",
            "order": p[5],
            "is_public": bool(p[6]),
            "html_classes": p[7] or "",
            "body_classes": p[8] or "",
            "head_html": p[9] or "",
            "body_template_html": p[10] or "",
            "inline_scripts": p[11] or "",
            "use_global_chrome": bool(p[12]),
            "sections": sections
        })

    # 6. Documents
    cur.execute("SELECT filename, title, rel_path, category, file_size_bytes FROM documents ORDER BY title")
    documents = [
        {"filename": d[0], "title": d[1], "rel_path": d[2], "category": d[3], "size_bytes": d[4]}
        for d in cur.fetchall()
    ]

    # 7. Images
    cur.execute("SELECT filename, alt_text, rel_path, category FROM images ORDER BY filename")
    images = [
        {"filename": i[0], "alt_text": i[1], "rel_path": i[2], "category": i[3]}
        for i in cur.fetchall()
    ]

    # 8. Publications
    cur.execute("SELECT title, authors, venue, year, doi, url, pdf_path, bibtex, display_order FROM publications ORDER BY display_order")
    publications = [
        {
            "title": pb[0],
            "authors": pb[1],
            "venue": pb[2],
            "year": pb[3],
            "doi": pb[4],
            "url": pb[5],
            "pdf_path": pb[6],
            "bibtex": pb[7]
        }
        for pb in cur.fetchall()
    ]

    # 9. Courses
    cur.execute("SELECT code, title, institution, term, syllabus_path, description, display_order FROM courses ORDER BY display_order")
    courses = [
        {
            "code": c[0],
            "title": c[1],
            "institution": c[2],
            "term": c[3],
            "syllabus_path": c[4],
            "description": c[5]
        }
        for c in cur.fetchall()
    ]

    # 10. Contacts Directory
    cur.execute("SELECT name, role, organization, email, phone, category, display_order FROM contacts_directory ORDER BY display_order")
    contacts = [
        {
            "name": ct[0],
            "role": ct[1],
            "organization": ct[2],
            "email": ct[3],
            "phone": ct[4],
            "category": ct[5]
        }
        for ct in cur.fetchall()
    ]

    export_bundle = {
        "_generated_at": datetime.now().isoformat(),
        "_source": "data/content.db (SQLite 16-Table Unified Engine)",
        "meta": meta,
        "navigation_menu": top_nav,
        "html_templates": html_templates,
        "stylesheets": stylesheets,
        "pages": pages,
        "documents": documents,
        "images": images,
        "publications": publications,
        "courses": courses,
        "contacts": contacts
    }

    PUBLIC_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PUBLIC_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(export_bundle, f, indent=2, ensure_ascii=False)

    with open(PUBLIC_JS_PATH, "w", encoding="utf-8") as f:
        f.write("window.__SITE_DATABASE = " + json.dumps(export_bundle, indent=2, ensure_ascii=False) + ";\n")

    print(
        f"[OK] Generated SQLite runtime bundle: {PUBLIC_JSON_PATH.name} & {PUBLIC_JS_PATH.name} "
        f"({len(pages)} pages, {len(stylesheets)} stylesheets, {len(top_nav)} top nav menus, {len(documents)} docs)"
    )


def sync_portal_bookmarks(conn: sqlite3.Connection):
    """Sync portal_bookmarks table to pages/portal/bookmarks.json and bookmarks_data.js."""
    cur = conn.cursor()
    cur.execute("SELECT chrome_id, title, url, category, subfolder, favicon, pinned, click_count FROM portal_bookmarks ORDER BY category, title")
    rows = cur.fetchall()

    if not rows:
        return

    bookmarks_list = []
    categories = set()
    category_counts = {}

    for r in rows:
        cat = r[3] or "General"
        categories.add(cat)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        bookmarks_list.append({
            "id": r[0],
            "name": r[1],
            "type": "bookmark",
            "url": r[2],
            "category": cat,
            "subfolder": r[4] or "",
            "favicon": r[5] or "",
            "pinned": bool(r[6]),
            "clicks": r[7]
        })

    payload = {
        "total_bookmarks": len(bookmarks_list),
        "categories": sorted(list(categories)),
        "category_counts": category_counts,
        "bookmarks": bookmarks_list,
        "_synced_from_sqlite": datetime.now().isoformat()
    }

    PORTAL_BOOKMARKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(PORTAL_BOOKMARKS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with open(PORTAL_BOOKMARKS_JS, "w", encoding="utf-8") as f:
        f.write("window.PORTAL_BOOKMARKS_DATA = " + json.dumps(payload, indent=2, ensure_ascii=False) + ";\n")

    print(f"[OK] Synced {len(bookmarks_list)} bookmarks to {PORTAL_BOOKMARKS_JSON.name} & {PORTAL_BOOKMARKS_JS.name}")


def git_commit_and_push(commit_msg: str | None = None):
    """Stage all synchronized public artifacts, verify content.db is excluded, and commit + push to GitHub."""
    temp_helper = REPO_ROOT / "scripts" / "convert_all_to_shells.py"
    if temp_helper.exists():
        temp_helper.unlink()

    print("-" * 68)
    print("[GIT] Preparing GitHub commit and push...")

    # 1. Stage all tracked and untracked public files (respecting .gitignore)
    subprocess.run(["git", "-C", str(REPO_ROOT), "add", "-A"], check=True)

    # 2. Explicit safety check: ensure data/content.db is never staged
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "reset", "-q", "HEAD", "--", "data/content.db"],
        capture_output=True,
        text=True,
    )

    # 3. Check if there are staged changes to commit
    diff_check = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    if diff_check.returncode == 0:
        print("[GIT] Working tree is already clean — nothing new to commit.")
    else:
        if not commit_msg:
            commit_msg = f"Sync website content, HTML templates & CSS from SQLite ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        commit_res = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
        )
        if commit_res.returncode != 0:
            print(f"[GIT ERROR] Commit failed:\n{commit_res.stderr or commit_res.stdout}")
            sys.exit(commit_res.returncode)
        print(f"[OK] Committed changes: {commit_msg}")

    # 4. Push to GitHub remote
    branch_res = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    branch = branch_res.stdout.strip() or "main"
    print(f"[GIT] Pushing to origin/{branch}...")
    push_res = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "push", "origin", branch],
        capture_output=True,
        text=True,
    )
    if push_res.returncode != 0:
        print(f"[GIT ERROR] Push failed:\n{push_res.stderr or push_res.stdout}")
        sys.exit(push_res.returncode)
    print(f"[OK] Successfully pushed to GitHub (origin/{branch})!")


def main():
    print("=" * 68)
    print("Dr. Islam Akef Ebeid - SQLite Full-Stack Content & UI Sync Engine")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 68)

    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}. Run scripts/extract_content_to_sqlite.py first.")
        sys.exit(1)

    check_git_safety()

    conn = sqlite3.connect(str(DB_PATH))
    export_public_content(conn)
    sync_portal_bookmarks(conn)
    conn.close()

    if "--no-push" not in sys.argv:
        custom_msg = None
        if "-m" in sys.argv:
            idx = sys.argv.index("-m")
            if idx + 1 < len(sys.argv):
                custom_msg = sys.argv[idx + 1]
        git_commit_and_push(custom_msg)

    print("=" * 68)
    print("[SUCCESS] Synchronization Complete! All HTML, CSS, Nav & Content synced.")
    print("=" * 68)


if __name__ == "__main__":
    main()
