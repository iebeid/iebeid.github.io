# Automation & Maintenance Toolchain

This directory houses the operational scripts powering the SQLite headless CMS, content hydration, verification, and deployment for `iebeid.github.io`.

## Active Core Tools

| Script | Purpose | Usage |
| :--- | :--- | :--- |
| **`sync_content.py`** | Central serialization & deployment engine. Reads `data/content.db`, synchronizes bookmarks, exports `public_content.json` & `public_content.js`, stages git changes, commits, and pushes. | `python scripts/sync_content.py [--export-only] [--no-push] [--dry-run] [-m "Commit message"]` |
| **`database_manager.py`** | SQLite schema definitions, CRUD helpers, and PBKDF2/AES-256-GCM encrypted vault manager. | `python scripts/database_manager.py` |
| **`query_db.py`** | Quick diagnostic script that displays record counts across all SQLite tables. | `python scripts/query_db.py` |
| **`verify_render.py`** | Full-stack validator ensuring that all body template placeholders match SQLite sections, HTML shells are properly configured, and public JSON artifacts are intact. | `python scripts/verify_render.py` |
| **`test_verify_all.py`** | Fast tag validator checking that exported section markup contains well-formed container tags. | `python scripts/test_verify_all.py` |

## Archived Migration Scripts (`archive/`)

The `archive/` subfolder contains historical, one-off extraction, parsing, and migration scripts (such as `extract_cv.py`, `update_edu.py`, `skeletonize_*.py`) that were executed during the initial migration of unstructured documents and HTML files into the unified SQLite database.
