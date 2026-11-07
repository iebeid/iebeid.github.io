try:
    with open('scripts/archive/storefront_full.txt', 'r', encoding='utf-16') as f:
        text = f.read()
except:
    with open('scripts/archive/storefront_full.txt', 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

import sys
sys.stdout.reconfigure(encoding='utf-8')

for section in text.split('='*60):
    lines = [l.strip() for l in section.strip().split('\n') if l.strip()]
    if lines:
        print("\n--- " + lines[0] + " ---")
        for line in lines[1:8]:
            print("  ", line[:120])
