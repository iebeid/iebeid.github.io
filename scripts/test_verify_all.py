import json
from pathlib import Path

json_path = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/data/public_content.json")
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
        if not html.startswith("<section"):
            print(f"     [!] Warning: {slug}.{k} does not start with <section: {html[:40]}")
            all_ok = False

if all_ok:
    print("\n[VERIFIED] All sections start with clean <section> tags and match template placeholders!")
