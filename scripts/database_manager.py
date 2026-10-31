#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Central Content, UI, Stylesheet & Vault SQLite Engine
Manages 100% of website HTML templates, CSS stylesheets, navigation hierarchy,
text sections, documents, media catalog, publications, and private encrypted portal assets.
"""

import os
import sys
import sqlite3
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

# AES-256-GCM and PBKDF2 Cryptographic modules
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "content.db"

# Default Master Key Derivation
DEFAULT_PORTAL_PASSCODE = "islam2026"


def derive_key(passcode: str, salt: bytes) -> bytes:
    """Derive 256-bit AES key using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(passcode.encode('utf-8'))


def encrypt_secret(plaintext: str, passcode: str = DEFAULT_PORTAL_PASSCODE) -> Dict[str, str]:
    """Encrypt a plaintext string using AES-256-GCM."""
    salt = os.urandom(16)
    key = derive_key(passcode, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return {
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "nonce": base64.b64encode(nonce).decode('utf-8'),
        "salt": base64.b64encode(salt).decode('utf-8')
    }


def decrypt_secret(encrypted_data: Dict[str, str], passcode: str = DEFAULT_PORTAL_PASSCODE) -> str:
    """Decrypt an AES-256-GCM encrypted payload."""
    salt = base64.b64decode(encrypted_data["salt"])
    nonce = base64.b64decode(encrypted_data["nonce"])
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    key = derive_key(passcode, salt)
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode('utf-8')


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get SQLite database connection with row factory enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path = DB_PATH):
    """Initialize all relational tables for website HTML, CSS, navigation, content, and private portal."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Site Metadata
    cur.execute("""
    CREATE TABLE IF NOT EXISTS site_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT
    );
    """)

    # 2. Pages (Metadata + Full Dynamic HTML Shell Info)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        slug TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subtitle TEXT,
        description TEXT,
        rel_path TEXT,
        nav_order INTEGER,
        is_public INTEGER DEFAULT 1,
        html_classes TEXT DEFAULT 'scroll-smooth',
        body_classes TEXT DEFAULT 'antialiased overflow-x-hidden',
        head_html TEXT DEFAULT '',
        body_template_html TEXT DEFAULT '',
        inline_scripts TEXT DEFAULT '',
        use_global_chrome INTEGER DEFAULT 1
    );
    """)

    # Ensure new columns exist if upgrading an existing database
    existing_cols = {r[1] for r in cur.execute("PRAGMA table_info(pages)").fetchall()}
    migrations = [
        ("rel_path", "TEXT DEFAULT ''"),
        ("html_classes", "TEXT DEFAULT 'scroll-smooth'"),
        ("body_classes", "TEXT DEFAULT 'antialiased overflow-x-hidden'"),
        ("head_html", "TEXT DEFAULT ''"),
        ("body_template_html", "TEXT DEFAULT ''"),
        ("inline_scripts", "TEXT DEFAULT ''"),
        ("use_global_chrome", "INTEGER DEFAULT 1")
    ]
    for col_name, col_def in migrations:
        if col_name not in existing_cols:
            cur.execute(f"ALTER TABLE pages ADD COLUMN {col_name} {col_def};")

    # 3. Page Sections (Modular HTML & Text Content Blocks)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS page_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_slug TEXT NOT NULL REFERENCES pages(slug),
        section_key TEXT NOT NULL,
        heading TEXT,
        subheading TEXT,
        content_html TEXT,
        content_text TEXT,
        display_order INTEGER DEFAULT 0,
        UNIQUE(page_slug, section_key)
    );
    """)

    # 4. CSS Stylesheets Table (All inline <style> blocks and external .css files)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stylesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        style_key TEXT UNIQUE NOT NULL,
        scope TEXT NOT NULL,
        page_slug TEXT,
        rel_path TEXT,
        style_type TEXT DEFAULT 'text/css',
        css_content TEXT NOT NULL,
        description TEXT,
        display_order INTEGER DEFAULT 0
    );
    """)

    # 5. HTML Templates & UI Components Table (Header, Footer, Floating Nav, Modals)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS html_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_key TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        html_content TEXT NOT NULL,
        description TEXT
    );
    """)

    # 6. Navigation Menu Tree (Top-Level Items & Hover Dropdown Sub-Pages for ALL HTML files)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS navigation_menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nav_key TEXT UNIQUE NOT NULL,
        parent_key TEXT,
        label TEXT NOT NULL,
        sublabel TEXT,
        folder TEXT NOT NULL,
        rel_path TEXT NOT NULL,
        icon_class TEXT,
        badge_text TEXT,
        display_order INTEGER DEFAULT 0,
        is_visible INTEGER DEFAULT 1
    );
    """)

    # 7. Documents Catalog (PDFs, CVs, Syllabi)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        title TEXT NOT NULL,
        rel_path TEXT NOT NULL UNIQUE,
        category TEXT,
        file_size_bytes INTEGER DEFAULT 0
    );
    """)

    # 8. Media Catalog (Images, Icons, Patterns)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        alt_text TEXT,
        rel_path TEXT NOT NULL UNIQUE,
        category TEXT
    );
    """)

    # 9. Publications & Research Papers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS publications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        authors TEXT NOT NULL,
        venue TEXT,
        year INTEGER,
        doi TEXT,
        url TEXT,
        pdf_path TEXT,
        bibtex TEXT,
        display_order INTEGER DEFAULT 0
    );
    """)

    # 10. Courses & Teaching
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        institution TEXT,
        term TEXT,
        syllabus_path TEXT,
        description TEXT,
        display_order INTEGER DEFAULT 0
    );
    """)

    # 11. Directory of Contacts & References
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts_directory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        organization TEXT,
        email TEXT,
        phone TEXT,
        category TEXT,
        display_order INTEGER DEFAULT 0
    );
    """)

    # 12. Portal Bookmarks (Chrome Bookmarks Hierarchy)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chrome_id TEXT UNIQUE,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        domain TEXT,
        category TEXT NOT NULL,
        subfolder TEXT,
        path TEXT,
        ai_tags TEXT,
        favicon TEXT,
        pinned INTEGER DEFAULT 0,
        click_count INTEGER DEFAULT 0
    );
    """)
    for col_name, col_type in [("domain", "TEXT"), ("path", "TEXT"), ("ai_tags", "TEXT")]:
        try:
            cur.execute(f"ALTER TABLE portal_bookmarks ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # 13. Portal Scratches Database
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_scratches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scratch_id TEXT UNIQUE,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 14. Portal Tasks & Milestones
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE,
        title TEXT NOT NULL,
        priority TEXT DEFAULT 'normal',
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL
    );
    """)

    # 15. Portal Messages Vault
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        email TEXT,
        subject TEXT NOT NULL,
        classification TEXT DEFAULT 'Confidential',
        body TEXT NOT NULL,
        fingerprint TEXT,
        date TEXT,
        unread INTEGER DEFAULT 1
    );
    """)

    # 16. Portal Encrypted Vault (Passcodes, API Keys, Shared Secrets)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS portal_vault (
        key TEXT PRIMARY KEY,
        ciphertext TEXT NOT NULL,
        nonce TEXT NOT NULL,
        salt TEXT NOT NULL,
        description TEXT,
        updated_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized with 16 tables at: {db_path}")


