import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def convert_colors_in_html(content):
    if not content:
        return content

    # 1. Specific talk deck classes and vars
    content = content.replace('badge-purple', 'badge-emerald')
    content = content.replace('highlight-purple', 'highlight-emerald')
    content = content.replace('var(--purple-accent)', 'var(--emerald-accent)')

    # 2. Tailwind violet and fuchsia classes -> emerald
    content = re.sub(r'\bviolet-([0-9]{2,3})\b', r'emerald-\1', content)
    content = re.sub(r'\bfuchsia-([0-9]{2,3})\b', r'emerald-\1', content)

    # 3. Tailwind purple classes -> emerald
    content = re.sub(r'\bpurple-([0-9]{2,3})\b', r'emerald-\1', content)

    # 4. Tailwind orange classes (e.g., text-orange-600, bg-orange-100, border-orange-400, hover:border-orange-400)
    # Be careful to only match class names like text-orange-*, bg-orange-*, border-orange-*, from-orange-*, to-orange-*, etc.
    # or standalone orange-50, orange-100, etc.
    content = re.sub(r'\b(?:(text|bg|border|from|to|via|ring|shadow)-)?orange-([0-9]{2,3})\b', 
                     lambda m: f"{m.group(1) + '-' if m.group(1) else ''}emerald-{m.group(2)}", content)

    return content

def main():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    # 1. Update page_sections
    cursor.execute("SELECT rowid, page_slug, section_key, content_html FROM page_sections")
    sections = cursor.fetchall()

    updated_sections_count = 0
    for rowid, page_slug, section_key, html in sections:
        if not html:
            continue
        new_html = convert_colors_in_html(html)
        if new_html != html:
            cursor.execute("UPDATE page_sections SET content_html = ? WHERE rowid = ?", (new_html, rowid))
            updated_sections_count += 1
            print(f"[UPDATED SECTION] rowid={rowid} ({page_slug} :: {section_key})")

    # 2. Update stylesheets rowid=2
    cursor.execute("SELECT rowid, style_key, css_content FROM stylesheets WHERE rowid = 2")
    row = cursor.fetchone()
    if row:
        rowid, key, css = row
        new_css = css
        if '--purple-accent' in new_css:
            new_css = new_css.replace('--purple-accent: #a855f7;', '--emerald-accent: #10b981;\n    --purple-accent: #10b981;')
            new_css = new_css.replace('.highlight-purple { color: var(--purple-accent); font-weight: 600; }',
                                      '.highlight-purple, .highlight-emerald { color: var(--emerald-accent); font-weight: 600; }')
            new_css = new_css.replace('.badge-purple {', '.badge-purple, .badge-emerald {')
            cursor.execute("UPDATE stylesheets SET css_content = ? WHERE rowid = ?", (new_css, rowid))
            print("[UPDATED STYLESHEET] rowid=2 talk custom CSS with emerald tokens")

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Updated {updated_sections_count} sections in database.")

    # 3. Update js/portal.js
    with open('js/portal.js', 'r', encoding='utf-8') as f:
        portal_js = f.read()

    new_portal_js = re.sub(r'\bviolet-([0-9]{2,3})\b', r'emerald-\1', portal_js)
    if new_portal_js != portal_js:
        with open('js/portal.js', 'w', encoding='utf-8') as f:
            f.write(new_portal_js)
        print("[UPDATED FILE] js/portal.js converted violet classes to emerald")

if __name__ == '__main__':
    main()
