from bs4 import BeautifulSoup
from pathlib import Path

for p in ['hobbies', 'media']:
    f = Path(f'G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/{p}/{p}.html')
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')
    main = soup.find('main')
    sections = main.find_all('section') if main else []
    print(f"{p}: has main? {bool(main)}, sections count: {len(sections)}")
    if main and not sections:
        # What children are in main?
        children = [c.name for c in main.children if c.name]
        print(f"   children of main: {children}")
