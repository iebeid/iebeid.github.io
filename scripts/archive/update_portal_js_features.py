#!/usr/bin/env python3
"""
Updates js/portal.js with:
1. Remember / Save for Later system (localStorage, toggle, clear, render).
2. Advanced Semantic Search Engine (Email account intent boost, URL query parameter isolation, intent synonyms).
3. Bookmark action buttons for Save for Later across all cards.
"""

from pathlib import Path

PORTAL_JS_PATH = Path(__file__).resolve().parent.parent / "js" / "portal.js"

with open(PORTAL_JS_PATH, "r", encoding="utf-8") as f:
    code = f.read()

# Normalize CRLF to LF for consistent replacement
code = code.replace("\r\n", "\n")

# 1. Add REMEMBER_STORAGE_KEY
target_consts = "const USAGE_STATS_KEY = 'portal_usage_stats';"
replacement_consts = """const USAGE_STATS_KEY = 'portal_usage_stats';
    const REMEMBER_STORAGE_KEY = 'portal_remember_bookmarks';"""

if target_consts in code:
    code = code.replace(target_consts, replacement_consts, 1)
    print("[OK] Added REMEMBER_STORAGE_KEY constant")
else:
    print("[WARN] target_consts not found")

# 2. Add Remember methods & enhance generateSemanticTags
target_gen_tags = "    function generateSemanticTags(name, domain, subfolder, category) {"
remember_logic = """    // -------------------------------------------------------------------------
    // REMEMBER / SAVE FOR LATER ENGINE
    // -------------------------------------------------------------------------
    function getRememberedIds() {
        const stored = localStorage.getItem(REMEMBER_STORAGE_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        return [];
    }

    function saveRememberedIds(ids) {
        localStorage.setItem(REMEMBER_STORAGE_KEY, JSON.stringify(ids));
    }

    function toggleRemember(bmId) {
        let ids = getRememberedIds();
        const numId = Number(bmId);
        const exists = ids.includes(numId);
        if (exists) {
            ids = ids.filter(id => id !== numId);
        } else {
            ids.unshift(numId);
        }
        saveRememberedIds(ids);
        renderDashboardRemember();

        // Update all visible button icons
        document.querySelectorAll(`[data-remember-btn="${numId}"]`).forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                if (!exists) {
                    icon.className = 'fas fa-bookmark text-violet-400';
                    btn.title = 'Remove from Save for Later';
                } else {
                    icon.className = 'far fa-bookmark text-slate-400';
                    btn.title = 'Save for Later';
                }
            }
        });
    }
    window.toggleRemember = toggleRemember;

    function clearAllRemembered() {
        if (confirm("Clear all bookmarks from your 'Save for Later' list?")) {
            saveRememberedIds([]);
            renderDashboardRemember();
            renderAll();
        }
    }
    window.clearAllRemembered = clearAllRemembered;

    function renderDashboardRemember() {
        const grid = document.getElementById('dashboard-remember-grid');
        const empty = document.getElementById('dashboard-remember-empty');
        const badge = document.getElementById('remember-count-badge');
        const clearBtn = document.getElementById('clear-remember-btn');
        if (!grid) return;

        const remIds = getRememberedIds();
        const allBms = getAllBookmarks();
        const bms = remIds.map(id => allBms.find(b => b.id === id)).filter(Boolean);

        if (badge) {
            badge.textContent = `${bms.length} Saved`;
        }

        if (bms.length === 0) {
            grid.innerHTML = '';
            grid.classList.add('hidden');
            if (empty) empty.classList.remove('hidden');
            if (clearBtn) clearBtn.classList.add('hidden');
            return;
        }

        if (empty) empty.classList.add('hidden');
        grid.classList.remove('hidden');
        if (clearBtn) clearBtn.classList.remove('hidden');

        grid.innerHTML = bms.map(bm => {
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            return `
            <div class="group relative bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-violet-500/50 rounded-xl p-3 flex flex-col justify-between transition-all duration-200 shadow-sm">
                <div>
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <div class="flex items-center gap-2 min-w-0">
                            <div class="w-6 h-6 rounded-lg bg-slate-900 border border-slate-700/80 flex items-center justify-center flex-shrink-0 p-1">
                                <img src="${faviconUrl}" alt="" class="w-4 h-4 object-contain rounded" onerror="this.onerror=null;this.src='../../images/favicon.png'"/>
                            </div>
                            <span class="text-[10px] font-mono font-medium text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded truncate max-w-[120px]">${escapeHtml(domain)}</span>
                        </div>
                        <button onclick="toggleRemember(${bm.id})" class="text-slate-500 hover:text-rose-400 text-xs transition p-1" title="Remove from Save for Later">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <h4 class="text-xs font-semibold text-slate-200 group-hover:text-violet-300 transition line-clamp-2 cursor-pointer leading-snug"
                        onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                        title="${escapeHtml(bm.name)}">
                        ${escapeHtml(bm.name)}
                    </h4>
                </div>
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-slate-700/50 text-[11px]">
                    <span class="text-[10px] text-slate-500 truncate max-w-[130px]"><i class="fas fa-folder mr-1 text-slate-600"></i>${escapeHtml(bm.subfolder || bm.category)}</span>
                    <a href="${escapeHtml(bm.url)}" target="_blank" rel="noopener noreferrer" onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                       class="text-violet-400 hover:text-violet-300 font-semibold flex items-center gap-1 transition">
                        <span>Open</span> <i class="fas fa-external-link-alt text-[9px]"></i>
                    </a>
                </div>
            </div>`;
        }).join('');
    }

    function generateSemanticTags(name, domain, subfolder, category) {
        const tokens = new Set();
        const stopwords = new Set([
            'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'was',
            'were', 'will', 'login', 'portal', 'home', 'page', 'site', 'official', 'online',
            'welcome', 'untitled', 'web', 'com', 'org', 'edu', 'gov', 'net', 'io', 'html', 'php'
        ]);

        const rawName = (name || '').toLowerCase();
        const d = (domain || '').toLowerCase().replace(/^www\\./, '');

        // Detect Email Accounts
        if (rawName.includes('@') || d.includes('mail.') || d.includes('outlook') || d.includes('proton') || d.includes('inbox')) {
            ['email', 'mail', 'inbox', 'webmail', 'messages', 'communication', 'account', 'email-account'].forEach(t => tokens.add(t));
        }"""

