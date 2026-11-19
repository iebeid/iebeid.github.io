#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Portal Project CRUD & Static Patch Applier
==================================================================
Shared SQLite write helpers for `projects`, `project_artifacts`, `project_tags`,
and `project_placements`. Used both by `scripts/portal_server.py` (live mode)
and directly via CLI to apply a `portal_project_patch.json` exported from the
static GitHub Pages portal.

Usage:
    python scripts/apply_portal_patch.py portal_project_patch.json --sync
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_projects_backbone import ensure_schema, infer_storage_source  # noqa: E402


def _slugify(val: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", (val or "").lower()).strip("-")
    return s[:64] or f"project-{int(datetime.now().timestamp())}"


def _parse_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        return [x.strip() for x in val.split(",") if x.strip()]
    return []


def save_project_record(conn: sqlite3.Connection, data: Dict[str, Any]) -> int:
    cur = conn.cursor()
    raw_pid = data.get("id")
    try:
        pid = int(raw_pid) if raw_pid is not None and int(raw_pid) > 0 else None
    except (TypeError, ValueError):
        pid = None
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("Project title is required.")

    raw_slug = (data.get("slug") or "").strip() or _slugify(title)
    slug = _slugify(raw_slug) if raw_slug != raw_slug.lower() or " " in raw_slug else raw_slug
    now_iso = datetime.now(timezone.utc).isoformat()

    tech_list = _parse_list(data.get("tech_stack"))
    kw_list = _parse_list(data.get("keywords"))
    tags_list = _parse_list(data.get("tags"))

    year_start = data.get("year_start")
    year_end = data.get("year_end")
    year_start = int(year_start) if str(year_start or "").strip().isdigit() else None
    year_end = int(year_end) if str(year_end or "").strip().isdigit() else None

    is_public = 1 if data.get("is_public") else 0
    is_featured = 1 if data.get("is_featured") else 0
    is_storefront = 1 if data.get("is_storefront") else 0
    display_order = int(data.get("display_order") or 99)

    if not pid:
        existing = cur.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if existing:
            pid = existing[0]

    if pid:
        cur.execute("""
            UPDATE projects SET
                slug = ?, title = ?, tagline = ?, short_summary = ?, full_description = ?,
                category = ?, project_kind = ?, status = ?, year_start = ?, year_end = ?,
                institution_or_org = ?, grant_award = ?, tech_stack = ?, keywords = ?,
                license_model = ?, price_display = ?, storefront_category = ?,
                is_featured = ?, is_storefront = ?, is_public = ?, display_order = ?,
                discovery_status = ?, gdrive_primary_url = ?, updated_at = ?
            WHERE id = ?
        """, (
            slug, title, data.get("tagline") or "",
            data.get("short_summary") or title,
            data.get("full_description") or data.get("short_summary") or title,
            data.get("category") or "General Portfolio",
            data.get("project_kind") or "research",
            data.get("status") or "Active",
            year_start, year_end,
            data.get("institution_or_org") or "",
            data.get("grant_award") or "",
            json.dumps(tech_list),
            json.dumps(kw_list),
            data.get("license_model") or "",
            data.get("price_display") or "",
            data.get("storefront_category") or "",
            is_featured, is_storefront, is_public, display_order,
            data.get("discovery_status") or "reviewed",
            data.get("gdrive_primary_url") or "",
            now_iso,
            int(pid),
        ))
        project_id = int(pid)
    else:
        # Ensure unique slug if collision
        base = slug
        idx = 2
        while cur.execute("SELECT 1 FROM projects WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base}-{idx}"
            idx += 1

        cur.execute("""
            INSERT INTO projects (
                slug, title, tagline, short_summary, full_description,
                category, domain_stage, status, year_start, year_end,
                institution_or_org, grant_award, tech_stack, keywords,
                license_model, price_display, storefront_category,
                is_featured, is_storefront, is_public, display_order,
                project_kind, discovery_status, source_origin,
                gdrive_primary_url, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'portal', ?, ?)
        """, (
            slug, title, data.get("tagline") or "",
            data.get("short_summary") or title,
            data.get("full_description") or data.get("short_summary") or title,
            data.get("category") or "General Portfolio",
            data.get("domain_stage") or "02_ai_modeling",
            data.get("status") or "Active",
            year_start, year_end,
            data.get("institution_or_org") or "",
            data.get("grant_award") or "",
            json.dumps(tech_list),
            json.dumps(kw_list),
            data.get("license_model") or "",
            data.get("price_display") or "",
            data.get("storefront_category") or "",
            is_featured, is_storefront, is_public, display_order,
            data.get("project_kind") or "research",
            data.get("discovery_status") or "canonical",
            data.get("gdrive_primary_url") or "",
            now_iso,
        ))
        project_id = cur.lastrowid

    if "tags" in data:
        cur.execute("DELETE FROM project_tags WHERE project_id = ?", (project_id,))
        for tag in tags_list:
            cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (project_id, tag))

    conn.commit()
    return project_id


def delete_project_record(conn: sqlite3.Connection, project_id: Optional[int] = None, slug: Optional[str] = None) -> bool:
    cur = conn.cursor()
    if project_id:
        cur.execute("DELETE FROM projects WHERE id = ?", (int(project_id),))
    elif slug:
        cur.execute("DELETE FROM projects WHERE slug = ?", (slug,))
    else:
        return False
    conn.commit()
    return cur.rowcount > 0


def save_artifact_record(conn: sqlite3.Connection, data: Dict[str, Any]) -> int:
    cur = conn.cursor()
    raw_pid = data.get("project_id")
    try:
        pid = int(raw_pid) if raw_pid is not None and int(raw_pid) > 0 else None
    except (TypeError, ValueError):
        pid = None
    if not pid and data.get("project_slug"):
        row = cur.execute("SELECT id FROM projects WHERE slug = ?", (data["project_slug"],)).fetchone()
        if row:
            pid = row[0]
    if not pid:
        raise ValueError("Valid project_id or project_slug is required for artifact.")

    url_val = (data.get("url") or data.get("url_or_rel_path") or "").strip()
    label = (data.get("label") or "").strip()
    if not url_val or not label:
        raise ValueError("Artifact label and URL/path are required.")

    storage = data.get("storage_source") or infer_storage_source(url_val)
    gdrive_id = (data.get("gdrive_file_id") or "").strip()
    if not gdrive_id and storage == "gdrive":
        m = re.search(r"/(?:d|folders)/([A-Za-z0-9_-]{15,})", url_val)
        if m:
            gdrive_id = m.group(1)

    is_public = 1 if data.get("is_public", True) else 0
    raw_aid = data.get("id")
    try:
        art_id = int(raw_aid) if raw_aid is not None and int(raw_aid) > 0 else None
    except (TypeError, ValueError):
        art_id = None
    if art_id:
        cur.execute("""
            UPDATE project_artifacts SET
                artifact_type = ?, label = ?, url_or_rel_path = ?, format_badge = ?,
                display_order = ?, storage_source = ?, gdrive_file_id = ?,
                gdrive_url = ?, is_public = ?
            WHERE id = ? AND project_id = ?
        """, (
            data.get("type") or data.get("artifact_type") or "design_doc",
            label, url_val, data.get("badge") or data.get("format_badge") or "",
            int(data.get("display_order") or 10),
            storage, gdrive_id or None,
            url_val if storage == "gdrive" else (data.get("gdrive_url") or None),
            is_public, int(art_id), int(pid),
        ))
        conn.commit()
        return int(art_id)

    cur.execute("""
        INSERT OR REPLACE INTO project_artifacts (
            project_id, artifact_type, label, url_or_rel_path, format_badge,
            display_order, storage_source, gdrive_file_id, gdrive_url, is_public
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(pid),
        data.get("type") or data.get("artifact_type") or "design_doc",
        label, url_val, data.get("badge") or data.get("format_badge") or "",
        int(data.get("display_order") or 10),
        storage, gdrive_id or None,
        url_val if storage == "gdrive" else (data.get("gdrive_url") or None),
        is_public,
    ))
    conn.commit()
    return cur.lastrowid


def delete_artifact_record(conn: sqlite3.Connection, artifact_id: int) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM project_artifacts WHERE id = ?", (int(artifact_id),))
    conn.commit()
    return cur.rowcount > 0


def set_project_placements(
    conn: sqlite3.Connection,
    project_id: Optional[int],
    placements: List[Dict[str, Any]],
    auto_public_if_placed: bool = True,
    project_slug: Optional[str] = None,
) -> int:
    cur = conn.cursor()
    try:
        pid_val = int(project_id) if project_id is not None and int(project_id) > 0 else None
    except (TypeError, ValueError):
        pid_val = None
    if not pid_val and project_slug:
        row = cur.execute("SELECT id FROM projects WHERE slug = ?", (project_slug,)).fetchone()
        if row:
            pid_val = row[0]
    if not pid_val:
        raise ValueError("Valid project_id or project_slug is required.")

    pid = int(pid_val)
    cur.execute("DELETE FROM project_placements WHERE project_id = ?", (pid,))
    visible_slots = []
    for idx, pl in enumerate(placements, 1):
        page_slug = (pl.get("page_slug") or "").strip()
        section_slot = (pl.get("section_slot") or "projects").strip()
        if not page_slug:
            continue
        is_vis = 1 if pl.get("is_visible", True) else 0
        variant = pl.get("card_variant") or (
            "home-compact" if (page_slug == "home" and section_slot == "featured")
            else "storefront-catalog" if (page_slug == "storefront" and section_slot == "catalog")
            else "research-cards"
        )
        order_val = int(pl.get("display_order") if pl.get("display_order") is not None else idx * 10)
        cur.execute("""
            INSERT OR REPLACE INTO project_placements (
                project_id, page_slug, section_slot, card_variant, display_order, is_visible
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, page_slug, section_slot, variant, order_val, is_vis))
        if is_vis:
            visible_slots.append((page_slug, section_slot))

    # Keep legacy convenience flags synchronized
    is_feat = 1 if ("home", "featured") in visible_slots else 0
    is_sf = 1 if ("storefront", "catalog") in visible_slots else 0
    cur.execute("UPDATE projects SET is_featured = ?, is_storefront = ? WHERE id = ?", (is_feat, is_sf, pid))
    if auto_public_if_placed and visible_slots:
        cur.execute("UPDATE projects SET is_public = 1, discovery_status = CASE WHEN discovery_status = 'discovered' THEN 'reviewed' ELSE discovery_status END WHERE id = ?", (pid,))

    conn.commit()
    return len(visible_slots)


def apply_patch_payload(conn: sqlite3.Connection, patch: Dict[str, Any]) -> Dict[str, int]:
    """Apply an ordered operations patch exported from static portal.html."""
    ensure_schema(conn.cursor())
    counts = {"saved": 0, "deleted": 0, "artifacts": 0, "placements": 0}
    for op in patch.get("operations", []):
        kind = op.get("op")
        payload = op.get("payload") or {}
        if kind == "save_project":
            save_project_record(conn, payload)
            counts["saved"] += 1
        elif kind == "delete_project":
            if delete_project_record(conn, payload.get("id"), payload.get("slug")):
                counts["deleted"] += 1
        elif kind == "save_artifact":
            save_artifact_record(conn, payload)
            counts["artifacts"] += 1
        elif kind == "delete_artifact":
            if payload.get("id") and delete_artifact_record(conn, int(payload["id"])):
                counts["artifacts"] += 1
        elif kind == "set_placements":
            set_project_placements(
                conn,
                payload.get("project_id"),
                payload.get("placements") or [],
                auto_public_if_placed=bool(payload.get("auto_public", True)),
                project_slug=payload.get("project_slug"),
            )
            counts["placements"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description="Apply portal_project_patch.json to data/content.db")
    parser.add_argument("patch_file", help="Path to JSON patch file exported from portal.html")
    parser.add_argument("--sync", action="store_true", help="Run sync_content.py --export-only after applying")
    args = parser.parse_args()

    patch_path = Path(args.patch_file)
    if not patch_path.exists():
        print(f"[ERROR] Patch file not found: {patch_path}")
        return 1

    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB_PATH)
    counts = apply_patch_payload(conn, patch)
    conn.close()
    print(f"[OK] Applied portal patch: {counts}")

    if args.sync:
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
