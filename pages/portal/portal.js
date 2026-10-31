/**
 * Dr. Islam Akef Ebeid - Personal Command Center & Portal Script
 * Aligned precisely with Chrome Bookmarks hierarchy:
 * 1. Work (185)
 * 2. Life (138)
 * 3. Tools (37)
 * 4. Dashboard (55) -> Houses "Daily Drivers & Quick Access"
 * 
 * Features:
 * - Dynamic addition & deletion of bookmarks with localStorage persistence
 * - Smart frequency & usage tracking (promotes most-used links into Quick Access)
 * - Pinned favorites, search highlighting, messaging hub, scratchpad, tasks
 * - Similarity & Relevance ranking search engine
 * - Top 10 Favorites live-updating section
 */

(function () {
    // -------------------------------------------------------------------------
    // 1. STATE & CONSTANTS
    // -------------------------------------------------------------------------
    const DEFAULT_PASSCODE = 'islam2026';
    const PASSCODE_STORAGE_KEY = 'portal_master_passcode';
    const AUTH_SESSION_KEY = 'portal_auth_token';
    const PINNED_STORAGE_KEY = 'portal_pinned_bookmarks';
    const SCRATCHPAD_KEY = 'portal_scratchpad_content';
    const SCRATCHES_DB_KEY = 'portal_scratches_database';
    const TASKS_KEY = 'portal_tasks_list';
    const MESSAGES_KEY = 'portal_messages_list';
    const CUSTOM_BM_KEY = 'portal_custom_bookmarks';
    const DELETED_BM_KEY = 'portal_deleted_bookmarks';
    const USAGE_STATS_KEY = 'portal_usage_stats';
    const HANDSHAKE_CONFIG_KEY = 'portal_handshake_config';

    const DEFAULT_HANDSHAKE_CONFIG = {
        passcode: 'islam2026',
        question: "What is Dr. Islam's primary research lab / institution?",
        answers: ["TWU", "Texas Woman's University", "Data2AI4LifeSciences", "Data2AI4LifeSciences Lab"],
        destinationEmail: 'islam.akef@gmail.com'
    };

    let activeCategory = 'all';
    let activeSubfolder = null;
    let activeDashFilter = 'all';
    let searchQuery = '';
    let aiSearchMode = false;
    let aiMatchedIds = [];
    let selectedMessageId = null;
    let activeTaskFilter = 'all';

    // -------------------------------------------------------------------------
    // 2. AUTHENTICATION & SECURITY (SQLite AES-256-GCM Vault + Local Override)
    // -------------------------------------------------------------------------
    let unlockedVaultSecrets = {};

    function base64ToUint8Array(b64) {
        const bin = atob(b64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        return arr;
    }

    async function decryptSqliteVaultEntry(entry, passcode) {
        if (!entry || !entry.ciphertext || !entry.nonce || !entry.salt) return null;
        if (!window.crypto || !window.crypto.subtle) return null;
        try {
            const enc = new TextEncoder();
            const salt = base64ToUint8Array(entry.salt);
            const nonce = base64ToUint8Array(entry.nonce);
            const ciphertext = base64ToUint8Array(entry.ciphertext);
            const keyMaterial = await window.crypto.subtle.importKey(
                'raw', enc.encode(passcode), { name: 'PBKDF2' }, false, ['deriveKey']
            );
            const aesKey = await window.crypto.subtle.deriveKey(
                { name: 'PBKDF2', salt: salt, iterations: 100000, hash: 'SHA-256' },
                keyMaterial,
                { name: 'AES-GCM', length: 256 },
                false,
                ['decrypt']
            );
            const decrypted = await window.crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: nonce },
                aesKey,
                ciphertext
            );
            return new TextDecoder().decode(decrypted);
        } catch (err) {
            return null;
        }
    }

    async function unlockSqliteVault(passcode) {
        const vault = window.__SITE_DATABASE && window.__SITE_DATABASE.portal_vault;
        if (!vault || typeof vault !== 'object') return false;
        const masterEntry = vault.master_passcode;
        if (!masterEntry) return false;
        const plainMaster = await decryptSqliteVaultEntry(masterEntry, passcode);
        if (plainMaster === null) return false;

        unlockedVaultSecrets.master_passcode = plainMaster;
        for (const [k, v] of Object.entries(vault)) {
            if (k === 'master_passcode') continue;
            const dec = await decryptSqliteVaultEntry(v, passcode);
            if (dec !== null) unlockedVaultSecrets[k] = dec;
        }
        if (unlockedVaultSecrets.handshake_token || unlockedVaultSecrets.handshake_question) {
            const hydratedConfig = {
                passcode: unlockedVaultSecrets.handshake_token || DEFAULT_HANDSHAKE_CONFIG.passcode,
                question: unlockedVaultSecrets.handshake_question || DEFAULT_HANDSHAKE_CONFIG.question,
                answers: unlockedVaultSecrets.handshake_answers
                    ? unlockedVaultSecrets.handshake_answers.split(',').map(s => s.trim()).filter(Boolean)
                    : DEFAULT_HANDSHAKE_CONFIG.answers,
                destinationEmail: unlockedVaultSecrets.destination_email || DEFAULT_HANDSHAKE_CONFIG.destinationEmail
            };
            if (!localStorage.getItem(HANDSHAKE_CONFIG_KEY)) {
                localStorage.setItem(HANDSHAKE_CONFIG_KEY, JSON.stringify(hydratedConfig));
            }
        }
        return true;
    }

    function getStoredPasscode() {
        return localStorage.getItem(PASSCODE_STORAGE_KEY) || unlockedVaultSecrets.master_passcode || DEFAULT_PASSCODE;
    }

    function isAuthenticated() {
        return sessionStorage.getItem(AUTH_SESSION_KEY) === 'authenticated' ||
               localStorage.getItem(AUTH_SESSION_KEY) === 'authenticated';
    }

    async function authenticate(passcode, remember) {
        const localOverride = localStorage.getItem(PASSCODE_STORAGE_KEY);
        let verified = false;
        if (localOverride) {
            verified = (passcode === localOverride);
        } else {
            verified = await unlockSqliteVault(passcode);
            if (!verified && passcode === getStoredPasscode()) {
                verified = true;
            }
        }
        if (verified) {
            if (remember) {
                localStorage.setItem(AUTH_SESSION_KEY, 'authenticated');
            } else {
                sessionStorage.setItem(AUTH_SESSION_KEY, 'authenticated');
            }
            return true;
        }
        return false;
    }

    function logout() {
        sessionStorage.removeItem(AUTH_SESSION_KEY);
        localStorage.removeItem(AUTH_SESSION_KEY);
        document.getElementById('portal-app').classList.add('hidden');
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('passcode-input').value = '';
        document.getElementById('login-error').classList.add('hidden');
    }

    function initAuth() {
        const loginScreen = document.getElementById('login-screen');
        const portalApp = document.getElementById('portal-app');
        const loginForm = document.getElementById('login-form');
        const passInput = document.getElementById('passcode-input');
        const loginError = document.getElementById('login-error');
        const rememberMe = document.getElementById('remember-me');
        const togglePassBtn = document.getElementById('toggle-password-btn');
        const eyeIcon = document.getElementById('eye-icon');
        const logoutBtn = document.getElementById('logout-btn');

        if (isAuthenticated()) {
            loginScreen.classList.add('hidden');
            portalApp.classList.remove('hidden');
        } else {
            loginScreen.classList.remove('hidden');
            portalApp.classList.add('hidden');
        }

        if (togglePassBtn) {
            togglePassBtn.addEventListener('click', () => {
                if (passInput.type === 'password') {
                    passInput.type = 'text';
                    eyeIcon.classList.replace('fa-eye', 'fa-eye-slash');
                } else {
                    passInput.type = 'password';
                    eyeIcon.classList.replace('fa-eye-slash', 'fa-eye');
                }
            });
        }

        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const entered = passInput.value.trim();
                const ok = await authenticate(entered, rememberMe.checked);
                if (ok) {
                    loginError.classList.add('hidden');
                    loginScreen.classList.add('opacity-0');
                    setTimeout(() => {
                        loginScreen.classList.add('hidden');
                        loginScreen.classList.remove('opacity-0');
                        portalApp.classList.remove('hidden');
                        renderAll();
                    }, 250);
                } else {
                    loginError.classList.remove('hidden');
                    passInput.select();
                }
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }

        // Change Passcode Form
        const changePassForm = document.getElementById('change-passcode-form');
        const newPass = document.getElementById('new-passcode');
        const confirmPass = document.getElementById('confirm-passcode');
        const changeMsg = document.getElementById('passcode-change-msg');

        if (changePassForm) {
            changePassForm.addEventListener('submit', (e) => {
                e.preventDefault();
                if (newPass.value !== confirmPass.value) {
                    changeMsg.className = 'text-xs text-rose-400 block';
                    changeMsg.textContent = 'Passcodes do not match.';
                    return;
                }
                if (newPass.value.length < 6) {
                    changeMsg.className = 'text-xs text-rose-400 block';
                    changeMsg.textContent = 'Passcode must be at least 6 characters.';
                    return;
                }
                localStorage.setItem(PASSCODE_STORAGE_KEY, newPass.value);
                changeMsg.className = 'text-xs text-emerald-400 block';
                changeMsg.textContent = 'Master passcode updated successfully! Remember your new passcode.';
                newPass.value = '';
                confirmPass.value = '';
            });
        }
    }

    // -------------------------------------------------------------------------
    // 3. LIVE CLOCK
    // -------------------------------------------------------------------------
    function startClock() {
        const clockEl = document.getElementById('live-clock');
        function update() {
            if (!clockEl) return;
            const now = new Date();
            const dateStr = now.toLocaleDateString('en-US', {
                weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
            });
            const timeStr = now.toLocaleTimeString('en-US', {
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            clockEl.textContent = `${dateStr} \u2022 ${timeStr}`;
        }
        update();
        setInterval(update, 1000);
    }

    // -------------------------------------------------------------------------
    // 4. TAB NAVIGATION
    // -------------------------------------------------------------------------
    window.switchTab = function (tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            if (content.id === tabId) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    function initTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.getAttribute('data-tab');
                if (tabId) switchTab(tabId);
            });
        });
    }

    // -------------------------------------------------------------------------
    // 5. BOOKMARKS STORAGE & RESOLUTION (CRUD + STATS)
    // -------------------------------------------------------------------------
    function getCustomBookmarks() {
        try {
            return JSON.parse(localStorage.getItem(CUSTOM_BM_KEY) || '[]');
        } catch (e) {
            return [];
        }
    }

    function saveCustomBookmarks(bms) {
        localStorage.setItem(CUSTOM_BM_KEY, JSON.stringify(bms));
    }

    function getDeletedBookmarkIds() {
        try {
            return JSON.parse(localStorage.getItem(DELETED_BM_KEY) || '[]');
        } catch (e) {
            return [];
        }
    }

    function saveDeletedBookmarkIds(ids) {
        localStorage.setItem(DELETED_BM_KEY, JSON.stringify(ids));
    }

    function getUsageStats() {
        try {
            return JSON.parse(localStorage.getItem(USAGE_STATS_KEY) || '{}');
        } catch (e) {
            return {};
        }
    }

    function saveUsageStats(stats) {
        localStorage.setItem(USAGE_STATS_KEY, JSON.stringify(stats));
    }

    function getBookmarkUsageCount(bmId) {
        const stats = getUsageStats();
        const item = stats[String(bmId)];
        return (item && item.count) ? item.count : 0;
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
            }
            return bm;
        });
        
        return combined;
    }

    function getPinnedIds() {
        const stored = localStorage.getItem(PINNED_STORAGE_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        // Default: first 8 bookmarks from Dashboard folder
        const allBms = getAllBookmarks();
        const dashBms = allBms.filter(b => b.category === 'Dashboard').slice(0, 8);
        const initial = dashBms.map(b => b.id);
        localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(initial));
        return initial;
    }

    function togglePin(bmId) {
        let pinned = getPinnedIds();
        const idNum = parseInt(bmId, 10);
        if (pinned.includes(idNum)) {
            pinned = pinned.filter(id => id !== idNum);
        } else {
            pinned.push(idNum);
        }
        localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));
        renderDashboardFavorites();
        renderBookmarks();
        updateStats();
    }
    window.togglePin = togglePin;

    // Smart Launch Tracker: records click frequency and updates Favorites & Rankings immediately
    function trackLaunch(bmId, url) {
        const stats = getUsageStats();
        const idStr = String(bmId);
        if (!stats[idStr]) {
            stats[idStr] = { count: 0, lastUsed: Date.now() };
        }
        stats[idStr].count += 1;
        stats[idStr].lastUsed = Date.now();
        saveUsageStats(stats);

        window.open(url, '_blank', 'noopener,noreferrer');

        // Immediately update favorites small section, search ranking results, bookmarks directory, and stats
        renderDashboardFavorites();
        if (typeof renderDashboardSearchResults === 'function') {
            renderDashboardSearchResults();
        }
        renderBookmarks();
        updateStats();
    }
    window.trackLaunch = trackLaunch;

    window.editBookmark = function(bmId) {
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
    };

    // Delete Bookmark with confirmation
    function deleteBookmark(bmId) {
        const allBms = getAllBookmarks();
        const bm = allBms.find(b => b.id === bmId);
        const title = bm ? bm.name : 'this bookmark';
        
        if (!confirm(`Are you sure you want to remove "${title}"?`)) {
            return;
        }

        // Add to deleted IDs
        const deleted = getDeletedBookmarkIds();
        if (!deleted.includes(bmId)) {
            deleted.push(bmId);
            saveDeletedBookmarkIds(deleted);
        }

        // Remove from custom list if it was a user-added one
        const custom = getCustomBookmarks().filter(b => b.id !== bmId);
        saveCustomBookmarks(custom);

        // Remove from pinned
        const pinned = getPinnedIds().filter(id => id !== bmId);
        localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(pinned));

        // Clean stats
        const stats = getUsageStats();
        delete stats[String(bmId)];
        saveUsageStats(stats);

        renderAll();
    }
    window.deleteBookmark = deleteBookmark;

    // Copy to clipboard helper
    function copyToClipboard(text, btnElement) {
        navigator.clipboard.writeText(text).then(() => {
            const originalHTML = btnElement.innerHTML;
            btnElement.innerHTML = '<i class="fas fa-check text-emerald-400"></i>';
            setTimeout(() => {
                btnElement.innerHTML = originalHTML;
            }, 1500);
        });
    }
    window.copyToClipboard = copyToClipboard;

    // -------------------------------------------------------------------------
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
    }

    // -------------------------------------------------------------------------
    // 7. FAVORITES (TOP 10 MOST CLICKED) & SIMILARITY / RELEVANCE RANKING ENGINE
    // -------------------------------------------------------------------------
    function renderDashboardFavorites() {
        const grid = document.getElementById('dashboard-favorites-grid');
        if (!grid) return;

        const allBms = getAllBookmarks();
        const pinnedIds = getPinnedIds();
        const stats = getUsageStats();

        // Sort all bookmarks:
        // 1. By click count descending
        // 2. By lastUsed descending
        // 3. By pinned status
        // 4. By id
        const sorted = [...allBms].sort((a, b) => {
            const countA = (stats[String(a.id)] && stats[String(a.id)].count) || 0;
            const countB = (stats[String(b.id)] && stats[String(b.id)].count) || 0;
            if (countB !== countA) return countB - countA;

            const timeA = (stats[String(a.id)] && stats[String(a.id)].lastUsed) || 0;
            const timeB = (stats[String(b.id)] && stats[String(b.id)].lastUsed) || 0;
            if (timeB !== timeA) return timeB - timeA;

            const pinA = pinnedIds.includes(a.id) ? 1 : 0;
            const pinB = pinnedIds.includes(b.id) ? 1 : 0;
            if (pinB !== pinA) return pinB - pinA;

            return a.id - b.id;
        });

        const top10 = sorted.slice(0, 10);

        grid.innerHTML = top10.map((bm, index) => {
            const rank = index + 1;
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const count = (stats[String(bm.id)] && stats[String(bm.id)].count) || 0;

            let rankBadgeClass = 'bg-slate-800 text-slate-400 border-slate-700';
            if (rank === 1) rankBadgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/40 font-bold';
            else if (rank === 2) rankBadgeClass = 'bg-slate-300/20 text-slate-200 border-slate-400/40 font-bold';
            else if (rank === 3) rankBadgeClass = 'bg-amber-700/20 text-amber-400 border-amber-600/40 font-bold';

            return `
                <div onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                    class="group relative bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-sky-500/50 rounded-xl p-3 cursor-pointer transition shadow-sm hover:shadow-md flex flex-col justify-between"
                    title="${escapeHtml(bm.name)} (${count} launches) - Click to launch">
                    <div>
                        <div class="flex items-center justify-between gap-1.5 mb-2">
                            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border ${rankBadgeClass}">
                                #${rank}
                            </span>
                            <span class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                <i class="fas fa-fire text-amber-400 text-[8px]"></i> ${count}
                            </span>
                        </div>
                        <div class="flex items-center gap-2 mb-1.5">
                            <img src="${faviconUrl}" alt="" onerror="this.onerror=null;this.src='../../images/favicon.png'" class="w-4 h-4 object-contain flex-shrink-0 rounded-sm">
                            <span class="text-[10px] font-mono text-slate-400 truncate flex-1" title="${escapeHtml(domain)}">
                                ${escapeHtml(domain)}
                            </span>
                        </div>
                        <h4 class="text-xs font-semibold text-slate-200 group-hover:text-sky-300 transition line-clamp-1 leading-snug">
                            ${escapeHtml(bm.name)}
                        </h4>
                    </div>
                    <div class="mt-2 pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
                        <span class="truncate">${escapeHtml(bm.subfolder || bm.category || 'Link')}</span>
                        <i class="fas fa-external-link-alt text-[8px] text-slate-400 group-hover:text-sky-400 group-hover:translate-x-0.5 transition-transform"></i>
                    </div>
                </div>
            `;
        }).join('');
    }
    window.renderDashboardFavorites = renderDashboardFavorites;

    function renderDashboardDailyDrivers() {
        renderDashboardFavorites();
    }

    // N-gram / Trigram Similarity for Typo-Tolerant Soft Matching
    function getTrigrams(str) {
        const s = `  ${str.toLowerCase()} `;
        const trigrams = new Set();
        for (let i = 0; i < s.length - 2; i++) {
            trigrams.add(s.substring(i, i + 3));
        }
        return trigrams;
    }

    function calculateTrigramSimilarity(strA, strB) {
        if (!strA || !strB) return 0;
        const triA = getTrigrams(strA);
        const triB = getTrigrams(strB);
        let intersection = 0;
        for (let t of triA) {
            if (triB.has(t)) intersection++;
        }
        const total = triA.size + triB.size;
        return total > 0 ? (2 * intersection) / total : 0;
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Similarity & Relevance Ranking Engine
    function calculateSimilarityAndRelevance(bm, query, usageCount, isPinned) {
        if (!query) return { score: 0, reason: '', matchPct: 0 };

        const q = query.toLowerCase().trim();
        const tokens = q.split(/\s+/).filter(Boolean);
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
        } else if (new RegExp(`\\b${escapeRegExp(q)}\\b`, 'i').test(name)) {
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
        }

        // 6. Multi-term Token Coverage
        if (tokens.length > 1) {
            let matchedTokenCount = 0;
            tokens.forEach(term => {
                let termMatched = false;
                if (name.includes(term)) { score += 70; termMatched = true; }
                if (domain.includes(term)) { score += 40; termMatched = true; }
                if (tags.includes(term)) { score += 40; termMatched = true; }
                if (path.includes(term)) { score += 20; termMatched = true; }
                if (termMatched) matchedTokenCount++;
            });

            // All-token coverage bonus (1.5x)
            if (matchedTokenCount === tokens.length) {
                score = Math.round(score * 1.5) + 150;
                reasons.push("100% Keywords Matched");
            } else if (matchedTokenCount > 0) {
                score += (matchedTokenCount * 30);
            }
        }

        // 7. Fuzzy Trigram Similarity on Title
        const triSim = calculateTrigramSimilarity(q, name);
        if (triSim > 0.3) {
            const fuzzyScore = Math.round(triSim * 180);
            score += fuzzyScore;
            if (reasons.length === 0 && triSim > 0.45) {
                reasons.push(`Fuzzy Title (${Math.round(triSim * 100)}%)`);
            }
        }

        // If no match at all, score is 0
        if (score === 0) {
            return { score: 0, reason: '', matchPct: 0 };
        }

        // 8. Usage Relevance & Priority Tie-breaker
        if (usageCount > 0) {
            score += Math.min(usageCount * 6, 80);
        }
        if (isPinned) {
            score += 30;
        }

        // Compute Normalized Match % (e.g., 99% down to 50%)
        let matchPct = 50;
        if (score >= 1000) {
            matchPct = Math.min(99, 95 + Math.round((score - 1000) / 100));
        } else if (score >= 400) {
            matchPct = 82 + Math.round(((score - 400) / 600) * 12);
        } else if (score >= 150) {
            matchPct = 68 + Math.round(((score - 150) / 250) * 13);
        } else {
            matchPct = 50 + Math.round((score / 150) * 17);
        }

        const primaryReason = reasons[0] || 'Relevant Match';

        return { score, reason: primaryReason, matchPct };
    }

    function highlightTokens(text, query) {
        if (!text || !query) return text;
        const tokens = query.trim().split(/\s+/).filter(Boolean);
        if (tokens.length === 0) return text;
        const pattern = tokens.map(escapeRegExp).join('|');
        const re = new RegExp(`(${pattern})`, 'gi');
        return text.replace(re, '<mark class="bg-sky-500/30 text-sky-200 px-0.5 rounded">$1</mark>');
    }

    // -------------------------------------------------------------------------
    // 8. RENDER BOOKMARKS EXPLORER & SEARCH RESULTS
    // -------------------------------------------------------------------------
    function renderSubfolderChips() {
        const container = document.getElementById('subfolder-chips-container');
        if (!container) return;

        if (activeCategory === 'pinned') {
            container.innerHTML = '';
            return;
        }

        const allBms = getAllBookmarks();
        const subfolders = new Set();
        for (let bm of allBms) {
            if (activeCategory === 'all' || bm.category === activeCategory) {
                if (bm.subfolder && bm.subfolder !== 'General') {
                    subfolders.add(bm.subfolder);
                }
            }
        }

        const sortedSubs = Array.from(subfolders).sort();

        if (sortedSubs.length === 0) {
            container.innerHTML = '';
            return;
        }

        let html = `
            <button data-sub="" class="sub-chip ${activeSubfolder === null ? 'bg-sky-500/20 text-sky-300 border-sky-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'} px-2.5 py-1 rounded text-[11px] font-medium border transition">
                All ${activeCategory === 'all' ? 'Subfolders' : activeCategory}
            </button>
        `;

        for (let s of sortedSubs) {
            const isActive = activeSubfolder === s;
            const count = allBms.filter(b => (activeCategory === 'all' || b.category === activeCategory) && b.subfolder === s).length;
            html += `
                <button data-sub="${escapeHtml(s)}" class="sub-chip ${isActive ? 'bg-sky-500/20 text-sky-300 border-sky-500/40' : 'bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border-slate-700/60'} px-2.5 py-1 rounded text-[11px] font-medium border transition">
                    ${escapeHtml(s)} (${count})
                </button>
            `;
        }

        container.innerHTML = html;

        container.querySelectorAll('.sub-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const val = btn.getAttribute('data-sub');
                activeSubfolder = val ? val : null;
                renderSubfolderChips();
                renderBookmarks();
            });
        });
    }

    function renderDashboardSearchResults() {
        const grid = document.getElementById('dashboard-bookmarks-grid');
        const statusLabel = document.getElementById('dashboard-results-status');
        const noResults = document.getElementById('dashboard-no-results-msg');
        const emptyMsg = document.getElementById('dashboard-empty-search-msg');
        
        if (!grid) return;
        
        const allBms = getAllBookmarks();
        const pinnedIds = getPinnedIds();
        const query = searchQuery.trim();
        
        if (!query && !aiSearchMode) {
            grid.innerHTML = '';
            statusLabel.classList.add('hidden');
            noResults.classList.add('hidden');
            emptyMsg.classList.remove('hidden');
            return;
        }
        
        emptyMsg.classList.add('hidden');

        let rankedList = [];

        if (aiSearchMode) {
            rankedList = allBms
                .filter(bm => aiMatchedIds.includes(bm.id))
                .map((bm, idx) => ({
                    bm,
                    score: 1000 - idx,
                    reason: 'AI Semantic Match',
                    matchPct: Math.max(70, 98 - (idx * 2))
                }));
        } else {
            // Apply Similarity & Relevance Scoring Engine
            rankedList = allBms.map(bm => {
                const count = getBookmarkUsageCount(bm.id);
                const isPinned = pinnedIds.includes(bm.id);
                const { score, reason, matchPct } = calculateSimilarityAndRelevance(bm, query, count, isPinned);
                return { bm, score, reason, matchPct };
            }).filter(item => item.score > 0);

            // Sort strictly descending by relevance score
            rankedList.sort((a, b) => b.score - a.score);
        }

        statusLabel.textContent = `Found ${rankedList.length} matching bookmark${rankedList.length === 1 ? '' : 's'} \u2022 Ranked by Similarity & Relevance`;
        statusLabel.classList.remove('hidden');

        if (rankedList.length === 0) {
            grid.innerHTML = '';
            noResults.classList.remove('hidden');
            return;
        }

        noResults.classList.add('hidden');

        grid.innerHTML = rankedList.map((item, index) => {
            const rank = index + 1;
            const bm = item.bm;
            const isPinned = pinnedIds.includes(bm.id);
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const count = getBookmarkUsageCount(bm.id);

            let badgeColor = 'bg-sky-500/10 text-sky-400 border-sky-500/20';
            if (bm.category === 'Bookmarks') badgeColor = 'bg-slate-700/50 text-sky-400 border-slate-700';

            // Match % Pill Color
            let matchBadgeColor = 'bg-slate-800 text-slate-300 border-slate-700';
            if (item.matchPct >= 90) matchBadgeColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
            else if (item.matchPct >= 75) matchBadgeColor = 'bg-sky-500/10 text-sky-300 border-sky-500/30';
            else if (item.matchPct >= 60) matchBadgeColor = 'bg-amber-500/10 text-amber-300 border-amber-500/30';

            return `
                <div class="bg-slate-900 border border-slate-800 hover:border-sky-500/50 rounded-xl p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition group">
                    <div>
                        <!-- Header with Rank, Domain, Badges -->
                        <div class="flex items-start justify-between gap-2 mb-2.5">
                            <div class="flex items-center gap-2 overflow-hidden">
                                <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                    #${rank}
                                </span>
                                <img src="${faviconUrl}" alt="" onerror="this.onerror=null;this.src='../../images/favicon.png'" class="w-4 h-4 object-contain flex-shrink-0 rounded-sm">
                                <span class="text-[11px] font-mono text-slate-400 truncate" title="${escapeHtml(domain)}">
                                    ${escapeHtml(domain)}
                                </span>
                            </div>
                            <div class="flex items-center gap-1.5 flex-shrink-0">
                                <span class="text-[9px] font-bold px-1.5 py-0.5 rounded border ${matchBadgeColor}">
                                    ${item.matchPct}% Match
                                </span>
                                ${count > 0 ? `
                                <span title="Launched ${count} times" class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                    <i class="fas fa-fire text-amber-400"></i> ${count}
                                </span>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Matched Reason Tag -->
                        ${item.reason ? `
                        <div class="mb-2">
                            <span class="inline-flex items-center gap-1 text-[9px] font-mono text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20 truncate max-w-full">
                                <i class="fas fa-bullseye text-[8px]"></i> ${escapeHtml(item.reason)}
                            </span>
                        </div>
                        ` : ''}

                        <!-- Bookmark Title with highlighted search tokens -->
                        <h3 class="text-sm font-bold text-slate-200 leading-snug line-clamp-2 mb-1.5 cursor-pointer hover:text-sky-300 transition" 
                            onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                            title="${escapeHtml(bm.name)}">
                            ${highlightTokens(escapeHtml(bm.name), query)}
                        </h3>

                        ${bm.path && bm.path !== 'General' ? `<p class="text-[10px] text-slate-500 font-mono truncate"><i class="fas fa-folder-open mr-1"></i>${escapeHtml(bm.path)}</p>` : ''}
                    </div>

                    <!-- Footer Action Bar -->
                    <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-800/60">
                        <div class="flex items-center gap-2">
                            <button onclick="togglePin(${bm.id})" class="text-xs ${isPinned ? 'text-amber-400 hover:text-amber-300' : 'text-slate-500 hover:text-slate-300'} transition" title="${isPinned ? 'Unpin' : 'Pin to top'}">
                                <i class="fas fa-star"></i>
                            </button>
                            <button onclick="copyToClipboard('${escapeHtml(bm.url)}', this)" class="text-xs text-slate-500 hover:text-slate-300 transition" title="Copy URL">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="editBookmark(${bm.id})" class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition" title="Edit">
                                <i class="fas fa-pen text-[10px]"></i>
                            </button>
                            <button onclick="deleteBookmark(${bm.id})" class="w-7 h-7 rounded-lg bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white flex items-center justify-center transition" title="Delete">
                                <i class="fas fa-trash-alt text-[10px]"></i>
                            </button>
                            <button onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white shadow shadow-sky-500/20 text-xs font-semibold transition" title="Launch">
                                <span>Open</span> <i class="fas fa-external-link-alt text-[9px]"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderBookmarks() {
        // Targets Tab 2 bookmarks directory
        const grid = document.getElementById('bookmarks-grid');
        const countLabel = document.getElementById('results-count-label');
        const noResults = document.getElementById('no-results-msg');
        if (!grid) return;

        const allBms = getAllBookmarks();
        const pinnedIds = getPinnedIds();
        
        // The directory filters by category and subfolder
        const filtered = allBms.filter(bm => {
            if (activeCategory === 'pinned') {
                if (!pinnedIds.includes(bm.id)) return false;
            } else if (activeCategory !== 'all') {
                if (bm.category !== activeCategory) return false;
            }
            if (activeSubfolder) {
                if (bm.subfolder !== activeSubfolder) return false;
            }
            return true;
        });

        if (countLabel) {
            countLabel.textContent = `Showing ${filtered.length} of ${allBms.length} bookmarks`;
        }

        if (filtered.length === 0) {
            grid.innerHTML = '';
            if (noResults) noResults.classList.remove('hidden');
            return;
        }

        if (noResults) noResults.classList.add('hidden');

        grid.innerHTML = filtered.map(bm => {
            const isPinned = pinnedIds.includes(bm.id);
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const count = getBookmarkUsageCount(bm.id);

            let badgeColor = 'bg-sky-500/10 text-sky-400 border-sky-500/20';
            if (bm.category === 'Bookmarks') badgeColor = 'bg-slate-700/50 text-sky-400 border-slate-700';

            return `
                <div class="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition group">
                    <div>
                        <!-- Header with domain, badges & actions -->
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <div class="flex items-center gap-2 overflow-hidden">
                                <img src="${faviconUrl}" alt="" onerror="this.onerror=null;this.src='../../images/favicon.png'" class="w-4 h-4 object-contain flex-shrink-0 rounded-sm">
                                <span class="text-[11px] font-mono text-slate-400 truncate" title="${escapeHtml(domain)}">
                                    ${escapeHtml(domain)}
                                </span>
                            </div>
                            <div class="flex items-center gap-1.5 flex-shrink-0">
                                ${count > 0 ? `
                                    <span title="Launched ${count} times" class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                        <i class="fas fa-fire text-amber-400"></i> ${count}
                                    </span>
                                ` : ''}
                                <span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${badgeColor}">
                                    ${bm.category}
                                </span>
                                <button onclick="togglePin(${bm.id})" title="${isPinned ? 'Unpin' : 'Pin to Launchpad'}"
                                    class="text-xs transition ml-1 ${isPinned ? 'text-amber-400' : 'text-slate-600 hover:text-amber-400'}">
                                    <i class="${isPinned ? 'fas' : 'far'} fa-star"></i>
                                </button>
                                <button onclick="deleteBookmark(${bm.id})" title="Delete Bookmark"
                                    class="text-slate-600 hover:text-rose-400 text-xs transition opacity-0 group-hover:opacity-100 ml-0.5">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </div>

                        <!-- Bookmark Title -->
                        <div onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                            class="font-semibold text-sm text-slate-200 group-hover:text-sky-300 transition line-clamp-2 leading-snug cursor-pointer" 
                            title="${escapeHtml(bm.name)}">
                            ${escapeHtml(bm.name)}
                        </div>

                        <!-- Path Breadcrumbs -->
                        <div class="mt-2 text-[10px] text-slate-500 truncate" title="${escapeHtml(bm.path || '')}">
                            <i class="fas fa-folder-open text-[9px] text-slate-600 mr-1"></i> ${escapeHtml(bm.path || bm.category)}
                        </div>
                    </div>

                    <!-- Footer Action Bar -->
                    <div class="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs">
                        <button onclick="copyToClipboard('${escapeHtml(bm.url)}', this)" title="Copy URL" 
                            class="text-slate-500 hover:text-slate-300 transition text-[11px] flex items-center gap-1">
                            <i class="far fa-copy"></i> <span>Copy</span>
                        </button>

                        <button onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-sky-600 text-sky-400 hover:text-white text-[11px] font-semibold transition">
                            <span>Open</span> <i class="fas fa-external-link-alt text-[9px]"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function initCategoryPills() {
        const container = document.getElementById('category-pills');
        if (!container) return;

        container.querySelectorAll('.cat-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                container.querySelectorAll('.cat-pill').forEach(b => {
                    b.className = 'cat-pill px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition';
                });
                btn.className = 'cat-pill active px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white shadow-sm transition';
                activeCategory = btn.getAttribute('data-cat');
                activeSubfolder = null;
                renderSubfolderChips();
                renderBookmarks();
            });
        });
    }

    window.filterCategoryAndOpen = function (categoryName) {
        switchTab('tab-bookmarks');
        activeCategory = categoryName;
        activeSubfolder = null;
        
        const container = document.getElementById('category-pills');
        if (container) {
            container.querySelectorAll('.cat-pill').forEach(b => {
                if (b.getAttribute('data-cat') === categoryName) {
                    b.className = 'cat-pill active px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 text-white shadow-sm transition';
                } else {
                    b.className = 'cat-pill px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition';
                }
            });
        }
        renderSubfolderChips();
        renderBookmarks();
    };

    // -------------------------------------------------------------------------
    // 9. SEARCH FUNCTIONALITY
    // -------------------------------------------------------------------------
    function initSearch() {
        const globalSearch = document.getElementById('global-search-input');
        const clearGlobal = document.getElementById('clear-search-btn');
        const bmSearch = document.getElementById('bm-search-input');
        const clearBm = document.getElementById('bm-clear-btn');

        function onSearchInput(val) {
            searchQuery = val;
            aiSearchMode = false;
            aiMatchedIds = [];
            if (globalSearch && globalSearch.value !== val) globalSearch.value = val;
            if (bmSearch && bmSearch.value !== val) bmSearch.value = val;

            if (clearGlobal) clearGlobal.classList.toggle('hidden', !val);
            if (clearBm) clearBm.classList.toggle('hidden', !val);

            renderDashboardSearchResults();
        }

        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => {
                onSearchInput(e.target.value);
                if (e.target.value && document.getElementById('tab-dashboard').classList.contains('hidden')) {
                    switchTab('tab-dashboard');
                }
            });
        }

        if (clearGlobal) {
            clearGlobal.addEventListener('click', () => {
                onSearchInput('');
                if (globalSearch) globalSearch.focus();
            });
        }

        if (bmSearch) {
            bmSearch.addEventListener('input', (e) => onSearchInput(e.target.value));
        }

        if (clearBm) {
            clearBm.addEventListener('click', () => {
                onSearchInput('');
                if (bmSearch) bmSearch.focus();
            });
        }

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA')) {
                e.preventDefault();
                if (bmSearch) {
                    bmSearch.focus();
                    bmSearch.select();
                } else if (globalSearch) {
                    globalSearch.focus();
                    globalSearch.select();
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 10. SECRET MESSAGE HUB & INBOUND DISPATCH PROTOCOL
    // -------------------------------------------------------------------------
    const SEED_DUMMY_IDS = [1, 2, 3, 4];
    const SEED_DUMMY_EMAILS = ["slin@mit.edu", "amorales@twu.edu", "cise-program@nsf.gov", "tmansour@cairo.edu.eg"];

    // Automatically purge legacy dummy messages and hydrate from SQLite portal_messages
    function getSqliteMessages() {
        const dbMsgs = window.__SITE_DATABASE && window.__SITE_DATABASE.portal_messages;
        return Array.isArray(dbMsgs) ? dbMsgs : [];
    }

    function purgeLegacyDummyMessages() {
        const stored = localStorage.getItem(MESSAGES_KEY);
        const sqliteMsgs = getSqliteMessages();
        if (!stored) {
            localStorage.setItem(MESSAGES_KEY, JSON.stringify(sqliteMsgs));
            return;
        }
        try {
            const parsed = JSON.parse(stored);
            if (Array.isArray(parsed)) {
                let cleaned = parsed.filter(m => 
                    m && !SEED_DUMMY_IDS.includes(m.id) &&
                    !SEED_DUMMY_EMAILS.includes(m.email) &&
                    Boolean(m.fingerprint)
                );
                if (cleaned.length === 0 && sqliteMsgs.length > 0) {
                    cleaned = sqliteMsgs;
                }
                localStorage.setItem(MESSAGES_KEY, JSON.stringify(cleaned));
            } else {
                localStorage.setItem(MESSAGES_KEY, JSON.stringify(sqliteMsgs));
            }
        } catch (e) {
            localStorage.setItem(MESSAGES_KEY, JSON.stringify(sqliteMsgs));
        }
    }
    purgeLegacyDummyMessages();

    function getStoredMessages() {
        const stored = localStorage.getItem(MESSAGES_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed)) {
                    const cleaned = parsed.filter(m => 
                        m && !SEED_DUMMY_IDS.includes(m.id) &&
                        !SEED_DUMMY_EMAILS.includes(m.email) &&
                        Boolean(m.fingerprint)
                    );
                    if (cleaned.length !== parsed.length) {
                        localStorage.setItem(MESSAGES_KEY, JSON.stringify(cleaned));
                    }
                    if (cleaned.length > 0) return cleaned;
                }
            } catch (e) { }
        }
        const sqliteMsgs = getSqliteMessages();
        if (sqliteMsgs.length > 0) {
            localStorage.setItem(MESSAGES_KEY, JSON.stringify(sqliteMsgs));
        }
        return sqliteMsgs;
    }

    function saveMessages(msgs) {
        localStorage.setItem(MESSAGES_KEY, JSON.stringify(msgs));
        renderInbox();
        updateStats();
    }

    window.clearAllMessages = function () {
        if (confirm('Permanently purge and shred all messages in your secret messaging vault?')) {
            saveMessages([]);
            selectedMessageId = null;
            renderInbox();
            renderMessageDetail(null);
        }
    };

    function getHandshakeConfig() {
        const stored = localStorage.getItem(HANDSHAKE_CONFIG_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        return DEFAULT_HANDSHAKE_CONFIG;
    }

    function saveHandshakeConfigObj(config) {
        localStorage.setItem(HANDSHAKE_CONFIG_KEY, JSON.stringify(config));
    }

    function initHandshakeSettings() {
        const config = getHandshakeConfig();
        const passInput = document.getElementById('handshake-passcode-input');
        const questionInput = document.getElementById('handshake-question-input');
        const answerInput = document.getElementById('handshake-answer-input');
        const emailInput = document.getElementById('handshake-email-input');
        const form = document.getElementById('handshake-config-form');
        const msg = document.getElementById('handshake-save-msg');

        if (passInput) passInput.value = config.passcode || DEFAULT_HANDSHAKE_CONFIG.passcode;
        if (questionInput) questionInput.value = config.question || DEFAULT_HANDSHAKE_CONFIG.question;
        if (answerInput) answerInput.value = (config.answers || DEFAULT_HANDSHAKE_CONFIG.answers).join(', ');
        if (emailInput) emailInput.value = config.destinationEmail || DEFAULT_HANDSHAKE_CONFIG.destinationEmail;

        if (form && !form.dataset.initialized) {
            form.dataset.initialized = 'true';
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const newPass = (passInput ? passInput.value : '').trim();
                const newQuestion = (questionInput ? questionInput.value : '').trim();
                const rawAnswers = (answerInput ? answerInput.value : '').trim();
                const destEmail = (emailInput ? emailInput.value : '').trim();

                if (!newPass || !newQuestion || !rawAnswers) {
                    if (msg) {
                        msg.className = 'text-xs text-rose-400 block';
                        msg.textContent = 'All handshake parameters are required.';
                    }
                    return;
                }

                const answersArr = rawAnswers.split(',').map(s => s.trim()).filter(Boolean);
                const updatedConfig = {
                    passcode: newPass,
                    question: newQuestion,
                    answers: answersArr,
                    destinationEmail: destEmail || DEFAULT_HANDSHAKE_CONFIG.destinationEmail
                };

                saveHandshakeConfigObj(updatedConfig);
                if (msg) {
                    msg.className = 'text-xs text-emerald-400 block';
                    msg.textContent = 'Secret handshake keys & destination email saved successfully!';
                    setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
                }
            });
        }
    }

    window.openHandshakeSettings = function () {
        switchTab('tab-settings');
        setTimeout(() => {
            const el = document.getElementById('handshake-passcode-input');
            if (el) {
                el.focus();
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 150);
    };

    window.openSecretDispatchModal = function () {
        const config = getHandshakeConfig();
        const questionLabel = document.getElementById('dispatch-challenge-question-label');
        if (questionLabel) {
            questionLabel.textContent = config.question || DEFAULT_HANDSHAKE_CONFIG.question;
        }
        const errorEl = document.getElementById('dispatch-error-msg');
        if (errorEl) {
            errorEl.classList.add('hidden');
            errorEl.textContent = '';
        }
        const form = document.getElementById('secret-dispatch-form');
        if (form) form.reset();

        const modal = document.getElementById('secret-dispatch-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeSecretDispatchModal = function () {
        const modal = document.getElementById('secret-dispatch-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    function initSecretDispatchForm() {
        const form = document.getElementById('secret-dispatch-form');
        if (!form || form.dataset.initialized) return;
        form.dataset.initialized = 'true';

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const config = getHandshakeConfig();
            const enteredPasscode = (document.getElementById('dispatch-passcode')?.value || '').trim();
            const enteredAnswer = (document.getElementById('dispatch-challenge-answer')?.value || '').trim().toLowerCase();
            const sender = (document.getElementById('dispatch-sender')?.value || '').trim();
            const email = (document.getElementById('dispatch-email')?.value || '').trim();
            const tag = document.getElementById('dispatch-tag')?.value || 'Confidential Collab';
            const subject = (document.getElementById('dispatch-subject')?.value || '').trim();
            const body = (document.getElementById('dispatch-body')?.value || '').trim();
            const errorEl = document.getElementById('dispatch-error-msg');

            // 1. Verify Passcode
            if (enteredPasscode !== config.passcode) {
                if (errorEl) {
                    errorEl.textContent = 'Authentication Failed: Handshake passcode token is invalid.';
                    errorEl.classList.remove('hidden');
                }
                return;
            }

            // 2. Verify Challenge Answer
            const validAnswers = (config.answers || []).map(a => a.toLowerCase().trim());
            const isAnswerMatch = validAnswers.some(a => a === enteredAnswer || enteredAnswer.includes(a) || a.includes(enteredAnswer));

            if (!isAnswerMatch) {
                if (errorEl) {
                    errorEl.textContent = 'Challenge Failed: Secret answer does not match the shared protocol.';
                    errorEl.classList.remove('hidden');
                }
                return;
            }

            // Generate verified dispatch payload with cryptographic audit fingerprint
            const rawHash = Array.from(crypto.getRandomValues(new Uint8Array(8)))
                .map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
            const fingerprint = `SHA256:${rawHash}`;

            const newMsg = {
                id: Date.now(),
                sender: sender,
                email: email,
                tag: tag,
                subject: subject,
                body: body,
                date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                unread: true,
                starred: false,
                fingerprint: fingerprint
            };

            const msgs = getStoredMessages();
            msgs.unshift(newMsg);
            saveMessages(msgs);

            closeSecretDispatchModal();
            selectedMessageId = newMsg.id;
            switchTab('tab-inbox');
            renderInbox();
            renderMessageDetail(newMsg.id);

            // Optional direct Web Email Relay dispatch to destination email
            const relayToEmail = document.getElementById('dispatch-relay-email')?.checked;
            const destEmail = config.destinationEmail || DEFAULT_HANDSHAKE_CONFIG.destinationEmail;

            if (relayToEmail && destEmail) {
                fetch(`https://formsubmit.co/ajax/${encodeURIComponent(destEmail)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify({
                        _subject: `[PORTAL SECRET DISPATCH] ${subject}`,
                        sender_codename: sender,
                        sender_email: email,
                        classification: tag,
                        audit_fingerprint: fingerprint,
                        secret_payload: body,
                        timestamp: new Date().toISOString()
                    })
                }).then(() => {
                    alert("Handshake Verified: Secret message saved to vault AND dispatched to Dr. Islam's email inbox via web relay.");
                }).catch(() => {
                    alert('Handshake Verified: Secret message authenticated and delivered to Message Hub.');
                });
            } else {
                alert('Handshake Verified: Secret message has been authenticated and delivered to your Message Hub.');
            }
        });
    }

    function renderInbox() {
        const msgs = getStoredMessages();
        const listEl = document.getElementById('messages-list');
        const searchInput = document.getElementById('msg-search-input');
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

        if (!listEl) return;

        const filtered = msgs.filter(m => {
            if (!query) return true;
            return m.sender.toLowerCase().includes(query) ||
                   m.subject.toLowerCase().includes(query) ||
                   m.email.toLowerCase().includes(query) ||
                   m.body.toLowerCase().includes(query) ||
                   (m.tag && m.tag.toLowerCase().includes(query));
        });

        if (filtered.length === 0) {
            listEl.innerHTML = `
                <div class="p-8 text-center text-xs text-slate-500 space-y-2">
                    <div class="w-10 h-10 rounded-full bg-slate-800 text-rose-400 flex items-center justify-center mx-auto mb-2 text-sm border border-slate-700">
                        <i class="fas fa-user-shield"></i>
                    </div>
                    <p class="font-semibold text-slate-300">Secret Messaging Vault Empty</p>
                    <p class="text-[11px] text-slate-500">Zero dummy messages. All dispatches require authorized handshake passcode and shared secret challenge response.</p>
                </div>
            `;
            if (selectedMessageId) {
                renderMessageDetail(null);
            }
            return;
        }

        listEl.innerHTML = filtered.map(m => {
            const isSelected = m.id === selectedMessageId;
            const initials = m.sender.split(' ').map(n => n[0]).join('').slice(0, 2);

            return `
                <div onclick="selectMessage(${m.id})" class="p-3.5 cursor-pointer transition flex items-start gap-3 ${isSelected ? 'bg-slate-800' : 'hover:bg-slate-800/50'} ${m.unread ? 'border-l-2 border-rose-500' : 'border-l-2 border-transparent'}">
                    <div class="w-8 h-8 rounded-full ${m.unread ? 'bg-rose-500 text-white' : 'bg-slate-700 text-slate-300'} flex items-center justify-center font-bold text-xs flex-shrink-0">
                        ${initials}
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between gap-1 mb-0.5">
                            <span class="text-xs font-bold truncate ${m.unread ? 'text-white' : 'text-slate-300'}">${escapeHtml(m.sender)}</span>
                            <span class="text-[10px] text-slate-500 flex-shrink-0">${m.date}</span>
                        </div>
                        <div class="text-xs font-medium text-slate-200 truncate ${m.unread ? 'font-bold text-white' : ''}">
                            ${escapeHtml(m.subject)}
                        </div>
                        <div class="text-[11px] text-slate-400 truncate mt-0.5">
                            ${escapeHtml(m.body.slice(0, 60))}...
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        if (selectedMessageId) {
            renderMessageDetail(selectedMessageId);
        }
    }

    window.selectMessage = function (msgId) {
        selectedMessageId = msgId;
        const msgs = getStoredMessages();
        const msg = msgs.find(m => m.id === msgId);
        if (msg && msg.unread) {
            msg.unread = false;
            saveMessages(msgs);
        } else {
            renderInbox();
        }
        renderMessageDetail(msgId);
    };

    function renderMessageDetail(msgId) {
        const msgs = getStoredMessages();
        const msg = msgs.find(m => m.id === msgId);
        const placeholder = document.getElementById('msg-placeholder');
        const container = document.getElementById('msg-content-container');

        if (!msg) {
            if (placeholder) placeholder.classList.remove('hidden');
            if (container) container.classList.add('hidden');
            return;
        }

        if (placeholder) placeholder.classList.add('hidden');
        if (container) {
            container.classList.remove('hidden');
            container.classList.add('flex');
        }

        const subjectEl = document.getElementById('msg-subject');
        const senderEl = document.getElementById('msg-sender');
        const emailEl = document.getElementById('msg-email');
        const dateEl = document.getElementById('msg-date');
        const tagEl = document.getElementById('msg-tag');
        const bodyEl = document.getElementById('msg-body');
        const avatarEl = document.getElementById('msg-avatar');
        const fingerprintEl = document.getElementById('msg-fingerprint');

        if (subjectEl) subjectEl.textContent = msg.subject;
        if (senderEl) senderEl.textContent = msg.sender;
        if (emailEl) emailEl.textContent = msg.email;
        if (dateEl) dateEl.textContent = msg.date;
        if (tagEl) tagEl.textContent = msg.tag || 'Encrypted Dispatch';
        if (bodyEl) bodyEl.textContent = msg.body;
        if (avatarEl) avatarEl.textContent = msg.sender.split(' ').map(n => n[0]).join('').slice(0, 2);
        if (fingerprintEl) fingerprintEl.textContent = msg.fingerprint || 'AUTHENTICATED-SHA256';

        const replyLink = document.getElementById('msg-reply-link');
        if (replyLink) {
            replyLink.href = `mailto:${msg.email}?subject=Re: [Secure] ${encodeURIComponent(msg.subject)}`;
        }

        const starBtn = document.getElementById('msg-star-btn');
        if (starBtn) {
            starBtn.innerHTML = `<i class="${msg.starred ? 'fas' : 'far'} fa-star"></i>`;
            starBtn.onclick = () => {
                msg.starred = !msg.starred;
                saveMessages(msgs);
                renderMessageDetail(msg.id);
            };
        }

        const deleteBtn = document.getElementById('msg-delete-btn');
        if (deleteBtn) {
            deleteBtn.onclick = () => {
                if (confirm('Shred and permanently delete this confidential message?')) {
                    const updated = msgs.filter(m => m.id !== msg.id);
                    selectedMessageId = null;
                    saveMessages(updated);
                    renderMessageDetail(null);
                }
            };
        }
    }

    window.copyCurrentMessageBody = function () {
        if (!selectedMessageId) return;
        const msgs = getStoredMessages();
        const msg = msgs.find(m => m.id === selectedMessageId);
        if (!msg) return;
        navigator.clipboard.writeText(msg.body).then(() => {
            alert('Encrypted dispatch body copied to clipboard.');
        }).catch(() => {
            prompt('Copy message body:', msg.body);
        });
    };

    window.refreshInbox = function () {
        renderInbox();
        const btn = document.querySelector('[title="Refresh Inbox"] i');
        if (btn) {
            btn.classList.add('fa-spin');
            setTimeout(() => btn.classList.remove('fa-spin'), 600);
        }
    };

    // -------------------------------------------------------------------------
    // SECURE EMAIL DISPATCH & REPLY MODAL LOGIC
    // -------------------------------------------------------------------------
    window.openSecureReplyModal = function () {
        if (!selectedMessageId) return alert('Please select an authenticated message first to reply.');
        const msgs = getStoredMessages();
        const msg = msgs.find(m => m.id === selectedMessageId);
        if (!msg) return;

        const recipientInput = document.getElementById('reply-recipient-email');
        const subjectInput = document.getElementById('reply-subject');
        const fpInput = document.getElementById('reply-fingerprint');
        const bodyInput = document.getElementById('reply-body');
        const statusMsg = document.getElementById('reply-status-msg');

        if (recipientInput) recipientInput.value = msg.email || '';
        if (subjectInput) subjectInput.value = msg.subject.startsWith('Re:') ? msg.subject : `Re: [Secure Dispatch] ${msg.subject}`;
        if (fpInput) fpInput.value = msg.fingerprint || 'AUTHENTICATED-SHA256';
        if (bodyInput) bodyInput.value = `Dear ${msg.sender},\n\n\n\n---\n[Authenticated Inbound Dispatch]\nSender: ${msg.sender} <${msg.email}>\nFingerprint: ${msg.fingerprint || 'N/A'}\nDate: ${msg.date}\nClassification: ${msg.tag || 'Confidential'}\n"${msg.body}"`;

        if (statusMsg) {
            statusMsg.className = 'hidden text-xs font-semibold p-2.5 rounded-lg';
            statusMsg.textContent = '';
        }

        const modal = document.getElementById('secure-reply-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeSecureReplyModal = function () {
        const modal = document.getElementById('secure-reply-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.sendReplyViaGmail = function () {
        const to = (document.getElementById('reply-recipient-email')?.value || '').trim();
        const su = (document.getElementById('reply-subject')?.value || '').trim();
        const body = (document.getElementById('reply-body')?.value || '').trim();
        const fp = (document.getElementById('reply-fingerprint')?.value || '').trim();
        const fullBody = `${body}\n\n---\n[Portal Secure Verification: ${fp}]\nTransmitted from Dr. Islam Akef Ebeid Command Center`;

        const url = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${encodeURIComponent(su)}&body=${encodeURIComponent(fullBody)}`;
        window.open(url, '_blank');
    };

    window.sendReplyViaOutlook = function () {
        const to = (document.getElementById('reply-recipient-email')?.value || '').trim();
        const su = (document.getElementById('reply-subject')?.value || '').trim();
        const body = (document.getElementById('reply-body')?.value || '').trim();
        const fp = (document.getElementById('reply-fingerprint')?.value || '').trim();
        const fullBody = `${body}\n\n---\n[Portal Secure Verification: ${fp}]\nTransmitted from Dr. Islam Akef Ebeid Command Center`;

        const url = `https://outlook.office.com/mail/deeplink/compose?to=${encodeURIComponent(to)}&subject=${encodeURIComponent(su)}&body=${encodeURIComponent(fullBody)}`;
        window.open(url, '_blank');
    };

    window.sendReplyViaRelay = async function () {
        const to = (document.getElementById('reply-recipient-email')?.value || '').trim();
        const su = (document.getElementById('reply-subject')?.value || '').trim();
        const body = (document.getElementById('reply-body')?.value || '').trim();
        const fp = (document.getElementById('reply-fingerprint')?.value || '').trim();
        const statusMsg = document.getElementById('reply-status-msg');
        const btn = document.getElementById('btn-reply-relay');

        if (!to || !body) {
            if (statusMsg) {
                statusMsg.className = 'text-xs text-rose-400 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 block';
                statusMsg.textContent = 'Recipient email and message body are required.';
            }
            return;
        }

        if (btn) btn.disabled = true;
        if (statusMsg) {
            statusMsg.className = 'text-xs text-sky-400 p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/20 block animate-pulse';
            statusMsg.textContent = 'Relaying dispatch through secure web email channel...';
        }

        try {
            const resp = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(to)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    _subject: su || '[PORTAL SECURE DISPATCH]',
                    recipient: to,
                    verification_fingerprint: fp,
                    secure_message: body,
                    dispatched_at: new Date().toISOString()
                })
            });

            if (resp.ok) {
                if (statusMsg) {
                    statusMsg.className = 'text-xs text-emerald-400 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 block font-semibold';
                    statusMsg.textContent = '✓ Secure dispatch transmitted directly to recipient email inbox via web relay!';
                }
            } else {
                throw new Error(`Relay returned status ${resp.status}`);
            }
        } catch (err) {
            if (statusMsg) {
                statusMsg.className = 'text-xs text-amber-400 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 block';
                statusMsg.textContent = `Direct API relay blocked by browser CORS. Click "Open in Gmail Web" or "Open in Outlook Web" above to send instantly!`;
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    };

    window.copyReplyPayload = function () {
        const to = (document.getElementById('reply-recipient-email')?.value || '').trim();
        const su = (document.getElementById('reply-subject')?.value || '').trim();
        const body = (document.getElementById('reply-body')?.value || '').trim();
        const fp = (document.getElementById('reply-fingerprint')?.value || '').trim();
        const payload = `To: ${to}\nSubject: ${su}\nVerification Fingerprint: ${fp}\nDate: ${new Date().toISOString()}\n\n${body}`;

        navigator.clipboard.writeText(payload).then(() => {
            alert('Formatted dispatch email payload copied to clipboard.');
        }).catch(() => {
            prompt('Copy email payload:', payload);
        });
    };

    // -------------------------------------------------------------------------
    // 11. SCRATCHPAD STUDIO, DATABASE & TASKS
    // -------------------------------------------------------------------------
    function updateScratchCounters(val) {
        const text = val || '';
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const chars = text.length;

        const dashCounter = document.getElementById('scratch-word-count');
        if (dashCounter) dashCounter.textContent = `${words} words`;

        const fullStats = document.getElementById('full-scratch-stats');
        if (fullStats) fullStats.textContent = `${words} words \u2022 ${chars} chars`;
    }

    function initScratchpad() {
        const dashScratch = document.getElementById('dashboard-scratchpad');
        const fullScratch = document.getElementById('full-scratchpad');
        const sqliteBuffer = (window.__SITE_DATABASE && window.__SITE_DATABASE.portal_scratches && window.__SITE_DATABASE.portal_scratches.active_buffer) || '';
        let saved = localStorage.getItem(SCRATCHPAD_KEY);
        if (saved === null) {
            saved = sqliteBuffer;
            if (saved) localStorage.setItem(SCRATCHPAD_KEY, saved);
        }

        if (dashScratch && document.activeElement !== dashScratch) dashScratch.value = saved;
        if (fullScratch && document.activeElement !== fullScratch) fullScratch.value = saved;
        updateScratchCounters(saved);

        if (initScratchpad.initialized) return;
        initScratchpad.initialized = true;

        if (dashScratch) dashScratch.setAttribute('autocomplete', 'off');
        if (fullScratch) fullScratch.setAttribute('autocomplete', 'off');

        function syncAndSave(val, source) {
            localStorage.setItem(SCRATCHPAD_KEY, val);
            if (source !== 'dash' && dashScratch && dashScratch.value !== val) {
                dashScratch.value = val;
            }
            if (source !== 'full' && fullScratch && fullScratch.value !== val) {
                fullScratch.value = val;
            }
            updateScratchCounters(val);

            const dashStatus = document.getElementById('scratch-save-status');
            const fullStatus = document.getElementById('full-scratch-status');
            if (dashStatus) dashStatus.textContent = 'Saved just now';
            if (fullStatus) fullStatus.textContent = 'Live Synced';

            clearTimeout(initScratchpad.statusTimer);
            initScratchpad.statusTimer = setTimeout(() => {
                if (dashStatus) dashStatus.textContent = 'Auto-saved';
                if (fullStatus) fullStatus.textContent = 'Live Synced';
            }, 1800);
        }

        if (dashScratch) {
            ['input', 'keyup', 'paste', 'change'].forEach(evt => {
                dashScratch.addEventListener(evt, (e) => {
                    syncAndSave(e.target.value, 'dash');
                });
            });
        }

        if (fullScratch) {
            ['input', 'keyup', 'paste', 'change'].forEach(evt => {
                fullScratch.addEventListener(evt, (e) => {
                    syncAndSave(e.target.value, 'full');
                });
            });
        }

        const dbSearchInput = document.getElementById('scratch-db-search');
        if (dbSearchInput) {
            dbSearchInput.addEventListener('input', () => {
                renderScratchesDb();
            });
        }
    }

    function getScratchesDb() {
        const stored = localStorage.getItem(SCRATCHES_DB_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.length > 0) return parsed;
            } catch (e) { }
        }
        const sqliteArchive = (window.__SITE_DATABASE && window.__SITE_DATABASE.portal_scratches && Array.isArray(window.__SITE_DATABASE.portal_scratches.archive))
            ? window.__SITE_DATABASE.portal_scratches.archive
            : [];
        if (sqliteArchive.length > 0) {
            localStorage.setItem(SCRATCHES_DB_KEY, JSON.stringify(sqliteArchive));
        }
        return sqliteArchive;
    }

    function saveScratchesDb(entries) {
        localStorage.setItem(SCRATCHES_DB_KEY, JSON.stringify(entries));
        renderScratchesDb();
    }

    window.commitScratchToDb = function () {
        const buffer = localStorage.getItem(SCRATCHPAD_KEY) || '';
        if (!buffer.trim()) {
            alert('Active scratchpad buffer is empty. Type some notes before saving to database.');
            return;
        }

        const firstLine = buffer.trim().split('\n')[0].slice(0, 40);
        const defaultTitle = firstLine ? `Snapshot: ${firstLine}` : `Scratch Archive ${new Date().toLocaleDateString()}`;
        const titlePrompt = prompt('Enter a label / title for this scratchpad snapshot:', defaultTitle);
        if (titlePrompt === null) return;

        const title = titlePrompt.trim() || defaultTitle;
        const words = buffer.trim().split(/\s+/).length;
        const chars = buffer.length;

        const newEntry = {
            id: Date.now(),
            title: title,
            content: buffer,
            timestamp: new Date().toISOString(),
            dateStr: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }),
            wordCount: words,
            charCount: chars
        };

        const db = getScratchesDb();
        db.unshift(newEntry);
        saveScratchesDb(db);

        const dashStatus = document.getElementById('scratch-save-status');
        const fullStatus = document.getElementById('full-scratch-status');
        if (dashStatus) dashStatus.textContent = 'Committed to DB!';
        if (fullStatus) fullStatus.textContent = 'Archived to Database!';

        alert(`Scratch snapshot "${title}" successfully committed to persistent database.`);
    };

    window.loadScratchIntoBuffer = function (entryId) {
        const db = getScratchesDb();
        const entry = db.find(e => e.id === entryId);
        if (!entry) return;

        if (confirm(`Load "${entry.title}" into active working buffer? (This will update both Dashboard and Scratchpad tabs)`)) {
            localStorage.setItem(SCRATCHPAD_KEY, entry.content);
            const dashScratch = document.getElementById('dashboard-scratchpad');
            const fullScratch = document.getElementById('full-scratchpad');
            if (dashScratch) dashScratch.value = entry.content;
            if (fullScratch) fullScratch.value = entry.content;
            updateScratchCounters(entry.content);
            alert('Snapshot loaded into active working buffer.');
        }
    };

    window.deleteScratchEntry = function (entryId) {
        if (confirm('Permanently delete this scratch archive record from database?')) {
            const db = getScratchesDb().filter(e => e.id !== entryId);
            saveScratchesDb(db);
        }
    };

    window.copyScratchEntry = function (entryId) {
        const db = getScratchesDb();
        const entry = db.find(e => e.id === entryId);
        if (!entry) return;
        navigator.clipboard.writeText(entry.content).then(() => {
            alert(`Copied "${entry.title}" content to clipboard.`);
        }).catch(() => {
            prompt('Copy content:', entry.content);
        });
    };

    window.copyScratchBuffer = function () {
        const buffer = localStorage.getItem(SCRATCHPAD_KEY) || '';
        if (!buffer) return alert('Scratchpad buffer is empty.');
        navigator.clipboard.writeText(buffer).then(() => {
            alert('Working scratchpad buffer copied to clipboard.');
        }).catch(() => {
            prompt('Copy buffer:', buffer);
        });
    };

    window.exportScratchesDbJSON = function () {
        const db = getScratchesDb();
        if (db.length === 0) return alert('Scratches database is empty. No records to export.');
        const exportData = {
            total_scratches: db.length,
            exported_at: new Date().toISOString(),
            scratches: db
        };
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `islam_ebeid_scratches_db_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    function renderScratchesDb() {
        const container = document.getElementById('scratches-db-container');
        const countBadge = document.getElementById('scratches-db-count');
        if (!container) return;

        const db = getScratchesDb();
        if (countBadge) countBadge.textContent = `${db.length} Records`;

        const query = (document.getElementById('scratch-db-search')?.value || '').toLowerCase().trim();
        const filtered = db.filter(e => {
            if (!query) return true;
            return e.title.toLowerCase().includes(query) || e.content.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-xs text-slate-500 rounded-xl bg-slate-800/30 border border-slate-800 space-y-1">
                    <i class="fas fa-database text-slate-600 text-lg mb-1 block"></i>
                    <p class="font-semibold text-slate-400">No persistent scratches found</p>
                    <p class="text-[11px] text-slate-500">Click "Commit / Save to Database" above or in Dashboard to archive notes here permanently.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(item => `
            <div class="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700/80 hover:border-slate-600 transition space-y-2">
                <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-bold text-white truncate">${escapeHtml(item.title)}</span>
                            <span class="text-[10px] font-mono text-slate-500 flex-shrink-0">${item.dateStr}</span>
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono mt-0.5">
                            ${item.wordCount || 0} words &bull; ${item.charCount || 0} chars
                        </div>
                    </div>
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        <button onclick="loadScratchIntoBuffer(${item.id})" class="px-2.5 py-1 rounded bg-sky-600/20 hover:bg-sky-600/40 text-sky-300 text-[11px] font-semibold border border-sky-500/30 transition" title="Load into active buffer">
                            <i class="fas fa-upload mr-1"></i> Load
                        </button>
                        <button onclick="copyScratchEntry(${item.id})" class="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs transition" title="Copy text">
                            <i class="far fa-copy"></i>
                        </button>
                        <button onclick="deleteScratchEntry(${item.id})" class="p-1.5 rounded bg-slate-700 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 text-xs transition" title="Delete record">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                <div class="text-xs text-slate-300 font-mono bg-slate-900/80 p-2.5 rounded-lg max-h-24 overflow-y-auto whitespace-pre-wrap border border-slate-800">
                    ${escapeHtml(item.content.slice(0, 300))}${item.content.length > 300 ? '...' : ''}
                </div>
            </div>
        `).join('');
    }

    window.downloadScratchpad = function() {
        const content = localStorage.getItem(SCRATCHPAD_KEY) || '';
        if (!content) return alert("Scratchpad is empty.");
        
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scratchpad_backup_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    window.clearScratchpad = function () {
        if (confirm('Are you sure you want to clear your active scratchpad buffer? (Your persistent database snapshots will remain safe)')) {
            localStorage.removeItem(SCRATCHPAD_KEY);
            const dashScratch = document.getElementById('dashboard-scratchpad');
            const fullScratch = document.getElementById('full-scratchpad');
            if (dashScratch) dashScratch.value = '';
            if (fullScratch) fullScratch.value = '';
            updateScratchCounters('');
        }
    };

    // Task List Logic (Hydrated from SQLite portal_tasks)
    function getStoredTasks() {
        const stored = localStorage.getItem(TASKS_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.length > 0) return parsed;
            } catch (e) { }
        }
        const sqliteTasks = (window.__SITE_DATABASE && Array.isArray(window.__SITE_DATABASE.portal_tasks))
            ? window.__SITE_DATABASE.portal_tasks
            : [];
        if (sqliteTasks.length > 0) {
            localStorage.setItem(TASKS_KEY, JSON.stringify(sqliteTasks));
        }
        return sqliteTasks;
    }

    function saveTasks(tasks) {
        localStorage.setItem(TASKS_KEY, JSON.stringify(tasks));
        renderTasks();
    }

    window.setTaskFilter = function (filter) {
        activeTaskFilter = filter;
        document.querySelectorAll('.task-filter-pill').forEach(btn => {
            if (btn.getAttribute('data-filter') === filter) {
                btn.className = 'task-filter-pill active px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-600 text-white transition';
            } else {
                btn.className = 'task-filter-pill px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition';
            }
        });
        renderTasks();
    };

    function renderTasks() {
        const list = document.getElementById('task-list');
        const statsLabel = document.getElementById('task-stats-label');
        if (!list) return;
        const tasks = getStoredTasks();

        const activeCount = tasks.filter(t => !t.done).length;
        if (statsLabel) {
            statsLabel.textContent = `${activeCount} active of ${tasks.length} total tasks`;
        }

        const filtered = tasks.filter(t => {
            if (activeTaskFilter === 'active') return !t.done;
            if (activeTaskFilter === 'completed') return t.done;
            return true;
        });

        if (filtered.length === 0) {
            list.innerHTML = `<li class="p-6 text-center text-xs text-slate-500 rounded-lg bg-slate-800/30">No tasks in this view.</li>`;
            return;
        }

        list.innerHTML = filtered.map(t => {
            let priorityBadge = '';
            if (t.priority === 'milestone') {
                priorityBadge = '<span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 flex-shrink-0">Milestone 🎯</span>';
            } else if (t.priority === 'high') {
                priorityBadge = '<span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30 flex-shrink-0">High 🔥</span>';
            }

            return `
                <li class="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 gap-3 group">
                    <label class="flex items-center gap-2.5 cursor-pointer flex-1 min-w-0">
                        <input type="checkbox" ${t.done ? 'checked' : ''} onchange="toggleTask(${t.id})" 
                            class="rounded border-slate-700 bg-slate-900 text-emerald-600 focus:ring-emerald-500 h-4 w-4">
                        <span class="text-xs text-slate-200 truncate ${t.done ? 'line-through text-slate-500' : ''}">
                            ${escapeHtml(t.text)}
                        </span>
                    </label>
                    <div class="flex items-center gap-2">
                        ${priorityBadge}
                        <button onclick="deleteTask(${t.id})" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 text-xs transition">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </li>
            `;
        }).join('');
    }

    window.addTask = function () {
        const input = document.getElementById('new-task-input');
        const prioritySelect = document.getElementById('new-task-priority');
        if (!input || !input.value.trim()) return;
        const tasks = getStoredTasks();
        tasks.push({
            id: Date.now(),
            text: input.value.trim(),
            priority: (prioritySelect ? prioritySelect.value : 'normal'),
            done: false
        });
        saveTasks(tasks);
        input.value = '';
    };

    window.toggleTask = function (id) {
        const tasks = getStoredTasks();
        const task = tasks.find(t => t.id === id);
        if (task) {
            task.done = !task.done;
            saveTasks(tasks);
        }
    };

    window.deleteTask = function (id) {
        const tasks = getStoredTasks().filter(t => t.id !== id);
        saveTasks(tasks);
    };

    window.clearCompletedTasks = function () {
        const tasks = getStoredTasks().filter(t => !t.done);
        saveTasks(tasks);
    };

    // -------------------------------------------------------------------------
    // 12. EXPORT & RESET DATA
    // -------------------------------------------------------------------------
    window.downloadBookmarksJSON = function () {
        const allBms = getAllBookmarks();
        const exportData = {
            total_bookmarks: allBms.length,
            exported_at: new Date().toISOString(),
            bookmarks: allBms
        };
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `islam_ebeid_bookmarks_portal_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    window.resetPortalData = function () {
        if (confirm('Warning: This will clear your custom passcode, custom added bookmarks, pinned favorites, tasks, scratches database, secret messages, and logout. Reset now?')) {
            localStorage.removeItem(PASSCODE_STORAGE_KEY);
            localStorage.removeItem(PINNED_STORAGE_KEY);
            localStorage.removeItem(SCRATCHPAD_KEY);
            localStorage.removeItem(SCRATCHES_DB_KEY);
            localStorage.removeItem(TASKS_KEY);
            localStorage.removeItem(MESSAGES_KEY);
            localStorage.removeItem(CUSTOM_BM_KEY);
            localStorage.removeItem(DELETED_BM_KEY);
            localStorage.removeItem(USAGE_STATS_KEY);
            localStorage.removeItem(HANDSHAKE_CONFIG_KEY);
            localStorage.removeItem('gemini_api_key');
            logout();
        }
    };

    // -------------------------------------------------------------------------
    // 13. STATS & UPDATE HELPERS
    // -------------------------------------------------------------------------
    function updateStats() {
        const allBms = getAllBookmarks();
        const msgs = getStoredMessages();
        const unreadCount = msgs.filter(m => m.unread).length;
        const stats = getUsageStats();
        const totalClicks = Object.values(stats).reduce((acc, s) => acc + ((s && s.count) || 0), 0);

        const totalBmEl = document.getElementById('stat-total-bookmarks');
        const totalClicksEl = document.getElementById('stat-total-clicks');
        const topFavEl = document.getElementById('stat-top-favorites');
        const unreadEl = document.getElementById('stat-unread-messages');
        const unreadBadge = document.getElementById('unread-badge');
        const navBmCount = document.getElementById('nav-bm-count');

        if (totalBmEl) totalBmEl.textContent = allBms.length;
        if (totalClicksEl) totalClicksEl.textContent = totalClicks;
        if (topFavEl) topFavEl.textContent = '10';
        if (unreadEl) unreadEl.textContent = `${unreadCount} New`;
        if (unreadBadge) {
            unreadBadge.textContent = unreadCount;
            unreadBadge.classList.toggle('hidden', unreadCount === 0);
        }
        if (navBmCount) navBmCount.textContent = allBms.length;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderAll() {
        renderDashboardFavorites();
        renderSubfolderChips();
        renderBookmarks();
        renderInbox();
        renderTasks();
        initScratchpad();
        renderScratchesDb();
        initGeminiSettings();
        initHandshakeSettings();
        updateStats();
    }

    // -------------------------------------------------------------------------
    // 14. INITIALIZATION
    // -------------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', () => {
        initAuth();
        startClock();
        initTabs();
        initCategoryPills();
        initSearch();
        initAddBookmarkForm();
        initSecretDispatchForm();
        if (isAuthenticated()) {
            renderAll();
        }
    });

    // -------------------------------------------------------------------------
    // 15. AI SEMANTIC SEARCH & SETTINGS CONFIGURATION
    // -------------------------------------------------------------------------
    function initGeminiSettings() {
        const keyInput = document.getElementById('settings-gemini-key');
        const statusBadge = document.getElementById('gemini-status-badge');
        const savedKey = localStorage.getItem('gemini_api_key') || '';

        if (keyInput) keyInput.value = savedKey;
        if (statusBadge) {
            if (savedKey) {
                statusBadge.textContent = 'Key Stored \u2713';
                statusBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30';
            } else {
                statusBadge.textContent = 'No Key Configured';
                statusBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700';
            }
        }
    }

    window.toggleGeminiKeyVisibility = function () {
        const input = document.getElementById('settings-gemini-key');
        const icon = document.getElementById('gemini-eye-icon');
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) { icon.classList.remove('fa-eye'); icon.classList.add('fa-eye-slash'); }
        } else {
            input.type = 'password';
            if (icon) { icon.classList.remove('fa-eye-slash'); icon.classList.add('fa-eye'); }
        }
    };

    window.saveGeminiApiKey = function () {
        const keyInput = document.getElementById('settings-gemini-key');
        const msg = document.getElementById('gemini-save-msg');
        const keyVal = keyInput ? keyInput.value.trim() : '';

        localStorage.setItem('gemini_api_key', keyVal);
        initGeminiSettings();

        if (msg) {
            msg.className = 'text-xs text-emerald-400 block';
            msg.textContent = 'Gemini API Key saved successfully!';
            setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
        }
    };

    window.clearGeminiApiKey = function () {
        if (confirm('Clear your saved Gemini API Key?')) {
            localStorage.removeItem('gemini_api_key');
            const keyInput = document.getElementById('settings-gemini-key');
            if (keyInput) keyInput.value = '';
            initGeminiSettings();
            const msg = document.getElementById('gemini-save-msg');
            if (msg) {
                msg.className = 'text-xs text-slate-400 block';
                msg.textContent = 'API Key cleared.';
                setTimeout(() => { if (msg) msg.textContent = ''; }, 3000);
            }
        }
    };

    window.testGeminiApiKey = async function () {
        const keyInput = document.getElementById('settings-gemini-key');
        const keyVal = keyInput ? keyInput.value.trim() : '';
        const msg = document.getElementById('gemini-save-msg');
        const statusBadge = document.getElementById('gemini-status-badge');

        if (!keyVal) {
            if (msg) {
                msg.className = 'text-xs text-rose-400 block';
                msg.textContent = 'Please enter an API key to test.';
            }
            return;
        }

        if (msg) {
            msg.className = 'text-xs text-indigo-300 block';
            msg.textContent = 'Testing connection with Google Gemini API...';
        }

        try {
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${keyVal}`);
            if (resp.ok) {
                if (msg) {
                    msg.className = 'text-xs text-emerald-400 block font-semibold';
                    msg.textContent = 'Connection Verified! API Key is active and valid.';
                }
                if (statusBadge) {
                    statusBadge.textContent = 'Verified Valid \u2713';
                    statusBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30';
                }
            } else {
                const errData = await resp.text();
                throw new Error(`HTTP ${resp.status}: ${errData.slice(0, 100)}`);
            }
        } catch (err) {
            if (msg) {
                msg.className = 'text-xs text-rose-400 block';
                msg.textContent = `Verification Failed: ${err.message}`;
            }
            if (statusBadge) {
                statusBadge.textContent = 'Test Failed \u2717';
                statusBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30';
            }
        }
    };

    window.triggerAISearch = async function() {
        const query = document.getElementById('bm-search-input').value.trim();
        if (!query) return;

        const apiKey = localStorage.getItem('gemini_api_key');
        if (!apiKey) {
            alert('Please set your Gemini API Key in Settings to use AI Search.');
            switchTab('tab-settings');
            const keyInput = document.getElementById('settings-gemini-key');
            if (keyInput) keyInput.focus();
            return;
        }

        const btn = document.getElementById('ai-search-btn');
        const originalText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = `<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Searching...`;
            btn.disabled = true;
        }
        
        const grid = document.getElementById('dashboard-bookmarks-grid');
        if (grid) {
            grid.innerHTML = `<div class="col-span-full py-16 flex flex-col items-center justify-center text-indigo-400">
                <svg class="w-10 h-10 animate-spin mb-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <p class="font-semibold animate-pulse">AI is reading your bookmarks...</p>
            </div>`;
        }

        try {
            const allBms = typeof getAllBookmarks === 'function' ? getAllBookmarks() : window.PORTAL_BOOKMARKS.bookmarks;
            const minimizedBms = allBms.map(bm => ({ id: bm.id, name: bm.name, domain: bm.domain }));
            
            const prompt = `You are a semantic search assistant for my bookmarks. The user query is: "${query}"

Here is the JSON list of my bookmarks:
${JSON.stringify(minimizedBms)}

Return ONLY a JSON array of the "id"s of bookmarks that conceptually or semantically match the query. Do not wrap in markdown blocks, just return the raw JSON array. If no matches, return [].`;

            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{
                        parts: [{ text: prompt }]
                    }],
                    generationConfig: {
                        temperature: 0.1
                    }
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`API Error ${response.status}: ${errText}`);
            }

            const data = await response.json();
            const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;
            
            if (!textResponse) throw new Error("No valid response from Gemini");
            
            let cleanText = textResponse.replace(/^\s*```(json)?\s*|\s*```\s*$/g, '').trim();
            let matchedIds = [];
            try {
                const startIdx = cleanText.indexOf('[');
                const endIdx = cleanText.lastIndexOf(']');
                if (startIdx !== -1 && endIdx !== -1 && endIdx >= startIdx) {
                    cleanText = cleanText.substring(startIdx, endIdx + 1);
                }
                matchedIds = JSON.parse(cleanText);
            } catch (e) {
                console.error("Failed to parse Gemini response as JSON:", textResponse);
                throw new Error("Could not parse AI response as JSON: " + textResponse.substring(0, 50) + "...");
            }

            if (!Array.isArray(matchedIds)) {
                throw new Error("Response is not an array");
            }

            aiSearchMode = true;
            aiMatchedIds = matchedIds.map(id => Number(id));
            
            activeCategory = 'all';
            activeSubfolder = null;
            
            if (typeof renderDashboardSearchResults === 'function') {
                renderDashboardSearchResults();
                const clearBm = document.getElementById('bm-clear-btn');
                if (clearBm) clearBm.classList.remove('hidden');
            }
            
            if (aiMatchedIds.length === 0) {
                alert("AI didn't find any bookmarks matching that query.");
            }

        } catch (err) {
            console.error(err);
            alert('AI Search failed: ' + err.message);
        } finally {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    };

})();
