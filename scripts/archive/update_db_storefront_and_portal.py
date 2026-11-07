#!/usr/bin/env python3
"""
Step 1: Database Updates in data/content.db:
1. Remove top 2 menu bars from storefront body_template_html.
2. Fix Arabic logo CSS in stylesheets (style_storefront and style_business).
3. Insert Remember / Save for Later section above Favorites in portal_app.
4. Hydrate rich email tags for all email accounts in portal_bookmarks.
"""

import sqlite3
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. STOREFRONT: Remove top 2 menu bars from body_template_html
    cur.execute("SELECT body_template_html FROM pages WHERE slug='storefront'")
    row = cur.fetchone()
    if row:
        tmpl = row[0]
        tmpl_clean = tmpl.replace('<div id="global-subpage-nav"></div>\n', '')
        tmpl_clean = tmpl_clean.replace('<div data-db-section="storefront.top_bar"></div>\n', '')
        cur.execute("UPDATE pages SET body_template_html = ? WHERE slug='storefront'", (tmpl_clean,))
        print("[OK] Updated storefront page template: top 2 menu bars removed.")

    # 2. STYLESHEETS: Fix Arabic logo colors matching English
    for style_key in ['style_storefront', 'style_business']:
        cur.execute("SELECT css_content FROM stylesheets WHERE style_key=?", (style_key,))
        s_row = cur.fetchone()
        if s_row:
            css = s_row[0]
            # Remove conflicting generic rule
            css = css.replace('.brand-arabic span {\n            color: #1e3a8a;\n        }', '')
            css = css.replace('.brand-arabic span { color: #1e3a8a; }', '')

            # Add explicit rules for arabic-unity (#4b5563) and arabic-systems (#1e3a8a)
            arabic_rules = """
        .unity-systems-trademark-brand .brand-arabic .arabic-unity,
        .brand-arabic .arabic-unity {
            color: #4b5563 !important;
        }

        .unity-systems-trademark-brand .brand-arabic .arabic-systems,
        .brand-arabic .arabic-systems {
            color: #1e3a8a !important;
        }
"""
            if '.arabic-unity' not in css:
                css += "\n/* Unified Trademark Arabic Logo Colors */" + arabic_rules
            else:
                css = re.sub(r'\.brand-arabic \.arabic-systems\s*\{[^}]*\}', '', css)
                css += "\n/* Unified Trademark Arabic Logo Colors */" + arabic_rules

            cur.execute("UPDATE stylesheets SET css_content = ? WHERE style_key=?", (css, style_key))
            print(f"[OK] Updated {style_key}: Arabic logo colors now match English (#4b5563 for Unity, #1e3a8a for Systems).")

    # 3. PORTAL_APP: Add Remember / Save for Later section above Favorites
    cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
    app_row = cur.fetchone()
    if app_row:
        app_html = app_row[0]
        
        remember_section_html = """<!-- Remember / Save for Later Section -->
<div class="bg-slate-900 p-6 rounded-2xl border border-slate-800/80 shadow-sm mb-6" id="dashboard-remember-section">
<div class="flex items-center justify-between mb-4">
<div class="flex items-center gap-2.5">
<div class="w-9 h-9 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center text-base">
<i class="fas fa-bookmark"></i>
</div>
<div>
<h2 class="serif-heading text-base font-bold text-white flex items-center gap-2">
                                Remember &amp; Save for Later
                                <span class="text-[10px] bg-violet-500/20 text-violet-300 font-semibold px-2 py-0.5 rounded-full border border-violet-500/30" id="remember-count-badge">0 Saved</span>
</h2>
<p class="text-xs text-slate-400 mt-0.5">Bookmarks and reading list items saved to review, research, or inspect later.</p>
</div>
</div>
<div class="flex items-center gap-2">
<button class="text-[11px] text-slate-500 hover:text-rose-400 font-mono transition flex items-center gap-1 hidden" id="clear-remember-btn" onclick="clearAllRemembered()">
<i class="fas fa-trash-alt text-[10px]"></i> Clear All
</button>
</div>
</div>
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" id="dashboard-remember-grid">
<!-- Dynamically populated by renderDashboardRemember() -->
</div>
<div class="py-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl" id="dashboard-remember-empty">
<i class="fas fa-bookmark text-2xl mb-2 text-slate-700"></i>
<p class="text-xs text-slate-400">No bookmarks saved for later yet.</p>
<p class="text-[11px] text-slate-500 mt-0.5">Click the <i class="fas fa-bookmark text-violet-400"></i> bookmark ribbon on any card or search result to pin it here.</p>
</div>
</div>

"""
        if 'id="dashboard-remember-section"' not in app_html:
            target_anchor = '<!-- Top 10 Favorites Section -->'
            if target_anchor in app_html:
                app_html = app_html.replace(target_anchor, remember_section_html + target_anchor)
                cur.execute("UPDATE page_sections SET content_html = ? WHERE page_slug='portal' AND section_key='portal_app'", (app_html,))
                print("[OK] Inserted Remember / Save for Later section above Favorites in portal_app.")
            else:
                print("[WARN] Could not find target anchor in portal_app!")
        else:
            print("[INFO] dashboard-remember-section already present in portal_app.")

    # 4. PORTAL_BOOKMARKS: Hydrate rich email tags for email accounts
    cur.execute("SELECT id, title, url, domain, ai_tags FROM portal_bookmarks")
    all_bms = cur.fetchall()
    updated_email_cnt = 0

    for bm_id, title, url, domain, tags in all_bms:
        name_lower = (title or '').lower()
        url_lower = (url or '').lower()
        tag_list = set(t.strip() for t in (tags or '').split(',') if t.strip())

        is_email = (
            '@' in name_lower or
            'mail.google.com' in url_lower or
            'outlook.live.com' in url_lower or
            'outlook.office.com' in url_lower or
            'mail.yahoo.com' in url_lower or
            'mail.proton.me' in url_lower or
            url_lower.endswith('/inbox') or
            '#inbox' in url_lower
        )

        if is_email:
            email_tags = [
                'email', 'mail', 'inbox', 'webmail', 'account', 'messages', 'communication',
                'email-account', 'inbox-zero', 'correspondence'
            ]
            if 'gmail' in url_lower or 'gmail' in name_lower or 'google' in (domain or ''):
                email_tags.extend(['gmail', 'google-mail', 'google'])
            if 'outlook' in url_lower or 'live.com' in (domain or '') or 'office.com' in (domain or ''):
                email_tags.extend(['outlook', 'microsoft-mail', 'office365'])
            if 'proton' in url_lower or 'proton' in name_lower:
                email_tags.extend(['proton', 'protonmail', 'encrypted-mail'])
            if 'yahoo' in url_lower or 'yahoo' in name_lower:
                email_tags.extend(['yahoo', 'yahoomail'])

            tag_list.update(email_tags)
            new_tags = ', '.join(sorted(tag_list))
            cur.execute("UPDATE portal_bookmarks SET ai_tags = ? WHERE id = ?", (new_tags, bm_id))
            updated_email_cnt += 1

    print(f"[OK] Enriched tags with dedicated email keywords for {updated_email_cnt} email accounts in SQLite.")

    conn.commit()
    conn.close()
    return 0

if __name__ == "__main__":
    exit(main())
