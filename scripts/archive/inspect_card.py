import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/archive/storefront_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

catalog_html = sections['catalog']['html']
cards = catalog_html.split('class="product-card')
print(f"Total product cards: {len(cards) - 1}")

for i, card in enumerate(cards[1:], 1):
    full_card = 'class="product-card' + card
    if 'toolkit' in full_card.lower() or 'dataintegration' in full_card.lower():
        print(f"\n--- Card {i} (MATCHED) ---")
        print(full_card[:1500])
