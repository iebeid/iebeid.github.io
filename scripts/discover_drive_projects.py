#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Smart Google Drive Project Discovery, Cross-Folder Linker & Update Watcher
==================================================================================================
Scans configured Google Drive roots (prioritizing `Workspace`) via the read-only `gdrive` CLI,
treats every meaningful body of work as a project ("everything is a project" — research, code,
manuscripts, presentations, poetry, essays, teaching, service, business, hobbies),
intelligently links scattered Drive artifacts across folders into unified canonical projects,
and logs incremental updates in `data/content.db` without auto-publishing private files.

Usage:
    python scripts/discover_drive_projects.py --dry-run --root Workspace/Research
    python scripts/discover_drive_projects.py --mode discover
    python scripts/discover_drive_projects.py --mode watch --since 2026-11-01T00:00:00Z
    python scripts/discover_drive_projects.py --mode discover --peek-docs --sync
"""

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_projects_backbone import ensure_schema, seed_drive_scan_roots  # noqa: E402
from reconcile_live_to_db import reconcile_live_to_db  # noqa: E402

FOLDER_MIME = "application/vnd.google-apps.folder"
GDOC_MIME = "application/vnd.google-apps.document"
GSHEET_MIME = "application/vnd.google-apps.spreadsheet"
GSLIDES_MIME = "application/vnd.google-apps.presentation"

SKIP_FOLDER_NAMES = {
    "external",
    "library",
    "__pycache__",
    ".git",
    ".idea",
    ".junie",
    ".vscode",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    "target",
    "bin",
    "obj",
    "tmp",
    "temp",
    "cache",
    "backups",
    "backup",
    "financial",
    "health",
    "legal",
    "security",
    "infrastructure",
    "family",
    "transcripts",
    "references",
    "cover letter",
    "planning",
}

NOISE_FILENAMES = {
    "desktop.ini",
    "thumbs.db",
    ".ds_store",
    ".gitignore",
    ".gitattributes",
    "__init__.py",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "license",
    "license.txt",
    "license.md",
}

STRIP_SUFFIX_TOKENS = {
    "grant",
    "proposal",
    "project",
    "website",
    "web",
    "ui",
    "app",
    "tool",
    "suite",
    "viewer",
    "sync",
    "data",
    "visualizations",
    "visualization",
    "viz",
    "paper",
    "manuscript",
    "slides",
    "presentation",
    "deck",
    "final",
    "draft",
    "edited",
    "layout",
    "engine",
    "system",
    "systems",
    "model",
    "models",
    "v1",
    "v2",
    "v3",
}

GENERIC_MATCH_WORDS = {
    "society",
    "club",
    "group",
    "meetup",
    "chapter",
    "class",
    "course",
    "lecture",
    "lectures",
    "assignment",
    "assignments",
    "notes",
    "learning",
    "study",
    "analysis",
    "dallas",
    "austin",
    "texas",
    "arkansas",
    "ut",
    "twu",
    "ualr",
    "uams",
}

ARTIFACT_SIGNAL_EXTS = {
    ".pdf", ".pptx", ".ppt", ".docx", ".doc", ".md", ".txt", ".ipynb",
    ".py", ".js", ".ts", ".cpp", ".c", ".h", ".java", ".r", ".jl",
    ".mp4", ".mov", ".webm", ".zip", ".tar", ".gz", ".csv", ".tsv", ".json",
    ".png", ".jpg", ".jpeg", ".svg",
}

# Known project aliases that help bridge shorthand folder names to canonical projects
KNOWN_ALIASES = {
    "digcn": "protgram-directgcn",
    "multivariategcn": "protgram-directgcn",
    "protgram": "protgram-directgcn",
    "autoprompt": "multimodal-med-seg",
    "autopromptgrant": "multimodal-med-seg",
    "visintx": "xlpm-visintx",
    "xlpm": "xlpm-visintx",
    "xlpmol": "xlpmol-viewer",
    "ditk": "dataintegrationtoolkit",
    "moder": "moder-grapher",
    "medgraph": "medgraph-pubmed-kg",
    "chem2bio2rdf": "chem2bio2rdf-drug-repurposing",
    "eyeart": "eyeadapt-gdwm",
    "eyeadapt": "eyeadapt-gdwm",
    "eyeadaptui": "eyeadapt-gdwm",
    "gdwm": "eyeadapt-gdwm",
    "caveinabox": "cave-realtime-scanner",
    "caveobjectscanner": "cave-realtime-scanner",
    "clusterwebgl": "cluster-webgl-earthviz",
    "clustersyncwebgl": "cluster-webgl-earthviz",
    "googleearthdatavisualizations": "cluster-webgl-earthviz",
    "googleearthvisualizations": "cluster-webgl-earthviz",
    "smartpromo": "smart-promotion-tool",
    "smarthrm": "smart-promotion-tool",
    "moroccosmartpromotool": "smart-promotion-tool",
    "contractprintlayout": "contract-print-bscs",
    "atuciswebsite": "atu-cis-web",
}


GDRIVE_BIN = shutil.which("gdrive") or "gdrive"


def run_gdrive_json(args: List[str], timeout: int = 45) -> Any:
    cmd = [GDRIVE_BIN, *args, "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"gdrive {' '.join(args)} failed: {res.stderr.strip() or res.stdout.strip()}")
    out = (res.stdout or "").strip()
    if not out or out == "null":
        return []
    return json.loads(out)


def list_folder_children(folder_id: str, modified_after: Optional[str] = None) -> List[Dict[str, Any]]:
    args = ["readonly", "search", "--parent-id", folder_id, "--max", "500"]
    if modified_after:
        args.extend(["--modified-after", modified_after])
    data = run_gdrive_json(args)
    return data if isinstance(data, list) else []


def peek_gdrive_text(file_item: Dict[str, Any]) -> str:
    """Best-effort short text extraction for Google Docs or small README/txt/md files."""
    fid = file_item["id"]
    mime = file_item.get("mimeType", "")
    name = (file_item.get("name") or "").lower()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "peek.txt"
        try:
            if mime == GDOC_MIME:
                subprocess.run(
                    [GDRIVE_BIN, "readonly", "export", fid, str(tmp_path), "--format", "txt"],
                    capture_output=True, text=True, timeout=25, check=True,
                )
            elif name.endswith((".md", ".txt")) or mime.startswith("text/"):
                subprocess.run(
                    [GDRIVE_BIN, "readonly", "download", fid, "--out", str(tmp_path)],
                    capture_output=True, text=True, timeout=25, check=True,
                )
            else:
                return ""
            if tmp_path.exists():
                text = tmp_path.read_text(encoding="utf-8", errors="ignore")
                cleaned = re.sub(r"\s+", " ", text).strip()
                return cleaned[:1200]
        except Exception:
            return ""
    return ""


def split_camel_and_tokens(text: str) -> List[str]:
    s = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", text or "")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
    return [tok for tok in s.split() if tok]


def normalize_compact(text: str) -> str:
    tokens = split_camel_and_tokens(text)
    return "".join(tokens)


def normalize_core_tokens(text: str) -> List[str]:
    tokens = split_camel_and_tokens(text)
    core = [t for t in tokens if t not in STRIP_SUFFIX_TOKENS and not re.fullmatch(r"20\d{2}", t)]
    return core or tokens


def humanize_title(raw_name: str) -> str:
    name = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", raw_name or "").strip()
    if " " in name or ("-" in name and len(name.split("-")) > 2):
        return re.sub(r"[_]+", " ", name).strip()
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", spaced)
    spaced = re.sub(r"[_-]+", " ", spaced)
    return re.sub(r"\s+", " ", spaced).strip() or raw_name


def slugify(text: str) -> str:
    s = "-".join(split_camel_and_tokens(text))
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:64] or "drive-project"


def infer_sharing_status(item: Dict[str, Any]) -> str:
    perms = item.get("permissions") or []
    for p in perms:
        if p.get("type") == "anyone":
            return "public_anyone"
    return "private" if perms else "unknown"


def infer_web_url(item: Dict[str, Any]) -> str:
    if item.get("webViewLink"):
        return item["webViewLink"]
    fid = item["id"]
    if item.get("mimeType") == FOLDER_MIME:
        return f"https://drive.google.com/drive/folders/{fid}"
    return f"https://drive.google.com/file/d/{fid}/view"


def classify_artifact_type(item: Dict[str, Any], rel_path: str) -> Tuple[str, str]:
    mime = item.get("mimeType", "")
    name = (item.get("name") or "").lower()
    path_low = rel_path.lower()

    if mime == FOLDER_MIME:
        return "gdrive_folder", "Drive Folder"
    if "/poetry/" in path_low:
        return "poem_draft", "Poetry"
    if mime == GDOC_MIME or name.endswith((".docx", ".doc")):
        if "/manuscripts/" in path_low or "paper" in name or "manuscript" in name:
            return "manuscript", "Doc"
        return "doc", "Doc"
    if mime == GSLIDES_MIME or name.endswith((".pptx", ".ppt")):
        return "slides", "Slides"
    if mime == GSHEET_MIME or name.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        return "dataset", "Sheet"
    if name.endswith(".pdf"):
        if "poster" in name:
            return "poster", "PDF"
        if "slide" in name or "/presentations/" in path_low or "/lectures/" in path_low:
            return "slides", "PDF"
        return "paper_pdf", "PDF"
    if name.endswith((".mp4", ".mov", ".avi", ".webm", ".mkv")):
        return "video", "Video"
    if name.endswith((".mp3", ".wav", ".m4a")):
        return "audio", "Audio"
    if name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return "screenshot", "Image"
    if name.endswith((".zip", ".tar.gz", ".tgz", ".7z")):
        return "source_zip", "Archive"
    if name.endswith((".py", ".ipynb", ".js", ".ts", ".cpp", ".c", ".java", ".r", ".jl", ".md")):
        return "code_repo", Path(name).suffix.lstrip(".").upper() or "Code"
    return "design_doc", "File"


def infer_domain_metadata(rel_parts: List[str], root_default_kind: str) -> Tuple[str, str, List[str]]:
    """Return (category, project_kind, extra_tags) from Workspace relative path."""
    low = [p.lower() for p in rel_parts]
    tags: List[str] = []

    if len(low) >= 2 and low[0] == "workspace":
        domain = low[1]
    elif low:
        domain = low[0]
    else:
        domain = root_default_kind

    if domain == "research":
        tags.append("Research")
        if "code" in low and len(low) >= 5:
            discipline = rel_parts[4].replace("-", " ").title()
            tags.append(discipline)
            disc_l = discipline.lower()
            if "bio" in disc_l:
                return "AI & Life Sciences", "research", tags
            if "graph" in disc_l or "language" in disc_l or "artificial" in disc_l:
                return "AI & Life Sciences", "research", tags
            if "data" in disc_l:
                return "Data Engineering & Entity Resolution", "research", tags
            if "vision" in disc_l or "graphics" in disc_l or "human" in disc_l:
                return "Scientific Visualization & HCI", "research", tags
        if "videos" in low or "images" in low:
            return "Scientific Visualization & HCI", "research", tags
        return "AI & Life Sciences", "research", tags

    if domain == "scholarship":
        tags.append("Scholarship")
        if "poetry" in low:
            tags.append("Poetry")
            return "Scholarship & Poetry", "poetry", tags
        if "lecturing" in low:
            tags.append("Lecturing")
            return "Scholarship & Lecturing", "scholarship", tags
        if "code" in low:
            tags.append("Scholarship Code")
            return "Scholarship & Computational Humanities", "scholarship", tags
        return "Scholarship & Writings", "scholarship", tags

    if domain == "teaching":
        tags.append("Teaching")
        return "Teaching & Courseware", "teaching", tags
    if domain == "business":
        tags.append("Business")
        return "Industry & Enterprise Systems", "business", tags
    if domain == "service":
        tags.append("Service")
        return "Service & Community Leadership", "service", tags
    if domain == "hobbies":
        tags.append("Hobbies")
        return "Creative Works & Hobbies", "hobby", tags
    if domain == "education":
        tags.append("Education")
        return "Education & Academic Milestones", "education", tags
    if domain == "relations":
        tags.append("Relations")
        return "Collaborations & Relations", "relations", tags
    if domain == "career":
        tags.append("Career")
        return "Career & Academic Dossier", "career", tags

    return "General Portfolio", root_default_kind or "research", tags


class DriveProjectScanner:
    def __init__(self, conn: sqlite3.Connection, dry_run: bool = False, peek_docs: bool = False, workers: int = 4):
        self.conn = conn
        self.cur = conn.cursor()
        self.dry_run = dry_run
        self.peek_docs = peek_docs
        self.workers = max(1, workers)

        # In-memory index of canonical & discovered projects for cross-folder linking
        self.project_index: List[Dict[str, Any]] = []
        self.slug_to_entry: Dict[str, Dict[str, Any]] = {}
        self.known_artifact_ids: set[str] = set()
        self._load_existing_projects()

    def _load_existing_projects(self):
        rows = self.cur.execute("""
            SELECT id, slug, title, tagline, grant_award, keywords, discovery_status, gdrive_primary_folder_id
            FROM projects
            ORDER BY id
        """).fetchall()
        for pid, slug, title, tagline, grant_award, kw_raw, dstatus, primary_fid in rows:
            try:
                kw = json.loads(kw_raw) if kw_raw else []
            except Exception:
                kw = []
            tags = [r[0] for r in self.cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (pid,)).fetchall()]
            arts = self.cur.execute(
                "SELECT label, url_or_rel_path, gdrive_file_id FROM project_artifacts WHERE project_id = ?",
                (pid,),
            ).fetchall()
            art_terms = []
            for label, url_val, gfid in arts:
                if gfid:
                    self.known_artifact_ids.add(gfid)
                if label:
                    art_terms.append(label)
                if url_val and not url_val.startswith("http"):
                    art_terms.append(Path(url_val).stem)

            entry = {
                "id": pid,
                "slug": slug,
                "title": title,
                "compact_title": normalize_compact(title),
                "compact_slug": normalize_compact(slug),
                "core_tokens": set(normalize_core_tokens(title) + normalize_core_tokens(slug)),
                "aliases": set([normalize_compact(x) for x in ([title, slug] + kw + art_terms) if x]),
                "grant_numbers": set(re.findall(r"\b\d{6,8}\b", grant_award or "")),
                "tags": set(tags),
                "discovery_status": dstatus or "canonical",
                "primary_fid": primary_fid or "",
            }
            self.project_index.append(entry)
            self.slug_to_entry[slug] = entry

    def match_candidate_to_project(self, candidate_name: str, rel_parts: List[str], peek_text: str = "") -> Tuple[Optional[Dict[str, Any]], float, str]:
        cand_compact = normalize_compact(candidate_name)
        cand_core_str = "".join(normalize_core_tokens(candidate_name))
        cand_tokens = set(normalize_core_tokens(candidate_name))

        # 0. Explicit alias map
        for alias_key, target_slug in KNOWN_ALIASES.items():
            if cand_compact == alias_key or cand_core_str == alias_key:
                entry = self.slug_to_entry.get(target_slug)
                if entry:
                    return entry, 0.97, f"alias_match:{alias_key}->{target_slug}"

        best_entry = None
        best_score = 0.0
        best_reason = ""

        # Do NOT cross-link poetry/individual teaching lectures blindly to unrelated research projects
        is_isolated_creative = any(p.lower() in ("poetry", "drafts", "submissions") for p in rel_parts)

        for entry in self.project_index:
            # 1. Exact compact match against title/slug/aliases
            if cand_compact and (cand_compact in entry["aliases"] or cand_core_str in entry["aliases"]):
                return entry, 0.96, f"exact_alias:{candidate_name}"

            if is_isolated_creative and entry["discovery_status"] == "canonical":
                continue

            # 2. Substring / containment for distinctive project identifiers with comparable lengths
            target_len = len(entry["compact_slug"])
            cand_len = len(cand_core_str)
            len_ratio = min(cand_len, target_len) / max(1, max(cand_len, target_len))
            if cand_len >= 6 and target_len >= 6 and (
                cand_core_str == entry["compact_slug"]
                or cand_core_str == entry["compact_title"]
                or (len_ratio >= 0.60 and (cand_core_str in entry["compact_slug"] or entry["compact_slug"] in cand_core_str))
            ):
                score = 0.90
                if score > best_score:
                    best_entry, best_score, best_reason = entry, score, f"name_containment:{candidate_name}->{entry['slug']}"
                continue

            # 3. Token Jaccard + SequenceMatcher (ignore generic/location words in overlap check)
            if cand_tokens and entry["core_tokens"]:
                sig_cand = cand_tokens - GENERIC_MATCH_WORDS
                sig_entry = entry["core_tokens"] - GENERIC_MATCH_WORDS
                inter = sig_cand & sig_entry
                union = (sig_cand | sig_entry) or (cand_tokens | entry["core_tokens"])
                jaccard = len(inter) / max(1, len(union))
                seq = SequenceMatcher(None, cand_core_str, entry["compact_title"]).ratio()
                combined = 0.60 * jaccard + 0.40 * seq
                if len(inter) >= 2 and jaccard >= 0.55:
                    combined = max(combined, 0.84)
                if len(inter) == 0:
                    combined = 0.0
                if combined > best_score:
                    best_entry = entry
                    best_score = combined
                    best_reason = f"fuzzy_match:{candidate_name}~{entry['slug']}({combined:.2f})"

            # 4. Content peek match (grant numbers or title inside doc/README)
            if peek_text:
                peek_low = peek_text.lower()
                for gnum in entry["grant_numbers"]:
                    if gnum in peek_low:
                        return entry, 0.93, f"grant_id_match:{gnum}"
                if len(entry["title"]) >= 8 and entry["title"].lower() in peek_low:
                    if 0.86 > best_score:
                        best_entry, best_score, best_reason = entry, 0.86, f"content_title_match:{entry['title']}"

        if best_entry and best_score >= 0.78:
            return best_entry, best_score, best_reason
        return None, 0.0, ""

    def should_skip_folder(self, name: str) -> bool:
        low = (name or "").strip().lower()
        return low in SKIP_FOLDER_NAMES or low.startswith(".")

    def is_project_unit_folder(self, rel_parts: List[str], child_items: List[Dict[str, Any]]) -> bool:
        """Decide if a Drive folder represents an atomic project container vs. a category/bucket folder."""
        low = [p.lower() for p in rel_parts]
        depth_in_ws = len(low) - (1 if low and low[0] == "workspace" else 0)

        # Workspace/Research patterns:
        if "research" in low:
            idx = low.index("research")
            sub = low[idx + 1:]
            # Images/<Project> or Videos/<Project>
            if len(sub) == 2 and sub[0] in ("images", "videos"):
                return True
            # Manuscripts/Internal/<Project>, Presentations/Internal/<Project>, Data/Internal/<Project>
            if len(sub) == 3 and sub[0] in ("manuscripts", "presentations", "data") and sub[1] == "internal":
                return True
            # Code/Internal/<Discipline>/<Project>
            if len(sub) == 4 and sub[0] == "code" and sub[1] == "internal":
                return True
            # Never treat top-level bucket folders as projects
            if len(sub) <= 1 or (len(sub) == 2 and sub[1] == "internal") or (len(sub) == 3 and sub[0] == "code" and sub[1] == "internal"):
                return False

        # Workspace/Scholarship patterns:
        if "scholarship" in low:
            idx = low.index("scholarship")
            sub = low[idx + 1:]
            # Poetry/Drafts and Poetry/Submissions hold individual poem files -> do NOT collapse into one folder project
            if len(sub) >= 1 and sub[0] == "poetry":
                return len(sub) >= 3  # only if a poem has its own subfolder
            if len(sub) == 2 and sub[0] in ("manuscripts", "code", "images", "lecturing"):
                return True
            if len(sub) <= 1:
                return False

        # Workspace/Teaching patterns:
        if "teaching" in low:
            idx = low.index("teaching")
            sub = low[idx + 1:]
            if len(sub) == 2 and sub[0] in ("assignments", "code", "lectures"):
                return True
            if len(sub) <= 1:
                return False

        # Workspace/Business/Unity Systems/<Project>
        if "business" in low:
            idx = low.index("business")
            sub = low[idx + 1:]
            if len(sub) >= 2:
                return True
            if len(sub) == 1:
                # If Business/<Org> has subfolders, descend; if only files, treat as project
                has_subdirs = any(c.get("mimeType") == FOLDER_MIME and not self.should_skip_folder(c.get("name", "")) for c in child_items)
                return not has_subdirs

        # General rule for other folders (Service, Hobbies, Education, Career, Relations, or non-Workspace roots):
        if depth_in_ws <= 1:
            return False
        subdirs = [c for c in child_items if c.get("mimeType") == FOLDER_MIME and not self.should_skip_folder(c.get("name", ""))]
        files = [c for c in child_items if c.get("mimeType") != FOLDER_MIME and (c.get("name") or "").lower() not in NOISE_FILENAMES]
        if files and not subdirs:
            return True
        if depth_in_ws >= 3 and (files or subdirs):
            return True
        return False

    def collect_candidates_from_root(
        self,
        root_name: str,
        root_folder_id: str,
        default_kind: str,
        max_depth: int = 4,
        modified_after: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Walk a Drive root (in parallel breadth levels) and emit project candidates."""
        candidates: List[Dict[str, Any]] = []
        files_scanned = 0

        root_parts = [p for p in root_name.split("/") if p]
        # Queue items: (folder_id, folder_name, rel_parts, folder_item_or_none, depth)
        frontier: List[Tuple[str, str, List[str], Optional[Dict[str, Any]], int]] = [
            (root_folder_id, root_parts[-1], root_parts, None, 0)
        ]

        while frontier:
            next_frontier: List[Tuple[str, str, List[str], Optional[Dict[str, Any]], int]] = []
            children_by_idx: Dict[int, List[Dict[str, Any]]] = {}

            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                future_map = {
                    pool.submit(list_folder_children, fid, modified_after if depth == 0 else None): idx
                    for idx, (fid, _, _, _, depth) in enumerate(frontier)
                }
                for fut in as_completed(future_map):
                    idx = future_map[fut]
                    try:
                        children_by_idx[idx] = fut.result()
                    except Exception as exc:
                        print(f"[WARN] Could not list folder {frontier[idx][0]} ({'/'.join(frontier[idx][2])}): {exc}")
                        children_by_idx[idx] = []

            for idx, (fid, fname, rel_parts, folder_item, depth) in enumerate(frontier):
                items = children_by_idx.get(idx, [])
                files_scanned += len(items)

                # If this folder itself is a project unit, collect it and its immediate artifacts
                if depth > 0 and self.is_project_unit_folder(rel_parts, items):
                    artifacts = [
                        it for it in items
                        if (it.get("name") or "").lower() not in NOISE_FILENAMES
                    ]
                    candidates.append({
                        "candidate_name": fname,
                        "rel_parts": rel_parts,
                        "folder_item": folder_item or {"id": fid, "name": fname, "mimeType": FOLDER_MIME},
                        "artifacts": artifacts,
                        "default_kind": default_kind,
                        "is_single_file": False,
                    })
                    continue

                # Otherwise inspect children: loose high-signal files may be standalone projects (e.g. Poetry/Drafts)
                low_parts = [p.lower() for p in rel_parts]
                allow_loose_files = (
                    depth >= 1
                    and (
                        "poetry" in low_parts
                        or "internal" in low_parts
                        or "manuscripts" in low_parts
                        or "presentations" in low_parts
                        or "lecturing" in low_parts
                        or "hobbies" in low_parts
                        or "service" in low_parts
                        or "teaching" in low_parts
                        or "business" in low_parts
                        or "career" in low_parts
                        or "education" in low_parts
                    )
                )

                for it in items:
                    iname = it.get("name") or ""
                    if it.get("mimeType") == FOLDER_MIME:
                        if self.should_skip_folder(iname):
                            continue
                        if depth + 1 <= max_depth:
                            next_frontier.append((it["id"], iname, rel_parts + [iname], it, depth + 1))
                    elif allow_loose_files:
                        ilow = iname.lower()
                        if ilow in NOISE_FILENAMES:
                            continue
                        ext = Path(ilow).suffix
                        is_google_native = (it.get("mimeType") or "").startswith("application/vnd.google-apps.")
                        if is_google_native or ext in ARTIFACT_SIGNAL_EXTS:
                            candidates.append({
                                "candidate_name": Path(iname).stem if not is_google_native else iname,
                                "rel_parts": rel_parts + [iname],
                                "folder_item": None,
                                "artifacts": [it],
                                "default_kind": default_kind,
                                "is_single_file": True,
                            })

            frontier = next_frontier

        return candidates, files_scanned

    def select_key_artifacts(self, cand: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pick the folder + highest-signal artifacts without flooding with 50 source files."""
        selected: List[Dict[str, Any]] = []
        if cand.get("folder_item"):
            selected.append(cand["folder_item"])

        items = cand.get("artifacts", [])
        if cand.get("is_single_file"):
            return items[:1]

        def score_file(it: Dict[str, Any]) -> Tuple[int, str]:
            name = (it.get("name") or "").lower()
            mime = it.get("mimeType", "")
            if "readme" in name:
                return (0, name)
            if mime in (GDOC_MIME, GSLIDES_MIME, GSHEET_MIME):
                return (1, name)
            if name.endswith((".pdf", ".pptx", ".docx")):
                return (2, name)
            if name.endswith((".mp4", ".mov", ".webm", ".ipynb")):
                return (3, name)
            if name.endswith((".png", ".jpg", ".jpeg", ".zip")):
                return (4, name)
            if name.endswith((".py", ".js", ".cpp", ".md", ".txt")):
                return (5, name)
            return (9, name)

        non_folders = [it for it in items if it.get("mimeType") != FOLDER_MIME]
        non_folders.sort(key=score_file)
        selected.extend(non_folders[:5])
        return selected

    def ensure_unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        idx = 2
        while slug in self.slug_to_entry:
            slug = f"{base_slug}-{idx}"
            idx += 1
        return slug

    def process_candidates(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats = {
            "projects_discovered": 0,
            "artifacts_linked": 0,
            "cross_links_matched": 0,
            "actions": [],
        }

        for cand in candidates:
            cand_name = cand["candidate_name"]
            rel_parts = cand["rel_parts"]
            rel_path_str = "/".join(rel_parts)

            peek_text = ""
            if self.peek_docs:
                for it in cand.get("artifacts", []):
                    nm = (it.get("name") or "").lower()
                    if it.get("mimeType") == GDOC_MIME or nm == "readme.md" or (cand.get("is_single_file") and nm.endswith((".txt", ".md"))):
                        peek_text = peek_gdrive_text(it)
                        if peek_text:
                            break

            matched_entry, score, reason = self.match_candidate_to_project(cand_name, rel_parts, peek_text)
            category, proj_kind, extra_tags = infer_domain_metadata(rel_parts, cand["default_kind"])
            key_artifacts = self.select_key_artifacts(cand)

            # Extract year span from modified/created timestamps
            years = []
            for it in key_artifacts:
                for ts_key in ("createdTime", "modifiedTime"):
                    ts = it.get(ts_key) or ""
                    if len(ts) >= 4 and ts[:4].isdigit():
                        years.append(int(ts[:4]))
            year_start = min(years) if years else None
            year_end = max(years) if years else None

            if matched_entry:
                pid = matched_entry["id"]
                slug = matched_entry["slug"]
                stats["cross_links_matched"] += 1
                match_tag = reason
                target_label = f"LINK -> [{slug}] ({reason})"
            else:
                base_slug = slugify(cand_name)
                slug = self.ensure_unique_slug(base_slug)
                title = humanize_title(cand_name)
                summary = (
                    peek_text[:280].rsplit(" ", 1)[0] + "..."
                    if len(peek_text) > 280
                    else (peek_text or f"Discovered {proj_kind} project located at Google Drive `{rel_path_str}`.")
                )
                folder_item = cand.get("folder_item")
                primary_fid = folder_item["id"] if folder_item else key_artifacts[0]["id"]
                primary_url = infer_web_url(folder_item or key_artifacts[0])
                now_iso = datetime.now(timezone.utc).isoformat()

                if not self.dry_run:
                    self.cur.execute("""
                        INSERT INTO projects (
                            slug, title, tagline, short_summary, full_description,
                            category, domain_stage, status, year_start, year_end,
                            institution_or_org, tech_stack, is_featured, is_storefront,
                            is_public, display_order, project_kind, keywords,
                            discovery_status, source_origin, confidence_score,
                            gdrive_primary_folder_id, gdrive_primary_url, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'discovered', 'Discovered (Draft)', ?, ?, '', '[]', 0, 0, 0, 500, ?, ?, 'discovered', 'gdrive_discovery', ?, ?, ?, ?)
                    """, (
                        slug, title, f"Drive Source: {rel_path_str}", summary, summary,
                        category, year_start, year_end, proj_kind,
                        json.dumps(list({cand_name, title, *extra_tags})),
                        0.85, primary_fid, primary_url, now_iso,
                    ))
                    pid = self.cur.lastrowid
                    for t in extra_tags:
                        self.cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (pid, t))
                else:
                    pid = -1

                new_entry = {
                    "id": pid,
                    "slug": slug,
                    "title": title,
                    "compact_title": normalize_compact(title),
                    "compact_slug": normalize_compact(slug),
                    "core_tokens": set(normalize_core_tokens(title) + normalize_core_tokens(slug)),
                    "aliases": set([normalize_compact(title), normalize_compact(slug), normalize_compact(cand_name)]),
                    "grant_numbers": set(),
                    "tags": set(extra_tags),
                    "discovery_status": "discovered",
                    "primary_fid": primary_fid,
                }
                self.project_index.append(new_entry)
                self.slug_to_entry[slug] = new_entry
                stats["projects_discovered"] += 1
                match_tag = "new_discovery"
                target_label = f"NEW -> [{slug}] '{title}' ({proj_kind})"

            linked_here = 0
            for order_idx, it in enumerate(key_artifacts, 1):
                fid = it["id"]
                web_url = infer_web_url(it)
                a_type, badge = classify_artifact_type(it, rel_path_str)
                sharing = infer_sharing_status(it)
                mod_at = it.get("modifiedTime") or ""
                mime = it.get("mimeType") or ""
                art_label = f"{it.get('name', cand_name)} (Drive)"

                if fid in self.known_artifact_ids:
                    if not self.dry_run:
                        self.cur.execute("""
                            UPDATE project_artifacts
                            SET gdrive_modified_at = ?, sharing_status = ?, gdrive_path = ?
                            WHERE gdrive_file_id = ?
                        """, (mod_at, sharing, f"{rel_path_str}/{it.get('name', '')}", fid))
                    continue

                if not self.dry_run and pid > 0:
                    self.cur.execute("""
                        INSERT OR IGNORE INTO project_artifacts (
                            project_id, artifact_type, label, url_or_rel_path, format_badge,
                            display_order, storage_source, gdrive_file_id, gdrive_url,
                            gdrive_path, mime_type, gdrive_modified_at, sharing_status,
                            is_public, match_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, 'gdrive', ?, ?, ?, ?, ?, ?, 0, ?)
                    """, (
                        pid, a_type, art_label, web_url, badge,
                        100 + order_idx, fid, web_url,
                        f"{rel_path_str}/{it.get('name', '')}", mime, mod_at, sharing, match_tag,
                    ))
                    if self.cur.rowcount > 0:
                        self.known_artifact_ids.add(fid)
                        linked_here += 1
                        stats["artifacts_linked"] += 1
                else:
                    self.known_artifact_ids.add(fid)
                    linked_here += 1
                    stats["artifacts_linked"] += 1

            if linked_here > 0 or not matched_entry:
                stats["actions"].append(f"{target_label} | +{linked_here} artifact(s) | {rel_path_str}")

        return stats


def main():
    parser = argparse.ArgumentParser(description="Smart Google Drive Project Discovery & Cross-Folder Linker")
    parser.add_argument("--mode", choices=["discover", "watch"], default="discover", help="discover (full scoped scan) or watch (incremental modified-after scan)")
    parser.add_argument("--root", action="append", default=[], help="Specific drive_scan_roots root_name(s) to scan (e.g. Workspace/Research)")
    parser.add_argument("--since", default=None, help="ISO timestamp override for watch mode (e.g. 2026-11-01T00:00:00Z)")
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum folder recursion depth inside each root")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent Drive API workers")
    parser.add_argument("--peek-docs", action="store_true", help="Read brief snippets from READMEs / Google Docs to enrich summaries and linking")
    parser.add_argument("--dry-run", action="store_true", help="Simulate discovery and print planned links without writing to content.db")
    parser.add_argument("--reset-discovered", action="store_true", help="Clear previously auto-discovered projects/Drive artifacts before re-scanning (preserves canonical projects)")
    parser.add_argument("--skip-reconcile", action="store_true", help="Skip reconciling live portal GitHub commits before scanning Drive")
    parser.add_argument("--sync", action="store_true", help="Run sync_content.py --export-only after updating content.db")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}")
        return 1

    # Ensure gdrive CLI token is valid before spawning concurrent workers
    auth_check = subprocess.run([GDRIVE_BIN, "auth", "status"], capture_output=True, text=True)
    if auth_check.returncode != 0 or "Not logged in" in (auth_check.stdout or ""):
        print("[ERROR] gdrive CLI is not authenticated. Run `gdrive auth login` first.")
        return 1

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ensure_schema(cur)
    seed_drive_scan_roots(cur)
    if not args.skip_reconcile and not args.dry_run:
        rec = reconcile_live_to_db(conn, DB_PATH)
        if rec.get("reconciled"):
            print(f"[RECONCILE] Absorbed live portal edits into content.db: {rec}")
    if args.reset_discovered and not args.dry_run:
        cur.execute("DELETE FROM project_artifacts WHERE storage_source = 'gdrive' AND is_public = 0")
        cur.execute("DELETE FROM projects WHERE discovery_status = 'discovered' AND source_origin = 'gdrive_discovery'")
    conn.commit()

    # Select roots to scan
    if args.root:
        placeholders = ",".join("?" for _ in args.root)
        roots = cur.execute(f"""
            SELECT id, root_name, gdrive_folder_id, priority, default_kind, last_scanned_at
            FROM drive_scan_roots
            WHERE is_excluded = 0 AND root_name IN ({placeholders})
            ORDER BY priority, id
        """, args.root).fetchall()
    else:
        # Default to Workspace domain roots (excluding the top umbrella 'Workspace' row if specific Workspace/* roots exist)
        roots = cur.execute("""
            SELECT id, root_name, gdrive_folder_id, priority, default_kind, last_scanned_at
            FROM drive_scan_roots
            WHERE is_excluded = 0 AND root_name != 'Workspace'
            ORDER BY priority, id
        """).fetchall()

    if not roots:
        print("[WARN] No matching active drive_scan_roots found.")
        conn.close()
        return 0

    scanner = DriveProjectScanner(conn, dry_run=args.dry_run, peek_docs=args.peek_docs, workers=args.workers)
    started_at = datetime.now(timezone.utc).isoformat()
    total_files = 0
    total_new_projects = 0
    total_linked = 0
    total_cross = 0

    print("=" * 72)
    print(f"Google Drive Project Discovery (mode={args.mode}, dry_run={args.dry_run}, peek_docs={args.peek_docs})")
    print("=" * 72)

    for root_id, root_name, folder_id, prio, default_kind, last_scanned in roots:
        mod_after = None
        if args.mode == "watch":
            mod_after = args.since or last_scanned

        print(f"\n[SCAN P{prio}] {root_name} (folder={folder_id}, modified_after={mod_after or 'ALL'})...")
        candidates, fcount = scanner.collect_candidates_from_root(
            root_name=root_name,
            root_folder_id=folder_id,
            default_kind=default_kind,
            max_depth=args.max_depth,
            modified_after=mod_after,
        )
        res = scanner.process_candidates(candidates)
        total_files += fcount
        total_new_projects += res["projects_discovered"]
        total_linked += res["artifacts_linked"]
        total_cross += res["cross_links_matched"]

        print(
            f"  -> scanned={fcount} entries, candidates={len(candidates)}, "
            f"new_projects={res['projects_discovered']}, cross_linked={res['cross_links_matched']}, "
            f"new_artifacts={res['artifacts_linked']}"
        )
        for line in res["actions"][:25]:
            print(f"     * {line}")
        if len(res["actions"]) > 25:
            print(f"     ... ({len(res['actions']) - 25} more actions)")

        if not args.dry_run:
            cur.execute(
                "UPDATE drive_scan_roots SET last_scanned_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), root_id),
            )

    finished_at = datetime.now(timezone.utc).isoformat()
    if not args.dry_run:
        cur.execute("""
            INSERT INTO drive_scan_runs (
                started_at, finished_at, mode, root_name, files_scanned, projects_discovered, artifacts_linked, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            started_at, finished_at, args.mode,
            ",".join(r[1] for r in roots),
            total_files, total_new_projects, total_linked,
            f"cross_links_matched={total_cross}",
        ))
        conn.commit()

    conn.close()

    print("\n" + "=" * 72)
    print(
        f"SUMMARY: files_scanned={total_files} | new_projects={total_new_projects} | "
        f"cross_linked={total_cross} | new_artifacts={total_linked}"
    )
    print("=" * 72)

    if args.sync and not args.dry_run:
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
