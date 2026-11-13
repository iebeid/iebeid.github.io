with open('scripts/sync_content.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def sync_portal_bookmarks' in l:
        for j in range(i+75, min(len(lines), i+115)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
