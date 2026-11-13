import re
import urllib.parse

def generate_bookmark_description(title, url, domain, subfolder, category):
    """
    Synthesize an intelligent, rich semantic paragraph description for any bookmark URL.
    Covers domain knowledge, service capabilities, synonyms, practical utility, and category taxonomy.
    """
    t = (title or '').strip()
    u = (url or '').strip()
    d = (domain or '').lower().replace('www.', '')
    sub = (subfolder or '').strip()
    cat = (category or '').strip()

    # Parse URL path
    parsed = urllib.parse.urlparse(u)
    path_parts = [p for p in parsed.path.split('/') if p and not p.endswith(('.html', '.php', '.aspx'))]
    
    # 1. Domain & Known Service Rules
    desc = []

    # Financial / Banking / Investment / Retirement
    if any(k in d for k in ['chase.com', 'capitalone.com', 'bankofamerica.com', 'alahlynet.com.eg', 'fidelity.com', 'robinhood.com', 'tiaa.org', 'upstart.com', 'earnin.com', 'moneymanagement.org', 'myretirementmanager.com', 'empower-retirement.com']) or \
       'taxact' in d or 'link.com' in d or 'paymentworks' in d or (d == 'texas.gov' and 'trs' in u.lower()):
        if 'chase' in d:
            return ("Chase Online Banking and financial services portal. Access checking, savings, credit cards, "
                    "mortgages, auto loans, commercial banking, account balances, monthly statements, wire transfers, "
                    "bill pay, and personal wealth management.")
        if 'capitalone' in d:
            return ("Capital One financial institution and online banking platform. Manage credit cards, rewards, "
                    "checking and high-yield savings accounts, auto loans, credit monitoring, financial statements, and payments.")
        if 'bankofamerica' in d:
            return ("Bank of America online and mobile banking portal. Secure access to personal and commercial bank accounts, "
                    "credit cards, debit transactions, mortgage loans, investing via Merrill, balance inquiries, and financial planning.")
        if 'alahlynet' in d or 'national bank of egypt' in t.lower():
            return ("National Bank of Egypt (Al Ahly Net / NBE) official online banking service. Manage Egyptian Pound and foreign "
                    "currency accounts, certificates of deposit (CDs), investment funds, wire transfers, currency exchange rates, "
                    "and international remittances.")
        if 'earnin' in d:
            return ("Earnin financial wellness app and cash advance service. Access earned wages prior to payday, track hours worked, "
                    "manage daily cash flow, balance protection alerts, and avoid overdraft bank fees.")
        if 'moneymanagement' in d or 'mmi' in t.lower():
            return ("Money Management International (MMI) non-profit financial counseling, debt management plans (DMP), "
                    "budget guidance, credit score education, student loan counseling, and mortgage relief.")
        if 'upstart' in d:
            return ("Upstart artificial intelligence lending platform. Personal loans, debt consolidation, refinancing, "
                    "credit evaluations, loan repayment schedules, and automated financial risk assessments.")
        if 'tiaa.org' in d:
            return ("TIAA (Teachers Insurance and Annuity Association) retirement, financial planning, and investment services. "
                    "Manage 403(b) retirement funds, mutual funds, annuities, retirement accounts, portfolio asset allocation, and university pension benefits.")
        if 'texas.gov' in d and 'trs' in u.lower():
            return ("Teacher Retirement System of Texas (TRS) member self-service portal. Manage Texas public educator pension plans, "
                    "retirement eligibility calculators, survivor benefits, healthcare coverage, and service credit statements.")
        if 'myretirementmanager' in d:
            return ("Retirement Manager (Corebridge / VALIC) participant portal. Plan administration, retirement contributions, "
                    "account balance monitoring, investment elections, and pension distributions.")
        if 'fidelity' in d:
            return ("Fidelity Investments brokerage and financial services portal. Trade stocks, ETFs, mutual funds, manage 401(k) "
                    "and IRA retirement plans, financial advisory, market research, and wealth asset management.")
        if 'empower-retirement' in d or 'texa$aver' in t.lower():
            return ("Texa$aver 401(k) and 457 retirement savings program administered by Empower Retirement. Manage Texas state employee "
                    "deferred compensation, voluntary payroll deductions, portfolio growth, and retirement distribution options.")
        if 'robinhood' in d:
            return ("Robinhood financial trading application. Commission-free stock trading, exchange-traded funds (ETFs), options, "
                    "cryptocurrencies, high-yield cash sweep interest, and mobile portfolio management.")
        if 'taxact' in d:
            return ("TaxAct online income tax preparation and e-filing software. Prepare federal and state tax returns, "
                    "deductions, tax credits, W-2 and 1099 filing, and IRS tax refunds.")
        if 'paymentworks' in d:
            return ("PaymentWorks automated digital supplier onboarding and vendor management network. Vendor identity verification, "
                    "secure ACH bank routing details, invoice processing, and business compliance.")
        if 'link.com' in d:
            return ("Link by Stripe one-click checkout and payment wallet. Saved credit card details, billing addresses, "
                    "purchase transaction history, and digital receipts.")

    # Email & Messaging
    if '@' in t or any(k in d for k in ['mail.google', 'outlook.live', 'outlook.office', 'mail.yahoo', 'mail.proton']):
        return (f"Personal and professional email communications inbox for {t}. Read, compose, and manage messages, "
                f"calendar invites, attachments, threads, mail filters, and directory correspondence on {d}.")

    # Code & Development
    if 'github.com' in d:
        return (f"GitHub software development platform repository for {t}. Version control, git commits, source code branches, "
                f"issues, pull requests, automated CI/CD workflows, open-source libraries, and collaborative programming.")
    if 'gitlab.com' in d or 'bitbucket.org' in d:
        return (f"Source code version control repository and DevOps pipeline on {d} for {t}. Git hosting, continuous integration, and deployments.")
    if 'stackoverflow.com' in d:
        return (f"Stack Overflow programming and developer knowledge base. Technical Q&A, debugging solutions, software algorithms, and language syntax.")

    # Academic Grants & Government Funding
    if any(k in d for k in ['research.gov', 'grants.gov', 'era.nih.gov', 'fastlane.nsf.gov', 'nsf.gov']):
        return (f"Federal research grant administration and scientific funding portal on {d} for '{t}'. Manage project proposals, "
                f"peer review scoring, budget allocations, principal investigator (PI) compliance, award notices, and progress reporting.")

    # Academic & Scientific Literature
    if any(k in d for k in ['arxiv.org', 'biorxiv.org', 'medrxiv.org', 'ncbi.nlm.nih.gov', 'pubmed', 'nature.com', 'science.org', 'cell.com', 'sciencedirect.com', 'ieeexplore.ieee.org', 'frontiersin.org', 'springer.com', 'wiley.com']):
        return (f"Peer-reviewed scientific literature and academic research publications on {d} covering '{t}'. "
                f"Full-text research papers, methodologies, empirical findings, preprints, citations, abstracts, and scholarly peer reviews.")

    # AI & Machine Learning Platforms
    if any(k in d for k in ['huggingface.co', 'kaggle.com', 'wandb.ai', 'openai.com', 'anthropic.com', 'deepmind.google']):
        return (f"Artificial intelligence and machine learning platform on {d} for {t}. Pretrained neural models, deep learning datasets, "
                f"benchmarks, generative AI, LLM prompting, computational experiments, and fine-tuning pipelines.")

    # Higher Education, Teaching & University Portals
    if 'twu.edu' in d:
        return (f"Texas Woman's University (TWU) official academic portal for {t}. Faculty administration, student records, "
                f"department of computer science, university intranet, academic schedule, and campus resources.")
    if 'instructure.com' in d or 'canvas' in d:
        return (f"Canvas Learning Management System (LMS) for course administration: {t}. Syllabi, lecture modules, student grading, "
                f"assignment submissions, announcements, and educational discussions.")

    # Google Workspace
    if 'drive.google.com' in d:
        return (f"Google Drive cloud storage and document repository: {t}. Shared files, spreadsheets, presentations, "
                f"collaborative folders, and cloud backups.")
    if 'calendar.google.com' in d:
        return (f"Google Calendar scheduling and time management tool: {t}. Manage meetings, appointments, tasks, "
                f"deadlines, notifications, and agenda tracking.")

    # Default Synthesis for General Web
    sub_text = f" filed under {sub}" if sub and sub != d and sub != 'General' else ""
    cat_text = f" in {cat}" if cat and cat != 'Bookmarks' else ""
    return (f"Online web resource and service for '{t}' hosted at {d}{sub_text}{cat_text}. "
            f"Provides relevant digital tools, reference documentation, interactive portal features, and verified web destination access.")
