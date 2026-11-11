with open('js/portal.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Favorites Card (970-1000) ---")
for i in range(970, 1000):
    if i < len(lines):
        print(f"L{i+1}: {lines[i]}", end='')

print("\n--- Search Result Card (1400-1445) ---")
for i in range(1400, 1445):
    if i < len(lines):
        print(f"L{i+1}: {lines[i]}", end='')
