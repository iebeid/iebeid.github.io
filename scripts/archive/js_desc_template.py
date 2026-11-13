import re

def generate_bookmark_description(name, domain, subfolder, category, url):
    t = (name or '').strip()
    u = (url or '').strip()
    d = (domain or '').lower().replace('www.', '')
    sub = (subfolder or '').strip()
    cat = (category or '').strip()
    tl = t.lower()
    ul = u.lower()

    if any(k in d for k in ['chase.com', 'capitalone.com', 'bankofamerica.com', 'alahlynet.com.eg', 'fidelity.com', 'robinhood.com', 'tiaa.org', 'upstart.com', 'earnin.com', 'moneymanagement.org', 'myretirementmanager.com', 'empower-retirement.com']) or \
       'taxact' in d or 'link.com' in d or 'paymentworks' in d or (d == 'texas.gov' and 'trs' in ul) or ('citi' in tl and 'citiprogram' not in d):
        if 'chase' in d:
            return ("Chase Online Banking and financial services portal. Access checking, savings, credit cards, "
                    "mortgages, auto loans, commercial banking, account balances, monthly statements, wire transfers, "
                    "bill pay, and personal wealth management.")
        if 'capitalone' in d or 'capitol one' in tl:
            return ("Capital One financial institution and online banking platform. Manage credit cards, rewards, "
                    "checking and high-yield savings accounts, auto loans, credit monitoring, financial statements, and payments.")
        if 'bankofamerica' in d:
            return ("Bank of America online and mobile banking portal. Secure access to personal and commercial bank accounts, "
                    "credit cards, debit transactions, mortgage loans, investing via Merrill, balance inquiries, and financial planning.")
        if 'alahlynet' in d or 'national bank of egypt' in tl:
            return ("National Bank of Egypt (Al Ahly Net / NBE) official online banking service. Manage Egyptian Pound and foreign "
                    "currency accounts, certificates of deposit (CDs), investment funds, wire transfers, currency exchange rates, "
                    "and international remittances.")
        if 'earnin' in d:
            return ("Earnin financial wellness app and cash advance service. Access earned wages prior to payday, track hours worked, "
                    "manage daily cash flow, balance protection alerts, and avoid overdraft bank fees.")
        if 'moneymanagement' in d or 'mmi' in tl:
            return ("Money Management International (MMI) non-profit financial counseling, debt management plans (DMP), "
                    "budget guidance, credit score education, student loan counseling, and mortgage relief.")
        if 'upstart' in d:
            return ("Upstart artificial intelligence lending platform. Personal loans, debt consolidation, refinancing, "
                    "credit evaluations, loan repayment schedules, and automated financial risk assessments.")
        if 'tiaa.org' in d:
            return ("TIAA (Teachers Insurance and Annuity Association) retirement, financial planning, and investment services. "
                    "Manage 403(b) retirement funds, mutual funds, annuities, retirement accounts, portfolio asset allocation, and university pension benefits.")
        if 'texas.gov' in d and 'trs' in ul:
            return ("Teacher Retirement System of Texas (TRS) member self-service portal. Manage Texas public educator pension plans, "
                    "financial retirement eligibility calculators, survivor benefits, healthcare coverage, and service credit statements.")
        if 'myretirementmanager' in d:
            return ("Retirement Manager (Corebridge / VALIC) participant portal. Financial planning and plan administration, retirement contributions, "
                    "account balance monitoring, investment elections, and pension distributions.")
        if 'fidelity' in d:
            return ("Fidelity Investments brokerage and financial services portal. Trade stocks, ETFs, mutual funds, manage 401(k) "
                    "and IRA retirement plans, financial advisory, market research, and wealth asset management.")
        if 'empower-retirement' in d or 'texa$aver' in tl:
            return ("Texa$aver 401(k) and 457 retirement savings program administered by Empower Retirement. Manage Texas state employee "
                    "deferred compensation, voluntary payroll deductions, financial portfolio growth, and retirement distribution options.")
        if 'robinhood' in d:
            return ("Robinhood financial trading application. Commission-free stock trading, exchange-traded funds (ETFs), options, "
                    "cryptocurrencies, high-yield cash sweep interest, and mobile portfolio management.")
        if 'taxact' in d:
            return ("TaxAct online income tax preparation and e-filing software. Financial deductions, prepare federal and state tax returns, "
                    "tax credits, W-2 and 1099 filing, and IRS tax refunds.")
        if 'paymentworks' in d:
            return ("PaymentWorks automated digital supplier onboarding and vendor management network. Vendor identity verification, "
                    "secure ACH bank routing details, invoice processing, and business compliance.")
        if 'link.com' in d:
            return ("Link by Stripe one-click checkout and payment wallet. Saved credit card details, financial transactions, billing addresses, "
                    "purchase transaction history, and digital receipts.")

    # Email
    if '@' in t or any(k in d for k in ['mail.google', 'outlook.live', 'outlook.office', 'mail.yahoo', 'mail.proton']):
        return (f"Personal and professional email communications inbox for {t}. Read, compose, and manage messages, "
                f"calendar invites, attachments, threads, mail filters, and directory correspondence on {d}.")

    # Code
    if 'github.com' in d:
        return (f"GitHub software development platform repository for {t}. Version control, git commits, source code branches, "
                f"issues, pull requests, automated CI/CD workflows, open-source libraries, and collaborative programming.")
    if 'gitlab.com' in d or 'bitbucket.org' in d:
        return (f"Source code version control repository and DevOps pipeline on {d} for {t}. Git hosting, continuous integration, and deployments.")
    if 'stackoverflow.com' in d:
        return (f"Stack Overflow programming and developer knowledge base. Technical Q&A, debugging solutions, software algorithms, and language syntax.")

    # Grants
    if any(k in d for k in ['research.gov', 'grants.gov', 'era.nih.gov', 'fastlane.nsf.gov', 'nsf.gov']):
        return (f"Federal research grant administration and scientific funding portal on {d} for '{t}'. Manage project proposals, "
                f"peer review scoring, budget allocations, principal investigator (PI) compliance, award notices, and progress reporting.")

    # Literature
    if any(k in d for k in ['arxiv.org', 'biorxiv.org', 'medrxiv.org', 'ncbi.nlm.nih.gov', 'pubmed', 'nature.com', 'science.org', 'cell.com', 'sciencedirect.com', 'ieeexplore.ieee.org', 'frontiersin.org', 'springer.com', 'wiley.com']):
        return (f"Peer-reviewed scientific literature and academic research publications on {d} covering '{t}'. "
                f"Full-text research papers, methodologies, empirical findings, preprints, citations, abstracts, and scholarly peer reviews.")

    # AI / ML
    if any(k in d for k in ['huggingface.co', 'kaggle.com', 'wandb.ai', 'openai.com', 'anthropic.com', 'deepmind.google', 'caiml.utdallas.edu']):
        return (f"Artificial intelligence and machine learning platform on {d} for {t}. Pretrained neural models, deep learning datasets, "
                f"benchmarks, generative AI, LLM prompting, computational experiments, and fine-tuning pipelines.")

    # Higher Ed
    if 'twu.edu' in d:
        return (f"Texas Woman's University (TWU) official academic portal for {t}. Faculty administration, student records, "
                f"department of computer science, university intranet, academic schedule, and campus resources.")
    if 'instructure.com' in d or 'canvas' in d:
        return (f"Canvas Learning Management System (LMS) for course administration: {t}. Syllabi, lecture modules, student grading, "
                f"assignment submissions, announcements, and educational discussions.")

    # Cloud
    if 'cloudbank.org' in d:
        return (f"CloudBank NSF-funded multicloud access portal for academic research. Manage cloud computing credits across AWS, Google Cloud, and Microsoft Azure for high-performance computing.")
    if 'access-ci.org' in d:
        return (f"ACCESS CI (Advanced Cyberinfrastructure Coordination Ecosystem) portal. National high-performance computing allocations, supercomputer resources, and cyberinfrastructure research.")

    # Google Workspace
    if 'drive.google.com' in d:
        return (f"Google Drive cloud storage and document repository: {t}. Shared files, spreadsheets, presentations, "
                f"collaborative folders, and cloud backups.")
    if 'calendar.google.com' in d:
        return (f"Google Calendar scheduling and time management tool: {t}. Manage meetings, appointments, tasks, "
                f"deadlines, notifications, and agenda tracking.")

    # General fallback
    sub_text = f" in {sub}" if sub and sub != d and sub != 'General' else ""
    return (f"Verified web application and executive bookmark for '{t}' hosted on {d}{sub_text}. "
            f"Provides direct navigation, authenticated access, digital documentation, and operational tooling.")
