import sqlite3
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=" * 70)
print("SCANNING SQLITE DATABASE FOR ENCODING CORRUPTIONS & WEIRD CHARS")
print("=" * 70)

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']

corrupt_findings = []

# Regex patterns for mojibake and replacement characters
patterns = [
    (r'\ufffd', "Unicode replacement character ()"),
    (r'â€[™œ–—•˜]', "Windows-1252 mojibake quotes/dashes (â€...)"),
    (r'â[€™˜]', "Windows-1252 mojibake apostrophe/quote (â...)"),
    (r'Ã[\x80-\xbf]', "UTF-8 double-encoded Latin chars (Ã...)"),
    (r'Â[\xa0-\xbf]', "UTF-8 double-encoded symbol/non-breaking space (Â...)"),
    (r'ΓÇ[óö]', "CP437/OEM mojibake bullet/dash (ΓÇ...)"),
    (r'[╪┘┌█▌▐▀▄]', "CP437 misinterpreted Arabic or box chars"),
]

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cursor.fetchall() if col[2] in ['TEXT', '']]
    
    for col in cols:
        query = f"SELECT rowid, {col} FROM {table} WHERE {col} IS NOT NULL"
        try:
            cursor.execute(query)
            for rowid, val in cursor.fetchall():
                if not isinstance(val, str):
                    continue
                for pat, desc in patterns:
                    matches = list(re.finditer(pat, val))
                    if matches:
                        # Extract a snippet around the match
                        for m in matches[:3]:
                            start = max(0, m.start() - 25)
                            end = min(len(val), m.end() + 25)
                            snippet = val[start:end].replace('\n', ' ')
                            corrupt_findings.append({
                                'location': f"{table}.{col} [rowid={rowid}]",
                                'type': desc,
                                'match': m.group(0),
                                'snippet': snippet
                            })
        except Exception as e:
            print(f"Error checking {table}.{col}: {e}")

print(f"Total database corruptions found: {len(corrupt_findings)}")
for f in corrupt_findings[:40]:
    print(f"  [{f['location']}] ({f['type']}): ...{f['snippet']}...")

if len(corrupt_findings) > 40:
    print(f"  ... and {len(corrupt_findings) - 40} more.")

# Now let's check files in repository
print("\n" + "=" * 70)
print("SCANNING HTML / JS FILES IN REPOSITORY")
print("=" * 70)

file_findings = []
for root, dirs, files in os.walk('.'):
    # Skip .git, .system_generated, node_modules, archive
    if any(skip in root for skip in ['.git', 'brain', 'node_modules', 'archive', '.gemini']):
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.json', '.md', '.txt')):
            fpath = os.path.join(root, file)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                for pat, desc in patterns:
                    matches = list(re.finditer(pat, content))
                    if matches:
                        for m in matches[:3]:
                            start = max(0, m.start() - 25)
                            end = min(len(val), m.end() + 25)
                            snippet = content[start:end].replace('\n', ' ')
                            file_findings.append({
                                'file': fpath,
                                'type': desc,
                                'snippet': snippet
                            })
            except Exception as e:
                pass

print(f"Total file corruptions found: {len(file_findings)}")
for f in file_findings[:30]:
    print(f"  [{f['file']}] ({f['type']}): ...{f['snippet']}...")

conn.close()