if target_gen_tags in code:
    code = code.replace(target_gen_tags, remember_logic, 1)
    print("[OK] Inserted Remember engine and updated generateSemanticTags")
else:
    print("[WARN] target_gen_tags not found")

# 3. Update calculateSimilarityAndRelevance with advanced email intent, query param isolation, and semantic synonym expansion
old_calc_sim = """    // Similarity & Relevance Ranking Engine
    function calculateSimilarityAndRelevance(bm, query, usageCount, isPinned) {
        if (!query) return { score: 0, reason: '', matchPct: 0 };

        const q = query.toLowerCase().trim();
        const tokens = q.split(/\\s+/).filter(Boolean);
        const name = (bm.name || '').toLowerCase();
        const domain = (bm.domain || '').toLowerCase();
        const tags = (bm.ai_tags || '').toLowerCase();
        const path = (bm.path || '').toLowerCase();
        const url = (bm.url || '').toLowerCase();

        let score = 0;
        let reasons = [];

        // 1. Exact Title Matches
        if (name === q) {
            score += 1200;
            reasons.push("Exact Title Match");
        } else if (name.startsWith(q)) {
            score += 650;
            reasons.push("Title Prefix");
        } else if (new RegExp(`\\\\b${escapeRegExp(q)}\\\\b`, 'i').test(name)) {
            score += 450;
            reasons.push("Word Boundary Match");
        } else if (name.includes(q)) {
            score += 250;
            reasons.push("Title Match");
        }

        // 2. Domain Matches
        if (domain === q) {
            score += 600;
            reasons.push(`Exact Domain (${domain})`);
        } else if (domain.startsWith(q)) {
            score += 350;
            reasons.push(`Domain Prefix (${domain})`);
        } else if (domain.includes(q)) {
            score += 180;
            reasons.push(`Domain Match (${domain})`);
        }

        // 3. AI Tags Semantic Keyword Matches
        if (tags) {
            const tagList = tags.split(',').map(t => t.trim().toLowerCase());
            const exactTag = tagList.find(t => t === q);
            if (exactTag) {
                score += 380;
                reasons.push(`AI Tag: ${exactTag}`);
            } else {
                const subTag = tagList.find(t => t.includes(q));
                if (subTag) {
                    score += 160;
                    reasons.push(`AI Tag: ${subTag}`);
                }
            }
        }

        // 4. Folder / Path / Category
        if (path.includes(q)) {
            score += 120;
            reasons.push(`Folder: ${bm.subfolder || bm.category}`);
        }

        // 5. URL
        if (url.includes(q)) {
            score += 60;
            if (reasons.length === 0) reasons.push("URL Match");
        }"""

