import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

suspicious_targets = ['â€“', 'â€”', 'â€™', 'â€˜', 'â€œ', 'â€ ', 'â€¢', 'â€¦', 'Ã©', 'Ã', 'Â', '\ufffd', 'ΓÇ', 'ï¿½']

findings = []

for root, dirs, files in os.walk('.'):
    if any(skip in root for skip in ['.git', 'brain', 'node_modules', 'archive', '.gemini']):
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.json')):
            fpath = os.path.join(root, file)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                for target in suspicious_targets:
                    if target in content:
                        count = content.count(target)
                        idx = content.find(target)
                        start = max(0, idx - 25)
                        end = min(len(content), idx + len(target) + 25)
                        snippet = content[start:end].replace('\n', ' ')
                        findings.append((fpath, target, count, snippet))
            except Exception as e:
                pass

print(f"Total findings in repo files: {len(findings)}")
for fpath, target, count, snip in findings:
    print(f"[{fpath}] found {count}x {repr(target)} -> ...{snip}...")
