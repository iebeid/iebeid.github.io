with open('js/template.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if any(k in line for k in ['DESKTOP_LINKS_HTML', 'text-sky', 'hover:', 'activePage', 'class=']):
        print(f"L{i+1}: {line.strip()[:120]}")
