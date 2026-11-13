import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Create portal_passwords table (zero plaintext metadata, strictly encrypted blobs)
cur.execute("""
CREATE TABLE IF NOT EXISTS portal_passwords (
    id TEXT PRIMARY KEY,
    ciphertext TEXT NOT NULL,
    nonce TEXT NOT NULL,
    salt TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
""")
conn.commit()
print("[OK] Ensured portal_passwords table exists in data/content.db")

# 2. Update portal_app HTML
cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'")
html, text = cur.fetchone()

# Add tab button right after tab-bookmarks
old_tab_btn = """<button class="tab-btn px-4 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-2 flex-shrink-0" data-tab="tab-bookmarks">
<i class="fas fa-bookmark"></i> <span>Bookmarks Catalog <span class="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-sky-400" id="nav-bm-count">415</span></span>
</button>"""

new_tab_btn = old_tab_btn + """
<button class="tab-btn px-4 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-2 flex-shrink-0" data-tab="tab-vault">
<i class="fas fa-key text-emerald-400"></i> <span>Password Vault <span class="ml-1 text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-emerald-400 hidden" id="nav-vault-count">0</span></span>
</button>"""

assert old_tab_btn in html, "old_tab_btn not found in portal_app"
if 'data-tab="tab-vault"' not in html:
    html = html.replace(old_tab_btn, new_tab_btn, 1)

