import re
import shutil
from pathlib import Path

home_file = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/home/home.html")
bak_file = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/home/home.html.bak")

# Backup
shutil.copy(home_file, bak_file)

with open(home_file, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Replace <main>...</main>
new_main = """    <main id="main-content">
        <!-- Dynamic Page Sections populated from SQLite via js/content-loader.js -->
        <div data-db-section="home.home"></div>
        <div data-db-section="home.about"></div>
        <div data-db-section="home.current-research"></div>
        <div data-db-section="home.experience"></div>
        <div data-db-section="home.publications"></div>
    </main>"""

content = re.sub(r'<main>.*?</main>', new_main, content, flags=re.DOTALL)

# Add scripts before </body> if not present
scripts_snippet = """    <!-- SQLite Content Database & Dynamic Loader -->
    <script src="../../data/public_content.js"></script>
    <script src="../../js/content-loader.js"></script>
</body>"""

if "content-loader.js" not in content:
    content = content.replace("</body>", scripts_snippet)

with open(home_file, "w", encoding="utf-8") as f:
    f.write(content)

print("[SUCCESS] home.html transformed into dynamic template skeleton!")
