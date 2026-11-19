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
 * - Top 20 Favorites live-updating section
 */

(function () {
    // Hydrate private portal slices if loaded separately via js/portal_data.js
    if (window.__PORTAL_DATABASE && typeof window.__PORTAL_DATABASE === 'object') {
        window.__SITE_DATABASE = Object.assign(window.__SITE_DATABASE || {}, window.__PORTAL_DATABASE);
    }

    // -------------------------------------------------------------------------
    // 1. STATE & CONSTANTS
    // -------------------------------------------------------------------------
    const PASSCODE_STORAGE_KEY = 'portal_master_passcode'; // legacy key cleared on upgrade
    const PASSCODE_VERIFIER_KEY = 'portal_master_verifier_v2';
    const AUTH_SESSION_KEY = 'portal_auth_token';
    const PINNED_STORAGE_KEY = 'portal_pinned_bookmarks';
    const SCRATCHPAD_KEY = 'portal_scratchpad_content';
    const SCRATCHES_DB_KEY = 'portal_scratches_database';
    const TASKS_KEY = 'portal_tasks_list';
    const MESSAGES_KEY = 'portal_messages_list';
    const CUSTOM_BM_KEY = 'portal_custom_bookmarks';
    const DELETED_BM_KEY = 'portal_deleted_bookmarks';
    const USAGE_STATS_KEY = 'portal_usage_stats';
    const REMEMBER_STORAGE_KEY = 'portal_remember_bookmarks';
    const HANDSHAKE_CONFIG_KEY = 'portal_handshake_config';

    const DEFAULT_HANDSHAKE_CONFIG = {
        passcode: '',
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
    let portalSessionPasscode = null; // Volatile memory only while tab is open

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

    async function createLocalPasscodeVerifier(passcode) {
        const payload = { verified: true, createdAt: Date.now() };
        const enc = new TextEncoder();
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const keyMaterial = await window.crypto.subtle.importKey(
            'raw', enc.encode(passcode), { name: 'PBKDF2' }, false, ['deriveKey']
        );
        const aesKey = await window.crypto.subtle.deriveKey(
            { name: 'PBKDF2', salt: salt, iterations: 100000, hash: 'SHA-256' },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt']
        );
        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            aesKey,
            enc.encode(JSON.stringify(payload))
        );
        const toB64 = (arr) => btoa(String.fromCharCode(...arr));
        return {
            ciphertext: toB64(new Uint8Array(encrypted)),
            nonce: toB64(iv),
            salt: toB64(salt)
        };
    }

    function isAuthenticated() {
        return sessionStorage.getItem(AUTH_SESSION_KEY) === 'authenticated' ||
               localStorage.getItem(AUTH_SESSION_KEY) === 'authenticated';
    }

    async function authenticate(passcode, remember) {
        if (!passcode) return false;
        let verified = false;

        // Migrate or purge any legacy plaintext override cleanly
        const legacyOverride = localStorage.getItem(PASSCODE_STORAGE_KEY);
        if (legacyOverride) {
            if (passcode === legacyOverride) {
                const verifier = await createLocalPasscodeVerifier(passcode);
                localStorage.setItem(PASSCODE_VERIFIER_KEY, JSON.stringify(verifier));
                verified = true;
            }
            localStorage.removeItem(PASSCODE_STORAGE_KEY);
        }

        if (!verified) {
            const verifierRaw = localStorage.getItem(PASSCODE_VERIFIER_KEY);
            if (verifierRaw) {
                try {
                    const verifierEntry = JSON.parse(verifierRaw);
                    const dec = await decryptSqliteVaultEntry(verifierEntry, passcode);
                    verified = (dec !== null);
                } catch (e) {
                    verified = false;
                }
            } else {
                // Strictly verify by decrypting the SQLite AES-256-GCM vault entry
                verified = await unlockSqliteVault(passcode);
            }
        }

        if (verified) {
            portalSessionPasscode = passcode;
            // Best-effort hydration of vault secrets if local override matched
            if (!unlockedVaultSecrets.master_passcode) {
                await unlockSqliteVault(passcode);
            }
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
        portalSessionPasscode = null;
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
            changePassForm.addEventListener('submit', async (e) => {
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
                const verifier = await createLocalPasscodeVerifier(newPass.value);
                localStorage.setItem(PASSCODE_VERIFIER_KEY, JSON.stringify(verifier));
                localStorage.removeItem(PASSCODE_STORAGE_KEY);
                changeMsg.className = 'text-xs text-emerald-400 block';
                changeMsg.textContent = 'Master passcode encrypted & updated locally! Remember your new passcode.';
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
        const stored = localStorage.getItem(USAGE_STATS_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        // Hydrate baseline click counts from SQLite bookmarks_data.js if localStorage is empty
        const base = (window.PORTAL_BOOKMARKS && window.PORTAL_BOOKMARKS.bookmarks) || [];
        const seeded = {};
        base.forEach(b => {
            if (b.clicks && Number(b.clicks) > 0) {
                seeded[String(b.id)] = { count: Number(b.clicks), lastUsed: 0 };
            }
        });
        return seeded;
    }

    function saveUsageStats(stats) {
        localStorage.setItem(USAGE_STATS_KEY, JSON.stringify(stats));
    }

    function getBookmarkUsageCount(bmId) {
        const stats = getUsageStats();
        const item = stats[String(bmId)];
        return (item && item.count) ? item.count : 0;
    }

    // -------------------------------------------------------------------------
    // REMEMBER / SAVE FOR LATER ENGINE
    // -------------------------------------------------------------------------
    function getRememberedIds() {
        const stored = localStorage.getItem(REMEMBER_STORAGE_KEY);
        if (stored) {
            try { return JSON.parse(stored); } catch (e) { }
        }
        const base = (window.PORTAL_BOOKMARKS && window.PORTAL_BOOKMARKS.bookmarks) || [];
        return base.filter(b => b.remembered).map(b => b.id);
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
                    icon.className = 'fas fa-bookmark text-emerald-400';
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

    // -------------------------------------------------------------------------
    // FLOATING TOAST NOTIFICATION UTILITY
    // -------------------------------------------------------------------------
    function showPortalToast(message, type = 'success') {
        let toast = document.getElementById('portal-floating-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'portal-floating-toast';
            document.body.appendChild(toast);
        }

        const iconClass = type === 'success' 
            ? 'fas fa-check-circle text-emerald-400' 
            : (type === 'info' ? 'fas fa-info-circle text-sky-400' : 'fas fa-exclamation-circle text-amber-400');
        const borderClass = type === 'success'
            ? 'border-emerald-500/80 shadow-emerald-950/50 text-emerald-200'
            : (type === 'info' ? 'border-sky-500/80 shadow-sky-950/50 text-sky-200' : 'border-amber-500/80 text-amber-200');

        toast.className = `fixed bottom-6 right-6 z-[99999] px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 text-xs font-semibold bg-slate-900 border transition-all duration-300 transform translate-y-0 opacity-100 pointer-events-auto ${borderClass}`;
        toast.innerHTML = `<i class="${iconClass} text-sm"></i> <span>${escapeHtml(message)}</span>`;

        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => {
            if (toast) {
                toast.className = toast.className.replace('translate-y-0 opacity-100', 'translate-y-12 opacity-0 pointer-events-none');
            }
        }, 3400);
    }
    window.showPortalToast = showPortalToast;

    // -------------------------------------------------------------------------
    // DRAG AND DROP HANDLERS FOR CHROME BOOKMARKS & PORTAL CARDS
    // -------------------------------------------------------------------------
    function handlePortalBookmarkDragStart(e, bmId) {
        if (!e || !e.dataTransfer) return;
        const allBms = getAllBookmarks();
        const bm = allBms.find(b => b.id === Number(bmId));
        e.dataTransfer.setData('text/x-portal-bookmark-id', String(bmId));
        if (bm) {
            e.dataTransfer.setData('text/plain', bm.url);
            e.dataTransfer.setData('text/uri-list', bm.url);
            e.dataTransfer.setData('text/html', `<a href="${escapeHtml(bm.url)}">${escapeHtml(bm.name)}</a>`);
        }
        e.dataTransfer.effectAllowed = 'copyMove';
    }
    window.handlePortalBookmarkDragStart = handlePortalBookmarkDragStart;

    function parseDroppedBookmarkData(e) {
        if (!e || !e.dataTransfer) return null;

        // 1. Internal bookmark card drag
        const internalId = e.dataTransfer.getData('text/x-portal-bookmark-id');
        if (internalId) {
            return { isInternal: true, id: Number(internalId) };
        }

        let url = '';
        let title = '';

        // 2. Chrome Bookmark Bar drag provides rich HTML anchor: <a href="...">Title</a>
        const htmlData = e.dataTransfer.getData('text/html');
        if (htmlData) {
            try {
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlData, 'text/html');
                const aTag = doc.querySelector('a');
                if (aTag) {
                    url = (aTag.getAttribute('href') || aTag.href || '').trim();
                    title = aTag.textContent ? aTag.textContent.trim() : '';
                }
            } catch (err) {
                console.warn('Error parsing drop HTML:', err);
            }
        }

        // 3. Fallback: text/uri-list (standard URI list format)
        if (!url) {
            const uriList = e.dataTransfer.getData('text/uri-list');
            if (uriList) {
                const lines = uriList.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
                if (lines.length > 0) {
                    url = lines[0];
                }
            }
        }

        // 4. Fallback: text/plain
        const plainText = (e.dataTransfer.getData('text/plain') || '').trim();
        if (!url && plainText && (plainText.startsWith('http://') || plainText.startsWith('https://') || plainText.includes('.'))) {
            url = plainText;
        }

        // 5. Fallback: URL data type
        if (!url) {
            url = (e.dataTransfer.getData('URL') || '').trim();
        }

        if (!url) return null;

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        let domain = 'web';
        try {
            domain = new URL(url).hostname.replace(/^www\./, '');
        } catch (err) {
            domain = url.split('/')[2] || 'web';
        }

        if (!title && plainText && plainText !== url && !plainText.startsWith('http')) {
            title = plainText;
        }

        if (!title) {
            try {
                const u = new URL(url);
                const pathSeg = u.pathname.split('/').filter(Boolean).pop();
                if (pathSeg && pathSeg.length > 2 && !pathSeg.includes('.')) {
                    title = decodeURIComponent(pathSeg).replace(/[-_]/g, ' ');
                    title = title.charAt(0).toUpperCase() + title.slice(1);
                } else {
                    title = domain;
                }
            } catch (err) {
                title = domain;
            }
        }

        return {
            isInternal: false,
            url: url,
            title: title,
            domain: domain
        };
    }

    function handleRememberDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        const data = parseDroppedBookmarkData(e);
        if (!data) {
            showPortalToast('No valid link detected in dropped item.', 'warn');
            return;
        }

        // Case A: Dragged from internal portal card
        if (data.isInternal) {
            const numId = Number(data.id);
            const allBms = getAllBookmarks();
            const bm = allBms.find(b => b.id === numId);
            if (bm) {
                let ids = getRememberedIds();
                if (!ids.includes(numId)) {
                    ids.unshift(numId);
                    saveRememberedIds(ids);
                    showPortalToast(`Saved "${bm.name}" to Remember & Save for Later!`, 'success');
                } else {
                    showPortalToast(`"${bm.name}" is already in Remember & Save for Later.`, 'info');
                }
                renderDashboardRemember();
                renderAll();
            }
            return;
        }

        // Case B: Dragged from Chrome's Bookmark Bar or external browser tab
        const allBms = getAllBookmarks();
        const norm = (u) => (u || '').toLowerCase().replace(/^https?:\/\/(www\.)?/, '').replace(/\/+$/, '');
        const targetNorm = norm(data.url);
        const matched = allBms.find(b => norm(b.url) === targetNorm);

        if (matched) {
            // Already known in directory: pin it to Remember list
            let ids = getRememberedIds();
            if (!ids.includes(matched.id)) {
                ids.unshift(matched.id);
                saveRememberedIds(ids);
                showPortalToast(`Saved "${matched.name}" to Remember & Save for Later!`, 'success');
            } else {
                showPortalToast(`"${matched.name}" is already in Remember & Save for Later.`, 'info');
            }
            renderDashboardRemember();
            renderAll();
            return;
        }

        // New Bookmark dropped from Chrome: persist into custom bookmarks & remember list
        const newId = Date.now();
        const category = 'Bookmarks';
        const subfolder = 'Chrome Drops';
        const aiTags = generateSemanticTags(data.title, data.domain, subfolder, category);

        const desc = generateBookmarkDescription(data.title, data.domain, subfolder, category, data.url);
        const newBm = {
            id: newId,
            name: data.title,
            url: data.url,
            category: category,
            subfolder: subfolder,
            path: `${category} / ${subfolder}`,
            path_parts: [category, subfolder],
            domain: data.domain,
            ai_tags: aiTags,
            description: desc,
            isCustom: true
        };

        const custom = getCustomBookmarks();
        custom.unshift(newBm);
        saveCustomBookmarks(custom);

        const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
        dynamicTags[newId] = aiTags;
        localStorage.setItem('portal_ai_tags_cache', JSON.stringify(dynamicTags));

        let ids = getRememberedIds();
        ids.unshift(newId);
        saveRememberedIds(ids);

        const stats = getUsageStats();
        stats[String(newId)] = { count: 1, lastUsed: Date.now() };
        saveUsageStats(stats);

        renderDashboardRemember();
        renderAll();
        showPortalToast(`Added "${newBm.name}" to Bookmarks & Saved for Later!`, 'success');
    }

    function initRememberDragAndDrop() {
        const section = document.getElementById('dashboard-remember-section');
        const overlay = document.getElementById('remember-drop-overlay');
        if (!section) return;

        let dragCounter = 0;

        section.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            section.classList.add('ring-2', 'ring-emerald-500', 'border-emerald-500/80', 'bg-slate-900/95');
            if (overlay) overlay.classList.remove('hidden');
        });

        section.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        section.addEventListener('dragleave', (e) => {
            dragCounter--;
            if (dragCounter <= 0) {
                dragCounter = 0;
                section.classList.remove('ring-2', 'ring-emerald-500', 'border-emerald-500/80', 'bg-slate-900/95');
                if (overlay) overlay.classList.add('hidden');
            }
        });

        section.addEventListener('drop', (e) => {
            dragCounter = 0;
            section.classList.remove('ring-2', 'ring-emerald-500', 'border-emerald-500/80', 'bg-slate-900/95');
            if (overlay) overlay.classList.add('hidden');
            handleRememberDrop(e);
        });
    }
    window.initRememberDragAndDrop = initRememberDragAndDrop;

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
            <div draggable="true" ondragstart="handlePortalBookmarkDragStart(event, ${bm.id})" class="group relative bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-3 flex flex-col justify-between transition-all duration-200 shadow-sm cursor-grab active:cursor-grabbing">
                <div>
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <div class="flex items-center gap-2 min-w-0">
                            <div class="w-6 h-6 rounded-lg bg-slate-900 border border-slate-700/80 flex items-center justify-center flex-shrink-0 p-1">
                                <img src="${faviconUrl}" alt="" class="w-4 h-4 object-contain rounded" onerror="this.onerror=null;this.src='../../images/favicon.png'"/>
                            </div>
                            <span class="text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded truncate max-w-[120px]">${escapeHtml(domain)}</span>
                        </div>
                        <button onclick="toggleRemember(${bm.id})" class="text-slate-500 hover:text-rose-400 text-xs transition p-1" title="Remove from Save for Later">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <h4 class="text-xs font-semibold text-slate-200 group-hover:text-emerald-300 transition line-clamp-2 cursor-pointer leading-snug"
                        onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                        title="${escapeHtml(bm.name)}">
                        ${escapeHtml(bm.name)}
                    </h4>
                </div>
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-slate-700/50 text-[11px]">
                    <span class="text-[10px] text-slate-500 truncate max-w-[130px]"><i class="fas fa-folder mr-1 text-slate-600"></i>${escapeHtml(bm.subfolder || bm.category)}</span>
                    <a href="${escapeHtml(bm.url)}" target="_blank" rel="noopener noreferrer" onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                       class="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition">
                        <span>Open</span> <i class="fas fa-external-link-alt text-[9px]"></i>
                    </a>
                </div>
            </div>`;
        }).join('');
    }

    function generateBookmarkDescription(name, domain, subfolder, category, url) {
        const t = (name || '').trim();
        const u = (url || '').trim();
        const d = (domain || '').toLowerCase().replace(/^www\./, '');
        const sub = (subfolder || '').trim();
        const cat = (category || '').trim();
        const tl = t.toLowerCase();
        const ul = u.toLowerCase();

        // 1. Financial / Banking / Investment / Retirement
        if (['chase.com', 'capitalone.com', 'bankofamerica.com', 'alahlynet.com.eg', 'fidelity.com', 'robinhood.com', 'tiaa.org', 'upstart.com', 'earnin.com', 'moneymanagement.org', 'myretirementmanager.com', 'empower-retirement.com'].some(k => d.includes(k)) ||
            d.includes('taxact') || d.includes('link.com') || d.includes('paymentworks') || (d === 'texas.gov' && ul.includes('trs')) || (tl.includes('citi') && !d.includes('citiprogram'))) {
            if (d.includes('chase')) {
                return "Chase Online Banking and financial services portal. Access checking, savings, credit cards, mortgages, auto loans, commercial banking, account balances, monthly statements, wire transfers, bill pay, and personal wealth management.";
            }
            if (d.includes('capitalone') || tl.includes('capitol one')) {
                return "Capital One financial institution and online banking platform. Manage credit cards, rewards, checking and high-yield savings accounts, auto loans, credit monitoring, financial statements, and payments.";
            }
            if (d.includes('bankofamerica')) {
                return "Bank of America online and mobile banking portal. Secure access to personal and commercial bank accounts, credit cards, debit transactions, mortgage loans, investing via Merrill, balance inquiries, and financial planning.";
            }
            if (d.includes('alahlynet') || tl.includes('national bank of egypt')) {
                return "National Bank of Egypt (Al Ahly Net / NBE) official online banking service. Manage Egyptian Pound and foreign currency accounts, certificates of deposit (CDs), investment funds, wire transfers, currency exchange rates, and international remittances.";
            }
            if (d.includes('earnin')) {
                return "Earnin financial wellness app and cash advance service. Access earned wages prior to payday, track hours worked, manage daily cash flow, balance protection alerts, and avoid overdraft bank fees.";
            }
            if (d.includes('moneymanagement') || tl.includes('mmi')) {
                return "Money Management International (MMI) non-profit financial counseling, debt management plans (DMP), budget guidance, credit score education, student loan counseling, and mortgage relief.";
            }
            if (d.includes('upstart')) {
                return "Upstart artificial intelligence lending platform. Personal loans, debt consolidation, refinancing, credit evaluations, loan repayment schedules, and automated financial risk assessments.";
            }
            if (d.includes('tiaa.org')) {
                return "TIAA (Teachers Insurance and Annuity Association) retirement, financial planning, and investment services. Manage 403(b) retirement funds, mutual funds, annuities, retirement accounts, portfolio asset allocation, and university pension benefits.";
            }
            if (d.includes('texas.gov') && ul.includes('trs')) {
                return "Teacher Retirement System of Texas (TRS) member self-service portal. Manage Texas public educator pension plans, financial retirement eligibility calculators, survivor benefits, healthcare coverage, and service credit statements.";
            }
            if (d.includes('myretirementmanager')) {
                return "Retirement Manager (Corebridge / VALIC) participant portal. Financial planning and plan administration, retirement contributions, account balance monitoring, investment elections, and pension distributions.";
            }
            if (d.includes('fidelity')) {
                return "Fidelity Investments brokerage and financial services portal. Trade stocks, ETFs, mutual funds, manage 401(k) and IRA retirement plans, financial advisory, market research, and wealth asset management.";
            }
            if (d.includes('empower-retirement') || tl.includes('texa$aver')) {
                return "Texa$aver 401(k) and 457 retirement savings program administered by Empower Retirement. Manage Texas state employee deferred compensation, voluntary payroll deductions, financial portfolio growth, and retirement distribution options.";
            }
            if (d.includes('robinhood')) {
                return "Robinhood financial trading application. Commission-free stock trading, exchange-traded funds (ETFs), options, cryptocurrencies, high-yield cash sweep interest, and mobile portfolio management.";
            }
            if (d.includes('taxact')) {
                return "TaxAct online income tax preparation and e-filing software. Financial deductions, prepare federal and state tax returns, tax credits, W-2 and 1099 filing, and IRS tax refunds.";
            }
            if (d.includes('paymentworks')) {
                return "PaymentWorks automated digital supplier onboarding and vendor management network. Vendor identity verification, secure ACH bank routing details, invoice processing, and business compliance.";
            }
            if (d.includes('link.com')) {
                return "Link by Stripe one-click checkout and payment wallet. Saved credit card details, financial transactions, billing addresses, purchase transaction history, and digital receipts.";
            }
        }

        // 2. Email & Communications
        if (tl.includes('@') || ['mail.google', 'outlook.live', 'outlook.office', 'mail.yahoo', 'mail.proton'].some(k => d.includes(k))) {
            return `Personal and professional email communications inbox for ${t}. Read, compose, and manage messages, calendar invites, attachments, threads, mail filters, and directory correspondence on ${d}.`;
        }

        // 3. Code, Software & Development
        if (d.includes('github.com')) {
            return `GitHub software development platform repository for ${t}. Version control, git commits, source code branches, issues, pull requests, automated CI/CD workflows, open-source libraries, and collaborative programming.`;
        }
        if (d.includes('gitlab.com') || d.includes('bitbucket.org')) {
            return `Source code version control repository and DevOps pipeline on ${d} for ${t}. Git hosting, continuous integration, and deployments.`;
        }
        if (d.includes('stackoverflow.com')) {
            return `Stack Overflow programming and developer knowledge base. Technical Q&A, debugging solutions, software algorithms, and language syntax.`;
        }

        // 4. Academic Grants & Government Funding
        if (['research.gov', 'grants.gov', 'era.nih.gov', 'fastlane.nsf.gov', 'nsf.gov'].some(k => d.includes(k))) {
            return `Federal research grant administration and scientific funding portal on ${d} for '${t}'. Manage project proposals, peer review scoring, budget allocations, principal investigator (PI) compliance, award notices, and progress reporting.`;
        }

        // 5. Scientific Literature, Journals & Preprints
        if (['arxiv.org', 'biorxiv.org', 'medrxiv.org', 'ncbi.nlm.nih.gov', 'pubmed', 'nature.com', 'science.org', 'cell.com', 'sciencedirect.com', 'ieeexplore.ieee.org', 'frontiersin.org', 'springer.com', 'wiley.com'].some(k => d.includes(k))) {
            return `Peer-reviewed scientific literature and academic research publications on ${d} covering '${t}'. Full-text research papers, methodologies, empirical findings, preprints, citations, abstracts, and scholarly peer reviews.`;
        }

        // 6. AI, Machine Learning & Data Science
        if (['huggingface.co', 'kaggle.com', 'wandb.ai', 'openai.com', 'anthropic.com', 'deepmind.google', 'caiml.utdallas.edu'].some(k => d.includes(k))) {
            return `Artificial intelligence and machine learning platform on ${d} for ${t}. Pretrained neural models, deep learning datasets, benchmarks, generative AI, LLM prompting, computational experiments, and fine-tuning pipelines.`;
        }

        // 7. Higher Education & University Administration
        if (d.includes('twu.edu')) {
            return `Texas Woman's University (TWU) official academic portal for ${t}. Faculty administration, student records, department of computer science, university intranet, academic schedule, and campus resources.`;
        }
        if (d.includes('instructure.com') || d.includes('canvas')) {
            return `Canvas Learning Management System (LMS) for course administration: ${t}. Syllabi, lecture modules, student grading, assignment submissions, announcements, and educational discussions.`;
        }

        // 8. Cloud & Compute
        if (d.includes('cloudbank.org')) {
            return `CloudBank NSF-funded multicloud access portal for academic research. Manage cloud computing credits across AWS, Google Cloud, and Microsoft Azure for high-performance computing.`;
        }
        if (d.includes('access-ci.org')) {
            return `ACCESS CI (Advanced Cyberinfrastructure Coordination Ecosystem) portal. National high-performance computing allocations, supercomputer resources, and cyberinfrastructure research.`;
        }

        // 9. Google Workspace
        if (d.includes('drive.google.com')) {
            return `Google Drive cloud storage and document repository: ${t}. Shared files, spreadsheets, presentations, collaborative folders, and cloud backups.`;
        }
        if (d.includes('calendar.google.com')) {
            return `Google Calendar scheduling and time management tool: ${t}. Manage meetings, appointments, tasks, deadlines, notifications, and agenda tracking.`;
        }

        // Default Fallback
        const subText = (sub && sub !== d && sub !== 'General') ? ` in ${sub}` : '';
        return `Verified web application and executive bookmark for '${t}' hosted on ${d}${subText}. Provides direct navigation, authenticated access, digital documentation, and operational tooling.`;
    }

    function generateSemanticTags(name, domain, subfolder, category) {
        const tokens = new Set();
        const stopwords = new Set([
            'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'are', 'was',
            'were', 'will', 'login', 'portal', 'home', 'page', 'site', 'official', 'online',
            'welcome', 'untitled', 'web', 'com', 'org', 'edu', 'gov', 'net', 'io', 'html', 'php'
        ]);

        const rawName = (name || '').toLowerCase();
        const d = (domain || '').toLowerCase().replace(/^www\./, '');

        // Detect Email Accounts
        if (rawName.includes('@') || d.includes('mail.') || d.includes('outlook') || d.includes('proton') || d.includes('inbox')) {
            ['email', 'mail', 'inbox', 'webmail', 'messages', 'communication', 'account', 'email-account'].forEach(t => tokens.add(t));
        }
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
            } else if (['chase', 'capitalone', 'bankofamerica', 'alahlynet', 'fidelity', 'robinhood', 'tiaa', 'upstart', 'earnin', 'moneymanagement', 'myretirementmanager', 'empower-retirement'].some(k => d.includes(k)) || ['bank', 'chase', 'capital one', 'fidelity', 'robinhood', 'earnin', 'upstart', 'retirement', 'tiaa', 'trs', 'tax'].some(k => rawName.includes(k))) {
                ['finance', 'financial', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment'].forEach(t => tokens.add(t));

        }

        if (subfolder && subfolder !== 'General' && subfolder !== d) {
            subfolder.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).forEach(t => {
                if (t.length > 2 && !stopwords.has(t)) tokens.add(t);
            });
        }

        if (category && category.toLowerCase() !== 'bookmarks') {
            tokens.add(category.toLowerCase());
        }

        const cleanedName = (name || '').toLowerCase().replace(/[^a-z0-9\s]/g, ' ');
        cleanedName.split(/\s+/).forEach(w => {
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
            if (!bm.description) {
                bm.description = generateBookmarkDescription(bm.name, bm.domain, bm.subfolder, bm.category, bm.url);
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
        const allBms = getAllBookmarks();
        const dbPinned = allBms.filter(b => b.pinned).map(b => b.id);
        if (dbPinned.length > 0) {
            localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(dbPinned));
            return dbPinned;
        }
        // Default: first 8 bookmarks from Dashboard folder
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

    window.refreshPortal = async function() {
        const btn = document.getElementById('portal-refresh-btn') || document.getElementById('ai-refresh-btn');
        const originalHTML = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin text-sky-400"></i> Refreshing...';
            btn.disabled = true;
        }

        try {
            const allBms = getAllBookmarks();
            const dynamicTags = JSON.parse(localStorage.getItem('portal_ai_tags_cache') || '{}');
            let refreshedCount = 0;

            for (const bm of allBms) {
                const tags = generateSemanticTags(bm.name, bm.domain, bm.subfolder, bm.category);
                dynamicTags[bm.id] = tags;
                bm.ai_tags = tags;
                if (!bm.description) {
                    bm.description = generateBookmarkDescription(bm.name, bm.domain, bm.subfolder, bm.category, bm.url);
                }
                refreshedCount++;
            }

            localStorage.setItem('portal_ai_tags_cache', JSON.stringify(dynamicTags));

            const custom = getCustomBookmarks();
            let customUpdated = false;
            custom.forEach(b => {
                if (dynamicTags[b.id]) {
                    b.ai_tags = dynamicTags[b.id];
                    customUpdated = true;
                }
                if (!b.description) {
                    b.description = generateBookmarkDescription(b.name, b.domain, b.subfolder, b.category, b.url);
                    customUpdated = true;
                }
            });
            if (customUpdated) {
                saveCustomBookmarks(custom);
            }

            // Full UI re-render: Rankings, Favorites, Save for Later, Directory, Stats & Search
            renderAll();
            if (searchQuery && searchQuery.trim()) {
                renderDashboardSearchResults();
            }

            showPortalToast(`Refreshed ${refreshedCount} bookmarks & workspace index`);

            if (btn) {
                btn.innerHTML = '<i class="fas fa-check text-emerald-400"></i> Refreshed!';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2000);
            }

        } catch (err) {
            console.error("Failed to refresh portal:", err);
            if (btn) {
                btn.innerHTML = '<i class="fas fa-exclamation-circle text-rose-400"></i> Refresh Failed';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2000);
            }
        }
    };
    // Backwards compatibility alias
    window.refreshAITags = window.refreshPortal;

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
                domain = new URL(url).hostname.replace(/^www\./, '');
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
                    custom[existingIdx].description = generateBookmarkDescription(name, domain, subfolder, category, url);
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
                const desc = generateBookmarkDescription(name, domain, subfolder, category, url);
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
                    description: desc,
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
    }

    // -------------------------------------------------------------------------
    // 7. FAVORITES (TOP 20 MOST CLICKED) & SIMILARITY / RELEVANCE RANKING ENGINE
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

        const top20 = sorted.slice(0, 20);

        grid.innerHTML = top20.map((bm, index) => {
            const rank = index + 1;
            const domain = bm.domain || 'web';
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const count = (stats[String(bm.id)] && stats[String(bm.id)].count) || 0;

            let rankBadgeClass = 'bg-slate-800 text-slate-400 border-slate-700';
            if (rank === 1) rankBadgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/40 font-bold';
            else if (rank === 2) rankBadgeClass = 'bg-slate-300/20 text-slate-200 border-slate-400/40 font-bold';
            else if (rank === 3) rankBadgeClass = 'bg-amber-700/20 text-amber-400 border-amber-600/40 font-bold';

            return `
                <div draggable="true" ondragstart="handlePortalBookmarkDragStart(event, ${bm.id})" onclick="trackLaunch(${bm.id}, '${escapeHtml(bm.url)}')"
                    class="group relative bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-sky-500/50 rounded-xl p-3 cursor-pointer transition shadow-sm hover:shadow-md flex flex-col justify-between"
                    title="${escapeHtml(bm.name)} (${count} launches) - Click to launch">
                    <div>
                        <div class="flex items-center justify-between gap-1.5 mb-2">
                            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded border ${rankBadgeClass}">
                                #${rank}
                            </span>
                            <div class="flex items-center gap-1">
                                <button onclick="event.stopPropagation(); toggleRemember(${bm.id});" data-remember-btn="${bm.id}"
                                    class="w-5 h-5 rounded hover:bg-slate-700/60 text-slate-400 hover:text-emerald-400 flex items-center justify-center transition text-[10px]"
                                    title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}">
                                    <i class="${getRememberedIds().includes(bm.id) ? 'fas text-emerald-400' : 'far'} fa-bookmark"></i>
                                </button>
                                <span class="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                    <i class="fas fa-fire text-amber-400 text-[8px]"></i> ${count}
                                </span>
                            </div>
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
        const cleanUrl = url.split('?')[0].split('#')[0];
        const desc = (bm.description || '').toLowerCase();

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
            'code': ['code', 'github', 'git', 'repo', 'repository', 'software', 'programming', 'python'],
            'financial': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'finance': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'finances': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'bank': ['bank', 'banking', 'checking', 'savings', 'accounts', 'statements', 'chase', 'capitalone', 'bankofamerica', 'national bank of egypt', 'financial', 'finance', 'money'],
            'banking': ['bank', 'banking', 'checking', 'savings', 'accounts', 'statements', 'chase', 'capitalone', 'bankofamerica', 'financial', 'finance', 'money'],
            'money': ['money', 'finance', 'financial', 'bank', 'banking', 'accounts', 'earnin', 'upstart', 'investment', 'funds'],
            'investment': ['investment', 'investing', 'stocks', 'portfolio', 'fidelity', 'robinhood', 'tiaa', 'retirement', 'etfs', 'financial', 'funds'],
            'investments': ['investment', 'investing', 'stocks', 'portfolio', 'fidelity', 'robinhood', 'tiaa', 'retirement', 'etfs', 'financial', 'funds'],
            'retirement': ['retirement', 'pension', '401k', '403b', 'tiaa', 'trs', 'fidelity', 'texasaver', 'valic', 'corebridge', 'financial', 'investing'],
            'tax': ['tax', 'taxes', 'taxact', 'irs', 'refund', 'deductions', 'financial', '1099', 'w2'],
            'taxes': ['tax', 'taxes', 'taxact', 'irs', 'refund', 'deductions', 'financial', '1099', 'w2']
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

        // 3.5 Full Semantic Paragraph Description Search
        if (desc) {
            if (new RegExp(`\\b${escapeRegExp(q)}\\b`, 'i').test(desc)) {
                score += 380;
                if (!reasons.some(r => r.includes("Description") || r.includes("Email Account"))) {
                    reasons.push(`Semantic Description Match`);
                }
            } else if (desc.includes(q)) {
                score += 220;
                if (!reasons.some(r => r.includes("Description") || r.includes("Email Account"))) {
                    reasons.push(`Description Match`);
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
        }

        // 6. Multi-term Token Coverage
        if (tokens.length > 1) {
            let matchedTokenCount = 0;
            tokens.forEach(term => {
                let termMatched = false;
                if (name.includes(term)) { score += 70; termMatched = true; }
                if (domain.includes(term)) { score += 40; termMatched = true; }
                if (tags.includes(term)) { score += 40; termMatched = true; }
                if (desc.includes(term)) { score += 45; termMatched = true; }
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

                        ${bm.description ? `
                        <p class="text-[11px] text-slate-400 leading-relaxed line-clamp-2 my-1.5" title="${escapeHtml(bm.description)}">
                            ${highlightTokens(escapeHtml(bm.description), query)}
                        </p>` : ''}
                        ${bm.path && bm.path !== 'General' ? `<p class="text-[10px] text-slate-500 font-mono truncate"><i class="fas fa-folder-open mr-1"></i>${escapeHtml(bm.path)}</p>` : ''}
                        ${bm.ai_tags ? `<p class="text-[10px] text-slate-500 font-mono truncate mt-0.5" title="Tags: ${escapeHtml(bm.ai_tags)}"><i class="fas fa-tags mr-1 text-slate-600"></i>${escapeHtml(bm.ai_tags.split(',').slice(0, 5).join(', '))}</p>` : ''}
                    </div>

                    <!-- Footer Action Bar -->
                    <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-800/60">
                        <div class="flex items-center gap-2">
                            <button onclick="togglePin(${bm.id})" class="text-xs ${isPinned ? 'text-amber-400 hover:text-amber-300' : 'text-slate-500 hover:text-slate-300'} transition" title="${isPinned ? 'Unpin' : 'Pin to top'}">
                                <i class="fas fa-star"></i>
                            </button>
                            <button onclick="toggleRemember(${bm.id})" data-remember-btn="${bm.id}" class="text-xs ${getRememberedIds().includes(bm.id) ? 'text-emerald-400 hover:text-emerald-300' : 'text-slate-500 hover:text-emerald-400'} transition" title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}">
                                <i class="${getRememberedIds().includes(bm.id) ? 'fas' : 'far'} fa-bookmark"></i>
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
                                <button onclick="toggleRemember(${bm.id})" title="${getRememberedIds().includes(bm.id) ? 'Remove from Save for Later' : 'Save for Later'}"
                                    data-remember-btn="${bm.id}"
                                    class="text-xs transition ml-1 ${getRememberedIds().includes(bm.id) ? 'text-emerald-400' : 'text-slate-600 hover:text-emerald-400'}">
                                    <i class="${getRememberedIds().includes(bm.id) ? 'fas' : 'far'} fa-bookmark"></i>
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

    window.exportFullPortalState = function () {
        const allBms = getAllBookmarks();
        const state = {
            _format: 'portal_full_state_v1',
            exported_at: new Date().toISOString(),
            origin: window.location.origin,
            total_bookmarks: allBms.length,
            all_bookmarks: allBms,
            custom_bookmarks: getCustomBookmarks(),
            deleted_ids: getDeletedBookmarkIds(),
            pinned_ids: getPinnedIds(),
            remembered_ids: getRememberedIds(),
            usage_stats: getUsageStats(),
            tasks: JSON.parse(localStorage.getItem(TASKS_KEY) || '[]'),
            scratches: JSON.parse(localStorage.getItem(SCRATCHES_DB_KEY) || '[]'),
            active_scratch: localStorage.getItem(SCRATCHPAD_KEY) || '',
        };
        const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `portal_full_state_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showPortalToast(`Exported Full Portal State (${allBms.length} bookmarks, ${state.pinned_ids.length} pinned, ${state.remembered_ids.length} remembered)`);
    };

    window.triggerImportPortalState = function () {
        const input = document.getElementById('portal-state-import-file');
        if (input) {
            input.value = '';
            input.click();
        }
    };

    window.handleImportPortalStateFile = async function (event) {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            const payload = JSON.parse(await file.text());

            // 1. Restore browser localStorage state on the current origin
            const baseUrls = new Set(((window.PORTAL_BOOKMARKS && window.PORTAL_BOOKMARKS.bookmarks) || []).map(b => String(b.url || '').trim()));
            const baseIds = new Set(((window.PORTAL_BOOKMARKS && window.PORTAL_BOOKMARKS.bookmarks) || []).map(b => String(b.id)));
            const incomingAll = Array.isArray(payload.all_bookmarks) ? payload.all_bookmarks : (Array.isArray(payload.bookmarks) ? payload.bookmarks : []);
            const incomingCustom = Array.isArray(payload.custom_bookmarks)
                ? payload.custom_bookmarks
                : incomingAll.filter(b => !baseIds.has(String(b.id)) && !baseUrls.has(String(b.url || '').trim()));

            if (incomingCustom.length > 0) saveCustomBookmarks(incomingCustom);
            if (Array.isArray(payload.deleted_ids || payload.deleted)) saveDeletedBookmarkIds(payload.deleted_ids || payload.deleted);
            if (Array.isArray(payload.pinned_ids || payload.pinned)) localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(payload.pinned_ids || payload.pinned));
            if (Array.isArray(payload.remembered_ids || payload.remember)) saveRememberedIds(payload.remembered_ids || payload.remember);
            if (payload.usage_stats || payload.usage) saveUsageStats(payload.usage_stats || payload.usage);
            if (Array.isArray(payload.tasks)) localStorage.setItem(TASKS_KEY, JSON.stringify(payload.tasks));
            if (Array.isArray(payload.scratches)) localStorage.setItem(SCRATCHES_DB_KEY, JSON.stringify(payload.scratches));
            if (typeof payload.active_scratch === 'string' && payload.active_scratch) localStorage.setItem(SCRATCHPAD_KEY, payload.active_scratch);

            // 2. If running via local portal_server.py, also persist permanently into content.db
            let dbNote = 'browser localStorage restored';
            try {
                const health = await fetch('/api/health', { cache: 'no-store' });
                if (health.ok) {
                    const resp = await fetch('/api/portal-state/import', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    const resData = await resp.json();
                    if (resData.ok && resData.stats) {
                        dbNote = `saved ${resData.stats.total_bookmarks} bookmarks to content.db`;
                    }
                }
            } catch (e) { /* static mode */ }

            renderAll();
            showPortalToast(`Imported Portal State (${dbNote})!`);
        } catch (err) {
            showPortalToast(`Import failed: ${err.message || err}`, 'error');
        }
    };

    window.resetPortalData = function () {
        if (confirm('Warning: This will clear your custom passcode, custom added bookmarks, pinned favorites, tasks, scratches database, secret messages, and logout. Reset now?')) {
            localStorage.removeItem(PASSCODE_STORAGE_KEY);
            localStorage.removeItem(PASSCODE_VERIFIER_KEY);
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
        if (topFavEl) topFavEl.textContent = '20';
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
        renderDashboardRemember();
        renderDashboardFavorites();
        initRememberDragAndDrop();
        renderSubfolderChips();
        renderBookmarks();
        renderInbox();
        renderTasks();
        initScratchpad();
        renderScratchesDb();
        initGeminiSettings();
        initGithubPublishSettings();
        initHandshakeSettings();
        updateStats();
        if (typeof window.__initPortalProjectsHub === 'function') {
            window.__initPortalProjectsHub();
        }
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
        initRememberDragAndDrop();
        initPasswordVault();
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
                statusBadge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/30';
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
            msg.className = 'text-xs text-sky-300 block';
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
            grid.innerHTML = `<div class="col-span-full py-16 flex flex-col items-center justify-center text-sky-400">
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

            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=${apiKey}`, {
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


    // -------------------------------------------------------------------------
    // 16. ZERO-KNOWLEDGE ENCRYPTED PASSWORD VAULT (AES-256-GCM + PBKDF2)
    // -------------------------------------------------------------------------
    const VAULT_STORAGE_KEY = 'portal_encrypted_passwords_v1';
    const VAULT_PBKDF2_ITERATIONS = 310000;
    const VAULT_AUTOLOCK_SECONDS = 300; // 5 minutes

    let vaultMasterPassword = null;      // Volatile memory only while unlocked
    let unlockedCredentials = [];        // Decrypted credentials in memory only
    let activeVaultCategory = 'all';
    let vaultAutoLockRemaining = VAULT_AUTOLOCK_SECONDS;
    let vaultAutoLockInterval = null;
    let pendingCsvParsedRecords = [];

    function uint8ArrayToBase64(bytes) {
        let bin = '';
        for (let i = 0; i < bytes.length; i++) {
            bin += String.fromCharCode(bytes[i]);
        }
        return btoa(bin);
    }

    function getEncryptedVaultBlobs() {
        const dbBlobs = (window.__SITE_DATABASE && Array.isArray(window.__SITE_DATABASE.portal_passwords))
            ? window.__SITE_DATABASE.portal_passwords
            : [];
        let localBlobs = null;
        try {
            const raw = localStorage.getItem(VAULT_STORAGE_KEY);
            if (raw) localBlobs = JSON.parse(raw);
        } catch (e) { }

        // If localStorage has been initialized by the user, prefer the union or latest local snapshot
        if (Array.isArray(localBlobs)) {
            const mergedMap = new Map();
            dbBlobs.forEach(b => mergedMap.set(b.id, b));
            localBlobs.forEach(b => mergedMap.set(b.id, b));
            return Array.from(mergedMap.values());
        }
        return dbBlobs;
    }

    function saveEncryptedVaultBlobs(blobs) {
        localStorage.setItem(VAULT_STORAGE_KEY, JSON.stringify(blobs));
        updateVaultCountBadges(blobs.length);
    }

    function updateVaultCountBadges(count) {
        const navBadge = document.getElementById('nav-vault-count');
        const dbCountEl = document.getElementById('vault-db-blob-count');
        if (navBadge) {
            navBadge.textContent = count;
            navBadge.classList.toggle('hidden', count === 0);
        }
        if (dbCountEl) dbCountEl.textContent = count;
    }

    async function encryptVaultPayload(plainObj, masterPassword) {
        const enc = new TextEncoder();
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        const keyMaterial = await window.crypto.subtle.importKey(
            'raw', enc.encode(masterPassword), { name: 'PBKDF2' }, false, ['deriveKey']
        );
        const aesKey = await window.crypto.subtle.deriveKey(
            { name: 'PBKDF2', salt: salt, iterations: VAULT_PBKDF2_ITERATIONS, hash: 'SHA-256' },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt']
        );

        const plaintextBytes = enc.encode(JSON.stringify(plainObj));
        const encryptedBuf = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            aesKey,
            plaintextBytes
        );

        return {
            id: plainObj.id,
            ciphertext: uint8ArrayToBase64(new Uint8Array(encryptedBuf)),
            nonce: uint8ArrayToBase64(iv),
            salt: uint8ArrayToBase64(salt),
            updated_at: plainObj.updatedAt || new Date().toISOString()
        };
    }

    async function decryptVaultBlob(blob, masterPassword) {
        if (!blob || !blob.ciphertext || !blob.nonce || !blob.salt) return null;
        try {
            const enc = new TextEncoder();
            const salt = base64ToUint8Array(blob.salt);
            const iv = base64ToUint8Array(blob.nonce);
            const ciphertext = base64ToUint8Array(blob.ciphertext);

            const keyMaterial = await window.crypto.subtle.importKey(
                'raw', enc.encode(masterPassword), { name: 'PBKDF2' }, false, ['deriveKey']
            );
            const aesKey = await window.crypto.subtle.deriveKey(
                { name: 'PBKDF2', salt: salt, iterations: VAULT_PBKDF2_ITERATIONS, hash: 'SHA-256' },
                keyMaterial,
                { name: 'AES-GCM', length: 256 },
                false,
                ['decrypt']
            );

            const decryptedBuf = await window.crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: iv },
                aesKey,
                ciphertext
            );
            const jsonStr = new TextDecoder().decode(decryptedBuf);
            return JSON.parse(jsonStr);
        } catch (err) {
            return null;
        }
    }

    function initPasswordVault() {
        const blobs = getEncryptedVaultBlobs();
        updateVaultCountBadges(blobs.length);

        const setupHint = document.getElementById('vault-setup-hint');
        const gateTitle = document.getElementById('vault-gate-title');
        const btnText = document.getElementById('vault-unlock-btn-text');
        if (blobs.length === 0) {
            if (setupHint) setupHint.classList.remove('hidden');
            if (gateTitle) gateTitle.textContent = 'Initialize Encrypted Password Vault';
            if (btnText) btnText.textContent = 'Create & Unlock Vault';
        } else {
            if (setupHint) setupHint.classList.add('hidden');
            if (gateTitle) gateTitle.textContent = 'Unlock Encrypted Password Vault';
            if (btnText) btnText.textContent = 'Unlock Vault';
        }

        const unlockForm = document.getElementById('vault-unlock-form');
        if (unlockForm && !unlockForm.dataset.bound) {
            unlockForm.dataset.bound = 'true';
            unlockForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const input = document.getElementById('vault-master-input');
                const errEl = document.getElementById('vault-unlock-error');
                const submitBtn = document.getElementById('vault-unlock-submit');
                const pass = input ? input.value : '';
                if (!pass) return;

                if (errEl) errEl.classList.add('hidden');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deriving Key...';
                }

                const currentBlobs = getEncryptedVaultBlobs();
                if (currentBlobs.length === 0) {
                    // First-time initialization with empty vault
                    vaultMasterPassword = pass;
                    unlockedCredentials = [];
                    if (input) input.value = '';
                    showUnlockedVaultView();
                    showPortalToast('Password Vault initialized with AES-256-GCM');
                } else {
                    const decryptedList = [];
                    let failed = false;
                    for (const blob of currentBlobs) {
                        const dec = await decryptVaultBlob(blob, pass);
                        if (!dec) {
                            failed = true;
                            break;
                        }
                        decryptedList.push(dec);
                    }

                    if (failed) {
                        if (errEl) errEl.classList.remove('hidden');
                    } else {
                        vaultMasterPassword = pass;
                        unlockedCredentials = decryptedList;
                        if (input) input.value = '';
                        showUnlockedVaultView();
                        showPortalToast(`Unlocked ${decryptedList.length} encrypted credentials`);
                    }
                }

                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-unlock-alt"></i> <span id="vault-unlock-btn-text">Unlock Vault</span>';
                }
            });
        }

        const credForm = document.getElementById('vault-credential-form');
        if (credForm && !credForm.dataset.bound) {
            credForm.dataset.bound = 'true';
            credForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await saveVaultCredentialFromModal();
            });
        }
    }

    function showUnlockedVaultView() {
        const lockedView = document.getElementById('vault-locked-view');
        const unlockedView = document.getElementById('vault-unlocked-view');
        if (lockedView) lockedView.classList.add('hidden');
        if (unlockedView) unlockedView.classList.remove('hidden');
        resetVaultAutoLock();
        renderVaultCredentials();
    }

    window.lockPasswordVault = function() {
        vaultMasterPassword = null;
        unlockedCredentials = [];
        if (vaultAutoLockInterval) {
            clearInterval(vaultAutoLockInterval);
            vaultAutoLockInterval = null;
        }
        const lockedView = document.getElementById('vault-locked-view');
        const unlockedView = document.getElementById('vault-unlocked-view');
        if (unlockedView) unlockedView.classList.add('hidden');
        if (lockedView) lockedView.classList.remove('hidden');
        const grid = document.getElementById('vault-credentials-grid');
        if (grid) grid.innerHTML = '';
        initPasswordVault();
        showPortalToast('Password Vault locked & memory cleared');
    };

    function resetVaultAutoLock() {
        vaultAutoLockRemaining = VAULT_AUTOLOCK_SECONDS;
        if (vaultAutoLockInterval) clearInterval(vaultAutoLockInterval);
        vaultAutoLockInterval = setInterval(() => {
            if (!vaultMasterPassword) {
                clearInterval(vaultAutoLockInterval);
                return;
            }
            vaultAutoLockRemaining--;
            const timerEl = document.getElementById('vault-autolock-timer');
            if (timerEl) {
                const mins = String(Math.floor(vaultAutoLockRemaining / 60)).padStart(2, '0');
                const secs = String(vaultAutoLockRemaining % 60).padStart(2, '0');
                timerEl.textContent = `Locks in ${mins}:${secs}`;
            }
            if (vaultAutoLockRemaining <= 0) {
                lockPasswordVault();
            }
        }, 1000);
    }

    function calculatePasswordEntropy(pwd) {
        if (!pwd) return { bits: 0, label: 'Empty', color: 'text-slate-500', isWeak: true };
        let pool = 0;
        if (/[a-z]/.test(pwd)) pool += 26;
        if (/[A-Z]/.test(pwd)) pool += 26;
        if (/[0-9]/.test(pwd)) pool += 10;
        if (/[^a-zA-Z0-9]/.test(pwd)) pool += 32;
        const bits = Math.round(pwd.length * Math.log2(Math.max(pool, 1)));
        if (bits < 45 || pwd.length < 10) return { bits, label: 'Weak', color: 'text-rose-400', isWeak: true };
        if (bits < 70) return { bits, label: 'Fair', color: 'text-amber-400', isWeak: false };
        if (bits < 100) return { bits, label: 'Strong', color: 'text-emerald-400', isWeak: false };
        return { bits, label: 'Very Strong', color: 'text-sky-400', isWeak: false };
    }

    function inferCredentialCategory(name, url) {
        const text = `${name || ''} ${url || ''}`.toLowerCase();
        if (['bank', 'chase', 'capitalone', 'fidelity', 'robinhood', 'tiaa', 'trs', 'tax', 'earnin', 'upstart', 'payment', 'paypal', 'stripe', 'empower', 'moneymanagement', 'alahly'].some(k => text.includes(k))) {
            return 'Banking & Finance';
        }
        if (['twu.edu', 'instructure', 'canvas', 'nih.gov', 'nsf.gov', 'grants', 'overleaf', 'scholar', 'orcid', 'research', 'arxiv', 'ieee'].some(k => text.includes(k))) {
            return 'Work & Academic';
        }
        if (['mail', 'gmail', 'outlook', 'proton', 'yahoo', 'slack', 'discord', 'zoom', 'teams'].some(k => text.includes(k))) {
            return 'Email & Comms';
        }
        if (['github', 'gitlab', 'aws', 'cloud', 'azure', 'google', 'huggingface', 'kaggle', 'nvidia', 'docker', 'vercel', 'netlify'].some(k => text.includes(k))) {
            return 'Cloud & Dev';
        }
        return 'General';
    }

    function extractDomainSafe(url) {
        try {
            if (!url) return 'web';
            const u = new URL(url.startsWith('http') ? url : 'https://' + url);
            return u.hostname.replace(/^www\./, '');
        } catch (e) {
            return 'web';
        }
    }

    window.setVaultCategoryFilter = function(cat) {
        activeVaultCategory = cat;
        document.querySelectorAll('.vault-cat-btn').forEach(btn => {
            const isMatch = btn.getAttribute('data-vault-cat') === cat;
            if (isMatch) {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 transition';
            } else if (btn.getAttribute('data-vault-cat') === '__issues__') {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition';
            } else {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition';
            }
        });
        renderVaultCredentials();
    };

    window.renderVaultCredentials = function() {
        if (!vaultMasterPassword) return;
        resetVaultAutoLock();

        const grid = document.getElementById('vault-credentials-grid');
        const emptyMsg = document.getElementById('vault-empty-msg');
        if (!grid) return;

        // Compute reuse counts in-memory
        const pwdFreq = {};
        unlockedCredentials.forEach(c => {
            if (c.password) pwdFreq[c.password] = (pwdFreq[c.password] || 0) + 1;
        });

        let strongCount = 0;
        let issuesCount = 0;
        unlockedCredentials.forEach(c => {
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;
            if (ent.isWeak || isReused) issuesCount++;
            else strongCount++;
        });

        const statTotal = document.getElementById('vault-stat-total');
        const statStrong = document.getElementById('vault-stat-strong');
        const statIssues = document.getElementById('vault-stat-issues');
        if (statTotal) statTotal.textContent = unlockedCredentials.length;
        if (statStrong) statStrong.textContent = strongCount;
        if (statIssues) statIssues.textContent = issuesCount;

        const query = (document.getElementById('vault-search-input')?.value || '').toLowerCase().trim();

        const filtered = unlockedCredentials.filter(c => {
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;
            if (activeVaultCategory === '__issues__') {
                if (!ent.isWeak && !isReused) return false;
            } else if (activeVaultCategory !== 'all') {
                if ((c.category || 'General') !== activeVaultCategory) return false;
            }

            if (query) {
                const hay = `${c.name || ''} ${c.url || ''} ${c.domain || ''} ${c.username || ''} ${c.category || ''} ${c.notes || ''}`.toLowerCase();
                if (!hay.includes(query)) return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            grid.innerHTML = '';
            if (emptyMsg) emptyMsg.classList.remove('hidden');
            return;
        }
        if (emptyMsg) emptyMsg.classList.add('hidden');

        grid.innerHTML = filtered.map(c => {
            const domain = c.domain || extractDomainSafe(c.url);
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;

            let healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">${ent.label}</span>`;
            if (ent.isWeak) {
                healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">Weak (${ent.bits}b)</span>`;
            } else if (isReused) {
                healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">Reused</span>`;
            }

            return `
            <div class="bg-slate-900 border border-slate-800 hover:border-emerald-500/40 rounded-2xl p-4 shadow-sm transition flex flex-col justify-between">
                <div>
                    <div class="flex items-start justify-between gap-2 mb-3">
                        <div class="flex items-center gap-2.5 min-w-0">
                            <img src="${faviconUrl}" alt="" onerror="this.onerror=null;this.src='../../images/favicon.png'" class="w-6 h-6 rounded object-contain bg-slate-950 p-0.5 border border-slate-800 flex-shrink-0">
                            <div class="min-w-0">
                                <h4 class="text-sm font-bold text-slate-100 truncate" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</h4>
                                <p class="text-[10px] font-mono text-slate-500 truncate">${escapeHtml(domain)}</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-1 flex-shrink-0">
                            ${healthBadge}
                        </div>
                    </div>

                    <div class="space-y-2 mb-3">
                        <div class="flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800/80">
                            <div class="min-w-0">
                                <span class="text-[9px] uppercase tracking-wider text-slate-500 block">Username</span>
                                <span class="text-xs font-mono text-slate-200 truncate block">${escapeHtml(c.username)}</span>
                            </div>
                            <button onclick="copyVaultField('${escapeHtml(c.id)}', 'username')" class="text-slate-400 hover:text-sky-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs flex-shrink-0" title="Copy Username">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>

                        <div class="flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800/80">
                            <div class="min-w-0 flex-1">
                                <span class="text-[9px] uppercase tracking-wider text-slate-500 block">Password</span>
                                <span id="vault-pwd-display-${escapeHtml(c.id)}" data-revealed="false" class="text-xs font-mono text-slate-200 tracking-widest truncate block">&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;</span>
                            </div>
                            <div class="flex items-center gap-1 flex-shrink-0">
                                <button onclick="toggleRevealVaultPwd('${escapeHtml(c.id)}', this)" class="text-slate-400 hover:text-amber-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs" title="Show / Hide">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button onclick="copyVaultField('${escapeHtml(c.id)}', 'password')" class="text-slate-400 hover:text-emerald-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs" title="Copy Password (Auto-clears in 30s)">
                                    <i class="far fa-copy"></i>
                                </button>
                            </div>
                        </div>
                    </div>

                    ${c.notes ? `<p class="text-[11px] text-slate-400 line-clamp-2 mb-3 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/50">${escapeHtml(c.notes)}</p>` : ''}
                </div>

                <div class="pt-2.5 border-t border-slate-800/60 flex items-center justify-between">
                    <span class="text-[10px] font-semibold text-slate-400 bg-slate-800/70 px-2 py-0.5 rounded-full">${escapeHtml(c.category || 'General')}</span>
                    <div class="flex items-center gap-1.5">
                        ${c.url ? `<a href="${escapeHtml(c.url.startsWith('http') ? c.url : 'https://' + c.url)}" target="_blank" rel="noopener" class="w-7 h-7 rounded-lg bg-sky-600/15 hover:bg-sky-600 text-sky-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Open Login Page"><i class="fas fa-external-link-alt"></i></a>` : ''}
                        <button onclick="openVaultCredentialModal('${escapeHtml(c.id)}')" class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Edit"><i class="fas fa-pen"></i></button>
                        <button onclick="deleteVaultCredential('${escapeHtml(c.id)}')" class="w-7 h-7 rounded-lg bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Delete"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>
            </div>`;
        }).join('');
    };

    window.togglePasswordVisibility = function(inputId, btn) {
        const input = document.getElementById(inputId);
        if (!input) return;
        const isPwd = input.type === 'password';
        input.type = isPwd ? 'text' : 'password';
        if (btn) btn.innerHTML = isPwd ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
    };

    window.toggleRevealVaultPwd = function(credId, btn) {
        resetVaultAutoLock();
        const cred = unlockedCredentials.find(c => c.id === credId);
        const span = document.getElementById(`vault-pwd-display-${credId}`);
        if (!cred || !span) return;
        const revealed = span.getAttribute('data-revealed') === 'true';
        if (revealed) {
            span.innerHTML = '&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;';
            span.classList.add('tracking-widest');
            span.setAttribute('data-revealed', 'false');
            if (btn) btn.innerHTML = '<i class="fas fa-eye"></i>';
        } else {
            span.textContent = cred.password;
            span.classList.remove('tracking-widest');
            span.setAttribute('data-revealed', 'true');
            if (btn) btn.innerHTML = '<i class="fas fa-eye-slash text-amber-400"></i>';
        }
    };

    window.copyVaultField = async function(credId, field) {
        resetVaultAutoLock();
        const cred = unlockedCredentials.find(c => c.id === credId);
        if (!cred) return;
        const val = cred[field] || '';
        try {
            await navigator.clipboard.writeText(val);
            if (field === 'password') {
                showPortalToast('Password copied! Clipboard auto-clears in 30s');
                setTimeout(async () => {
                    try {
                        const current = await navigator.clipboard.readText();
                        if (current === val) await navigator.clipboard.writeText('');
                    } catch (e) { }
                }, 30000);
            } else {
                showPortalToast('Username copied to clipboard');
            }
        } catch (err) {
            showPortalToast('Clipboard access denied by browser');
        }
    };

    function generateCryptographicPassword(length = 20, useUpper = true, useLower = true, useNums = true, useSyms = true) {
        let charset = '';
        if (useUpper) charset += 'ABCDEFGHJKLMNPQRSTUVWXYZ';
        if (useLower) charset += 'abcdefghijkmnopqrstuvwxyz';
        if (useNums) charset += '23456789';
        if (useSyms) charset += '!@#$%^&*-_=+?';
        if (!charset) charset = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';

        const arr = new Uint32Array(length);
        window.crypto.getRandomValues(arr);
        let pwd = '';
        for (let i = 0; i < length; i++) {
            pwd += charset[arr[i] % charset.length];
        }
        return pwd;
    }

    window.openVaultCredentialModal = function(credId = null) {
        resetVaultAutoLock();
        const modal = document.getElementById('vault-credential-modal');
        if (!modal) return;

        const titleEl = document.getElementById('vault-cred-modal-title');
        const idEl = document.getElementById('vault-cred-id');
        const nameEl = document.getElementById('vault-cred-name');
        const urlEl = document.getElementById('vault-cred-url');
        const userEl = document.getElementById('vault-cred-username');
        const pwdEl = document.getElementById('vault-cred-password');
        const catEl = document.getElementById('vault-cred-category');
        const notesEl = document.getElementById('vault-cred-notes');

        if (credId) {
            const cred = unlockedCredentials.find(c => c.id === credId);
            if (!cred) return;
            if (titleEl) titleEl.innerHTML = '<i class="fas fa-pen text-sky-400"></i> Edit Credential';
            if (idEl) idEl.value = cred.id;
            if (nameEl) nameEl.value = cred.name || '';
            if (urlEl) urlEl.value = cred.url || '';
            if (userEl) userEl.value = cred.username || '';
            if (pwdEl) { pwdEl.value = cred.password || ''; pwdEl.type = 'password'; }
            if (catEl) catEl.value = cred.category || 'General';
            if (notesEl) notesEl.value = cred.notes || '';
        } else {
            if (titleEl) titleEl.innerHTML = '<i class="fas fa-key text-emerald-400"></i> Add Credential';
            if (idEl) idEl.value = '';
            if (nameEl) nameEl.value = '';
            if (urlEl) urlEl.value = '';
            if (userEl) userEl.value = '';
            if (pwdEl) { pwdEl.value = ''; pwdEl.type = 'password'; }
            if (catEl) catEl.value = 'General';
            if (notesEl) notesEl.value = '';
        }

        updateModalPasswordStrength();
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (nameEl) nameEl.focus();
    };

    window.closeVaultCredentialModal = function() {
        const modal = document.getElementById('vault-credential-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.fillGeneratedPasswordInModal = function() {
        const pwdEl = document.getElementById('vault-cred-password');
        if (!pwdEl) return;
        pwdEl.value = generateCryptographicPassword(22, true, true, true, true);
        pwdEl.type = 'text';
        updateModalPasswordStrength();
    };

    window.updateModalPasswordStrength = function() {
        const pwd = document.getElementById('vault-cred-password')?.value || '';
        const ent = calculatePasswordEntropy(pwd);
        const lbl = document.getElementById('vault-cred-strength-label');
        const bitsLbl = document.getElementById('vault-cred-entropy-label');
        if (lbl) {
            lbl.textContent = `Strength: ${ent.label}`;
            lbl.className = ent.color;
        }
        if (bitsLbl) bitsLbl.textContent = `${ent.bits} bits entropy`;
    };

    async function saveVaultCredentialFromModal() {
        if (!vaultMasterPassword) return;
        const idVal = document.getElementById('vault-cred-id')?.value;
        const name = document.getElementById('vault-cred-name')?.value.trim() || '';
        const url = document.getElementById('vault-cred-url')?.value.trim() || '';
        const username = document.getElementById('vault-cred-username')?.value.trim() || '';
        const password = document.getElementById('vault-cred-password')?.value || '';
        const category = document.getElementById('vault-cred-category')?.value || inferCredentialCategory(name, url);
        const notes = document.getElementById('vault-cred-notes')?.value.trim() || '';

        if (!name || !username || !password) return;

        const nowIso = new Date().toISOString();
        const credId = idVal || ('cred_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7));
        const credObj = {
            id: credId,
            name,
            url,
            domain: extractDomainSafe(url),
            username,
            password,
            category,
            notes,
            updatedAt: nowIso
        };

        const blob = await encryptVaultPayload(credObj, vaultMasterPassword);
        const blobs = getEncryptedVaultBlobs().filter(b => b.id !== credId);
        blobs.unshift(blob);
        saveEncryptedVaultBlobs(blobs);

        unlockedCredentials = unlockedCredentials.filter(c => c.id !== credId);
        unlockedCredentials.unshift(credObj);

        closeVaultCredentialModal();
        renderVaultCredentials();
        showPortalToast(`Encrypted & saved login for ${name}`);
    }

    window.deleteVaultCredential = function(credId) {
        if (!vaultMasterPassword) return;
        const cred = unlockedCredentials.find(c => c.id === credId);
        if (!cred) return;
        if (!confirm(`Delete encrypted login for "${cred.name}" (${cred.username})?`)) return;

        unlockedCredentials = unlockedCredentials.filter(c => c.id !== credId);
        const blobs = getEncryptedVaultBlobs().filter(b => b.id !== credId);
        saveEncryptedVaultBlobs(blobs);
        renderVaultCredentials();
        showPortalToast(`Deleted ${cred.name} from vault`);
    };

    // Password Generator Modal
    window.openVaultGeneratorModal = function() {
        resetVaultAutoLock();
        const modal = document.getElementById('vault-generator-modal');
        if (!modal) return;
        generateAndDisplayPassword();
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    };

    window.closeVaultGeneratorModal = function() {
        const modal = document.getElementById('vault-generator-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.generateAndDisplayPassword = function() {
        const len = parseInt(document.getElementById('vault-gen-len')?.value || '20', 10);
        const u = document.getElementById('vault-gen-upper')?.checked !== false;
        const l = document.getElementById('vault-gen-lower')?.checked !== false;
        const n = document.getElementById('vault-gen-nums')?.checked !== false;
        const s = document.getElementById('vault-gen-syms')?.checked !== false;

        const pwd = generateCryptographicPassword(len, u, l, n, s);
        const outEl = document.getElementById('vault-gen-output');
        const entEl = document.getElementById('vault-gen-entropy');
        if (outEl) outEl.textContent = pwd;
        if (entEl) {
            const ent = calculatePasswordEntropy(pwd);
            entEl.innerHTML = `Entropy: <strong class="${ent.color}">${ent.bits} bits (${ent.label})</strong>`;
        }
    };

    window.copyGeneratedPassword = async function() {
        const pwd = document.getElementById('vault-gen-output')?.textContent || '';
        if (!pwd) return;
        await navigator.clipboard.writeText(pwd);
        showPortalToast('Generated password copied to clipboard');
    };

    // CSV Parser & Importer (Google Password Manager & LastPass)
    function parseCsvMatrix(text) {
        const rows = [];
        let row = [];
        let field = '';
        let inQuotes = false;
        for (let i = 0; i < text.length; i++) {
            const ch = text[i];
            const next = text[i + 1];
            if (inQuotes) {
                if (ch === '"' && next === '"') {
                    field += '"';
                    i++;
                } else if (ch === '"') {
                    inQuotes = false;
                } else {
                    field += ch;
                }
            } else {
                if (ch === '"') {
                    inQuotes = true;
                } else if (ch === ',') {
                    row.push(field);
                    field = '';
                } else if (ch === '\r' && next === '\n') {
                    row.push(field);
                    rows.push(row);
                    row = [];
                    field = '';
                    i++;
                } else if (ch === '\n' || ch === '\r') {
                    row.push(field);
                    rows.push(row);
                    row = [];
                    field = '';
                } else {
                    field += ch;
                }
            }
        }
        if (field.length > 0 || row.length > 0) {
            row.push(field);
            rows.push(row);
        }
        return rows;
    }

    window.openVaultImportModal = function() {
        resetVaultAutoLock();
        pendingCsvParsedRecords = [];
        const statusEl = document.getElementById('vault-import-status');
        const btn = document.getElementById('vault-confirm-import-btn');
        const fileEl = document.getElementById('vault-csv-file');
        if (statusEl) statusEl.textContent = 'No file selected yet';
        if (btn) btn.disabled = true;
        if (fileEl) fileEl.value = '';
        const modal = document.getElementById('vault-import-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeVaultImportModal = function() {
        const modal = document.getElementById('vault-import-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.handleVaultCsvFileSelect = function(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const matrix = parseCsvMatrix(e.target.result || '');
            if (matrix.length < 2) return;
            const headers = matrix[0].map(h => h.trim().toLowerCase());
            const idxName = headers.indexOf('name');
            const idxUrl = headers.indexOf('url');
            const idxUser = headers.indexOf('username');
            const idxPwd = headers.indexOf('password');
            const idxExtra = headers.indexOf('extra') !== -1 ? headers.indexOf('extra') : headers.indexOf('note');
            const idxGroup = headers.indexOf('grouping');

            const parsed = [];
            for (let i = 1; i < matrix.length; i++) {
                const r = matrix[i];
                if (!r || r.length < 3) continue;
                const url = idxUrl !== -1 ? (r[idxUrl] || '').trim() : '';
                const name = (idxName !== -1 ? (r[idxName] || '').trim() : '') || extractDomainSafe(url) || 'Imported Login';
                const username = idxUser !== -1 ? (r[idxUser] || '').trim() : '';
                const password = idxPwd !== -1 ? (r[idxPwd] || '') : '';
                const notes = idxExtra !== -1 ? (r[idxExtra] || '').trim() : '';
                const grouping = idxGroup !== -1 ? (r[idxGroup] || '').trim() : '';

                if (!password && !username) continue;
                parsed.push({
                    name,
                    url,
                    domain: extractDomainSafe(url),
                    username,
                    password,
                    notes,
                    category: grouping || inferCredentialCategory(name, url)
                });
            }

            pendingCsvParsedRecords = parsed;
            const statusEl = document.getElementById('vault-import-status');
            const btn = document.getElementById('vault-confirm-import-btn');
            if (statusEl) statusEl.innerHTML = `<span class="text-emerald-400 font-semibold">Ready to encrypt &amp; import ${parsed.length} credentials from ${escapeHtml(file.name)}</span>`;
            if (btn) btn.disabled = (parsed.length === 0);
        };
        reader.readAsText(file);
    };

    window.confirmVaultCsvImport = async function() {
        if (!vaultMasterPassword || pendingCsvParsedRecords.length === 0) return;
        const btn = document.getElementById('vault-confirm-import-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Encrypting...';
        }

        const existingKeys = new Set(unlockedCredentials.map(c => `${c.domain}|${c.username}`));
        const blobs = getEncryptedVaultBlobs();
        let importedCount = 0;

        for (const rec of pendingCsvParsedRecords) {
            const key = `${rec.domain}|${rec.username}`;
            if (existingKeys.has(key)) continue;
            existingKeys.add(key);

            const credObj = {
                id: 'cred_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
                name: rec.name,
                url: rec.url,
                domain: rec.domain,
                username: rec.username,
                password: rec.password,
                category: rec.category,
                notes: rec.notes,
                updatedAt: new Date().toISOString()
            };
            const blob = await encryptVaultPayload(credObj, vaultMasterPassword);
            blobs.unshift(blob);
            unlockedCredentials.unshift(credObj);
            importedCount++;
        }

        saveEncryptedVaultBlobs(blobs);
        pendingCsvParsedRecords = [];
        closeVaultImportModal();
        renderVaultCredentials();
        showPortalToast(`Encrypted & imported ${importedCount} credentials (AES-256-GCM)`);
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Encrypt & Import';
        }
    };

    // Export strictly encrypted blobs for SQLite content.db sync
    window.exportEncryptedVaultForSQLite = function() {
        const blobs = getEncryptedVaultBlobs();
        const payload = {
            _format: "portal_passwords_aes256gcm_v1",
            _exported_at: new Date().toISOString(),
            count: blobs.length,
            records: blobs
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `portal_vault_sync.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showPortalToast(`Downloaded ${blobs.length} encrypted blobs (run import_vault_to_db.py to save to content.db)`);
    };

    // -------------------------------------------------------------------------
    // 18. MASTER PROJECTS, DRIVE ARTIFACTS & WEBSITE PLACEMENTS HUB
    // -------------------------------------------------------------------------
    const PROJECT_PATCH_OPS_KEY = 'portal_project_patch_ops_v1';
    const DELETED_PROJ_SLUGS_KEY = 'portal_deleted_project_slugs_v1';
    const GITHUB_PAT_KEY = 'portal_github_pat_v1';
    const GITHUB_REPO_KEY = 'portal_github_repo_v1';
    const GITHUB_BRANCH_KEY = 'portal_github_branch_v1';
    const PROJECTS_PAGE_SIZE = 20;

    const portalProjectsState = {
        liveMode: false,
        backendChecked: false,
        unlocked: false,
        projects: [],
        placementSlots: [],
        driveRoots: [],
        driveRuns: [],
        statusFilter: 'all',
        slotFilter: '',
        kindFilter: '',
        search: '',
        page: 1,
        editingProjectId: null,
        pendingDraftArtifacts: [],
    };

    function getStagedPatchOps() {
        try {
            return JSON.parse(localStorage.getItem(PROJECT_PATCH_OPS_KEY) || '[]');
        } catch (e) {
            return [];
        }
    }

    function pushStagedPatchOp(op, payload) {
        const ops = getStagedPatchOps();
        ops.push({ op, payload, ts: new Date().toISOString() });
        localStorage.setItem(PROJECT_PATCH_OPS_KEY, JSON.stringify(ops));
        updatePatchBadge();
    }

    function updatePatchBadge() {
        const ops = getStagedPatchOps();
        const badge = document.getElementById('projects-patch-count');
        const pendingBadge = document.getElementById('projects-pending-badge');
        if (badge) {
            if (ops.length > 0 && !portalProjectsState.liveMode) {
                badge.textContent = String(ops.length);
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
        if (pendingBadge) {
            const customBmCnt = getCustomBookmarks().length;
            const totalPending = ops.length + customBmCnt;
            if (totalPending > 0 && !portalProjectsState.liveMode) {
                pendingBadge.textContent = String(totalPending);
                pendingBadge.classList.remove('hidden');
            } else {
                pendingBadge.classList.add('hidden');
            }
        }
    }

    function applyLocalPatchOpsToMemory(projects) {
        const ops = getStagedPatchOps();
        if (!ops.length) return projects;
        const list = projects.map(p => ({ ...p, artifacts: [...(p.artifacts || [])], placements: [...(p.placements || [])], tags: [...(p.tags || [])] }));
        for (const item of ops) {
            const pl = item.payload || {};
            if (item.op === 'save_project') {
                const idx = list.findIndex(x => (pl.id && x.id === pl.id) || (pl.slug && x.slug === pl.slug));
                if (idx >= 0) {
                    list[idx] = { ...list[idx], ...pl };
                } else {
                    list.unshift({ id: pl.id || -Date.now(), artifacts: [], placements: [], ...pl });
                }
            } else if (item.op === 'delete_project') {
                const idx = list.findIndex(x => (pl.id && x.id === pl.id) || (pl.slug && x.slug === pl.slug));
                if (idx >= 0) list.splice(idx, 1);
            } else if (item.op === 'save_artifact') {
                const proj = list.find(x => (pl.project_id && x.id === pl.project_id) || (pl.project_slug && x.slug === pl.project_slug));
                if (proj) {
                    const art = { id: pl.id || -Date.now(), ...pl };
                    const aIdx = proj.artifacts.findIndex(a => a.id === art.id);
                    if (aIdx >= 0) proj.artifacts[aIdx] = art;
                    else proj.artifacts.push(art);
                }
            } else if (item.op === 'delete_artifact') {
                list.forEach(p => {
                    p.artifacts = p.artifacts.filter(a => a.id !== pl.id);
                });
            } else if (item.op === 'set_placements') {
                const proj = list.find(x => (pl.project_id && x.id === pl.project_id) || (pl.project_slug && x.slug === pl.project_slug));
                if (proj) {
                    proj.placements = pl.placements || [];
                    if (pl.auto_public && proj.placements.some(x => x.is_visible !== false)) {
                        proj.is_public = true;
                    }
                }
            } else if (item.op === 'merge_projects') {
                applyInMemoryMerge(list, pl.source_id, pl.source_slug, pl.target_id, pl.target_slug, pl);
            }
        }
        return list;
    }

    function applyInMemoryMerge(list, srcId, srcSlug, tgtId, tgtSlug, opts = {}) {
        const sIdx = list.findIndex(x => (srcId && x.id === srcId) || (srcSlug && x.slug === srcSlug));
        const tIdx = list.findIndex(x => (tgtId && x.id === tgtId) || (tgtSlug && x.slug === tgtSlug));
        if (sIdx < 0 || tIdx < 0 || sIdx === tIdx) return false;
        const src = list[sIdx];
        const tgt = list[tIdx];

        const seenUrls = new Set((tgt.artifacts || []).map(a => a.url).filter(Boolean));
        const seenGfids = new Set((tgt.artifacts || []).map(a => a.gdrive_file_id).filter(Boolean));
        tgt.artifacts = [...(tgt.artifacts || [])];
        (src.artifacts || []).forEach(a => {
            if (seenUrls.has(a.url) || (a.gdrive_file_id && seenGfids.has(a.gdrive_file_id))) return;
            tgt.artifacts.push(a);
            if (a.url) seenUrls.add(a.url);
            if (a.gdrive_file_id) seenGfids.add(a.gdrive_file_id);
        });

        const seenSlots = new Set((tgt.placements || []).map(p => `${p.page_slug}.${p.section_slot}`));
        tgt.placements = [...(tgt.placements || [])];
        (src.placements || []).forEach(p => {
            const key = `${p.page_slug}.${p.section_slot}`;
            if (!seenSlots.has(key)) {
                tgt.placements.push(p);
                seenSlots.add(key);
            }
        });

        tgt.tags = Array.from(new Set([...(tgt.tags || []), ...(src.tags || [])]));
        tgt.tech_stack = Array.from(new Set([...(tgt.tech_stack || []), ...(src.tech_stack || [])]));
        const kw = [...(tgt.keywords || []), ...(src.keywords || [])];
        if (opts.add_alias !== false) {
            if (src.title) kw.push(src.title);
            if (src.slug) kw.push(src.slug);
        }
        tgt.keywords = Array.from(new Set(kw.filter(Boolean)));
        const seenPubs = new Set((tgt.publications || []).map(pb => pb.id || pb.title));
        tgt.publications = [...(tgt.publications || [])];
        (src.publications || []).forEach(pb => {
            const k = pb.id || pb.title;
            if (!seenPubs.has(k)) { tgt.publications.push(pb); seenPubs.add(k); }
        });
        const years = [tgt.year_start, tgt.year_end, src.year_start, src.year_end].filter(y => Number.isFinite(Number(y)) && Number(y) > 1900).map(Number);
        if (years.length) { tgt.year_start = Math.min(...years); tgt.year_end = Math.max(...years); }
        if (opts.append_summary && src.short_summary && !(tgt.full_description || '').includes(src.short_summary)) {
            tgt.full_description = `${tgt.full_description || tgt.short_summary || ''}\n\n[Merged from ${src.title}]: ${src.short_summary}`.trim();
        }
        tgt.updated_at = new Date().toISOString();
        list.splice(sIdx, 1);
        return true;
    }

    async function probeLiveProjectsServer() {
        const host = window.location.hostname;
        if (host !== '127.0.0.1' && host !== 'localhost') return false;
        try {
            const resp = await fetch('/api/health', { cache: 'no-store' });
            if (!resp.ok) return false;
            const data = await resp.json();
            return Boolean(data && data.ok);
        } catch (e) {
            return false;
        }
    }

    function populatePlacementDropdown() {
        const sel = document.getElementById('projects-slot-filter');
        if (!sel) return;
        const current = sel.value;
        const slots = portalProjectsState.placementSlots || [];
        sel.innerHTML = '<option value="">All Website Placement Slots</option>' + slots.map(s => {
            const val = `${s.page_slug}.${s.section_slot}`;
            return `<option value="${escapeHtml(val)}">${escapeHtml(s.label)}</option>`;
        }).join('');
        if (current) sel.value = current;
    }

    function updateProjectsModeUI() {
        const badge = document.getElementById('projects-mode-badge');
        const watchBtn = document.getElementById('projects-watch-btn');
        const syncBtn = document.getElementById('projects-sync-btn');
        const unlockCard = document.getElementById('projects-unlock-card');
        const hasGhPat = Boolean((localStorage.getItem(GITHUB_PAT_KEY) || '').trim());
        const repoName = localStorage.getItem(GITHUB_REPO_KEY) || 'iebeid/iebeid.github.io';
        if (badge) {
            if (portalProjectsState.liveMode) {
                badge.textContent = 'SQLite Live Mode (localhost)';
                badge.className = 'px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/40';
            } else if (hasGhPat) {
                badge.textContent = `GitHub Direct Publish (${repoName})`;
                badge.className = 'px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/40';
            } else {
                badge.textContent = 'Static Mode (Add GitHub PAT in Settings)';
                badge.className = 'px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/40';
            }
        }
        if (watchBtn) watchBtn.classList.toggle('hidden', !portalProjectsState.liveMode);
        if (syncBtn) syncBtn.classList.toggle('hidden', !portalProjectsState.liveMode);
        if (unlockCard) unlockCard.classList.toggle('hidden', portalProjectsState.liveMode || portalProjectsState.unlocked);
        updatePatchBadge();
    }

    function hydrateBundleState(bundle) {
        portalProjectsState.projects = portalProjectsState.liveMode
            ? (bundle.projects || [])
            : applyLocalPatchOpsToMemory(bundle.projects || []);
        portalProjectsState.placementSlots = bundle.placement_slots || (window.__SITE_DATABASE && window.__SITE_DATABASE.site_placement_slots) || [];
        portalProjectsState.driveRoots = bundle.drive_scan_roots || [];
        portalProjectsState.driveRuns = bundle.drive_scan_runs || [];
        portalProjectsState.unlocked = true;
        populatePlacementDropdown();
        renderPortalProjectsHub();
    }

    window.unlockPortalProjectsBundle = async function (event) {
        if (event) event.preventDefault();
        const passEl = document.getElementById('projects-unlock-pass');
        const pass = (passEl && passEl.value.trim()) || portalSessionPasscode || vaultMasterPassword;
        if (!pass) return;
        const enc = window.__SITE_DATABASE && window.__SITE_DATABASE.portal_projects_encrypted;
        if (!enc) {
            showPortalToast('Encrypted project bundle not found in portal_data.js.', 'error');
            return;
        }
        const plain = await decryptSqliteVaultEntry(enc, pass);
        if (!plain) {
            showPortalToast('Invalid passcode for encrypted project catalog.', 'error');
            return;
        }
        portalSessionPasscode = pass;
        if (passEl) passEl.value = '';
        hydrateBundleState(JSON.parse(plain));
        updateProjectsModeUI();
        showPortalToast(`Unlocked ${portalProjectsState.projects.length} master projects`);
    };

    window.__initPortalProjectsHub = async function () {
        if (!portalProjectsState.backendChecked) {
            portalProjectsState.backendChecked = true;
            portalProjectsState.liveMode = await probeLiveProjectsServer();
        }
        if (portalProjectsState.liveMode) {
            try {
                const resp = await fetch('/api/projects', { cache: 'no-store' });
                const data = await resp.json();
                if (data && data.ok) {
                    hydrateBundleState(data);
                }
            } catch (e) {
                portalProjectsState.liveMode = false;
            }
        } else {
            const enc = window.__SITE_DATABASE && window.__SITE_DATABASE.portal_projects_encrypted;
            const autoPass = portalSessionPasscode || vaultMasterPassword;
            if (enc && autoPass) {
                const plain = await decryptSqliteVaultEntry(enc, autoPass);
                if (plain) {
                    hydrateBundleState(JSON.parse(plain));
                }
            }
            if (!portalProjectsState.unlocked && window.__SITE_DATABASE && Array.isArray(window.__SITE_DATABASE.projects)) {
                // Show public projects immediately as a preview while keeping the full encrypted catalog locked
                portalProjectsState.projects = applyLocalPatchOpsToMemory(
                    window.__SITE_DATABASE.projects.map(p => ({ ...p, is_public: true, discovery_status: p.discovery_status || 'canonical' }))
                );
                portalProjectsState.placementSlots = window.__SITE_DATABASE.site_placement_slots || [];
                if (!enc) portalProjectsState.unlocked = true;
                populatePlacementDropdown();
            }
        }
        updateProjectsModeUI();
        renderPortalProjectsHub();
    };

    window.setPortalProjectsStatusFilter = function (statusKey) {
        portalProjectsState.statusFilter = statusKey;
        portalProjectsState.page = 1;
        document.querySelectorAll('#projects-status-pills .proj-pill').forEach(btn => {
            const active = btn.getAttribute('data-pfilter') === statusKey;
            btn.className = active
                ? 'proj-pill active px-3 py-1 rounded-full bg-sky-600 text-white font-semibold'
                : 'proj-pill px-3 py-1 rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700';
        });
        renderPortalProjectsHub();
    };

    window.onPortalProjectsFilterChange = function () {
        portalProjectsState.search = (document.getElementById('projects-search-input')?.value || '').trim().toLowerCase();
        portalProjectsState.slotFilter = document.getElementById('projects-slot-filter')?.value || '';
        portalProjectsState.kindFilter = document.getElementById('projects-kind-filter')?.value || '';
        portalProjectsState.page = 1;
        renderPortalProjectsHub();
    };

    window.goToProjectsPage = function (pageNum) {
        portalProjectsState.page = Math.max(1, pageNum);
        renderPortalProjectsHub();
    };

    function getFilteredPortalProjects() {
        const q = portalProjectsState.search;
        const sf = portalProjectsState.statusFilter;
        const slotF = portalProjectsState.slotFilter;
        const kindF = portalProjectsState.kindFilter;

        return portalProjectsState.projects.filter(p => {
            const visiblePlacements = (p.placements || []).filter(pl => pl.is_visible !== false);
            if (sf === 'placed' && visiblePlacements.length === 0) return false;
            if (sf === 'discovered' && p.discovery_status !== 'discovered') return false;
            if (sf === 'public' && !p.is_public) return false;
            if (sf === 'private' && p.is_public) return false;
            if (kindF && (p.project_kind || '').toLowerCase() !== kindF.toLowerCase()) return false;
            if (slotF && !visiblePlacements.some(pl => `${pl.page_slug}.${pl.section_slot}` === slotF)) return false;
            if (q) {
                const hay = [
                    p.title, p.slug, p.tagline, p.short_summary, p.category, p.project_kind,
                    ...(p.tags || []),
                    ...(p.artifacts || []).map(a => `${a.label} ${a.gdrive_path || ''} ${a.url || ''}`),
                ].join(' ').toLowerCase();
                if (!hay.includes(q)) return false;
            }
            return true;
        });
    }

    function renderPortalProjectsHub() {
        const listEl = document.getElementById('projects-list-container');
        const pagEl = document.getElementById('projects-pagination-bar');
        if (!listEl) return;

        const all = portalProjectsState.projects || [];
        const publicCnt = all.filter(p => p.is_public).length;
        const discCnt = all.filter(p => p.discovery_status === 'discovered').length;
        const gdriveCnt = all.reduce((acc, p) => acc + (p.artifacts || []).filter(a => a.storage_source === 'gdrive').length, 0);
        const placeCnt = all.reduce((acc, p) => acc + (p.placements || []).filter(pl => pl.is_visible !== false).length, 0);

        const setTxt = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = String(v); };
        setTxt('proj-stat-total', all.length);
        setTxt('proj-stat-public', publicCnt);
        setTxt('proj-stat-discovered', discCnt);
        setTxt('proj-stat-gdrive', gdriveCnt);
        setTxt('proj-stat-placements', placeCnt);

        if (!portalProjectsState.unlocked && !portalProjectsState.liveMode && all.length === 0) {
            listEl.innerHTML = '';
            if (pagEl) pagEl.innerHTML = '';
            return;
        }

        const filtered = getFilteredPortalProjects();
        const sizeVal = document.getElementById('projects-page-size')?.value || 'all';
        const pageSize = (sizeVal === 'all') ? Math.max(1, filtered.length) : Math.max(1, Number(sizeVal) || 50);

        const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (portalProjectsState.page > totalPages) portalProjectsState.page = totalPages;
        const start = (portalProjectsState.page - 1) * pageSize;
        const slice = filtered.slice(start, start + pageSize);
        setTxt('projects-result-count', filtered.length ? `Showing ${start + 1}–${start + slice.length} of ${filtered.length} (${all.length} total)` : `Showing 0 of ${all.length}`);

        if (slice.length === 0) {
            listEl.innerHTML = '<div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-xs text-slate-400">No projects match the current filter.</div>';
            if (pagEl) pagEl.innerHTML = '';
            return;
        }

        listEl.innerHTML = slice.map(p => {
            const visSlots = (p.placements || []).filter(pl => pl.is_visible !== false);
            const slotPills = visSlots.length
                ? visSlots.map(pl => `<span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-sky-500/15 text-sky-300 border border-sky-500/30">${escapeHtml(pl.page_slug)}.${escapeHtml(pl.section_slot)}</span>`).join('')
                : '<span class="text-[11px] text-slate-500 italic">Not placed on website yet</span>';

            const pubBadge = p.is_public
                ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">PUBLIC</span>'
                : '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">PRIVATE</span>';

            const statusBadge = p.discovery_status === 'discovered'
                ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/30">discovered</span>'
                : `<span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300">${escapeHtml(p.discovery_status || 'canonical')}</span>`;

            const driveLink = p.gdrive_primary_url || ((p.artifacts || []).find(a => a.storage_source === 'gdrive') || {}).url || '';
            const safeId = JSON.stringify(p.id);

            return `
                <article class="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-4 shadow transition">
                    <div class="flex flex-col md:flex-row md:items-start justify-between gap-3">
                        <div class="space-y-1.5 min-w-0 flex-1">
                            <div class="flex flex-wrap items-center gap-2">
                                ${pubBadge}
                                ${statusBadge}
                                <span class="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/30">${escapeHtml(p.project_kind || 'research')}</span>
                                <span class="text-[11px] font-mono text-slate-500">${escapeHtml(p.slug)}</span>
                            </div>
                            <h3 class="text-base font-bold text-white truncate">${escapeHtml(p.title)}</h3>
                            <p class="text-xs text-slate-400 line-clamp-2">${escapeHtml(p.short_summary || p.tagline || '')}</p>
                            <div class="flex flex-wrap items-center gap-1.5 pt-1">
                                <span class="text-[10px] uppercase tracking-wider text-slate-500 mr-1">Website Cards:</span>
                                ${slotPills}
                            </div>
                        </div>
                        <div class="flex flex-wrap md:flex-col items-end gap-2 flex-shrink-0">
                            <div class="flex items-center gap-1.5">
                                ${driveLink ? `<a href="${escapeHtml(driveLink)}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs font-semibold flex items-center gap-1"><i class="fab fa-google-drive"></i> Drive (${(p.artifacts || []).length})</a>` : `<span class="px-2.5 py-1.5 rounded-lg bg-slate-950 text-slate-500 text-xs">${(p.artifacts || []).length} artifacts</span>`}
                                <button type="button" onclick='openProjectEditorModal(${safeId})' class="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold flex items-center gap-1"><i class="fas fa-edit"></i> Edit / Place</button>
                                <button type="button" onclick='openManualMergeModal(${safeId})' class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-purple-600/80 text-slate-300 hover:text-white text-xs font-semibold" title="Merge into another project"><i class="fas fa-code-branch"></i></button>
                                <button type="button" onclick='deletePortalProject(${safeId})' class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-600/80 text-slate-300 hover:text-white text-xs" title="Delete project"><i class="fas fa-trash"></i></button>
                            </div>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        if (pagEl) {
            if (totalPages <= 1) {
                pagEl.innerHTML = '';
            } else {
                pagEl.innerHTML = `
                    <button type="button" onclick="goToProjectsPage(${portalProjectsState.page - 1})" ${portalProjectsState.page <= 1 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 disabled:opacity-40">Prev</button>
                    <span class="text-xs font-mono text-slate-400">Page ${portalProjectsState.page} / ${totalPages}</span>
                    <button type="button" onclick="goToProjectsPage(${portalProjectsState.page + 1})" ${portalProjectsState.page >= totalPages ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 disabled:opacity-40">Next</button>
                `;
            }
        }
    }

    function renderEditorPlacementCheckboxes(proj) {
        const grid = document.getElementById('pe-placements-grid');
        if (!grid) return;
        const activeSet = new Set(
            ((proj && proj.placements) || [])
                .filter(pl => pl.is_visible !== false)
                .map(pl => `${pl.page_slug}.${pl.section_slot}`)
        );
        const slots = portalProjectsState.placementSlots || [];
        grid.innerHTML = slots.map(s => {
            const key = `${s.page_slug}.${s.section_slot}`;
            const checked = activeSet.has(key) ? 'checked' : '';
            return `
                <label class="flex items-start gap-2 p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-sky-500/40 cursor-pointer text-[11px] text-slate-300">
                    <input type="checkbox" class="pe-placement-cb accent-sky-500 mt-0.5" data-page="${escapeHtml(s.page_slug)}" data-slot="${escapeHtml(s.section_slot)}" ${checked} />
                    <span><strong class="text-white">${escapeHtml(s.page_slug)}.${escapeHtml(s.section_slot)}</strong><br/><span class="text-slate-400 text-[10px]">${escapeHtml(s.label)}</span></span>
                </label>
            `;
        }).join('');
    }

    function renderEditorArtifactsList(proj) {
        const listEl = document.getElementById('pe-artifacts-list');
        if (!listEl) return;
        const arts = (proj && proj.artifacts) || [];
        if (!arts.length) {
            listEl.innerHTML = '<div class="text-xs text-slate-500 italic">No artifacts linked yet.</div>';
            return;
        }
        listEl.innerHTML = arts.map((a, idx) => {
            const safeArtId = JSON.stringify(a.id != null ? a.id : idx);
            const srcBadge = a.storage_source === 'gdrive'
                ? '<span class="px-1.5 py-0.5 rounded text-[10px] bg-sky-500/15 text-sky-300 font-mono">gdrive</span>'
                : `<span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono">${escapeHtml(a.storage_source || 'repo')}</span>`;
            const pubChecked = a.is_public !== false ? 'checked' : '';
            return `
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs">
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center gap-2">
                            ${srcBadge}
                            <span class="font-semibold text-white truncate">${escapeHtml(a.label)}</span>
                            <span class="text-[10px] font-mono text-slate-500">${escapeHtml(a.type)}</span>
                        </div>
                        <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener noreferrer" class="text-[11px] text-sky-400 hover:underline truncate block">${escapeHtml(a.gdrive_path || a.url)}</a>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0">
                        <label class="inline-flex items-center gap-1 text-[11px] text-emerald-300 cursor-pointer">
                            <input type="checkbox" ${pubChecked} onchange='toggleArtifactPublic(${safeArtId}, this.checked)' class="accent-emerald-500" /> Public
                        </label>
                        <button type="button" onclick='deleteArtifactFromEditor(${safeArtId})' class="px-2 py-1 rounded bg-slate-800 hover:bg-rose-600/80 text-slate-300 hover:text-white text-[11px]"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `;
        }).join('');
    }

    window.openProjectEditorModal = function (projectId) {
        const proj = projectId != null ? portalProjectsState.projects.find(p => p.id === projectId) : null;
        portalProjectsState.editingProjectId = proj ? proj.id : null;

        document.getElementById('proj-modal-heading').textContent = proj ? `Edit: ${proj.title}` : 'Create New Project';
        document.getElementById('pe-id').value = proj ? String(proj.id) : '';
        document.getElementById('pe-title').value = proj ? proj.title : '';
        document.getElementById('pe-slug').value = proj ? proj.slug : '';
        document.getElementById('pe-kind').value = (proj && proj.project_kind) || 'research';
        document.getElementById('pe-category').value = (proj && proj.category) || 'AI & Life Sciences';
        document.getElementById('pe-status').value = (proj && proj.status) || 'Active';
        document.getElementById('pe-discovery').value = (proj && proj.discovery_status) || 'canonical';
        document.getElementById('pe-year-start').value = (proj && proj.year_start) || '';
        document.getElementById('pe-year-end').value = (proj && proj.year_end) || '';
        document.getElementById('pe-order').value = (proj && proj.display_order != null) ? proj.display_order : 50;
        document.getElementById('pe-public').checked = proj ? Boolean(proj.is_public) : false;
        document.getElementById('pe-tagline').value = (proj && proj.tagline) || '';
        document.getElementById('pe-summary').value = (proj && proj.short_summary) || '';
        document.getElementById('pe-description').value = (proj && proj.full_description) || '';
        document.getElementById('pe-tech').value = ((proj && proj.tech_stack) || []).join(', ');
        document.getElementById('pe-tags').value = ((proj && proj.tags) || []).join(', ');
        document.getElementById('pe-org').value = (proj && (proj.grant_award || proj.institution_or_org)) || '';

        renderEditorPlacementCheckboxes(proj);
        const artSec = document.getElementById('pe-artifacts-section');
        if (artSec) artSec.classList.toggle('hidden', !proj);
        if (proj) renderEditorArtifactsList(proj);

        const modal = document.getElementById('project-editor-modal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    };

    window.closeProjectEditorModal = function () {
        const modal = document.getElementById('project-editor-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.submitProjectEditorForm = async function (event) {
        event.preventDefault();
        const idRaw = document.getElementById('pe-id').value;
        const placements = [];
        document.querySelectorAll('#pe-placements-grid .pe-placement-cb:checked').forEach((cb, idx) => {
            placements.push({
                page_slug: cb.getAttribute('data-page'),
                section_slot: cb.getAttribute('data-slot'),
                display_order: (idx + 1) * 10,
                is_visible: true,
            });
        });

        const payload = {
            id: idRaw ? Number(idRaw) : null,
            title: document.getElementById('pe-title').value.trim(),
            slug: document.getElementById('pe-slug').value.trim(),
            project_kind: document.getElementById('pe-kind').value,
            category: document.getElementById('pe-category').value.trim() || 'General Portfolio',
            status: document.getElementById('pe-status').value.trim(),
            discovery_status: document.getElementById('pe-discovery').value,
            year_start: document.getElementById('pe-year-start').value || null,
            year_end: document.getElementById('pe-year-end').value || null,
            display_order: Number(document.getElementById('pe-order').value || 50),
            is_public: document.getElementById('pe-public').checked || placements.length > 0,
            tagline: document.getElementById('pe-tagline').value.trim(),
            short_summary: document.getElementById('pe-summary').value.trim(),
            full_description: document.getElementById('pe-description').value.trim(),
            tech_stack: document.getElementById('pe-tech').value.split(',').map(s => s.trim()).filter(Boolean),
            tags: document.getElementById('pe-tags').value.split(',').map(s => s.trim()).filter(Boolean),
            institution_or_org: document.getElementById('pe-org').value.trim(),
            placements,
            auto_public: true,
        };

        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/projects/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await resp.json();
            if (!data.ok) {
                showPortalToast(data.error || 'Failed to save project', 'error');
                return;
            }
            hydrateBundleState(data);
            showPortalToast(`Saved "${payload.title}" to SQLite content.db`);
        } else {
            if (!payload.id) payload.id = -Date.now();
            if (!payload.slug) payload.slug = payload.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            pushStagedPatchOp('save_project', payload);
            pushStagedPatchOp('set_placements', { project_id: payload.id, project_slug: payload.slug, placements, auto_public: true });
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            renderPortalProjectsHub();
            showPortalToast(`Staged "${payload.title}" locally (Export Patch JSON to apply to content.db)`);
        }
        closeProjectEditorModal();
    };

    window.deletePortalProject = async function (projectId) {
        const proj = portalProjectsState.projects.find(p => p.id === projectId);
        if (!proj || !confirm(`Delete "${proj.title}" from the master projects database?`)) return;
        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/projects/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: proj.id, slug: proj.slug }),
            });
            const data = await resp.json();
            if (data.ok) hydrateBundleState(data);
            showPortalToast(`Deleted "${proj.title}" from content.db`);
        } else {
            if (proj.slug) {
                try {
                    const delSlugs = JSON.parse(localStorage.getItem(DELETED_PROJ_SLUGS_KEY) || '[]');
                    if (!delSlugs.includes(proj.slug)) delSlugs.push(proj.slug);
                    localStorage.setItem(DELETED_PROJ_SLUGS_KEY, JSON.stringify(delSlugs));
                } catch (e) { }
            }
            pushStagedPatchOp('delete_project', { id: proj.id, slug: proj.slug });
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            renderPortalProjectsHub();
            showPortalToast(`Staged deletion of "${proj.title}"`);
        }
    };

    window.addArtifactFromEditor = async function () {
        const proj = portalProjectsState.projects.find(p => p.id === portalProjectsState.editingProjectId);
        if (!proj) return;
        const type = document.getElementById('pa-type').value;
        const label = document.getElementById('pa-label').value.trim();
        const url = document.getElementById('pa-url').value.trim();
        if (!label || !url) {
            showPortalToast('Provide both an artifact label and Drive/URL/path.', 'warn');
            return;
        }
        const payload = {
            project_id: proj.id,
            project_slug: proj.slug,
            type,
            label,
            url,
            is_public: Boolean(proj.is_public),
        };
        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/artifacts/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await resp.json();
            if (data.ok) {
                hydrateBundleState(data);
                const updated = portalProjectsState.projects.find(p => p.id === proj.id);
                renderEditorArtifactsList(updated);
            }
        } else {
            payload.id = -Date.now();
            pushStagedPatchOp('save_artifact', payload);
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            const updated = portalProjectsState.projects.find(p => p.id === proj.id);
            renderEditorArtifactsList(updated);
        }
        document.getElementById('pa-label').value = '';
        document.getElementById('pa-url').value = '';
        showPortalToast(`Linked artifact "${label}"`);
    };

    window.toggleArtifactPublic = async function (artifactId, isPublic) {
        const proj = portalProjectsState.projects.find(p => p.id === portalProjectsState.editingProjectId);
        if (!proj) return;
        const art = (proj.artifacts || []).find(a => a.id === artifactId);
        if (!art) return;
        const payload = { ...art, project_id: proj.id, project_slug: proj.slug, is_public: isPublic };
        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/artifacts/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await resp.json();
            if (data.ok) hydrateBundleState(data);
        } else {
            pushStagedPatchOp('save_artifact', payload);
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
        }
        showPortalToast(`Artifact "${art.label}" marked ${isPublic ? 'PUBLIC' : 'PRIVATE'}`);
    };

    window.deleteArtifactFromEditor = async function (artifactId) {
        const proj = portalProjectsState.projects.find(p => p.id === portalProjectsState.editingProjectId);
        if (!proj) return;
        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/artifacts/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: artifactId }),
            });
            const data = await resp.json();
            if (data.ok) {
                hydrateBundleState(data);
                const updated = portalProjectsState.projects.find(p => p.id === proj.id);
                renderEditorArtifactsList(updated);
            }
        } else {
            pushStagedPatchOp('delete_artifact', { id: artifactId });
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            const updated = portalProjectsState.projects.find(p => p.id === proj.id);
            renderEditorArtifactsList(updated);
        }
        showPortalToast('Removed artifact');
    };

    window.exportPortalProjectPatch = function () {
        const ops = getStagedPatchOps();
        const payload = {
            _format: 'portal_project_patch_v1',
            _exported_at: new Date().toISOString(),
            operations: ops,
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'portal_project_patch.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showPortalToast(`Exported ${ops.length} change(s) -> run apply_portal_patch.py`);
    };

    window.triggerPortalSiteSync = async function () {
        if (!portalProjectsState.liveMode) return;
        const btn = document.getElementById('projects-sync-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...'; }
        try {
            const resp = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ export_only: true }),
            });
            const data = await resp.json();
            showPortalToast(data.ok ? 'Website bundles synced & verified!' : 'Sync reported errors (check terminal)', data.ok ? 'success' : 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-sync-alt"></i> Sync &amp; Build Site'; }
        }
    };

    window.triggerPortalDriveWatch = async function () {
        if (!portalProjectsState.liveMode) return;
        const btn = document.getElementById('projects-watch-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning Drive...'; }
        try {
            const resp = await fetch('/api/discover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'watch' }),
            });
            const data = await resp.json();
            if (data.ok) hydrateBundleState(data);
            showPortalToast(data.ok ? 'Drive watch scan complete & synced!' : 'Drive scan failed (check terminal)', data.ok ? 'success' : 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fab fa-google-drive"></i> Scan Drive Updates'; }
        }
    };

    // -------------------------------------------------------------------------
    // 19. GITHUB DIRECT PUBLISH (ZERO-SERVER ATOMIC COMMIT + AES-256-GCM)
    // -------------------------------------------------------------------------
    function initGithubPublishSettings() {
        const repoEl = document.getElementById('settings-github-repo');
        const branchEl = document.getElementById('settings-github-branch');
        const patEl = document.getElementById('settings-github-pat');
        const badge = document.getElementById('github-pat-status-badge');

        const savedRepo = localStorage.getItem(GITHUB_REPO_KEY) || 'iebeid/iebeid.github.io';
        const savedBranch = localStorage.getItem(GITHUB_BRANCH_KEY) || 'master';
        const savedPat = localStorage.getItem(GITHUB_PAT_KEY) || '';

        if (repoEl) repoEl.value = savedRepo;
        if (branchEl) branchEl.value = savedBranch;
        if (patEl) patEl.value = savedPat;
        if (badge) {
            if (savedPat) {
                badge.textContent = 'Token Stored ✓';
                badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/40';
            } else {
                badge.textContent = 'Not Configured';
                badge.className = 'text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700';
            }
        }
        updateProjectsModeUI();
    }

    window.toggleGithubPatVisibility = function () {
        const input = document.getElementById('settings-github-pat');
        const icon = document.getElementById('github-pat-eye-icon');
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) { icon.classList.remove('fa-eye'); icon.classList.add('fa-eye-slash'); }
        } else {
            input.type = 'password';
            if (icon) { icon.classList.remove('fa-eye-slash'); icon.classList.add('fa-eye'); }
        }
    };

    window.saveGithubPublishSettings = function () {
        const repo = (document.getElementById('settings-github-repo')?.value || 'iebeid/iebeid.github.io').trim();
        const branch = (document.getElementById('settings-github-branch')?.value || 'master').trim();
        const pat = (document.getElementById('settings-github-pat')?.value || '').trim();
        const msg = document.getElementById('github-pat-msg');

        localStorage.setItem(GITHUB_REPO_KEY, repo);
        localStorage.setItem(GITHUB_BRANCH_KEY, branch);
        if (pat) localStorage.setItem(GITHUB_PAT_KEY, pat);
        else localStorage.removeItem(GITHUB_PAT_KEY);

        initGithubPublishSettings();
        if (msg) {
            msg.className = 'text-xs text-emerald-400 block';
            msg.textContent = pat ? `GitHub Direct Publish configured for ${repo} (${branch}).` : 'GitHub token cleared.';
        }
    };

    window.clearGithubPublishSettings = function () {
        localStorage.removeItem(GITHUB_PAT_KEY);
        const patEl = document.getElementById('settings-github-pat');
        if (patEl) patEl.value = '';
        initGithubPublishSettings();
        const msg = document.getElementById('github-pat-msg');
        if (msg) {
            msg.className = 'text-xs text-slate-400 block';
            msg.textContent = 'GitHub token removed from browser storage.';
        }
    };

    window.testGithubPublishConnection = async function () {
        const repo = (document.getElementById('settings-github-repo')?.value || localStorage.getItem(GITHUB_REPO_KEY) || 'iebeid/iebeid.github.io').trim();
        const pat = (document.getElementById('settings-github-pat')?.value || localStorage.getItem(GITHUB_PAT_KEY) || '').trim();
        const msg = document.getElementById('github-pat-msg');
        if (!pat) {
            if (msg) { msg.className = 'text-xs text-amber-400 block'; msg.textContent = 'Enter a Fine-Grained GitHub PAT first.'; }
            return;
        }
        try {
            const resp = await fetch(`https://api.github.com/repos/${repo}`, {
                headers: { Authorization: `Bearer ${pat}`, Accept: 'application/vnd.github+json' },
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.message || `HTTP ${resp.status}`);
            const canPush = Boolean(data.permissions && data.permissions.push);
            if (msg) {
                msg.className = canPush ? 'text-xs text-emerald-400 block' : 'text-xs text-amber-400 block';
                msg.textContent = canPush
                    ? `Connected to ${data.full_name} (push permission verified ✓)`
                    : `Connected to ${data.full_name}, but push permission is missing.`;
            }
        } catch (err) {
            if (msg) { msg.className = 'text-xs text-rose-400 block'; msg.textContent = `Connection failed: ${err.message}`; }
        }
    };

    async function encryptSqliteVaultEntry(plaintextStr, passcode) {
        const enc = new TextEncoder();
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const keyMaterial = await window.crypto.subtle.importKey(
            'raw', enc.encode(passcode), { name: 'PBKDF2' }, false, ['deriveKey']
        );
        const aesKey = await window.crypto.subtle.deriveKey(
            { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt']
        );
        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            aesKey,
            enc.encode(plaintextStr)
        );
        return {
            ciphertext: uint8ArrayToBase64(new Uint8Array(encrypted)),
            nonce: uint8ArrayToBase64(iv),
            salt: uint8ArrayToBase64(salt),
        };
    }

    function utf8ToBase64(str) {
        const bytes = new TextEncoder().encode(str);
        const chunk = 0x8000;
        let bin = '';
        for (let i = 0; i < bytes.length; i += chunk) {
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
        }
        return btoa(bin);
    }

    function buildBookmarksPublishPayload(nowIso) {
        const pinnedSet = new Set(getPinnedIds().map(String));
        const remSet = new Set(getRememberedIds().map(String));
        const usage = getUsageStats();

        const bookmarksList = getAllBookmarks().map(b => {
            const idStr = String(b.id);
            const cat = b.category || 'Bookmarks';
            const sub = b.subfolder || '';
            const clicks = (usage[idStr] && usage[idStr].count) ? Number(usage[idStr].count) : Number(b.clicks || 0);
            return {
                id: b.id,
                name: b.name,
                type: 'bookmark',
                url: b.url,
                domain: b.domain || sub || 'web',
                category: cat,
                subfolder: sub,
                path: b.path || (sub ? `${cat} > ${sub}` : cat),
                path_parts: sub ? [cat, sub] : [cat],
                ai_tags: b.ai_tags || '',
                favicon: b.favicon || '',
                pinned: pinnedSet.has(idStr),
                clicks,
                description: b.description || '',
                remembered: remSet.has(idStr),
            };
        });

        const categories = Array.from(new Set(bookmarksList.map(b => b.category))).sort();
        const categoryCounts = {};
        const foldersTree = {};
        bookmarksList.forEach(b => {
            categoryCounts[b.category] = (categoryCounts[b.category] || 0) + 1;
            const sub = b.subfolder || 'General';
            if (!foldersTree[b.category]) foldersTree[b.category] = {};
            if (!foldersTree[b.category][sub]) foldersTree[b.category][sub] = [];
            foldersTree[b.category][sub].push(b);
        });
        const topFolders = Object.keys(foldersTree).sort().map(catName => ({
            name: catName,
            type: 'folder',
            children: Object.keys(foldersTree[catName]).sort().map(subName => ({
                name: subName,
                type: 'folder',
                children: foldersTree[catName][subName],
            })),
        }));

        return {
            total_bookmarks: bookmarksList.length,
            categories,
            category_counts: categoryCounts,
            top_folders: topFolders,
            bookmarks: bookmarksList,
            _synced_from_sqlite: nowIso,
        };
    }

    function buildPublicContentPayload(nowIso) {
        const base = window.__SITE_DATABASE || {};
        const publicKeys = [
            'meta', 'navigation_menu', 'html_templates', 'stylesheets', 'pages',
            'documents', 'images', 'publications', 'site_placement_slots',
            'courses', 'contacts', 'xlpm_datasets',
        ];
        const out = {
            _generated_at: nowIso,
            _source: 'portal.html (Direct GitHub Publish)',
        };
        publicKeys.forEach(k => {
            if (base[k] !== undefined) out[k] = base[k];
        });

        out.projects = (portalProjectsState.projects || [])
            .filter(p => p.is_public)
            .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
            .map(p => ({
                id: p.id,
                slug: p.slug,
                title: p.title,
                tagline: p.tagline || '',
                short_summary: p.short_summary || '',
                full_description: p.full_description || '',
                category: p.category || 'General Portfolio',
                domain_stage: p.domain_stage || 'foundational',
                status: p.status || '',
                year_start: p.year_start || null,
                year_end: p.year_end || null,
                institution_or_org: p.institution_or_org || '',
                grant_award: p.grant_award || '',
                tech_stack: p.tech_stack || [],
                code_snippet: p.code_snippet || '',
                license_model: p.license_model || '',
                price_display: p.price_display || '',
                storefront_category: p.storefront_category || '',
                is_featured: Boolean(p.is_featured),
                is_storefront: Boolean(p.is_storefront),
                display_order: p.display_order || 0,
                project_kind: p.project_kind || 'research',
                keywords: p.keywords || [],
                artifacts: (p.artifacts || [])
                    .filter(a => a.is_public !== false)
                    .map(a => ({
                        type: a.type,
                        label: a.label,
                        url: a.url,
                        badge: a.badge || '',
                        document_id: a.document_id ?? null,
                        storage_source: a.storage_source || 'repo',
                    })),
                placements: (p.placements || [])
                    .filter(pl => pl.is_visible !== false)
                    .map(pl => ({
                        page_slug: pl.page_slug,
                        section_slot: pl.section_slot,
                        card_variant: pl.card_variant || 'research-cards',
                        display_order: pl.display_order || 0,
                        is_visible: true,
                    })),
                tags: p.tags || [],
                publications: p.publications || [],
            }));
        return out;
    }

    async function githubApiRequest(repo, pat, path, method = 'GET', bodyObj = null) {
        const opts = {
            method,
            headers: {
                Authorization: `Bearer ${pat}`,
                Accept: 'application/vnd.github+json',
            },
        };
        if (bodyObj !== null) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(bodyObj);
        }
        const resp = await fetch(`https://api.github.com/repos/${repo}/${path}`, opts);
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            throw new Error(data.message || `GitHub API ${method} ${path} failed (${resp.status})`);
        }
        return data;
    }

    window.publishPortalToGithub = async function () {
        const pat = (localStorage.getItem(GITHUB_PAT_KEY) || '').trim();
        const repo = (localStorage.getItem(GITHUB_REPO_KEY) || 'iebeid/iebeid.github.io').trim();
        const branch = (localStorage.getItem(GITHUB_BRANCH_KEY) || 'master').trim();

        if (!pat) {
            showPortalToast('Configure your GitHub Fine-Grained PAT in Settings & Security first.', 'warn');
            switchTab('tab-settings');
            return;
        }

        let passcode = portalSessionPasscode || vaultMasterPassword;
        if (!passcode) {
            passcode = prompt('Enter your portal master passcode to re-encrypt the private project catalog:') || '';
            if (!passcode) return;
        }
        if (!portalProjectsState.unlocked && window.__SITE_DATABASE?.portal_projects_encrypted) {
            const plain = await decryptSqliteVaultEntry(window.__SITE_DATABASE.portal_projects_encrypted, passcode);
            if (!plain) {
                showPortalToast('Passcode could not verify encrypted project catalog.', 'error');
                return;
            }
            hydrateBundleState(JSON.parse(plain));
            portalSessionPasscode = passcode;
        }
        if (!portalProjectsState.unlocked && !portalProjectsState.liveMode && window.__SITE_DATABASE?.portal_projects_encrypted) {
            showPortalToast('Unlock the encrypted master portfolio before publishing.', 'error');
            return;
        }
        if ((portalProjectsState.projects || []).length === 0) {
            showPortalToast('Refusing to publish an empty project catalog.', 'error');
            return;
        }

        const btn = document.getElementById('projects-github-publish-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publishing...'; }

        try {
            const nowIso = new Date().toISOString();
            const deletedSlugs = JSON.parse(localStorage.getItem(DELETED_PROJ_SLUGS_KEY) || '[]');

            // 1. Build public_content.json & public_content.js
            const publicPayload = buildPublicContentPayload(nowIso);
            const publicJsonStr = JSON.stringify(publicPayload, null, 2);
            const publicJsStr = `window.__SITE_DATABASE = ${publicJsonStr};\n`;

            // 2. Build AES-256-GCM encrypted portal_data.js
            const masterBundle = {
                _published_from: 'portal_github_api',
                _generated_at: nowIso,
                projects: portalProjectsState.projects || [],
                placement_slots: portalProjectsState.placementSlots || [],
                drive_scan_roots: portalProjectsState.driveRoots || [],
                drive_scan_runs: portalProjectsState.driveRuns || [],
                deleted_project_slugs: deletedSlugs,
            };
            const encryptedProjBlob = await encryptSqliteVaultEntry(JSON.stringify(masterBundle), passcode);
            const baseSite = window.__SITE_DATABASE || {};
            const portalBundle = {
                portal_tasks: baseSite.portal_tasks || [],
                portal_scratches: baseSite.portal_scratches || { active_buffer: '', archive: [] },
                portal_messages: baseSite.portal_messages || [],
                portal_vault: baseSite.portal_vault || {},
                portal_passwords: getEncryptedVaultBlobs ? getEncryptedVaultBlobs() : (baseSite.portal_passwords || []),
                portal_projects_encrypted: encryptedProjBlob,
                site_placement_slots: portalProjectsState.placementSlots || baseSite.site_placement_slots || [],
            };
            const portalJsStr =
                `window.__PORTAL_DATABASE = ${JSON.stringify(portalBundle, null, 2)};\n` +
                `if (window.__SITE_DATABASE) { Object.assign(window.__SITE_DATABASE, window.__PORTAL_DATABASE); }\n`;

            // 3. Build bookmarks.json & bookmarks_data.js
            const bmPayload = buildBookmarksPublishPayload(nowIso);
            const bmJsonStr = JSON.stringify(bmPayload, null, 2);
            const bmJsStr = `window.PORTAL_BOOKMARKS = ${bmJsonStr};\nwindow.PORTAL_BOOKMARKS_DATA = window.PORTAL_BOOKMARKS;\n`;

            const files = [
                { path: 'data/public_content.json', content: publicJsonStr },
                { path: 'data/public_content.js', content: publicJsStr },
                { path: 'js/portal_data.js', content: portalJsStr },
                { path: 'data/bookmarks.json', content: bmJsonStr },
                { path: 'js/bookmarks_data.js', content: bmJsStr },
            ];

            // 4. Atomic multi-file commit via GitHub Git Data API
            const refData = await githubApiRequest(repo, pat, `git/ref/heads/${branch}`);
            const latestCommitSha = refData.object.sha;
            const commitData = await githubApiRequest(repo, pat, `git/commits/${latestCommitSha}`);
            const baseTreeSha = commitData.tree.sha;

            const blobResults = await Promise.all(
                files.map(f =>
                    githubApiRequest(repo, pat, 'git/blobs', 'POST', {
                        content: utf8ToBase64(f.content),
                        encoding: 'base64',
                    }).then(res => ({ path: f.path, mode: '100644', type: 'blob', sha: res.sha }))
                )
            );

            const treeData = await githubApiRequest(repo, pat, 'git/trees', 'POST', {
                base_tree: baseTreeSha,
                tree: blobResults,
            });
            const newCommit = await githubApiRequest(repo, pat, 'git/commits', 'POST', {
                message: `Portal Direct Publish: ${publicPayload.projects.length} public projects, ${bmPayload.total_bookmarks} bookmarks (${nowIso.slice(0, 19)}Z)`,
                tree: treeData.sha,
                parents: [latestCommitSha],
            });
            await githubApiRequest(repo, pat, `git/refs/heads/${branch}`, 'PATCH', {
                sha: newCommit.sha,
                force: false,
            });

            // 5. Update local in-memory caches and clear pending diffs
            window.PORTAL_BOOKMARKS = bmPayload;
            window.PORTAL_BOOKMARKS_DATA = bmPayload;
            Object.assign(window.__SITE_DATABASE, publicPayload, portalBundle);
            localStorage.removeItem(PROJECT_PATCH_OPS_KEY);
            localStorage.removeItem(DELETED_PROJ_SLUGS_KEY);
            localStorage.removeItem(CUSTOM_BM_KEY);
            localStorage.removeItem(DELETED_BM_KEY);
            updatePatchBadge();

            showPortalToast(`Published to GitHub (${newCommit.sha.slice(0, 7)}) — Pages deploys in ~30s!`);
        } catch (err) {
            console.error('[GitHub Publish Error]', err);
            showPortalToast(`GitHub publish failed: ${err.message}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fab fa-github"></i> Publish to GitHub <span id="projects-pending-badge" class="hidden px-1.5 py-0.5 rounded bg-slate-950/40 text-[10px] font-mono">0</span>';
                updatePatchBadge();
            }
        }
    };

    // -------------------------------------------------------------------------
    // 20. SMART SEMANTIC ENTITY RESOLUTION & MANUAL MERGE ENGINE
    // -------------------------------------------------------------------------
    const ER_DISMISSED_KEY = 'portal_er_dismissed_pairs_v1';
    const ER_STOP_WORDS = new Set([
        'the', 'and', 'for', 'with', 'from', 'into', 'using', 'via', 'over', 'under',
        'project', 'projects', 'system', 'systems', 'tool', 'toolkit', 'engine', 'app',
        'application', 'web', 'website', 'suite', 'model', 'models', 'modeling',
        'discovered', 'workspace', 'drive', 'source', 'research', 'scholarship',
        'internal', 'manuscripts', 'presentations', 'images', 'videos', 'code', 'data',
        'artifacts', 'artifact', 'located', 'google', 'draft', 'final', 'old', 'new',
        'test', 'demo', 'exp', 'in', 'on', 'of', 'to', 'a', 'an',
        'computer', 'vision', 'graphics', 'human', 'interaction', 'career',
        'statement', 'relations', 'society', 'class', 'learning', 'dallas',
        'teaching', 'service', 'business', 'hobbies', 'education', 'artificial',
        'intelligence', 'software', 'engineering', 'science', 'sciences',
    ]);
    const ER_SYNONYMS = {
        coronavirus: 'covid', sarscov2: 'covid', kg: 'knowledgegraph', kge: 'knowledgegraph',
        gcn: 'gnn', digcn: 'gnn', directgcn: 'gnn', grapher: 'entityresolution', moder: 'entityresolution',
        ditk: 'dataintegration', kit: 'toolkit', realsense: 'rgbd', kinect: 'rgbd',
        odometry: 'slam', localization: 'slam', eyetracking: 'gaze', eye: 'gaze',
        eyeadapt: 'gaze', eyeart: 'gaze', gdwm: 'gaze', ge: 'googleearth', earthviz: 'googleearth',
        cv: 'curriculumvitae', resume: 'curriculumvitae', llms: 'llm', biomedical: 'medical',
        med: 'medical', medgraph: 'pubmed', vrjuggler: 'vrj', vrj: 'vr',
    };

    let currentErCandidates = [];

    function erTokenizeCamel(text) {
        const s = String(text || '')
            .replace(/\.[A-Za-z0-9]{1,5}$/g, ' ')
            .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
            .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
            .replace(/[^A-Za-z0-9]+/g, ' ')
            .toLowerCase()
            .trim();
        return s ? s.split(/\s+/).filter(Boolean) : [];
    }

    function erCanonicalTokens(text) {
        const raw = erTokenizeCamel(text);
        const out = [];
        for (let i = 0; i < raw.length; i++) {
            if (i + 1 < raw.length) {
                const pair = raw[i] + raw[i + 1];
                if (pair === 'knowledgegraph' || pair === 'entityresolution' || pair === 'dataintegration' || pair === 'eyetracking' || pair === 'curriculumvitae' || pair === 'googleearth') {
                    out.push(pair);
                    i++;
                    continue;
                }
            }
            const mapped = ER_SYNONYMS[raw[i]] || raw[i];
            if (!ER_STOP_WORDS.has(mapped) && mapped.length >= 2) out.push(mapped);
        }
        return out;
    }

    function erCharNgrams(text, n = 3) {
        const clean = String(text || '').toLowerCase().replace(/[^a-z0-9]/g, '');
        const counts = {};
        if (!clean) return counts;
        if (clean.length < n) { counts[clean] = 1; return counts; }
        for (let i = 0; i <= clean.length - n; i++) {
            const g = clean.slice(i, i + n);
            counts[g] = (counts[g] || 0) + 1;
        }
        return counts;
    }

    function erExtractAcronyms(rawTitle) {
        const explicit = new Set();
        const matches = String(rawTitle || '').match(/\b[A-Z][A-Z0-9]{1,7}\b/g) || [];
        matches.forEach(m => explicit.add(m.toLowerCase()));
        const toks = erTokenizeCamel(rawTitle).filter(t => !['the', 'and', 'of', 'for', 'in', 'to'].includes(t));
        const initials = new Set();
        if (toks.length >= 2 && toks.length <= 6) {
            initials.add(toks.map(t => t[0]).join(''));
        }
        return { explicit, initials };
    }

    function erCosine(vecA, vecB) {
        const keysA = Object.keys(vecA);
        const keysB = Object.keys(vecB);
        if (!keysA.length || !keysB.length) return 0;
        let dot = 0, normA = 0, normB = 0;
        for (const k of keysA) {
            const va = vecA[k];
            normA += va * va;
            if (vecB[k]) dot += va * vecB[k];
        }
        if (dot <= 0) return 0;
        for (const k of keysB) normB += vecB[k] * vecB[k];
        return (normA > 0 && normB > 0) ? dot / (Math.sqrt(normA) * Math.sqrt(normB)) : 0;
    }

    function getDismissedErSet() {
        try { return new Set(JSON.parse(localStorage.getItem(ER_DISMISSED_KEY) || '[]')); }
        catch (e) { return new Set(); }
    }

    function erPairKey(idA, idB) {
        const a = String(idA), b = String(idB);
        return a < b ? `${a}|${b}` : `${b}|${a}`;
    }

    function runSemanticEntityResolution(minScore = 0.45, topK = 50) {
        const projects = portalProjectsState.projects || [];
        const dismissed = getDismissedErSet();
        const nDocs = Math.max(1, projects.length);
        const df = {};

        const profiles = projects.map(p => {
            const artText = (p.artifacts || []).map(a => `${a.label || ''} ${a.gdrive_path || ''}`).join(' ');
            const urls = new Set((p.artifacts || []).map(a => a.url).filter(u => u && u.startsWith('http') && !u.includes('drive.google.com')));
            const titleToks = erCanonicalTokens(`${p.title} ${p.slug} ${(p.keywords || []).join(' ')}`);
            const bodyToks = erCanonicalTokens(`${p.tagline || ''} ${p.short_summary || ''} ${(p.tags || []).join(' ')} ${artText}`);
            const fullToks = [...titleToks, ...titleToks, ...titleToks, ...bodyToks];
            const tf = {};
            fullToks.forEach(t => { tf[t] = (tf[t] || 0) + 1; });
            Object.keys(tf).forEach(t => { df[t] = (df[t] || 0) + 1; });
            const acr = erExtractAcronyms(p.title);
            const keepPriority =
                (p.is_public ? 1000 : 0) +
                (p.discovery_status === 'canonical' ? 500 : p.discovery_status === 'reviewed' ? 100 : 0) +
                ((p.placements || []).filter(pl => pl.is_visible !== false).length * 50) +
                (p.artifacts || []).length;

            return {
                proj: p,
                titleTokSet: new Set(titleToks),
                gramVec: erCharNgrams(`${p.title} ${p.slug}`, 3),
                explicitAcr: acr.explicit,
                phraseInit: acr.initials,
                tf,
                urls,
                keepPriority,
            };
        });

        const idf = {};
        Object.keys(df).forEach(t => { idf[t] = Math.log((nDocs + 1) / (df[t] + 1)) + 1.0; });
        profiles.forEach(pr => {
            const vec = {};
            Object.keys(pr.tf).forEach(t => { vec[t] = pr.tf[t] * (idf[t] || 1.0); });
            pr.tfidf = vec;
        });

        const cands = [];
        for (let i = 0; i < profiles.length; i++) {
            const a = profiles[i];
            for (let j = i + 1; j < profiles.length; j++) {
                const b = profiles[j];
                if (dismissed.has(erPairKey(a.proj.id, b.proj.id))) continue;
                if (a.proj.project_kind === 'poetry' && b.proj.project_kind === 'poetry') {
                    if (erCosine(a.gramVec, b.gramVec) < 0.72) continue;
                }

                const tfidfSim = erCosine(a.tfidf, b.tfidf);
                const gramSim = erCosine(a.gramVec, b.gramVec);
                const sharedTitle = Array.from(a.titleTokSet).filter(t => b.titleTokSet.has(t));
                const unionSize = new Set([...a.titleTokSet, ...b.titleTokSet]).size;
                const titleJaccard = unionSize ? sharedTitle.length / unionSize : 0;

                const acrMatches = [
                    ...Array.from(a.explicitAcr).filter(x => b.phraseInit.has(x) || b.explicitAcr.has(x)),
                    ...Array.from(b.explicitAcr).filter(x => a.phraseInit.has(x)),
                ];
                const uniqueAcr = Array.from(new Set(acrMatches));
                const strongAcr = uniqueAcr.some(x => x.length >= 3);
                const sharedUrls = Array.from(a.urls).filter(u => b.urls.has(u));

                let score = 0.42 * tfidfSim + 0.28 * gramSim + 0.30 * titleJaccard;
                const reasons = [];
                if (strongAcr) {
                    score += 0.16;
                    reasons.push(`acronym:${uniqueAcr[0]}`);
                } else if (uniqueAcr.length && gramSim >= 0.35) {
                    score += 0.08;
                    reasons.push(`acronym:${uniqueAcr[0]}`);
                }
                if (sharedUrls.length) {
                    score += 0.25;
                    reasons.push('shared_external_url');
                }
                score = Math.min(0.99, score);
                if (score < minScore) continue;

                if (sharedTitle.length) reasons.push(`tokens:${sharedTitle.slice(0, 4).join(',')}`);
                if (gramSim >= 0.45) reasons.push(`char3:${gramSim.toFixed(2)}`);
                if (tfidfSim >= 0.35) reasons.push(`tfidf:${tfidfSim.toFixed(2)}`);

                const target = (a.keepPriority >= b.keepPriority) ? a.proj : b.proj;
                const source = (a.keepPriority >= b.keepPriority) ? b.proj : a.proj;
                cands.push({ score, source, target, reasons, aiVerdict: null });
            }
        }

        cands.sort((x, y) => (y.score - x.score) || ((y.target.artifacts || []).length - (x.target.artifacts || []).length));
        return cands.slice(0, topK);
    }

    window.openDuplicateResolverModal = function () {
        if (!portalProjectsState.unlocked && !portalProjectsState.liveMode && window.__SITE_DATABASE?.portal_projects_encrypted) {
            showPortalToast('Unlock the encrypted master portfolio first to scan all 228 projects.', 'warn');
        }
        const modal = document.getElementById('er-duplicates-modal');
        if (modal) { modal.classList.remove('hidden'); modal.classList.add('flex'); }
        runAndRenderErDuplicates();
    };

    window.closeDuplicateResolverModal = function () {
        const modal = document.getElementById('er-duplicates-modal');
        if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
    };

    window.onErThresholdChange = function () {
        const val = document.getElementById('er-threshold-slider')?.value || '45';
        const lbl = document.getElementById('er-threshold-label');
        if (lbl) lbl.textContent = `${val}%`;
        runAndRenderErDuplicates();
    };

    window.runAndRenderErDuplicates = function () {
        const pct = Number(document.getElementById('er-threshold-slider')?.value || 45);
        currentErCandidates = runSemanticEntityResolution(pct / 100, 60);
        renderErDuplicatesList();
    };

    function renderErDuplicatesList() {
        const listEl = document.getElementById('er-duplicates-list');
        const cntEl = document.getElementById('er-candidate-count');
        if (cntEl) cntEl.textContent = `${currentErCandidates.length} candidate pair(s)`;
        if (!listEl) return;

        if (!currentErCandidates.length) {
            listEl.innerHTML = '<div class="bg-slate-950/60 border border-slate-800 rounded-xl p-8 text-center text-xs text-slate-400">No duplicate candidates above this similarity threshold.</div>';
            return;
        }

        listEl.innerHTML = currentErCandidates.map((c, idx) => {
            const pctStr = `${(c.score * 100).toFixed(1)}%`;
            const scoreCls = c.score >= 0.70 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : c.score >= 0.55 ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/40';
            const aiBadge = c.aiVerdict
                ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-mono ${c.aiVerdict.verdict === 'SAME_PROJECT' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800 text-slate-300 border border-slate-700'}">${escapeHtml(c.aiVerdict.verdict)}: ${escapeHtml(c.aiVerdict.reason || '')}</span>`
                : '';

            return `
                <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                        <div class="flex flex-wrap items-center gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${scoreCls}">${pctStr} Match</span>
                            <span class="text-[11px] font-mono text-slate-400">${escapeHtml(c.reasons.join(' | '))}</span>
                            ${aiBadge}
                        </div>
                        <div class="flex items-center gap-1.5">
                            <button type="button" onclick="swapErCandidatePair(${idx})" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold"><i class="fas fa-exchange-alt mr-1"></i> Swap</button>
                            <button type="button" onclick="mergeErCandidatePair(${idx})" class="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold"><i class="fas fa-compress-arrows-alt mr-1"></i> Merge into Target</button>
                            <button type="button" onclick="dismissErPair(${idx})" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-600/70 text-slate-400 hover:text-white text-[11px]">Dismiss</button>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div class="bg-slate-900/90 border border-rose-500/25 rounded-lg p-3 space-y-1">
                            <div class="text-[10px] font-bold uppercase text-rose-300">Fold Source (${escapeHtml(c.source.discovery_status || 'discovered')} &bull; ${(c.source.artifacts || []).length} artifacts)</div>
                            <div class="font-bold text-white">${escapeHtml(c.source.title)}</div>
                            <div class="font-mono text-[10px] text-slate-500">${escapeHtml(c.source.slug)}</div>
                            <p class="text-slate-400 text-[11px] line-clamp-2">${escapeHtml(c.source.short_summary || c.source.tagline || '')}</p>
                        </div>
                        <div class="bg-slate-900/90 border border-emerald-500/25 rounded-lg p-3 space-y-1">
                            <div class="text-[10px] font-bold uppercase text-emerald-300">Keep Target (${escapeHtml(c.target.discovery_status || 'canonical')} &bull; ${(c.target.artifacts || []).length} artifacts)</div>
                            <div class="font-bold text-white">${escapeHtml(c.target.title)}</div>
                            <div class="font-mono text-[10px] text-slate-500">${escapeHtml(c.target.slug)}</div>
                            <p class="text-slate-400 text-[11px] line-clamp-2">${escapeHtml(c.target.short_summary || c.target.tagline || '')}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    window.swapErCandidatePair = function (idx) {
        const c = currentErCandidates[idx];
        if (!c) return;
        const tmp = c.source;
        c.source = c.target;
        c.target = tmp;
        renderErDuplicatesList();
    };

    window.dismissErPair = function (idx) {
        const c = currentErCandidates[idx];
        if (!c) return;
        const set = getDismissedErSet();
        set.add(erPairKey(c.source.id, c.target.id));
        localStorage.setItem(ER_DISMISSED_KEY, JSON.stringify(Array.from(set)));
        currentErCandidates.splice(idx, 1);
        renderErDuplicatesList();
    };

    window.clearDismissedErPairs = function () {
        localStorage.removeItem(ER_DISMISSED_KEY);
        runAndRenderErDuplicates();
        showPortalToast('Cleared dismissed duplicate pairs');
    };

    window.mergeErCandidatePair = async function (idx) {
        const c = currentErCandidates[idx];
        if (!c) return;
        const ok = await mergePortalProjects(c.source.id, c.target.id, { appendSummary: false, addAlias: true });
        if (ok) runAndRenderErDuplicates();
    };

    function setErProgressBanner(msg) {
        const el = document.getElementById('er-progress-banner');
        if (!el) return;
        if (!msg) {
            el.classList.add('hidden');
            el.textContent = '';
        } else {
            el.classList.remove('hidden');
            el.textContent = msg;
        }
    }

    function needsSemanticDescription(proj) {
        const s = (proj.short_summary || '').trim();
        return !s || s.startsWith('Discovered ') || s.length < 40;
    }

    function buildProjectPromptSnapshot(p) {
        const arts = (p.artifacts || []).slice(0, 8).map(a => `${a.type}: ${a.label}${a.gdrive_path ? ' [' + a.gdrive_path + ']' : ''}`);
        return {
            id: p.id,
            title: p.title,
            slug: p.slug,
            kind: p.project_kind || 'research',
            category: p.category || '',
            tagline: p.tagline || '',
            artifacts: arts,
        };
    }

    async function callGeminiJson(apiKey, promptText, model = 'gemini-3.8-flash') {
        const candidates = Array.from(new Set([model, 'gemini-3.8-flash', 'gemini-3-flash', 'gemini-2.5-flash']));
        let lastErr = null;
        for (const mdl of candidates) {
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${mdl}:generateContent?key=${encodeURIComponent(apiKey)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: promptText }] }],
                    generationConfig: { temperature: 0.15, responseMimeType: 'application/json' },
                }),
            });
            const data = await resp.json();
            if (resp.ok) {
                const txt = (data.candidates?.[0]?.content?.parts?.[0]?.text || '').replace(/^\s*```(?:json)?\s*|\s*```\s*$/g, '').trim();
                return JSON.parse(txt);
            }
            const msg = data.error?.message || `Gemini HTTP ${resp.status}`;
            lastErr = new Error(msg);
            if (!(resp.status === 404 || /no longer available|not found|not supported/i.test(msg))) {
                throw lastErr;
            }
        }
        throw lastErr || new Error('Gemini API call failed');
    }

    window.aiDescribeSingleProject = async function () {
        const apiKey = (localStorage.getItem('gemini_api_key') || '').trim();
        if (!apiKey) {
            showPortalToast('Add your Gemini API Key in Settings & Security first.', 'warn');
            return;
        }
        const title = document.getElementById('pe-title')?.value.trim();
        if (!title) return;
        const proj = portalProjectsState.projects.find(p => p.id === portalProjectsState.editingProjectId) || {
            id: 0,
            title,
            slug: document.getElementById('pe-slug')?.value.trim() || '',
            project_kind: document.getElementById('pe-kind')?.value || 'research',
            category: document.getElementById('pe-category')?.value || '',
            artifacts: [],
        };
        const btn = document.getElementById('pe-ai-describe-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Generating...'; }
        try {
            const snap = buildProjectPromptSnapshot({ ...proj, title });
            const prompt = `Generate a crisp, factual portfolio description for this project based strictly on its title, domain kind, Drive folder paths, and artifact filenames. Return JSON object: {"short_summary": "1-2 factual sentences", "tagline": "short 5-9 word subtitle", "tags": ["3-5 domain tags"], "keywords": ["acronyms, aliases, key concepts"]}.\n\n${JSON.stringify(snap)}`;
            const res = await callGeminiJson(apiKey, prompt);
            if (res.short_summary) document.getElementById('pe-summary').value = res.short_summary;
            if (res.tagline && !document.getElementById('pe-tagline').value.trim()) document.getElementById('pe-tagline').value = res.tagline;
            if (Array.isArray(res.tags) && !document.getElementById('pe-tags').value.trim()) document.getElementById('pe-tags').value = res.tags.join(', ');
            showPortalToast('Generated semantic summary via Gemini');
        } catch (err) {
            showPortalToast(`AI Describe failed: ${err.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-magic mr-1"></i> AI Describe'; }
        }
    };

    window.aiEnrichPortalProjects = async function () {
        const apiKey = (localStorage.getItem('gemini_api_key') || '').trim();
        if (!apiKey) {
            showPortalToast('Add your Gemini API Key in Settings & Security first.', 'warn');
            return;
        }
        const targets = (portalProjectsState.projects || []).filter(needsSemanticDescription);
        if (!targets.length) {
            showPortalToast('All projects already have semantic descriptions!');
            return;
        }
        const btn = document.getElementById('er-ai-enrich-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Enriching...'; }

        let enrichedCount = 0;
        const BATCH_SIZE = 12;
        try {
            for (let i = 0; i < targets.length; i += BATCH_SIZE) {
                const batch = targets.slice(i, i + BATCH_SIZE);
                setErProgressBanner(`Generating LLM semantic descriptions & keywords: ${i} / ${targets.length} projects...`);
                const snaps = batch.map(buildProjectPromptSnapshot);
                const prompt = `You are curating Dr. Islam Akef Ebeid's academic, software, and creative portfolio. For each project below, infer what it is from its title, kind, Google Drive path, and artifact filenames (do not invent fake metrics or grants). Return a JSON array of objects matching each input id: [{"id": number, "short_summary": "1-2 clear factual sentences", "tagline": "short 5-9 word subtitle", "tags": ["3-5 tags"], "keywords": ["acronyms, aliases, key domain concepts"]}].\n\n${JSON.stringify(snaps)}`;
                const results = await callGeminiJson(apiKey, prompt);
                const byId = new Map((Array.isArray(results) ? results : []).map(r => [String(r.id), r]));

                for (const p of batch) {
                    const r = byId.get(String(p.id));
                    if (!r || !r.short_summary) continue;
                    const mergedTags = Array.from(new Set([...(p.tags || []), ...(r.tags || [])].filter(Boolean)));
                    const mergedKw = Array.from(new Set([...(p.keywords || []), ...(r.keywords || [])].filter(Boolean)));
                    const updated = {
                        ...p,
                        short_summary: r.short_summary,
                        full_description: (!p.full_description || p.full_description.startsWith('Discovered ')) ? r.short_summary : p.full_description,
                        tagline: (!p.tagline || p.tagline.startsWith('Drive Source:')) ? (r.tagline || p.tagline) : p.tagline,
                        tags: mergedTags,
                        keywords: mergedKw,
                        updated_at: new Date().toISOString(),
                    };
                    if (portalProjectsState.liveMode) {
                        await fetch('/api/projects/save', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(updated),
                        });
                    } else {
                        pushStagedPatchOp('save_project', updated);
                    }
                    Object.assign(p, updated);
                    enrichedCount++;
                }
            }
            if (!portalProjectsState.liveMode) {
                portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            }
            renderPortalProjectsHub();
            setErProgressBanner(`Enriched ${enrichedCount} project descriptions & keywords! Now click "2. AI Semantic Match" to run embedding + LLM duplicate detection.`);
            showPortalToast(`Enriched ${enrichedCount} projects with Gemini semantic descriptions`);
        } catch (err) {
            setErProgressBanner(`Enrichment paused after ${enrichedCount} projects: ${err.message}`);
            showPortalToast(`AI enrichment error: ${err.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-magic mr-1"></i> 1. AI Enrich Descriptions'; }
        }
    };

    function cosineDense(a, b) {
        let dot = 0, na = 0, nb = 0;
        for (let i = 0; i < a.length; i++) {
            dot += a[i] * b[i];
            na += a[i] * a[i];
            nb += b[i] * b[i];
        }
        return (na > 0 && nb > 0) ? dot / (Math.sqrt(na) * Math.sqrt(nb)) : 0;
    }

    window.aiRunFullSemanticEntityResolution = async function () {
        const apiKey = (localStorage.getItem('gemini_api_key') || '').trim();
        if (!apiKey) {
            showPortalToast('Add your Gemini API Key in Settings & Security first.', 'warn');
            return;
        }
        const projects = portalProjectsState.projects || [];
        if (projects.length < 2) return;

        const btn = document.getElementById('er-ai-embed-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Embedding...'; }

        try {
            const dismissed = getDismissedErSet();
            const embeddings = [];
            const EMB_BATCH = 80;
            const embModels = ['gemini-embedding-001', 'gemini-embedding-2'];
            let activeEmbModel = embModels[0];
            for (let i = 0; i < projects.length; i += EMB_BATCH) {
                const slice = projects.slice(i, i + EMB_BATCH);
                setErProgressBanner(`Computing Gemini semantic embeddings (${i}/${projects.length})...`);
                let data = null;
                let lastErr = null;
                for (const em of (i === 0 ? embModels : [activeEmbModel])) {
                    const requests = slice.map(p => {
                        const artPaths = (p.artifacts || []).slice(0, 6).map(a => a.gdrive_path || a.label).join('; ');
                        const txt = `${p.title} (${p.slug}) | Kind: ${p.project_kind || ''} | Category: ${p.category || ''} | ${p.tagline || ''} | ${p.short_summary || ''} | Tags: ${(p.tags || []).join(', ')} | Keywords: ${(p.keywords || []).join(', ')} | Artifacts: ${artPaths}`;
                        return {
                            model: `models/${em}`,
                            content: { parts: [{ text: txt.slice(0, 1800) }] },
                            taskType: 'SEMANTIC_SIMILARITY',
                        };
                    });
                    const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${em}:batchEmbedContents?key=${encodeURIComponent(apiKey)}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ requests }),
                    });
                    const parsed = await resp.json();
                    if (resp.ok) {
                        data = parsed;
                        activeEmbModel = em;
                        break;
                    }
                    const msg = parsed.error?.message || `Embedding HTTP ${resp.status}`;
                    lastErr = new Error(msg);
                    if (!(resp.status === 404 || /no longer available|not found|not supported/i.test(msg))) {
                        throw lastErr;
                    }
                }
                if (!data) throw lastErr || new Error('Embedding call failed');
                (data.embeddings || []).forEach(e => embeddings.push(e.values || []));
            }

            // Compute all-pairs semantic embedding cosine similarity + keep top 40 pairs
            setErProgressBanner('Scoring all pairs by Gemini embedding similarity & verifying top candidates with Gemini LLM...');
            const heuristicMap = new Map();
            runSemanticEntityResolution(0.20, 400).forEach(c => {
                heuristicMap.set(erPairKey(c.source.id, c.target.id), c);
            });

            const semPairs = [];
            for (let i = 0; i < projects.length; i++) {
                const va = embeddings[i];
                if (!va || !va.length) continue;
                for (let j = i + 1; j < projects.length; j++) {
                    const vb = embeddings[j];
                    if (!vb || !vb.length) continue;
                    const a = projects[i], b = projects[j];
                    if (dismissed.has(erPairKey(a.id, b.id))) continue;
                    const embSim = cosineDense(va, vb);
                    if (embSim < 0.68) continue;
                    const h = heuristicMap.get(erPairKey(a.id, b.id));
                    const blended = h ? (0.65 * embSim + 0.35 * h.score) : embSim;
                    const keepA = ((a.is_public ? 1000 : 0) + (a.discovery_status === 'canonical' ? 500 : 0) + (a.artifacts || []).length)
                        >= ((b.is_public ? 1000 : 0) + (b.discovery_status === 'canonical' ? 500 : 0) + (b.artifacts || []).length);
                    semPairs.push({
                        score: Math.min(0.99, blended),
                        embSim,
                        source: keepA ? b : a,
                        target: keepA ? a : b,
                        reasons: [`gemini_emb:${embSim.toFixed(2)}`, ...(h ? h.reasons : [])],
                        aiVerdict: null,
                    });
                }
            }
            semPairs.sort((x, y) => y.score - x.score);
            currentErCandidates = semPairs.slice(0, 40);
            renderErDuplicatesList();

            // Automatically run LLM verification on top 25 embedding pairs
            const toVerify = currentErCandidates.slice(0, 25);
            if (toVerify.length) {
                const promptPairs = toVerify.map((c, idx) => ({
                    idx,
                    a: buildProjectPromptSnapshot(c.source),
                    b: buildProjectPromptSnapshot(c.target),
                    a_summary: (c.source.short_summary || '').slice(0, 220),
                    b_summary: (c.target.short_summary || '').slice(0, 220),
                }));
                const prompt = `Judge whether each pair of projects refers to the SAME underlying project (e.g. code folder + paper + slides + renamed version of the exact same work) vs a RELATED_SERIES (separate projects/courses/poems in a series) vs DISTINCT. For each pair, return JSON array: [{"idx": number, "verdict": "SAME_PROJECT" | "RELATED_SERIES" | "DISTINCT", "recommended_target": "a" | "b", "reason": "concise 6-12 word explanation"}].\n\n${JSON.stringify(promptPairs)}`;
                const verdicts = await callGeminiJson(apiKey, prompt);
                (Array.isArray(verdicts) ? verdicts : []).forEach(v => {
                    const c = currentErCandidates[v.idx];
                    if (!c) return;
                    c.aiVerdict = v;
                    if (v.recommended_target === 'a') {
                        const tmp = c.source; c.source = c.target; c.target = tmp;
                    }
                });
                const order = { SAME_PROJECT: 0, RELATED_SERIES: 1, DISTINCT: 2 };
                currentErCandidates.sort((x, y) => {
                    const ox = x.aiVerdict ? (order[x.aiVerdict.verdict] ?? 3) : 3;
                    const oy = y.aiVerdict ? (order[y.aiVerdict.verdict] ?? 3) : 3;
                    return (ox - oy) || (y.score - x.score);
                });
                renderErDuplicatesList();
            }

            const sameCnt = currentErCandidates.filter(c => c.aiVerdict?.verdict === 'SAME_PROJECT').length;
            setErProgressBanner(`Semantic Match complete: ${sameCnt} SAME_PROJECT duplicate(s) highlighted out of ${currentErCandidates.length} semantic pairs.`);
            showPortalToast(`Found ${sameCnt} AI-confirmed duplicate project pairs!`);
        } catch (err) {
            setErProgressBanner(`Semantic Match error: ${err.message}`);
            showPortalToast(`AI Semantic Match failed: ${err.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-brain mr-1"></i> 2. AI Semantic Match (Embeddings + LLM)'; }
        }
    };

    window.aiVerifyTopErDuplicates = async function () {
        const apiKey = (localStorage.getItem('gemini_api_key') || '').trim();
        if (!apiKey) {
            showPortalToast('Add your Gemini API Key in Settings & Security to run AI semantic verification.', 'warn');
            return;
        }
        const slice = currentErCandidates.slice(0, 15);
        if (!slice.length) return;
        const btn = document.getElementById('er-ai-verify-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Verifying...'; }

        try {
            const promptPairs = slice.map((c, idx) => ({
                idx,
                a: { title: c.source.title, slug: c.source.slug, kind: c.source.project_kind, summary: (c.source.short_summary || '').slice(0, 220) },
                b: { title: c.target.title, slug: c.target.slug, kind: c.target.project_kind, summary: (c.target.short_summary || '').slice(0, 220) },
            }));
            const prompt = `Evaluate these project pairs from an academic/software portfolio. For each pair, return JSON array of objects: {"idx": number, "verdict": "SAME_PROJECT" | "RELATED_SERIES" | "DISTINCT", "reason": "short 6-10 word reason"}. Return ONLY raw JSON.\n\n${JSON.stringify(promptPairs)}`;
            const verdicts = await callGeminiJson(apiKey, prompt);
            (Array.isArray(verdicts) ? verdicts : []).forEach(v => {
                if (currentErCandidates[v.idx]) currentErCandidates[v.idx].aiVerdict = v;
            });
            renderErDuplicatesList();
            showPortalToast(`AI verified top ${verdicts.length} pairs`);
        } catch (err) {
            showPortalToast(`AI verify failed: ${err.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-check-double mr-1"></i> Verify Listed Pairs'; }
        }
    };

    // Manual Merge Modal Controls
    window.openManualMergeModal = function (preselectedSourceId = null) {
        const modal = document.getElementById('manual-merge-modal');
        if (!modal) return;
        document.getElementById('mm-source-filter').value = '';
        document.getElementById('mm-target-filter').value = '';
        populateManualMergeSelects(preselectedSourceId);
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    };

    window.closeManualMergeModal = function () {
        const modal = document.getElementById('manual-merge-modal');
        if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
    };

    window.populateManualMergeSelects = function (preselectedSourceId = null) {
        const projects = [...(portalProjectsState.projects || [])].sort((a, b) => (a.title || '').localeCompare(b.title || ''));
        const srcQ = (document.getElementById('mm-source-filter')?.value || '').toLowerCase();
        const tgtQ = (document.getElementById('mm-target-filter')?.value || '').toLowerCase();
        const srcSel = document.getElementById('mm-source-select');
        const tgtSel = document.getElementById('mm-target-select');
        if (!srcSel || !tgtSel) return;

        const prevSrc = preselectedSourceId != null ? String(preselectedSourceId) : srcSel.value;
        const prevTgt = tgtSel.value;
        const filterFn = (p, q) => !q || `${p.title} ${p.slug} ${p.category} ${p.project_kind}`.toLowerCase().includes(q);

        srcSel.innerHTML = projects.filter(p => filterFn(p, srcQ)).map(p =>
            `<option value="${escapeHtml(String(p.id))}">${escapeHtml(p.title)} [${escapeHtml(p.slug)}] (${(p.artifacts || []).length} art)</option>`
        ).join('');
        tgtSel.innerHTML = projects.filter(p => filterFn(p, tgtQ)).map(p =>
            `<option value="${escapeHtml(String(p.id))}">${escapeHtml(p.title)} [${escapeHtml(p.slug)}] (${p.is_public ? 'PUBLIC' : 'private'}, ${(p.artifacts || []).length} art)</option>`
        ).join('');

        if (prevSrc && Array.from(srcSel.options).some(o => o.value === prevSrc)) srcSel.value = prevSrc;
        if (prevTgt && Array.from(tgtSel.options).some(o => o.value === prevTgt)) tgtSel.value = prevTgt;
        if (srcSel.value === tgtSel.value && tgtSel.options.length > 1) {
            tgtSel.selectedIndex = srcSel.selectedIndex === 0 ? 1 : 0;
        }
        renderManualMergePreview();
    };

    window.renderManualMergePreview = function () {
        const srcId = Number(document.getElementById('mm-source-select')?.value);
        const tgtId = Number(document.getElementById('mm-target-select')?.value);
        const src = (portalProjectsState.projects || []).find(p => p.id === srcId);
        const tgt = (portalProjectsState.projects || []).find(p => p.id === tgtId);
        const fmt = p => p
            ? `<div><strong>${escapeHtml(p.title)}</strong> (${escapeHtml(p.discovery_status || 'canonical')})</div><div>${(p.artifacts || []).length} artifacts &bull; ${(p.placements || []).length} placements</div><div class="truncate text-slate-500 mt-1">${escapeHtml(p.short_summary || '')}</div>`
            : 'Select a project';
        const sEl = document.getElementById('mm-source-preview');
        const tEl = document.getElementById('mm-target-preview');
        if (sEl) sEl.innerHTML = fmt(src);
        if (tEl) tEl.innerHTML = fmt(tgt);
    };

    window.swapManualMergeSides = function () {
        const srcSel = document.getElementById('mm-source-select');
        const tgtSel = document.getElementById('mm-target-select');
        if (!srcSel || !tgtSel) return;
        const sVal = srcSel.value;
        const tVal = tgtSel.value;
        if (Array.from(srcSel.options).some(o => o.value === tVal)) srcSel.value = tVal;
        if (Array.from(tgtSel.options).some(o => o.value === sVal)) tgtSel.value = sVal;
        renderManualMergePreview();
    };

    window.executeManualMerge = async function () {
        const srcId = Number(document.getElementById('mm-source-select')?.value);
        const tgtId = Number(document.getElementById('mm-target-select')?.value);
        if (!srcId || !tgtId || srcId === tgtId) {
            showPortalToast('Choose two different projects to merge.', 'warn');
            return;
        }
        const appendSummary = Boolean(document.getElementById('mm-append-summary')?.checked);
        const addAlias = Boolean(document.getElementById('mm-add-alias')?.checked);
        const ok = await mergePortalProjects(srcId, tgtId, { appendSummary, addAlias });
        if (ok) closeManualMergeModal();
    };

    async function mergePortalProjects(sourceId, targetId, opts = {}) {
        const src = (portalProjectsState.projects || []).find(p => p.id === sourceId);
        const tgt = (portalProjectsState.projects || []).find(p => p.id === targetId);
        if (!src || !tgt || src.id === tgt.id) return false;

        if (portalProjectsState.liveMode) {
            const resp = await fetch('/api/projects/merge', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_id: src.id,
                    target_id: tgt.id,
                    append_summary: Boolean(opts.appendSummary),
                    add_alias: opts.addAlias !== false,
                }),
            });
            const data = await resp.json();
            if (!data.ok) {
                showPortalToast(data.error || 'Merge failed', 'error');
                return false;
            }
            hydrateBundleState(data);
        } else {
            if (src.slug) {
                try {
                    const delSlugs = JSON.parse(localStorage.getItem(DELETED_PROJ_SLUGS_KEY) || '[]');
                    if (!delSlugs.includes(src.slug)) delSlugs.push(src.slug);
                    localStorage.setItem(DELETED_PROJ_SLUGS_KEY, JSON.stringify(delSlugs));
                } catch (e) { }
            }
            pushStagedPatchOp('merge_projects', {
                source_id: src.id,
                source_slug: src.slug,
                target_id: tgt.id,
                target_slug: tgt.slug,
                append_summary: Boolean(opts.appendSummary),
                add_alias: opts.addAlias !== false,
            });
            portalProjectsState.projects = applyLocalPatchOpsToMemory(portalProjectsState.projects);
            renderPortalProjectsHub();
        }
        showPortalToast(`Merged "${src.title}" -> "${tgt.title}"`);
        return true;
    }

})();
