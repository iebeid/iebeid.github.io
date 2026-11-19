#!/usr/bin/env python3
"""
Idempotently adds `[data-db-projects]` dynamic project card slots across all
content pages in `data/content.db` and upgrades existing slots with explicit
`data-placement-page` and `data-placement-slot` attributes.

Empty slots remain `hidden` until one or more projects are placed into them via
`project_placements` (managed from `pages/portal/portal.html` or CLI).
"""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"


SLOT_CONFIGS = [
    {
        "page_slug": "education",
        "section_slot": "projects",
        "heading": "Academic Milestones & Educational Projects",
        "badge": "Education",
        "icon": "fas fa-graduation-cap",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "relations",
        "section_slot": "projects",
        "heading": "Collaborations, Mentorship & Community Projects",
        "badge": "Relations",
        "icon": "fas fa-users",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "research",
        "section_slot": "projects",
        "heading": "Additional & Cross-Disciplinary Research Projects",
        "badge": "Research Portfolio",
        "icon": "fas fa-microscope",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "scholarship",
        "section_slot": "projects",
        "heading": "Writings, Essays, Lectures & Poetry Projects",
        "badge": "Scholarship",
        "icon": "fas fa-feather-alt",
        "border": "border-emerald-600",
        "accent_text": "text-emerald-600",
        "badge_cls": "bg-emerald-100 text-emerald-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "teaching",
        "section_slot": "projects",
        "heading": "Courseware, Labs & Teaching Portfolio",
        "badge": "Teaching",
        "icon": "fas fa-chalkboard-teacher",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "service",
        "section_slot": "projects",
        "heading": "Leadership, Outreach & Service Initiatives",
        "badge": "Service",
        "icon": "fas fa-hands-helping",
        "border": "border-emerald-600",
        "accent_text": "text-emerald-600",
        "badge_cls": "bg-emerald-100 text-emerald-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "business",
        "section_slot": "projects",
        "heading": "Applied Consulting & Commercial Initiatives",
        "badge": "Business",
        "icon": "fas fa-briefcase",
        "border": "border-sky-700",
        "accent_text": "text-sky-700",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "hobbies",
        "section_slot": "projects",
        "heading": "Creative Works, Travel & Personal Projects",
        "badge": "Hobbies",
        "icon": "fas fa-compass",
        "border": "border-emerald-600",
        "accent_text": "text-emerald-600",
        "badge_cls": "bg-emerald-100 text-emerald-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "media",
        "section_slot": "projects",
        "heading": "Talks, Podcasts & Featured Media Projects",
        "badge": "Media",
        "icon": "fas fa-photo-video",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "downloads",
        "section_slot": "projects",
        "heading": "Shared Project Bundles & Public Artifacts",
        "badge": "Downloads",
        "icon": "fas fa-folder-open",
        "border": "border-slate-600",
        "accent_text": "text-slate-700",
        "badge_cls": "bg-slate-200 text-slate-800",
        "insert_mode": "before_main_div_close",
    },
    {
        "page_slug": "lab",
        "section_slot": "projects",
        "heading": "Active Lab Projects & Open Artifacts",
        "badge": "Data2AI4LifeSciences",
        "icon": "fas fa-flask",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_main_close",
    },
    {
        "page_slug": "talk-index",
        "section_slot": "projects",
        "heading": "Related Presentation & Talk Projects",
        "badge": "Presentations",
        "icon": "fas fa-chalkboard",
        "border": "border-sky-600",
        "accent_text": "text-sky-600",
        "badge_cls": "bg-sky-100 text-sky-800",
        "insert_mode": "before_footer_placeholder",
    },
]


def build_slot_html(cfg: dict) -> str:
    slug = cfg["page_slug"]
    slot = cfg["section_slot"]
    border = cfg["border"]
    if slug == "lab":
        return (
            f'<section class="model-section hidden" data-projects-section="true" id="lab-projects">\n'
            f'  <div class="section-heading">\n'
            f'    <h2>{cfg["heading"]}</h2>\n'
            f'  </div>\n'
            f'  <div class="grid grid-cols-1 md:grid-cols-2 gap-6" '
            f'data-db-projects="placed" data-placement-page="{slug}" '
            f'data-placement-slot="{slot}" data-view="research-cards" '
            f'data-border-class="{border}"></div>\n'
            f'</section>'
        )
    return (
        f'<section class="hidden mt-10" data-projects-section="true" id="{slug}-dynamic-projects">\n'
        f'  <div class="flex items-center justify-between border-b-2 {border} pb-2 mb-6">\n'
        f'    <h2 class="text-2xl font-bold text-gray-800 flex items-center">\n'
        f'      <i class="{cfg["icon"]} {cfg["accent_text"]} mr-3"></i> {cfg["heading"]}\n'
        f'    </h2>\n'
        f'    <span class="text-xs {cfg["badge_cls"]} font-semibold px-2.5 py-1 rounded-full">{cfg["badge"]}</span>\n'
        f'  </div>\n'
        f'  <div class="grid grid-cols-1 md:grid-cols-2 gap-6" '
        f'data-db-projects="placed" data-placement-page="{slug}" '
        f'data-placement-slot="{slot}" data-view="research-cards" '
        f'data-border-class="{border}"></div>\n'
        f'</section>'
    )


