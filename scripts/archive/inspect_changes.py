import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/content.db')
cursor = conn.cursor()

cursor.execute("SELECT section_key, content_html FROM page_sections WHERE page_slug = 'storefront'")
for key, html in cursor.fetchall():
    if "From Published Research" in html or "GPU Compute" in html:
        print(f"=== MATCH in section {key} ===")
        for line in html.splitlines():
            if "From Published Research" in line or "GPU Compute" in line or "CudaParticles" in line:
                print("  ", line.strip()[:140])

conn.close()