new_calc_sim = """    // Similarity & Relevance Ranking Engine
    function calculateSimilarityAndRelevance(bm, query, usageCount, isPinned) {
        if (!query) return { score: 0, reason: '', matchPct: 0 };

        const q = query.toLowerCase().trim();
        const tokens = q.split(/\\s+/).filter(Boolean);
        const name = (bm.name || '').toLowerCase();
        const domain = (bm.domain || '').toLowerCase();
        const tags = (bm.ai_tags || '').toLowerCase();
        const path = (bm.path || '').toLowerCase();
        const url = (bm.url || '').toLowerCase();
        const cleanUrl = url.split('?')[0].split('#')[0];

        let score = 0;
        let reasons = [];

        // 0. High-Priority Semantic Intent Handling (e.g. "email" -> user's email accounts)
        const isEmailAccount = name.includes('@') ||
            cleanUrl.includes('mail.google.com') ||
            cleanUrl.includes('outlook.live.com') ||
            cleanUrl.includes('outlook.office.com') ||
            cleanUrl.includes('mail.proton.me') ||
            cleanUrl.includes('mail.yahoo.com') ||
            tags.includes('email-account');

        const isEmailQuery = (q === 'email' || q === 'emails' || q === 'mail' || q === 'inbox' || q === 'webmail');

        if (isEmailQuery && isEmailAccount) {
            score += 2500;
            reasons.unshift("Primary Email Account");
        }

        // Expanded Intent Synonym Mapping
        const INTENT_MAP = {
            'email': ['email', 'mail', 'inbox', 'webmail', 'gmail', 'outlook', 'hotmail', 'proton', 'yahoo', 'messages', 'communication'],
            'emails': ['email', 'mail', 'inbox', 'webmail', 'gmail', 'outlook', 'hotmail', 'proton', 'yahoo', 'messages'],
            'mail': ['email', 'mail', 'inbox', 'webmail', 'gmail', 'outlook', 'hotmail', 'proton', 'yahoo'],
            'inbox': ['inbox', 'email', 'mail', 'gmail', 'outlook', 'webmail'],
            'ai': ['ai', 'artificial-intelligence', 'machine-learning', 'ml', 'gnn', 'neural', 'deep-learning', 'transformers', 'nlp'],
            'grant': ['grant', 'grants', 'nsf', 'nih', 'funding', 'proposal', 'awards', 'fastlane', 'research.gov'],
            'grants': ['grant', 'grants', 'nsf', 'nih', 'funding', 'proposal', 'awards', 'fastlane', 'research.gov'],
            'paper': ['paper', 'papers', 'publication', 'publications', 'manuscript', 'journal', 'arxiv', 'pubmed', 'ieee'],
            'papers': ['paper', 'papers', 'publication', 'publications', 'manuscript', 'journal', 'arxiv', 'pubmed', 'ieee'],
            'course': ['course', 'courses', 'teaching', 'class', 'classes', 'syllabus', 'canvas', 'lms', 'student', 'students', 'twu'],
            'courses': ['course', 'courses', 'teaching', 'class', 'classes', 'syllabus', 'canvas', 'lms', 'student', 'students', 'twu'],
            'teaching': ['teaching', 'course', 'courses', 'class', 'syllabus', 'canvas', 'lms', 'student', 'students', 'twu'],
            'code': ['code', 'github', 'git', 'repo', 'repository', 'software', 'programming', 'python']
        };

        if (INTENT_MAP[q]) {
            INTENT_MAP[q].forEach(syn => {
                if (tags.includes(syn) || cleanUrl.includes(syn) || name.includes(syn)) {
                    score += 350;
                    if (!reasons.some(r => r.includes("Semantic Match") || r.includes("Email Account"))) {
                        reasons.push(`Semantic Match: ${syn}`);
                    }
                }
            });
        }

        // 1. Exact Title Matches
        if (name === q) {
            score += 1200;
            reasons.push("Exact Title Match");
        } else if (name.startsWith(q)) {
            score += 650;
            reasons.push("Title Prefix");
        } else if (new RegExp(`\\\\b${escapeRegExp(q)}\\\\b`, 'i').test(name)) {
            score += 450;
            reasons.push("Word Boundary Match");
        } else if (name.includes(q)) {
            score += 250;
            reasons.push("Title Match");
        }

        // 2. Domain Matches
        if (domain === q) {
            score += 600;
            reasons.push(`Exact Domain (${domain})`);
        } else if (domain.startsWith(q)) {
            score += 350;
            reasons.push(`Domain Prefix (${domain})`);
        } else if (domain.includes(q)) {
            score += 180;
            reasons.push(`Domain Match (${domain})`);
        }

        // 3. AI Tags Semantic Keyword Matches
        if (tags) {
            const tagList = tags.split(',').map(t => t.trim().toLowerCase());
            const exactTag = tagList.find(t => t === q);
            if (exactTag) {
                score += 400;
                if (!reasons.some(r => r.includes("AI Tag") || r.includes("Email Account"))) {
                    reasons.push(`AI Tag: ${exactTag}`);
                }
            } else {
                const subTag = tagList.find(t => t.includes(q));
                if (subTag) {
                    score += 180;
                    if (!reasons.some(r => r.includes("AI Tag") || r.includes("Email Account"))) {
                        reasons.push(`AI Tag: ${subTag}`);
                    }
                }
            }
        }

        // 4. Folder / Path / Category
        if (path.includes(q)) {
            score += 120;
            reasons.push(`Folder: ${bm.subfolder || bm.category}`);
        }

        // 5. Clean URL Path vs Query String
        // Isolate query strings so telemetry like ?utm_medium=email or ?email_id= does not hijack search results
        if (cleanUrl.includes(q)) {
            score += 100;
            if (reasons.length === 0) reasons.push("URL Match");
        } else if (url.includes(q)) {
            score += 5; // Minimal weight for query string matches
        }"""