def upgrade_existing_slots(cur):
    """Attach data-placement-page / data-placement-slot to existing slots on home, research, storefront."""
    updates = [
        ("home", "current-research", 'data-db-projects="featured"', 'data-db-projects="featured" data-placement-page="home" data-placement-slot="featured"'),
        ("research", "section_1", 'data-db-projects="all" data-view="research-cards"', 'data-db-projects="all" data-placement-page="research" data-placement-slot="ai_life_sciences" data-view="research-cards"'),
        ("research", "section_2", 'data-db-projects="all" data-view="research-cards"', 'data-db-projects="all" data-placement-page="research" data-placement-slot="data_engineering" data-view="research-cards"'),
        ("research", "section_3", 'data-db-projects="all" data-view="research-cards"', 'data-db-projects="all" data-placement-page="research" data-placement-slot="visualization_hci" data-view="research-cards"'),
        ("research", "section_4", 'data-db-projects="all" data-view="research-cards"', 'data-db-projects="all" data-placement-page="research" data-placement-slot="legacy_industry" data-view="research-cards"'),
        ("storefront", "catalog", 'data-db-projects="storefront"', 'data-db-projects="storefront" data-placement-page="storefront" data-placement-slot="catalog"'),
    ]
    for slug, sec_key, old_attr, new_attr in updates:
        row = cur.execute(
            "SELECT content_html FROM page_sections WHERE page_slug = ? AND section_key = ?",
            (slug, sec_key),
        ).fetchone()
        if not row:
            continue
        html = row[0] or ""
        if "data-placement-slot=" in html:
            continue
        if old_attr in html:
            new_html = html.replace(old_attr, new_attr, 1)
            cur.execute(
                "UPDATE page_sections SET content_html = ? WHERE page_slug = ? AND section_key = ?",
                (new_html, slug, sec_key),
            )
            print(f"[OK] Upgraded existing slot {slug}.{sec_key}")


def insert_placeholder(tmpl: str, placeholder: str, mode: str, slug: str) -> str:
    if placeholder in tmpl:
        return tmpl
    if mode == "before_main_div_close":
        m = re.search(r'(</div>\s*</main>)', tmpl, flags=re.IGNORECASE)
        if m:
            idx = m.start(1)
            return tmpl[:idx] + f"\n{placeholder}\n" + tmpl[idx:]
    if mode == "before_main_close":
        m = re.search(r'(</main>)', tmpl, flags=re.IGNORECASE)
        if m:
            idx = m.start(1)
            return tmpl[:idx] + f"    {placeholder}\n" + tmpl[idx:]
    if mode == "before_footer_placeholder":
        footer_ph = f'<div data-db-section="{slug}.footer"></div>'
        if footer_ph in tmpl:
            return tmpl.replace(footer_ph, f"{placeholder}\n    {footer_ph}", 1)
    raise RuntimeError(f"Could not place '{placeholder}' into template for '{slug}' (mode={mode})")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    upgrade_existing_slots(cur)

    for cfg in SLOT_CONFIGS:
        slug = cfg["page_slug"]
        sec_key = "projects_slot"
        html = build_slot_html(cfg)

        max_order = cur.execute(
            "SELECT COALESCE(MAX(display_order), 0) FROM page_sections WHERE page_slug = ?",
            (slug,),
        ).fetchone()[0]

        existing = cur.execute(
            "SELECT id FROM page_sections WHERE page_slug = ? AND section_key = ?",
            (slug, sec_key),
        ).fetchone()
        if existing:
            cur.execute(
                "UPDATE page_sections SET heading = ?, content_html = ? WHERE id = ?",
                (cfg["heading"], html, existing[0]),
            )
        else:
            cur.execute("""
                INSERT INTO page_sections (page_slug, section_key, heading, subheading, content_html, content_text, display_order)
                VALUES (?, ?, ?, '', ?, '', ?)
            """, (slug, sec_key, cfg["heading"], html, max_order + 1))

        row = cur.execute("SELECT body_template_html FROM pages WHERE slug = ?", (slug,)).fetchone()
        if row and row[0]:
            placeholder = f'<div data-db-section="{slug}.{sec_key}"></div>'
            updated_tmpl = insert_placeholder(row[0], placeholder, cfg["insert_mode"], slug)
            if updated_tmpl != row[0]:
                cur.execute(
                    "UPDATE pages SET body_template_html = ? WHERE slug = ?",
                    (updated_tmpl, slug),
                )
        print(f"[OK] Configured dynamic project slot on '{slug}' (slot='{cfg['section_slot']}')")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
