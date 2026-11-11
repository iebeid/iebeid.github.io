import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def update_portal_app_section():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'portal' AND section_key = 'portal_app'")
    html = cursor.fetchone()[0]

    # Target the dashboard-remember-section block
    old_section_pattern = r'<!-- Remember / Save for Later Section -->[\s\S]*?<!-- Top 10 Favorites Section -->'

    new_section_html = '''<!-- Remember / Save for Later Section -->
<div class="relative bg-slate-900 p-6 rounded-2xl border border-slate-800/80 shadow-sm mb-6 transition-all duration-200" id="dashboard-remember-section">
    <!-- Visual Drop Target Overlay -->
    <div id="remember-drop-overlay" class="absolute inset-0 bg-slate-900/95 backdrop-blur-sm rounded-2xl border-2 border-dashed border-emerald-500 flex flex-col items-center justify-center z-30 transition-all duration-200 pointer-events-none hidden">
        <div class="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-2xl mb-3 shadow-lg shadow-emerald-950/50 animate-bounce">
            <i class="fas fa-file-import"></i>
        </div>
        <h3 class="text-sm font-bold text-white tracking-wide mb-1">Drop Chrome Bookmark Here</h3>
        <p class="text-xs text-emerald-300">Release to save and pin directly to Remember &amp; Save for Later</p>
    </div>

    <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-base">
                <i class="fas fa-bookmark"></i>
            </div>
            <div>
                <h2 class="serif-heading text-base font-bold text-white flex items-center gap-2">
                    Remember &amp; Save for Later
                    <span class="text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30" id="remember-count-badge">0 Saved</span>
                </h2>
                <p class="text-xs text-slate-400 mt-0.5">Drag &amp; drop bookmarks from your Chrome Bookmark Bar here, or click the bookmark ribbon on any card.</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <span class="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-slate-500 font-mono bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/50">
                <i class="fas fa-arrows-alt text-emerald-400 text-[10px]"></i> Drag &amp; Drop Ready
            </span>
            <button class="text-[11px] text-slate-500 hover:text-rose-400 font-mono transition flex items-center gap-1 hidden" id="clear-remember-btn" onclick="clearAllRemembered()">
                <i class="fas fa-trash-alt text-[10px]"></i> Clear All
            </button>
        </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" id="dashboard-remember-grid">
        <!-- Dynamically populated by renderDashboardRemember() -->
    </div>
    <div class="py-8 px-4 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl transition hover:border-slate-700" id="dashboard-remember-empty">
        <div class="w-12 h-12 rounded-2xl bg-slate-800/60 text-slate-600 mx-auto flex items-center justify-center text-xl mb-3">
            <i class="fas fa-bookmark"></i>
        </div>
        <p class="text-xs font-medium text-slate-300">Drag &amp; drop links directly from your Chrome Bookmarks Bar</p>
        <p class="text-[11px] text-slate-500 mt-1 max-w-md mx-auto">Grab any bookmark from your browser's top bar and drop it anywhere into this box to instantly save it for later review.</p>
    </div>
</div>

<!-- Top 10 Favorites Section -->'''

    html, count = re.subn(old_section_pattern, new_section_html, html, count=1)
    if count == 0:
        print("[ERROR] Could not match old remember section in portal_app")
        sys.exit(1)

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'portal' AND section_key = 'portal_app'", (html,))
    conn.commit()
    conn.close()
    print("[SUCCESS] Updated portal_app in database with Drag & Drop Remember UI")

def update_portal_js():
    with open('js/portal.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Insert Toast & Drag/Drop functions after clearAllRemembered()
    target_needle = 'window.clearAllRemembered = clearAllRemembered;'
    if target_needle not in js:
        print("[ERROR] target_needle not found in js/portal.js")
        sys.exit(1)

    drag_and_drop_code = '''window.clearAllRemembered = clearAllRemembered;

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
                const lines = uriList.split(/\\r?\\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
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
            domain = new URL(url).hostname.replace(/^www\\./, '');
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
        const norm = (u) => (u || '').toLowerCase().replace(/^https?:\\/\\/(www\\.)?/, '').replace(/\\/+$/, '');
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
    window.initRememberDragAndDrop = initRememberDragAndDrop;'''

    js = js.replace(target_needle, drag_and_drop_code, 1)

    # 2. Make cards draggable in renderDashboardRemember
    old_rem_card = '<div class="group relative bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-3 flex flex-col justify-between transition-all duration-200 shadow-sm">'
    new_rem_card = '<div draggable="true" ondragstart="handlePortalBookmarkDragStart(event, ${bm.id})" class="group relative bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-emerald-500/50 rounded-xl p-3 flex flex-col justify-between transition-all duration-200 shadow-sm cursor-grab active:cursor-grabbing">'
    js = js.replace(old_rem_card, new_rem_card)

    # 3. Make cards draggable in renderDashboardFavorites
    old_fav_card = '<div onclick="trackLaunch(${bm.id}, \'${escapeHtml(bm.url)}\')"\n                    class="group relative bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-sky-500/50 rounded-xl p-3 cursor-pointer transition shadow-sm hover:shadow-md flex flex-col justify-between"'
    new_fav_card = '<div draggable="true" ondragstart="handlePortalBookmarkDragStart(event, ${bm.id})" onclick="trackLaunch(${bm.id}, \'${escapeHtml(bm.url)}\')"\n                    class="group relative bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-sky-500/50 rounded-xl p-3 cursor-pointer transition shadow-sm hover:shadow-md flex flex-col justify-between"'
    js = js.replace(old_fav_card, new_fav_card)

    # 4. Make cards draggable in renderDashboardSearchResults
    old_sr_card = '<div class="group bg-slate-900 border border-slate-800/80 hover:border-sky-500/50 rounded-xl p-4 transition flex flex-col justify-between shadow-sm hover:shadow-md">'
    new_sr_card = '<div draggable="true" ondragstart="handlePortalBookmarkDragStart(event, ${bm.id})" class="group bg-slate-900 border border-slate-800/80 hover:border-sky-500/50 rounded-xl p-4 transition flex flex-col justify-between shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing">'
    js = js.replace(old_sr_card, new_sr_card)

    # 5. Call initRememberDragAndDrop in DOMContentLoaded and renderAll
    old_dom_loaded = "initSecretDispatchForm();\n        if (isAuthenticated()) {"
    new_dom_loaded = "initSecretDispatchForm();\n        initRememberDragAndDrop();\n        if (isAuthenticated()) {"
    js = js.replace(old_dom_loaded, new_dom_loaded)

    old_render_all = "renderDashboardRemember();\n        renderDashboardFavorites();"
    new_render_all = "renderDashboardRemember();\n        renderDashboardFavorites();\n        initRememberDragAndDrop();"
    js = js.replace(old_render_all, new_render_all)

    with open('js/portal.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("[SUCCESS] Updated js/portal.js with Chrome Bookmark Bar Drag & Drop Engine")

if __name__ == '__main__':
    update_portal_app_section()
    update_portal_js()
