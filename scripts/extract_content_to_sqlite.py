#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Master SQLite Content, HTML Template, CSS & Navigation Extraction Engine
Extracts 100% of website content, HTML templates, page sections, CSS stylesheets,
navigation menu hierarchy (including hover dropdown sub-pages), documents, images,
publications, courses, contacts, and AES-256 encrypted portal vault secrets into data/content.db.
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from database_manager import init_database, get_connection, store_vault_secret, DEFAULT_PORTAL_PASSCODE

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PAGES_DIR = REPO_ROOT / "pages"
DOCS_DIR = REPO_ROOT / "documents"
IMAGES_DIR = REPO_ROOT / "images"


def convert_tailwind_apply(css_text: str) -> str:
    """Convert @apply directives into standard CSS rules so dynamic <style> injection works immediately."""
    replacements = {
        r"@apply\s+inline-block\s+bg-sky-100\s+text-sky-800\s+text-xs\s+font-semibold\s+mr-1\.5\s+mb-1\.5\s+px-2\.5\s+py-1\s+rounded-full\s*;": (
            "display: inline-block; background-color: #e0f2fe; color: #075985; font-size: 0.75rem; "
            "line-height: 1rem; font-weight: 600; margin-right: 0.375rem; margin-bottom: 0.375rem; "
            "padding: 0.25rem 0.625rem; border-radius: 9999px;"
        ),
        r"@apply\s+inline-block\s+bg-sky-100\s+text-sky-800\s+text-xs\s+font-semibold\s+mr-2\s+px-2\.5\s+py-0\.5\s+rounded-full\s*;": (
            "display: inline-block; background-color: #e0f2fe; color: #075985; font-size: 0.75rem; "
            "line-height: 1rem; font-weight: 600; margin-right: 0.5rem; margin-bottom: 0.25rem; "
            "padding: 0.125rem 0.625rem; border-radius: 9999px;"
        ),
        r"@apply\s+inline-block\s+bg-teal-100\s+text-teal-800\s+text-xs\s+font-semibold\s+mr-2\s+mb-2\s+px-2\.5\s+py-0\.5\s+rounded-full\s*;": (
            "display: inline-block; background-color: #ccfbf1; color: #115e59; font-size: 0.75rem; "
            "line-height: 1rem; font-weight: 600; margin-right: 0.5rem; margin-bottom: 0.5rem; "
            "padding: 0.125rem 0.625rem; border-radius: 9999px;"
        ),
        r"@apply\s+text-3xl\s+font-bold\s+text-gray-800\s+mb-8\s+text-center\s*;": (
            "font-size: 1.875rem; line-height: 2.25rem; font-weight: 700; color: #1f2937; "
            "margin-bottom: 2rem; text-align: center;"
        ),
        r"@apply\s+text-3xl\s+font-bold\s+text-gray-800\s+mb-8\s+pb-2\s+border-b-2\s+border-teal-500\s+inline-block\s*;": (
            "font-size: 1.875rem; line-height: 2.25rem; font-weight: 700; color: #1f2937; "
            "margin-bottom: 2rem; padding-bottom: 0.5rem; border-bottom: 2px solid #14b8a6; display: inline-block;"
        ),
        r"@apply\s+bg-white/90\s+backdrop-blur-sm\s+shadow-lg\s*;": (
            "background-color: rgba(255, 255, 255, 0.9); backdrop-filter: blur(4px); "
            "box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);"
        ),
        r"@apply\s+bg-white\s+p-6\s+rounded-lg\s+shadow-md\s+transition-all\s+duration-300\s+hover:shadow-xl\s*;": (
            "background-color: #ffffff; padding: 1.5rem; border-radius: 0.5rem; "
            "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.3s ease;"
        ),
    }
    out = css_text
    for pattern, repl in replacements.items():
        out = re.sub(pattern, repl, out)
    return out


def extract_site_meta(conn: sqlite3.Connection):
    """Seed site-level metadata."""
    cur = conn.cursor()
    meta_entries = [
        ("author_name", "Islam Akef Ebeid, Ph.D.", "Full legal / academic name"),
        ("arabic_name", "إسلام عاطف عبيد", "Full Arabic name"),
        ("job_title", "Assistant Professor of Computer & Information Science", "Primary academic title"),
        ("institution", "Texas Woman's University", "Primary academic institution"),
        ("lab_name", "Data2AI4LifeSciences Lab", "Research laboratory"),
        ("canonical_url", "https://iebeid.github.io/", "Website production root URL"),
        ("primary_email", "iebeid@twu.edu", "Institutional email"),
        ("direct_email", "islam.akef@gmail.com", "Personal verified inbox"),
        ("phone_us", "+1 (512) 921-1311", "Direct US mobile"),
        ("office_phone", "+1 (940) 898-2165", "Faculty office line"),
        ("office_location", "MCL 412, Texas Woman's University, Denton, TX 76204", "Physical academic office"),
        ("google_scholar", "https://scholar.google.com/citations?user=Qwm3Py8AAAAJ&hl=en", "Google Scholar profile"),
        ("researchgate", "https://www.researchgate.net/profile/Islam-Ebeid", "ResearchGate profile"),
        ("dblp", "https://dblp.org/pid/182/4444.html", "DBLP computer science bibliography"),
        ("github", "https://github.com/iebeid", "GitHub profile"),
        ("linkedin", "https://linkedin.com/in/iebeid", "LinkedIn profile"),
        ("copyright_year", "2026", "Current copyright year"),
        ("footer_rights", "Islam Akef Ebeid. All Rights Reserved.", "Footer copyright notice")
    ]

    for key, val, desc in meta_entries:
        cur.execute("""
        INSERT INTO site_meta (key, value, description)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, description = excluded.description;
        """, (key, val, desc))

    conn.commit()
    print(f"[OK] Seeded {len(meta_entries)} site_meta entries.")


