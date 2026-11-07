import shutil
from pathlib import Path
from bs4 import BeautifulSoup

REPO_ROOT = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io")
PAGES_DIR = REPO_ROOT / "pages"

pages_to_process = [
    ("scholarship", PAGES_DIR / "scholarship" / "scholarship.html"),
    ("teaching", PAGES_DIR / "teaching" / "teaching.html"),
    ("education", PAGES_DIR / "education" / "education.html"),
    ("research", PAGES_DIR / "research" / "research.html"),
    ("service", PAGES_DIR / "service" / "service.html"),
    ("business", PAGES_DIR / "business" / "business.html"),
    ("downloads", PAGES_DIR / "downloads" / "downloads.html")
]

for slug, html_file in pages_to_process:
    if not html_file.exists():
        print(f"[SKIP] {html_file} does not exist.")
        continue

    # Backup
    bak_file = html_file.with_suffix(".html.bak")
    shutil.copy(html_file, bak_file)

    with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    main = soup.find("main")
    if not main:
        print(f"[WARN] No <main> found in {slug}")
        continue

    sections = main.find_all("section")
    print(f"[{slug}] Found {len(sections)} sections in <main>.")

    for idx, sec in enumerate(sections):
        sec_id = sec.get("id", f"section_{idx+1}")
        placeholder = soup.new_tag("div")
        placeholder["data-db-section"] = f"{slug}.{sec_id}"
        sec.replace_with(placeholder)

    # Add scripts before </body> if not present
    body = soup.find("body")
    if body:
        existing_scripts = [s.get("src", "") for s in body.find_all("script")]
        if not any("public_content.js" in s for s in existing_scripts):
            script_data = soup.new_tag("script", src="../../data/public_content.js")
            script_loader = soup.new_tag("script", src="../../js/content-loader.js")
            body.append(script_data)
            body.append(script_loader)

    # Save formatted
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"[SUCCESS] {slug}.html skeletonized successfully!")
