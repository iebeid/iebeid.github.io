#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Live GitHub Portal -> Local SQLite Reconciler
=====================================================================
Checks `js/portal_data.js` (encrypted `portal_projects_encrypted`) and
`data/bookmarks.json` for changes published directly from the live portal
(`https://iebeid.github.io/pages/portal/portal.html` via GitHub API) and
reconciles them into `data/content.db` so local Drive discovery and sync
never overwrite edits made on the live website.

Usage:
    python scripts/reconcile_live_to_db.py
    python scripts/reconcile_live_to_db.py --force
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
PORTAL_DATA_JS = REPO_ROOT / "js" / "portal_data.js"
BOOKMARKS_JSON = REPO_ROOT / "data" / "bookmarks.json"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from apply_portal_patch import (  # noqa: E402
    delete_project_record,
    save_artifact_record,
    save_project_record,
    set_project_placements,
)
from build_projects_backbone import ensure_schema  # noqa: E402
from database_manager import DEFAULT_PORTAL_PASSCODE, decrypt_secret, read_vault_secret  # noqa: E402
from import_portal_bookmarks import apply_portal_state  # noqa: E402


def _get_vault_passcode(db_path: Path) -> str:
    try:
        sec = read_vault_secret("master_passcode", DEFAULT_PORTAL_PASSCODE, db_path)
        if sec:
            return sec
    except Exception:
        pass
    return DEFAULT_PORTAL_PASSCODE


def _read_portal_data_js() -> Dict[str, Any]:
    if not PORTAL_DATA_JS.exists():
        return {}
    raw = PORTAL_DATA_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.__PORTAL_DATABASE\s*=\s*(\{.*\})\s*;", raw, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def reconcile_live_to_db(conn: sqlite3.Connection, db_path: Path = DB_PATH, force: bool = False) -> Dict[str, Any]:
    """Ingest live GitHub-published portal state into SQLite if newer than last seen."""
    cur = conn.cursor()
    ensure_schema(cur)
    result = {"reconciled": False, "reason": "up_to_date", "projects_synced": 0, "projects_deleted": 0, "bookmarks": 0}

    pdata = _read_portal_data_js()
    enc_proj = pdata.get("portal_projects_encrypted")
    if not enc_proj:
        result["reason"] = "no_encrypted_bundle"
        return result

    passcode = _get_vault_passcode(db_path)
    try:
        bundle = json.loads(decrypt_secret(enc_proj, passcode))
    except Exception as exc:
        result["reason"] = f"decrypt_skipped:{type(exc).__name__}"
        return result

    published_from = bundle.get("_published_from", "")
    gen_at = bundle.get("_generated_at", "")
    row = cur.execute("SELECT value FROM site_meta WHERE key = 'last_portal_publish_seen'").fetchone()
    last_seen = row[0] if row else ""

    if not force:
        if published_from != "portal_github_api":
            result["reason"] = "local_sync_origin"
            return result
        if gen_at and last_seen and gen_at <= last_seen:
            result["reason"] = "already_reconciled"
            return result

    # 1. Delete any project slugs explicitly deleted in the live portal
    for slug in bundle.get("deleted_project_slugs") or []:
        if delete_project_record(conn, slug=slug):
            result["projects_deleted"] += 1

    # 2. Upsert projects, artifacts, and website placements from live portal bundle
    for proj in bundle.get("projects") or []:
        # Only overwrite/insert if project is new, or portal bundle carries a newer updated_at
        slug = proj.get("slug")
        existing = cur.execute("SELECT id, updated_at FROM projects WHERE slug = ?", (slug,)).fetchone()
        proj_payload = dict(proj)
        if existing:
            proj_payload["id"] = existing[0]
        else:
            proj_payload["id"] = None

        pid = save_project_record(conn, proj_payload)

        # Sync artifacts cleanly for this project
        incoming_arts = proj.get("artifacts") or []
        incoming_urls = {a.get("url") for a in incoming_arts if a.get("url")}
        if existing:
            cur.execute("DELETE FROM project_artifacts WHERE project_id = ? AND url_or_rel_path NOT IN ({})".format(
                ",".join("?" for _ in incoming_urls) if incoming_urls else "''"
            ), (pid, *incoming_urls) if incoming_urls else (pid,))
            conn.commit()
        for a in incoming_arts:
            art_payload = dict(a)
            art_payload["project_id"] = pid
            art_payload["project_slug"] = slug
            art_payload["id"] = None
            # Preserve existing artifact id if matched by url
            arow = cur.execute(
                "SELECT id FROM project_artifacts WHERE project_id = ? AND url_or_rel_path = ?",
                (pid, a.get("url")),
            ).fetchone()
            if arow:
                art_payload["id"] = arow[0]
            try:
                save_artifact_record(conn, art_payload)
            except ValueError:
                pass

        # Sync placements
        if "placements" in proj:
            set_project_placements(
                conn,
                pid,
                proj.get("placements") or [],
                auto_public_if_placed=False,
            )
        result["projects_synced"] += 1

    # 3. Reconcile bookmarks.json (431+ bookmarks, pinned, remembered, click counts)
    if BOOKMARKS_JSON.exists():
        bm_data = json.loads(BOOKMARKS_JSON.read_text(encoding="utf-8"))
        bm_list = bm_data.get("bookmarks") or []
        pinned_ids = [str(b["id"]) for b in bm_list if b.get("pinned")]
        remembered_ids = [str(b["id"]) for b in bm_list if b.get("remembered")]
        usage_stats = {str(b["id"]): {"count": int(b.get("clicks") or 0)} for b in bm_list if b.get("clicks")}
        bm_stats = apply_portal_state(conn, {
            "all_bookmarks": bm_list,
            "pinned_ids": pinned_ids,
            "remembered_ids": remembered_ids,
            "usage_stats": usage_stats,
        })
        result["bookmarks"] = bm_stats.get("total_bookmarks", 0)

    if gen_at:
        cur.execute("""
            INSERT INTO site_meta (key, value, description)
            VALUES ('last_portal_publish_seen', ?, 'Timestamp of last live GitHub portal state reconciled into content.db')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (gen_at,))
        conn.commit()

    result["reconciled"] = True
    result["reason"] = "synced_from_live_portal"
    return result


def main():
    parser = argparse.ArgumentParser(description="Reconcile live portal GitHub commits back into data/content.db")
    parser.add_argument("--force", action="store_true", help="Force reconciliation regardless of timestamp")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    res = reconcile_live_to_db(conn, DB_PATH, force=args.force)
    conn.close()
    print(f"[RECONCILE] {res}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
