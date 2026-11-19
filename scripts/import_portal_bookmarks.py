#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Portal Bookmarks & Full State Importer
=============================================================
Imports a `portal_full_state_*.json` (or `islam_ebeid_bookmarks_portal_*.json`
from `downloadBookmarksJSON()`) exported from the live `portal.html` into
`data/content.db` (`portal_bookmarks`, `portal_tasks`, `portal_scratches`).

Usage:
    python scripts/import_portal_bookmarks.py path/to/portal_full_state.json --sync
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent


def ensure_bookmark_columns(cur: sqlite3.Cursor):
    existing = {r[1] for r in cur.execute("PRAGMA table_info(portal_bookmarks)").fetchall()}
    for col, col_def in [
        ("domain", "TEXT"),
        ("path", "TEXT"),
        ("ai_tags", "TEXT"),
        ("description", "TEXT"),
        ("remembered", "INTEGER DEFAULT 0"),
    ]:
        if col not in existing:
            cur.execute(f"ALTER TABLE portal_bookmarks ADD COLUMN {col} {col_def}")


def _next_numeric_id(cur: sqlite3.Cursor) -> int:
    max_id = 10000
    for (cid,) in cur.execute("SELECT chrome_id FROM portal_bookmarks").fetchall():
        try:
            val = int(cid)
            if val > max_id:
                max_id = val
        except (TypeError, ValueError):
            pass
    return max_id + 1


