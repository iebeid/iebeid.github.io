import sqlite3
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

print("=" * 70)
print("SCANNING FOR PURPLE & ORANGE ACROSS DATABASE")
print("=" * 70)

target_pattern = re.compile(r'\b(purple|orange|violet|fuchsia)(?:-([0-9]{2,3}))?\b', re.IGNORECASE)

db_findings = []

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall() if c[2] in ['TEXT', '']]
    
    for col in cols:
        cursor.execute(f"SELECT rowid, {col} FROM {table} WHERE {col} IS NOT NULL")
        for rowid, val in cursor.fetchall():
            if not isinstance(val, str):
                continue
            matches = list(target_pattern.finditer(val))
            if matches:
                matched_words = [m.group(0) for m in matches]
                db_findings.append((table, col, rowid, len(matches), set(matched_words)))

print(f"Total database columns/rows with matches: {len(db_findings)}")
for table, col, rowid, count, words in db_findings:
    print(f"  [{table}.{col} | rowid={rowid}] {count}x matches: {words}")

print("\n" + "=" * 70)
print("SCANNING REPOSITORY FILES FOR PURPLE & ORANGE")
print("=" * 70)

file_findings = []
for root, dirs, files in os.walk('.'):
    if any(skip in root for skip in ['.git', 'brain', 'node_modules', 'archive', '.gemini']):
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.css', '.json', '.py')):
            fpath = os.path.join(root, file)
            if fpath.endswith(('public_content.json', 'public_content.js')):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                matches = list(target_pattern.finditer(content))
                if matches:
                    matched_words = [m.group(0) for m in matches]
                    file_findings.append((fpath, len(matches), set(matched_words)))
            except Exception as e:
                pass

print(f"Total files with matches: {len(file_findings)}")
for fpath, count, words in file_findings:
    print(f"  [{fpath}] {count}x matches: {words}")

conn.close()
