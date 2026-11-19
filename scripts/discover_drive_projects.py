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
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
AI_CACHE_PATH = REPO_ROOT / "data" / "ai_discovery_cache.json"
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
    "eyeart": "eyeart",
    "eyeadapt": "eyeadapt-engine",
    "eyeadaptui": "eyeadapt-engine",
    "eyeadaptengine": "eyeadapt-engine",
    "gdwm": "gdwm",
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


class SemanticDiscoveryValidator:
    """
    AI-model-based semantic validator & project matcher injected into Drive discovery.

    Because the `gdrive` CLI only provides raw folder/file metadata and exports,
    this validator uses Gemini Flash to:
      1. Cross-Link Guard (Stage A): Verify heuristic/alias matches before linking so
         unrelated projects (e.g. acronym collisions like GDWM vs EyeAdapt) are VETOED
         and kept as separate projects.
      2. Semantic Discovery (Stage B): Match unmatched Drive folders to existing projects
         when folder names differ semantically (acronyms, sub-projects, renamed repos).
      3. Semantic Enrichment (Stage C): Generate factual summaries, taglines, tags, and
         keywords for newly discovered projects from folder paths, filenames, and excerpts.
    """

    DEFAULT_MODELS = [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, api_key: str, cache_path: Path = AI_CACHE_PATH, model: str = "gemini-3.8-flash"):
        self.api_key = (api_key or "").strip()
        self.cache_path = cache_path
        self.preferred_model = model
        self.sticky_model: Optional[str] = None
        self.deprioritized: set[str] = set()
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8")) or {}
            except Exception:
                return {}
        return {}

    def save_cache(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _fingerprint(obj: Any) -> str:
        raw = json.dumps(obj, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def _call_gemini_json(self, prompt: str) -> Any:
        ordered = []
        for m in [self.sticky_model, self.preferred_model, *self.DEFAULT_MODELS]:
            if m and m not in ordered:
                ordered.append(m)
        ordered = [m for m in ordered if m not in self.deprioritized] + [m for m in ordered if m in self.deprioritized]

        last_err: Optional[Exception] = None
        for idx, mdl in enumerate(ordered):
            has_more = idx + 1 < len(ordered)
            max_attempts = 1 if has_more else 3
            use_thinking = True
            attempt = 0
            while attempt < max_attempts:
                attempt += 1
                gen_cfg: Dict[str, Any] = {"responseMimeType": "application/json", "maxOutputTokens": 8192}
                if use_thinking:
                    if mdl.startswith(("gemini-3", "gemini-4")):
                        gen_cfg["thinkingConfig"] = {"thinkingLevel": "low"}
                    elif mdl.startswith("gemini-2.5") and "lite" not in mdl:
                        gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={self.api_key}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps({
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": gen_cfg,
                    }).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    txt = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    txt = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", txt).strip()
                    parsed = json.loads(txt)
                    self.sticky_model = mdl
                    self.deprioritized.discard(mdl)
                    return parsed
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode("utf-8", errors="ignore")
                    last_err = RuntimeError(f"Gemini {mdl} HTTP {exc.code}: {body[:260]}")
                    if exc.code == 400 and use_thinking and "thinking" in body.lower():
                        use_thinking = False
                        attempt -= 1
                        continue
                    if exc.code in (401, 403):
                        raise last_err from exc
                    if exc.code == 404 or "not found" in body.lower() or "no longer available" in body.lower():
                        self.deprioritized.add(mdl)
                        break
                    if exc.code in (429, 500, 502, 503, 504):
                        if attempt < max_attempts:
                            time.sleep(1.5 * (2 ** (attempt - 1)))
                            continue
                        self.deprioritized.add(mdl)
                        if has_more:
                            break
                    raise last_err from exc
                except Exception as exc:
                    last_err = exc
                    if attempt < max_attempts:
                        time.sleep(1.0 * attempt)
                        continue
                    if has_more:
                        self.deprioritized.add(mdl)
                        break
                    raise
        raise last_err or RuntimeError("Gemini semantic discovery call failed")

    def validate_proposed_links(self, proposals: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Stage A: Validate candidate-to-project cross-links in batches.
        Returns map[proposal_id] -> {"same_project": bool, "confidence": float, "reason": str}
        """
        results: Dict[str, Dict[str, Any]] = {}
        to_query: List[Dict[str, Any]] = []
        fp_map: Dict[str, str] = {}

        for prop in proposals:
            pid = prop["proposal_id"]
            fp = "link:" + self._fingerprint({
                "cand_name": prop["cand_name"],
                "rel_path": prop["rel_path"],
                "files": prop["sample_files"],
                "target_slug": prop["target_slug"],
                "target_title": prop["target_title"],
                "target_summary": prop["target_summary"][:200],
            })
            fp_map[pid] = fp
            if fp in self.cache:
                results[pid] = self.cache[fp]
            else:
                to_query.append(prop)

        for i in range(0, len(to_query), 15):
            batch = to_query[i:i + 15]
            prompt = (
                "You are a strict semantic entity-resolution validator for Dr. Islam Akef Ebeid's research, "
                "software, and academic Google Drive portfolio.\n"
                "For each proposed folder-to-project link below, judge whether the Drive folder truly belongs "
                "to the EXACT SAME underlying project as the target project.\n"
                "CRITICAL RULES:\n"
                "- Do NOT conflate unrelated projects that merely share a broad topic or an ambiguous acronym "
                "(for example: EyeAdapt/EyeAdaptUI eye-tracking vs EyeArt poster vs GDWM entity-resolution/ITNG paper "
                "are THREE SEPARATE projects).\n"
                "- Look closely at the candidate filenames, Drive path, and excerpt vs target title, summary, and existing artifacts.\n"
                "- Return ONLY a JSON array: "
                '[{"proposal_id": str, "same_project": true|false, "confidence": 0.0-1.0, "reason": "concise 6-14 word reason"}].\n\n'
                + json.dumps(batch, ensure_ascii=False)
            )
            try:
                raw = self._call_gemini_json(prompt)
                arr = raw if isinstance(raw, list) else (raw.get("results") or raw.get("items") or [] if isinstance(raw, dict) else [])
                for item in arr:
                    pid = str(item.get("proposal_id") or "")
                    if not pid or pid not in fp_map:
                        continue
                    verdict = {
                        "same_project": bool(item.get("same_project", True)),
                        "confidence": float(item.get("confidence", 0.5)),
                        "reason": str(item.get("reason") or ""),
                    }
                    results[pid] = verdict
                    self.cache[fp_map[pid]] = verdict
                self.save_cache()
            except Exception as exc:
                print(f"  [AI-VALIDATOR WARN] Link validation batch failed (keeping heuristic): {exc}")
        return results

    def discover_semantic_matches(
        self,
        unmatched: List[Dict[str, Any]],
        project_catalog: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Stage B & C: For Drive candidates with no heuristic match, ask Gemini whether they
        semantically match any existing project in the catalog (by acronym/topic/filenames),
        or if genuinely new, generate factual title/summary/tags/keywords.
        """
        results: Dict[str, Dict[str, Any]] = {}
        to_query: List[Dict[str, Any]] = []
        fp_map: Dict[str, str] = {}

        compact_catalog = [
            {
                "slug": e["slug"],
                "title": e["title"],
                "category": e.get("category") or "",
                "summary": (e.get("short_summary") or "")[:140],
            }
            for e in project_catalog
        ]
        cat_fp = self._fingerprint([c["slug"] for c in compact_catalog])

        for item in unmatched:
            cid = item["cand_id"]
            fp = "disc:" + self._fingerprint({
                "cand_name": item["cand_name"],
                "rel_path": item["rel_path"],
                "files": item["sample_files"],
                "cat_fp": cat_fp,
            })
            fp_map[cid] = fp
            if fp in self.cache:
                results[cid] = self.cache[fp]
            else:
                to_query.append(item)

        for i in range(0, len(to_query), 15):
            batch = to_query[i:i + 15]
            prompt = (
                "You are performing semantic project discovery on Dr. Islam Akef Ebeid's Google Drive.\n"
                "Given EXISTING_PROJECTS and NEW_DRIVE_CANDIDATES, decide for each candidate whether it is:\n"
                "1. An exact/semantic continuation of ONE existing project (matched_slug != null, confidence >= 0.80), OR\n"
                "2. A genuinely separate project (matched_slug = null), in which case generate a factual short_summary, tagline, tags, and keywords.\n"
                "Be conservative: never merge distinct projects just because they are in the same broad field.\n"
                "Return ONLY a JSON array: "
                '[{"cand_id": str, "matched_slug": str|null, "confidence": 0.0-1.0, "reason": str, '
                '"short_summary": "1-2 factual sentences", "tagline": "5-9 word subtitle", "tags": ["2-4 tags"], "keywords": ["2-5 keywords"]}].\n\n'
                + json.dumps({"EXISTING_PROJECTS": compact_catalog, "NEW_DRIVE_CANDIDATES": batch}, ensure_ascii=False)
            )
            try:
                raw = self._call_gemini_json(prompt)
                arr = raw if isinstance(raw, list) else (raw.get("results") or raw.get("items") or [] if isinstance(raw, dict) else [])
                for item in arr:
                    cid = str(item.get("cand_id") or "")
                    if not cid or cid not in fp_map:
                        continue
                    verdict = {
                        "matched_slug": item.get("matched_slug") or None,
                        "confidence": float(item.get("confidence", 0.0)),
                        "reason": str(item.get("reason") or ""),
                        "short_summary": str(item.get("short_summary") or "").strip(),
                        "tagline": str(item.get("tagline") or "").strip(),
                        "tags": [str(t).strip() for t in (item.get("tags") or []) if str(t).strip()],
                        "keywords": [str(k).strip() for k in (item.get("keywords") or []) if str(k).strip()],
                    }
                    results[cid] = verdict
                    self.cache[fp_map[cid]] = verdict
                self.save_cache()
            except Exception as exc:
                print(f"  [AI-VALIDATOR WARN] Semantic discovery batch failed (falling back to draft): {exc}")
        return results


class DriveProjectScanner:
    def __init__(
        self,
        conn: sqlite3.Connection,
        dry_run: bool = False,
        peek_docs: bool = False,
        workers: int = 4,
        ai_validator: Optional[SemanticDiscoveryValidator] = None,
    ):
        self.conn = conn
        self.cur = conn.cursor()
        self.dry_run = dry_run
        self.peek_docs = peek_docs
        self.workers = max(1, workers)
        self.ai_validator = ai_validator

        # In-memory index of canonical & discovered projects for cross-folder linking
        self.project_index: List[Dict[str, Any]] = []
        self.slug_to_entry: Dict[str, Dict[str, Any]] = {}
        self.known_artifact_ids: set[str] = set()
        self._load_existing_projects()

    def _load_existing_projects(self):
        rows = self.cur.execute("""
            SELECT id, slug, title, tagline, short_summary, category, grant_award, keywords, discovery_status, gdrive_primary_folder_id
            FROM projects
            ORDER BY id
        """).fetchall()
        for pid, slug, title, tagline, short_summary, category, grant_award, kw_raw, dstatus, primary_fid in rows:
            try:
                kw = json.loads(kw_raw) if kw_raw else []
            except Exception:
                kw = []
            tags = [r[0] for r in self.cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (pid,)).fetchall()]
            arts = self.cur.execute(
                "SELECT label, url_or_rel_path, gdrive_file_id, gdrive_path FROM project_artifacts WHERE project_id = ?",
                (pid,),
            ).fetchall()
            art_terms = []
            sample_arts = []
            for label, url_val, gfid, gpath in arts:
                if gfid:
                    self.known_artifact_ids.add(gfid)
                if label:
                    art_terms.append(label)
                    sample_arts.append(gpath or label)
                if url_val and not url_val.startswith("http"):
                    art_terms.append(Path(url_val).stem)

            entry = {
                "id": pid,
                "slug": slug,
                "title": title,
                "short_summary": short_summary or tagline or "",
                "category": category or "",
                "sample_artifacts": sample_arts[:6],
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
            "ai_vetoed_links": 0,
            "ai_semantic_matches": 0,
            "actions": [],
        }

        # Pre-pass: gather peek text, key artifacts, and initial heuristic proposals
        prepared: List[Dict[str, Any]] = []
        link_proposals: List[Dict[str, Any]] = []
        unmatched_for_ai: List[Dict[str, Any]] = []

        for idx, cand in enumerate(candidates):
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
            key_artifacts = self.select_key_artifacts(cand)
            sample_files = [it.get("name", "") for it in key_artifacts[:8] if it.get("name")]
            folder_item = cand.get("folder_item")
            folder_fid = folder_item["id"] if folder_item else ""

            rec = {
                "idx": idx,
                "cand": cand,
                "cand_name": cand_name,
                "rel_parts": rel_parts,
                "rel_path_str": rel_path_str,
                "peek_text": peek_text,
                "matched_entry": matched_entry,
                "score": score,
                "reason": reason,
                "key_artifacts": key_artifacts,
                "sample_files": sample_files,
                "ai_meta": None,
            }
            prepared.append(rec)

            if self.ai_validator:
                # Stage A: Validate heuristic/alias links (skip only when exact Drive folder ID already belongs to target)
                if matched_entry and not (folder_fid and folder_fid == matched_entry.get("primary_fid")):
                    link_proposals.append({
                        "proposal_id": f"p{idx}",
                        "cand_name": cand_name,
                        "rel_path": rel_path_str,
                        "sample_files": sample_files,
                        "peek_excerpt": peek_text[:300],
                        "heuristic_reason": reason,
                        "target_slug": matched_entry["slug"],
                        "target_title": matched_entry["title"],
                        "target_category": matched_entry.get("category") or "",
                        "target_summary": (matched_entry.get("short_summary") or "")[:240],
                        "target_artifacts": matched_entry.get("sample_artifacts") or [],
                    })
                elif not matched_entry:
                    unmatched_for_ai.append({
                        "cand_id": f"c{idx}",
                        "cand_name": cand_name,
                        "rel_path": rel_path_str,
                        "sample_files": sample_files,
                        "peek_excerpt": peek_text[:300],
                    })

        # Run batch AI Semantic Validation (Stage A) and Semantic Discovery (Stage B & C)
        if self.ai_validator:
            if link_proposals:
                verdicts = self.ai_validator.validate_proposed_links(link_proposals)
                for rec in prepared:
                    pid = f"p{rec['idx']}"
                    v = verdicts.get(pid)
                    if v and (not v.get("same_project")) and float(v.get("confidence", 0.0)) >= 0.65:
                        old_slug = rec["matched_entry"]["slug"] if rec["matched_entry"] else ""
                        rec["matched_entry"] = None
                        rec["reason"] = f"ai_vetoed:{old_slug}({v.get('reason', '')})"
                        stats["ai_vetoed_links"] += 1
                        unmatched_for_ai.append({
                            "cand_id": f"c{rec['idx']}",
                            "cand_name": rec["cand_name"],
                            "rel_path": rec["rel_path_str"],
                            "sample_files": rec["sample_files"],
                            "peek_excerpt": rec["peek_text"][:300],
                        })
                    elif v and v.get("same_project"):
                        rec["reason"] = f"{rec['reason']}|ai_verified({v.get('confidence', 0):.2f})"

            if unmatched_for_ai:
                disc_verdicts = self.ai_validator.discover_semantic_matches(unmatched_for_ai, self.project_index)
                for rec in prepared:
                    cid = f"c{rec['idx']}"
                    dv = disc_verdicts.get(cid)
                    if not dv:
                        continue
                    rec["ai_meta"] = dv
                    mslug = dv.get("matched_slug")
                    if mslug and float(dv.get("confidence", 0.0)) >= 0.80 and mslug in self.slug_to_entry:
                        rec["matched_entry"] = self.slug_to_entry[mslug]
                        rec["score"] = float(dv.get("confidence", 0.85))
                        rec["reason"] = f"ai_semantic_match:{mslug}({dv.get('reason', '')})"
                        stats["ai_semantic_matches"] += 1

        for rec in prepared:
            cand = rec["cand"]
            cand_name = rec["cand_name"]
            rel_parts = rec["rel_parts"]
            rel_path_str = rec["rel_path_str"]
            peek_text = rec["peek_text"]
            matched_entry = rec["matched_entry"]
            reason = rec["reason"]
            key_artifacts = rec["key_artifacts"]
            ai_meta = rec["ai_meta"] or {}

            category, proj_kind, extra_tags = infer_domain_metadata(rel_parts, cand["default_kind"])

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
                ai_summary = ai_meta.get("short_summary") or ""
                ai_tagline = ai_meta.get("tagline") or f"Drive Source: {rel_path_str}"
                merged_tags = list(dict.fromkeys([*extra_tags, *(ai_meta.get("tags") or [])]))
                merged_kw = list(dict.fromkeys([cand_name, title, *merged_tags, *(ai_meta.get("keywords") or [])]))
                summary = ai_summary or (
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
                        slug, title, ai_tagline, summary, summary,
                        category, year_start, year_end, proj_kind,
                        json.dumps(merged_kw),
                        0.90 if ai_summary else 0.85, primary_fid, primary_url, now_iso,
                    ))
                    pid = self.cur.lastrowid
                    for t in merged_tags:
                        self.cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (pid, t))
                else:
                    pid = -1

                new_entry = {
                    "id": pid,
                    "slug": slug,
                    "title": title,
                    "short_summary": summary,
                    "category": category,
                    "sample_artifacts": rec["sample_files"][:6],
                    "compact_title": normalize_compact(title),
                    "compact_slug": normalize_compact(slug),
                    "core_tokens": set(normalize_core_tokens(title) + normalize_core_tokens(slug)),
                    "aliases": set([normalize_compact(title), normalize_compact(slug), normalize_compact(cand_name)]),
                    "grant_numbers": set(),
                    "tags": set(merged_tags),
                    "discovery_status": "discovered",
                    "primary_fid": primary_fid,
                }
                self.project_index.append(new_entry)
                self.slug_to_entry[slug] = new_entry
                stats["projects_discovered"] += 1
                match_tag = reason if reason.startswith("ai_vetoed:") else "new_discovery"
                target_label = f"NEW -> [{slug}] '{title}' ({proj_kind})" + (f" [{reason}]" if reason.startswith("ai_vetoed:") else "")

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
    parser.add_argument("--ai-validate", action="store_true", help="Require Gemini AI semantic validator during discovery (auto-enabled when GEMINI_API_KEY is set)")
    parser.add_argument("--no-ai-validate", action="store_true", help="Disable Gemini AI semantic validator even if GEMINI_API_KEY is set")
    parser.add_argument("--gemini-key", default=None, help="Gemini API key override (defaults to GEMINI_API_KEY env var)")
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

    api_key = (args.gemini_key or os.environ.get("GEMINI_API_KEY") or "").strip()
    ai_validator: Optional[SemanticDiscoveryValidator] = None
    if not args.no_ai_validate and api_key:
        ai_validator = SemanticDiscoveryValidator(api_key=api_key)
    elif args.ai_validate and not api_key:
        print("[ERROR] --ai-validate requested, but GEMINI_API_KEY is not set.")
        conn.close()
        return 1

    scanner = DriveProjectScanner(
        conn,
        dry_run=args.dry_run,
        peek_docs=args.peek_docs,
        workers=args.workers,
        ai_validator=ai_validator,
    )
    started_at = datetime.now(timezone.utc).isoformat()
    total_files = 0
    total_new_projects = 0
    total_linked = 0
    total_cross = 0
    total_ai_vetoed = 0
    total_ai_semantic = 0

    print("=" * 72)
    print(
        f"Google Drive Project Discovery (mode={args.mode}, dry_run={args.dry_run}, "
        f"peek_docs={args.peek_docs}, ai_validator={'ON' if ai_validator else 'OFF (set GEMINI_API_KEY)'})"
    )
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
        total_ai_vetoed += res.get("ai_vetoed_links", 0)
        total_ai_semantic += res.get("ai_semantic_matches", 0)

        print(
            f"  -> scanned={fcount} entries, candidates={len(candidates)}, "
            f"new_projects={res['projects_discovered']}, cross_linked={res['cross_links_matched']}, "
            f"ai_vetoed={res.get('ai_vetoed_links', 0)}, ai_semantic={res.get('ai_semantic_matches', 0)}, "
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