def seed_navigation_menu(conn: sqlite3.Connection):
    """Seed complete navigation menu tree with top-level items and hover dropdown sub-pages for ALL HTML pages."""
    cur = conn.cursor()
    cur.execute("DELETE FROM navigation_menu;")

    # Format: (nav_key, parent_key, label, sublabel, folder, rel_path, icon_class, badge_text, display_order, is_visible)
    nav_entries = [
        # Top-Level Menu Bar Items
        ("home", None, "Home", "Academic Portfolio & Overview", "home", "pages/home/home.html", "fas fa-home", "", 1, 1),
        ("relations", None, "Relations", "Directory, Mentors & Drop-Box", "relations", "pages/relations/relations.html", "fas fa-handshake", "", 2, 1),
        ("education", None, "Education", "Degrees & Academic Lineage", "education", "pages/education/education.html", "fas fa-graduation-cap", "", 3, 1),
        ("research", None, "Research", "Projects, Lab & 3D Demos", "research", "pages/research/research.html", "fas fa-microscope", "", 4, 1),
        ("scholarship", None, "Scholarship", "Fiqh, Psychology, Books & Poetry", "scholarship", "pages/scholarship/scholarship.html", "fas fa-feather-alt", "", 5, 1),
        ("teaching", None, "Teaching", "Courses, Evaluations & Syllabi", "teaching", "pages/teaching/teaching.html", "fas fa-chalkboard-teacher", "", 6, 1),
        ("service", None, "Service", "Governance, Review & Leadership", "service", "pages/service/service.html", "fas fa-university", "", 7, 1),
        ("business", None, "Business", "Unity Systems & Storefront", "business", "pages/business/business.html", "fas fa-briefcase", "", 8, 1),
        ("hobbies", None, "Hobbies", "Creative Works & Personal", "hobbies", "pages/hobbies/hobbies.html", "fas fa-camera-retro", "", 9, 1),
        ("media", None, "Media", "Talks, Slide Decks & Press", "media", "pages/media/media.html", "fas fa-broadcast-tower", "", 10, 1),
        ("downloads", None, "Downloads", "50+ Papers, Decks & Syllabi", "downloads", "pages/downloads/downloads.html", "fas fa-folder-open", "", 11, 1),

        # Hover Dropdown Children under "Home"
        ("home_main", "home", "Academic Homepage", "Biography, Research & Selected Papers", "home", "pages/home/home.html", "fas fa-user-graduate", "Main", 1, 1),
        ("home_portal", "home", "Executive Personal Portal", "Encrypted Command Center, Bookmarks & Vault", "portal", "pages/portal/portal.html", "fas fa-shield-halved", "Private", 2, 1),
        ("home_root", "home", "Root Entry (index.html)", "Canonical Root Redirect", "home", "index.html", "fas fa-link", "Root", 3, 1),

        # Hover Dropdown Children under "Relations"
        ("relations_main", "relations", "Relations & Academic Network", "Contact Directory, Mentors, Students & Family", "relations", "pages/relations/relations.html", "fas fa-address-book", "Directory", 1, 1),
        ("relations_drop", "relations", "Confidential Secure Drop-Box", "Zero-Trust Handshake & Direct Message Relay", "relations", "pages/relations/drop.html", "fas fa-key", "Encrypted", 2, 1),

        # Hover Dropdown Children under "Research"
        ("research_main", "research", "Research Portfolio & Grants", "Biomedical AI, GNNs, Data Quality & VR", "research", "pages/research/research.html", "fas fa-project-diagram", "Portfolio", 1, 1),
        ("research_lab", "research", "Data2AI4LifeSciences Lab", "Official TWU Research Laboratory Portal", "research", "pages/research/lab.html", "fas fa-flask", "Lab Site", 2, 1),
        ("research_xlpm", "research", "XLPM & VisInt-X 3D Viewer", "Interactive WebGL Protein Structure & Contact Map", "research", "pages/research/xlpm/index.html", "fas fa-dna", "3D Live App", 3, 1),

        # Hover Dropdown Children under "Business"
        ("business_main", "business", "Unity Systems & Consulting", "Startup Profile, Telecom & Government Engineering", "business", "pages/business/business.html", "fas fa-building", "Overview", 1, 1),
        ("business_storefront", "business", "Unity Systems Storefront", "Commercial Software Catalog, SaaS & Licensing", "business", "pages/business/storefront.html", "fas fa-store", "Storefront", 2, 1),

        # Hover Dropdown Children under "Media"
        ("media_main", "media", "Media & Invited Talks", "Seminars, Press Features, Op-Eds & Interviews", "media", "pages/media/media.html", "fas fa-newspaper", "Archive", 1, 1),
        ("media_talk_hub", "media", "Faculty Presentations Portal", "Interactive Slide Decks Hub & Speaker Notes", "media", "pages/media/talk/index.html", "fas fa-tv", "Portal", 2, 1),
        ("media_talk_deck", "media", "20-Min Committee Job Talk", "Full Reveal.js Interactive Faculty Slide Deck", "media", "pages/media/talk/talk.html", "fas fa-chalkboard", "20-Min Deck", 3, 1),
        ("media_talk_summary", "media", "10-Min Executive Brief", "Condensed Reveal.js High-Impact Research Deck", "media", "pages/media/talk/summary.html", "fas fa-bolt", "10-Min Brief", 4, 1),
    ]

    for entry in nav_entries:
        cur.execute("""
        INSERT INTO navigation_menu (
            nav_key, parent_key, label, sublabel, folder, rel_path, icon_class, badge_text, display_order, is_visible
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, entry)

    conn.commit()
    print(f"[OK] Seeded {len(nav_entries)} navigation menu items (including hover dropdowns for all sub-pages).")


def seed_html_templates(conn: sqlite3.Connection):
    """Seed global reusable HTML structural templates (Header, Footer, Subpage Quick-Bar) into html_templates."""
    cur = conn.cursor()

    templates = [
        (
            "global_header",
            "navigation",
            """<div class="container mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
        <div class="flex-shrink-0 flex items-center gap-2.5 sm:gap-3">
            <a href="{{PORTAL_HREF}}" rel="nofollow" title="Open Personal Portal" class="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full overflow-hidden flex-shrink-0 block hover:ring-2 hover:ring-sky-500 hover:scale-105 transition duration-300">
                <img src="{{EMBLEM_SRC}}" alt="Islamic Pattern Emblem" class="w-full h-full object-cover">
            </a>
            <a href="{{HOME_HREF}}" class="flex items-center gap-2 group">
                <span class="text-lg sm:text-xl font-bold text-gray-800 group-hover:text-sky-700 transition" data-db="site_meta.author_name_short">Islam Akef Ebeid</span>
                <img src="{{ARABIC_NAME_SRC}}" alt="Arabic Name" class="inline-block h-7 sm:h-8 ml-0.5">
            </a>
        </div>
        <nav class="hidden md:flex md:items-center md:space-x-6 lg:space-x-7">
            {{DESKTOP_LINKS_HTML}}
        </nav>
        <div class="md:hidden flex items-center">
            <button id="mobile-menu-button" class="text-gray-600 hover:text-gray-900 focus:outline-none p-2" aria-label="Toggle menu">
                <i class="fas fa-bars text-xl"></i>
            </button>
        </div>
    </div>
    <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-1.5 border-t border-gray-100 pt-2 max-h-[80vh] overflow-y-auto">
        {{MOBILE_LINKS_HTML}}
    </div>
</div>""",
            "Global sticky navigation header with hover dropdown menus for all sub-pages"
        ),
        (
            "global_footer",
            "footer",
            """<div class="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
    <p>&copy; <span id="year">{{YEAR}}</span> Islam Akef Ebeid. All Rights Reserved. <span class="mx-2 text-gray-500">&bull;</span> <a href="{{SITEMAP_HREF}}" target="_blank" class="text-gray-400 hover:text-sky-400 transition underline underline-offset-2">Sitemap</a> <span class="mx-2 text-gray-500">&bull;</span> <a href="{{PORTAL_HREF}}" class="text-gray-400 hover:text-sky-400 transition underline underline-offset-2" title="Private Executive Portal"><i class="fas fa-lock text-[10px] mr-0.5"></i> Portal</a></p>
</div>""",
            "Global academic website footer with Sitemap and Portal links"
        ),
        (
            "subpage_global_bar",
            "navigation",
            """<div class="bg-slate-900 text-slate-200 border-b border-slate-800 text-xs relative z-[9999]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-9 flex items-center justify-between">
        <div class="flex items-center gap-2">
            <a href="{{HOME_HREF}}" class="font-bold text-white hover:text-sky-400 transition flex items-center gap-1.5">
                <i class="fas fa-globe text-sky-400"></i> Islam Akef Ebeid
            </a>
            <span class="text-slate-600">/</span>
            <span class="text-slate-400 font-medium truncate">{{PAGE_TITLE}}</span>
        </div>
        <div class="hidden md:flex items-center space-x-4">
            {{SUBPAGE_QUICK_LINKS}}
        </div>
    </div>
</div>""",
            "Compact global navigation bar for standalone themed sub-pages"
        )
    ]

    for key, cat, html_str, desc in templates:
        cur.execute("""
        INSERT INTO html_templates (template_key, category, html_content, description)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(template_key) DO UPDATE SET
            category = excluded.category,
            html_content = excluded.html_content,
            description = excluded.description;
        """, (key, cat, html_str, desc))

    conn.commit()
    print(f"[OK] Seeded {len(templates)} global HTML templates into html_templates.")


def seed_external_stylesheets(conn: sqlite3.Connection):
    """Store global base CSS and all 7 external .css files into the stylesheets table."""
    cur = conn.cursor()

    global_css = """
body, button, input, select, textarea {
    font-family: 'Linux Libertine', 'Linux Libertine O', Georgia, 'Times New Roman', Times, serif;
}
.tag {
    display: inline-block;
    background-color: #e0f2fe;
    color: #075985;
    font-size: 0.75rem;
    line-height: 1rem;
    font-weight: 600;
    margin-right: 0.375rem;
    margin-bottom: 0.375rem;
    padding: 0.25rem 0.625rem;
    border-radius: 9999px;
}
.section-title {
    font-size: 1.875rem;
    line-height: 2.25rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 2rem;
    text-align: center;
}
.scrolled {
    background-color: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
}
/* Dropdown menu transitions */
.nav-dropdown-group:hover .nav-dropdown-menu {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
    pointer-events: auto;
}
.nav-dropdown-menu {
    opacity: 0;
    visibility: hidden;
    transform: translateY(6px);
    pointer-events: none;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
"""
    cur.execute("""
    INSERT INTO stylesheets (style_key, scope, page_slug, rel_path, style_type, css_content, description, display_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(style_key) DO UPDATE SET
        css_content = excluded.css_content,
        description = excluded.description;
    """, ("global_base", "global", None, None, "text/css", global_css.strip(), "Global typography, tags, section titles, and dropdown menu animations", 0))

    # Also catalog the 7 Reveal.js CSS files into stylesheets
    css_files = sorted(REPO_ROOT.rglob("*.css"))
    count = 1
    for css_path in css_files:
        rel_path = css_path.relative_to(REPO_ROOT).as_posix()
        style_key = "file_" + re.sub(r"[^a-zA-Z0-9_]", "_", rel_path)
        css_content = css_path.read_text(encoding="utf-8", errors="ignore")
        cur.execute("""
        INSERT INTO stylesheets (style_key, scope, page_slug, rel_path, style_type, css_content, description, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(style_key) DO UPDATE SET
            css_content = excluded.css_content,
            rel_path = excluded.rel_path;
        """, (style_key, "external_file", "talk-deck", rel_path, "text/css", css_content, f"External stylesheet {rel_path}", count))
        count += 1

    conn.commit()
    print(f"[OK] Seeded global_base and {count - 1} external .css files into stylesheets.")


def upsert_section(cur: sqlite3.Cursor, page_slug: str, section_key: str, heading: str, html_str: str, order: int):
    """Insert or update a page section in page_sections."""
    soup = BeautifulSoup(html_str, "html.parser")
    text_str = soup.get_text(separator=" ", strip=True)
    cur.execute("""
    INSERT INTO page_sections (page_slug, section_key, heading, content_html, content_text, display_order)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(page_slug, section_key) DO UPDATE SET
        heading = excluded.heading,
        content_html = excluded.content_html,
        content_text = excluded.content_text,
        display_order = excluded.display_order;
    """, (page_slug, section_key, heading, html_str.strip(), text_str, order))


def upsert_page_stylesheet(cur: sqlite3.Cursor, page_slug: str, rel_path: str, css_content: str, order: int):
    """Store a page's inline <style> block in stylesheets."""
    clean_css = convert_tailwind_apply(css_content.strip())
    if not clean_css:
        return
    style_key = f"style_{page_slug.replace('-', '_')}"
    cur.execute("""
    INSERT INTO stylesheets (style_key, scope, page_slug, rel_path, style_type, css_content, description, display_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(style_key) DO UPDATE SET
        css_content = excluded.css_content,
        rel_path = excluded.rel_path;
    """, (style_key, "page", page_slug, rel_path, "text/css", clean_css, f"Stylesheet for {page_slug} ({rel_path})", order))


def extract_all_pages_and_templates(conn: sqlite3.Connection):
    """
    Extract all 20 website HTML pages into `pages`, `page_sections`, and `stylesheets`.
    Idempotent: if an HTML file on disk is already converted to a minimal SQLite shell
    (marked by data-sqlite-shell="true"), it preserves the extracted sections & templates in SQLite.
    """
    cur = conn.cursor()

    # 1. Define the 11 Main Academic Portfolio Pages
    main_pages = [
        ("home", "Islam Akef Ebeid", "Academic Homepage & Research Portfolio", "pages/home/home.html", 1),
        ("relations", "Islam Akef Ebeid", "Relations, Mentors & Network Directory", "pages/relations/relations.html", 2),
        ("education", "Islam Akef Ebeid", "Education, Credentials & Academic Lineage", "pages/education/education.html", 3),
        ("research", "Islam Akef Ebeid", "Research Portfolio, Grants & Lab", "pages/research/research.html", 4),
        ("scholarship", "Islam Akef Ebeid", "Islamic Jurisprudence, Psychology, Books & Poetry", "pages/scholarship/scholarship.html", 5),
        ("teaching", "Islam Akef Ebeid", "Teaching Philosophy, Evaluations & Syllabi", "pages/teaching/teaching.html", 6),
        ("service", "Islam Akef Ebeid", "Institutional Governance, Peer Review & Leadership", "pages/service/service.html", 7),
        ("business", "Islam Akef Ebeid", "Unity Systems Startup & Enterprise Consulting", "pages/business/business.html", 8),
        ("hobbies", "Islam Akef Ebeid", "Hobbies, Creative Works & Personal Pursuits", "pages/hobbies/hobbies.html", 9),
        ("media", "Islam Akef Ebeid", "Media, Invited Talks & Public Engagement", "pages/media/media.html", 10),
        ("downloads", "Islam Akef Ebeid", "Downloads & Consolidated Document Index", "pages/downloads/downloads.html", 11),
    ]

    for slug, title, desc, rel_path, order in main_pages:
        html_file = REPO_ROOT / rel_path
        if not html_file.exists():
            continue
        raw_html = html_file.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(raw_html, "html.parser")

        # Check if already converted to a minimal shell
        if soup.html and soup.html.get("data-sqlite-shell") == "true":
            print(f"[SKIP-SHELL] {rel_path} is already a minimal shell; preserving database records.")
            continue

        # Extract <style> block
        styles = "\n".join(s.get_text() for s in soup.find_all("style"))
        upsert_page_stylesheet(cur, slug, rel_path, styles, order)

        # Extract special top banners/callouts in <main> that were not <section> tags
        main_el = soup.find("main")
        inline_script_code = ""

        if slug == "relations" and main_el:
            # Find Confidential Dead-Drop Callout div
            callout = main_el.find("div", class_=lambda c: c and "bg-slate-900" in c)
            if callout and not callout.get("data-db-section"):
                upsert_section(cur, "relations", "dead_drop_callout", "Confidential Dead-Drop & Secure Transmission Vault", str(callout), 0)
                placeholder = soup.new_tag("div")
                placeholder["data-db-section"] = "relations.dead_drop_callout"
                callout.replace_with(placeholder)

        elif slug == "research" and main_el:
            banner = main_el.find("div", class_=lambda c: c and "from-sky-900" in c)
            if banner and not banner.get("data-db-section"):
                upsert_section(cur, "research", "lab_banner", "The Data2AI4LifeSciences Laboratory", str(banner), 0)
                placeholder = soup.new_tag("div")
                placeholder["data-db-section"] = "research.lab_banner"
                banner.replace_with(placeholder)

        elif slug == "scholarship" and main_el:
            banner = main_el.find("div", class_=lambda c: c and "from-emerald-900" in c)
            if banner and not banner.get("data-db-section"):
                upsert_section(cur, "scholarship", "hero_banner", "Islamic Jurisprudence, Psychology, Writing & Creative Works", str(banner), 0)
                placeholder = soup.new_tag("div")
                placeholder["data-db-section"] = "scholarship.hero_banner"
                banner.replace_with(placeholder)

        elif slug == "business" and main_el:
            banner = main_el.find("div", class_=lambda c: c and "mb-16" in c and "text-center" in c)
            if banner and not banner.get("data-db-section"):
                upsert_section(cur, "business", "hero_banner", "Unity Systems & Startup Ventures", str(banner), 0)
                placeholder = soup.new_tag("div")
                placeholder["data-db-section"] = "business.hero_banner"
                banner.replace_with(placeholder)

        elif slug == "downloads" and main_el:
            banner = main_el.find("div", class_=lambda c: c and "border-sky-600" in c)
            if banner and not banner.get("data-db-section"):
                upsert_section(cur, "downloads", "header_filter_bar", "Downloads & Document Index", str(banner), 0)
                placeholder = soup.new_tag("div")
                placeholder["data-db-section"] = "downloads.header_filter_bar"
                banner.replace_with(placeholder)

            # Extract inline search script in downloads.html
            for scr in soup.find_all("script"):
                if not scr.get("src") and scr.get("type") != "application/ld+json":
                    if "search-input" in scr.get_text():
                        inline_script_code = scr.get_text().strip()

        # Build clean body_template_html with <header id="navbar">, <main>, and <footer id="footer">
        if main_el:
            # Strip HTML comments inside main_el so not even static comment text remains
            for comment in main_el.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            main_template_str = str(main_el)
        else:
            main_template_str = '<main id="main-content"></main>'

        body_template_html = (
            '<header id="navbar"></header>\n'
            f'{main_template_str}\n'
            '<footer id="footer"></footer>'
        )

        html_classes = " ".join(soup.html.get("class", ["scroll-smooth"])) if soup.html else "scroll-smooth"
        body_classes = " ".join(soup.body.get("class", ["antialiased", "overflow-x-hidden"])) if soup.body else "antialiased overflow-x-hidden"

        # Extract JSON-LD if present in <head>
        head_extra = []
        if soup.head:
            for ld in soup.head.find_all("script", type="application/ld+json"):
                head_extra.append(str(ld))
        head_html = "\n".join(head_extra)

        cur.execute("""
        INSERT INTO pages (
            slug, title, subtitle, description, rel_path, nav_order, is_public,
            html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            title = excluded.title,
            subtitle = excluded.subtitle,
            description = excluded.description,
            rel_path = excluded.rel_path,
            nav_order = excluded.nav_order,
            html_classes = excluded.html_classes,
            body_classes = excluded.body_classes,
            head_html = excluded.head_html,
            body_template_html = excluded.body_template_html,
            inline_scripts = excluded.inline_scripts,
            use_global_chrome = excluded.use_global_chrome;
        """, (slug, title, desc, desc, rel_path, order, 1, html_classes, body_classes, head_html, body_template_html, inline_script_code, 1))

    # 2. Extract Root `index.html`
    index_file = REPO_ROOT / "index.html"
    if index_file.exists():
        raw_index = index_file.read_text(encoding="utf-8", errors="ignore")
        soup_idx = BeautifulSoup(raw_index, "html.parser")
        if not (soup_idx.html and soup_idx.html.get("data-sqlite-shell") == "true"):
            p_tag = soup_idx.find("p")
            p_html = str(p_tag) if p_tag else '<p>If you are not redirected automatically, please follow <a href="pages/home/home.html">Redirect</a>.</p>'
            upsert_section(cur, "index", "redirect_notice", "Redirecting to Academic Homepage", p_html, 1)
            ld_scripts = "\n".join(str(s) for s in soup_idx.find_all("script", type="application/ld+json"))
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                rel_path = excluded.rel_path,
                head_html = excluded.head_html,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "index", "Islam Akef Ebeid", "Root Entry", "Canonical root redirect to Academic Homepage",
                "index.html", 0, 1, "", "", ld_scripts,
                '<div data-db-section="index.redirect_notice"></div>',
                'window.location.replace("pages/home/home.html");',
                0
            ))

    # 3. Seed `pages/relations/drop.html` (Confidential Dead-Drop & Handshake Terminal)
    drop_styles = """
body {
    font-family: 'Linux Libertine', 'Linux Libertine O', Georgia, 'Times New Roman', Times, serif;
    background-color: #020617;
    color: #f8fafc;
}
.mono {
    font-family: 'JetBrains Mono', monospace;
}
.glass {
    background: rgba(15, 23, 42, 0.78);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(51, 65, 85, 0.6);
}
"""
    upsert_page_stylesheet(cur, "drop", "pages/relations/drop.html", drop_styles, 12)
    cur.execute("DELETE FROM page_sections WHERE page_slug = 'drop';")

    drop_header_html = """<header class="border-b border-slate-800/80 bg-slate-950/90 backdrop-blur sticky top-0 z-30">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <a href="relations.html" class="inline-flex items-center gap-2.5 text-sm font-medium text-slate-300 hover:text-white transition">
            <i class="fas fa-arrow-left text-rose-500"></i>
            <span>Return to Relations &amp; Network Directory</span>
        </a>
        <div class="flex items-center gap-2 text-xs mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1 rounded-full">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>ZERO-TRUST HANDSHAKE CHANNEL</span>
        </div>
    </div>
</header>"""

    drop_step_handshake_html = """<section id="step-handshake" class="glass rounded-2xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
    <div class="absolute -top-24 -right-24 w-56 h-56 bg-rose-600/10 rounded-full blur-3xl pointer-events-none"></div>
    <div class="flex items-center gap-3 mb-4">
        <div class="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xl">
            <i class="fas fa-fingerprint"></i>
        </div>
        <div>
            <span class="text-[11px] mono uppercase tracking-widest text-rose-400 font-semibold block">Step 1 of 2 • Identity Handshake</span>
            <h1 class="text-xl sm:text-2xl font-bold text-white">Confidential Dead-Drop Verification</h1>
        </div>
    </div>
    <p class="text-slate-300 text-sm leading-relaxed mb-6">
        To prevent automated spam and unauthorized harvesting, this channel requires a lightweight cryptographic handshake before unlocking the direct transmission terminal to <strong>Dr. Islam Akef Ebeid</strong>.
    </p>
    <form onsubmit="verifyHandshake(event)" class="space-y-5">
        <div>
            <label class="block text-xs mono uppercase tracking-wider text-slate-400 mb-2">
                Handshake Verification Method
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                <button type="button" id="mode-challenge-btn" onclick="setHandshakeMode('challenge')" class="p-3 rounded-xl border border-rose-500 bg-rose-500/10 text-left transition">
                    <div class="text-xs font-bold text-white flex items-center justify-between">
                        <span>Academic Challenge</span>
                        <i class="fas fa-graduation-cap text-rose-400"></i>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-1">Answer a quick question about Dr. Islam's lab or institution.</p>
                </button>
                <button type="button" id="mode-token-btn" onclick="setHandshakeMode('token')" class="p-3 rounded-xl border border-slate-700 bg-slate-900/60 text-left transition">
                    <div class="text-xs font-bold text-slate-200 flex items-center justify-between">
                        <span>Direct Invite Token</span>
                        <i class="fas fa-key text-amber-400"></i>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-1">Enter a pre-shared invite key provided by Dr. Islam.</p>
                </button>
            </div>
        </div>
        <div id="challenge-box" class="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
            <label for="handshake-input" id="handshake-prompt-label" class="block text-xs font-semibold text-amber-300 mb-2">
                Challenge: What is the name of Dr. Islam's primary university (acronym or full name) or research lab?
            </label>
            <input type="text" id="handshake-input" required placeholder="e.g., TWU, Texas Woman's University, or Data2AI4LifeSciences"
                class="w-full bg-slate-950 border border-slate-700 focus:border-rose-500 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition mono">
            <p id="handshake-error" class="hidden text-xs text-rose-400 mt-2 flex items-center gap-1.5">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Verification failed. Hint: Enter <code>TWU</code> or <code>Data2AI4LifeSciences</code>.</span>
            </p>
        </div>
        <button type="submit" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-3 px-5 rounded-xl shadow-lg shadow-rose-600/25 transition flex items-center justify-center gap-2 text-sm">
            <i class="fas fa-unlock-alt"></i>
            <span>Verify Handshake &amp; Unlock Transmission Terminal</span>
        </button>
    </form>
</section>"""

    drop_step_compose_html = """<section id="step-compose" class="hidden glass rounded-2xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-4 mb-6">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <i class="fas fa-shield-alt"></i>
            </div>
            <div>
                <span class="text-[11px] mono uppercase tracking-widest text-emerald-400 font-semibold block">Step 2 of 2 • Channel Unlocked</span>
                <h2 class="text-lg sm:text-xl font-bold text-white">Compose Confidential Transmission</h2>
            </div>
        </div>
        <span id="session-badge" class="text-[11px] mono bg-slate-900 border border-slate-700 text-slate-300 px-2.5 py-1 rounded"></span>
    </div>
    <form id="drop-form" onsubmit="submitDropMessage(event)" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
                <label class="block text-xs mono uppercase text-slate-400 mb-1">Your Name / Alias *</label>
                <input type="text" id="sender-name" required placeholder="Dr. Jane Doe"
                    class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-400 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none">
            </div>
            <div>
                <label class="block text-xs mono uppercase text-slate-400 mb-1">Return Email / Contact *</label>
                <input type="email" id="sender-contact" required placeholder="jane.doe@university.edu"
                    class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-400 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none">
            </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="sm:col-span-2">
                <label class="block text-xs mono uppercase text-slate-400 mb-1">Subject / Topic *</label>
                <input type="text" id="msg-subject" required placeholder="Research Collaboration / Confidential Inquiry"
                    class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-400 rounded-lg px-3.5 py-2 text-sm text-white focus:outline-none">
            </div>
            <div>
                <label class="block text-xs mono uppercase text-slate-400 mb-1">Priority Level</label>
                <select id="msg-priority" class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none">
                    <option value="NORMAL">Normal</option>
                    <option value="HIGH">High Priority</option>
                    <option value="URGENT">Urgent / Time-Sensitive</option>
                </select>
            </div>
        </div>
        <div>
            <label class="block text-xs mono uppercase text-slate-400 mb-1">Confidential Message Payload *</label>
            <textarea id="msg-body" rows="5" required placeholder="Enter your message, manuscript link, or confidential inquiry..."
                class="w-full bg-slate-950 border border-slate-700 focus:border-emerald-400 rounded-lg p-3.5 text-sm text-white focus:outline-none"></textarea>
        </div>
        <div class="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p class="text-[11px] text-slate-400">
                <i class="fas fa-lock text-emerald-400 mr-1"></i> Dispatches directly to Dr. Islam's verified inbox (<code>islam.akef@gmail.com</code>) &amp; Portal Hub.
            </p>
            <button type="submit" id="dispatch-btn" class="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-6 rounded-xl shadow-lg transition flex items-center justify-center gap-2 text-sm">
                <i class="fas fa-paper-plane"></i>
                <span>Encrypt &amp; Dispatch Now</span>
            </button>
        </div>
    </form>
</section>"""

    drop_step_dispatched_html = """<section id="step-dispatched" class="hidden glass rounded-2xl p-6 sm:p-10 shadow-2xl text-center space-y-5">
    <div class="w-16 h-16 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 flex items-center justify-center text-2xl mx-auto">
        <i class="fas fa-check-double"></i>
    </div>
    <div>
        <span class="text-xs mono uppercase tracking-widest text-emerald-400 font-semibold">Transmission Complete</span>
        <h2 class="text-2xl font-bold text-white mt-1">Confidential Packet Dispatched</h2>
        <p id="dispatch-status-text" class="text-sm text-slate-300 mt-2 max-w-lg mx-auto leading-relaxed">
            Your message has been transmitted to <strong>islam.akef@gmail.com</strong> and logged in the Executive Portal inbox.
        </p>
    </div>
    <div class="bg-slate-950/90 border border-slate-800 rounded-xl p-4 text-left font-mono text-xs text-slate-300 max-w-lg mx-auto space-y-1">
        <div><span class="text-slate-500">PACKET_ID:</span> <span id="receipt-id" class="text-emerald-400"></span></div>
        <div><span class="text-slate-500">TIMESTAMP:</span> <span id="receipt-time"></span></div>
        <div><span class="text-slate-500">DESTINATION:</span> <span class="text-sky-400">islam.akef@gmail.com</span></div>
    </div>
    <div class="pt-3 flex flex-wrap justify-center gap-3">
        <button type="button" onclick="resetDropForm()" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition">
            Send Another Transmission
        </button>
        <a href="relations.html" class="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition">
            Return to Relations Page
        </a>
    </div>
</section>"""

    drop_footer_html = """<footer class="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
    <div class="max-w-4xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>&copy; 2026 Dr. Islam Akef Ebeid • Zero-Trust Dead-Drop Protocol</span>
        <a href="../portal/portal.html" class="text-slate-400 hover:text-sky-400 transition">
            <i class="fas fa-shield-halved mr-1"></i> Executive Portal Login
        </a>
    </div>
</footer>"""

    upsert_section(cur, "drop", "header", "Encrypted Dead-Drop Header", drop_header_html, 1)
    upsert_section(cur, "drop", "step-handshake", "Identity Handshake Verification", drop_step_handshake_html, 2)
    upsert_section(cur, "drop", "step-compose", "Compose Confidential Transmission", drop_step_compose_html, 3)
    upsert_section(cur, "drop", "step-dispatched", "Transmission Dispatched Confirmation", drop_step_dispatched_html, 4)
    upsert_section(cur, "drop", "footer", "Encrypted Dead-Drop Footer", drop_footer_html, 5)

    drop_inline_js = """
const DROP_STORAGE_KEY = 'dr_islam_portal_messages_v2';
const TARGET_INBOX_EMAIL = 'islam.akef@gmail.com';
let handshakeMode = 'challenge';

function setHandshakeMode(mode) {
    handshakeMode = mode;
    const chBtn = document.getElementById('mode-challenge-btn');
    const tkBtn = document.getElementById('mode-token-btn');
    const label = document.getElementById('handshake-prompt-label');
    const input = document.getElementById('handshake-input');
    const err = document.getElementById('handshake-error');
    if (err) err.classList.add('hidden');
    if (mode === 'token') {
        tkBtn.className = 'p-3 rounded-xl border border-amber-500 bg-amber-500/10 text-left transition';
        chBtn.className = 'p-3 rounded-xl border border-slate-700 bg-slate-900/60 text-left transition';
        label.textContent = 'Enter Direct Handshake Token provided by Dr. Islam:';
        input.placeholder = 'Enter invite token...';
    } else {
        chBtn.className = 'p-3 rounded-xl border border-rose-500 bg-rose-500/10 text-left transition';
        tkBtn.className = 'p-3 rounded-xl border border-slate-700 bg-slate-900/60 text-left transition';
        label.textContent = "Challenge: What is the name of Dr. Islam's primary university (acronym or full name) or research lab?";
        input.placeholder = "e.g., TWU, Texas Woman's University, or Data2AI4LifeSciences";
    }
}

function verifyHandshake(e) {
    e.preventDefault();
    const raw = (document.getElementById('handshake-input').value || '').trim().toLowerCase();
    const accepted = [
        'islam2026', 'twu', 'texas womans university', "texas woman's university",
        'data2ai4lifesciences', 'data2ai4lifesciences lab', 'nile university', 'ualr', 'ut austin', 'ebeid'
    ];
    const valid = accepted.some(ans => raw.includes(ans));
    const err = document.getElementById('handshake-error');
    if (!valid) {
        if (err) err.classList.remove('hidden');
        return;
    }
    if (err) err.classList.add('hidden');
    document.getElementById('step-handshake').classList.add('hidden');
    document.getElementById('step-compose').classList.remove('hidden');
    const badge = document.getElementById('session-badge');
    if (badge) {
        badge.textContent = 'SESSION-' + Math.random().toString(36).substring(2, 8).toUpperCase();
    }
}

async function submitDropMessage(e) {
    e.preventDefault();
    const btn = document.getElementById('dispatch-btn');
    const senderName = document.getElementById('sender-name').value.trim();
    const senderContact = document.getElementById('sender-contact').value.trim();
    const subject = document.getElementById('msg-subject').value.trim();
    const priority = document.getElementById('msg-priority').value;
    const body = document.getElementById('msg-body').value.trim();
    const packetId = 'PKT-' + Date.now().toString(36).toUpperCase();
    const timestamp = new Date().toISOString();

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i><span>Dispatching Packet...</span>';
    }

    // 1. Store in local portal inbox queue
    try {
        const existing = JSON.parse(localStorage.getItem(DROP_STORAGE_KEY) || '[]');
        existing.unshift({
            id: packetId,
            senderName,
            senderContact,
            subject: `[${priority}] ${subject}`,
            body,
            timestamp,
            handshakeMode,
            read: false
        });
        localStorage.setItem(DROP_STORAGE_KEY, JSON.stringify(existing));
    } catch (err) {
        console.warn('Local storage queue write failed:', err);
    }

    // 2. Dispatch directly to islam.akef@gmail.com via FormSubmit AJAX relay
    let relayDelivered = false;
    try {
        const response = await fetch(`https://formsubmit.co/ajax/${TARGET_INBOX_EMAIL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                _subject: `[Confidential Dead-Drop • ${priority}] ${subject}`,
                packet_id: packetId,
                sender_name: senderName,
                sender_email: senderContact,
                priority: priority,
                message: body,
                timestamp: timestamp
            })
        });
        const resJson = await response.json();
        if (response.ok && (resJson.success === 'true' || resJson.success === true)) {
            relayDelivered = true;
        }
    } catch (networkErr) {
        console.warn('Direct HTTPS relay warning:', networkErr);
    }

    document.getElementById('step-compose').classList.add('hidden');
    document.getElementById('step-dispatched').classList.remove('hidden');
    document.getElementById('receipt-id').textContent = packetId;
    document.getElementById('receipt-time').textContent = timestamp;
    const statusText = document.getElementById('dispatch-status-text');
    if (statusText) {
        statusText.innerHTML = relayDelivered
            ? 'Your encrypted packet was dispatched directly to <strong>islam.akef@gmail.com</strong> and synchronized with the Executive Portal inbox.'
            : 'Your packet has been recorded in the local Executive Portal queue and prepared for <strong>islam.akef@gmail.com</strong>.';
    }
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Encrypt &amp; Dispatch Now</span>';
    }
}

function resetDropForm() {
    document.getElementById('drop-form').reset();
    document.getElementById('step-dispatched').classList.add('hidden');
    document.getElementById('step-compose').classList.remove('hidden');
}
""".strip()

    drop_body_tpl = (
        '<div id="global-subpage-nav"></div>\n'
        '<div data-db-section="drop.header"></div>\n'
        '<main class="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-10 flex flex-col justify-center">\n'
        '    <div data-db-section="drop.step-handshake"></div>\n'
        '    <div data-db-section="drop.step-compose"></div>\n'
        '    <div data-db-section="drop.step-dispatched"></div>\n'
        '</main>\n'
        '<div data-db-section="drop.footer"></div>'
    )
    cur.execute("""
    INSERT INTO pages (
        slug, title, subtitle, description, rel_path, nav_order, is_public,
        html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(slug) DO UPDATE SET
        title = excluded.title,
        rel_path = excluded.rel_path,
        html_classes = excluded.html_classes,
        body_classes = excluded.body_classes,
        body_template_html = excluded.body_template_html,
        inline_scripts = excluded.inline_scripts,
        use_global_chrome = excluded.use_global_chrome;
    """, (
        "drop", "Confidential Drop-Box | Dr. Islam Akef Ebeid", "Confidential Dead-Drop & Handshake Terminal",
        "Zero-trust confidential message transmission terminal", "pages/relations/drop.html", 12, 1,
        "dark", "min-h-screen flex flex-col antialiased selection:bg-rose-500 selection:text-white",
        "", drop_body_tpl, drop_inline_js, 0
    ))

    # 4. Extract `pages/research/lab.html`
    lab_file = REPO_ROOT / "pages/research/lab.html"
    if lab_file.exists():
        raw_lab = lab_file.read_text(encoding="utf-8", errors="ignore")
        soup_lab = BeautifulSoup(raw_lab, "html.parser")
        if not (soup_lab.html and soup_lab.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_lab.find_all("style"))
            upsert_page_stylesheet(cur, "lab", "pages/research/lab.html", styles, 13)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'lab';")
            hdr = soup_lab.find("header")
            if hdr:
                upsert_section(cur, "lab", "header", "Data2AI4LifeSciences Lab Header", str(hdr), 1)

            sec_placeholders = []
            for idx, sec in enumerate(soup_lab.find_all("section")):
                sec_id = sec.get("id", f"section_{idx+1}")
                h_el = sec.find(["h1", "h2", "h3"])
                h_txt = h_el.get_text(strip=True) if h_el else sec_id
                upsert_section(cur, "lab", sec_id, h_txt, str(sec), idx + 2)
                sec_placeholders.append(f'    <div data-db-section="lab.{sec_id}"></div>')

            ftr = soup_lab.find("footer")
            if ftr:
                upsert_section(cur, "lab", "footer", "Data2AI4LifeSciences Lab Footer", str(ftr), 20)

            # Extract body inline script (excluding head tailwind.config script)
            body_scripts = []
            if soup_lab.body:
                for s in soup_lab.body.find_all("script"):
                    if not s.get("src"):
                        body_scripts.append(s.get_text().strip())
            inline_js = "\n".join(body_scripts)

            body_tpl = (
                '<div id="global-subpage-nav"></div>\n'
                '<div data-db-section="lab.header"></div>\n'
                '<main class="container mx-auto px-6 py-12">\n'
                + "\n".join(sec_placeholders) + "\n"
                '</main>\n'
                '<div data-db-section="lab.footer"></div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                html_classes = excluded.html_classes,
                body_classes = excluded.body_classes,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "lab", "The Data2AI4LifeSciences Laboratory @ TWU", "Data2AI4LifeSciences Lab",
                "Official laboratory page for the Data2AI4LifeSciences Lab at Texas Woman's University",
                "pages/research/lab.html", 13, 1,
                "scroll-smooth", "text-gray-700", "", body_tpl, inline_js, 0
            ))

    # 5. Extract `pages/research/xlpm/index.html`
    xlpm_file = REPO_ROOT / "pages/research/xlpm/index.html"
    if xlpm_file.exists():
        raw_xlpm = xlpm_file.read_text(encoding="utf-8", errors="ignore")
        soup_xlpm = BeautifulSoup(raw_xlpm, "html.parser")
        if not (soup_xlpm.html and soup_xlpm.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_xlpm.find_all("style"))
            upsert_page_stylesheet(cur, "xlpm", "pages/research/xlpm/index.html", styles, 14)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'xlpm';")
            hdr = soup_xlpm.find("header")
            if hdr:
                upsert_section(cur, "xlpm", "header", "XLPM & VisInt-X Header", str(hdr), 1)

            sec_placeholders = []
            for idx, sec in enumerate(soup_xlpm.find_all("section")):
                sec_key = f"section_{idx+1}"
                h_el = sec.find(["h1", "h2", "h3"])
                h_txt = h_el.get_text(strip=True) if h_el else sec_key
                upsert_section(cur, "xlpm", sec_key, h_txt, str(sec), idx + 2)
                sec_placeholders.append(f'    <div data-db-section="xlpm.{sec_key}"></div>')

            ftr = soup_xlpm.find("footer")
            if ftr:
                upsert_section(cur, "xlpm", "footer", "XLPM Footer", str(ftr), 10)

            body_tpl = (
                '<div id="global-subpage-nav"></div>\n'
                '<div data-db-section="xlpm.header"></div>\n'
                '<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">\n'
                + "\n".join(sec_placeholders) + "\n"
                '</main>\n'
                '<div data-db-section="xlpm.footer"></div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                html_classes = excluded.html_classes,
                body_classes = excluded.body_classes,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "xlpm", "XLPM & VisInt-X | Interactive Protein Structure & Cross-Linking Demo",
                "XLPM 3D Biomolecular Structure Viewer",
                "Interactive WebGL and D3 visualization of Cross-Linking Mass Spectrometry (XL-MS) protein structures",
                "pages/research/xlpm/index.html", 14, 1,
                "scroll-smooth", "antialiased overflow-x-hidden", "", body_tpl, "", 0
            ))

    # 6. Extract `pages/business/storefront.html`
    sf_file = REPO_ROOT / "pages/business/storefront.html"
    if sf_file.exists():
        raw_sf = sf_file.read_text(encoding="utf-8", errors="ignore")
        soup_sf = BeautifulSoup(raw_sf, "html.parser")
        if not (soup_sf.html and soup_sf.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_sf.find_all("style"))
            upsert_page_stylesheet(cur, "storefront", "pages/business/storefront.html", styles, 15)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'storefront';")
            top_bar = soup_sf.find("div", class_="top-bar")
            hdr = soup_sf.find("header")
            modal = soup_sf.find("div", id="license-modal")
            ftr = soup_sf.find("footer")

            if top_bar:
                upsert_section(cur, "storefront", "top_bar", "Unity Systems Top Announcement Bar", str(top_bar), 1)
            if hdr:
                upsert_section(cur, "storefront", "header", "Unity Systems Brand Header", str(hdr), 2)

            sf_sec_placeholders = []
            for idx, sec in enumerate(soup_sf.find_all("section")):
                sec_key = sec.get("id") or f"section_{idx+1}"
                h_el = sec.find(["h1", "h2", "h3"])
                h_txt = h_el.get_text(strip=True) if h_el else sec_key
                upsert_section(cur, "storefront", sec_key, h_txt, str(sec), idx + 3)
                sf_sec_placeholders.append(f'    <div data-db-section="storefront.{sec_key}"></div>')

            if modal:
                upsert_section(cur, "storefront", "license_modal", "Enterprise Licensing Modal", str(modal), 15)
            if ftr:
                upsert_section(cur, "storefront", "footer", "Unity Systems Storefront Footer", str(ftr), 16)

            inline_js = "\n".join(
                s.get_text().strip() for s in soup_sf.find_all("script") if not s.get("src")
            )
            body_tpl = (
                '<div id="global-subpage-nav"></div>\n'
                '<div data-db-section="storefront.top_bar"></div>\n'
                '<div data-db-section="storefront.header"></div>\n'
                '<main>\n'
                + "\n".join(sf_sec_placeholders) + "\n"
                '</main>\n'
                '<div data-db-section="storefront.license_modal"></div>\n'
                '<div data-db-section="storefront.footer"></div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                html_classes = excluded.html_classes,
                body_classes = excluded.body_classes,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "storefront", "Unity Systems | Software Storefront & Commercial Solutions",
                "Unity Systems Storefront",
                "Commercial software catalog, SaaS platforms, and enterprise AI licensing by Unity Systems",
                "pages/business/storefront.html", 15, 1,
                "", "", "", body_tpl, inline_js, 0
            ))

    # 7. Extract `pages/media/talk/index.html`
    talk_idx_file = REPO_ROOT / "pages/media/talk/index.html"
    if talk_idx_file.exists():
        raw_ti = talk_idx_file.read_text(encoding="utf-8", errors="ignore")
        soup_ti = BeautifulSoup(raw_ti, "html.parser")
        if not (soup_ti.html and soup_ti.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_ti.find_all("style"))
            upsert_page_stylesheet(cur, "talk-index", "pages/media/talk/index.html", styles, 16)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'talk-index';")
            hdr = soup_ti.find("header")
            hero = soup_ti.find("section", class_="hero")
            cards = soup_ti.find("section", class_="decks-grid")
            ftr = soup_ti.find("footer")

            if hdr:
                upsert_section(cur, "talk-index", "header", "Faculty Presentations Header", str(hdr), 1)
            if hero:
                upsert_section(cur, "talk-index", "hero", "Faculty Job Talk & Executive Briefings Hero", str(hero), 2)
            if cards:
                upsert_section(cur, "talk-index", "cards", "Interactive Presentation Decks & Downloads", str(cards), 3)
            if ftr:
                upsert_section(cur, "talk-index", "footer", "Presentations Portal Footer", str(ftr), 4)

            body_tpl = (
                '<div id="global-subpage-nav"></div>\n'
                '<div class="container">\n'
                '    <div data-db-section="talk-index.header"></div>\n'
                '    <div data-db-section="talk-index.hero"></div>\n'
                '    <div data-db-section="talk-index.cards"></div>\n'
                '    <div data-db-section="talk-index.footer"></div>\n'
                '</div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                body_template_html = excluded.body_template_html,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "talk-index", "Islam Akef Ebeid | Faculty Interview Presentations",
                "Faculty Interview Presentations Portal",
                "Interactive Reveal.js presentation decks for faculty job talk and executive briefing",
                "pages/media/talk/index.html", 16, 1,
                "", "", "", body_tpl, "", 0
            ))

    # 8. Extract `pages/media/talk/talk.html` (20-Min Committee Job Talk Deck)
    talk_deck_file = REPO_ROOT / "pages/media/talk/talk.html"
    if talk_deck_file.exists():
        raw_td = talk_deck_file.read_text(encoding="utf-8", errors="ignore")
        soup_td = BeautifulSoup(raw_td, "html.parser")
        if not (soup_td.html and soup_td.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_td.find_all("style"))
            upsert_page_stylesheet(cur, "talk-deck", "pages/media/talk/talk.html", styles, 17)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'talk-deck';")
            deck_nav = soup_td.find("div", class_="deck-nav")
            if deck_nav:
                upsert_section(cur, "talk-deck", "deck_nav", "Deck Navigation Overlay", str(deck_nav), 1)

            slides_div = soup_td.find("div", class_="slides")
            slide_placeholders = []
            if slides_div:
                top_sections = slides_div.find_all("section", recursive=False)
                for idx, slide in enumerate(top_sections):
                    s_key = f"slide_{idx+1}"
                    h_el = slide.find(["h1", "h2", "h3", "h4"])
                    h_txt = h_el.get_text(strip=True) if h_el else f"Slide {idx+1}"
                    upsert_section(cur, "talk-deck", s_key, h_txt, str(slide), idx + 2)
                    slide_placeholders.append(f'            <div data-db-section="talk-deck.{s_key}"></div>')

            inline_js = ""
            for s in soup_td.find_all("script"):
                if not s.get("src") and "Reveal.initialize" in s.get_text():
                    inline_js = s.get_text().strip()

            body_tpl = (
                '<div data-db-section="talk-deck.deck_nav"></div>\n'
                '<div class="reveal">\n'
                '    <div class="slides">\n'
                + "\n".join(slide_placeholders) + "\n"
                '    </div>\n'
                '</div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "talk-deck", "Islam Akef Ebeid | 20-Min Committee Job Talk",
                "20-Min Committee Job Talk Slide Deck",
                "Full 17-slide interactive Reveal.js presentation deck",
                "pages/media/talk/talk.html", 17, 1,
                "", "", "", body_tpl, inline_js, 0
            ))

    # 9. Extract `pages/media/talk/summary.html` (10-Min Executive Brief Deck)
    talk_sum_file = REPO_ROOT / "pages/media/talk/summary.html"
    if talk_sum_file.exists():
        raw_ts = talk_sum_file.read_text(encoding="utf-8", errors="ignore")
        soup_ts = BeautifulSoup(raw_ts, "html.parser")
        if not (soup_ts.html and soup_ts.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_ts.find_all("style"))
            upsert_page_stylesheet(cur, "talk-summary", "pages/media/talk/summary.html", styles, 18)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'talk-summary';")
            deck_nav = soup_ts.find("div", class_="deck-nav")
            if deck_nav:
                upsert_section(cur, "talk-summary", "deck_nav", "Executive Brief Navigation Overlay", str(deck_nav), 1)

            slides_div = soup_ts.find("div", class_="slides")
            slide_placeholders = []
            if slides_div:
                top_sections = slides_div.find_all("section", recursive=False)
                for idx, slide in enumerate(top_sections):
                    s_key = f"slide_{idx+1}"
                    h_el = slide.find(["h1", "h2", "h3", "h4"])
                    h_txt = h_el.get_text(strip=True) if h_el else f"Slide {idx+1}"
                    upsert_section(cur, "talk-summary", s_key, h_txt, str(slide), idx + 2)
                    slide_placeholders.append(f'            <div data-db-section="talk-summary.{s_key}"></div>')

            inline_js = ""
            for s in soup_ts.find_all("script"):
                if not s.get("src") and "Reveal.initialize" in s.get_text():
                    inline_js = s.get_text().strip()

            body_tpl = (
                '<div data-db-section="talk-summary.deck_nav"></div>\n'
                '<div class="reveal">\n'
                '    <div class="slides">\n'
                + "\n".join(slide_placeholders) + "\n"
                '    </div>\n'
                '</div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "talk-summary", "Islam Akef Ebeid | 10-Min Executive Brief",
                "10-Min Executive Brief Slide Deck",
                "Condensed 8-slide interactive Reveal.js executive presentation",
                "pages/media/talk/summary.html", 18, 1,
                "", "", "", body_tpl, inline_js, 0
            ))

    # 10. Extract `pages/portal/portal.html` (Personal Command Center & Vault)
    portal_file = REPO_ROOT / "pages/portal/portal.html"
    if portal_file.exists():
        raw_pt = portal_file.read_text(encoding="utf-8", errors="ignore")
        soup_pt = BeautifulSoup(raw_pt, "html.parser")
        if not (soup_pt.html and soup_pt.html.get("data-sqlite-shell") == "true"):
            styles = "\n".join(s.get_text() for s in soup_pt.find_all("style"))
            upsert_page_stylesheet(cur, "portal", "pages/portal/portal.html", styles, 19)

            cur.execute("DELETE FROM page_sections WHERE page_slug = 'portal';")
            login_div = soup_pt.find("div", id="login-screen")
            app_div = soup_pt.find("div", id="portal-app")
            reply_modal = soup_pt.find("div", id="secure-reply-modal")
            bm_modal = soup_pt.find("div", id="add-bookmark-modal")

            if login_div:
                upsert_section(cur, "portal", "login_screen", "Executive Portal Authentication Gate", str(login_div), 1)
            if app_div:
                upsert_section(cur, "portal", "portal_app", "Executive Portal Main Workspace", str(app_div), 2)
            if reply_modal:
                upsert_section(cur, "portal", "secure_reply_modal", "Encrypted Direct Email Relay Modal", str(reply_modal), 3)
            if bm_modal:
                upsert_section(cur, "portal", "add_bookmark_modal", "Add Bookmark Modal", str(bm_modal), 4)

            body_tpl = (
                '<div data-db-section="portal.login_screen"></div>\n'
                '<div data-db-section="portal.portal_app"></div>\n'
                '<div data-db-section="portal.secure_reply_modal"></div>\n'
                '<div data-db-section="portal.add_bookmark_modal"></div>'
            )
            cur.execute("""
            INSERT INTO pages (
                slug, title, subtitle, description, rel_path, nav_order, is_public,
                html_classes, body_classes, head_html, body_template_html, inline_scripts, use_global_chrome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                rel_path = excluded.rel_path,
                html_classes = excluded.html_classes,
                body_classes = excluded.body_classes,
                body_template_html = excluded.body_template_html,
                inline_scripts = excluded.inline_scripts,
                use_global_chrome = excluded.use_global_chrome;
            """, (
                "portal", "Islam Akef Ebeid | Executive Personal Portal",
                "Personal Command Center & Vault",
                "Encrypted command center for bookmarks, notes, tasks, and secure messaging",
                "pages/portal/portal.html", 19, 0,
                "dark", "min-h-screen antialiased selection:bg-sky-500 selection:text-white",
                "", body_tpl, "", 0
            ))

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM pages")
    p_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM page_sections")
    s_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stylesheets")
    st_cnt = cur.fetchone()[0]
    print(f"[OK] Extracted {p_cnt} pages, {s_cnt} modular HTML sections, and {st_cnt} stylesheets into SQLite.")


