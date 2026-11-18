#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Master Project Schema CLI Manager
Provides a clean interface to inspect, add, update, and attach artifacts or
publications to the normalized `projects` backbone in data/content.db.

After making changes, run `python scripts/sync_content.py` to propagate
updates automatically across every page in the website.

Examples:
    python scripts/project_manager.py list
    python scripts/project_manager.py show xlpm-visintx
    python scripts/project_manager.py add --slug my-proj --title "My Project" --category "AI & Life Sciences" --summary "..."
    python scripts/project_manager.py update --slug my-proj --status "Active Research" --featured 1
    python scripts/project_manager.py add-artifact --project my-proj --type github_repo --label "Source" --url "https://github.com/iebeid/my-proj"
    python scripts/project_manager.py add-tag --project my-proj --tag "GNN"
"""

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def cmd_list(args):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.display_order, p.slug, p.title, p.category, p.status,
               p.is_featured, p.is_storefront,
               (SELECT COUNT(*) FROM project_artifacts a WHERE a.project_id = p.id) AS acnt
        FROM projects p
        ORDER BY p.display_order, p.id
    """)
    for order, slug, title, cat, status, feat, sf, acnt in cur.fetchall():
        flags = []
        if feat:
            flags.append("FEATURED")
        if sf:
            flags.append("STOREFRONT")
        print(f"{order:2d}. [{slug}] {title} | {cat} | {status} | artifacts={acnt} {'('+','.join(flags)+')' if flags else ''}")
    conn.close()


def cmd_show(args):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM projects WHERE slug = ?", (args.slug,)).fetchone()
    if not row:
        print(f"[ERROR] Project '{args.slug}' not found.")
        conn.close()
        return 1
    print(json.dumps(dict(row), indent=2))
    arts = [dict(r) for r in cur.execute("SELECT * FROM project_artifacts WHERE project_id = ? ORDER BY display_order", (row["id"],)).fetchall()]
    tags = [r["tag"] for r in cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (row["id"],)).fetchall()]
    pubs = [dict(r) for r in cur.execute("SELECT pub.* FROM publications pub JOIN project_publications pp ON pub.id = pp.publication_id WHERE pp.project_id = ?", (row["id"],)).fetchall()]
    print("Artifacts:", json.dumps(arts, indent=2))
    print("Tags:", tags)
    print("Publications:", json.dumps(pubs, indent=2))
    conn.close()


def cmd_add(args):
    conn = get_conn()
    cur = conn.cursor()
    tech_json = json.dumps([t.strip() for t in (args.tech or "").split(",") if t.strip()])
    cur.execute("""
        INSERT INTO projects (
            slug, title, tagline, short_summary, full_description,
            category, domain_stage, status, year_start, year_end,
            institution_or_org, grant_award, tech_stack, code_snippet,
            license_model, price_display, storefront_category,
            is_featured, is_storefront, is_public, display_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        args.slug, args.title, args.tagline, args.summary, args.description or args.summary,
        args.category, args.stage, args.status, args.year_start, args.year_end,
        args.org, args.grant, tech_json, args.snippet,
        args.license, args.price, args.storefront_category,
        args.featured, args.storefront, args.order,
    ))
    conn.commit()
    conn.close()
    print(f"[OK] Added project '{args.slug}'. Run `python scripts/sync_content.py` to publish.")


def cmd_update(args):
    conn = get_conn()
    cur = conn.cursor()
    fields = []
    vals = []
    mapping = {
        "title": args.title,
        "tagline": args.tagline,
        "short_summary": args.summary,
        "full_description": args.description,
        "category": args.category,
        "status": args.status,
        "grant_award": args.grant,
        "license_model": args.license,
        "price_display": args.price,
        "storefront_category": args.storefront_category,
        "is_featured": args.featured,
        "is_storefront": args.storefront,
        "is_public": args.public,
        "display_order": args.order,
    }
    for col, val in mapping.items():
        if val is not None:
            fields.append(f"{col} = ?")
            vals.append(val)
    if args.tech is not None:
        fields.append("tech_stack = ?")
        vals.append(json.dumps([t.strip() for t in args.tech.split(",") if t.strip()]))
    if not fields:
        print("[WARN] No update flags supplied.")
        conn.close()
        return
    vals.append(args.slug)
    cur.execute(f"UPDATE projects SET {', '.join(fields)} WHERE slug = ?", vals)
    if cur.rowcount == 0:
        print(f"[ERROR] Project '{args.slug}' not found.")
    else:
        conn.commit()
        print(f"[OK] Updated project '{args.slug}'. Run `python scripts/sync_content.py` to publish.")
    conn.close()


def cmd_add_artifact(args):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM projects WHERE slug = ?", (args.project,)).fetchone()
    if not row:
        print(f"[ERROR] Project '{args.project}' not found.")
        conn.close()
        return 1
    pid = row[0]
    doc_id = None
    if args.doc:
        drow = cur.execute("SELECT id FROM documents WHERE filename = ?", (args.doc,)).fetchone()
        if drow:
            doc_id = drow[0]
    cur.execute("""
        INSERT OR REPLACE INTO project_artifacts (project_id, artifact_type, label, url_or_rel_path, format_badge, document_id, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pid, args.type, args.label, args.url, args.badge, doc_id, args.order))
    conn.commit()
    conn.close()
    print(f"[OK] Linked artifact '{args.label}' -> '{args.project}'. Run `python scripts/sync_content.py` to publish.")


