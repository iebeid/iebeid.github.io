import sqlite3
import re

def update_global_base(cursor):
    new_global_css = '''/* ====================================================================
   Dr. Islam Akef Ebeid - Unified Academic & Professional Color System
   Palette: Dominant Blue/Turquoise + Emerald Green + Refined Gray Typography
   ==================================================================== */

:root {
    /* --- Primary: Dominant Blue & Turquoise Spectrum --- */
    --color-navy: #0f172a;           /* Deep midnight / slate 900 */
    --color-deep-blue: #1e3a8a;      /* Deep sapphire / blue 900 */
    --color-primary-blue: #0284c7;   /* Dominant sky 600 */
    --color-sky-dark: #0369a1;       /* Sky 700 */
    --color-sky-vibrant: #0ea5e9;    /* Sky 500 */
    --color-cyan: #06b6d4;           /* Cyan 500 */
    --color-cyan-dark: #0891b2;      /* Cyan 600 */
    --color-teal: #0d9488;           /* Teal 600 */
    --color-turquoise: #14b8a6;      /* Turquoise / Teal 500 */
    --color-sky-light: #e0f2fe;      /* Sky 100 */
    --color-sky-tint: #f0f9ff;       /* Sky 50 */
    --color-teal-light: #ccfbf1;     /* Teal 100 */
    --color-teal-tint: #f0fdfa;      /* Teal 50 */

    /* --- Secondary: Emerald & Forest Green Spectrum (Scholarship) --- */
    --color-emerald-deep: #064e3b;    /* Emerald 900 */
    --color-emerald-forest: #065f46;  /* Emerald 800 */
    --color-emerald: #059669;         /* Emerald 600 */
    --color-emerald-dark: #047857;    /* Emerald 700 */
    --color-emerald-mint: #10b981;    /* Emerald 500 */
    --color-emerald-sage: #34d399;    /* Emerald 400 */
    --color-emerald-light: #d1fae5;   /* Emerald 100 */
    --color-emerald-tint: #ecfdf5;    /* Emerald 50 */

    /* --- Neutral Gray Typography & Structural Surfaces --- */
    --color-gray-950: #030712;
    --color-gray-900: #111827;       /* Primary Headings */
    --color-gray-800: #1f2937;       /* Section Titles & Strong Text */
    --color-gray-700: #374151;       /* Body Text */
    --color-gray-600: #4b5563;       /* Subtitles & Descriptions */
    --color-gray-500: #6b7280;       /* Metadata & Captions */
    --color-gray-400: #9ca3af;       /* Faint Accents & Dividers */
    --color-gray-200: #e5e7eb;       /* Card Borders */
    --color-gray-100: #f3f4f6;       /* Subsurface Containers */
    --color-gray-50: #f9fafb;        /* Light Surface */
    --color-bg-page: #f8fafc;        /* Canonical Page Background */
    --color-bg-surface: #ffffff;     /* Canonical Card Surface */
}

body, button, input, select, textarea {
    font-family: 'Linux Libertine', 'Linux Libertine O', Georgia, 'Times New Roman', Times, serif;
    color: var(--color-gray-700);
}

h1, h2, h3, h4, h5, h6 {
    color: var(--color-gray-900);
}

/* --- Canonical Tag / Badge System --- */
.tag {
    display: inline-block;
    background-color: var(--color-sky-light);
    color: var(--color-sky-dark);
    border: 1px solid #bae6fd;
    font-size: 0.75rem;
    line-height: 1rem;
    font-weight: 600;
    margin-right: 0.375rem;
    margin-bottom: 0.375rem;
    padding: 0.25rem 0.625rem;
    border-radius: 9999px;
    transition: all 0.2s ease;
}

.tag-emerald {
    background-color: var(--color-emerald-tint);
    color: var(--color-emerald-forest);
    border-color: #a7f3d0;
}

.tag-teal {
    background-color: var(--color-teal-tint);
    color: #0f766e;
    border-color: #99f6e4;
}

.tag-gray {
    background-color: var(--color-gray-100);
    color: var(--color-gray-700);
    border-color: var(--color-gray-200);
}

/* --- Section Title Styling --- */
.section-title {
    font-size: 1.875rem;
    line-height: 2.25rem;
    font-weight: 700;
    color: var(--color-gray-900);
    margin-bottom: 2rem;
    text-align: center;
}

/* --- Navbar Scrolled State --- */
.scrolled {
    background-color: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
}

/* --- Dropdown Menu Transitions --- */
.nav-dropdown-group:hover .nav-dropdown-menu {
    opacity: 1 !important;
    visibility: visible !important;
    transform: translateY(0) !important;
    pointer-events: auto !important;
}

.nav-dropdown-menu {
    opacity: 0;
    visibility: hidden;
    transform: translateY(6px);
    pointer-events: none;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
'''
    cursor.execute("UPDATE stylesheets SET css_content = ? WHERE style_key = 'global_base'", (new_global_css,))
    print("[OK] Updated global_base stylesheet with design tokens")

def update_sections(cursor):
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

    count = 0
    for page_slug, section_key, html in sections:
        if page_slug not in replacements:
            continue
        page_rules = replacements[page_slug]
        rules = []
        if section_key in page_rules:
            rules.extend(page_rules[section_key])
        if '*' in page_rules:
            rules.extend(page_rules['*'])
        
        updated_html = html
        for pat, repl in rules:
            updated_html = re.sub(pat, repl, updated_html)
        
        if updated_html != html:
            cursor.execute(
                "UPDATE page_sections SET content_html = ? WHERE page_slug = ? AND section_key = ?",
                (updated_html, page_slug, section_key)
            )
            count += 1
            print(f"[UPDATED] {page_slug} :: {section_key}")

    print(f"[SUCCESS] Updated {count} sections in SQLite database.")

def main():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    update_global_base(cursor)
    update_sections(cursor)

    conn.commit()
    conn.close()
    print("[ALL DONE] Database modifications committed successfully.")

if __name__ == '__main__':
    main()
