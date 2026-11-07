import os
from pathlib import Path

repo = Path(r"G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io")

print("=== HTML FILES ===")
for p in sorted(repo.rglob("*.html")):
    if ".git" in p.parts:
        continue
    rel = p.relative_to(repo).as_posix()
    size = p.stat().st_size
    lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
    print(f"  {rel:45s} ({lines:4d} lines, {size:7d} bytes)")

print("\n=== CSS FILES ===")
for p in sorted(repo.rglob("*.css")):
    if ".git" in p.parts:
        continue
    rel = p.relative_to(repo).as_posix()
    size = p.stat().st_size
    lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
    print(f"  {rel:45s} ({lines:4d} lines, {size:7d} bytes)")

print("\n=== JS FILES ===")
for p in sorted(repo.rglob("*.js")):
    if ".git" in p.parts:
        continue
    rel = p.relative_to(repo).as_posix()
    size = p.stat().st_size
    lines = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
    print(f"  {rel:45s} ({lines:4d} lines, {size:7d} bytes)")
