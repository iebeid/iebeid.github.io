with open('js/portal.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for i, line in enumerate(lines):
    if any(k in line for k in ['initAddBookmarkForm', 'initRemember', 'DOMContentLoaded', 'window.onload', 'initDrag']):
        print(f"L{i+1}: {line.strip()[:140]}")
