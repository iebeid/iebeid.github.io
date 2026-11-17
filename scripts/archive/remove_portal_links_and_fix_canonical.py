import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Remove Portal link from global_footer
cur.execute("SELECT html_content FROM html_templates WHERE template_key='global_footer'")
footer_html = cur.fetchone()[0]
old_portal_footer_part = ' <span class="mx-2 text-gray-500">&bull;</span> <a href="{{PORTAL_HREF}}" class="text-gray-400 hover:text-sky-400 transition underline underline-offset-2" title="Private Executive Portal"><i class="fas fa-lock text-[10px] mr-0.5"></i> Portal</a>'
assert old_portal_footer_part in footer_html, "Portal link not found in global_footer"
new_footer_html = footer_html.replace(old_portal_footer_part, '')
cur.execute("UPDATE html_templates SET html_content=? WHERE template_key='global_footer'", (new_footer_html,))
print("[OK] Removed Portal link from global_footer")

# 2. Remove Portal link from drop.footer
new_drop_footer = """<footer class="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-center">
        <span>&copy; 2026 Dr. Islam Akef Ebeid • Zero-Trust Dead-Drop Protocol</span>
    </div>
</footer>"""
cur.execute(
    "UPDATE page_sections SET content_html=?, content_text=? WHERE page_slug='drop' AND section_key='footer'",
    (new_drop_footer, "© 2026 Dr. Islam Akef Ebeid • Zero-Trust Dead-Drop Protocol")
)
print("[OK] Removed Executive Portal Login link from drop.footer")

# 3. Add canonical link to home and index head_html in pages table
canonical_tag = '<link rel="canonical" href="https://iebeid.github.io/pages/home/home.html" />'
for slug in ('home', 'index'):
    cur.execute("SELECT head_html FROM pages WHERE slug=?", (slug,))
    head_html = cur.fetchone()[0] or ''
    if 'rel="canonical"' not in head_html:
        head_html = canonical_tag + '\n    ' + head_html
        cur.execute("UPDATE pages SET head_html=? WHERE slug=?", (head_html, slug))
        print(f"[OK] Added canonical tag to pages.{slug}.head_html")

conn.commit()
conn.close()
