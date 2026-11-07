import sqlite3
import re

def update_pillar2():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'architecture'")
    arch_html = cursor.fetchone()[0]

    old_pillar_2 = '''<div class="pillar-card">
<span class="pillar-step">02 // RESEARCH_IMPLEMENTATIONS</span>
<h3>Implementing Published Research &amp; Novel Frameworks</h3>
<p>
    Our primary niche: translating complex peer-reviewed algorithms from top-tier academic literature into robust, high-performance software libraries alongside innovating original mathematical architectures. Includes high-efficiency neural feature extractors (<strong>ProtGram-DirectGCN</strong>) and unsupervised modularity-based entity resolution engines (<strong>ModER-GraphER</strong>).
</p>
</div>'''

    new_pillar_2 = '''<div class="pillar-card">
<span class="pillar-step">02 // AI_MODELING_ENGINES</span>
<h3>AI Modeling: LLMs, Graph Neural Networks &amp; Agentic AI</h3>
<p>
    The second stage of our framework is centered around advanced AI modeling—spanning Large Language Models (LLMs), Graph Neural Networks (GNNs), Agentic AI architectures, and neuro-symbolic deep learning systems. We translate published breakthrough research and novel algorithms into high-performance training and inference engines (including <strong>ProtGram-DirectGCN</strong>, <strong>ModER-GraphER</strong>, and autonomous agentic workflows) built to operate directly on curated upstream data.
</p>
</div>'''

    if old_pillar_2 in arch_html:
        arch_html = arch_html.replace(old_pillar_2, new_pillar_2)
        print("[OK] Replaced Pillar 2 with exact match")
    else:
        print("[WARN] Attempting regex replacement for Pillar 2")
        arch_html = re.sub(
            r'<div class="pillar-card">\s*<span class="pillar-step">02[\s\S]*?</div>\s*(?=<div class="pillar-card">\s*<span class="pillar-step">03)',
            new_pillar_2 + '\n',
            arch_html,
            count=1
        )
        print("[OK] Regex replaced Pillar 2")

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'architecture'", (arch_html,))
    conn.commit()
    conn.close()
    print("[SUCCESS] Database updated successfully!")

if __name__ == '__main__':
    update_pillar2()
