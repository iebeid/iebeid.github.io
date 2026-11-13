with open('js/portal.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'DOMContentLoaded' in l or 'function renderAll' in l:
        print(f"Line {i+1}: {l.strip()}")
