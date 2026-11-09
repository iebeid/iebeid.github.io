import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

mojibake_strings = ['â€“', 'â€”', 'â€™', 'â€˜', 'â€œ', 'â€ ', 'â€¢', 'â€¦', 'Ã©', 'Ã', 'Â', '\ufffd', 'ΓÇ', 'ï¿½']

findings = []

for root, dirs, files in os.walk('.'):
    if any(skip in root for skip in ['.git', 'brain', 'node_modules', 'archive', '.gemini']):
        continue
    for file in files:
        if file.endswith(('.py', '.js', '.html', '.css', '.json', '.md')):
            fpath = os.path.join(root, file)
            # Skip generated bundles which will be regenerated
            if fpath.endswith(('public_content.json', 'public_content.js')):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                for m in mojibake_strings:
                    if m in content:
                        findings.append((fpath, m, content.count(m)))
            except Exception as e:
                pass

print(f"Total findings in active repo files: {len(findings)}")
for fpath, m, count in findings:
    print(f"  [{fpath}] found {count}x {repr(m)}")
