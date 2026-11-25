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

    if not pid:
        existing_id_row = cur.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if existing_id_row:
            pid = existing_id_row[0]

    existing_map: Dict[str, Any] = {}
    if pid:
        cur.execute("SELECT * FROM projects WHERE id = ?", (int(pid),))
        row_vals = cur.fetchone()
        if row_vals:
            col_names = [desc[0] for desc in cur.description]
            existing_map = dict(zip(col_names, row_vals))
        else:
            pid = None

    def _pick_str(key: str, default: str = "") -> str:
        if key in data and data[key] is not None:
            return str(data[key])
        if key in existing_map and existing_map[key] is not None:
            return str(existing_map[key])
        return default

    def _pick_year(key: str) -> Optional[int]:
        if key in data:
            val = data.get(key)
            return int(val) if str(val or "").strip().isdigit() else None
        existing_val = existing_map.get(key)
        return int(existing_val) if str(existing_val or "").strip().isdigit() else None

    def _pick_flag(key: str, default: int = 0) -> int:
        if key in data and data[key] is not None:
            return 1 if data[key] else 0
        if key in existing_map and existing_map[key] is not None:
            return 1 if existing_map[key] else 0
        return default

    tech_json = (
        json.dumps(_parse_list(data.get("tech_stack")))
        if "tech_stack" in data
        else (existing_map.get("tech_stack") or "[]")
    )
    kw_json = (
        json.dumps(_parse_list(data.get("keywords")))
        if "keywords" in data
        else (existing_map.get("keywords") or "[]")
    )
    tags_list = _parse_list(data.get("tags"))

    year_start = _pick_year("year_start")
    year_end = _pick_year("year_end")
    is_public = _pick_flag("is_public", 0)
    is_featured = _pick_flag("is_featured", 0)
    is_storefront = _pick_flag("is_storefront", 0)
    if "display_order" in data and data.get("display_order") is not None and str(data.get("display_order")).strip() != "":
        display_order = int(data["display_order"])
    elif existing_map.get("display_order") is not None:
        display_order = int(existing_map["display_order"])
    else:
        display_order = 99

    tagline_val = _pick_str("tagline", "")
    short_summary_val = _pick_str("short_summary", title) or title
    full_desc_val = _pick_str("full_description", short_summary_val) or short_summary_val
    category_val = _pick_str("category", "General Portfolio") or "General Portfolio"
    domain_stage_val = _pick_str("domain_stage", "02_ai_modeling") or "02_ai_modeling"
    project_kind_val = _pick_str("project_kind", "research") or "research"
    status_val = _pick_str("status", "Active") or "Active"
    inst_val = _pick_str("institution_or_org", "")
    grant_val = _pick_str("grant_award", "")
    code_snippet_val = _pick_str("code_snippet", "")
    license_val = _pick_str("license_model", "")
    price_val = _pick_str("price_display", "")
    sf_cat_val = _pick_str("storefront_category", "")
    disc_val = _pick_str("discovery_status", "reviewed" if pid else "canonical") or ("reviewed" if pid else "canonical")
    gdrive_url_val = _pick_str("gdrive_primary_url", "")

    if pid:
        cur.execute("""
            UPDATE projects SET
                slug = ?, title = ?, tagline = ?, short_summary = ?, full_description = ?,
                category = ?, domain_stage = ?, project_kind = ?, status = ?, year_start = ?, year_end = ?,
                institution_or_org = ?, grant_award = ?, tech_stack = ?, keywords = ?, code_snippet = ?,
                license_model = ?, price_display = ?, storefront_category = ?,
                is_featured = ?, is_storefront = ?, is_public = ?, display_order = ?,
                discovery_status = ?, gdrive_primary_url = ?, updated_at = ?
            WHERE id = ?
        """, (
            slug, title, tagline_val, short_summary_val, full_desc_val,
            category_val, domain_stage_val, project_kind_val, status_val, year_start, year_end,
            inst_val, grant_val, tech_json, kw_json, code_snippet_val,
            license_val, price_val, sf_cat_val,
            is_featured, is_storefront, is_public, display_order,
            disc_val, gdrive_url_val, now_iso,
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
                institution_or_org, grant_award, tech_stack, keywords, code_snippet,
                license_model, price_display, storefront_category,
                is_featured, is_storefront, is_public, display_order,
                project_kind, discovery_status, source_origin,
                gdrive_primary_url, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'portal', ?, ?)
        """, (
            slug, title, tagline_val, short_summary_val, full_desc_val,
            category_val, domain_stage_val, status_val, year_start, year_end,
            inst_val, grant_val, tech_json, kw_json, code_snippet_val,
            license_val, price_val, sf_cat_val,
            is_featured, is_storefront, is_public, display_order,
            project_kind_val, disc_val,
            gdrive_url_val, now_iso,
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


def _resolve_project_id(cur: sqlite3.Cursor, id_or_slug: Any) -> Optional[int]:
    if id_or_slug is None:
        return None
    if isinstance(id_or_slug, int) and id_or_slug > 0:
        row = cur.execute("SELECT id FROM projects WHERE id = ?", (id_or_slug,)).fetchone()
        return row[0] if row else None
    s = str(id_or_slug).strip()
    if s.isdigit() and int(s) > 0:
        row = cur.execute("SELECT id FROM projects WHERE id = ?", (int(s),)).fetchone()
        if row:
            return row[0]
    row = cur.execute("SELECT id FROM projects WHERE slug = ?", (s,)).fetchone()
    return row[0] if row else None


def merge_projects_in_db(
    conn: sqlite3.Connection,
    source: Any,
    target: Any,
    append_summary: bool = False,
    add_alias: bool = True,
) -> Dict[str, Any]:
    """Fold `source` project (artifacts, placements, tags, keywords, pubs) into `target` and delete `source`."""
    cur = conn.cursor()
    src_id = _resolve_project_id(cur, source)
    tgt_id = _resolve_project_id(cur, target)
    if not src_id or not tgt_id:
        raise ValueError(f"Could not resolve source ({source}) or target ({target}) project.")
    if src_id == tgt_id:
        raise ValueError("Source and target projects must be different.")

    src_row = cur.execute(
        "SELECT slug, title, short_summary, full_description, tech_stack, keywords, year_start, year_end FROM projects WHERE id = ?",
        (src_id,),
    ).fetchone()
    tgt_row = cur.execute(
        "SELECT slug, title, short_summary, full_description, tech_stack, keywords, year_start, year_end FROM projects WHERE id = ?",
        (tgt_id,),
    ).fetchone()
    src_slug, src_title, src_sum, src_desc, src_tech, src_kw, src_ys, src_ye = src_row
    tgt_slug, tgt_title, tgt_sum, tgt_desc, tgt_tech, tgt_kw, tgt_ys, tgt_ye = tgt_row

    # 1. Move artifacts (skip duplicates by url_or_rel_path or gdrive_file_id)
    existing_urls = {
        r[0] for r in cur.execute("SELECT url_or_rel_path FROM project_artifacts WHERE project_id = ?", (tgt_id,)).fetchall()
    }
    existing_gfids = {
        r[0] for r in cur.execute("SELECT gdrive_file_id FROM project_artifacts WHERE project_id = ? AND gdrive_file_id IS NOT NULL", (tgt_id,)).fetchall()
    }
    moved_artifacts = 0
    for aid, url_val, gfid in cur.execute(
        "SELECT id, url_or_rel_path, gdrive_file_id FROM project_artifacts WHERE project_id = ?", (src_id,)
    ).fetchall():
        if url_val in existing_urls or (gfid and gfid in existing_gfids):
            cur.execute("DELETE FROM project_artifacts WHERE id = ?", (aid,))
        else:
            cur.execute("UPDATE project_artifacts SET project_id = ? WHERE id = ?", (tgt_id, aid))
            existing_urls.add(url_val)
            if gfid:
                existing_gfids.add(gfid)
            moved_artifacts += 1

    # 2. Move placements
    existing_slots = {
        (r[0], r[1]) for r in cur.execute("SELECT page_slug, section_slot FROM project_placements WHERE project_id = ?", (tgt_id,)).fetchall()
    }
    moved_placements = 0
    for pl_id, p_slug, s_slot in cur.execute(
        "SELECT id, page_slug, section_slot FROM project_placements WHERE project_id = ?", (src_id,)
    ).fetchall():
        if (p_slug, s_slot) in existing_slots:
            cur.execute("DELETE FROM project_placements WHERE id = ?", (pl_id,))
        else:
            cur.execute("UPDATE project_placements SET project_id = ? WHERE id = ?", (tgt_id, pl_id))
            existing_slots.add((p_slug, s_slot))
            moved_placements += 1

    # 3. Move tags, publications, courses
    for (tag,) in cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (src_id,)).fetchall():
        cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (tgt_id, tag))
    for (pub_id,) in cur.execute("SELECT publication_id FROM project_publications WHERE project_id = ?", (src_id,)).fetchall():
        cur.execute("INSERT OR IGNORE INTO project_publications (project_id, publication_id) VALUES (?, ?)", (tgt_id, pub_id))
    for (crs_id,) in cur.execute("SELECT course_id FROM project_courses WHERE project_id = ?", (src_id,)).fetchall():
        cur.execute("INSERT OR IGNORE INTO project_courses (project_id, course_id) VALUES (?, ?)", (tgt_id, crs_id))

    # 4. Merge tech_stack, keywords (recording source title/slug as permanent alias), years, optional summary
    merged_tech = list(dict.fromkeys(_parse_list(tgt_tech) + _parse_list(src_tech)))
    merged_kw = _parse_list(tgt_kw) + _parse_list(src_kw)
    if add_alias:
        for alias in (src_title, src_slug):
            if alias and alias not in merged_kw:
                merged_kw.append(alias)
    merged_kw = list(dict.fromkeys(merged_kw))

    years = [y for y in (tgt_ys, tgt_ye, src_ys, src_ye) if isinstance(y, int)]
    new_ys = min(years) if years else tgt_ys
    new_ye = max(years) if years else tgt_ye
    new_desc = tgt_desc or tgt_sum or ""
    if append_summary and src_sum and src_sum not in new_desc:
        new_desc = f"{new_desc}\n\n[Merged from {src_title}]: {src_sum}".strip()

    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("""
        UPDATE projects
        SET tech_stack = ?, keywords = ?, year_start = ?, year_end = ?, full_description = ?, updated_at = ?
        WHERE id = ?
    """, (json.dumps(merged_tech), json.dumps(merged_kw), new_ys, new_ye, new_desc, now_iso, tgt_id))

    # 5. Delete source project
    cur.execute("DELETE FROM projects WHERE id = ?", (src_id,))
    conn.commit()
    return {
        "source_slug": src_slug,
        "target_slug": tgt_slug,
        "moved_artifacts": moved_artifacts,
        "moved_placements": moved_placements,
    }


def apply_patch_payload(conn: sqlite3.Connection, patch: Dict[str, Any]) -> Dict[str, int]:
    """Apply an ordered operations patch exported from static portal.html."""
    ensure_schema(conn.cursor())
    counts = {"saved": 0, "deleted": 0, "artifacts": 0, "placements": 0, "merged": 0}
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
        elif kind == "merge_projects":
            merge_projects_in_db(
                conn,
                payload.get("source") or payload.get("source_slug") or payload.get("source_id"),
                payload.get("target") or payload.get("target_slug") or payload.get("target_id"),
                append_summary=bool(payload.get("append_summary", False)),
                add_alias=bool(payload.get("add_alias", True)),
            )
            counts["merged"] += 1
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
