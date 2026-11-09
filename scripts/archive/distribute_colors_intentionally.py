import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    # 1. Update home :: about (Vision card specifically)
    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'home' AND section_key = 'about'")
    home_about_html = cursor.fetchone()[0]

    old_vision = '''<div class="bg-amber-50 p-5 rounded-xl border-l-4 border-amber-600 shadow-sm">
                        <h3 class="text-base font-bold text-amber-900 mb-2 flex items-center">
                            <i class="fas fa-eye mr-2 text-amber-600"></i> Vision'''

    new_vision = '''<div class="bg-emerald-50 p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">
                        <h3 class="text-base font-bold text-emerald-900 mb-2 flex items-center">
                            <i class="fas fa-eye mr-2 text-emerald-600"></i> Vision'''

    if old_vision in home_about_html:
        home_about_html = home_about_html.replace(old_vision, new_vision)
        print("[OK] Replaced Vision card in home::about with exact match")
    else:
        # Regex replacement for Vision card
        home_about_html = re.sub(
            r'<div class="bg-amber-50 p-5 rounded-xl border-l-4 border-amber-600 shadow-sm">\s*<h3 class="text-base font-bold text-amber-900 mb-2 flex items-center">\s*<i class="fas fa-eye mr-2 text-amber-600"></i> Vision',
            '<div class="bg-emerald-50 p-5 rounded-xl border-l-4 border-emerald-600 shadow-sm">\n                        <h3 class="text-base font-bold text-emerald-900 mb-2 flex items-center">\n                            <i class="fas fa-eye mr-2 text-emerald-600"></i> Vision',
            home_about_html
        )
        print("[OK] Replaced Vision card in home::about via regex")

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'home' AND section_key = 'about'", (home_about_html,))

    # 2. General color distribution for remaining sections
    section_rules = {
        ('relations', 'fatherhood'): [
            (r'\btext-amber-700\b', 'text-emerald-700'),
            (r'\btext-amber-800\b', 'text-emerald-800'),
        ],
        ('relations', 'section_5'): [
            (r'\bfrom-rose-50/70\b', 'from-teal-50/70'),
            (r'\btext-rose-800\b', 'text-teal-800'),
            (r'\bhover:text-rose-800\b', 'hover:text-teal-800'),
        ],
        ('relations', 'section_6'): [
            (r'\bhover:border-amber-400\b', 'hover:border-teal-400'),
            (r'\btext-amber-700\b', 'text-teal-700'),
            (r'\bgroup-hover:bg-amber-600\b', 'group-hover:bg-teal-600'),
            (r'\bhover:border-red-400\b', 'hover:border-sky-400'),
            (r'\bhover:bg-red-50/40\b', 'hover:bg-sky-50/40'),
            (r'\bbg-red-100\b', 'bg-sky-100'),
            (r'\btext-red-600\b', 'text-sky-600'),
            (r'\bgroup-hover:bg-red-600\b', 'group-hover:bg-sky-600'),
            (r'\bhover:bg-rose-50/40\b', 'hover:bg-emerald-50/40'),
        ],
        ('relations', 'dead_drop_callout'): [
            (r'\btext-rose-400\b', 'text-emerald-400'),
            (r'\btext-rose-300\b', 'text-emerald-300'),
        ],
        ('research', 'section_1'): [
            (r'\btext-amber-800\b', 'text-emerald-800'),
        ],
        ('research', 'section_2'): [
            (r'\btext-amber-800\b', 'text-sky-800'),
        ],
        ('research', 'section_3'): [
            (r'\btext-amber-800\b', 'text-emerald-800'),
            (r'\btext-amber-700\b', 'text-emerald-700'),
        ],
        ('research', 'section_8'): [
            (r'\btext-pink-800\b', 'text-teal-800'),
        ],
        ('research', 'section_9'): [
            (r'\btext-amber-800\b', 'text-teal-800'),
            (r'\btext-amber-600\b', 'text-teal-600'),
            (r'\btext-amber-700\b', 'text-teal-700'),
            (r'\btext-amber-900\b', 'text-teal-900'),
        ],
        ('teaching', 'projects'): [
            (r'\btext-red-600\b', 'text-sky-600'),
        ],
        ('service', 'campus-leadership'): [
            (r'\bbg-rose-50\b', 'bg-emerald-50'),
            (r'\bbg-rose-50/60\b', 'bg-emerald-50/60'),
            (r'\btext-rose-700\b', 'text-emerald-700'),
            (r'\bborder-rose-200\b', 'border-emerald-200'),
            (r'\bborder-rose-100\b', 'border-emerald-100'),
        ],
        ('service', 'visual-artwork'): [
            (r'\btext-red-500\b', 'text-emerald-600'),
        ],
        ('business', 'section_2'): [
            (r'\btext-rose-700\b', 'text-teal-700'),
            (r'\bbg-rose-50\b', 'bg-teal-50'),
            (r'\btext-amber-800\b', 'text-emerald-800'),
            (r'\btext-rose-600\b', 'text-teal-600'),
        ],
        ('business', 'section_6'): [
            (r'\btext-amber-500\b', 'text-emerald-600'),
            (r'\btext-amber-600\b', 'text-teal-600'),
            (r'\bborder-l-amber-500\b', 'border-l-teal-500'),
        ],
        ('education', 'section_1'): [
            (r'\btext-amber-600\b', 'text-emerald-600'),
            (r'\btext-amber-700\b', 'text-emerald-700'),
        ],
        ('hobbies', 'section_1'): [
            (r'\btext-rose-700\b', 'text-teal-700'),
            (r'\bbg-rose-50\b', 'bg-teal-50'),
            (r'\bborder-rose-200\b', 'border-teal-200'),
            (r'\btext-rose-600\b', 'text-teal-600'),
        ],
        ('hobbies', 'section_2'): [
            (r'\bbg-rose-100\b', 'bg-teal-100'),
            (r'\btext-rose-600\b', 'text-teal-600'),
            (r'\btext-rose-700\b', 'text-teal-700'),
            (r'\bbg-amber-100\b', 'bg-emerald-100'),
            (r'\btext-amber-600\b', 'text-emerald-600'),
        ],
        ('media', 'section_1'): [
            (r'\bbg-amber-100\b', 'bg-teal-100'),
            (r'\btext-amber-800\b', 'text-teal-800'),
        ],
        ('media', 'section_2'): [
            (r'\bborder-amber-500\b', 'border-teal-500'),
        ],
        ('lab', 'about'): [
            (r'\bto-pink-800\b', 'to-slate-900'),
        ],
        ('xlpm', 'header'): [
            (r'\btext-amber-400\b', 'text-emerald-400'),
        ],
        ('xlpm', 'section_1'): [
            (r'\btext-amber-400\b', 'text-emerald-400'),
            (r'\btext-amber-300\b', 'text-emerald-300'),
            (r'\btext-red-400\b', 'text-cyan-400'),
        ],
        ('xlpm', 'section_2'): [
            (r'\bbg-amber-100\b', 'bg-emerald-100'),
            (r'\btext-amber-800\b', 'text-emerald-800'),
            (r'\bbg-rose-100\b', 'bg-teal-100'),
            (r'\btext-rose-800\b', 'text-teal-800'),
        ],
        ('xlpm', 'section_3'): [
            (r'\btext-red-600\b', 'text-emerald-600'),
        ],
        ('xlpm', 'section_4'): [
            (r'\btext-amber-700\b', 'text-teal-700'),
        ]
    }

    updated_count = 0
    for (page_slug, section_key), rules in section_rules.items():
        cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = ? AND section_key = ?", (page_slug, section_key))
        row = cursor.fetchone()
        if not row:
            continue
        html = row[0]
        orig_html = html
        for pat, repl in rules:
            html = re.sub(pat, repl, html)
        if html != orig_html:
            cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = ? AND section_key = ?", (html, page_slug, section_key))
            updated_count += 1
            print(f"[UPDATED] {page_slug} :: {section_key}")

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Intentionally distributed colors across {updated_count} sections in database.")

if __name__ == '__main__':
    main()
