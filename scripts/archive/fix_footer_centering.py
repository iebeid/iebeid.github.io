import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Fix style_relations and style_scholarship (.text-center p was set to text-align: revert -> left-aligned!)
for skey in ('style_relations', 'style_scholarship'):
    cur.execute("SELECT css_content FROM stylesheets WHERE style_key=?", (skey,))
    css = cur.fetchone()[0]
    old_rule = "h1, h2, h3, h4, .text-center p, .text-center {\n            text-align: revert;\n        }"
    new_rule = "h1, h2, h3, h4 {\n            text-align: revert;\n        }\n        .text-center, .text-center p {\n            text-align: center;\n        }"
    if old_rule in css:
        css = css.replace(old_rule, new_rule)
        cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key=?", (css, skey))
        print(f"[OK] Fixed .text-center p alignment in {skey}")
    else:
        print(f"[WARN] old_rule not matched exactly in {skey}")

# 2. Ensure global_footer <p> explicitly has text-center
cur.execute("SELECT html_content FROM html_templates WHERE template_key='global_footer'")
gf = cur.fetchone()[0]
if '<p>&copy;' in gf:
    gf = gf.replace('<p>&copy;', '<p class="text-center">&copy;')
    cur.execute("UPDATE html_templates SET html_content=? WHERE template_key='global_footer'", (gf,))
    print("[OK] Added explicit text-center to global_footer <p>")

# 3. Ensure global_base enforces centered #footer text
cur.execute("SELECT css_content FROM stylesheets WHERE style_key='global_base'")
gb = cur.fetchone()[0]
if '#footer, #footer p' not in gb:
    gb += "\n/* --- Canonical Centered Footer --- */\n#footer, #footer .container, #footer p {\n    text-align: center;\n}\n"
    cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key='global_base'", (gb,))
    print("[OK] Added canonical centered #footer rule to global_base")

# 4. Center xlpm.footer
cur.execute("SELECT content_html FROM page_sections WHERE page_slug='xlpm' AND section_key='footer'")
xlpm_f = cur.fetchone()[0]
old_xlpm = '<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">'
new_xlpm = '<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-center gap-3">'
if old_xlpm in xlpm_f:
    xlpm_f = xlpm_f.replace(old_xlpm, new_xlpm)
    cur.execute("UPDATE page_sections SET content_html=? WHERE page_slug='xlpm' AND section_key='footer'", (xlpm_f,))
    print("[OK] Centered xlpm.footer")

# 5. Center storefront footer in style_storefront
cur.execute("SELECT css_content FROM stylesheets WHERE style_key='style_storefront'")
sf_css = cur.fetchone()[0]
old_sf_footer = """        footer {
            max-width: 1360px;
            margin: 3rem auto 0;
            padding: 2.5rem 2rem 0;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            color: var(--text-muted);
            font-size: 0.85rem;
        }"""
new_sf_footer = """        footer {
            max-width: 1360px;
            margin: 3rem auto 0;
            padding: 2.5rem 2rem 0;
            border-top: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            gap: 0.75rem;
            color: var(--text-muted);
            font-size: 0.85rem;
        }"""
if old_sf_footer in sf_css:
    sf_css = sf_css.replace(old_sf_footer, new_sf_footer)
    cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key='style_storefront'", (sf_css,))
    print("[OK] Centered storefront footer CSS")

conn.commit()
conn.close()
