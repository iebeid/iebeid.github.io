import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT css_content FROM stylesheets WHERE style_key = 'style_storefront'")
css = cursor.fetchone()[0]

for line in css.splitlines():
    if "h1" in line:
        print(line)

conn.close()
