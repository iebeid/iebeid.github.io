#!/usr/bin/env python3
"""
Updates js/portal.js to fix adding new bookmarks, editing bookmarks,
generating semantic tags, and implementing window.refreshAITags.
"""

from pathlib import Path

PORTAL_JS_PATH = Path(__file__).resolve().parent.parent / "js" / "portal.js"

with open(PORTAL_JS_PATH, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Insert generateSemanticTags and update getAllBookmarks
old_get_all_bms = """    function getAllBookmarks() {
        let baseList = [];
        const bmSource = window.PORTAL_BOOKMARKS || window.PORTAL_BOOKMARKS_DATA || (window.__SITE_DATABASE && window.__SITE_DATABASE.portal_bookmarks);
        if (bmSource && Array.isArray(bmSource.bookmarks)) {
            baseList = bmSource.bookmarks;
        }
        const custom = getCustomBookmarks();
        const deletedSet = new Set(getDeletedBookmarkIds());
        
        let combined = [...custom, ...baseList].filter(bm => !deletedSet.has(bm.id));
        
        const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
        combined = combined.map(bm => {
            if (dynamicTags[bm.id]) {
                bm.ai_tags = dynamicTags[bm.id];
            }
            return bm;
        });
        
        return combined;
    }"""

new_get_all_bms = """    function generateSemanticTags(name, domain, subfolder, category) {
        const tokens = new Set();
        const stopwords = new Set([
            'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'was',
            'were', 'will', 'login', 'portal', 'home', 'page', 'site', 'official', 'online',
            'welcome', 'untitled', 'web', 'com', 'org', 'edu', 'gov', 'net', 'io', 'html', 'php'
        ]);

        const d = (domain || '').toLowerCase().replace(/^www\\./, '');
        if (d) {
            tokens.add(d);
            const domainParts = d.split('.').filter(p => !stopwords.has(p) && p.length > 2);
            domainParts.forEach(p => tokens.add(p));

            if (d.includes('github')) {
                ['git', 'code', 'repository', 'developer', 'open-source', 'software'].forEach(t => tokens.add(t));
            } else if (d.includes('twu.edu')) {
                ['twu', 'texas-womans-university', 'faculty', 'courses', 'education', 'academic', 'university'].forEach(t => tokens.add(t));
            } else if (d.includes('canvas') || d.includes('instructure')) {
                ['canvas', 'lms', 'courses', 'teaching', 'assignments', 'grades', 'education'].forEach(t => tokens.add(t));
            } else if (d.includes('nih.gov') || d.includes('ncbi') || d.includes('pubmed')) {
                ['nih', 'ncbi', 'pubmed', 'research', 'biology', 'bioinformatics', 'papers', 'medicine', 'grant'].forEach(t => tokens.add(t));
            } else if (d.includes('nsf.gov') || d.includes('research.gov') || d.includes('fastlane')) {
                ['nsf', 'grants', 'funding', 'proposal', 'research', 'government', 'fastlane'].forEach(t => tokens.add(t));
            } else if (d.includes('overleaf')) {
                ['overleaf', 'latex', 'paper', 'writing', 'manuscript', 'publishing', 'academic'].forEach(t => tokens.add(t));
            } else if (d.includes('arxiv')) {
                ['arxiv', 'preprint', 'research', 'ai', 'machine-learning', 'papers'].forEach(t => tokens.add(t));
            } else if (d.includes('drive.google')) {
                ['drive', 'google-drive', 'docs', 'cloud-storage', 'files'].forEach(t => tokens.add(t));
            } else if (d.includes('mail.google') || d.includes('gmail')) {
                ['gmail', 'email', 'inbox', 'communication', 'mail'].forEach(t => tokens.add(t));
            } else if (d.includes('scholar.google')) {
                ['google-scholar', 'scholar', 'citations', 'papers', 'academic', 'publications'].forEach(t => tokens.add(t));
            } else if (d.includes('zoom')) {
                ['zoom', 'meeting', 'video-call', 'conference'].forEach(t => tokens.add(t));
            } else if (d.includes('youtube')) {
                ['youtube', 'video', 'streaming', 'talks', 'media'].forEach(t => tokens.add(t));
            } else if (d.includes('kaggle')) {
                ['kaggle', 'data-science', 'datasets', 'machine-learning', 'python'].forEach(t => tokens.add(t));
            } else if (d.includes('huggingface')) {
                ['huggingface', 'models', 'transformers', 'nlp', 'ai', 'deep-learning'].forEach(t => tokens.add(t));
            } else if (d.includes('openai') || d.includes('chatgpt')) {
                ['chatgpt', 'openai', 'llm', 'generative-ai', 'ai'].forEach(t => tokens.add(t));
            } else if (d.includes('anthropic') || d.includes('claude')) {
                ['claude', 'anthropic', 'ai-assistant', 'llm'].forEach(t => tokens.add(t));
            } else if (d.includes('gemini')) {
                ['gemini', 'google-ai', 'llm', 'deepmind', 'ai'].forEach(t => tokens.add(t));
            } else if (d.includes('nature') || d.includes('science.org') || d.includes('cell.com')) {
                ['journal', 'peer-review', 'scientific-papers', 'publishing'].forEach(t => tokens.add(t));
            } else if (d.includes('biorxiv') || d.includes('medrxiv')) {
                ['biorxiv', 'medrxiv', 'preprint', 'biology', 'bioinformatics'].forEach(t => tokens.add(t));
            } else if (d.includes('amazon') || d.includes('aws')) {
                ['aws', 'amazon', 'cloud', 'compute'].forEach(t => tokens.add(t));
            } else if (d.includes('microsoft') || d.includes('azure')) {
                ['azure', 'microsoft', 'cloud', 'enterprise'].forEach(t => tokens.add(t));
            } else if (d.includes('stackoverflow')) {
                ['stack-overflow', 'programming', 'code', 'debugging'].forEach(t => tokens.add(t));
            } else if (d.includes('linkedin')) {
                ['linkedin', 'career', 'networking', 'professional'].forEach(t => tokens.add(t));
            }
        }

        if (subfolder && subfolder !== 'General' && subfolder !== d) {
            subfolder.toLowerCase().replace(/[^a-z0-9\\s]/g, ' ').split(/\\s+/).forEach(t => {
                if (t.length > 2 && !stopwords.has(t)) tokens.add(t);
            });
        }

        if (category && category.toLowerCase() !== 'bookmarks') {
            tokens.add(category.toLowerCase());
        }

        const cleanedName = (name || '').toLowerCase().replace(/[^a-z0-9\\s]/g, ' ');
        cleanedName.split(/\\s+/).forEach(w => {
            if (w.length > 2 && !stopwords.has(w) && isNaN(w)) {
                tokens.add(w);
            }
        });

        return Array.from(tokens).join(', ');
    }

    function getAllBookmarks() {
        let baseList = [];
        const bmSource = window.PORTAL_BOOKMARKS || window.PORTAL_BOOKMARKS_DATA || (window.__SITE_DATABASE && window.__SITE_DATABASE.portal_bookmarks);
        if (bmSource && Array.isArray(bmSource.bookmarks)) {
            baseList = bmSource.bookmarks;
        }
        const custom = getCustomBookmarks();
        const deletedSet = new Set(getDeletedBookmarkIds());
        
        let combined = [...custom, ...baseList].filter(bm => !deletedSet.has(bm.id));
        
        const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
        combined = combined.map(bm => {
            if (dynamicTags[bm.id]) {
                bm.ai_tags = dynamicTags[bm.id];
            } else if (!bm.ai_tags) {
                bm.ai_tags = generateSemanticTags(bm.name, bm.domain, bm.subfolder, bm.category);
            }
            return bm;
        });
        
        return combined;
    }"""

if old_get_all_bms.replace("\r\n", "\n") in code.replace("\r\n", "\n"):
    # Normalize CRLF
    code = code.replace("\r\n", "\n")
    code = code.replace(old_get_all_bms.replace("\r\n", "\n"), new_get_all_bms.replace("\r\n", "\n"))
    print("[OK] Replaced getAllBookmarks and added generateSemanticTags")
else:
    print("[WARN] Could not match old_get_all_bms")

# 2. Update editBookmark, openAddBookmarkModal, closeAddBookmarkModal, initAddBookmarkForm, and refreshAITags
old_modal_logic = """    window.editBookmark = function(bmId) {
        const allBms = getAllBookmarks();
        const bm = allBms.find(b => b.id === bmId);
        if (!bm) return;

        document.getElementById('add-modal-title').innerHTML = '<i class="fas fa-bookmark text-sky-400"></i> Edit Bookmark';
        document.getElementById('bm-edit-id').value = bmId;
        document.getElementById('bm-new-name').value = bm.name || '';
        document.getElementById('bm-new-url').value = bm.url || '';
        document.getElementById('bm-new-cat').value = bm.category || 'Bookmarks';
        document.getElementById('bm-new-sub').value = bm.path || '';

        document.getElementById('add-modal').classList.remove('hidden');
    };"""

new_modal_logic = """    window.editBookmark = function(bmId) {
        const allBms = getAllBookmarks();
        const bm = allBms.find(b => b.id === bmId);
        if (!bm) return;

        const modal = document.getElementById('add-bookmark-modal');
        if (!modal) return;

        const titleEl = document.getElementById('add-modal-title');
        if (titleEl) {
            titleEl.innerHTML = '<i class="fas fa-bookmark text-sky-400"></i> Edit Bookmark';
        }

        const editId = document.getElementById('bm-edit-id');
        if (editId) editId.value = bmId;

        const nameEl = document.getElementById('bm-new-name');
        if (nameEl) nameEl.value = bm.name || '';

        const urlEl = document.getElementById('bm-new-url');
        if (urlEl) urlEl.value = bm.url || '';

        const catSelect = document.getElementById('bm-new-cat');
        if (catSelect) {
            catSelect.value = bm.category || 'Bookmarks';
        }

        const subEl = document.getElementById('bm-new-sub');
        if (subEl) subEl.value = bm.subfolder || '';

        const tagsEl = document.getElementById('bm-new-tags');
        if (tagsEl) tagsEl.value = bm.ai_tags || '';

        const pinEl = document.getElementById('bm-new-pin');
        if (pinEl) pinEl.checked = getPinnedIds().includes(bmId);

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (nameEl) nameEl.focus();
    };"""

if old_modal_logic.replace("\r\n", "\n") in code:
    code = code.replace(old_modal_logic.replace("\r\n", "\n"), new_modal_logic.replace("\r\n", "\n"))
    print("[OK] Replaced editBookmark with proper modal ID, fields, and pin check")
else:
    print("[WARN] Could not match old_modal_logic")

old_add_form_logic = """    // -------------------------------------------------------------------------
    // 6. ADD BOOKMARK MODAL & FORM
    // -------------------------------------------------------------------------
    window.openAddBookmarkModal = function (defaultCat) {
        const modal = document.getElementById('add-bookmark-modal');
        if (!modal) return;
        const catSelect = document.getElementById('bm-new-cat');
        if (catSelect && defaultCat) {
            catSelect.value = defaultCat;
        }
        document.getElementById('bm-new-name').value = '';
        document.getElementById('bm-new-url').value = '';
        document.getElementById('bm-new-sub').value = '';
        document.getElementById('bm-new-pin').checked = (defaultCat === 'Dashboard');

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.getElementById('bm-new-name').focus();
    };

    window.closeAddBookmarkModal = function () {
        const modal = document.getElementById('add-bookmark-modal');
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    };

    function initAddBookmarkForm() {
        const form = document.getElementById('add-bookmark-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('bm-new-name').value.trim();
            let url = document.getElementById('bm-new-url').value.trim();
            const category = document.getElementById('bm-new-cat').value;
            let subfolder = document.getElementById('bm-new-sub').value.trim();
            const isPin = document.getElementById('bm-new-pin').checked;

            if (!name || !url) return;
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }

            let domain = 'web';
            try {
                domain = new URL(url).hostname.replace('www.', '');
            } catch (err) {
                domain = url.split('/')[2] || 'web';
            }

            if (!subfolder) {
                subfolder = 'General';
            }

            const newId = Date.now();
            const newBm = {
                id: newId,
                name: name,
                url: url,
                category: category,
                subfolder: subfolder,
                path: `${category} / ${subfolder}`,
                path_parts: [category, subfolder],
                domain: domain,
                isCustom: true
            };

            const custom = getCustomBookmarks();
            custom.unshift(newBm);
            saveCustomBookmarks(custom);

            if (isPin) {
                const pinned = getPinnedIds();
                if (!pinned.includes(newId)) {
                    pinned.unshift(newId);
                    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));
                }
            }

            // Initial seed usage
            const stats = getUsageStats();
            stats[String(newId)] = { count: 1, lastUsed: Date.now() };
            saveUsageStats(stats);

            closeAddBookmarkModal();
            renderAll();
        });
    }"""

new_add_form_logic = """    // -------------------------------------------------------------------------
    // 6. ADD & EDIT BOOKMARK MODAL, FORM & REFRESH TAGS
    // -------------------------------------------------------------------------
    window.openAddBookmarkModal = function (defaultCat) {
        const modal = document.getElementById('add-bookmark-modal');
        if (!modal) return;

        const titleEl = document.getElementById('add-modal-title');
        if (titleEl) {
            titleEl.innerHTML = '<i class="fas fa-plus-circle text-sky-400"></i> Add New Bookmark';
        }

        const editId = document.getElementById('bm-edit-id');
        if (editId) editId.value = '';

        const catSelect = document.getElementById('bm-new-cat');
        if (catSelect) {
            if (defaultCat && Array.from(catSelect.options).some(o => o.value === defaultCat)) {
                catSelect.value = defaultCat;
            } else {
                catSelect.value = 'Bookmarks';
            }
        }

        const nameEl = document.getElementById('bm-new-name');
        if (nameEl) nameEl.value = '';

        const urlEl = document.getElementById('bm-new-url');
        if (urlEl) urlEl.value = '';

        const subEl = document.getElementById('bm-new-sub');
        if (subEl) subEl.value = '';

        const tagsEl = document.getElementById('bm-new-tags');
        if (tagsEl) tagsEl.value = '';

        const pinEl = document.getElementById('bm-new-pin');
        if (pinEl) pinEl.checked = (defaultCat === 'Dashboard');

        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (nameEl) nameEl.focus();
    };

    window.closeAddBookmarkModal = function () {
        const modal = document.getElementById('add-bookmark-modal');
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    };

    window.refreshAITags = async function() {
        const btn = document.getElementById('ai-refresh-btn');
        const originalHTML = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin text-sky-400"></i> Updating Tags...';
            btn.disabled = true;
        }

        try {
            const allBms = getAllBookmarks();
            const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
            let updatedCount = 0;

            for (const bm of allBms) {
                const tags = generateSemanticTags(bm.name, bm.domain, bm.subfolder, bm.category);
                dynamicTags[bm.id] = tags;
                bm.ai_tags = tags;
                updatedCount++;
            }

            localStorage.setItem('portal_ai_tags_cache', JSON.stringify(dynamicTags));

            const custom = getCustomBookmarks();
            let customUpdated = false;
            custom.forEach(b => {
                if (dynamicTags[b.id]) {
                    b.ai_tags = dynamicTags[b.id];
                    customUpdated = true;
                }
            });
            if (customUpdated) {
                saveCustomBookmarks(custom);
            }

            renderAll();
            if (searchQuery && searchQuery.trim()) {
                renderDashboardSearchResults();
            }

            if (btn) {
                btn.innerHTML = `<i class="fas fa-check text-emerald-400"></i> Updated ${updatedCount} Tags!`;
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2500);
            }

        } catch (err) {
            console.error("Failed to update tags:", err);
            if (btn) {
                btn.innerHTML = '<i class="fas fa-exclamation-circle text-rose-400"></i> Update Failed';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2500);
            }
        }
    };

    function initAddBookmarkForm() {
        const form = document.getElementById('add-bookmark-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const editIdVal = document.getElementById('bm-edit-id')?.value;
            const name = document.getElementById('bm-new-name')?.value.trim() || '';
            let url = document.getElementById('bm-new-url')?.value.trim() || '';
            const category = document.getElementById('bm-new-cat')?.value || 'Bookmarks';
            let subfolder = document.getElementById('bm-new-sub')?.value.trim() || 'General';
            const customTags = document.getElementById('bm-new-tags')?.value.trim() || '';
            const pinEl = document.getElementById('bm-new-pin');
            const isPin = pinEl ? pinEl.checked : false;

            if (!name || !url) return;
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }

            let domain = 'web';
            try {
                domain = new URL(url).hostname.replace(/^www\\./, '');
            } catch (err) {
                domain = url.split('/')[2] || 'web';
            }

            const finalTags = customTags || generateSemanticTags(name, domain, subfolder, category);

            if (editIdVal) {
                // EDIT EXISTING BOOKMARK
                const bmId = isNaN(Number(editIdVal)) ? editIdVal : Number(editIdVal);
                const custom = getCustomBookmarks();
                const existingIdx = custom.findIndex(b => b.id === bmId);

                if (existingIdx !== -1) {
                    custom[existingIdx].name = name;
                    custom[existingIdx].url = url;
                    custom[existingIdx].category = category;
                    custom[existingIdx].subfolder = subfolder;
                    custom[existingIdx].path = `${category} / ${subfolder}`;
                    custom[existingIdx].path_parts = [category, subfolder];
                    custom[existingIdx].domain = domain;
                    custom[existingIdx].ai_tags = finalTags;
                    saveCustomBookmarks(custom);
                } else {
                    const overrideBm = {
                        id: bmId,
                        name: name,
                        url: url,
                        category: category,
                        subfolder: subfolder,
                        path: `${category} / ${subfolder}`,
                        path_parts: [category, subfolder],
                        domain: domain,
                        ai_tags: finalTags,
                        isCustom: true
                    };
                    custom.unshift(overrideBm);
                    saveCustomBookmarks(custom);
                }

                const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
                dynamicTags[bmId] = finalTags;
                localStorage.setItem('portal_ai_tags_cache', JSON.stringify(dynamicTags));

                let pinned = getPinnedIds().filter(id => id !== bmId);
                if (isPin) {
                    pinned.unshift(bmId);
                }
                localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));

            } else {
                // ADD NEW BOOKMARK
                const newId = Date.now();
                const newBm = {
                    id: newId,
                    name: name,
                    url: url,
                    category: category,
                    subfolder: subfolder,
                    path: `${category} / ${subfolder}`,
                    path_parts: [category, subfolder],
                    domain: domain,
                    ai_tags: finalTags,
                    isCustom: true
                };

                const custom = getCustomBookmarks();
                custom.unshift(newBm);
                saveCustomBookmarks(custom);

                const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
                dynamicTags[newId] = finalTags;
                localStorage.setItem('portal_ai_tags_cache', JSON.stringify(dynamicTags));

                if (isPin) {
                    const pinned = getPinnedIds();
                    if (!pinned.includes(newId)) {
                        pinned.unshift(newId);
                        localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));
                    }
                }

                const stats = getUsageStats();
                stats[String(newId)] = { count: 1, lastUsed: Date.now() };
                saveUsageStats(stats);
            }

            closeAddBookmarkModal();
            renderAll();
            if (searchQuery && searchQuery.trim()) {
                renderDashboardSearchResults();
            }
        });
    }"""

if old_add_form_logic.replace("\r\n", "\n") in code:
    code = code.replace(old_add_form_logic.replace("\r\n", "\n"), new_add_form_logic.replace("\r\n", "\n"))
    print("[OK] Replaced openAddBookmarkModal, closeAddBookmarkModal, initAddBookmarkForm, and added refreshAITags")
else:
    print("[WARN] Could not match old_add_form_logic")

with open(PORTAL_JS_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("[SUCCESS] js/portal.js successfully updated!")
