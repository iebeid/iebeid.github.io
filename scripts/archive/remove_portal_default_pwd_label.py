import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='portal' AND section_key='login_screen'")
html, text = cur.fetchone()

target = '<span class="text-slate-500 text-[11px]">Passcode default: <code class="text-sky-300">islam2026</code></span>'
assert target in html, "Default passcode label not found in login_screen"

new_html = html.replace(target + '\n', '').replace(target, '')
new_text = (text or '').replace('Passcode default: islam2026', '').strip()

cur.execute(
    "UPDATE page_sections SET content_html=?, content_text=? WHERE page_slug='portal' AND section_key='login_screen'",
    (new_html, new_text)
)
conn.commit()
conn.close()
print("[OK] Removed default passcode label from login_screen in data/content.db")
