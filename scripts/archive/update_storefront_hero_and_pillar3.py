import sqlite3

def update_storefront():
    conn = sqlite3.connect('data/content.db')
    cursor = conn.cursor()

    # 1. Update storefront.section_1 (Hero)
    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'section_1'")
    section_1_html = cursor.fetchone()[0]

    old_h1 = '<h1>From Published Research to <span>Production-Grade AI &amp; Compute</span> Systems.</h1>'
    new_h1 = '<h1>From Published Research to <span>Data-Engineered, Production-Grade AI Modeling</span> &amp; Scientific Compute Systems.</h1>'

    if old_h1 in section_1_html:
        section_1_html = section_1_html.replace(old_h1, new_h1)
        print("[OK] Replaced H1 in section_1")
    else:
        print("[WARN] old_h1 not matched directly in section_1, attempting regex replacement")
        import re
        section_1_html = re.sub(r'<h1>From Published Research to[\s\S]*?Systems\.</h1>', new_h1, section_1_html, count=1)
        print("[OK] Regex replaced H1 in section_1")

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'section_1'", (section_1_html,))

    # 2. Update storefront.architecture (Pillar 3)
    cursor.execute("SELECT content_html FROM page_sections WHERE page_slug = 'storefront' AND section_key = 'architecture'")
    arch_html = cursor.fetchone()[0]

    old_pillar_3 = '''<div class="pillar-card">
<span class="pillar-step">03 // VISUALIZATION_COMPUTE</span>
<h3>GPU Compute &amp; Immersive Visualization</h3>
<p>
    Ultra-low-latency C++, CUDA, OpenGL, and WebGL rendering engines compiled for multi-million particle simulations (<strong>CudaParticles Engine</strong>), stereoscopic VR raymarching (<strong>RaymarcherVR Engine</strong>), and structural molecular cross-linking inspection (<strong>VisInt-X</strong>).
</p>
</div>'''

    new_pillar_3 = '''<div class="pillar-card">
<span class="pillar-step">03 // VISUALIZATION_&amp;_REPORTING</span>
<h3>High-Performance Visualizations &amp; KPI Reporting Tools</h3>
<p>
    The third stage of our framework delivers actionable intelligence through high-performance graphics visualizations and scientific and professional reporting tools to deliver mission-critical KPIs. Blending ultra-low-latency GPU compute, WebGL/OpenGL rendering, and automated analytical dashboards (including <strong>VisInt-X</strong>, <strong>RaymarcherVR Engine</strong>, and <strong>CudaParticles Engine</strong>) to communicate complex multi-dimensional findings and executive KPIs to decision-makers, engineering teams, and scientific stakeholders.
</p>
</div>'''

    if old_pillar_3 in arch_html:
        arch_html = arch_html.replace(old_pillar_3, new_pillar_3)
        print("[OK] Replaced Pillar 3 in architecture")
    else:
        print("[WARN] old_pillar_3 not exact match, attempting regex replacement")
        import re
        arch_html = re.sub(
            r'<div class="pillar-card">\s*<span class="pillar-step">03[\s\S]*?</div>\s*</div>\s*</section>',
            new_pillar_3 + '\n</div>\n</section>',
            arch_html,
            count=1
        )
        print("[OK] Regex replaced Pillar 3 in architecture")

    cursor.execute("UPDATE page_sections SET content_html = ? WHERE page_slug = 'storefront' AND section_key = 'architecture'", (arch_html,))

    conn.commit()
    conn.close()
    print("[SUCCESS] Database committed successfully!")

if __name__ == '__main__':
    update_storefront()
