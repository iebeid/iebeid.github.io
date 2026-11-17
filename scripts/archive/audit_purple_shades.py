import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

for skey in ('file_pages_media_talk_reveal_css_custom_css', 'style_talk_index'):
    cur.execute("SELECT css_content FROM stylesheets WHERE style_key=?", (skey,))
    css = cur.fetchone()[0]
    print(f"=== {skey} ===")
    for i, line in enumerate(css.splitlines(), 1):
        if any(k in line.lower() for k in ['purple', '168,', '6366f1', '818cf8', 'indigo']):
            print(f"  L{i}: {line}")

conn.close()
