from bs4 import BeautifulSoup
from pathlib import Path

for p in ['hobbies', 'media']:
    f = Path(f'G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/{p}/{p}.html')
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    main = soup.find('main')
    print(f"\n=== {p} sections ===")
    if main:
        container = main.find('div')
        if container:
            blocks = [c for c in container.children if c.name == 'div']
            for i, b in enumerate(blocks):
                h = b.find(['h1', 'h2', 'h3', 'h4'])
                txt = h.get_text(strip=True) if h else "No heading"
                print(f"  block {i+1}: {txt} ({len(str(b))} bytes)")
