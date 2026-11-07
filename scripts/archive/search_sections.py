import json

with open('scripts/archive/storefront_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

for key in ['section_1', 'architecture', 'catalog', 'licensing', 'faq', 'footer']:
    if key in sections:
        print(f"=== {key} ===")
        html = sections[key]['html']
        lines = html.splitlines()
        print(f"Lines: {len(lines)}")
        for i, line in enumerate(lines[:30]):
            if any(term in line.lower() for term in ['toolkit', 'bioinformatics', 'academic', 'research', 'engineer', 'itil', 'gnn', 'graph neural']):
                print(f"  Line {i}: {line.strip()[:120]}")

print("\n=== SEARCHING FOR 'toolkit' ACROSS ALL SECTIONS ===")
for key, sec in sections.items():
    html = sec['html']
    if 'toolkit' in html.lower() or 'dataintegration' in html.lower():
        print(f"Found in {key}")
        for line in html.splitlines():
            if 'toolkit' in line.lower() or 'dataintegration' in line.lower():
                print(f"  [{key}] {line.strip()[:140]}")
