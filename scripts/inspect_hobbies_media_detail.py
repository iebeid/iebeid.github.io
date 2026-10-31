from bs4 import BeautifulSoup
from pathlib import Path

for p in ['hobbies', 'media']:
    f = Path(f'G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/{p}/{p}.html')
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    main = soup.find('main')
    print(f"\n=== {p} main structure ===")
    if main:
        container = main.find('div')
        if container:
            blocks = [c.name for c in container.children if c.name]
            print(f"Container class: {container.get('class')}")
            print(f"Container direct children: {len(blocks)} elements: {blocks[:10]}")
