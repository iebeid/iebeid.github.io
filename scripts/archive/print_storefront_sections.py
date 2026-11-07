import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/archive/storefront_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

for key in ['section_1', 'architecture', 'licensing', 'faq']:
    print(f"\n==================== {key.upper()} ====================")
    print(sections[key]['html'])
