import json

data = json.load(open('data/bookmarks.json', 'r', encoding='utf-8'))
bms = data.get('bookmarks', [])
print(f"Total bookmarks: {len(bms)}")
missing = [b for b in bms if not b.get('description')]
print(f"Missing descriptions: {len(missing)}")

financial = [b for b in bms if 'financial' in b.get('description', '').lower() or 'finance' in b.get('description', '').lower()]
print(f"Total matching 'financial' or 'finance' in description: {len(financial)}")
for b in financial:
    print(f"  #{b['id']}: {b['name']} ({b['domain']})")