if old_calc_sim in code:
    code = code.replace(old_calc_sim, new_calc_sim, 1)
    print("[OK] Replaced calculateSimilarityAndRelevance with advanced email intent & clean URL scoring")
else:
    print("[WARN] old_calc_sim not found")

# 4. Add Remember toggle button to renderDashboardFavorites cards
old_fav_card_header = """                        <div class="flex items-center justify-between gap-1.5 mb-2">
                            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border ${rankBadgeClass}">
                                #${rank}
                            </span>
                            <span class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                <i class="fas fa-fire text-amber-400 text-[8px]"></i> ${count}
                            </span>
                        </div>"""

new_fav_card_header = """                        <div class="flex items-center justify-between gap-1.5 mb-2">
                            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border ${rankBadgeClass}">
                                #${rank}
                            </span>
                            <div class="flex items-center gap-1">
                                <button onclick="event.stopPropagation(); toggleRemember(${bm.id});" data-remember-btn="${bm.id}"
                                    class="w-5 h-5 rounded hover:bg-slate-700/60 text-slate-400 hover:text-violet-400 flex items-center justify-center transition text-[10px]"
                                    title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}">
                                    <i class="${getRememberedIds().includes(bm.id) ? 'fas text-violet-400' : 'far'} fa-bookmark"></i>
                                </button>
                                <span class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                    <i class="fas fa-fire text-amber-400 text-[8px]"></i> ${count}
                                </span>
                            </div>
                        </div>"""

if old_fav_card_header in code:
    code = code.replace(old_fav_card_header, new_fav_card_header, 1)
    print("[OK] Added remember button to Favorites cards")
else:
    print("[WARN] old_fav_card_header not found")

# 5. Add Remember button and tags preview to renderDashboardSearchResults
old_search_actions = """                        <div class="flex items-center gap-2">
                            <button onclick="togglePin(${bm.id})" class="text-xs ${isPinned ? 'text-amber-400 hover:text-amber-300' : 'text-slate-500 hover:text-slate-300'} transition" title="${isPinned ? 'Unpin' : 'Pin to top'}">
                                <i class="fas fa-star"></i>
                            </button>
                            <button onclick="copyToClipboard('${escapeHtml(bm.url)}', this)" class="text-xs text-slate-500 hover:text-slate-300 transition" title="Copy URL">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>"""

