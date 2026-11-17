import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

# 1. Derive style_lab CSS directly from style_storefront, shifting blue accents -> emerald green shades
cur.execute("SELECT css_content FROM stylesheets WHERE style_key='style_storefront'")
sf_css = cur.fetchone()[0]

lab_css = sf_css
# Replace blue/navy accent colors with emerald green shades while keeping gray (#4b5563, #6b7280) intact
replacements = [
    ("#1e3a8a", "#047857"),
    ("#172554", "#064e3b"),
    ("#0f172a", "#064e3b"),
    ("rgba(30, 58, 138,", "rgba(4, 120, 87,"),
    ("rgba(15, 23, 42,", "rgba(4, 120, 87,"),
    (".unity-systems-trademark-brand", ".lab-trademark-brand"),
    (".word-unity", ".word-gray"),
    (".word-systems", ".word-green"),
    (".arabic-unity", ".arabic-gray"),
    (".arabic-systems", ".arabic-green"),
]
for old, new in replacements:
    lab_css = lab_css.replace(old, new)

# Add subtle two-column grid helper for Topics & Courses/Funding
lab_css += """
        .lab-cards-2col {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }
        @media (max-width: 768px) {
            .lab-cards-2col {
                grid-template-columns: 1fr;
            }
        }
        .lab-topic-pill {
            display: inline-block;
            background: rgba(4, 120, 87, 0.08);
            color: #047857;
            border: 1px solid rgba(4, 120, 87, 0.25);
            padding: 0.28rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.2rem 0.25rem 0.2rem 0;
        }
        .lab-pub-item {
            border-left: 3px solid #047857;
            padding-left: 1.15rem;
            margin-bottom: 1.35rem;
        }
        .lab-pub-item:last-child {
            margin-bottom: 0;
        }
        .lab-pub-link {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            margin-top: 0.5rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: #047857;
            text-decoration: none;
        }
        .lab-pub-link:hover {
            color: #064e3b;
            text-decoration: underline;
        }
"""

cur.execute("UPDATE stylesheets SET css_content=? WHERE style_key='style_lab'", (lab_css,))
print("[OK] Updated style_lab CSS to match style_storefront with gray & green palette")

# 2. Update lab body_template_html & body_classes in pages table
lab_body_tpl = """<div data-db-section="lab.header"></div>
<main>
    <div data-db-section="lab.about"></div>
    <div data-db-section="lab.narrative"></div>
    <div data-db-section="lab.mission"></div>
    <div data-db-section="lab.vision"></div>
    <div data-db-section="lab.topics"></div>
    <div data-db-section="lab.members"></div>
    <div data-db-section="lab.publications"></div>
    <div data-db-section="lab.courses"></div>
    <div data-db-section="lab.funding"></div>
</main>
<div data-db-section="lab.footer"></div>"""

cur.execute(
    "UPDATE pages SET body_template_html=?, body_classes='' WHERE slug='lab'",
    (lab_body_tpl,)
)
print("[OK] Updated lab page template to match storefront layout")

