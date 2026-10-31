import shutil
from pathlib import Path
from bs4 import BeautifulSoup

REPO_ROOT = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io")
PAGES_DIR = REPO_ROOT / "pages"

pages = [
    ("hobbies", PAGES_DIR / "hobbies" / "hobbies.html", [
        ("section_1", "Beyond the Laboratory"),
        ("section_2", "Photography & Creative Pursuits")
    ]),
    ("media", PAGES_DIR / "media" / "media.html", [
        ("section_1", "Faculty Candidate Presentations"),
        ("section_2", "Invited Talks, Lectures & Graduate Seminars"),
        ("section_3", "Media Appearances & University Press Features"),
        ("section_4", "Public Discourse, Published Op-Eds & Letters to the Editor")
    ])
]

for slug, html_file, sec_defs in pages:
    if not html_file.exists():
        continue

    # Backup
    bak = html_file.with_suffix(".html.bak")
    shutil.copy(html_file, bak)

    with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    main = soup.find("main")
    if not main:
        continue
    container = main.find("div")
    if not container:
        continue

    blocks = [c for c in container.children if c.name == "div"]
    for i, b in enumerate(blocks):
        if i >= len(sec_defs):
            break
        sec_key, _ = sec_defs[i]
        placeholder = soup.new_tag("div")
        placeholder["data-db-section"] = f"{slug}.{sec_key}"
        b.replace_with(placeholder)

    # Add scripts
    body = soup.find("body")
    if body:
        existing_scripts = [s.get("src", "") for s in body.find_all("script")]
        if not any("public_content.js" in s for s in existing_scripts):
            s_data = soup.new_tag("script", src="../../data/public_content.js")
            s_loader = soup.new_tag("script", src="../../js/content-loader.js")
            body.append(s_data)
            body.append(s_loader)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"[SUCCESS] Skeletonized {slug}.html!")
