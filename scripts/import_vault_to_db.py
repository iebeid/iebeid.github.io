"""
Import Zero-Knowledge Encrypted Password Vault JSON into data/content.db.
Usage:
    python scripts/import_vault_to_db.py path/to/portal_vault_sync.json
"""
import sys
import json
import sqlite3
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_vault_to_db.py <path/to/portal_vault_sync.json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"[ERROR] File not found: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    records = payload.get("records", payload if isinstance(payload, list) else [])
    if not isinstance(records, list):
        print("[ERROR] Invalid vault sync JSON format.")
        sys.exit(1)

    conn = sqlite3.connect("data/content.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_passwords (
        id TEXT PRIMARY KEY,
        ciphertext TEXT NOT NULL,
        nonce TEXT NOT NULL,
        salt TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Replace current vault blobs with synced snapshot
    cur.execute("DELETE FROM portal_passwords")
    count = 0
    for rec in records:
        if not all(k in rec for k in ("id", "ciphertext", "nonce", "salt")):
            continue
        cur.execute(
            "INSERT INTO portal_passwords (id, ciphertext, nonce, salt, updated_at) VALUES (?, ?, ?, ?, ?)",
            (rec["id"], rec["ciphertext"], rec["nonce"], rec["salt"], rec.get("updated_at", "")),
        )
        count += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Imported {count} encrypted password records into data/content.db (portal_passwords).")
    print("Next step: Run `python scripts/sync_content.py -m \"Sync encrypted password vault\"` to update runtime bundles.")

if __name__ == "__main__":
    main()
