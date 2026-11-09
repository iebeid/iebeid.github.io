import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']

suspicious_targets = ['â€“', 'â€”', 'â€™', 'â€˜', 'â€œ', 'â€', 'â€¢', 'â€¦', 'Ã©', 'Ã', 'Â', '\ufffd', 'ΓÇ', 'ï¿½']

findings = []

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall() if c[2] in ['TEXT', '']]
    
    for col in cols:
        cursor.execute(f"SELECT rowid, {col} FROM {table} WHERE {col} IS NOT NULL")
        for rowid, val in cursor.fetchall():
            if not isinstance(val, str):
                continue
            for target in suspicious_targets:
                if target in val:
                    count = val.count(target)
                    idx = val.find(target)
                    start = max(0, idx - 25)
                    end = min(len(val), idx + len(target) + 25)
                    snippet = val[start:end].replace('\n', ' ')
                    findings.append((table, col, rowid, target, count, snippet))

print(f"Total findings across all database tables: {len(findings)}")
for table, col, rowid, target, count, snip in findings:
    print(f"[{table}.{col} | id={rowid}] found {count}x {repr(target)} -> ...{snip}...")

conn.close()
