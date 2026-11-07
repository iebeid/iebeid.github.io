import sqlite3
import re

def update_content():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    # 1. Update storefront.catalog
    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'catalog'")
    catalog_row = cursor.fetchone()
    if not catalog_row:
        raise ValueError("storefront.catalog not found")
    
    catalog_html = catalog_row[0]

    # Replace catalog section intro
    old_intro = '<p>Filter production-ready packages by AI &amp; data lifecycle stage. Inspect API usage, open-source repositories, and commercial node/seat licensing.</p>'
    new_intro = '<p>Filter production-ready packages by AI &amp; data lifecycle stage. Our core niche is translating published academic research into robust enterprise libraries and innovating novel frameworks—delivering seamless data engineering and preparation pipelines right before data scientists operate. Built by academically trained graduate engineers adhering to ITIL certification standards.</p>'
    if old_intro in catalog_html:
        catalog_html = catalog_html.replace(old_intro, new_intro)
    else:
        print("Warning: old_intro in catalog not matched directly")

    # Replace DataIntegrationToolkit card
    ditk_pattern = r'<article class="product-card" data-category="DATA_CURATION MODELING_ENGINES">[\s\S]*?DataIntegrationToolkit[\s\S]*?</article>'
    
    new_ditk_card = '''<article class="product-card" data-category="DATA_CURATION MODELING_ENGINES">
<div class="card-header">
<div class="tag-container">
<span class="tech-tag lifecycle">DATA_CURATION &amp; PREPARATION</span>
<span class="tech-tag stack">Python / Medallion Lakehouse / Entity Resolution / ML Feature Prep</span>
</div>
<h3>DataIntegrationToolkit (DITK)</h3>
<p class="description">
    Generalized, high-performance Lakehouse &amp; Data Preparation Engine built to streamline the critical data engineering pipeline right before data scientists operate. Implements a tiered Medallion storage model (Bronze &rarr; Silver &rarr; Gold) with automated ingestion, fuzzy blocking, and scalable Entity Resolution (ER)—transforming disparate, messy data across any domain into deterministic, model-ready feature stores for downstream machine learning and AI modeling.
</p>
</div>
<div class="snippet-container">
<pre><span class="keyword">import</span> dataintegrationtoolkit <span class="keyword">as</span> ditk
lakehouse = ditk.<span class="function">Lakehouse</span>(storage_root=<span class="string">"./lakehouse"</span>)
<span class="comment"># 1. Multi-source ingestion into Bronze tier</span>
bronze = lakehouse.<span class="function">ingest</span>(source=<span class="string">"records_stream.parquet"</span>, tier=<span class="string">"bronze"</span>)
<span class="comment"># 2. Automated blocking, matching &amp; Entity Resolution (Silver tier)</span>
silver = lakehouse.<span class="function">resolve_entities</span>(bronze, blocker=<span class="string">"minhash_lsh"</span>, matcher=<span class="string">"dwm"</span>)
<span class="comment"># 3. Clean feature export right before data science modeling</span>
gold = lakehouse.<span class="function">export_feature_store</span>(silver, format=<span class="string">"parquet"</span>, split=<span class="string">"train_val_test"</span>)</pre>
</div>
<div class="card-footer">
<div class="licensing-box">
<div class="license-type">Dual-Licensed: <br/><strong>AGPLv3</strong> / <strong>Proprietary Commercial</strong></div>
<div class="price-tag">$999<span>/dev seat</span></div>
</div>
<div class="action-row">
<a class="btn btn-oss" href="https://github.com/iebeid/DataIntegrationToolkit" target="_blank"><i class="fab fa-github"></i> Source Code</a>
<button class="btn btn-commercial" onclick="openLicenseModal('DataIntegrationToolkit ($999 / dev seat)')" type="button"><i class="fas fa-key"></i> License Codebase</button>
</div>
</div>
</article>'''

    catalog_html, count = re.subn(ditk_pattern, new_ditk_card, catalog_html, count=1)
    if count == 0:
        raise ValueError("Could not replace DITK card in catalog_html")
    print(f"[OK] Replaced DITK card in catalog (matches: {count})")

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'catalog'", (catalog_html,))

    # 2. Update storefront.section_1 (Hero)
    new_hero_html = '''<section class="hero">
<div>
<div class="hero-badge">
<i class="fas fa-graduation-cap"></i> Academic Innovation &bull; Industrial Software Engineering &bull; ITIL-Certified Standards
</div>
<h1>From Published Research to <span>Production-Grade AI &amp; Compute</span> Systems.</h1>
<p>
    Our core niche is translating peer-reviewed academic publications and cutting-edge research into battle-tested industrial software, alongside innovating novel mathematical frameworks. Built by a dedicated team of professional software engineers and academically trained graduate staff who are ITIL certified (or actively in the certification pipeline as an organizational standard), we provide seamless data engineering and preparation pipelines right before data scientists operate, robust AI lifecycle tools, and ultra-high-performance compute engines.
</p>
<div class="hero-actions">
<a class="btn-primary" href="#catalog">
<i class="fas fa-cubes"></i> Explore Component Catalog
</a>
<div class="install-cmd" onclick="copyInstallCmd(this)" title="Click to copy pip install command">
<span id="pip-text">pip install ailifecyclekit</span>
<i class="far fa-copy" style="color: var(--text-muted); font-size: 0.8rem;"></i>
</div>
</div>
</div>
<div class="code-window" id="code">
<div class="code-header">
<div class="code-dots">
<div class="code-dot red"></div>
<div class="code-dot amber"></div>
<div class="code-dot green"></div>
</div>
<span>example_pipeline.py — Unity Systems SDK</span>
</div>
<pre><code><span class="keyword">import</span> ailifecyclekit <span class="keyword">as</span> alk
<span class="keyword">import</span> dataintegrationtoolkit <span class="keyword">as</span> ditk

<span class="comment"># 1. Seamless data engineering &amp; prep before ML modeling</span>
lakehouse = ditk.<span class="function">Lakehouse</span>(storage_root=<span class="string">"./lakehouse"</span>)
clean_data = lakehouse.<span class="function">prepare_ml_dataset</span>(source=<span class="string">"records.parquet"</span>)

<span class="comment"># 2. Automated dataset curation, drift &amp; lineage tracking</span>
tracker = alk.<span class="function">DriftTracker</span>(baseline_dataset=clean_data)
anomalies = tracker.<span class="function">evaluate_stream</span>(incoming_tensor, threshold=<span class="string">0.85</span>)
tracker.<span class="function">commit_lineage</span>(export_path=<span class="string">"./metadata/"</span>)</code></pre>
</div>
</section>'''
    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'section_1'", (new_hero_html,))
    print("[OK] Updated storefront.section_1 (Hero)")

    # 3. Update storefront.architecture
    new_arch_html = '''<section class="model-section" id="architecture">
<div class="section-heading">
<h2>The Unity Systems Technical &amp; Commercial Architecture</h2>
<p>
    Unity Systems bridges the gap between state-of-the-art published academic research and production-grade software engineering, complemented by original algorithmic frameworks. Every component is developed and maintained by professional software engineers and academically trained graduate researchers who are ITIL certified (or pursuing ITIL certification as a strict hiring requirement)—ensuring industrial reliability, structured lifecycle governance, and enterprise-grade SLAs across three decoupled layers.
</p>
</div>
<div class="pillars-grid">
<div class="pillar-card">
<span class="pillar-step">01 // DATA_PREPARATION &amp; CURATION</span>
<h3>Data Engineering &amp; ML Preparation Pipelines</h3>
<p>
    Eliminating the pre-modeling data bottleneck right before data scientists operate. High-throughput multi-source ingestion, tiered Medallion Lakehouse partitioning (Bronze &rarr; Silver &rarr; Gold), scalable fuzzy Entity Resolution (<strong>DataIntegrationToolkit</strong>), deterministic lineage versioning, and real-time distribution drift tracking (<strong>AILifecycleKit</strong>) generalized for any downstream machine learning or AI modeling task.
</p>
</div>
<div class="pillar-card">
<span class="pillar-step">02 // RESEARCH_IMPLEMENTATIONS</span>
<h3>Implementing Published Research &amp; Novel Frameworks</h3>
<p>
    Our primary niche: translating complex peer-reviewed algorithms from top-tier academic literature into robust, high-performance software libraries alongside innovating original mathematical architectures. Includes high-efficiency neural feature extractors (<strong>ProtGram-DirectGCN</strong>) and unsupervised modularity-based entity resolution engines (<strong>ModER-GraphER</strong>).
</p>
</div>
<div class="pillar-card">
<span class="pillar-step">03 // VISUALIZATION_COMPUTE</span>
<h3>GPU Compute &amp; Immersive Visualization</h3>
<p>
    Ultra-low-latency C++, CUDA, OpenGL, and WebGL rendering engines compiled for multi-million particle simulations (<strong>CudaParticles Engine</strong>), stereoscopic VR raymarching (<strong>RaymarcherVR Engine</strong>), and structural molecular cross-linking inspection (<strong>VisInt-X</strong>).
</p>
</div>
</div>
</section>'''
    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'architecture'", (new_arch_html,))
    print("[OK] Updated storefront.architecture")

    # 4. Update storefront.licensing
    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'licensing'")
    licensing_html = cursor.fetchone()[0]
    
    old_lic_intro = '<p>\n                    We believe in advancing open scientific reproducibility while building a sustainable software engineering business. All Unity Systems modules are dual-licensed based on your deployment and IP requirements.\n                </p>'
    new_lic_intro = '<p>\n    We believe in advancing open scientific reproducibility while building a sustainable software engineering business. Every component translates published scientific research into turnkey industrial code, maintained by professional graduate engineers with ITIL-certified service lifecycle governance. All Unity Systems modules are dual-licensed based on your deployment and IP requirements.\n</p>'
    
    if old_lic_intro in licensing_html:
        licensing_html = licensing_html.replace(old_lic_intro, new_lic_intro)
    else:
        # flexible regex replace
        licensing_html = re.sub(r'<p>\s*We believe in advancing open scientific reproducibility[\s\S]*?</p>', new_lic_intro, licensing_html, count=1)

    old_msa_feat = '<li><span class="icon-check">✓</span> Dedicated architectural integration &amp; custom feature engineering</li>'
    new_msa_feat = '<li><span class="icon-check">✓</span> Dedicated integration by academically trained graduate staff &amp; ITIL-certified engineers</li>'
    if old_msa_feat in licensing_html:
        licensing_html = licensing_html.replace(old_msa_feat, new_msa_feat)

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'licensing'", (licensing_html,))
    print("[OK] Updated storefront.licensing")

    # 5. Update storefront.faq
    new_faq_html = '''<section class="faq-section" id="faq">
<div class="section-header-center">
<h2>Enterprise Licensing &amp; Fulfillment FAQ</h2>
<p>How Unity Systems delivers commercial licenses, private package tokens, and custom engineering agreements.</p>
</div>
<div class="faq-grid">
<div class="faq-item">
<h4><i class="fas fa-graduation-cap" style="color: var(--accent-cyan);"></i> What is Unity Systems' core niche and team standard?</h4>
<p>
    Our defining niche is the academic focus of implementing published, peer-reviewed scientific research into battle-tested industrial software, alongside inventing our own innovative frameworks. Our team consists of professional software engineers and academically trained graduate staff who are ITIL certified (or actively in the ITIL certification pipeline as an organizational hiring standard). This ensures academic innovation is executed with rigorous enterprise change management, SLA reliability, and ITSM governance.
</p>
</div>
<div class="faq-item">
<h4><i class="fas fa-diagram-project" style="color: var(--accent-green);"></i> How does DataIntegrationToolkit (DITK) prepare data for AI/ML?</h4>
<p>
    DITK is engineered to solve the most critical bottleneck in data science: the data engineering and preparation pipeline right before data scientists operate. Operating on a tiered Medallion Lakehouse architecture (Bronze &rarr; Silver &rarr; Gold), it automates raw ingestion, fuzzy blocking, and scalable Entity Resolution (ER). While proven on complex bioinformatics datasets, it is fully generalized for any domain where downstream consumers perform machine learning, deep learning, or AI modeling.
</p>
</div>
<div class="faq-item">
<h4><i class="fas fa-file-signature" style="color: var(--accent-cyan);"></i> Do you offer customized Master Service Agreements (MSAs)?</h4>
<p>
    Yes. If your corporate legal or procurement team requires customized indemnification limits, vendor onboarding, or an enterprise-wide site license instead of individual developer seats or compute nodes, contact us directly to execute a custom MSA.
</p>
</div>
<div class="faq-item">
<h4><i class="fas fa-box-open" style="color: var(--accent-green);"></i> How is the commercial key &amp; package delivered?</h4>
<p>
    Upon license execution, your engineering team receives a unique authentication token for our private PyPI and compiled binary registry along with a counter-signed legal PDF copy of your commercial license agreement.
</p>
</div>
<div class="faq-item">
<h4><i class="fas fa-scale-balanced" style="color: var(--accent-amber);"></i> When do I need a Commercial License vs. AGPLv3?</h4>
<p>
    If you are using our libraries for academic research or open-source software released under a compatible license, the $0 AGPLv3/MIT tier applies. If you embed our libraries into a proprietary product, internal commercial pipeline, or hosted network service without disclosing your source code, a Commercial License is required.
</p>
</div>
<div class="faq-item">
<h4><i class="fas fa-screwdriver-wrench" style="color: var(--brand-primary);"></i> Can Unity Systems build custom extensions or implement custom research papers?</h4>
<p>
    Yes. Beyond off-the-shelf component licensing, Unity Systems provides bespoke R&amp;D consulting to implement specific published research papers, create custom data engineering prep pipelines, or integrate our high-performance AI engines directly into your enterprise infrastructure under ITIL-governed delivery cycles.
</p>
</div>
</div>
</section>'''
    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'faq'", (new_faq_html,))
    print("[OK] Updated storefront.faq")

    # 6. Update storefront.footer
    new_footer_html = '''<footer>
<div>
<strong>Unity Systems | <span dir="rtl" lang="ar" style="font-family: 'Cairo', sans-serif;"><span class="arabic-unity">الوحدة</span> <span class="arabic-systems">للأنظمة</span></span></strong> &copy; 2026 Dr. Islam Akef Ebeid. All rights reserved.
<div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 4px;">Translating Published Academic Research into Enterprise Software &bull; Academically Trained Graduate Engineers &bull; ITIL-Certified Service Management</div>
</div>
<div>
<a href="business.html">Business Portfolio</a> &bull;
<a href="../../index.html">Main Website</a> &bull;
<a href="mailto:iaebeid@gmail.com">iaebeid@gmail.com</a>
</div>
</footer>'''
    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'footer'", (new_footer_html,))
    print("[OK] Updated storefront.footer")

    # 7. Update business.hero_banner and business.section_6
    new_business_hero = '''<div class="max-w-5xl mx-auto text-center mb-16">
<h1 class="text-4xl font-bold text-gray-900 mb-4 text-center">Unity Systems &amp; Startup Ventures</h1>
<p class="text-xl text-sky-700 font-medium mb-6">Bridging Advanced Computational Intelligence &amp; Scalable Enterprise Software</p>
<p class="text-lg text-gray-700 leading-relaxed text-justify md:text-center max-w-4xl mx-auto">
<strong>Unity Systems</strong> is my technology startup and entrepreneurial venture dedicated to developing intelligent data architectures, high-impact community platforms, and mission-critical software solutions. Our defining niche is the academic focus of implementing peer-reviewed published research into battle-tested enterprise systems, in addition to innovating novel algorithmic frameworks and data engineering pipelines. We operate with a specialized team of professional software engineers and academically trained graduate staff who are ITIL certified (or actively pursuing ITIL certification as a strict hiring requirement)—combining academic scientific rigor with enterprise IT service management standards and industry engineering experience across multinational corporate leaders (including Arkansas.gov / NIC Inc., WeDo Technologies, Orange Telecom / Mobinil, Xpress Integration, Maroc Telecom, Tunisie Telecom, Ericsson Egypt, Vodafone, and Hanna Instruments).
</p>
</div>'''
    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'business' AND section_key = 'hero_banner'", (new_business_hero,))
    print("[OK] Updated business.hero_banner")

    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'business' AND section_key = 'section_6'")
    sec6_html = cursor.fetchone()[0]
    old_itil = '<p class="text-sm font-semibold text-sky-600 mb-2">IT Service Management (ITSM)</p>\n<p class="text-gray-600 text-sm leading-relaxed">Certified in IT service lifecycle frameworks, continual service improvement, incident governance, and enterprise delivery standards.</p>'
    new_itil = '<p class="text-sm font-semibold text-sky-600 mb-2">IT Service Management (ITSM) &bull; Team Hiring Standard</p>\n<p class="text-gray-600 text-sm leading-relaxed">Certified in IT service lifecycle frameworks, continual service improvement, incident governance, and enterprise delivery standards. ITIL certification (or active candidacy) is also a required engineering baseline for all Unity Systems graduate and engineering personnel.</p>'
    if old_itil in sec6_html:
        sec6_html = sec6_html.replace(old_itil, new_itil)
        cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'business' AND section_key = 'section_6'", (sec6_html,))
        print("[OK] Updated business.section_6")
    else:
        print("Note: old_itil not exact string match in section_6, skipping section_6 update or using regex")

    conn.commit()
    conn.close()
    print("Database updates committed successfully!")

if __name__ == '__main__':
    update_content()
