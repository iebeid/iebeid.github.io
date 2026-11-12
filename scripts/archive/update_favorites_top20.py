import sqlite3

# 1. Update SQLite content.db
conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
row = cur.fetchone()
if not row:
    raise Exception("portal_app section not found")

content_html, content_text = row

# Replace stat-top-favorites 10 -> 20
old_stat = '<div class="text-2xl font-bold text-white" id="stat-top-favorites">10</div>'
new_stat = '<div class="text-2xl font-bold text-white" id="stat-top-favorites">20</div>'

# Replace Top 10 Most Clicked -> Top 20 Most Clicked
old_badge = '<span class="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full border border-amber-500/30">Top 10 Most Clicked</span>'
new_badge = '<span class="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full border border-amber-500/30">Top 20 Most Clicked</span>'

assert old_stat in content_html, "old_stat not found in content_html"
assert old_badge in content_html, "old_badge not found in content_html"

content_html = content_html.replace(old_stat, new_stat)
content_html = content_html.replace(old_badge, new_badge)

if content_text:
    content_text = content_text.replace("Top 10 Most Clicked", "Top 20 Most Clicked")
    content_text = content_text.replace("Top 10", "Top 20")

cur.execute("UPDATE page_sections SET content_html=?, content_text=? WHERE page_slug='portal' AND section_key='portal_app'", (content_html, content_text))
conn.commit()
conn.close()
print("[OK] Updated data/content.db portal_app section")

# 2. Update js/portal.js
with open('js/portal.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Update header comment
js_content = js_content.replace("* - Top 10 Favorites live-updating section", "* - Top 20 Favorites live-updating section")

# Update section comment
js_content = js_content.replace("// 7. FAVORITES (TOP 10 MOST CLICKED) & SIMILARITY / RELEVANCE RANKING ENGINE", "// 7. FAVORITES (TOP 20 MOST CLICKED) & SIMILARITY / RELEVANCE RANKING ENGINE")

# Update slice(0, 10) to slice(0, 20) in renderDashboardFavorites
old_slice = "const top10 = sorted.slice(0, 10);"
new_slice = "const top20 = sorted.slice(0, 20);"
assert old_slice in js_content, "old_slice not found in js/portal.js"
js_content = js_content.replace(old_slice, new_slice)

old_grid_map = "grid.innerHTML = top10.map((bm, index) => {"
new_grid_map = "grid.innerHTML = top20.map((bm, index) => {"
assert old_grid_map in js_content, "old_grid_map not found in js/portal.js"
js_content = js_content.replace(old_grid_map, new_grid_map)

# Update stat topFavEl.textContent = '10' -> '20'
old_top_fav = "if (topFavEl) topFavEl.textContent = '10';"
new_top_fav = "if (topFavEl) topFavEl.textContent = '20';"
assert old_top_fav in js_content, "old_top_fav not found in js/portal.js"
js_content = js_content.replace(old_top_fav, new_top_fav)

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(js_content)
print("[OK] Updated js/portal.js to Top 20")
