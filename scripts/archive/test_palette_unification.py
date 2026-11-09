import sqlite3
import re

def preview_replacements():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    cursor.execute("SELECT page_slug, section_key, content_html FROM page_sections")
    sections = cursor.fetchall()

    replacements = {
        'scholarship': {
            'books': [
                (r'\bamber-50\b', 'teal-50'),
                (r'\bamber-100\b', 'teal-100'),
                (r'\bamber-200\b', 'teal-200'),
                (r'\bamber-300\b', 'teal-300'),
                (r'\bamber-500\b', 'teal-600'),
                (r'\bamber-600\b', 'teal-600'),
                (r'\bamber-700\b', 'teal-700'),
                (r'\bamber-800\b', 'teal-800'),
                (r'\bindigo-50\b', 'emerald-50'),
                (r'\bindigo-100\b', 'emerald-100'),
                (r'\bindigo-200\b', 'emerald-200'),
                (r'\bindigo-600\b', 'emerald-600'),
                (r'\bindigo-700\b', 'emerald-700'),
                (r'\bindigo-800\b', 'emerald-800'),
            ],
            'psychology': [
                (r'\bindigo-50\b', 'sky-50'),
                (r'\bindigo-100\b', 'sky-100'),
                (r'\bindigo-200\b', 'sky-200'),
                (r'\bindigo-600\b', 'sky-600'),
                (r'\bindigo-700\b', 'sky-700'),
                (r'\bindigo-800\b', 'sky-800'),
            ],
            'poetry': [
                (r'\bpurple-50\b', 'emerald-50'),
                (r'\bpurple-100\b', 'emerald-100'),
                (r'\bpurple-200\b', 'emerald-200'),
                (r'\bpurple-600\b', 'emerald-600'),
                (r'\bpurple-700\b', 'emerald-700'),
                (r'\bpurple-800\b', 'emerald-800'),
                (r'\bpurple-900\b', 'emerald-900'),
                (r'\bpurple-950\b', 'emerald-950'),
            ]
        },
        'downloads': {
            '*': [
                (r'\brose-50\b', 'sky-50'),
                (r'\brose-100\b', 'sky-100'),
                (r'\brose-200\b', 'sky-200'),
                (r'\brose-600\b', 'sky-600'),
                (r'\brose-700\b', 'sky-700'),
                (r'\bamber-50\b', 'teal-50'),
                (r'\bamber-100\b', 'teal-100'),
                (r'\bamber-200\b', 'teal-200'),
                (r'\bamber-300\b', 'teal-300'),
                (r'\bamber-500\b', 'teal-600'),
                (r'\bamber-600\b', 'teal-600'),
                (r'\bamber-700\b', 'teal-700'),
                (r'\bamber-800\b', 'teal-800'),
                (r'\bindigo-50\b', 'emerald-50'),
                (r'\bindigo-100\b', 'emerald-100'),
                (r'\bindigo-200\b', 'emerald-200'),
                (r'\bindigo-300\b', 'emerald-300'),
                (r'\bindigo-600\b', 'emerald-600'),
                (r'\bindigo-700\b', 'emerald-700'),
                (r'\bpurple-300\b', 'cyan-300'),
                (r'\bpurple-600\b', 'cyan-600'),
            ]
        },
        'research': {
            '*': [
                (r'\bpurple-50\b', 'slate-50'),
                (r'\bpurple-100\b', 'slate-100'),
                (r'\bpurple-200\b', 'slate-200'),
                (r'\bindigo-50\b', 'sky-50'),
                (r'\bindigo-100\b', 'sky-100'),
                (r'\bindigo-600\b', 'sky-700'),
                (r'\borange-50\b', 'cyan-50'),
                (r'\borange-100\b', 'cyan-100'),
                (r'\borange-500\b', 'cyan-600'),
                (r'\bpink-50\b', 'teal-50'),
                (r'\bpink-100\b', 'teal-100'),
                (r'\bpink-500\b', 'teal-600'),
                (r'\bamber-50\b', 'emerald-50'),
                (r'\bamber-100\b', 'emerald-100'),
                (r'\bamber-200\b', 'emerald-200'),
                (r'\bamber-500\b', 'emerald-600'),
            ]
        },
        'relations': {
            '*': [
                (r'\brose-100\b', 'teal-100'),
                (r'\brose-200\b', 'teal-200'),
                (r'\brose-500\b', 'emerald-500'),
                (r'\brose-600\b', 'emerald-600'),
                (r'\bindigo-600\b', 'sky-700'),
                (r'\bamber-50\b', 'emerald-50'),
                (r'\bamber-100\b', 'emerald-100'),
                (r'\bamber-200\b', 'emerald-200'),
                (r'\bamber-500\b', 'emerald-600'),
                (r'\bpurple-100\b', 'teal-100'),
                (r'\bpurple-200\b', 'teal-200'),
                (r'\bpurple-600\b', 'teal-600'),
            ]
        },
        'teaching': {
            '*': [
                (r'\bindigo-600\b', 'sky-700'),
                (r'\bindigo-900\b', 'teal-950'),
                (r'\bpurple-600\b', 'emerald-600'),
                (r'\borange-500\b', 'teal-600'),
                (r'\bred-500\b', 'sky-600'),
            ]
        },
        'service': {
            '*': [
                (r'\brose-500\b', 'emerald-600'),
                (r'\brose-600\b', 'emerald-600'),
                (r'\bpurple-600\b', 'teal-600'),
                (r'\bindigo-600\b', 'sky-700'),
                (r'\bred-600\b', 'teal-600'),
            ]
        },
        'education': {
            '*': [
                (r'\bindigo-100\b', 'teal-100'),
                (r'\bindigo-500\b', 'sky-600'),
                (r'\bamber-100\b', 'emerald-100'),
            ]
        },
        'business': {
            '*': [
                (r'\brose-100\b', 'teal-100'),
                (r'\brose-200\b', 'teal-200'),
                (r'\bamber-50\b', 'emerald-50'),
                (r'\bamber-100\b', 'emerald-100'),
                (r'\bamber-200\b', 'emerald-200'),
                (r'\bindigo-100\b', 'sky-100'),
            ]
        }
    }

    total_changes = 0
    for page_slug, section_key, html in sections:
        if page_slug not in replacements:
            continue
        page_rules = replacements[page_slug]
        
        # Check specific section rules or '*'
        rules = []
        if section_key in page_rules:
            rules.extend(page_rules[section_key])
        if '*' in page_rules:
            rules.extend(page_rules['*'])
        
        orig_html = html
        for pat, repl in rules:
            html = re.sub(pat, repl, html)
        
        if html != orig_html:
            print(f"[CHANGE] {page_slug} :: {section_key}")
            total_changes += 1

    print(f"\nTotal sections that would be updated: {total_changes}")
    conn.close()

if __name__ == '__main__':
    preview_replacements()
