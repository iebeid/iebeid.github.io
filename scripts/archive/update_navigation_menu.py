import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Remove all menu items from Relations (parent_key = 'relations')
cur.execute("DELETE FROM navigation_menu WHERE parent_key = 'relations'")
print(f"Deleted {cur.rowcount} items from Relations")

# 2. In Research, keep only Data2AI4LifeSciences Lab (remove research_main)
cur.execute("DELETE FROM navigation_menu WHERE parent_key = 'research' AND nav_key != 'research_lab'")
print(f"Deleted {cur.rowcount} item(s) from Research (kept research_lab)")

conn.commit()

cur.execute("""
    SELECT id, nav_key, parent_key, label, rel_path, display_order
    FROM navigation_menu
    ORDER BY COALESCE(parent_key, nav_key), parent_key IS NOT NULL, display_order, id
""")
print("\nRemaining navigation_menu rows:")
for r in cur.fetchall():
    print(" ", r)

conn.close()
