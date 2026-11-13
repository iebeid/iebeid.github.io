import os

for root, _, files in os.walk('js'):
    for fn in files:
        if fn.endswith('.js'):
            p = os.path.join(root, fn)
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
            if 'navigation_menu' in txt:
                print(f"Found in {p}")
