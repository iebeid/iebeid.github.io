import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/archive/storefront_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

for key, sec in sections.items():
    print("=" * 60)
    print(f"SECTION: {key} (Heading: {sec['heading']})")
    print("=" * 60)
    print(sec['html'])