new_search_actions = """                        <div class="flex items-center gap-2">
                            <button onclick="togglePin(${bm.id})" class="text-xs ${isPinned ? 'text-amber-400 hover:text-amber-300' : 'text-slate-500 hover:text-slate-300'} transition" title="${isPinned ? 'Unpin' : 'Pin to top'}">
                                <i class="fas fa-star"></i>
                            </button>
                            <button onclick="toggleRemember(${bm.id})" data-remember-btn="${bm.id}" class="text-xs ${getRememberedIds().includes(bm.id) ? 'text-violet-400 hover:text-violet-300' : 'text-slate-500 hover:text-violet-400'} transition" title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}">
                                <i class="${getRememberedIds().includes(bm.id) ? 'fas' : 'far'} fa-bookmark"></i>
                            </button>
                            <button onclick="copyToClipboard('${escapeHtml(bm.url)}', this)" class="text-xs text-slate-500 hover:text-slate-300 transition" title="Copy URL">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>"""

if old_search_actions in code:
    code = code.replace(old_search_actions, new_search_actions, 1)
    print("[OK] Added remember button to Search Result cards")
else:
    print("[WARN] old_search_actions not found")

# Add tags preview to search results cards if not already present
old_path_preview = "${bm.path && bm.path !== 'General' ? `<p class=\"text-[10px] text-slate-500 font-mono truncate\"><i class=\"fas fa-folder-open mr-1\"></i>${escapeHtml(bm.path)}</p>` : ''}"
new_path_preview = """${bm.path && bm.path !== 'General' ? `<p class="text-[10px] text-slate-500 font-mono truncate"><i class="fas fa-folder-open mr-1"></i>${escapeHtml(bm.path)}</p>` : ''}
                        ${bm.ai_tags ? `<p class="text-[10px] text-slate-500 font-mono truncate mt-1" title="Tags: ${escapeHtml(bm.ai_tags)}"><i class="fas fa-tags mr-1 text-slate-600"></i>${escapeHtml(bm.ai_tags.split(',').slice(0, 5).join(', '))}</p>` : ''}"""

if old_path_preview in code:
    code = code.replace(old_path_preview, new_path_preview, 1)
    print("[OK] Added tags snippet preview to search cards")
else:
    print("[WARN] old_path_preview not found")

# 6. Add Remember button to renderBookmarks cards
old_bms_pin_btn = """                                <button onclick="togglePin(${bm.id})" title="${isPinned ? 'Unpin' : 'Pin to Launchpad'}"
                                    class="text-xs transition ml-1 ${isPinned ? 'text-amber-400' : 'text-slate-600 hover:text-amber-400'}">
                                    <i class="${isPinned ? 'fas' : 'far'} fa-star"></i>
                                </button>"""

new_bms_pin_btn = """                                <button onclick="togglePin(${bm.id})" title="${isPinned ? 'Unpin' : 'Pin to Launchpad'}"
                                    class="text-xs transition ml-1 ${isPinned ? 'text-amber-400' : 'text-slate-600 hover:text-amber-400'}">
                                    <i class="${isPinned ? 'fas' : 'far'} fa-star"></i>
                                </button>
                                <button onclick="toggleRemember(${bm.id})" title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}"
                                    data-remember-btn="${bm.id}"
                                    class="text-xs transition ml-1 ${getRememberedIds().includes(bm.id) ? 'text-violet-400' : 'text-slate-600 hover:text-violet-400'}">
                                    <i class="${getRememberedIds().includes(bm.id) ? 'fas' : 'far'} fa-bookmark"></i>
                                </button>"""

if old_bms_pin_btn in code:
    code = code.replace(old_bms_pin_btn, new_bms_pin_btn, 1)
    print("[OK] Added remember button to Bookmarks Directory cards")
else:
    print("[WARN] old_bms_pin_btn not found")

# 7. Update renderAll to call renderDashboardRemember()
old_render_all = """    function renderAll() {
        renderDashboardFavorites();"""

new_render_all = """    function renderAll() {
        renderDashboardRemember();
        renderDashboardFavorites();"""

if old_render_all in code:
    code = code.replace(old_render_all, new_render_all, 1)
    print("[OK] Added renderDashboardRemember() to renderAll()")
else:
    print("[WARN] old_render_all not found")

with open(PORTAL_JS_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("[SUCCESS] js/portal.js successfully updated with Remember engine & semantic search!")