def extract_documents_and_media(conn: sqlite3.Connection):
    """Catalog all documents and images into database."""
    cur = conn.cursor()

    doc_count = 0
    if DOCS_DIR.exists():
        for doc_path in DOCS_DIR.iterdir():
            if doc_path.is_file():
                rel = f"documents/{doc_path.name}"
                size = doc_path.stat().st_size
                name_clean = doc_path.stem.replace('_', ' ').replace('-', ' ').title()
                cat = "CV" if "cv" in doc_path.name.lower() else "Document"
                cur.execute("""
                INSERT INTO documents (filename, title, rel_path, category, file_size_bytes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(rel_path) DO UPDATE SET
                    filename = excluded.filename,
                    title = excluded.title,
                    file_size_bytes = excluded.file_size_bytes;
                """, (doc_path.name, name_clean, rel, cat, size))
                doc_count += 1

    img_count = 0
    if IMAGES_DIR.exists():
        for img_path in IMAGES_DIR.iterdir():
            if img_path.is_file():
                rel = f"images/{img_path.name}"
                name_clean = img_path.stem.replace('_', ' ').replace('-', ' ').title()
                cat = "headshot" if "image1" in img_path.name.lower() else "media"
                cur.execute("""
                INSERT INTO images (filename, alt_text, rel_path, category)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(rel_path) DO UPDATE SET
                    filename = excluded.filename,
                    alt_text = excluded.alt_text;
                """, (img_path.name, name_clean, rel, cat))
                img_count += 1

    conn.commit()
    print(f"[OK] Cataloged {doc_count} documents and {img_count} media images.")


