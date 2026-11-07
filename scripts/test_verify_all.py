#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Rapid Section & Tag Validator
Validates that all sections in public_content.json have clean structural container tags.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
json_path = REPO_ROOT / "data" / "public_content.json"

if not json_path.exists():
    print(f"[ERROR] public_content.json not found at {json_path}")
    exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    d = json.load(f)

print(f"Total pages in DB: {len(d['pages'])}")
all_ok = True
for p in d['pages']:
    slug = p['slug']
    secs = p.get('sections', [])
    print(f"  Page '{slug}': {len(secs)} sections")
    for s in secs:
        k = s.get("section_key")
        html = s.get("content_html", "").strip()
        if not (html.startswith("<section") or html.startswith("<div") or html.startswith("<article") or html.startswith("<header") or html.startswith("<footer") or html.startswith("<main") or html.startswith("<p")):
            print(f"     [!] Warning: {slug}.{k} does not start with standard container tag: {html[:40]}")
            all_ok = False

if all_ok:
    print("\n[VERIFIED] All sections start with clean HTML container tags!")
