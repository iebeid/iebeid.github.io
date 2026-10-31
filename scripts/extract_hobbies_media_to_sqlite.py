import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup

db_path = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/data/content.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

pages = [
    ("hobbies", "G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/hobbies/hobbies.html", [
        ("section_1", "Beyond the Laboratory"),
        ("section_2", "Photography & Creative Pursuits")
    ]),
    ("media", "G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/media/media.html", [
        ("section_1", "Faculty Candidate Presentations"),
        ("section_2", "Invited Talks, Lectures & Graduate Seminars"),
        ("section_3", "Media Appearances & University Press Features"),
        ("section_4", "Public Discourse, Published Op-Eds & Letters to the Editor")
    ])
]

for slug, html_path, sec_defs in pages:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as fp:
        soup = BeautifulSoup(fp.read(), "html.parser")
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
        sec_key, default_heading = sec_defs[i]
        h = b.find(["h1", "h2", "h3", "h4"])
        heading = h.get_text(strip=True) if h else default_heading
        content_text = b.get_text(separator=" ", strip=True)
        content_html = str(b)

        cur.execute("""
        INSERT INTO page_sections (page_slug, section_key, heading, content_html, content_text, display_order)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(page_slug, section_key) DO UPDATE SET
            heading = excluded.heading,
            content_html = excluded.content_html,
            content_text = excluded.content_text,
            display_order = excluded.display_order;
        """, (slug, sec_key, heading, content_html, content_text, i + 1))
        print(f"[OK] Added {slug}.{sec_key} ({len(content_html)} bytes) - {heading}")

conn.commit()
print("[SUCCESS] hobbies and media added to content.db!")