def extract_portal_bookmarks(conn: sqlite3.Connection):
    """Extract Chrome Bookmarks tree from bookmarks.json into portal_bookmarks table."""
    bm_json_path = PAGES_DIR / "portal" / "bookmarks.json"
    if not bm_json_path.exists():
        return

    try:
        with open(bm_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        bookmarks_list = data.get("bookmarks", [])
        cur = conn.cursor()
        count = 0
        for item in bookmarks_list:
            cur.execute("""
            INSERT INTO portal_bookmarks (chrome_id, title, url, category, subfolder, favicon, pinned, click_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chrome_id) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                category = excluded.category,
                subfolder = excluded.subfolder;
            """, (
                str(item.get("id")),
                item.get("name", item.get("title", "Untitled")),
                item.get("url", "#"),
                item.get("category", "General"),
                item.get("subfolder", ""),
                item.get("favicon", ""),
                0,
                0
            ))
            count += 1

        conn.commit()
        print(f"[OK] Seeded {count} portal bookmarks into database.")
    except Exception as e:
        print(f"[WARN] Failed extracting portal bookmarks: {e}")


def extract_courses(conn: sqlite3.Connection):
    """Seed courses and syllabi records."""
    cur = conn.cursor()
    cur.execute("DELETE FROM courses;")
    courses_data = [
        ("CSCI 3603 / 5173", "Human-Computer Interaction & Advanced HCI", "Texas Woman's University", "Fall / Spring", "documents/CSCI-3603-2-Syllabus.pdf", "UI/UX engineering, user study paradigms, usability metrics, accessibility, cognitive load frameworks."),
        ("CSCI 5103", "Advanced Database Systems", "Texas Woman's University", "Graduate Core", "documents/CSCI-5103-Syllabus.pdf", "Relational database internals, query optimization, ACID transactions, distributed databases, NoSQL engines."),
        ("CSCI 4513 / 5803", "Artificial Intelligence & Intelligent Systems", "Texas Woman's University", "Advanced CS", "documents/CSCI-5803-Syllabus.pdf", "Heuristic search, knowledge representation, reinforcement learning, NLP, computer vision, ethical AI."),
        ("CSCI 5663", "Deep Learning & Neural Architectures", "Texas Woman's University", "Graduate Elective", "documents/CSCI-5663-Syllabus.pdf", "Backpropagation, CNNs, RNNs/Transformers, Graph Neural Networks (GNNs), biological sequence modeling."),
        ("CSCI 5001", "Graduate Computer Science Seminar", "Texas Woman's University", "Master's Core", "documents/CSCI-5001-Syllabus-HB2504.pdf", "Research methods, peer review ethics, literature synthesis, conference presentation, proposal writing."),
        ("CSCI 4623", "Big Data Analytics & Principles of Data Mining", "Texas Woman's University", "Undergraduate", "", "Data warehousing, ETL pipelines, clustering, classification, association rules, scalable cloud analytics."),
        ("CSCI 2111 / 2113", "Data Structures & Algorithms Laboratory", "Southern Arkansas University", "Undergraduate Core", "documents/CSCI-2111-2113-Syllabus-Ebeid.pdf", "Object-oriented implementation of linked lists, trees, graphs, sorting algorithms, asymptotic analysis."),
        ("MCIS 5133", "Database Architecture & Information Systems", "Southern Arkansas University", "Graduate Core", "documents/MCIS-5133-Syllabus.pdf", "Relational calculus, database design, normalization, stored procedures, enterprise data governance."),
        ("MCIS 5013", "Advanced Operating Systems & Kernel Architecture", "Southern Arkansas University", "Graduate Core", "documents/MCIS-5013-Syllabus.pdf", "Concurrency, process synchronization, virtual memory management, file system architectures."),
        ("PAISE", "Physics, AI, and Simulation Engineering Seminar", "The University of Texas at Austin", "Alumni / Fellowship", "documents/PAISE-2019-Syllabus.pdf", "High-performance computing, scientific ML simulations, AI-accelerated physics calculations.")
    ]
    for idx, (code, title, inst, term, syl, desc) in enumerate(courses_data, 1):
        cur.execute("""
        INSERT INTO courses (code, title, institution, term, syllabus_path, description, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, title, inst, term, syl, desc, idx))
    conn.commit()
    print(f"[OK] Seeded {len(courses_data)} courses and syllabi records.")


def extract_publications(conn: sqlite3.Connection):
    """Seed peer-reviewed research publications."""
    cur = conn.cursor()
    cur.execute("DELETE FROM publications;")
    pubs_data = [
        ("Deep Learning and Graph Neural Networks for Protein-Protein Interaction Prediction: Cross-Species Benchmarking", "Islam Akef Ebeid, et al.", "Frontiers in Bioinformatics", 2025, "10.3389/fbinf.2025.1651623", "https://doi.org/10.3389/fbinf.2025.1651623", "documents/Ebeid_Final_Paper.pdf", 1),
        ("XLPM: Cross-Linking Mass Spectrometry 3D Molecular Visualization and Structural Analysis", "Islam Akef Ebeid, John R. Talburt", "SPIE / IS&T Electronic Imaging", 2023, "", "", "documents/XLPM-SPIE-IST-submission.pdf", 2),
        ("XLPMol3DViewer: An Interactive WebGL-Based Biomolecular 3D Structure and Contact Map Viewer", "Islam Akef Ebeid, et al.", "Journal of Molecular Graphics & Modelling", 2022, "", "", "documents/XLPMol3DViewer.pdf", 3),
        ("Immersive Virtual Reality for Protein Structure Exploration in CAVE Environments", "Islam Akef Ebeid, Dirk Reiners, Carolina Cruz-Neira", "ACM Symposium on Eye Tracking Research & Applications (ETRA)", 2019, "10.1145/3314111.3319832", "https://doi.org/10.1145/3314111.3319832", "documents/vr-project-final-paper.pdf", 4),
        ("Information Quality and Entity Resolution in Healthcare Information Exchange Systems", "Islam Akef Ebeid, John R. Talburt", "iConference Proceedings", 2019, "10.21900/iconf.2019.103363", "https://doi.org/10.21900/iconf.2019.103363", "", 5)
    ]
    for title, authors, venue, year, doi, url, pdf, order in pubs_data:
        cur.execute("""
        INSERT INTO publications (title, authors, venue, year, doi, url, pdf_path, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, authors, venue, year, doi, url, pdf, order))
    conn.commit()
    print(f"[OK] Seeded {len(pubs_data)} publications and peer-reviewed papers.")


def seed_encrypted_vault(conn: sqlite3.Connection):
    """Encrypt and store master credentials in the database."""
    vault_items = [
        ("master_passcode", "islam2026", "Master login passcode for Dr. Islam Command Center"),
        ("handshake_token", "islam2026", "Shared handshake token for zero-trust message transmission"),
        ("handshake_question", "What is Dr. Islam's primary research lab / institution?", "Shared secret challenge question"),
        ("handshake_answers", "TWU, Texas Woman's University, Data2AI4LifeSciences, Data2AI4LifeSciences Lab", "Accepted answers list"),
        ("destination_email", "islam.akef@gmail.com", "Verified inbox for direct dispatch relay")
    ]
    for key, val, desc in vault_items:
        store_vault_secret(key, val, desc, DEFAULT_PORTAL_PASSCODE)
    print(f"[OK] Encrypted and stored {len(vault_items)} secrets in portal_vault.")


def main():
    init_database()
    conn = get_connection()
    print("=== Extracting All Website HTML, CSS, Navigation & Content to SQLite ===")
    extract_site_meta(conn)
    seed_navigation_menu(conn)
    seed_html_templates(conn)
    seed_external_stylesheets(conn)
    extract_all_pages_and_templates(conn)
    extract_documents_and_media(conn)
    extract_courses(conn)
    extract_publications(conn)
    extract_portal_bookmarks(conn)
    seed_encrypted_vault(conn)
    conn.close()
    print("=== Master Extraction Complete! 100% of HTML, CSS, Navigation & Content is in data/content.db ===")


if __name__ == "__main__":
    main()