def cmd_add_tag(args):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT id FROM projects WHERE slug = ?", (args.project,)).fetchone()
    if not row:
        print(f"[ERROR] Project '{args.project}' not found.")
        conn.close()
        return 1
    cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (row[0], args.tag))
    conn.commit()
    conn.close()
    print(f"[OK] Added tag '{args.tag}' to '{args.project}'.")


def main():
    parser = argparse.ArgumentParser(description="Master Project Backbone Manager for content.db")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List all canonical projects")

    p_show = sub.add_parser("show", help="Show full JSON & artifacts for a project slug")
    p_show.add_argument("slug")

    p_add = sub.add_parser("add", help="Add a new canonical project")
    p_add.add_argument("--slug", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--tagline", default="")
    p_add.add_argument("--summary", required=True)
    p_add.add_argument("--description", default=None)
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--stage", default="02_ai_modeling")
    p_add.add_argument("--status", default="Active Research")
    p_add.add_argument("--year-start", type=int, default=2026)
    p_add.add_argument("--year-end", type=int, default=None)
    p_add.add_argument("--org", default="Texas Woman's University")
    p_add.add_argument("--grant", default=None)
    p_add.add_argument("--tech", default="")
    p_add.add_argument("--snippet", default=None)
    p_add.add_argument("--license", default="Open Source")
    p_add.add_argument("--price", default=None)
    p_add.add_argument("--storefront-category", default=None)
    p_add.add_argument("--featured", type=int, default=0)
    p_add.add_argument("--storefront", type=int, default=0)
    p_add.add_argument("--order", type=int, default=99)

    p_upd = sub.add_parser("update", help="Update fields on an existing project")
    p_upd.add_argument("--slug", required=True)
    p_upd.add_argument("--title")
    p_upd.add_argument("--tagline")
    p_upd.add_argument("--summary")
    p_upd.add_argument("--description")
    p_upd.add_argument("--category")
    p_upd.add_argument("--status")
    p_upd.add_argument("--grant")
    p_upd.add_argument("--tech")
    p_upd.add_argument("--license")
    p_upd.add_argument("--price")
    p_upd.add_argument("--storefront-category")
    p_upd.add_argument("--featured", type=int)
    p_upd.add_argument("--storefront", type=int)
    p_upd.add_argument("--public", type=int)
    p_upd.add_argument("--order", type=int)

    p_art = sub.add_parser("add-artifact", help="Attach a repo, demo, paper, dataset, or zip to a project")
    p_art.add_argument("--project", required=True)
    p_art.add_argument("--type", required=True, help="github_repo | live_demo | source_zip | dataset | paper_pdf | slides | poster | video | pip_command | publisher_url | design_doc")
    p_art.add_argument("--label", required=True)
    p_art.add_argument("--url", required=True)
    p_art.add_argument("--badge", default="")
    p_art.add_argument("--doc", default=None)
    p_art.add_argument("--order", type=int, default=10)

    p_tag = sub.add_parser("add-tag", help="Attach a tag to a project")
    p_tag.add_argument("--project", required=True)
    p_tag.add_argument("--tag", required=True)

    args = parser.parse_args()
    handlers = {
        "list": cmd_list,
        "show": cmd_show,
        "add": cmd_add,
        "update": cmd_update,
        "add-artifact": cmd_add_artifact,
        "add-tag": cmd_add_tag,
    }
    return handlers[args.cmd](args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
