with open('js/portal.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 295-340 ---")
for i in range(295, 340):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')

print("\n--- Lines 540-565 ---")
for i in range(540, 565):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')
