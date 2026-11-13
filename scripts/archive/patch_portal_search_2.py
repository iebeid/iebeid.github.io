with open('js/portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update calculateSimilarityAndRelevance to include bm.description
old_calc_vars = """        const q = query.toLowerCase().trim();
        const tokens = q.split(/\\s+/).filter(Boolean);
        const name = (bm.name || '').toLowerCase();
        const domain = (bm.domain || '').toLowerCase();
        const tags = (bm.ai_tags || '').toLowerCase();
        const path = (bm.path || '').toLowerCase();
        const url = (bm.url || '').toLowerCase();
        const cleanUrl = url.split('?')[0].split('#')[0];"""

new_calc_vars = """        const q = query.toLowerCase().trim();
        const tokens = q.split(/\\s+/).filter(Boolean);
        const name = (bm.name || '').toLowerCase();
        const domain = (bm.domain || '').toLowerCase();
        const tags = (bm.ai_tags || '').toLowerCase();
        const path = (bm.path || '').toLowerCase();
        const url = (bm.url || '').toLowerCase();
        const cleanUrl = url.split('?')[0].split('#')[0];
        const desc = (bm.description || '').toLowerCase();"""

assert old_calc_vars in code, "old_calc_vars not found"
code = code.replace(old_calc_vars, new_calc_vars, 1)

# 2. Add financial intent mapping to INTENT_MAP
old_intent_map = """            'code': ['code', 'github', 'git', 'repo', 'repository', 'software', 'programming', 'python']
        };"""

new_intent_map = """            'code': ['code', 'github', 'git', 'repo', 'repository', 'software', 'programming', 'python'],
            'financial': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'finance': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'finances': ['financial', 'finance', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment', 'retirement', 'taxes', 'credit'],
            'bank': ['bank', 'banking', 'checking', 'savings', 'accounts', 'statements', 'chase', 'capitalone', 'bankofamerica', 'national bank of egypt', 'financial', 'finance', 'money'],
            'banking': ['bank', 'banking', 'checking', 'savings', 'accounts', 'statements', 'chase', 'capitalone', 'bankofamerica', 'financial', 'finance', 'money'],
            'money': ['money', 'finance', 'financial', 'bank', 'banking', 'accounts', 'earnin', 'upstart', 'investment', 'funds'],
            'investment': ['investment', 'investing', 'stocks', 'portfolio', 'fidelity', 'robinhood', 'tiaa', 'retirement', 'etfs', 'financial', 'funds'],
            'investments': ['investment', 'investing', 'stocks', 'portfolio', 'fidelity', 'robinhood', 'tiaa', 'retirement', 'etfs', 'financial', 'funds'],
            'retirement': ['retirement', 'pension', '401k', '403b', 'tiaa', 'trs', 'fidelity', 'texasaver', 'valic', 'corebridge', 'financial', 'investing'],
            'tax': ['tax', 'taxes', 'taxact', 'irs', 'refund', 'deductions', 'financial', '1099', 'w2'],
            'taxes': ['tax', 'taxes', 'taxact', 'irs', 'refund', 'deductions', 'financial', '1099', 'w2']
        };"""

assert old_intent_map in code, "old_intent_map not found"
code = code.replace(old_intent_map, new_intent_map, 1)

# 3. Add Description Searching block in calculateSimilarityAndRelevance right after step 3 (tags)
old_tags_block_end = """        // 4. Folder / Path / Category
        if (path.includes(q)) {
            score += 120;
            reasons.push(`Folder: ${bm.subfolder || bm.category}`);
        }"""

new_tags_and_desc_block = """        // 3.5 Full Semantic Paragraph Description Search
        if (desc) {
            if (new RegExp(`\\\\b${escapeRegExp(q)}\\\\b`, 'i').test(desc)) {
                score += 380;
                if (!reasons.some(r => r.includes("Description") || r.includes("Email Account"))) {
                    reasons.push(`Semantic Description Match`);
                }
            } else if (desc.includes(q)) {
                score += 220;
                if (!reasons.some(r => r.includes("Description") || r.includes("Email Account"))) {
                    reasons.push(`Description Match`);
                }
            }
        }

        // 4. Folder / Path / Category
        if (path.includes(q)) {
            score += 120;
            reasons.push(`Folder: ${bm.subfolder || bm.category}`);
        }"""

assert old_tags_block_end in code, "old_tags_block_end not found"
code = code.replace(old_tags_block_end, new_tags_and_desc_block, 1)

# 4. Multi-term Token Coverage: also check term in desc
old_multi_term = """                if (name.includes(term)) { score += 70; termMatched = true; }
                if (domain.includes(term)) { score += 40; termMatched = true; }
                if (tags.includes(term)) { score += 40; termMatched = true; }
                if (path.includes(term)) { score += 20; termMatched = true; }"""

new_multi_term = """                if (name.includes(term)) { score += 70; termMatched = true; }
                if (domain.includes(term)) { score += 40; termMatched = true; }
                if (tags.includes(term)) { score += 40; termMatched = true; }
                if (desc.includes(term)) { score += 45; termMatched = true; }
                if (path.includes(term)) { score += 20; termMatched = true; }"""

assert old_multi_term in code, "old_multi_term not found"
code = code.replace(old_multi_term, new_multi_term, 1)

# 5. Render Description in Search Result Cards
old_card_desc = """                        ${bm.path && bm.path !== 'General' ? `<p class="text-[10px] text-slate-500 font-mono truncate"><i class="fas fa-folder-open mr-1"></i>${escapeHtml(bm.path)}</p>` : ''}
                        ${bm.ai_tags ? `<p class="text-[10px] text-slate-500 font-mono truncate mt-1" title="Tags: ${escapeHtml(bm.ai_tags)}"><i class="fas fa-tags mr-1 text-slate-600"></i>${escapeHtml(bm.ai_tags.split(',').slice(0, 5).join(', '))}</p>` : ''}"""

new_card_desc = """                        ${bm.description ? `
                        <p class="text-[11px] text-slate-400 leading-relaxed line-clamp-2 my-1.5" title="${escapeHtml(bm.description)}">
                            ${highlightTokens(escapeHtml(bm.description), query)}
                        </p>` : ''}
                        ${bm.path && bm.path !== 'General' ? `<p class="text-[10px] text-slate-500 font-mono truncate"><i class="fas fa-folder-open mr-1"></i>${escapeHtml(bm.path)}</p>` : ''}
                        ${bm.ai_tags ? `<p class="text-[10px] text-slate-500 font-mono truncate mt-0.5" title="Tags: ${escapeHtml(bm.ai_tags)}"><i class="fas fa-tags mr-1 text-slate-600"></i>${escapeHtml(bm.ai_tags.split(',').slice(0, 5).join(', '))}</p>` : ''}"""

assert old_card_desc in code, "old_card_desc not found"
code = code.replace(old_card_desc, new_card_desc, 1)

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("[OK] Full semantic paragraph search engine implemented in js/portal.js")
