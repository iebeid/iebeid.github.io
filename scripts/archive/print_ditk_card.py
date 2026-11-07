import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/archive/storefront_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

catalog_html = sections['catalog']['html']
cards = catalog_html.split('class="product-card')
print("class=\"product-card" + cards[2][:2000])
