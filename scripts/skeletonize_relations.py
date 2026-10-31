import re
import shutil
from pathlib import Path

rel_file = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/relations/relations.html")
bak_file = Path("G:/My Drive/Documents/Projects/Career/Website/iebeid.github.io/pages/relations/relations.html.bak")

# Backup
shutil.copy(rel_file, bak_file)

with open(rel_file, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

new_main = """    <main class="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="max-w-4xl mx-auto space-y-10">

            <!-- Section 1: Contact Information (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.contact"></div>

            <!-- Confidential Dead-Drop Callout -->
            <div class="p-6 rounded-xl bg-slate-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-slate-800 shadow-md">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0 text-base">
                        <i class="fas fa-shield-halved"></i>
                    </div>
                    <div>
                        <h3 class="text-sm font-bold text-white flex items-center gap-2">
                            Confidential Dead-Drop &amp; Secure Transmission Vault
                            <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">Encrypted</span>
                        </h3>
                        <p class="text-xs text-slate-300 mt-0.5">
                            Need to transmit sensitive research disclosures or confidential inquiries? Access Dr. Islam's verified zero-trust drop-box.
                        </p>
                    </div>
                </div>
                <a href="drop.html" class="inline-flex items-center gap-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition whitespace-nowrap shadow-md flex-shrink-0">
                    <i class="fas fa-key"></i> Access Secure Drop
                </a>
            </div>

            <!-- Section 1.5: Academic Mentors & References (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.mentors"></div>

            <!-- Section 1.6: Student Mentorship & Advising (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.students"></div>

            <!-- Section 2: Fatherhood & Family Life (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.fatherhood"></div>

            <!-- Section 3: Managed Community Groups (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.section_5"></div>

            <!-- Section 4: Academic, Scholarly & Social Networks (Loaded dynamically from SQLite) -->
            <div data-db-section="relations.section_6"></div>

        </div>
    </main>"""

content = re.sub(r'<main.*?</main>', new_main, content, flags=re.DOTALL)

# Add scripts before </body>
scripts_tag = """    <!-- SQLite Content Database & Dynamic Loader -->
    <script src="../../data/public_content.js"></script>
    <script src="../../js/content-loader.js"></script>
</body>"""

if "public_content.js" not in content:
    content = content.replace("</body>", scripts_tag)

with open(rel_file, "w", encoding="utf-8") as f:
    f.write(content)

print("[SUCCESS] relations.html transformed into dynamic template skeleton!")
