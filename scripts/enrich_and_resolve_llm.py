#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - LLM Semantic Description & Embedding Entity Resolution
===============================================================================
Uses the Gemini API (`gemini-2.5-flash` + `gemini-embedding-001:batchEmbedContents`)
to:
  1. Generate semantic descriptions, taglines, tags, and ER keywords for
     Drive-discovered projects (`--enrich`, optionally `--peek-docs` to inspect
     READMEs/Google Docs via `gdrive readonly`).
  2. Compute dense semantic embeddings across all projects and have Gemini
     verify whether top candidate pairs are `SAME_PROJECT`, `RELATED_SERIES`,
     or `DISTINCT` (`--resolve`).

Usage:
    $env:GEMINI_API_KEY="AIza..."
    python scripts/enrich_and_resolve_llm.py --enrich --resolve --sync
    python scripts/enrich_and_resolve_llm.py --resolve --json-out llm_duplicates.json
"""

import argparse
import json
import math
import os
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_projects_backbone import ensure_schema  # noqa: E402
from discover_drive_projects import peek_gdrive_text  # noqa: E402


def gemini_post(endpoint: str, payload: Dict[str, Any], api_key: str, timeout: int = 90) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/{endpoint}?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini API error ({exc.code}): {body[:400]}") from exc


def gemini_generate_json(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> Any:
    data = gemini_post(
        f"models/{model}:generateContent",
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.15, "responseMimeType": "application/json"},
        },
        api_key,
    )
    txt = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    txt = txt.strip().strip("`")
    if txt.startswith("json"):
        txt = txt[4:].strip()
    return json.loads(txt)


def cosine_dense(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if (na > 0 and nb > 0) else 0.0


def load_all_projects(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    ensure_schema(cur)
    rows = cur.execute("""
        SELECT id, slug, title, tagline, short_summary, full_description,
               category, project_kind, keywords, is_public, discovery_status
        FROM projects
        ORDER BY id
    """).fetchall()
    projects = []
    for pid, slug, title, tagline, summary, desc, cat, kind, kw_raw, is_pub, dstatus in rows:
        try:
            kw = json.loads(kw_raw) if kw_raw else []
        except Exception:
            kw = []
        tags = [r[0] for r in cur.execute("SELECT tag FROM project_tags WHERE project_id = ?", (pid,)).fetchall()]
        arts = [
            {"id": r[0], "type": r[1], "label": r[2], "gdrive_file_id": r[3], "gdrive_path": r[4], "mime_type": r[5]}
            for r in cur.execute(
                "SELECT id, artifact_type, label, gdrive_file_id, gdrive_path, mime_type FROM project_artifacts WHERE project_id = ?",
                (pid,),
            ).fetchall()
        ]
        projects.append({
            "id": pid,
            "slug": slug,
            "title": title,
            "tagline": tagline or "",
            "short_summary": summary or "",
            "full_description": desc or "",
            "category": cat or "",
            "project_kind": kind or "research",
            "keywords": kw,
            "tags": tags,
            "is_public": bool(is_pub),
            "discovery_status": dstatus or "canonical",
            "artifacts": arts,
        })
    return projects


def run_enrich(conn: sqlite3.Connection, api_key: str, peek_docs: bool = False, batch_size: int = 12) -> int:
    projects = load_all_projects(conn)
    targets = [
        p for p in projects
        if not p["short_summary"].strip()
        or p["short_summary"].startswith("Discovered ")
        or len(p["short_summary"].strip()) < 40
    ]
    if not targets:
        print("[OK] All projects already have semantic descriptions.")
        return 0

    cur = conn.cursor()
    enriched = 0
    for i in range(0, len(targets), batch_size):
        batch = targets[i:i + batch_size]
        snaps = []
        for p in batch:
            snippet = ""
            if peek_docs:
                for a in p["artifacts"]:
                    if a.get("gdrive_file_id") and (
                        "readme" in (a.get("label") or "").lower()
                        or a.get("mime_type") == "application/vnd.google-apps.document"
                        or a.get("type") in ("poem_draft", "manuscript", "doc")
                    ):
                        snippet = peek_gdrive_text({
                            "id": a["gdrive_file_id"],
                            "name": a["label"],
                            "mimeType": a.get("mime_type") or "",
                        })
                        if snippet:
                            break
            snaps.append({
                "id": p["id"],
                "title": p["title"],
                "slug": p["slug"],
                "kind": p["project_kind"],
                "category": p["category"],
                "artifacts": [f"{a['type']}: {a['label']} [{a.get('gdrive_path') or ''}]" for a in p["artifacts"][:8]],
                "excerpt": snippet[:500] if snippet else "",
            })

        prompt = (
            "You are curating Dr. Islam Akef Ebeid's academic, software, and creative portfolio. "
            "For each project below, generate a factual semantic description strictly from its title, kind, "
            "Google Drive path, artifact filenames, and excerpt (never invent metrics or grants). "
            "Return JSON array: [{\"id\": int, \"short_summary\": \"1-2 factual sentences\", "
            "\"tagline\": \"5-9 word subtitle\", \"tags\": [\"3-5 tags\"], \"keywords\": [\"acronyms, aliases, key concepts\"]}].\n\n"
            + json.dumps(snaps, ensure_ascii=False)
        )
        results = gemini_generate_json(prompt, api_key)
        by_id = {int(r["id"]): r for r in (results if isinstance(results, list) else []) if "id" in r}

        for p in batch:
            r = by_id.get(p["id"])
            if not r or not r.get("short_summary"):
                continue
            merged_kw = list(dict.fromkeys(p["keywords"] + (r.get("keywords") or [])))
            new_tagline = r.get("tagline") if (not p["tagline"] or p["tagline"].startswith("Drive Source:")) else p["tagline"]
            new_desc = r["short_summary"] if (not p["full_description"] or p["full_description"].startswith("Discovered ")) else p["full_description"]
            cur.execute("""
                UPDATE projects
                SET short_summary = ?, full_description = ?, tagline = ?, keywords = ?
                WHERE id = ?
            """, (r["short_summary"], new_desc, new_tagline, json.dumps(merged_kw), p["id"]))
            for tag in (r.get("tags") or []):
                if str(tag).strip():
                    cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (p["id"], str(tag).strip()))
            enriched += 1
        conn.commit()
        print(f"  [ENRICH] {min(i + batch_size, len(targets))}/{len(targets)} processed (updated {enriched})")

    return enriched


def run_semantic_resolve(conn: sqlite3.Connection, api_key: str, min_emb: float = 0.72, top_k: int = 30) -> List[Dict[str, Any]]:
    projects = load_all_projects(conn)
    embeddings: List[List[float]] = []
    for i in range(0, len(projects), 80):
        slice_p = projects[i:i + 80]
        requests = []
        for p in slice_p:
            art_paths = "; ".join((a.get("gdrive_path") or a["label"]) for a in p["artifacts"][:6])
            txt = (
                f"{p['title']} ({p['slug']}) | Kind: {p['project_kind']} | Category: {p['category']} | "
                f"{p['tagline']} | {p['short_summary']} | Tags: {', '.join(p['tags'])} | "
                f"Keywords: {', '.join(p['keywords'])} | Artifacts: {art_paths}"
            )[:1800]
            requests.append({
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": txt}]},
                "taskType": "SEMANTIC_SIMILARITY",
            })
        resp = gemini_post("models/gemini-embedding-001:batchEmbedContents", {"requests": requests}, api_key)
        for item in resp.get("embeddings", []):
            embeddings.append(item.get("values", []))

    pairs: List[Dict[str, Any]] = []
    for i in range(len(projects)):
        for j in range(i + 1, len(projects)):
            sim = cosine_dense(embeddings[i], embeddings[j])
            if sim < min_emb:
                continue
            a, b = projects[i], projects[j]
            prio_a = (1000 if a["is_public"] else 0) + (500 if a["discovery_status"] == "canonical" else 0) + len(a["artifacts"])
            prio_b = (1000 if b["is_public"] else 0) + (500 if b["discovery_status"] == "canonical" else 0) + len(b["artifacts"])
            target, source = (a, b) if prio_a >= prio_b else (b, a)
            pairs.append({"emb_sim": round(sim, 3), "source": source, "target": target})

    pairs.sort(key=lambda x: -x["emb_sim"])
    top_pairs = pairs[:top_k]
    if not top_pairs:
        return []

    prompt_pairs = [
        {
            "idx": idx,
            "emb_sim": p["emb_sim"],
            "a": {"slug": p["source"]["slug"], "title": p["source"]["title"], "kind": p["source"]["project_kind"], "summary": p["source"]["short_summary"][:220]},
            "b": {"slug": p["target"]["slug"], "title": p["target"]["title"], "kind": p["target"]["project_kind"], "summary": p["target"]["short_summary"][:220]},
        }
        for idx, p in enumerate(top_pairs)
    ]
    prompt = (
        "Judge whether each pair of projects is the SAME_PROJECT (e.g. code + paper + slides + renamed duplicate of the exact same work) "
        "vs RELATED_SERIES vs DISTINCT. Return JSON array: "
        "[{\"idx\": int, \"verdict\": \"SAME_PROJECT\" | \"RELATED_SERIES\" | \"DISTINCT\", \"recommended_target\": \"a\" | \"b\", \"reason\": \"concise explanation\"}].\n\n"
        + json.dumps(prompt_pairs, ensure_ascii=False)
    )
    verdicts = gemini_generate_json(prompt, api_key)
    vmap = {int(v["idx"]): v for v in (verdicts if isinstance(verdicts, list) else []) if "idx" in v}

    out = []
    for idx, p in enumerate(top_pairs):
        v = vmap.get(idx, {"verdict": "UNVERIFIED", "recommended_target": "b", "reason": ""})
        src, tgt = p["source"], p["target"]
        if v.get("recommended_target") == "a":
            src, tgt = tgt, src
        out.append({
            "emb_sim": p["emb_sim"],
            "verdict": v.get("verdict"),
            "reason": v.get("reason", ""),
            "source_slug": src["slug"],
            "source_title": src["title"],
            "target_slug": tgt["slug"],
            "target_title": tgt["title"],
        })
    order = {"SAME_PROJECT": 0, "RELATED_SERIES": 1, "DISTINCT": 2}
    out.sort(key=lambda x: (order.get(x["verdict"], 3), -x["emb_sim"]))
    return out


def main():
    parser = argparse.ArgumentParser(description="Gemini LLM Semantic Enrichment & Embedding Entity Resolution")
    parser.add_argument("--api-key", default=os.environ.get("GEMINI_API_KEY", ""), help="Gemini API key (or set GEMINI_API_KEY)")
    parser.add_argument("--enrich", action="store_true", help="Generate LLM semantic summaries, tags & keywords for discovered projects")
    parser.add_argument("--peek-docs", action="store_true", help="Also read README/Doc snippets from Drive during enrichment")
    parser.add_argument("--resolve", action="store_true", help="Run gemini-embedding-001 + Gemini LLM duplicate verification")
    parser.add_argument("--min-emb", type=float, default=0.72, help="Minimum embedding cosine similarity (default 0.72)")
    parser.add_argument("--top", type=int, default=30, help="Top pairs to verify with Gemini LLM")
    parser.add_argument("--json-out", default=None, help="Save resolved candidate pairs to JSON")
    parser.add_argument("--sync", action="store_true", help="Run sync_content.py --export-only after enrichment")
    args = parser.parse_args()

    if not args.api_key:
        print("[ERROR] Provide --api-key or set GEMINI_API_KEY environment variable.")
        return 1

    conn = sqlite3.connect(DB_PATH)
    if args.enrich:
        print("[STEP 1] Enriching project descriptions with Gemini...")
        cnt = run_enrich(conn, args.api_key, peek_docs=args.peek_docs)
        print(f"[OK] Enriched {cnt} projects in {DB_PATH.name}.")

    if args.resolve:
        print("[STEP 2] Running Gemini Embedding + LLM Semantic Entity Resolution...")
        results = run_semantic_resolve(conn, args.api_key, min_emb=args.min_emb, top_k=args.top)
        for idx, r in enumerate(results, 1):
            print(f"{idx:2d}. [{r['verdict']:14s} | emb={r['emb_sim']:.3f}] {r['source_slug']} -> {r['target_slug']} | {r['reason']}")
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(f"[OK] Wrote {len(results)} pairs to {args.json_out}")

    conn.close()
    if args.sync and args.enrich:
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "sync_content.py"), "--export-only"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
