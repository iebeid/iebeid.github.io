import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

tables = ['publications', 'courses', 'contacts_directory', 'portal_bookmarks', 'pages', 'site_meta', 'documents', 'stylesheets', 'navigation_menu']

issues = []

for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cursor.fetchall() if c[2] in ['TEXT', '']]
    for col in cols:
        cursor.execute(f"SELECT rowid, {col} FROM {table} WHERE {col} IS NOT NULL")
        for rowid, val in cursor.fetchall():
            if not isinstance(val, str):
                continue
            for double_ent in ['&amp;amp;', '&amp;quot;', '&amp;apos;', '&amp;lt;', '&amp;gt;']:
                if double_ent in val:
                    issues.append((f"{table}.{col}", rowid, f"Double-escaped entity {double_ent}"))
            if r'\"' in val or r"\'" in val:
                issues.append((f"{table}.{col}", rowid, "Escaped quotes"))
            mojibake_matches = re.findall(r'(?:â€[™œ –—•˜]|â[€™˜]|Ã[\x80-\xbf]|Â[\xa0-\xbf]|ΓÇ[óö])', val)
            if mojibake_matches:
                issues.append((f"{table}.{col}", rowid, f"Mojibake: {set(mojibake_matches)}"))

print(f"Total issues in other tables: {len(issues)}")
for loc, rowid, desc in issues:
    print(f"  [{loc} | rowid={rowid}] - {desc}")

conn.close()
