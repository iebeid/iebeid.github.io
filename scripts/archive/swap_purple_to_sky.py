import re
import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Replace indigo-* -> sky-* in all page_sections
cur.execute("SELECT id, page_slug, section_key, content_html FROM page_sections WHERE content_html LIKE '%indigo-%'")
rows = cur.fetchall()
for row_id, slug, key, html in rows:
    new_html = re.sub(r'\bindigo-(\d+)\b', r'sky-\1', html)
    if new_html != html:
        cur.execute("UPDATE page_sections SET content_html=? WHERE id=?", (new_html, row_id))
        print(f"[OK] Swapped indigo-* -> sky-* in page_sections: {slug}.{key}")

# 2. Update file_pages_media_talk_reveal_css_custom_css
cur.execute("SELECT css_content FROM stylesheets WHERE style_key='file_pages_media_talk_reveal_css_custom_css'")
reveal_css = cur.fetchone()[0]
new_reveal_css = (
    reveal_css
    .replace('--purple-accent: #10b981;', '--purple-accent: #0ea5e9;')
    .replace('rgba(168, 85, 247,', 'rgba(14, 165, 233,')
)
if new_reveal_css != reveal_css:
    cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key='file_pages_media_talk_reveal_css_custom_css'", (new_reveal_css,))
    print("[OK] Swapped rgba(168, 85, 247, ...) -> sky-500 rgba(14, 165, 233, ...) in reveal custom.css")

# 3. Update style_talk_index
cur.execute("SELECT css_content FROM stylesheets WHERE style_key='style_talk_index'")
talk_css = cur.fetchone()[0]
new_talk_css = (
    talk_css
    .replace('#818cf8', '#38bdf8')
    .replace('#6366f1', '#0284c7')
)
if new_talk_css != talk_css:
    cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key='style_talk_index'", (new_talk_css,))
    print("[OK] Swapped #818cf8/#6366f1 -> #38bdf8/#0284c7 in style_talk_index")

conn.commit()
conn.close()

# 4. Update js/portal.js and js/content-loader.js
for js_path in ('js/portal.js', 'js/content-loader.js'):
    with open(js_path, 'r', encoding='utf-8') as f:
        txt = f.read()
    new_txt = re.sub(r'\bindigo-(\d+)\b', r'sky-\1', txt)
    if new_txt != txt:
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(new_txt)
        print(f"[OK] Swapped indigo-* -> sky-* in {js_path}")
