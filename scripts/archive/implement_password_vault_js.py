with open('js/portal.js', 'r', encoding='utf-8') as f:
    js = f.read()

vault_module = r"""
    // -------------------------------------------------------------------------
    // 16. ZERO-KNOWLEDGE ENCRYPTED PASSWORD VAULT (AES-256-GCM + PBKDF2)
    // -------------------------------------------------------------------------
    const VAULT_STORAGE_KEY = 'portal_encrypted_passwords_v1';
    const VAULT_PBKDF2_ITERATIONS = 310000;
    const VAULT_AUTOLOCK_SECONDS = 300; // 5 minutes

    let vaultMasterPassword = null;      // Volatile memory only while unlocked
    let unlockedCredentials = [];        // Decrypted credentials in memory only
    let activeVaultCategory = 'all';
    let vaultAutoLockRemaining = VAULT_AUTOLOCK_SECONDS;
    let vaultAutoLockInterval = null;
    let pendingCsvParsedRecords = [];

    function uint8ArrayToBase64(bytes) {
        let bin = '';
        for (let i = 0; i < bytes.length; i++) {
            bin += String.fromCharCode(bytes[i]);
        }
        return btoa(bin);
    }

    function getEncryptedVaultBlobs() {
        const dbBlobs = (window.__SITE_DATABASE && Array.isArray(window.__SITE_DATABASE.portal_passwords))
            ? window.__SITE_DATABASE.portal_passwords
            : [];
        let localBlobs = null;
        try {
            const raw = localStorage.getItem(VAULT_STORAGE_KEY);
            if (raw) localBlobs = JSON.parse(raw);
        } catch (e) { }

        // If localStorage has been initialized by the user, prefer the union or latest local snapshot
        if (Array.isArray(localBlobs)) {
            const mergedMap = new Map();
            dbBlobs.forEach(b => mergedMap.set(b.id, b));
            localBlobs.forEach(b => mergedMap.set(b.id, b));
            return Array.from(mergedMap.values());
        }
        return dbBlobs;
    }

    function saveEncryptedVaultBlobs(blobs) {
        localStorage.setItem(VAULT_STORAGE_KEY, JSON.stringify(blobs));
        updateVaultCountBadges(blobs.length);
    }

    function updateVaultCountBadges(count) {
        const navBadge = document.getElementById('nav-vault-count');
        const dbCountEl = document.getElementById('vault-db-blob-count');
        if (navBadge) {
            navBadge.textContent = count;
            navBadge.classList.toggle('hidden', count === 0);
        }
        if (dbCountEl) dbCountEl.textContent = count;
    }

    async function encryptVaultPayload(plainObj, masterPassword) {
        const enc = new TextEncoder();
        const salt = window.crypto.getRandomValues(new Uint8Array(16));
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        const keyMaterial = await window.crypto.subtle.importKey(
            'raw', enc.encode(masterPassword), { name: 'PBKDF2' }, false, ['deriveKey']
        );
        const aesKey = await window.crypto.subtle.deriveKey(
            { name: 'PBKDF2', salt: salt, iterations: VAULT_PBKDF2_ITERATIONS, hash: 'SHA-256' },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            false,
            ['encrypt']
        );

        const plaintextBytes = enc.encode(JSON.stringify(plainObj));
        const encryptedBuf = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            aesKey,
            plaintextBytes
        );

        return {
            id: plainObj.id,
            ciphertext: uint8ArrayToBase64(new Uint8Array(encryptedBuf)),
            nonce: uint8ArrayToBase64(iv),
            salt: uint8ArrayToBase64(salt),
            updated_at: plainObj.updatedAt || new Date().toISOString()
        };
    }

    async function decryptVaultBlob(blob, masterPassword) {
        if (!blob || !blob.ciphertext || !blob.nonce || !blob.salt) return null;
        try {
            const enc = new TextEncoder();
            const salt = base64ToUint8Array(blob.salt);
            const iv = base64ToUint8Array(blob.nonce);
            const ciphertext = base64ToUint8Array(blob.ciphertext);

            const keyMaterial = await window.crypto.subtle.importKey(
                'raw', enc.encode(masterPassword), { name: 'PBKDF2' }, false, ['deriveKey']
            );
            const aesKey = await window.crypto.subtle.deriveKey(
                { name: 'PBKDF2', salt: salt, iterations: VAULT_PBKDF2_ITERATIONS, hash: 'SHA-256' },
                keyMaterial,
                { name: 'AES-GCM', length: 256 },
                false,
                ['decrypt']
            );

            const decryptedBuf = await window.crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: iv },
                aesKey,
                ciphertext
            );
            const jsonStr = new TextDecoder().decode(decryptedBuf);
            return JSON.parse(jsonStr);
        } catch (err) {
            return null;
        }
    }

    function initPasswordVault() {
        const blobs = getEncryptedVaultBlobs();
        updateVaultCountBadges(blobs.length);

        const setupHint = document.getElementById('vault-setup-hint');
        const gateTitle = document.getElementById('vault-gate-title');
        const btnText = document.getElementById('vault-unlock-btn-text');
        if (blobs.length === 0) {
            if (setupHint) setupHint.classList.remove('hidden');
            if (gateTitle) gateTitle.textContent = 'Initialize Encrypted Password Vault';
            if (btnText) btnText.textContent = 'Create & Unlock Vault';
        } else {
            if (setupHint) setupHint.classList.add('hidden');
            if (gateTitle) gateTitle.textContent = 'Unlock Encrypted Password Vault';
            if (btnText) btnText.textContent = 'Unlock Vault';
        }

        const unlockForm = document.getElementById('vault-unlock-form');
        if (unlockForm && !unlockForm.dataset.bound) {
            unlockForm.dataset.bound = 'true';
            unlockForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const input = document.getElementById('vault-master-input');
                const errEl = document.getElementById('vault-unlock-error');
                const submitBtn = document.getElementById('vault-unlock-submit');
                const pass = input ? input.value : '';
                if (!pass) return;

                if (errEl) errEl.classList.add('hidden');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deriving Key...';
                }

                const currentBlobs = getEncryptedVaultBlobs();
                if (currentBlobs.length === 0) {
                    // First-time initialization with empty vault
                    vaultMasterPassword = pass;
                    unlockedCredentials = [];
                    if (input) input.value = '';
                    showUnlockedVaultView();
                    showPortalToast('Password Vault initialized with AES-256-GCM');
                } else {
                    const decryptedList = [];
                    let failed = false;
                    for (const blob of currentBlobs) {
                        const dec = await decryptVaultBlob(blob, pass);
                        if (!dec) {
                            failed = true;
                            break;
                        }
                        decryptedList.push(dec);
                    }

                    if (failed) {
                        if (errEl) errEl.classList.remove('hidden');
                    } else {
                        vaultMasterPassword = pass;
                        unlockedCredentials = decryptedList;
                        if (input) input.value = '';
                        showUnlockedVaultView();
                        showPortalToast(`Unlocked ${decryptedList.length} encrypted credentials`);
                    }
                }

                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-unlock-alt"></i> <span id="vault-unlock-btn-text">Unlock Vault</span>';
                }
            });
        }

        const credForm = document.getElementById('vault-credential-form');
        if (credForm && !credForm.dataset.bound) {
            credForm.dataset.bound = 'true';
            credForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await saveVaultCredentialFromModal();
            });
        }
    }

    function showUnlockedVaultView() {
        const lockedView = document.getElementById('vault-locked-view');
        const unlockedView = document.getElementById('vault-unlocked-view');
        if (lockedView) lockedView.classList.add('hidden');
        if (unlockedView) unlockedView.classList.remove('hidden');
        resetVaultAutoLock();
        renderVaultCredentials();
    }

    window.lockPasswordVault = function() {
        vaultMasterPassword = null;
        unlockedCredentials = [];
        if (vaultAutoLockInterval) {
            clearInterval(vaultAutoLockInterval);
            vaultAutoLockInterval = null;
        }
        const lockedView = document.getElementById('vault-locked-view');
        const unlockedView = document.getElementById('vault-unlocked-view');
        if (unlockedView) unlockedView.classList.add('hidden');
        if (lockedView) lockedView.classList.remove('hidden');
        const grid = document.getElementById('vault-credentials-grid');
        if (grid) grid.innerHTML = '';
        initPasswordVault();
        showPortalToast('Password Vault locked & memory cleared');
    };

    function resetVaultAutoLock() {
        vaultAutoLockRemaining = VAULT_AUTOLOCK_SECONDS;
        if (vaultAutoLockInterval) clearInterval(vaultAutoLockInterval);
        vaultAutoLockInterval = setInterval(() => {
            if (!vaultMasterPassword) {
                clearInterval(vaultAutoLockInterval);
                return;
            }
            vaultAutoLockRemaining--;
            const timerEl = document.getElementById('vault-autolock-timer');
            if (timerEl) {
                const mins = String(Math.floor(vaultAutoLockRemaining / 60)).padStart(2, '0');
                const secs = String(vaultAutoLockRemaining % 60).padStart(2, '0');
                timerEl.textContent = `Locks in ${mins}:${secs}`;
            }
            if (vaultAutoLockRemaining <= 0) {
                lockPasswordVault();
            }
        }, 1000);
    }

    function calculatePasswordEntropy(pwd) {
        if (!pwd) return { bits: 0, label: 'Empty', color: 'text-slate-500', isWeak: true };
        let pool = 0;
        if (/[a-z]/.test(pwd)) pool += 26;
        if (/[A-Z]/.test(pwd)) pool += 26;
        if (/[0-9]/.test(pwd)) pool += 10;
        if (/[^a-zA-Z0-9]/.test(pwd)) pool += 32;
        const bits = Math.round(pwd.length * Math.log2(Math.max(pool, 1)));
        if (bits < 45 || pwd.length < 10) return { bits, label: 'Weak', color: 'text-rose-400', isWeak: true };
        if (bits < 70) return { bits, label: 'Fair', color: 'text-amber-400', isWeak: false };
        if (bits < 100) return { bits, label: 'Strong', color: 'text-emerald-400', isWeak: false };
        return { bits, label: 'Very Strong', color: 'text-sky-400', isWeak: false };
    }

    function inferCredentialCategory(name, url) {
        const text = `${name || ''} ${url || ''}`.toLowerCase();
        if (['bank', 'chase', 'capitalone', 'fidelity', 'robinhood', 'tiaa', 'trs', 'tax', 'earnin', 'upstart', 'payment', 'paypal', 'stripe', 'empower', 'moneymanagement', 'alahly'].some(k => text.includes(k))) {
            return 'Banking & Finance';
        }
        if (['twu.edu', 'instructure', 'canvas', 'nih.gov', 'nsf.gov', 'grants', 'overleaf', 'scholar', 'orcid', 'research', 'arxiv', 'ieee'].some(k => text.includes(k))) {
            return 'Work & Academic';
        }
        if (['mail', 'gmail', 'outlook', 'proton', 'yahoo', 'slack', 'discord', 'zoom', 'teams'].some(k => text.includes(k))) {
            return 'Email & Comms';
        }
        if (['github', 'gitlab', 'aws', 'cloud', 'azure', 'google', 'huggingface', 'kaggle', 'nvidia', 'docker', 'vercel', 'netlify'].some(k => text.includes(k))) {
            return 'Cloud & Dev';
        }
        return 'General';
    }

    function extractDomainSafe(url) {
        try {
            if (!url) return 'web';
            const u = new URL(url.startsWith('http') ? url : 'https://' + url);
            return u.hostname.replace(/^www\./, '');
        } catch (e) {
            return 'web';
        }
    }

    window.setVaultCategoryFilter = function(cat) {
        activeVaultCategory = cat;
        document.querySelectorAll('.vault-cat-btn').forEach(btn => {
            const isMatch = btn.getAttribute('data-vault-cat') === cat;
            if (isMatch) {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 transition';
            } else if (btn.getAttribute('data-vault-cat') === '__issues__') {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition';
            } else {
                btn.className = 'vault-cat-btn px-3 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 hover:text-white transition';
            }
        });
        renderVaultCredentials();
    };

    window.renderVaultCredentials = function() {
        if (!vaultMasterPassword) return;
        resetVaultAutoLock();

        const grid = document.getElementById('vault-credentials-grid');
        const emptyMsg = document.getElementById('vault-empty-msg');
        if (!grid) return;

        // Compute reuse counts in-memory
        const pwdFreq = {};
        unlockedCredentials.forEach(c => {
            if (c.password) pwdFreq[c.password] = (pwdFreq[c.password] || 0) + 1;
        });

        let strongCount = 0;
        let issuesCount = 0;
        unlockedCredentials.forEach(c => {
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;
            if (ent.isWeak || isReused) issuesCount++;
            else strongCount++;
        });

        const statTotal = document.getElementById('vault-stat-total');
        const statStrong = document.getElementById('vault-stat-strong');
        const statIssues = document.getElementById('vault-stat-issues');
        if (statTotal) statTotal.textContent = unlockedCredentials.length;
        if (statStrong) statStrong.textContent = strongCount;
        if (statIssues) statIssues.textContent = issuesCount;

        const query = (document.getElementById('vault-search-input')?.value || '').toLowerCase().trim();

        const filtered = unlockedCredentials.filter(c => {
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;
            if (activeVaultCategory === '__issues__') {
                if (!ent.isWeak && !isReused) return false;
            } else if (activeVaultCategory !== 'all') {
                if ((c.category || 'General') !== activeVaultCategory) return false;
            }

            if (query) {
                const hay = `${c.name || ''} ${c.url || ''} ${c.domain || ''} ${c.username || ''} ${c.category || ''} ${c.notes || ''}`.toLowerCase();
                if (!hay.includes(query)) return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            grid.innerHTML = '';
            if (emptyMsg) emptyMsg.classList.remove('hidden');
            return;
        }
        if (emptyMsg) emptyMsg.classList.add('hidden');

        grid.innerHTML = filtered.map(c => {
            const domain = c.domain || extractDomainSafe(c.url);
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
            const ent = calculatePasswordEntropy(c.password);
            const isReused = (pwdFreq[c.password] || 0) > 1;

            let healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">${ent.label}</span>`;
            if (ent.isWeak) {
                healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">Weak (${ent.bits}b)</span>`;
            } else if (isReused) {
                healthBadge = `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">Reused</span>`;
            }

            return `
            <div class="bg-slate-900 border border-slate-800 hover:border-emerald-500/40 rounded-2xl p-4 shadow-sm transition flex flex-col justify-between">
                <div>
                    <div class="flex items-start justify-between gap-2 mb-3">
                        <div class="flex items-center gap-2.5 min-w-0">
                            <img src="${faviconUrl}" alt="" onerror="this.onerror=null;this.src='../../images/favicon.png'" class="w-6 h-6 rounded object-contain bg-slate-950 p-0.5 border border-slate-800 flex-shrink-0">
                            <div class="min-w-0">
                                <h4 class="text-sm font-bold text-slate-100 truncate" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</h4>
                                <p class="text-[10px] font-mono text-slate-500 truncate">${escapeHtml(domain)}</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-1 flex-shrink-0">
                            ${healthBadge}
                        </div>
                    </div>

                    <div class="space-y-2 mb-3">
                        <div class="flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800/80">
                            <div class="min-w-0">
                                <span class="text-[9px] uppercase tracking-wider text-slate-500 block">Username</span>
                                <span class="text-xs font-mono text-slate-200 truncate block">${escapeHtml(c.username)}</span>
                            </div>
                            <button onclick="copyVaultField('${escapeHtml(c.id)}', 'username')" class="text-slate-400 hover:text-sky-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs flex-shrink-0" title="Copy Username">
                                <i class="far fa-copy"></i>
                            </button>
                        </div>

                        <div class="flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800/80">
                            <div class="min-w-0 flex-1">
                                <span class="text-[9px] uppercase tracking-wider text-slate-500 block">Password</span>
                                <span id="vault-pwd-display-${escapeHtml(c.id)}" data-revealed="false" class="text-xs font-mono text-slate-200 tracking-widest truncate block">&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;</span>
                            </div>
                            <div class="flex items-center gap-1 flex-shrink-0">
                                <button onclick="toggleRevealVaultPwd('${escapeHtml(c.id)}', this)" class="text-slate-400 hover:text-amber-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs" title="Show / Hide">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button onclick="copyVaultField('${escapeHtml(c.id)}', 'password')" class="text-slate-400 hover:text-emerald-400 p-1.5 rounded-lg hover:bg-slate-800 transition text-xs" title="Copy Password (Auto-clears in 30s)">
                                    <i class="far fa-copy"></i>
                                </button>
                            </div>
                        </div>
                    </div>

                    ${c.notes ? `<p class="text-[11px] text-slate-400 line-clamp-2 mb-3 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/50">${escapeHtml(c.notes)}</p>` : ''}
                </div>

                <div class="pt-2.5 border-t border-slate-800/60 flex items-center justify-between">
                    <span class="text-[10px] font-semibold text-slate-400 bg-slate-800/70 px-2 py-0.5 rounded-full">${escapeHtml(c.category || 'General')}</span>
                    <div class="flex items-center gap-1.5">
                        ${c.url ? `<a href="${escapeHtml(c.url.startsWith('http') ? c.url : 'https://' + c.url)}" target="_blank" rel="noopener" class="w-7 h-7 rounded-lg bg-sky-600/15 hover:bg-sky-600 text-sky-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Open Login Page"><i class="fas fa-external-link-alt"></i></a>` : ''}
                        <button onclick="openVaultCredentialModal('${escapeHtml(c.id)}')" class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Edit"><i class="fas fa-pen"></i></button>
                        <button onclick="deleteVaultCredential('${escapeHtml(c.id)}')" class="w-7 h-7 rounded-lg bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white flex items-center justify-center transition text-[10px]" title="Delete"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>
            </div>`;
        }).join('');
    };

    window.togglePasswordVisibility = function(inputId, btn) {
        const input = document.getElementById(inputId);
        if (!input) return;
        const isPwd = input.type === 'password';
        input.type = isPwd ? 'text' : 'password';
        if (btn) btn.innerHTML = isPwd ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
    };

    window.toggleRevealVaultPwd = function(credId, btn) {
        resetVaultAutoLock();
        const cred = unlockedCredentials.find(c => c.id === credId);
        const span = document.getElementById(`vault-pwd-display-${credId}`);
        if (!cred || !span) return;
        const revealed = span.getAttribute('data-revealed') === 'true';
        if (revealed) {
            span.innerHTML = '&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;';
            span.classList.add('tracking-widest');
            span.setAttribute('data-revealed', 'false');
            if (btn) btn.innerHTML = '<i class="fas fa-eye"></i>';
        } else {
            span.textContent = cred.password;
            span.classList.remove('tracking-widest');
            span.setAttribute('data-revealed', 'true');
            if (btn) btn.innerHTML = '<i class="fas fa-eye-slash text-amber-400"></i>';
        }
    };

    window.copyVaultField = async function(credId, field) {
        resetVaultAutoLock();
        const cred = unlockedCredentials.find(c => c.id === credId);
        if (!cred) return;
        const val = cred[field] || '';
        try {
            await navigator.clipboard.writeText(val);
            if (field === 'password') {
                showPortalToast('Password copied! Clipboard auto-clears in 30s');
                setTimeout(async () => {
                    try {
                        const current = await navigator.clipboard.readText();
                        if (current === val) await navigator.clipboard.writeText('');
                    } catch (e) { }
                }, 30000);
            } else {
                showPortalToast('Username copied to clipboard');
            }
        } catch (err) {
            showPortalToast('Clipboard access denied by browser');
        }
    };

    function generateCryptographicPassword(length = 20, useUpper = true, useLower = true, useNums = true, useSyms = true) {
        let charset = '';
        if (useUpper) charset += 'ABCDEFGHJKLMNPQRSTUVWXYZ';
        if (useLower) charset += 'abcdefghijkmnopqrstuvwxyz';
        if (useNums) charset += '23456789';
        if (useSyms) charset += '!@#$%^&*-_=+?';
        if (!charset) charset = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';

        const arr = new Uint32Array(length);
        window.crypto.getRandomValues(arr);
        let pwd = '';
        for (let i = 0; i < length; i++) {
            pwd += charset[arr[i] % charset.length];
        }
        return pwd;
    }

    window.openVaultCredentialModal = function(credId = null) {
        resetVaultAutoLock();
        const modal = document.getElementById('vault-credential-modal');
        if (!modal) return;

        const titleEl = document.getElementById('vault-cred-modal-title');
        const idEl = document.getElementById('vault-cred-id');
        const nameEl = document.getElementById('vault-cred-name');
        const urlEl = document.getElementById('vault-cred-url');
        const userEl = document.getElementById('vault-cred-username');
        const pwdEl = document.getElementById('vault-cred-password');
        const catEl = document.getElementById('vault-cred-category');
        const notesEl = document.getElementById('vault-cred-notes');

        if (credId) {
            const cred = unlockedCredentials.find(c => c.id === credId);
            if (!cred) return;
            if (titleEl) titleEl.innerHTML = '<i class="fas fa-pen text-sky-400"></i> Edit Credential';
            if (idEl) idEl.value = cred.id;
            if (nameEl) nameEl.value = cred.name || '';
            if (urlEl) urlEl.value = cred.url || '';
            if (userEl) userEl.value = cred.username || '';
            if (pwdEl) { pwdEl.value = cred.password || ''; pwdEl.type = 'password'; }
            if (catEl) catEl.value = cred.category || 'General';
            if (notesEl) notesEl.value = cred.notes || '';
        } else {
            if (titleEl) titleEl.innerHTML = '<i class="fas fa-key text-emerald-400"></i> Add Credential';
            if (idEl) idEl.value = '';
            if (nameEl) nameEl.value = '';
            if (urlEl) urlEl.value = '';
            if (userEl) userEl.value = '';
            if (pwdEl) { pwdEl.value = ''; pwdEl.type = 'password'; }
            if (catEl) catEl.value = 'General';
            if (notesEl) notesEl.value = '';
        }

        updateModalPasswordStrength();
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        if (nameEl) nameEl.focus();
    };

    window.closeVaultCredentialModal = function() {
        const modal = document.getElementById('vault-credential-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.fillGeneratedPasswordInModal = function() {
        const pwdEl = document.getElementById('vault-cred-password');
        if (!pwdEl) return;
        pwdEl.value = generateCryptographicPassword(22, true, true, true, true);
        pwdEl.type = 'text';
        updateModalPasswordStrength();
    };

    window.updateModalPasswordStrength = function() {
        const pwd = document.getElementById('vault-cred-password')?.value || '';
        const ent = calculatePasswordEntropy(pwd);
        const lbl = document.getElementById('vault-cred-strength-label');
        const bitsLbl = document.getElementById('vault-cred-entropy-label');
        if (lbl) {
            lbl.textContent = `Strength: ${ent.label}`;
            lbl.className = ent.color;
        }
        if (bitsLbl) bitsLbl.textContent = `${ent.bits} bits entropy`;
    };

    async function saveVaultCredentialFromModal() {
        if (!vaultMasterPassword) return;
        const idVal = document.getElementById('vault-cred-id')?.value;
        const name = document.getElementById('vault-cred-name')?.value.trim() || '';
        const url = document.getElementById('vault-cred-url')?.value.trim() || '';
        const username = document.getElementById('vault-cred-username')?.value.trim() || '';
        const password = document.getElementById('vault-cred-password')?.value || '';
        const category = document.getElementById('vault-cred-category')?.value || inferCredentialCategory(name, url);
        const notes = document.getElementById('vault-cred-notes')?.value.trim() || '';

        if (!name || !username || !password) return;

        const nowIso = new Date().toISOString();
        const credId = idVal || ('cred_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7));
        const credObj = {
            id: credId,
            name,
            url,
            domain: extractDomainSafe(url),
            username,
            password,
            category,
            notes,
            updatedAt: nowIso
        };

        const blob = await encryptVaultPayload(credObj, vaultMasterPassword);
        const blobs = getEncryptedVaultBlobs().filter(b => b.id !== credId);
        blobs.unshift(blob);
        saveEncryptedVaultBlobs(blobs);

        unlockedCredentials = unlockedCredentials.filter(c => c.id !== credId);
        unlockedCredentials.unshift(credObj);

        closeVaultCredentialModal();
        renderVaultCredentials();
        showPortalToast(`Encrypted & saved login for ${name}`);
    }

    window.deleteVaultCredential = function(credId) {
        if (!vaultMasterPassword) return;
        const cred = unlockedCredentials.find(c => c.id === credId);
        if (!cred) return;
        if (!confirm(`Delete encrypted login for "${cred.name}" (${cred.username})?`)) return;

        unlockedCredentials = unlockedCredentials.filter(c => c.id !== credId);
        const blobs = getEncryptedVaultBlobs().filter(b => b.id !== credId);
        saveEncryptedVaultBlobs(blobs);
        renderVaultCredentials();
        showPortalToast(`Deleted ${cred.name} from vault`);
    };

    // Password Generator Modal
    window.openVaultGeneratorModal = function() {
        resetVaultAutoLock();
        const modal = document.getElementById('vault-generator-modal');
        if (!modal) return;
        generateAndDisplayPassword();
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    };

    window.closeVaultGeneratorModal = function() {
        const modal = document.getElementById('vault-generator-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.generateAndDisplayPassword = function() {
        const len = parseInt(document.getElementById('vault-gen-len')?.value || '20', 10);
        const u = document.getElementById('vault-gen-upper')?.checked !== false;
        const l = document.getElementById('vault-gen-lower')?.checked !== false;
        const n = document.getElementById('vault-gen-nums')?.checked !== false;
        const s = document.getElementById('vault-gen-syms')?.checked !== false;

        const pwd = generateCryptographicPassword(len, u, l, n, s);
        const outEl = document.getElementById('vault-gen-output');
        const entEl = document.getElementById('vault-gen-entropy');
        if (outEl) outEl.textContent = pwd;
        if (entEl) {
            const ent = calculatePasswordEntropy(pwd);
            entEl.innerHTML = `Entropy: <strong class="${ent.color}">${ent.bits} bits (${ent.label})</strong>`;
        }
    };

    window.copyGeneratedPassword = async function() {
        const pwd = document.getElementById('vault-gen-output')?.textContent || '';
        if (!pwd) return;
        await navigator.clipboard.writeText(pwd);
        showPortalToast('Generated password copied to clipboard');
    };

    // CSV Parser & Importer (Google Password Manager & LastPass)
    function parseCsvMatrix(text) {
        const rows = [];
        let row = [];
        let field = '';
        let inQuotes = false;
        for (let i = 0; i < text.length; i++) {
            const ch = text[i];
            const next = text[i + 1];
            if (inQuotes) {
                if (ch === '"' && next === '"') {
                    field += '"';
                    i++;
                } else if (ch === '"') {
                    inQuotes = false;
                } else {
                    field += ch;
                }
            } else {
                if (ch === '"') {
                    inQuotes = true;
                } else if (ch === ',') {
                    row.push(field);
                    field = '';
                } else if (ch === '\r' && next === '\n') {
                    row.push(field);
                    rows.push(row);
                    row = [];
                    field = '';
                    i++;
                } else if (ch === '\n' || ch === '\r') {
                    row.push(field);
                    rows.push(row);
                    row = [];
                    field = '';
                } else {
                    field += ch;
                }
            }
        }
        if (field.length > 0 || row.length > 0) {
            row.push(field);
            rows.push(row);
        }
        return rows;
    }

    window.openVaultImportModal = function() {
        resetVaultAutoLock();
        pendingCsvParsedRecords = [];
        const statusEl = document.getElementById('vault-import-status');
        const btn = document.getElementById('vault-confirm-import-btn');
        const fileEl = document.getElementById('vault-csv-file');
        if (statusEl) statusEl.textContent = 'No file selected yet';
        if (btn) btn.disabled = true;
        if (fileEl) fileEl.value = '';
        const modal = document.getElementById('vault-import-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    };

    window.closeVaultImportModal = function() {
        const modal = document.getElementById('vault-import-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.handleVaultCsvFileSelect = function(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const matrix = parseCsvMatrix(e.target.result || '');
            if (matrix.length < 2) return;
            const headers = matrix[0].map(h => h.trim().toLowerCase());
            const idxName = headers.indexOf('name');
            const idxUrl = headers.indexOf('url');
            const idxUser = headers.indexOf('username');
            const idxPwd = headers.indexOf('password');
            const idxExtra = headers.indexOf('extra') !== -1 ? headers.indexOf('extra') : headers.indexOf('note');
            const idxGroup = headers.indexOf('grouping');

            const parsed = [];
            for (let i = 1; i < matrix.length; i++) {
                const r = matrix[i];
                if (!r || r.length < 3) continue;
                const url = idxUrl !== -1 ? (r[idxUrl] || '').trim() : '';
                const name = (idxName !== -1 ? (r[idxName] || '').trim() : '') || extractDomainSafe(url) || 'Imported Login';
                const username = idxUser !== -1 ? (r[idxUser] || '').trim() : '';
                const password = idxPwd !== -1 ? (r[idxPwd] || '') : '';
                const notes = idxExtra !== -1 ? (r[idxExtra] || '').trim() : '';
                const grouping = idxGroup !== -1 ? (r[idxGroup] || '').trim() : '';

                if (!password && !username) continue;
                parsed.push({
                    name,
                    url,
                    domain: extractDomainSafe(url),
                    username,
                    password,
                    notes,
                    category: grouping || inferCredentialCategory(name, url)
                });
            }

            pendingCsvParsedRecords = parsed;
            const statusEl = document.getElementById('vault-import-status');
            const btn = document.getElementById('vault-confirm-import-btn');
            if (statusEl) statusEl.innerHTML = `<span class="text-emerald-400 font-semibold">Ready to encrypt &amp; import ${parsed.length} credentials from ${escapeHtml(file.name)}</span>`;
            if (btn) btn.disabled = (parsed.length === 0);
        };
        reader.readAsText(file);
    };

    window.confirmVaultCsvImport = async function() {
        if (!vaultMasterPassword || pendingCsvParsedRecords.length === 0) return;
        const btn = document.getElementById('vault-confirm-import-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Encrypting...';
        }

        const existingKeys = new Set(unlockedCredentials.map(c => `${c.domain}|${c.username}`));
        const blobs = getEncryptedVaultBlobs();
        let importedCount = 0;

        for (const rec of pendingCsvParsedRecords) {
            const key = `${rec.domain}|${rec.username}`;
            if (existingKeys.has(key)) continue;
            existingKeys.add(key);

            const credObj = {
                id: 'cred_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
                name: rec.name,
                url: rec.url,
                domain: rec.domain,
                username: rec.username,
                password: rec.password,
                category: rec.category,
                notes: rec.notes,
                updatedAt: new Date().toISOString()
            };
            const blob = await encryptVaultPayload(credObj, vaultMasterPassword);
            blobs.unshift(blob);
            unlockedCredentials.unshift(credObj);
            importedCount++;
        }

        saveEncryptedVaultBlobs(blobs);
        pendingCsvParsedRecords = [];
        closeVaultImportModal();
        renderVaultCredentials();
        showPortalToast(`Encrypted & imported ${importedCount} credentials (AES-256-GCM)`);
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Encrypt & Import';
        }
    };

    // Export strictly encrypted blobs for SQLite content.db sync
    window.exportEncryptedVaultForSQLite = function() {
        const blobs = getEncryptedVaultBlobs();
        const payload = {
            _format: "portal_passwords_aes256gcm_v1",
            _exported_at: new Date().toISOString(),
            count: blobs.length,
            records: blobs
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `portal_vault_sync.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showPortalToast(`Downloaded ${blobs.length} encrypted blobs (run import_vault_to_db.py to save to content.db)`);
    };
"""

# Hook initPasswordVault() inside DOMContentLoaded and renderAll()
assert "initRememberDragAndDrop();" in js
js = js.replace(
    "        initRememberDragAndDrop();\n        if (isAuthenticated()) {",
    "        initRememberDragAndDrop();\n        initPasswordVault();\n        if (isAuthenticated()) {",
    1
)

# Insert vault_module right before the closing })();
assert js.rstrip().endswith("})();")
idx = js.rfind("})();")
js = js[:idx] + vault_module + "\n})();\n"

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("[OK] Implemented Zero-Knowledge Password Vault engine in js/portal.js")
