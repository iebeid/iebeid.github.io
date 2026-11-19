#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Smart & Semantic Project Entity Resolution Engine
=========================================================================
Detects non-exact semantic duplicate projects across `data/content.db` using:
  1. Domain synonym expansion & morphological normalization
  2. Acronym / initialism matching (e.g. GDWM <-> Gaze Directed World Model, GE <-> Google Earth)
  3. TF-IDF weighted cosine similarity across title, summary, tags, and Drive artifact paths
  4. Character 3-gram cosine similarity across normalized titles/slugs
  5. Shared evidence signals (URLs, GitHub repos, grant numbers, artifact labels)

Also supports manual merging of any two projects via CLI (`--merge SOURCE TARGET`),
automatically forwarding artifacts, placements, tags, publications, and recording
the source title/slug as an alias in `keywords` so Drive discovery never re-splits them.

Usage:
    python scripts/resolve_project_entities.py --top 40
    python scripts/resolve_project_entities.py --min-score 0.45 --json-out duplicates.json
    python scripts/resolve_project_entities.py --merge ai-lifecycle-toolkit ailifecyclekit --sync
"""

import argparse
import json
import math
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from apply_portal_patch import merge_projects_in_db  # noqa: E402
from build_projects_backbone import ensure_schema  # noqa: E402

STOP_WORDS = {
    "the", "and", "for", "with", "from", "into", "using", "via", "over", "under",
    "project", "projects", "system", "systems", "tool", "toolkit", "engine", "app",
    "application", "web", "website", "suite", "model", "models", "modeling",
    "discovered", "workspace", "drive", "source", "research", "scholarship",
    "internal", "manuscripts", "presentations", "images", "videos", "code", "data",
    "artifacts", "artifact", "located", "google", "draft", "final", "old", "new",
    "test", "demo", "exp", "in", "on", "of", "to", "a", "an",
    # Discipline / folder-bucket words that cause sibling false positives
    "computer", "vision", "graphics", "human", "interaction", "career",
    "statement", "relations", "society", "class", "learning", "dallas",
    "teaching", "service", "business", "hobbies", "education", "artificial",
    "intelligence", "software", "engineering", "science", "sciences",
}

SYNONYM_MAP = {
    "coronavirus": "covid",
    "sarscov2": "covid",
    "kg": "knowledgegraph",
    "kge": "knowledgegraph",
    "gcn": "gnn",
    "digcn": "gnn",
    "directgcn": "gnn",
    "grapher": "entityresolution",
    "moder": "entityresolution",
    "ditk": "dataintegration",
    "kit": "toolkit",
    "realsense": "rgbd",
    "kinect": "rgbd",
    "odometry": "slam",
    "localization": "slam",
    "eyetracking": "gaze",
    "eye": "gaze",
    "eyeadapt": "gaze",
    "eyeart": "gaze",
    "gdwm": "gaze",
    "ge": "googleearth",
    "earthviz": "googleearth",
    "cv": "curriculumvitae",
    "resume": "curriculumvitae",
    "llms": "llm",
    "biomedical": "medical",
    "med": "medical",
    "medgraph": "pubmed",
    "vrjuggler": "vrj",
    "vrj": "vr",
}


def tokenize_camel(text: str) -> List[str]:
    s = re.sub(r"\.[A-Za-z0-9]{1,5}$", " ", text or "")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
    return [t for t in s.split() if t]


def canonical_tokens(text: str, keep_stop: bool = False) -> List[str]:
    raw = tokenize_camel(text)
    out: List[str] = []
    # Also combine adjacent tokens for compound synonyms like "knowledge graph"
    i = 0
    while i < len(raw):
        if i + 1 < len(raw):
            pair = raw[i] + raw[i + 1]
            if pair in ("knowledgegraph", "entityresolution", "dataintegration", "eyetracking", "curriculumvitae", "googleearth"):
                out.append(pair)
                i += 2
                continue
        tok = raw[i]
        mapped = SYNONYM_MAP.get(tok, tok)
        if keep_stop or (mapped not in STOP_WORDS and len(mapped) >= 2):
            out.append(mapped)
        i += 1
    return out


def char_ngrams(text: str, n: int = 3) -> Counter:
    clean = re.sub(r"[^a-z0-9]", "", (text or "").lower())
    if len(clean) < n:
        return Counter([clean]) if clean else Counter()
    return Counter(clean[i:i + n] for i in range(len(clean) - n + 1))


def extract_acronyms(raw_title: str) -> Tuple[Set[str], Set[str]]:
    explicit: Set[str] = set()
    for m in re.findall(r"\b[A-Z][A-Z0-9]{1,7}\b", raw_title or ""):
        explicit.add(m.lower())
    toks = [t for t in tokenize_camel(raw_title) if t not in {"the", "and", "of", "for", "in", "to"}]
    initials: Set[str] = set()
    if 2 <= len(toks) <= 6:
        initials.add("".join(t[0] for t in toks))
    return explicit, initials


def cosine_sparse(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    dot = sum(val * vec_b.get(k, 0.0) for k, val in vec_a.items())
    if dot <= 0.0:
        return 0.0
    na = math.sqrt(sum(v * v for v in vec_a.values()))
    nb = math.sqrt(sum(v * v for v in vec_b.values()))
    return dot / (na * nb) if (na > 0 and nb > 0) else 0.0


def load_project_profiles(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    ensure_schema(cur)
    rows = cur.execute("""
        SELECT id, slug, title, tagline, short_summary, full_description,
               category, project_kind, grant_award, keywords, is_public, discovery_status
        FROM projects
        ORDER BY id
    """).fetchall()

    profiles: List[Dict[str, Any]] = []
    for pid, slug, title, tagline, summary, desc, cat, kind, grant, kw_raw, is_pub, dstatus in rows:
        try:
            kw = json.loads(kw_raw) if kw_raw else []
        except Exception:
            kw = []
        tags = [r[0] for r in cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (pid,)).fetchall()]
        arts = cur.execute(
            "SELECT label, url_or_rel_path, gdrive_path FROM project_artifacts WHERE project_id = ?",
            (pid,),
        ).fetchall()
        plcs = cur.execute(
            "SELECT page_slug, section_slot FROM project_placements WHERE project_id = ? AND is_visible = 1",
            (pid,),
        ).fetchall()

        art_text = " ".join(f"{a[0] or ''} {a[2] or ''}" for a in arts)
        urls = {a[1] for a in arts if a[1] and a[1].startswith("http") and "drive.google.com" not in a[1]}
        grants = set(re.findall(r"\b\d{6,8}\b", grant or ""))

        title_toks = canonical_tokens(f"{title} {slug} {' '.join(kw)}", keep_stop=False)
        full_toks = (
            title_toks * 3
            + canonical_tokens(f"{tagline or ''} {summary or ''} {' '.join(tags)} {art_text}", keep_stop=False)
        )

        # Priority score for recommending which record to keep as Target
        keep_priority = (
            (1000 if is_pub else 0)
            + (500 if dstatus == "canonical" else 100 if dstatus == "reviewed" else 0)
            + len(plcs) * 50
            + len(arts)
        )

        exp_acr, init_acr = extract_acronyms(title)
        profiles.append({
            "id": pid,
            "slug": slug,
            "title": title,
            "category": cat,
            "project_kind": kind or "research",
            "is_public": bool(is_pub),
            "discovery_status": dstatus or "canonical",
            "artifact_count": len(arts),
            "placement_count": len(plcs),
            "keep_priority": keep_priority,
            "title_tokens": set(title_toks),
            "title_grams": char_ngrams(f"{title} {slug}", 3),
            "explicit_acronyms": exp_acr,
            "phrase_initials": init_acr,
            "full_tf": Counter(full_toks),
            "urls": urls,
            "grants": grants,
            "summary": summary or "",
        })
    return profiles


def find_duplicate_candidates(
    profiles: List[Dict[str, Any]],
    min_score: float = 0.42,
    top_k: int = 40,
) -> List[Dict[str, Any]]:
    n_docs = max(1, len(profiles))
    df: Counter = Counter()
    for p in profiles:
        for term in p["full_tf"].keys():
            df[term] += 1

    idf = {term: math.log((n_docs + 1) / (cnt + 1)) + 1.0 for term, cnt in df.items()}
    for p in profiles:
        p["tfidf"] = {t: tf * idf.get(t, 1.0) for t, tf in p["full_tf"].items()}
        p["gram_vec"] = {g: float(c) for g, c in p["title_grams"].items()}

    candidates: List[Dict[str, Any]] = []
    for i in range(len(profiles)):
        a = profiles[i]
        for j in range(i + 1, len(profiles)):
            b = profiles[j]

            # Guard: don't pair unrelated poems unless titles themselves are highly similar
            if a["project_kind"] == "poetry" and b["project_kind"] == "poetry":
                gram_only = cosine_sparse(a["gram_vec"], b["gram_vec"])
                if gram_only < 0.72:
                    continue

            tfidf_sim = cosine_sparse(a["tfidf"], b["tfidf"])
            gram_sim = cosine_sparse(a["gram_vec"], b["gram_vec"])

            shared_title = a["title_tokens"] & b["title_tokens"]
            union_title = a["title_tokens"] | b["title_tokens"]
            title_jaccard = (len(shared_title) / len(union_title)) if union_title else 0.0

            acr_matches = (
                (a["explicit_acronyms"] & b["phrase_initials"])
                | (b["explicit_acronyms"] & a["phrase_initials"])
                | (a["explicit_acronyms"] & b["explicit_acronyms"])
            )
            strong_acr = any(len(x) >= 3 for x in acr_matches)
            shared_urls = a["urls"] & b["urls"]
            shared_grants = a["grants"] & b["grants"]

            reasons: List[str] = []
            score = 0.42 * tfidf_sim + 0.28 * gram_sim + 0.30 * title_jaccard
            if strong_acr:
                score += 0.16
                reasons.append(f"acronym:{sorted(acr_matches)[0]}")
            elif acr_matches and gram_sim >= 0.35:
                score += 0.08
                reasons.append(f"acronym:{sorted(acr_matches)[0]}")
            if shared_urls:
                score += 0.25
                reasons.append("shared_external_url")
            if shared_grants:
                score += 0.20
                reasons.append(f"shared_grant:{sorted(shared_grants)[0]}")

            score = min(0.99, score)
            if score < min_score:
                continue

            if shared_title:
                reasons.append(f"tokens:{','.join(sorted(shared_title)[:4])}")
            if gram_sim >= 0.45:
                reasons.append(f"char3:{gram_sim:.2f}")
            if tfidf_sim >= 0.35:
                reasons.append(f"tfidf:{tfidf_sim:.2f}")

            # Recommend target (keep) vs source (fold)
            if a["keep_priority"] >= b["keep_priority"]:
                target, source = a, b
            else:
                target, source = b, a

            candidates.append({
                "score": round(score, 3),
                "source_id": source["id"],
                "source_slug": source["slug"],
                "source_title": source["title"],
                "source_status": source["discovery_status"],
                "source_artifacts": source["artifact_count"],
                "target_id": target["id"],
                "target_slug": target["slug"],
                "target_title": target["title"],
                "target_status": target["discovery_status"],
                "target_artifacts": target["artifact_count"],
                "reasons": reasons,
            })

    candidates.sort(key=lambda x: (-x["score"], -x["target_artifacts"]))
    return candidates[:top_k] if top_k > 0 else candidates


def main():
    parser = argparse.ArgumentParser(description="Smart & Semantic Entity Resolution and Merge for content.db Projects")
    parser.add_argument("--min-score", type=float, default=0.45, help="Minimum semantic similarity score (0..1)")
    parser.add_argument("--top", type=int, default=40, help="Show top N duplicate candidate pairs")
    parser.add_argument("--json-out", default=None, help="Optional path to save duplicate candidates JSON")
    parser.add_argument("--merge", nargs=2, metavar=("SOURCE", "TARGET"), help="Manually merge SOURCE (slug or id) into TARGET (slug or id)")
    parser.add_argument("--append-summary", action="store_true", help="Append source short_summary to target full_description when merging")
    parser.add_argument("--sync", action="store_true", help="Run sync_content.py --export-only after merging")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    if args.merge:
        src, tgt = args.merge
        res = merge_projects_in_db(conn, src, tgt, append_summary=args.append_summary, add_alias=True)
        conn.close()
        print(f"[OK] Merged '{res['source_slug']}' -> '{res['target_slug']}' (+{res['moved_artifacts']} artifacts, +{res['moved_placements']} placements)")
        if args.sync:
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"], check=True)
        return 0

    profiles = load_project_profiles(conn)
    conn.close()
    cands = find_duplicate_candidates(profiles, min_score=args.min_score, top_k=args.top)

    print("=" * 78)
    print(f"SEMANTIC ENTITY RESOLUTION REPORT ({len(profiles)} projects, min_score={args.min_score})")
    print("=" * 78)
    for idx, c in enumerate(cands, 1):
        print(
            f"{idx:2d}. [{c['score']*100:4.1f}%] "
            f"FOLD [{c['source_slug']}] ({c['source_status']}, art={c['source_artifacts']}) "
            f"==> KEEP [{c['target_slug']}] ({c['target_status']}, art={c['target_artifacts']})"
        )
        print(f"      '{c['source_title']}'  -->  '{c['target_title']}' | {', '.join(c['reasons'])}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(cands, indent=2), encoding="utf-8")
        print(f"\n[OK] Wrote {len(cands)} candidate pairs to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
