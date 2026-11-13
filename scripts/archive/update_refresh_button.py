import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Update HTML in portal_app section
cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html, text = cur.fetchone()

old_btn = '<button class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl shadow-sm text-xs font-bold transition flex items-center gap-1.5 whitespace-nowrap" id="ai-refresh-btn" onclick="refreshAITags()" title="Update AI Tags for all bookmarks"><i class="fas fa-sync-alt"></i> Update Tags</button>'
new_btn = '<button class="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl shadow-sm text-xs font-bold transition flex items-center gap-1.5 whitespace-nowrap" id="portal-refresh-btn" onclick="refreshPortal()" title="Refresh bookmark index, descriptions, and dashboard rankings"><i class="fas fa-sync-alt"></i> Refresh</button>'

assert old_btn in html, "old_btn not found in content_html"
html = html.replace(old_btn, new_btn)

cur.execute("UPDATE page_sections SET content_html=? WHERE page_slug='portal' AND section_key='portal_app'", (html,))
conn.commit()
conn.close()
print("[OK] Updated button in content.db to 'Refresh'")

# 2. Update js/portal.js
with open('js/portal.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_refresh_func = """    window.refreshAITags = async function() {
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
    };"""

new_refresh_func = """    window.refreshPortal = async function() {
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
    window.refreshAITags = window.refreshPortal;"""

assert old_refresh_func in js, "old_refresh_func not found in portal.js"
js = js.replace(old_refresh_func, new_refresh_func, 1)

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("[OK] Updated js/portal.js with refreshPortal workflow")