def apply_portal_state(conn: sqlite3.Connection, payload: Dict[str, Any]) -> Dict[str, int]:
    cur = conn.cursor()
    ensure_bookmark_columns(cur)

    # Support Full Portal State, downloadBookmarksJSON(), and DevTools snippet shapes
    all_bookmarks: List[Dict[str, Any]] = []
    if isinstance(payload.get("all_bookmarks"), list):
        all_bookmarks.extend(payload["all_bookmarks"])
    if isinstance(payload.get("custom_bookmarks"), list):
        all_bookmarks.extend(payload["custom_bookmarks"])
    if isinstance(payload.get("bookmarks"), list):
        all_bookmarks.extend(payload["bookmarks"])

    deleted_ids = {str(x) for x in (payload.get("deleted_ids") or payload.get("deleted") or [])}
    pinned_ids = payload.get("pinned_ids") if "pinned_ids" in payload else payload.get("pinned")
    remembered_ids = payload.get("remembered_ids") if "remembered_ids" in payload else payload.get("remember")
    usage_stats = payload.get("usage_stats") if "usage_stats" in payload else (payload.get("usage") or {})

    # Existing URL -> chrome_id index to avoid duplicate rows for the same URL
    url_to_cid: Dict[str, str] = {}
    existing_cids = set()
    for cid, url in cur.execute("SELECT chrome_id, url FROM portal_bookmarks").fetchall():
        existing_cids.add(str(cid))
        if url:
            url_to_cid[url.strip()] = str(cid)

    next_id = _next_numeric_id(cur)
    upserted = 0
    deleted = 0
    id_remap: Dict[str, str] = {}

    for bm in all_bookmarks:
        url = (bm.get("url") or "").strip()
        title = (bm.get("name") or bm.get("title") or "").strip()
        if not url or not title:
            continue

        raw_cid = bm.get("id") or bm.get("chrome_id")
        orig_cid_str = str(raw_cid).strip() if raw_cid is not None and str(raw_cid).strip() else ""
        cid_str = orig_cid_str
        if cid_str in deleted_ids:
            continue
        if not cid_str:
            cid_str = url_to_cid.get(url) or ""
        if not cid_str:
            cid_str = str(next_id)
            next_id += 1
        elif cid_str not in existing_cids and url in url_to_cid:
            cid_str = url_to_cid[url]

        if orig_cid_str:
            id_remap[orig_cid_str] = cid_str

        cat = bm.get("category") or "Work"
        sub = bm.get("subfolder") or "General"
        domain = bm.get("domain") or sub
        path_str = bm.get("path") or (f"{cat} > {sub}" if sub else cat)
        ai_tags = bm.get("ai_tags") or ""
        favicon = bm.get("favicon") or ""
        pinned = 1 if bm.get("pinned") else 0
        clicks = int(bm.get("clicks") or 0)
        desc = bm.get("description") or ""

        cur.execute("""
            INSERT INTO portal_bookmarks (
                chrome_id, title, url, domain, category, subfolder, path,
                ai_tags, favicon, pinned, click_count, description, remembered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chrome_id) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                domain = excluded.domain,
                category = excluded.category,
                subfolder = excluded.subfolder,
                path = excluded.path,
                ai_tags = CASE WHEN excluded.ai_tags != '' THEN excluded.ai_tags ELSE portal_bookmarks.ai_tags END,
                favicon = CASE WHEN excluded.favicon != '' THEN excluded.favicon ELSE portal_bookmarks.favicon END,
                description = CASE WHEN excluded.description != '' THEN excluded.description ELSE portal_bookmarks.description END,
                click_count = MAX(portal_bookmarks.click_count, excluded.click_count)
        """, (cid_str, title, url, domain, cat, sub, path_str, ai_tags, favicon, pinned, clicks, desc, 0))
        existing_cids.add(cid_str)
        url_to_cid[url] = cid_str
        upserted += 1

    for d_id in deleted_ids:
        cur.execute("DELETE FROM portal_bookmarks WHERE chrome_id = ?", (d_id,))
        deleted += cur.rowcount

    if isinstance(pinned_ids, list):
        pinned_set = {id_remap.get(str(x), str(x)) for x in pinned_ids}
        cur.execute("UPDATE portal_bookmarks SET pinned = 0")
        for pid in pinned_set:
            cur.execute("UPDATE portal_bookmarks SET pinned = 1 WHERE chrome_id = ?", (pid,))

    if isinstance(remembered_ids, list):
        rem_set = {id_remap.get(str(x), str(x)) for x in remembered_ids}
        cur.execute("UPDATE portal_bookmarks SET remembered = 0")
        for rid in rem_set:
            cur.execute("UPDATE portal_bookmarks SET remembered = 1 WHERE chrome_id = ?", (rid,))

    if isinstance(usage_stats, dict):
        for bm_id, st in usage_stats.items():
            cnt = int((st or {}).get("count") or 0) if isinstance(st, dict) else 0
            if cnt > 0:
                target_id = id_remap.get(str(bm_id), str(bm_id))
                cur.execute(
                    "UPDATE portal_bookmarks SET click_count = MAX(click_count, ?) WHERE chrome_id = ?",
                    (cnt, target_id),
                )

    tasks = payload.get("tasks")
    if isinstance(tasks, list):
        for t in tasks:
            tid = t.get("id")
            text = (t.get("text") or "").strip()
            done = bool(t.get("done"))
            status = "completed" if done else "active"
            if tid is not None:
                cur.execute("UPDATE portal_tasks SET status = ? WHERE id = ?", (status, tid))
            elif text:
                cur.execute("UPDATE portal_tasks SET status = ? WHERE title = ?", (status, text))

    conn.commit()
    total_count = cur.execute("SELECT COUNT(*) FROM portal_bookmarks").fetchone()[0]
    return {
        "upserted": upserted,
        "deleted": deleted,
        "total_bookmarks": total_count,
        "pinned_count": cur.execute("SELECT COUNT(*) FROM portal_bookmarks WHERE pinned = 1").fetchone()[0],
        "remembered_count": cur.execute("SELECT COUNT(*) FROM portal_bookmarks WHERE remembered = 1").fetchone()[0],
    }


def main():
    parser = argparse.ArgumentParser(description="Import Full Portal State or Bookmarks JSON into content.db")
    parser.add_argument("json_file", help="Path to exported portal_full_state_*.json or bookmarks JSON")
    parser.add_argument("--sync", action="store_true", help="Run sync_content.py --export-only after importing")
    args = parser.parse_args()

    src = Path(args.json_file)
    if not src.exists():
        print(f"[ERROR] File not found: {src}")
        return 1

    payload = json.loads(src.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    stats = apply_portal_state(conn, payload)
    conn.close()
    print(f"[OK] Imported portal bookmarks state into {DB_PATH.name}: {stats}")

    if args.sync:
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
