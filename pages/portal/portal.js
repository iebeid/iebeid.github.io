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
    const TASKS_KEY = 'portal_tasks_list';
    const MESSAGES_KEY = 'portal_messages_list';
    const CUSTOM_BM_KEY = 'portal_custom_bookmarks';
    const DELETED_BM_KEY = 'portal_deleted_bookmarks';
    const USAGE_STATS_KEY = 'portal_usage_stats';

    let activeCategory = 'all';
    let activeSubfolder = null;
    let activeDashFilter = 'all';
    let searchQuery = '';
    let aiSearchMode = false;
    let aiMatchedIds = [];
    let selectedMessageId = null;

    // Seed Messages (Academic, grant, and student inquiries)
    const SEED_MESSAGES = [
        {
            id: 1,
            sender: "Dr. Sarah Lin",
            email: "slin@mit.edu",
            subject: "Potential Collab: Multimodal Medical Segmentation & Auto-prompting",
            date: "Oct 22, 2026",
            tag: "Research Collab",
            unread: true,
            starred: true,
            body: `Dear Dr. Ebeid,\n\nI read your recent work on foundation models for medical image segmentation and your newly awarded NSF grant with great interest. Our laboratory at MIT is currently developing complementary prompt-tuning pipelines for high-throughput radiology datasets.\n\nWe would love to discuss a potential joint workshop submission for CVPR or IEEE BIBM, and perhaps explore whether our pre-trained encoders could integrate with your directed graph convolutional framework.\n\nWould you be open to a brief 20-minute Zoom call sometime next week?\n\nWarm regards,\nDr. Sarah Lin\nAssociate Professor, Department of EECS, MIT`
        },
        {
            id: 2,
            sender: "Alexandria Morales",
            email: "amorales@twu.edu",
            subject: "Inquiry regarding Undergraduate Research in Data2AI4LifeSciences Lab",
            date: "Oct 21, 2026",
            tag: "Student Mentorship",
            unread: true,
            starred: false,
            body: `Hello Dr. Ebeid,\n\nI am a junior Computer Science major at TWU enrolled in your database course. I am very interested in bioinformatics and machine learning, and I saw on your faculty page that your research group works with graph neural networks on protein structures.\n\nCould I schedule a time during your office hours to ask about potential undergraduate research assistant positions or independent study opportunities for Spring 2027?\n\nThank you for your time and guidance!\n\nAlexandria Morales\nB.S. in Computer Science Candidate, TWU`
        },
        {
            id: 3,
            sender: "Program Director (NSF CISE)",
            email: "cise-program@nsf.gov",
            subject: "NSF CISE/CCF PI Meeting & Grant Reporting Schedule",
            date: "Oct 19, 2026",
            tag: "Grant Operations",
            unread: true,
            starred: true,
            body: `Dear Dr. Ebeid,\n\nCongratulations again on your collaborative award under the CCF/CISE program. This is an informational reminder that the annual PI meeting will be held in Alexandria, VA in late spring.\n\nPlease ensure your preliminary project milestones and student support reporting protocols are updated in Research.gov.\n\nSincerely,\nDivision of Computing and Communication Foundations\nNational Science Foundation`
        },
        {
            id: 4,
            sender: "Dr. Tarek Mansour",
            email: "tmansour@cairo.edu.eg",
            subject: "Invitation: Keynote Session on AI in Drug Discovery",
            date: "Oct 15, 2026",
            tag: "Keynote / Invited Talk",
            unread: false,
            starred: false,
            body: `Dear Dr. Islam,\n\nI hope this email finds you well. The organizing committee of the International Conference on Bioinformatics and Computational Health Systems in Cairo would be honored to host you as an invited keynote speaker this December.\n\nGiven your extensive expertise across entity resolution, structural proteomics, and foundation models, your presentation would be invaluable to our faculty and graduate students.\n\nPlease let us know if your schedule might accommodate this invitation.\n\nBest regards,\nProf. Tarek Mansour\nFaculty of Computers and Artificial Intelligence`
        }
    ];

    // -------------------------------------------------------------------------
    // 2. AUTHENTICATION & SECURITY
    // -------------------------------------------------------------------------
    function getStoredPasscode() {
        return localStorage.getItem(PASSCODE_STORAGE_KEY) || DEFAULT_PASSCODE;
    }

    function isAuthenticated() {
        return sessionStorage.getItem(AUTH_SESSION_KEY) === 'authenticated' ||
               localStorage.getItem(AUTH_SESSION_KEY) === 'authenticated';
    }

    function authenticate(passcode, remember) {
        const correct = getStoredPasscode();
        if (passcode === correct) {
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
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const entered = passInput.value.trim();
                if (authenticate(entered, rememberMe.checked)) {
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
        if (window.PORTAL_BOOKMARKS && Array.isArray(window.PORTAL_BOOKMARKS.bookmarks)) {
            baseList = window.PORTAL_BOOKMARKS.bookmarks;
        }
        const custom = getCustomBookmarks();
        const deletedSet = new Set(getDeletedBookmarkIds());
        
        // Merge base + custom, filtering out deleted bookmarks
        const combined = [...custom, ...baseList].filter(bm => !deletedSet.has(bm.id));
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
        renderDashboardDailyDrivers();
        renderBookmarks();
        updateStats();
    }
    window.togglePin = togglePin;

    // Smart Launch Tracker: records click frequency and updates Quick Access
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

        // Immediately update views to reflect new usage ranking
        setTimeout(() => {
            renderDashboardDailyDrivers();
            renderBookmarks();
        }, 100);
    }
    window.trackLaunch = trackLaunch;

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
    // 7. RENDER DASHBOARD (DAILY DRIVERS & AUTO-LEARNED FREQUENT BOOKMARKS)
    // -------------------------------------------------------------------------
    function renderDashboardDailyDrivers() { return; }

    // -------------------------------------------------------------------------
    // 8. RENDER BOOKMARKS EXPLORER (The 4 Top Folders: Work, Life, Tools, Dashboard)
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

    function renderBookmarks() {
        const grid = document.getElementById('bookmarks-grid');
        const countLabel = document.getElementById('results-count-label');
        const noResults = document.getElementById('no-results-msg');
        if (!grid) return;

        const allBms = getAllBookmarks();
        const pinnedIds = getPinnedIds();
        const query = searchQuery.toLowerCase().trim();

        const filtered = allBms.filter(bm => {
            // Category check (Work, Life, Tools, Dashboard, or pinned)
            if (activeCategory === 'pinned') {
                if (!pinnedIds.includes(bm.id)) return false;
            } else if (activeCategory !== 'all') {
                if (bm.category !== activeCategory) return false;
            }

            // Subfolder check
            if (activeSubfolder) {
                if (bm.subfolder !== activeSubfolder) return false;
            }

            // Search query check
            if (aiSearchMode) {
                if (!aiMatchedIds.includes(bm.id)) return false;
            } else if (query) {
                const matchName = bm.name && bm.name.toLowerCase().includes(query);
                const matchUrl = bm.url && bm.url.toLowerCase().includes(query);
                const matchDomain = bm.domain && bm.domain.toLowerCase().includes(query);
                const matchPath = bm.path && bm.path.toLowerCase().includes(query);
                if (!matchName && !matchUrl && !matchDomain && !matchPath) return false;
            }

            return true;
        });

        countLabel.textContent = `Showing ${filtered.length} of ${allBms.length} bookmarks`;

        if (filtered.length === 0) {
            grid.innerHTML = '';
            noResults.classList.remove('hidden');
            return;
        }

        noResults.classList.add('hidden');

        grid.innerHTML = filtered.map(bm => {
            const isPinned = pinnedIds.includes(bm.id);
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const count = getBookmarkUsageCount(bm.id);

            // Category badge color
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
                            ${highlightQuery(escapeHtml(bm.name), query)}
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

    function highlightQuery(text, query) {
        if (!query) return text;
        const re = new RegExp(`(${query.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')})`, 'gi');
        return text.replace(re, '<mark class="bg-sky-500/30 text-sky-200 px-0.5 rounded">$1</mark>');
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

            renderBookmarks();
        }

        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => {
                onSearchInput(e.target.value);
                if (e.target.value && document.getElementById('tab-bookmarks').classList.contains('hidden')) {
                    switchTab('tab-bookmarks');
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
                if (globalSearch) {
                    globalSearch.focus();
                    globalSearch.select();
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 10. MESSAGE HUB & INBOX
    // -------------------------------------------------------------------------
    function getStoredMessages() {
        const stored = localStorage.getItem(MESSAGES_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        localStorage.setItem(MESSAGES_KEY, JSON.stringify(SEED_MESSAGES));
        return SEED_MESSAGES;
    }

    function saveMessages(msgs) {
        localStorage.setItem(MESSAGES_KEY, JSON.stringify(msgs));
        renderInbox();
        updateStats();
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
                   m.body.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            listEl.innerHTML = `<div class="p-8 text-center text-xs text-slate-500">No messages found.</div>`;
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

        document.getElementById('msg-subject').textContent = msg.subject;
        document.getElementById('msg-sender').textContent = msg.sender;
        document.getElementById('msg-email').textContent = msg.email;
        document.getElementById('msg-date').textContent = msg.date;
        document.getElementById('msg-tag').textContent = msg.tag;
        document.getElementById('msg-body').textContent = msg.body;
        document.getElementById('msg-avatar').textContent = msg.sender.split(' ').map(n => n[0]).join('').slice(0, 2);

        const replyLink = document.getElementById('msg-reply-link');
        replyLink.href = `mailto:${msg.email}?subject=Re: ${encodeURIComponent(msg.subject)}`;

        const starBtn = document.getElementById('msg-star-btn');
        starBtn.innerHTML = `<i class="${msg.starred ? 'fas' : 'far'} fa-star"></i>`;
        starBtn.onclick = () => {
            msg.starred = !msg.starred;
            saveMessages(msgs);
            renderMessageDetail(msg.id);
        };

        const deleteBtn = document.getElementById('msg-delete-btn');
        deleteBtn.onclick = () => {
            const updated = msgs.filter(m => m.id !== msg.id);
            selectedMessageId = null;
            saveMessages(updated);
            renderMessageDetail(null);
        };
    }

    window.refreshInbox = function () {
        renderInbox();
        const btn = document.querySelector('[title="Refresh Inbox"] i');
        if (btn) {
            btn.classList.add('fa-spin');
            setTimeout(() => btn.classList.remove('fa-spin'), 600);
        }
    };

    window.openFormIntegrationModal = function () {
        const modal = document.getElementById('form-integration-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeFormIntegrationModal = function () {
        const modal = document.getElementById('form-integration-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    // -------------------------------------------------------------------------
    // 11. SCRATCHPAD & TASKS
    // -------------------------------------------------------------------------
    function initScratchpad() {
        const dashScratch = document.getElementById('dashboard-scratchpad');
        const fullScratch = document.getElementById('full-scratchpad');
        const saveStatus = document.getElementById('scratch-save-status');

        const saved = localStorage.getItem(SCRATCHPAD_KEY) || '';
        if (dashScratch) dashScratch.value = saved;
        if (fullScratch) fullScratch.value = saved;

        function save(val) {
            localStorage.setItem(SCRATCHPAD_KEY, val);
            if (dashScratch && dashScratch.value !== val) dashScratch.value = val;
            if (fullScratch && fullScratch.value !== val) fullScratch.value = val;
            if (saveStatus) {
                saveStatus.textContent = 'Saved just now';
                setTimeout(() => { if (saveStatus) saveStatus.textContent = 'Auto-saved'; }, 2000);
            }
        }

        if (dashScratch) dashScratch.addEventListener('input', (e) => save(e.target.value));
        if (fullScratch) fullScratch.addEventListener('input', (e) => save(e.target.value));
    }

    window.clearScratchpad = function () {
        if (confirm('Are you sure you want to clear your scratchpad?')) {
            localStorage.removeItem(SCRATCHPAD_KEY);
            const dashScratch = document.getElementById('dashboard-scratchpad');
            const fullScratch = document.getElementById('full-scratchpad');
            if (dashScratch) dashScratch.value = '';
            if (fullScratch) fullScratch.value = '';
        }
    };

    // Task List Logic
    function getStoredTasks() {
        const stored = localStorage.getItem(TASKS_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        const initialTasks = [
            { id: 1, text: "Review NSF project milestone deliverables for student research assistants", done: false },
            { id: 2, text: "Finalize revision comments for Frontiers in Bioinformatics ProtGram manuscript", done: true },
            { id: 3, text: "Upload CSCI modern coursework lab assignments to Canvas", done: false }
        ];
        localStorage.setItem(TASKS_KEY, JSON.stringify(initialTasks));
        return initialTasks;
    }

    function saveTasks(tasks) {
        localStorage.setItem(TASKS_KEY, JSON.stringify(tasks));
        renderTasks();
    }

    function renderTasks() {
        const list = document.getElementById('task-list');
        if (!list) return;
        const tasks = getStoredTasks();

        list.innerHTML = tasks.map(t => `
            <li class="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/60 gap-3 group">
                <label class="flex items-center gap-2.5 cursor-pointer flex-1 min-w-0">
                    <input type="checkbox" ${t.done ? 'checked' : ''} onchange="toggleTask(${t.id})" 
                        class="rounded border-slate-700 bg-slate-900 text-sky-600 focus:ring-sky-500 h-4 w-4">
                    <span class="text-xs text-slate-200 truncate ${t.done ? 'line-through text-slate-500' : ''}">
                        ${escapeHtml(t.text)}
                    </span>
                </label>
                <button onclick="deleteTask(${t.id})" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 text-xs transition">
                    <i class="fas fa-times"></i>
                </button>
            </li>
        `).join('');
    }

    window.addTask = function () {
        const input = document.getElementById('new-task-input');
        if (!input || !input.value.trim()) return;
        const tasks = getStoredTasks();
        tasks.push({
            id: Date.now(),
            text: input.value.trim(),
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
        if (confirm('Warning: This will clear your custom passcode, custom added bookmarks, pinned favorites, tasks, and logout. Reset now?')) {
            localStorage.removeItem(PASSCODE_STORAGE_KEY);
            localStorage.removeItem(PINNED_STORAGE_KEY);
            localStorage.removeItem(SCRATCHPAD_KEY);
            localStorage.removeItem(TASKS_KEY);
            localStorage.removeItem(MESSAGES_KEY);
            localStorage.removeItem(CUSTOM_BM_KEY);
            localStorage.removeItem(DELETED_BM_KEY);
            localStorage.removeItem(USAGE_STATS_KEY);
            logout();
        }
    };

    // -------------------------------------------------------------------------
    // 13. STATS & UPDATE HELPERS
    // -------------------------------------------------------------------------
    function updateStats() {
        const allBms = getAllBookmarks();
        const pinned = getPinnedIds();
        const msgs = getStoredMessages();
        const unreadCount = msgs.filter(m => m.unread).length;
        const dashCount = allBms.filter(b => b.category === 'Dashboard').length;

        const totalBmEl = document.getElementById('stat-total-bookmarks');
        const dashCountEl = document.getElementById('stat-dash-count');
        const pinnedEl = document.getElementById('stat-pinned-count');
        const unreadEl = document.getElementById('stat-unread-messages');
        const unreadBadge = document.getElementById('unread-badge');
        const navBmCount = document.getElementById('nav-bm-count');

        if (totalBmEl) totalBmEl.textContent = allBms.length;
        if (dashCountEl) dashCountEl.textContent = `${dashCount} Launchpad`;
        if (pinnedEl) pinnedEl.textContent = pinned.length;
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
        renderDashboardDailyDrivers();
        renderSubfolderChips();
        renderBookmarks();
        renderInbox();
        renderTasks();
        initScratchpad();
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
        if (isAuthenticated()) {
            renderAll();
        }
    });


    // -------------------------------------------------------------------------


    // -------------------------------------------------------------------------
    // 15. AI SEARCH & SETTINGS
    // -------------------------------------------------------------------------

    window.openSettingsModal = function() {
        const modal = document.getElementById('settings-modal');
        const keyInput = document.getElementById('settings-gemini-key');
        const savedKey = localStorage.getItem('gemini_api_key');
        if (savedKey) {
            keyInput.value = savedKey;
        }
        modal.classList.remove('hidden');
        // trigger reflow
        void modal.offsetWidth;
        modal.classList.remove('opacity-0');
        modal.classList.add('opacity-100');
    };

    window.closeSettingsModal = function() {
        const modal = document.getElementById('settings-modal');
        modal.classList.remove('opacity-100');
        modal.classList.add('opacity-0');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    };

    window.saveSettings = function() {
        const keyInput = document.getElementById('settings-gemini-key');
        localStorage.setItem('gemini_api_key', keyInput.value.trim());
        window.closeSettingsModal();
    };

    window.triggerAISearch = async function() {
        console.log("AI Search Button Clicked!");
        
        const query = document.getElementById('bm-search-input').value.trim();
        if (!query) return;

        const apiKey = localStorage.getItem('gemini_api_key');
        if (!apiKey) {
            alert('Please set your Gemini API Key in Settings to use AI Search.');
            window.openSettingsModal();
            return;
        }

        const btn = document.getElementById('ai-search-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = `<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Searching...`;
        btn.disabled = true;

        try {
            // Get all bookmarks locally
            const allBms = typeof getAllBookmarks === 'function' ? getAllBookmarks() : window.PORTAL_BOOKMARKS.bookmarks;
            // Minimize data to avoid huge token count
            const minimizedBms = allBms.map(bm => ({ id: bm.id, name: bm.name, domain: bm.domain }));
            
            const prompt = `You are a semantic search assistant for my bookmarks. The user query is: "${query}"

Here is the JSON list of my bookmarks:
${JSON.stringify(minimizedBms)}

Return ONLY a JSON array of the "id"s of bookmarks that conceptually or semantically match the query. Do not wrap in markdown blocks, just return the raw JSON array. If no matches, return [].`;

            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key=${apiKey}`, {
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
            
            // parse the raw text back to an array
            let cleanText = textResponse.replace(/^\s*```(json)?\s*|\s*```\s*$/g, '').trim();
            let matchedIds = [];
            try {
                // Find first [ and last ] to extract just the array
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

            // Set state and render
            aiSearchMode = true;
            aiMatchedIds = matchedIds.map(id => Number(id)); // ensure they are numbers
            
            console.log("AI matched IDs:", aiMatchedIds);
            
            // Re-render
            if (typeof renderBookmarks === 'function') {
                renderBookmarks();
                // Also update UI to show clear button
                const clearBm = document.getElementById('bm-clear-btn');
                if (clearBm) clearBm.classList.remove('hidden');
                
                // Force a render of subfolders/dash if needed
                if (typeof renderDashboardDailyDrivers === 'function') renderDashboardDailyDrivers();
                
            } else {
                alert("Error: renderBookmarks is not a function.");
            }
            
            if (aiMatchedIds.length === 0) {
                alert("AI didn't find any bookmarks matching that query.");
            }

        } catch (err) {
            console.error(err);
            
            // Diagnostic fallback if model not found
            if (err.message.includes("404")) {
                try {
                    const diagResponse = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
                    if (diagResponse.ok) {
                        const diagData = await diagResponse.json();
                        const availableModels = diagData.models
                            .filter(m => m.supportedGenerationMethods && m.supportedGenerationMethods.includes("generateContent"))
                            .map(m => m.name)
                            .join("\n");
                        const msg = `Model not found (404). But your key is valid! Available models for your key are:\n\n${availableModels}`;
                        try {
                            await navigator.clipboard.writeText(availableModels);
                            alert(msg + "\n\n(SUCCESS: This list has been automatically COPIED to your clipboard! You can just paste it to the AI.)");
                        } catch (cpErr) {
                            prompt(msg + "\n\nCopy the text below:", availableModels);
                        }
                        return;
                    }
                } catch (diagErr) {
                    console.error("Diagnostic failed", diagErr);
                }
            }
            
            alert('AI Search failed: ' + err.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };

})();