# 3. Update all lab sections in page_sections
sections = {
    "header": """<header>
<div class="nav-container">
    <!-- LAB TRADEMARK-STYLE BRAND LOGO (Gray & Green Palette) -->
    <a aria-label="Data2AI4LifeSciences Lab Brand Logo" class="lab-trademark-brand" href="lab.html">
        <div class="brand-icon" title="Data2AI4LifeSciences Laboratory">Δ²</div>
        <div class="brand-content">
            <div class="brand-text-column">
                <div class="brand-title">
                    <span><span class="word-gray">DATA2AI</span><span class="word-green">4LIFESCIENCES</span></span>
                    <span class="brand-divider">|</span>
                    <span class="brand-arabic" dir="rtl" lang="ar"><span class="arabic-gray">مختبر</span> <span class="arabic-green">البيانات والذكاء</span></span>
                </div>
                <span class="brand-subtitle"><span>Data Quality</span><span>•</span><span>Biomedical AI</span><span>•</span><span>Human Factors</span></span>
            </div>
            <span class="region-tag">TWU • NSF</span>
        </div>
    </a>
    <nav class="nav-links">
        <a href="#about">Overview</a>
        <a href="#narrative">Narrative &amp; Mission</a>
        <a href="#topics">Topics</a>
        <a href="#members">Members</a>
        <a href="#publications">Publications</a>
        <a href="#funding">Funding</a>
        <a class="github-link" href="research.html">
            <i class="fas fa-arrow-left"></i> Research Portfolio
        </a>
    </nav>
</div>
</header>""",

    "about": """<section class="hero" id="about">
    <div>
        <div class="hero-badge">
            <i class="fas fa-flask"></i> Texas Woman's University &bull; NSF Award #2523786 &bull; Computational Life Sciences
        </div>
        <h1>The <span>Data2AI4LifeSciences</span> Laboratory @ TWU.</h1>
        <p>
            Advancing trustworthy AI for the Life Sciences—bridging rigorous Data Quality, Graph Representation Learning, Biomedical Informatics, and Human Factors from the cell to the brain.
        </p>
        <div class="hero-actions">
            <a class="btn-primary" href="#topics">
                <i class="fas fa-dna"></i> Explore Research Topics
            </a>
            <a class="btn-primary" href="#publications">
                <i class="fas fa-book-open"></i> Selected Publications
            </a>
        </div>
    </div>
    <div class="code-window">
        <div class="code-header">
            <div class="code-dots">
                <div class="code-dot red"></div>
                <div class="code-dot amber"></div>
                <div class="code-dot green"></div>
            </div>
            <span>lab_pillars.py — Data2AI4LifeSciences</span>
        </div>
        <pre><code><span class="comment"># Three Core Research Pillars @ TWU</span>
pillars = {
    <span class="string">"01_Data_Quality_in_AI"</span>:
        <span class="string">"Reliability, entity resolution &amp; integrity of AI datasets."</span>,
    <span class="string">"02_AI_in_Life_Sciences"</span>:
        <span class="string">"GNNs, proteomics, imaging &amp; drug discovery."</span>,
    <span class="string">"03_Human_Factors_in_AI"</span>:
        <span class="string">"Biometrics, ethics &amp; societal impact of AI."</span>
}</code></pre>
    </div>
</section>""",

    "narrative": """<section class="model-section" id="narrative">
    <div class="section-heading">
        <h2>What We Do &amp; Lab Architecture</h2>
        <p>
            Our research ecosystem is dedicated to AI for Life Sciences, grounded in foundational theoretical computer science and applied data science. Our domains include Computer Vision, Language Modeling, Information Science, Network Science, and Human Factors. We advance traditional analyses by pioneering Graph Representation Learning and Multimodal Data Integration—transforming unstructured information into dynamic Knowledge Graphs that bridge data validity and model accuracy.
        </p>
    </div>
    <div class="pillars-grid">
        <div class="pillar-card">
            <span class="pillar-step">01 // DATA_QUALITY_IN_AI</span>
            <h3>Data Quality in AI</h3>
            <p>
                We focus on ensuring the reliability, entity resolution, and structural integrity of data used in artificial intelligence systems—establishing rigorous standards before downstream modeling begins.
            </p>
        </div>
        <div class="pillar-card">
            <span class="pillar-step">02 // AI_IN_LIFE_SCIENCES</span>
            <h3>AI in Life Sciences</h3>
            <p>
                Applying cutting-edge Graph Neural Networks, foundation models, and multimodal deep learning to solve complex problems in biology, proteomics, biomedical imaging, and medicine.
            </p>
        </div>
        <div class="pillar-card">
            <span class="pillar-step">03 // HUMAN_FACTORS_IN_AI</span>
            <h3>Human Factors in AI</h3>
            <p>
                Investigating operator attention via biometrics and non-linear analysis alongside the ethical, legal, and societal implications of sustainable AI technologies.
            </p>
        </div>
    </div>
</section>""",

    "mission": """<section class="model-section" id="mission" style="padding-top: 1.5rem;">
    <div class="software-card" style="padding: 2rem;">
        <span class="pillar-step">LAB_MISSION // BIOMEDICAL_INTELLIGENCE</span>
        <h3 style="font-size: 1.45rem; color: #4b5563; margin-bottom: 0.75rem;">Mission</h3>
        <p style="color: var(--text-muted); font-size: 0.98rem; line-height: 1.7;">
            Our mission is to accelerate progress in Biomedical Informatics, Biomedical Literature Mining, Biomedical Imaging, and Computational Drug Discovery. We achieve this by developing novel Graph Neural Networks, integrating large foundation models, and automating Knowledge-Extraction pipelines that transform raw data into actionable insights. To address structural challenges in Data Science, we establish rigorous standards for Data Quality, Entity Resolution, and Entity Recognition. We also enhance Human Factors in AI by integrating Biometrics and Non-Linear Analysis to model operator attention during system interaction—committed to ethical, sustainable end-to-end AI systems that generate valid, interpretable, reliable, and safe scientific hypotheses.
        </p>
    </div>
</section>""",

    "vision": """<section class="model-section" id="vision" style="padding-top: 1.5rem;">
    <div class="software-card" style="padding: 2rem;">
        <span class="pillar-step">LAB_VISION // SCIENTIFIC_DISCOVERY</span>
        <h3 style="font-size: 1.45rem; color: #4b5563; margin-bottom: 0.75rem;">Vision</h3>
        <p style="color: var(--text-muted); font-size: 0.98rem; line-height: 1.7;">
            We envision a future in which Data Mining, Network Biology, and Information Retrieval merge into an intelligent system that advances scientific discovery. In this world, Language Modeling and Graph Theory work together to automatically curate biological knowledge and reduce the time needed for discoveries. Here, AI is a transparent partner, always grounded in Ethics, Law, and Data Quality, and serves to enhance, never replace, human intelligence. Ultimately, we strive to define the next generation of Biomedical Intelligence, where structured networks clarify the underlying logic of life.
        </p>
    </div>
</section>""",

    "topics": """<section class="model-section" id="topics">
    <div class="section-heading">
        <h2>Research Topics &amp; Domains</h2>
        <p>Interdisciplinary investigations spanning computational biology, network intelligence, information engineering, and responsible human-centered AI.</p>
    </div>
    <div class="lab-cards-2col">
        <div class="software-card" style="padding: 1.75rem;">
            <span class="pillar-step">DOMAIN_01</span>
            <h3 style="font-size: 1.2rem; color: #4b5563; margin-bottom: 0.9rem;">Biomedical &amp; Life Sciences</h3>
            <div>
                <span class="lab-topic-pill">Biomedical informatics</span>
                <span class="lab-topic-pill">Computational drug discovery</span>
                <span class="lab-topic-pill">Protein interaction prediction</span>
                <span class="lab-topic-pill">Computational biomedical imaging</span>
                <span class="lab-topic-pill">Network biology</span>
                <span class="lab-topic-pill">Hypothesis generation</span>
            </div>
        </div>
        <div class="software-card" style="padding: 1.75rem;">
            <span class="pillar-step">DOMAIN_02</span>
            <h3 style="font-size: 1.2rem; color: #4b5563; margin-bottom: 0.9rem;">Graph Theory &amp; Network Intelligence</h3>
            <div>
                <span class="lab-topic-pill">Graph theory</span>
                <span class="lab-topic-pill">Knowledge graphs</span>
                <span class="lab-topic-pill">Network science</span>
                <span class="lab-topic-pill">Graph representation learning</span>
                <span class="lab-topic-pill">Graph neural networks</span>
                <span class="lab-topic-pill">Deep learning</span>
                <span class="lab-topic-pill">Generative AI</span>
                <span class="lab-topic-pill">Foundation models</span>
            </div>
        </div>
        <div class="software-card" style="padding: 1.75rem;">
            <span class="pillar-step">DOMAIN_03</span>
            <h3 style="font-size: 1.2rem; color: #4b5563; margin-bottom: 0.9rem;">Data Science &amp; Information Engineering</h3>
            <div>
                <span class="lab-topic-pill">Data quality</span>
                <span class="lab-topic-pill">Multimodal data integration</span>
                <span class="lab-topic-pill">Data science</span>
                <span class="lab-topic-pill">Big data</span>
                <span class="lab-topic-pill">Data mining</span>
                <span class="lab-topic-pill">Information retrieval</span>
                <span class="lab-topic-pill">Entity resolution</span>
                <span class="lab-topic-pill">Entity recognition</span>
                <span class="lab-topic-pill">Information science</span>
                <span class="lab-topic-pill">Automated knowledge extraction</span>
            </div>
        </div>
        <div class="software-card" style="padding: 1.75rem;">
            <span class="pillar-step">DOMAIN_04</span>
            <h3 style="font-size: 1.2rem; color: #4b5563; margin-bottom: 0.9rem;">Human Factors &amp; Responsible AI</h3>
            <div>
                <span class="lab-topic-pill">Human-computer interaction</span>
                <span class="lab-topic-pill">Eye tracking</span>
                <span class="lab-topic-pill">Ethics and sustainability in AI</span>
            </div>
        </div>
    </div>
</section>""",

    "members": """<section class="model-section" id="members">
    <div class="section-heading">
        <h2>Laboratory Members</h2>
        <p>Principal Investigator, graduate researchers, and affiliated faculty collaborating at Texas Woman's University.</p>
    </div>
    <div class="pillars-grid">
        <div class="pillar-card">
            <span class="pillar-step">PRINCIPAL_INVESTIGATOR</span>
            <h3>Dr. Islam Akef Ebeid</h3>
            <p>Assistant Professor of Computer Science &amp; Laboratory Director at Texas Woman's University.</p>
            <a class="lab-pub-link" href="mailto:iebeid@twu.edu"><i class="fas fa-envelope"></i> iebeid@twu.edu</a>
        </div>
        <div class="pillar-card">
            <span class="pillar-step">GRADUATE_RESEARCHERS</span>
            <h3>Students</h3>
            <p>Meagan Stephens</p>
        </div>
        <div class="pillar-card">
            <span class="pillar-step">COLLABORATORS</span>
            <h3>Affiliated Faculty</h3>
            <p>Dr. Wen Xu</p>
        </div>
    </div>
</section>""",

    "publications": """<section class="model-section" id="publications">
    <div class="section-heading">
        <h2>Selected Lab Publications</h2>
        <p>Peer-reviewed contributions in Graph Neural Networks, proteomics, and biomedical imaging foundation models.</p>
    </div>
    <div class="software-card" style="padding: 2rem;">
        <div class="lab-pub-item">
            <p style="color: #4b5563; font-size: 0.96rem; line-height: 1.65;">
                Ebeid IA, Tang H, and Gu P (2025). Inferred global dense residue transition graphs from primary structure sequences enable protein interaction prediction via directed graph convolutional neural networks.
                <em>Front. Bioinform.</em> 5:1651623. doi: 10.3389/fbinf.2025.1651623
            </p>
            <a class="lab-pub-link" href="https://doi.org/10.3389/fbinf.2025.1651623" rel="noopener noreferrer" target="_blank">
                <i class="fas fa-external-link-alt"></i> View Publication
            </a>
        </div>
        <div class="lab-pub-item">
            <p style="color: #4b5563; font-size: 0.96rem; line-height: 1.65;">
                Gu, P., Tang, H., Ebeid, I. A., Nunez, J. A., Vazquez, F., Adame, D., ... &amp; Chen, D. Z. (2025, June). Adapting a Segmentation Foundation Model for Medical Image Classification.
                <em>In 2025, IEEE 38th International Symposium on Computer-Based Medical Systems (CBMS)</em> (pp. 167-172). IEEE.
            </p>
        </div>
    </div>
</section>""",

    "courses": """<section class="model-section" id="courses" style="padding-top: 1.5rem;">
    <div class="software-card" style="padding: 1.75rem;">
        <span class="pillar-step">CURRICULUM_&_TRAINING</span>
        <h3 style="font-size: 1.25rem; color: #4b5563; margin-bottom: 0.75rem;">Courses</h3>
        <p style="color: var(--text-muted); font-size: 0.95rem;">
            <strong style="color: #4b5563;">CSCI 4623:</strong> Big Data and High-Performance Computing
        </p>
    </div>
</section>""",

    "funding": """<section class="model-section" id="funding" style="padding-top: 1.5rem;">
    <div class="software-card" style="padding: 1.75rem;">
        <span class="pillar-step">SPONSORED_RESEARCH</span>
        <h3 style="font-size: 1.25rem; color: #4b5563; margin-bottom: 0.75rem;">Funding Sources</h3>
        <p style="color: var(--text-muted); font-size: 0.95rem;">
            <strong style="color: #4b5563;">National Science Foundation (NSF)</strong><br/>
            Award Number: 2523786
        </p>
    </div>
</section>""",

    "footer": """<footer>
    <div>
        <strong>Data2AI4LifeSciences Laboratory @ TWU | <span dir="rtl" lang="ar" style="font-family: 'Cairo', sans-serif;"><span class="arabic-gray">مختبر</span> <span class="arabic-green">البيانات والذكاء</span></span></strong> &copy; 2026 Dr. Islam Akef Ebeid. All rights reserved.
        <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 4px;">Data Quality in AI &bull; AI in Life Sciences &bull; Human Factors in AI</div>
    </div>
    <div>
        <a href="research.html">Research Portfolio</a> &bull;
        <a href="../../index.html">Main Website</a> &bull;
        <a href="mailto:iebeid@twu.edu">iebeid@twu.edu</a>
    </div>
</footer>"""
}

for key, html in sections.items():
    cur.execute(
        "UPDATE page_sections SET content_html=? WHERE page_slug='lab' AND section_key=?",
        (html, key)
    )
    print(f"[OK] Updated lab.{key}")

conn.commit()
conn.close()
