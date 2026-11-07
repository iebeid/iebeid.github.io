#!/usr/bin/env python3
"""
Fixes portal bookmark modal HTML in SQLite content.db,
precomputes and populates rich semantic AI tags for all 415 bookmarks,
and updates the search button in portal_app.
"""

import sqlite3
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"

def generate_tags(name, domain, subfolder, category):
    tokens = set()
    stopwords = {
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'was',
        'were', 'will', 'login', 'portal', 'home', 'page', 'site', 'official', 'online',
        'welcome', 'untitled', 'web', 'com', 'org', 'edu', 'gov', 'net', 'io', 'html', 'php'
    }
    
    d = (domain or '').lower().replace('www.', '')
    if d:
        tokens.add(d)
        parts = [p for p in d.split('.') if p not in stopwords and len(p) > 2]
        for p in parts:
            tokens.add(p)
            
        if 'github' in d:
            tokens.update(['git', 'code', 'repository', 'developer', 'open-source', 'software'])
        elif 'twu.edu' in d:
            tokens.update(['twu', 'texas-womans-university', 'faculty', 'courses', 'education', 'academic', 'university'])
        elif 'canvas' in d or 'instructure' in d:
            tokens.update(['canvas', 'lms', 'courses', 'teaching', 'assignments', 'grades', 'education'])
        elif 'nih.gov' in d or 'ncbi' in d or 'pubmed' in d:
            tokens.update(['nih', 'ncbi', 'pubmed', 'research', 'biology', 'bioinformatics', 'papers', 'medicine', 'grant'])
        elif 'nsf.gov' in d or 'research.gov' in d or 'fastlane' in d:
            tokens.update(['nsf', 'grants', 'funding', 'proposal', 'research', 'government', 'fastlane'])
        elif 'overleaf' in d:
            tokens.update(['overleaf', 'latex', 'paper', 'writing', 'manuscript', 'publishing', 'academic'])
        elif 'arxiv' in d:
            tokens.update(['arxiv', 'preprint', 'research', 'ai', 'machine-learning', 'papers'])
        elif 'google' in d:
            tokens.update(['google', 'cloud'])
        elif 'drive' in d:
            tokens.update(['drive', 'docs', 'storage', 'files', 'cloud'])
        elif 'gmail' in d or 'mail.google' in d:
            tokens.update(['gmail', 'email', 'inbox', 'communication', 'mail'])
        elif 'scholar' in d:
            tokens.update(['scholar', 'citations', 'academic', 'publications', 'research'])
        elif 'zoom' in d:
            tokens.update(['zoom', 'meeting', 'video-call', 'conference'])
        elif 'youtube' in d:
            tokens.update(['youtube', 'video', 'streaming', 'talks', 'media'])
        elif 'kaggle' in d:
            tokens.update(['kaggle', 'data-science', 'datasets', 'machine-learning', 'python'])
        elif 'huggingface' in d:
            tokens.update(['huggingface', 'models', 'transformers', 'nlp', 'ai', 'deep-learning'])
        elif 'openai' in d or 'chatgpt' in d:
            tokens.update(['chatgpt', 'openai', 'llm', 'generative-ai', 'ai'])
        elif 'anthropic' in d or 'claude' in d:
            tokens.update(['claude', 'anthropic', 'ai-assistant', 'llm'])
        elif 'gemini' in d:
            tokens.update(['gemini', 'google-ai', 'llm', 'deepmind', 'ai'])
        elif 'nature' in d or 'science.org' in d or 'cell.com' in d:
            tokens.update(['journal', 'peer-review', 'scientific-papers', 'publishing'])
        elif 'biorxiv' in d or 'medrxiv' in d:
            tokens.update(['biorxiv', 'medrxiv', 'preprint', 'biology', 'bioinformatics'])
        elif 'aws' in d or 'amazon' in d:
            tokens.update(['aws', 'amazon', 'cloud', 'compute'])
        elif 'microsoft' in d or 'azure' in d:
            tokens.update(['azure', 'microsoft', 'cloud', 'enterprise'])
        elif 'stackoverflow' in d:
            tokens.update(['stack-overflow', 'programming', 'code', 'debugging'])
        elif 'linkedin' in d:
            tokens.update(['linkedin', 'career', 'networking', 'professional'])

    # Category / Subfolder tokens
    if subfolder and subfolder != 'General' and subfolder != d:
        cleaned_sub = re.sub(r'[^a-zA-Z0-9\s]', ' ', subfolder).lower()
        for w in cleaned_sub.split():
            if len(w) > 2 and w not in stopwords:
                tokens.add(w)

    if category and category.lower() != 'bookmarks':
        tokens.add(category.lower())

    # Name tokens
    cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', ' ', name or '').lower()
    for w in cleaned_name.split():
        if len(w) > 2 and w not in stopwords and not w.isdigit():
            tokens.add(w)

    return ', '.join(sorted(tokens))

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Update add_bookmark_modal section
    modal_html = """<div class="fixed inset-0 z-50 hidden items-center justify-center bg-black/75 p-4 backdrop-blur-sm" id="add-bookmark-modal">
<div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
<div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
<h3 class="serif-heading text-lg font-bold text-white flex items-center gap-2" id="add-modal-title">
<i class="fas fa-plus-circle text-sky-400"></i> Add New Bookmark
</h3>
<button class="text-slate-400 hover:text-white" onclick="closeAddBookmarkModal()">
<i class="fas fa-times"></i>
</button>
</div>
<form class="space-y-4" id="add-bookmark-form">
<input id="bm-edit-id" type="hidden" value=""/>
<div>
<label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Title / Name *</label>
<input class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none" id="bm-new-name" placeholder="e.g. Canvas LMS, NSF Fastlane, GitHub..." required="" type="text"/>
</div>
<div>
<label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Destination URL *</label>
<input class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none" id="bm-new-url" placeholder="https://..." required="" type="url"/>
</div>
<div class="grid grid-cols-2 gap-3">
<div>
<label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Top Folder *</label>
<select class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none" id="bm-new-cat">
<option value="Dashboard">Dashboard</option>
<option value="Work">Work</option>
<option value="Life">Life</option>
<option value="Tools">Tools</option>
<option value="Bookmarks" selected="">Bookmarks</option>
</select>
</div>
<div>
<label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Subfolder</label>
<input class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none" id="bm-new-sub" placeholder="e.g. Research, Courses, Admin..." type="text"/>
</div>
</div>
<div>
<label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Tags (Comma-Separated for Search)</label>
<input class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none" id="bm-new-tags" placeholder="e.g. nsf, grant, ai, genomics..." type="text"/>
</div>
<div class="flex items-center gap-2 pt-1">
<input class="rounded border-slate-700 bg-slate-800 text-sky-500 focus:ring-sky-500 h-4 w-4" id="bm-new-pin" type="checkbox"/>
<label class="text-xs text-slate-300 cursor-pointer select-none" for="bm-new-pin">Pin to Quick Access / Top Favorites</label>
</div>
<div class="flex justify-end gap-2 pt-4 border-t border-slate-800">
<button class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition" onclick="closeAddBookmarkModal()" type="button">
Cancel
</button>
<button class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1.5" type="submit">
<i class="fas fa-check"></i> Save Bookmark
</button>
</div>
</form>
</div>
</div>"""

    cur.execute("UPDATE page_sections SET content_html = ? WHERE page_slug='portal' AND section_key='add_bookmark_modal'", (modal_html,))
    print("[OK] Updated add_bookmark_modal section with pin checkbox, category options, title id, and tags input.")

    # 2. Update portal_app search button to say "Update Tags"
    cur.execute("SELECT content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
    app_html = cur.fetchone()[0]
    app_html = app_html.replace('title="Refresh AI Tags for new bookmarks"><i class="fas fa-sync-alt"></i> Refresh Tags</button>', 'title="Update AI Tags for all bookmarks"><i class="fas fa-sync-alt"></i> Update Tags</button>')
    cur.execute("UPDATE page_sections SET content_html = ? WHERE page_slug='portal' AND section_key='portal_app'", (app_html,))
    print("[OK] Updated portal_app search button label to 'Update Tags'.")

    # 3. Populate ai_tags across all 415 bookmarks in portal_bookmarks table
    bms = cur.execute("SELECT id, title, url, domain, category, subfolder FROM portal_bookmarks").fetchall()
    updated_tags = 0
    for bm_id, title, url, domain, cat, sub in bms:
        tags = generate_tags(title, domain, sub, cat)
        cur.execute("UPDATE portal_bookmarks SET ai_tags = ? WHERE id = ?", (tags, bm_id))
        updated_tags += 1

    print(f"[OK] Precomputed and populated ai_tags for all {updated_tags} bookmarks in SQLite portal_bookmarks table.")

    conn.commit()
    conn.close()
    return 0

if __name__ == "__main__":
    exit(main())