def store_vault_secret(key: str, plaintext: str, description: str = "", passcode: str = DEFAULT_PORTAL_PASSCODE, db_path: Path = DB_PATH):
    """Encrypt and store a secret in the portal_vault table."""
    enc = encrypt_secret(plaintext, passcode)
    conn = get_connection(db_path)
    cur = conn.cursor()
    from datetime import datetime
    now_str = datetime.now().isoformat()

    cur.execute("""
    INSERT INTO portal_vault (key, ciphertext, nonce, salt, description, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
        ciphertext = excluded.ciphertext,
        nonce = excluded.nonce,
        salt = excluded.salt,
        description = excluded.description,
        updated_at = excluded.updated_at;
    """, (key, enc["ciphertext"], enc["nonce"], enc["salt"], description, now_str))

    conn.commit()
    conn.close()


def read_vault_secret(key: str, passcode: str = DEFAULT_PORTAL_PASSCODE, db_path: Path = DB_PATH) -> Optional[str]:
    """Read and decrypt a secret from the portal_vault table."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT ciphertext, nonce, salt FROM portal_vault WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return decrypt_secret({
        "ciphertext": row["ciphertext"],
        "nonce": row["nonce"],
        "salt": row["salt"]
    }, passcode)


if __name__ == "__main__":
    init_database()
