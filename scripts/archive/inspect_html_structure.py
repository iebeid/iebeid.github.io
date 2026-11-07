from bs4 import BeautifulSoup
from pathlib import Path

pages_dir = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages")
pages = [
    ("home", pages_dir / "home" / "home.html"),
    ("relations", pages_dir / "relations" / "relations.html"),
    ("scholarship", pages_dir / "scholarship" / "scholarship.html"),
    ("teaching", pages_dir / "teaching" / "teaching.html"),
    ("education", pages_dir / "education" / "education.html"),
    ("research", pages_dir / "research" / "research.html"),
    ("service", pages_dir / "service" / "service.html"),
    ("business", pages_dir / "business" / "business.html"),
    ("downloads", pages_dir / "downloads" / "downloads.html")
]

for name, p in pages:
    if not p.exists():
        continue
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    main = soup.find("main")
    sections = main.find_all("section") if main else []
    sec_ids = [s.get("id", f"idx_{i}") for i, s in enumerate(sections)]
    print(f"{name:12}: {len(sections)} sections -> {sec_ids}")
