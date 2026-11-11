with open('js/portal.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2715, 2750):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')