# Add tab-vault main section & modals right before Footer
vault_html = """<!-- ============================================================= -->
<!-- TAB 6: ZERO-KNOWLEDGE ENCRYPTED PASSWORD VAULT -->
<!-- ============================================================= -->
<main class="tab-content hidden flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6" id="tab-vault">

    <!-- Vault Locked / Setup View -->
    <div id="vault-locked-view" class="max-w-lg mx-auto my-8 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        <div class="absolute -top-20 -right-20 w-52 h-52 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="text-center mb-6 relative z-10">
            <div class="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center text-2xl mx-auto mb-4 shadow-lg">
                <i class="fas fa-shield-alt"></i>
            </div>
            <h2 class="serif-heading text-xl font-bold text-white" id="vault-gate-title">Unlock Encrypted Password Vault</h2>
            <p class="text-xs text-slate-400 mt-1.5 leading-relaxed" id="vault-gate-subtitle">
                AES-256-GCM &bull; PBKDF2 (310,000 Iterations) &bull; Zero-Knowledge Client-Side Decryption.
                Plaintext credentials only exist in volatile browser memory while unlocked.
            </p>
        </div>

        <form id="vault-unlock-form" class="space-y-4 relative z-10">
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5" for="vault-master-input">
                    Master Vault Password
                </label>
                <div class="relative">
                    <input type="password" id="vault-master-input" required autocomplete="off"
                        placeholder="Enter your strong Vault Master Password..."
                        class="w-full px-4 py-3 pr-10 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition">
                    <button type="button" onclick="togglePasswordVisibility('vault-master-input', this)"
                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
                <p id="vault-setup-hint" class="hidden text-[11px] text-emerald-400/90 mt-2">
                    <i class="fas fa-info-circle mr-1"></i> First-time setup: Choose a dedicated strong Master Password to initialize your encrypted vault.
                </p>
            </div>

            <div id="vault-unlock-error" class="hidden text-xs text-rose-400 bg-rose-500/10 border border-rose-500/30 px-3 py-2 rounded-lg">
                <i class="fas fa-exclamation-triangle mr-1"></i> Incorrect Master Vault Password or corrupted ciphertext.
            </div>

            <button type="submit" id="vault-unlock-submit"
                class="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-500/20 transition flex items-center justify-center gap-2">
                <i class="fas fa-unlock-alt"></i> <span id="vault-unlock-btn-text">Unlock Vault</span>
            </button>
        </form>

        <div class="mt-6 pt-5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
            <span class="flex items-center gap-1.5"><i class="fas fa-database text-sky-400"></i> <span id="vault-db-blob-count">0</span> encrypted records</span>
            <span>Auto-locks on idle</span>
        </div>
    </div>

    <!-- Vault Unlocked Workspace -->
    <div id="vault-unlocked-view" class="hidden space-y-6">
        <!-- Top Security & Health Stats Bar -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800/80 flex items-center gap-3.5">
                <div class="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-base">
                    <i class="fas fa-key"></i>
                </div>
                <div>
                    <div class="text-xl font-bold text-white" id="vault-stat-total">0</div>
                    <div class="text-[11px] text-slate-400">Saved Logins</div>
                </div>
            </div>
            <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800/80 flex items-center gap-3.5">
                <div class="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center text-base">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <div>
                    <div class="text-xl font-bold text-white" id="vault-stat-strong">0</div>
                    <div class="text-[11px] text-slate-400">Strong Passwords</div>
                </div>
            </div>
            <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800/80 flex items-center gap-3.5">
                <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center text-base">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div>
                    <div class="text-xl font-bold text-white" id="vault-stat-issues">0</div>
                    <div class="text-[11px] text-slate-400">Weak / Reused</div>
                </div>
            </div>
            <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800/80 flex items-center justify-between gap-2">
                <div>
                    <div class="text-xs font-mono font-bold text-emerald-400 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> UNLOCKED
                    </div>
                    <div class="text-[11px] text-slate-400 mt-0.5 font-mono" id="vault-autolock-timer">Locks in 05:00</div>
                </div>
                <button onclick="lockPasswordVault()" title="Lock Vault Immediately"
                    class="px-3 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/20 text-xs font-bold transition flex items-center gap-1.5">
                    <i class="fas fa-lock"></i> Lock
                </button>
            </div>
        </div>

        <!-- Action & Search Toolbar -->
        <div class="bg-slate-900 p-5 rounded-2xl border border-slate-800/80 space-y-4">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                <div class="relative flex-1">
                    <i class="fas fa-search absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
                    <input type="text" id="vault-search-input" oninput="renderVaultCredentials()"
                        placeholder="Search credentials by site, domain, username, category, or notes..."
                        class="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-emerald-500 transition">
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <button onclick="openVaultCredentialModal()"
                        class="px-3.5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-sm transition flex items-center gap-1.5">
                        <i class="fas fa-plus"></i> Add Login
                    </button>
                    <button onclick="openVaultGeneratorModal()"
                        class="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 text-xs font-bold transition flex items-center gap-1.5">
                        <i class="fas fa-dice"></i> Generator
                    </button>
                    <button onclick="openVaultImportModal()"
                        class="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold transition flex items-center gap-1.5"
                        title="Import from Google Password Manager or LastPass CSV">
                        <i class="fas fa-file-import text-amber-400"></i> Import CSV
                    </button>
                    <button onclick="exportEncryptedVaultForSQLite()"
                        class="px-3.5 py-2.5 rounded-xl bg-sky-600/15 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 text-xs font-bold transition flex items-center gap-1.5"
                        title="Download encrypted vault JSON to sync into data/content.db">
                        <i class="fas fa-database"></i> Sync to content.db
                    </button>
                </div>
            </div>

            <!-- Category Filter Pills -->
            <div class="flex flex-wrap items-center gap-2 pt-1" id="vault-category-filters">
                <button onclick="setVaultCategoryFilter('all')" data-vault-cat="all" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 transition">All</button>
                <button onclick="setVaultCategoryFilter('Banking & Finance')" data-vault-cat="Banking & Finance" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition">Banking &amp; Finance</button>
                <button onclick="setVaultCategoryFilter('Work & Academic')" data-vault-cat="Work & Academic" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition">Work &amp; Academic</button>
                <button onclick="setVaultCategoryFilter('Email & Comms')" data-vault-cat="Email & Comms" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition">Email &amp; Comms</button>
                <button onclick="setVaultCategoryFilter('Cloud & Dev')" data-vault-cat="Cloud & Dev" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition">Cloud &amp; Dev</button>
                <button onclick="setVaultCategoryFilter('General')" data-vault-cat="General" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition">General</button>
                <button onclick="setVaultCategoryFilter('__issues__')" data-vault-cat="__issues__" class="vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition">Weak / Reused</button>
            </div>
        </div>

        <!-- Credentials Grid -->
        <div id="vault-credentials-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <!-- Populated dynamically by renderVaultCredentials() -->
        </div>

        <div id="vault-empty-msg" class="hidden text-center py-12 bg-slate-900/60 rounded-2xl border border-dashed border-slate-800">
            <i class="fas fa-key text-3xl text-slate-600 mb-3"></i>
            <p class="text-sm font-semibold text-slate-300">No credentials found in this view.</p>
            <p class="text-xs text-slate-500 mt-1">Click <strong>Add Login</strong> or <strong>Import CSV</strong> (Google Password Manager / LastPass) to get started.</p>
        </div>
    </div>
</main>

<!-- Modal: Add / Edit Credential -->
<div id="vault-credential-modal" class="fixed inset-0 z-50 hidden items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 class="text-base font-bold text-white flex items-center gap-2" id="vault-cred-modal-title">
                <i class="fas fa-key text-emerald-400"></i> Add Credential
            </h3>
            <button onclick="closeVaultCredentialModal()" class="text-slate-400 hover:text-white text-sm"><i class="fas fa-times"></i></button>
        </div>
        <form id="vault-credential-form" class="space-y-3.5">
            <input type="hidden" id="vault-cred-id">
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 mb-1">Site / Service Name *</label>
                <input type="text" id="vault-cred-name" required placeholder="e.g. Chase Bank, GitHub, TWU Portal"
                    class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 mb-1">Login URL</label>
                <input type="text" id="vault-cred-url" placeholder="https://..."
                    class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 mb-1">Username / Email *</label>
                <input type="text" id="vault-cred-username" required placeholder="islam.akef@gmail.com"
                    class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-emerald-500">
            </div>
            <div>
                <div class="flex items-center justify-between mb-1">
                    <label class="block text-[11px] font-semibold text-slate-300">Password *</label>
                    <button type="button" onclick="fillGeneratedPasswordInModal()" class="text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold">
                        <i class="fas fa-magic mr-1"></i> Generate Strong
                    </button>
                </div>
                <div class="relative">
                    <input type="password" id="vault-cred-password" required oninput="updateModalPasswordStrength()"
                        class="w-full px-3.5 py-2 pr-10 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs font-mono focus:outline-none focus:border-emerald-500">
                    <button type="button" onclick="togglePasswordVisibility('vault-cred-password', this)"
                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
                <div id="vault-cred-strength-bar" class="mt-1.5 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span id="vault-cred-strength-label">Strength: —</span>
                    <span id="vault-cred-entropy-label"></span>
                </div>
            </div>
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 mb-1">Category</label>
                <select id="vault-cred-category" class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-emerald-500">
                    <option value="Banking & Finance">Banking &amp; Finance</option>
                    <option value="Work & Academic">Work &amp; Academic</option>
                    <option value="Email & Comms">Email &amp; Comms</option>
                    <option value="Cloud & Dev">Cloud &amp; Dev</option>
                    <option value="General">General</option>
                </select>
            </div>
            <div>
                <label class="block text-[11px] font-semibold text-slate-300 mb-1">Secure Notes (Optional)</label>
                <textarea id="vault-cred-notes" rows="2" placeholder="Recovery codes, PINs, security questions..."
                    class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-xs focus:outline-none focus:border-emerald-500"></textarea>
            </div>
            <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button type="button" onclick="closeVaultCredentialModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold">Cancel</button>
                <button type="submit" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow">Encrypt &amp; Save</button>
            </div>
        </form>
    </div>
</div>

<!-- Modal: Password Generator -->
<div id="vault-generator-modal" class="fixed inset-0 z-50 hidden items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fas fa-dice text-sky-400"></i> Cryptographic Password Generator
            </h3>
            <button onclick="closeVaultGeneratorModal()" class="text-slate-400 hover:text-white text-sm"><i class="fas fa-times"></i></button>
        </div>
        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-2">
            <code id="vault-gen-output" class="text-sm font-mono text-emerald-400 break-all select-all"></code>
            <div class="flex items-center gap-1.5 flex-shrink-0">
                <button onclick="generateAndDisplayPassword()" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs" title="Regenerate"><i class="fas fa-sync-alt"></i></button>
                <button onclick="copyGeneratedPassword()" class="p-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs" title="Copy"><i class="far fa-copy"></i></button>
            </div>
        </div>
        <div class="space-y-3 text-xs text-slate-300">
            <div class="flex items-center justify-between">
                <span>Length: <strong id="vault-gen-len-val" class="text-sky-400 font-mono">20</strong></span>
                <input type="range" id="vault-gen-len" min="12" max="64" value="20" oninput="document.getElementById('vault-gen-len-val').textContent=this.value; generateAndDisplayPassword();" class="w-48 accent-emerald-500">
            </div>
            <div class="grid grid-cols-2 gap-2">
                <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" id="vault-gen-upper" checked onchange="generateAndDisplayPassword()" class="accent-emerald-500"> Uppercase (A-Z)</label>
                <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" id="vault-gen-lower" checked onchange="generateAndDisplayPassword()" class="accent-emerald-500"> Lowercase (a-z)</label>
                <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" id="vault-gen-nums" checked onchange="generateAndDisplayPassword()" class="accent-emerald-500"> Numbers (0-9)</label>
                <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" id="vault-gen-syms" checked onchange="generateAndDisplayPassword()" class="accent-emerald-500"> Symbols (!@#$%)</label>
            </div>
            <div id="vault-gen-entropy" class="text-[11px] font-mono text-slate-400 pt-1"></div>
        </div>
    </div>
</div>

<!-- Modal: Import CSV (Google Password Manager / LastPass) -->
<div id="vault-import-modal" class="fixed inset-0 z-50 hidden items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 class="text-base font-bold text-white flex items-center gap-2">
                <i class="fas fa-file-import text-amber-400"></i> Import from Google / LastPass CSV
            </h3>
            <button onclick="closeVaultImportModal()" class="text-slate-400 hover:text-white text-sm"><i class="fas fa-times"></i></button>
        </div>
        <p class="text-xs text-slate-400 leading-relaxed">
            Export your passwords as CSV from <strong>Chrome / Google Password Manager</strong> (<code class="text-sky-300">name, url, username, password</code>) or <strong>LastPass</strong> (<code class="text-sky-300">url, username, password, extra, name, grouping</code>). Parsing and AES-256-GCM encryption happen 100% locally in your browser.
        </p>
        <div class="border-2 border-dashed border-slate-700 hover:border-emerald-500/60 rounded-xl p-6 text-center transition">
            <input type="file" id="vault-csv-file" accept=".csv" onchange="handleVaultCsvFileSelect(event)" class="hidden">
            <label for="vault-csv-file" class="cursor-pointer flex flex-col items-center gap-2">
                <i class="fas fa-cloud-upload-alt text-3xl text-emerald-400"></i>
                <span class="text-xs font-bold text-slate-200">Click to select exported .csv file</span>
                <span class="text-[11px] text-slate-500" id="vault-import-status">No file selected yet</span>
            </label>
        </div>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button type="button" onclick="closeVaultImportModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold">Close</button>
            <button type="button" id="vault-confirm-import-btn" onclick="confirmVaultCsvImport()" disabled
                class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold shadow">
                Encrypt &amp; Import
            </button>
        </div>
    </div>
</div>
<!-- Footer -->"""

assert '<!-- Footer -->' in html, "Footer marker not found in portal_app"
if 'id="tab-vault"' not in html:
    html = html.replace('<!-- Footer -->', vault_html, 1)

cur.execute("UPDATE page_sections SET content_html=? WHERE page_slug='portal' AND section_key='portal_app'", (html,))
conn.commit()
conn.close()
print("[OK] Updated portal_app in data/content.db with Password Vault tab and modals")
