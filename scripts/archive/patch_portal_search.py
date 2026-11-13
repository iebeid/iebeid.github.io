# Complete upgrade script for js/portal.js:
# 1. Adds generateBookmarkDescription(name, domain, subfolder, category, url)
# 2. Updates generateSemanticTags to include full banking/financial, government, and tax dictionaries
# 3. Updates getAllBookmarks() to ensure bm.description is populated (from database or dynamic generator)
# 4. Updates calculateSimilarityAndRelevance to perform full paragraph description search & scoring
# 5. Displays description snippet in search result cards

with open('js/portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Insertion of generateBookmarkDescription right before generateSemanticTags
desc_func = """    function generateBookmarkDescription(name, domain, subfolder, category, url) {
        const t = (name || '').trim();
        const u = (url || '').trim();
        const d = (domain || '').toLowerCase().replace(/^www\\./, '');
        const sub = (subfolder || '').trim();
        const cat = (category || '').trim();
        const tl = t.toLowerCase();
        const ul = u.toLowerCase();

        // 1. Financial / Banking / Investment / Retirement
        if (['chase.com', 'capitalone.com', 'bankofamerica.com', 'alahlynet.com.eg', 'fidelity.com', 'robinhood.com', 'tiaa.org', 'upstart.com', 'earnin.com', 'moneymanagement.org', 'myretirementmanager.com', 'empower-retirement.com'].some(k => d.includes(k)) ||
            d.includes('taxact') || d.includes('link.com') || d.includes('paymentworks') || (d === 'texas.gov' && ul.includes('trs')) || (tl.includes('citi') && !d.includes('citiprogram'))) {
            if (d.includes('chase')) {
                return "Chase Online Banking and financial services portal. Access checking, savings, credit cards, mortgages, auto loans, commercial banking, account balances, monthly statements, wire transfers, bill pay, and personal wealth management.";
            }
            if (d.includes('capitalone') || tl.includes('capitol one')) {
                return "Capital One financial institution and online banking platform. Manage credit cards, rewards, checking and high-yield savings accounts, auto loans, credit monitoring, financial statements, and payments.";
            }
            if (d.includes('bankofamerica')) {
                return "Bank of America online and mobile banking portal. Secure access to personal and commercial bank accounts, credit cards, debit transactions, mortgage loans, investing via Merrill, balance inquiries, and financial planning.";
            }
            if (d.includes('alahlynet') || tl.includes('national bank of egypt')) {
                return "National Bank of Egypt (Al Ahly Net / NBE) official online banking service. Manage Egyptian Pound and foreign currency accounts, certificates of deposit (CDs), investment funds, wire transfers, currency exchange rates, and international remittances.";
            }
            if (d.includes('earnin')) {
                return "Earnin financial wellness app and cash advance service. Access earned wages prior to payday, track hours worked, manage daily cash flow, balance protection alerts, and avoid overdraft bank fees.";
            }
            if (d.includes('moneymanagement') || tl.includes('mmi')) {
                return "Money Management International (MMI) non-profit financial counseling, debt management plans (DMP), budget guidance, credit score education, student loan counseling, and mortgage relief.";
            }
            if (d.includes('upstart')) {
                return "Upstart artificial intelligence lending platform. Personal loans, debt consolidation, refinancing, credit evaluations, loan repayment schedules, and automated financial risk assessments.";
            }
            if (d.includes('tiaa.org')) {
                return "TIAA (Teachers Insurance and Annuity Association) retirement, financial planning, and investment services. Manage 403(b) retirement funds, mutual funds, annuities, retirement accounts, portfolio asset allocation, and university pension benefits.";
            }
            if (d.includes('texas.gov') && ul.includes('trs')) {
                return "Teacher Retirement System of Texas (TRS) member self-service portal. Manage Texas public educator pension plans, financial retirement eligibility calculators, survivor benefits, healthcare coverage, and service credit statements.";
            }
            if (d.includes('myretirementmanager')) {
                return "Retirement Manager (Corebridge / VALIC) participant portal. Financial planning and plan administration, retirement contributions, account balance monitoring, investment elections, and pension distributions.";
            }
            if (d.includes('fidelity')) {
                return "Fidelity Investments brokerage and financial services portal. Trade stocks, ETFs, mutual funds, manage 401(k) and IRA retirement plans, financial advisory, market research, and wealth asset management.";
            }
            if (d.includes('empower-retirement') || tl.includes('texa$aver')) {
                return "Texa$aver 401(k) and 457 retirement savings program administered by Empower Retirement. Manage Texas state employee deferred compensation, voluntary payroll deductions, financial portfolio growth, and retirement distribution options.";
            }
            if (d.includes('robinhood')) {
                return "Robinhood financial trading application. Commission-free stock trading, exchange-traded funds (ETFs), options, cryptocurrencies, high-yield cash sweep interest, and mobile portfolio management.";
            }
            if (d.includes('taxact')) {
                return "TaxAct online income tax preparation and e-filing software. Financial deductions, prepare federal and state tax returns, tax credits, W-2 and 1099 filing, and IRS tax refunds.";
            }
            if (d.includes('paymentworks')) {
                return "PaymentWorks automated digital supplier onboarding and vendor management network. Vendor identity verification, secure ACH bank routing details, invoice processing, and business compliance.";
            }
            if (d.includes('link.com')) {
                return "Link by Stripe one-click checkout and payment wallet. Saved credit card details, financial transactions, billing addresses, purchase transaction history, and digital receipts.";
            }
        }

        // 2. Email & Communications
        if (tl.includes('@') || ['mail.google', 'outlook.live', 'outlook.office', 'mail.yahoo', 'mail.proton'].some(k => d.includes(k))) {
            return `Personal and professional email communications inbox for ${t}. Read, compose, and manage messages, calendar invites, attachments, threads, mail filters, and directory correspondence on ${d}.`;
        }

        // 3. Code, Software & Development
        if (d.includes('github.com')) {
            return `GitHub software development platform repository for ${t}. Version control, git commits, source code branches, issues, pull requests, automated CI/CD workflows, open-source libraries, and collaborative programming.`;
        }
        if (d.includes('gitlab.com') || d.includes('bitbucket.org')) {
            return `Source code version control repository and DevOps pipeline on ${d} for ${t}. Git hosting, continuous integration, and deployments.`;
        }
        if (d.includes('stackoverflow.com')) {
            return `Stack Overflow programming and developer knowledge base. Technical Q&A, debugging solutions, software algorithms, and language syntax.`;
        }

        // 4. Academic Grants & Government Funding
        if (['research.gov', 'grants.gov', 'era.nih.gov', 'fastlane.nsf.gov', 'nsf.gov'].some(k => d.includes(k))) {
            return `Federal research grant administration and scientific funding portal on ${d} for '${t}'. Manage project proposals, peer review scoring, budget allocations, principal investigator (PI) compliance, award notices, and progress reporting.`;
        }

        // 5. Scientific Literature, Journals & Preprints
        if (['arxiv.org', 'biorxiv.org', 'medrxiv.org', 'ncbi.nlm.nih.gov', 'pubmed', 'nature.com', 'science.org', 'cell.com', 'sciencedirect.com', 'ieeexplore.ieee.org', 'frontiersin.org', 'springer.com', 'wiley.com'].some(k => d.includes(k))) {
            return `Peer-reviewed scientific literature and academic research publications on ${d} covering '${t}'. Full-text research papers, methodologies, empirical findings, preprints, citations, abstracts, and scholarly peer reviews.`;
        }

        // 6. AI, Machine Learning & Data Science
        if (['huggingface.co', 'kaggle.com', 'wandb.ai', 'openai.com', 'anthropic.com', 'deepmind.google', 'caiml.utdallas.edu'].some(k => d.includes(k))) {
            return `Artificial intelligence and machine learning platform on ${d} for ${t}. Pretrained neural models, deep learning datasets, benchmarks, generative AI, LLM prompting, computational experiments, and fine-tuning pipelines.`;
        }

        // 7. Higher Education & University Administration
        if (d.includes('twu.edu')) {
            return `Texas Woman's University (TWU) official academic portal for ${t}. Faculty administration, student records, department of computer science, university intranet, academic schedule, and campus resources.`;
        }
        if (d.includes('instructure.com') || d.includes('canvas')) {
            return `Canvas Learning Management System (LMS) for course administration: ${t}. Syllabi, lecture modules, student grading, assignment submissions, announcements, and educational discussions.`;
        }

        // 8. Cloud & Compute
        if (d.includes('cloudbank.org')) {
            return `CloudBank NSF-funded multicloud access portal for academic research. Manage cloud computing credits across AWS, Google Cloud, and Microsoft Azure for high-performance computing.`;
        }
        if (d.includes('access-ci.org')) {
            return `ACCESS CI (Advanced Cyberinfrastructure Coordination Ecosystem) portal. National high-performance computing allocations, supercomputer resources, and cyberinfrastructure research.`;
        }

        // 9. Google Workspace
        if (d.includes('drive.google.com')) {
            return `Google Drive cloud storage and document repository: ${t}. Shared files, spreadsheets, presentations, collaborative folders, and cloud backups.`;
        }
        if (d.includes('calendar.google.com')) {
            return `Google Calendar scheduling and time management tool: ${t}. Manage meetings, appointments, tasks, deadlines, notifications, and agenda tracking.`;
        }

        // Default Fallback
        const subText = (sub && sub !== d && sub !== 'General') ? ` in ${sub}` : '';
        return `Verified web application and executive bookmark for '${t}' hosted on ${d}${subText}. Provides direct navigation, authenticated access, digital documentation, and operational tooling.`;
    }

"""

target_tag_func = "    function generateSemanticTags(name, domain, subfolder, category) {"
assert target_tag_func in code, "target_tag_func not found"
code = code.replace(target_tag_func, desc_func + target_tag_func, 1)

# 2. Enhance generateSemanticTags with banking/financial tags
banking_tags_block = """            } else if (['chase', 'capitalone', 'bankofamerica', 'alahlynet', 'fidelity', 'robinhood', 'tiaa', 'upstart', 'earnin', 'moneymanagement', 'myretirementmanager', 'empower-retirement'].some(k => d.includes(k)) || ['bank', 'chase', 'capital one', 'fidelity', 'robinhood', 'earnin', 'upstart', 'retirement', 'tiaa', 'trs', 'tax'].some(k => rawName.includes(k))) {
                ['finance', 'financial', 'bank', 'banking', 'money', 'accounts', 'statements', 'funds', 'investment'].forEach(t => tokens.add(t));
"""
target_linkedin = """            } else if (d.includes('linkedin')) {
                ['linkedin', 'career', 'networking', 'professional'].forEach(t => tokens.add(t));
            }"""
assert target_linkedin in code, "target_linkedin not found"
code = code.replace(target_linkedin, target_linkedin + "\n" + banking_tags_block, 1)

# 3. Ensure getAllBookmarks attaches bm.description
old_get_all = """        combined = combined.map(bm => {
            if (dynamicTags[bm.id]) {
                bm.ai_tags = dynamicTags[bm.id];
            } else if (!bm.ai_tags) {
                bm.ai_tags = generateSemanticTags(bm.name, bm.domain, bm.subfolder, bm.category);
            }
            return bm;
        });"""

new_get_all = """        combined = combined.map(bm => {
            if (dynamicTags[bm.id]) {
                bm.ai_tags = dynamicTags[bm.id];
            } else if (!bm.ai_tags) {
                bm.ai_tags = generateSemanticTags(bm.name, bm.domain, bm.subfolder, bm.category);
            }
            if (!bm.description) {
                bm.description = generateBookmarkDescription(bm.name, bm.domain, bm.subfolder, bm.category, bm.url);
            }
            return bm;
        });"""
assert old_get_all in code, "old_get_all not found"
code = code.replace(old_get_all, new_get_all, 1)

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("[OK] Step 1-3 applied to js/portal.js")
