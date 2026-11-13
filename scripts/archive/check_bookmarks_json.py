import json

data = json.load(open('data/bookmarks.json', 'r', encoding='utf-8'))
bms = [b for b in data['bookmarks'] if 'financial' in b.get('description', '').lower() or 'finance' in b.get('description', '').lower() or 'bank' in b.get('description', '').lower()]
print(f"Total bookmarks matching finance/bank in description: {len(bms)}")
for b in bms:
    print(f"  {b['id']}: {b['name']} ({b['domain']})")
