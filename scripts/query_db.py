#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "content.db"
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = sorted([r[0] for r in cur.fetchall()])

print(f"=== Database Stats ({db_path}) ===")
for t in tables:
    cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:<22} : {cnt:>4} records")
conn.close()
