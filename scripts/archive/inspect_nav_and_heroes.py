import sqlite3

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=== NAVIGATION MENU CSS / HTML ===")
cursor.execute("SELECT menu_key, length(menu_html) FROM navigation_menu")
for r in cursor.fetchall():
    print(r)

cursor.execute("SELECT menu_html FROM navigation_menu WHERE menu_key = 'main_navbar' OR menu_key = 'global_navbar' LIMIT 1")
nav = cursor.fetchone()
if nav:
    print("\nNavbar sample:\n", nav[0][:600])

print("\n=== HERO BANNERS ACROSS PAGES ===")
cursor.execute("SELECT page_slug, section_key, heading, content_html FROM page_sections WHERE section_key LIKE '%hero%' OR section_key LIKE '%banner%'")
for r in cursor.fetchall():
    print(f"\n--- {r[0]} :: {r[1]} ({r[2]}) ---")
    print(r[3][:400] if r[3] else "EMPTY")

conn.close()
