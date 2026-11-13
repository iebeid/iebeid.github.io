import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Remove all menu items from Home (parent_key = 'home')
cur.execute("DELETE FROM navigation_menu WHERE parent_key = 'home'")
print(f"Deleted {cur.rowcount} items from Home")

# 2. Remove confidential drop-box menu item from Relations (nav_key = 'relations_drop')
cur.execute("DELETE FROM navigation_menu WHERE nav_key = 'relations_drop'")
print(f"Deleted {cur.rowcount} item (relations_drop) from Relations")

# 3. Remove xlpm menu item from Research (nav_key = 'research_xlpm')
cur.execute("DELETE FROM navigation_menu WHERE nav_key = 'research_xlpm'")
print(f"Deleted {cur.rowcount} item (research_xlpm) from Research")

# 4. Remove first Unity Systems & Consulting menu item from Business (nav_key = 'business_main')
cur.execute("DELETE FROM navigation_menu WHERE nav_key = 'business_main'")
print(f"Deleted {cur.rowcount} item (business_main) from Business")

# 5. Remove all menu items from Media (parent_key = 'media')
cur.execute("DELETE FROM navigation_menu WHERE parent_key = 'media'")
print(f"Deleted {cur.rowcount} items from Media")

conn.commit()

# Verify remaining menu structure
cur.execute("""
    SELECT id, nav_key, parent_key, label, rel_path, display_order
    FROM navigation_menu
    ORDER BY COALESCE(parent_key, nav_key), parent_key IS NOT NULL, display_order, id
""")
print("\nRemaining navigation_menu rows:")
for r in cur.fetchall():
    print(" ", r)

conn.close()
