import sqlite3
import re

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'downloads'")
for key, html in cursor.fetchall():
    roses = re.findall(r'\brose-[0-9]{2,3}\b', html)
    purples = re.findall(r'\bpurple-[0-9]{2,3}\b', html)
    ambers = re.findall(r'\bamber-[0-9]{2,3}\b', html)
    indigos = re.findall(r'\bindigo-[0-9]{2,3}\b', html)
    print(f"=== {key} ===")
    if roses:
        print(f"  Roses: {set(roses)}")
    if purples:
        print(f"  Purples: {set(purples)}")
    if ambers:
        print(f"  Ambers: {set(ambers)}")
    if indigos:
        print(f"  Indigos: {set(indigos)}")

conn.close()
