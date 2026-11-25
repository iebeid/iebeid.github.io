#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Local Portal Command Center Server
==========================================================
Serves `iebeid.github.io` locally and exposes loopback REST endpoints backed
directly by `data/content.db` so edits, deletions, Drive artifact links, and
website card placements made in `pages/portal/portal.html` persist immediately
to SQLite and can sync/verify with one click.

Usage:
    python scripts/portal_server.py
    python scripts/portal_server.py --port 8765
"""

import argparse
import functools
import http.server
import json
import secrets
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from apply_portal_patch import (  # noqa: E402
    apply_patch_payload,
    delete_artifact_record,
    delete_project_record,
    merge_projects_in_db,
    save_artifact_record,
    save_project_record,
    set_project_placements,
)
from build_projects_backbone import ensure_schema  # noqa: E402
from database_manager import decrypt_secret, encrypt_secret  # noqa: E402
from import_portal_bookmarks import apply_portal_state  # noqa: E402

SERVER_CSRF_TOKEN = secrets.token_hex(24)

SITE_PLACEMENT_SLOTS = [
    {"page_slug": "home", "section_slot": "featured", "label": "Home — Current Research & Flagship Systems"},
    {"page_slug": "research", "section_slot": "ai_life_sciences", "label": "Research — AI & Life Sciences / Bioinformatics"},
    {"page_slug": "research", "section_slot": "data_engineering", "label": "Research — Data Quality, Engineering & NLP"},
    {"page_slug": "research", "section_slot": "visualization_hci", "label": "Research — Scientific Visualization & HCI"},
    {"page_slug": "research", "section_slot": "legacy_industry", "label": "Research — Legacy & Industry Systems"},
    {"page_slug": "research", "section_slot": "projects", "label": "Research — Additional Cross-Disciplinary Projects"},
    {"page_slug": "storefront", "section_slot": "catalog", "label": "Storefront — Commercial Software Catalog"},
    {"page_slug": "education", "section_slot": "projects", "label": "Education — Academic Milestones & Projects"},
    {"page_slug": "scholarship", "section_slot": "projects", "label": "Scholarship — Writings, Essays, Lectures & Poetry"},
    {"page_slug": "teaching", "section_slot": "projects", "label": "Teaching — Courseware & Teaching Portfolio"},
    {"page_slug": "service", "section_slot": "projects", "label": "Service — Leadership & Outreach Initiatives"},
    {"page_slug": "business", "section_slot": "projects", "label": "Business — Applied Consulting & Commercial"},
    {"page_slug": "hobbies", "section_slot": "projects", "label": "Hobbies — Creative Works, Travel & Personal"},
    {"page_slug": "media", "section_slot": "projects", "label": "Media — Talks, Podcasts & Featured Media"},
    {"page_slug": "relations", "section_slot": "projects", "label": "Relations — Collaborations & Mentorship"},
    {"page_slug": "downloads", "section_slot": "projects", "label": "Downloads — Shared Project Bundles"},
    {"page_slug": "lab", "section_slot": "projects", "label": "Lab — Data2AI4LifeSciences Lab Projects"},
    {"page_slug": "talk-index", "section_slot": "projects", "label": "Talks — Related Presentation Projects"},
]


def _parse_json_list(raw_val: Any):
    try:
        parsed = json.loads(raw_val) if raw_val else []
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return [t.strip() for t in str(raw_val or "").split(",") if t.strip()]


def fetch_master_bundle(conn: sqlite3.Connection) -> Dict[str, Any]:
    cur = conn.cursor()
    ensure_schema(cur)
    cur.execute("""
        SELECT id, slug, title, tagline, short_summary, full_description,
               category, domain_stage, status, year_start, year_end,
               institution_or_org, grant_award, tech_stack, code_snippet,
               license_model, price_display, storefront_category,
               is_featured, is_storefront, is_public, display_order,
               project_kind, keywords, discovery_status, source_origin,
               confidence_score, gdrive_primary_folder_id, gdrive_primary_url, updated_at
        FROM projects
        ORDER BY display_order, id
    """)
    projects = []
    for pr in cur.fetchall():
        pid = pr[0]
        cur.execute("""
            SELECT id, artifact_type, label, url_or_rel_path, format_badge, document_id,
                   display_order, storage_source, gdrive_file_id, gdrive_url, gdrive_path,
                   mime_type, gdrive_modified_at, md5_checksum, sharing_status,
                   COALESCE(is_public, 1), match_reason
            FROM project_artifacts
            WHERE project_id = ?
            ORDER BY display_order, id
        """, (pid,))
        artifacts = [
            {
                "id": ar[0],
                "type": ar[1],
                "label": ar[2],
                "url": ar[3],
                "badge": ar[4] or "",
                "document_id": ar[5],
                "display_order": ar[6] or 0,
                "storage_source": ar[7] or "repo",
                "gdrive_file_id": ar[8] or "",
                "gdrive_url": ar[9] or "",
                "gdrive_path": ar[10] or "",
                "mime_type": ar[11] or "",
                "gdrive_modified_at": ar[12] or "",
                "md5_checksum": ar[13] or "",
                "sharing_status": ar[14] or "unknown",
                "is_public": bool(ar[15]),
                "match_reason": ar[16] or "",
            }
            for ar in cur.fetchall()
        ]
        cur.execute("SELECT tag FROM project_tags WHERE project_id = ? ORDER BY tag", (pid,))
        tags = [tr[0] for tr in cur.fetchall()]

        cur.execute("""
            SELECT id, page_slug, section_slot, card_variant, display_order, is_visible
            FROM project_placements
            WHERE project_id = ?
            ORDER BY display_order, id
        """, (pid,))
        placements = [
            {
                "id": pl[0],
                "page_slug": pl[1],
                "section_slot": pl[2],
                "card_variant": pl[3] or "research-cards",
                "display_order": pl[4] or 0,
                "is_visible": bool(pl[5]),
            }
            for pl in cur.fetchall()
        ]

        projects.append({
            "id": pid,
            "slug": pr[1],
            "title": pr[2],
            "tagline": pr[3] or "",
            "short_summary": pr[4] or "",
            "full_description": pr[5] or "",
            "category": pr[6],
            "domain_stage": pr[7] or "foundational",
            "status": pr[8] or "",
            "year_start": pr[9],
            "year_end": pr[10],
            "institution_or_org": pr[11] or "",
            "grant_award": pr[12] or "",
            "tech_stack": _parse_json_list(pr[13]),
            "code_snippet": pr[14] or "",
            "license_model": pr[15] or "",
            "price_display": pr[16] or "",
            "storefront_category": pr[17] or "",
            "is_featured": bool(pr[18]),
            "is_storefront": bool(pr[19]),
            "is_public": bool(pr[20]),
            "display_order": pr[21] or 0,
            "project_kind": pr[22] or "research",
            "keywords": _parse_json_list(pr[23]),
            "discovery_status": pr[24] or "canonical",
            "source_origin": pr[25] or "manual",
            "confidence_score": pr[26] if pr[26] is not None else 1.0,
            "gdrive_primary_folder_id": pr[27] or "",
            "gdrive_primary_url": pr[28] or "",
            "updated_at": pr[29] or "",
            "artifacts": artifacts,
            "placements": placements,
            "tags": tags,
        })

    cur.execute("""
        SELECT id, root_name, gdrive_folder_id, priority, default_kind, default_page_slug, is_excluded, last_scanned_at
        FROM drive_scan_roots ORDER BY priority, root_name
    """)
    roots = [
        {
            "id": r[0],
            "root_name": r[1],
            "gdrive_folder_id": r[2],
            "priority": r[3],
            "default_kind": r[4],
            "default_page_slug": r[5] or "",
            "is_excluded": bool(r[6]),
            "last_scanned_at": r[7] or "",
        }
        for r in cur.fetchall()
    ]

    cur.execute("""
        SELECT id, started_at, finished_at, mode, root_name, files_scanned, projects_discovered, artifacts_linked, notes
        FROM drive_scan_runs ORDER BY id DESC LIMIT 20
    """)
    runs = [
        {
            "id": r[0],
            "started_at": r[1],
            "finished_at": r[2] or "",
            "mode": r[3],
            "root_name": r[4] or "",
            "files_scanned": r[5] or 0,
            "projects_discovered": r[6] or 0,
            "artifacts_linked": r[7] or 0,
            "notes": r[8] or "",
        }
        for r in cur.fetchall()
    ]

    return {
        "projects": projects,
        "placement_slots": SITE_PLACEMENT_SLOTS,
        "drive_scan_roots": roots,
        "drive_scan_runs": runs,
    }


class PortalRequestHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, payload: Dict[str, Any], status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _is_loopback_request_allowed(self, require_csrf: bool = False) -> bool:
        host_hdr = (self.headers.get("Host") or "").split(":")[0].strip().lower()
        if host_hdr not in ("127.0.0.1", "localhost", "[::1]"):
            self._send_json({"ok": False, "error": "Forbidden Host header (DNS rebinding guard)."}, 403)
            return False

        sec_site = (self.headers.get("Sec-Fetch-Site") or "").strip().lower()
        if sec_site and sec_site not in ("same-origin", "none"):
            self._send_json({"ok": False, "error": "Cross-site browser requests are forbidden."}, 403)
            return False

        origin = (self.headers.get("Origin") or "").strip().lower()
        if origin:
            parsed_origin = urlparse(origin)
            if parsed_origin.hostname not in ("127.0.0.1", "localhost", "::1"):
                self._send_json({"ok": False, "error": "Cross-origin requests are forbidden."}, 403)
                return False

        if require_csrf:
            ctype = (self.headers.get("Content-Type") or "").lower()
            if not ctype.startswith("application/json"):
                self._send_json({"ok": False, "error": "Content-Type: application/json required."}, 415)
                return False
            token = (self.headers.get("X-Portal-CSRF") or "").strip()
            if not token or not secrets.compare_digest(token, SERVER_CSRF_TOKEN):
                self._send_json({"ok": False, "error": "Invalid or missing X-Portal-CSRF token. Refresh Portal tab."}, 403)
                return False
        return True

    def _is_blocked_static_path(self, url_path: str) -> bool:
        norm = "/" + url_path.lstrip("/").replace("\\", "/").lower()
        blocked_prefixes = ("/.git", "/.idea", "/.junie", "/scripts/", "/data/content.db")
        blocked_suffixes = (".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".pyc", ".env")
        if any(norm == p.rstrip("/") or norm.startswith(p) for p in blocked_prefixes):
            return True
        if norm.endswith(blocked_suffixes):
            return True
        return False

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            if not self._is_loopback_request_allowed(require_csrf=False):
                return
            self._send_json({
                "ok": True,
                "mode": "sqlite-live",
                "db_path": str(DB_PATH),
                "csrf_token": SERVER_CSRF_TOKEN,
            })
            return
        if path == "/api/projects":
            if not self._is_loopback_request_allowed(require_csrf=False):
                return
            conn = sqlite3.connect(DB_PATH)
            try:
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, **bundle})
            finally:
                conn.close()
            return
        if self._is_blocked_static_path(path):
            self._send_json({"ok": False, "error": "Forbidden static resource."}, 403)
            return
        super().do_GET()

    def do_POST(self):
        if not self._is_loopback_request_allowed(require_csrf=True):
            return
        path = urlparse(self.path).path
        try:
            body = self._read_json_body()
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Invalid JSON: {exc}"}, 400)
            return

        if path == "/api/vault/rotate-passcode":
            cur_pass = str(body.get("current_passcode") or "")
            new_pass = str(body.get("new_passcode") or "")
            if len(new_pass) < 6:
                self._send_json({"ok": False, "error": "New passcode must be at least 6 characters."}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            try:
                cur = conn.cursor()
                rows = cur.execute("SELECT key, ciphertext, nonce, salt, description FROM portal_vault").fetchall()
                decrypted_entries = {}
                for k, ct, nc, slt, desc in rows:
                    try:
                        plain = decrypt_secret({"ciphertext": ct, "nonce": nc, "salt": slt}, cur_pass)
                    except Exception:
                        self._send_json({"ok": False, "error": "Current passcode did not match SQLite portal_vault."}, 403)
                        return
                    decrypted_entries[k] = (plain, desc or "")

                decrypted_entries["master_passcode"] = (
                    new_pass,
                    decrypted_entries.get("master_passcode", ("", "Portal Master Passcode"))[1] or "Portal Master Passcode",
                )
                now_str = datetime.now().isoformat()
                for k, (plain_val, desc) in decrypted_entries.items():
                    enc = encrypt_secret(plain_val, new_pass)
                    cur.execute("""
                        INSERT INTO portal_vault (key, ciphertext, nonce, salt, description, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET
                            ciphertext = excluded.ciphertext,
                            nonce = excluded.nonce,
                            salt = excluded.salt,
                            description = excluded.description,
                            updated_at = excluded.updated_at
                    """, (k, enc["ciphertext"], enc["nonce"], enc["salt"], desc, now_str))
                conn.commit()
            finally:
                conn.close()

            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only", "--skip-reconcile"],
                capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
            )
            self._send_json({"ok": True, "rotated_keys": len(decrypted_entries)})
            return

        if path == "/api/projects/save":
            conn = sqlite3.connect(DB_PATH)
            try:
                pid = save_project_record(conn, body)
                if "placements" in body and isinstance(body["placements"], list):
                    set_project_placements(conn, pid, body["placements"], auto_public_if_placed=bool(body.get("auto_public", True)))
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "project_id": pid, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/projects/delete":
            conn = sqlite3.connect(DB_PATH)
            try:
                deleted = delete_project_record(conn, body.get("id"), body.get("slug"))
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "deleted": deleted, **bundle})
            finally:
                conn.close()
            return

        if path == "/api/projects/merge":
            conn = sqlite3.connect(DB_PATH)
            try:
                info = merge_projects_in_db(
                    conn,
                    body.get("source") or body.get("source_id") or body.get("source_slug"),
                    body.get("target") or body.get("target_id") or body.get("target_slug"),
                    append_summary=bool(body.get("append_summary", False)),
                    add_alias=bool(body.get("add_alias", True)),
                )
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "merge": info, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/artifacts/save":
            conn = sqlite3.connect(DB_PATH)
            try:
                aid = save_artifact_record(conn, body)
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "artifact_id": aid, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/artifacts/delete":
            conn = sqlite3.connect(DB_PATH)
            try:
                deleted = delete_artifact_record(conn, int(body["id"]))
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "deleted": deleted, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/placements/set":
            conn = sqlite3.connect(DB_PATH)
            try:
                cnt = set_project_placements(
                    conn,
                    body.get("project_id"),
                    body.get("placements") or [],
                    auto_public_if_placed=bool(body.get("auto_public", True)),
                    project_slug=body.get("project_slug"),
                )
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "visible_count": cnt, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/patch/apply":
            conn = sqlite3.connect(DB_PATH)
            try:
                counts = apply_patch_payload(conn, body)
                bundle = fetch_master_bundle(conn)
                self._send_json({"ok": True, "counts": counts, **bundle})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, 400)
            finally:
                conn.close()
            return

        if path == "/api/portal-state/import":
            conn = sqlite3.connect(DB_PATH)
            try:
                stats = apply_portal_state(conn, body)
            except Exception as exc:
                conn.close()
                self._send_json({"ok": False, "error": str(exc)}, 400)
                return
            conn.close()
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"],
                capture_output=True, text=True, cwd=str(REPO_ROOT), check=True,
            )
            self._send_json({"ok": True, "stats": stats})
            return

        if path == "/api/sync":
            cmd = [sys.executable, str(SCRIPTS_DIR / "sync_content.py")]
            if body.get("push"):
                pass
            elif body.get("commit"):
                cmd.append("--no-push")
            else:
                cmd.append("--export-only")
            if body.get("message"):
                cmd.extend(["-m", str(body["message"])])
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
            ver = subprocess.run([sys.executable, str(SCRIPTS_DIR / "verify_render.py")], capture_output=True, text=True, cwd=str(REPO_ROOT))
            self._send_json({
                "ok": res.returncode == 0 and ver.returncode == 0,
                "sync_output": res.stdout + res.stderr,
                "verify_output": ver.stdout + ver.stderr,
            }, 200 if res.returncode == 0 else 500)
            return

        if path == "/api/discover":
            mode = body.get("mode") if body.get("mode") in ("discover", "watch") else "watch"
            cmd = [sys.executable, str(SCRIPTS_DIR / "discover_drive_projects.py"), "--mode", mode, "--sync"]
            if body.get("peek_docs"):
                cmd.append("--peek-docs")
            if body.get("root"):
                cmd.extend(["--root", str(body["root"])])
            res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300)
            conn = sqlite3.connect(DB_PATH)
            try:
                bundle = fetch_master_bundle(conn)
            finally:
                conn.close()
            self._send_json({
                "ok": res.returncode == 0,
                "output": res.stdout + res.stderr,
                **bundle,
            }, 200 if res.returncode == 0 else 500)
            return

        self._send_json({"ok": False, "error": f"Unknown endpoint: {path}"}, 404)


def main():
    parser = argparse.ArgumentParser(description="Local SQLite-backed Portal Command Center Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    handler = functools.partial(PortalRequestHandler, directory=str(REPO_ROOT))
    server = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    print("=" * 68)
    print(f"Portal Command Center Server running at http://{args.host}:{args.port}/")
    print(f"Open Portal UI : http://{args.host}:{args.port}/pages/portal/portal.html")
    print(f"Backed by DB   : {DB_PATH}")
    print("Press Ctrl+C to stop.")
    print("=" * 68)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
