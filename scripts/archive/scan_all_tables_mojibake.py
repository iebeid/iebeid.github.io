import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall() if r[0] != 'sqlite_sequence']

mojibake_strings = [
    'â€“', 'â€”', 'â€™', 'â€˜', 'â€œ', 'â€', 'â€¢', 'â€¦', 
    'Ã©', 'Ã¨', 'Ã ', 'Ã¡', 'Ã³', 'Ã±', 'Ã§', 'Ã®', 'Ã¯', 'Ã´', 'Ã»', 'Ã¼', 'Ã¶', 'Ã¤',
    'Â ', 'Â', 'ΓÇó', 'ΓÇö', 'ΓÇô', '\ufffd'
]

findings = []

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall()]
    
    for col in cols:
        for m in mojibake_strings:
            query = f"SELECT rowid, {col} FROM {table} WHERE {col} LIKE ?"
            try:
                cursor.execute(query, (f"%{m}%",))
                rows = cursor.fetchall()
                for r in rows:
                    val = str(r[1])
                    idx = val.find(m)
                    start = max(0, idx - 20)
                    end = min(len(val), idx + len(m) + 20)
                    snippet = val[start:end].replace('\n', ' ')
                    findings.append((table, col, r[0], m, snippet))
            except Exception as e:
                pass

print(f"Total findings across all tables: {len(findings)}")
for table, col, rowid, m, snippet in findings:
    print(f"[{table}.{col} | id={rowid}] mojibake: {repr(m)} -> ...{snippet}...")

conn.close()
