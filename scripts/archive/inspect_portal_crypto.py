with open('js/portal.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['portal_vault', 'subtle', 'PBKDF2', 'AES-GCM', 'switchTab']):
        print(f"Line {i+1}: {l.strip()}")
