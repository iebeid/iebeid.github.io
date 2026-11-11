with open('js/portal.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
print(f"Total lines in portal.js: {len(lines)}")
for i in range(380, 465):
    print(f"L{i+1}: {lines[i]}")
