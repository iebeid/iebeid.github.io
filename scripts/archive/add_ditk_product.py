#!/usr/bin/env python3
"""
Adds DataIntegrationToolkit (DITK) product card to storefront catalog
and updates licensing modal options in SQLite content.db.
"""

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Update catalog section
    cur.execute("SELECT content_html FROM page_sections WHERE page_slug='storefront' AND section_key='catalog'")
    row = cur.fetchone()
    if not row:
        print("[ERROR] storefront.catalog section not found!")
        return 1

    catalog_html = row[0]

    # Update filter counts
    catalog_html = catalog_html.replace("ALL_SYSTEMS (7)", "ALL_SYSTEMS (8)")
    catalog_html = catalog_html.replace("DATA_CURATION (3)", "DATA_CURATION (4)")
    catalog_html = catalog_html.replace("MODELING_ENGINES (2)", "MODELING_ENGINES (3)")

    ditk_card = """<!-- PRODUCT 2: DataIntegrationToolkit (DITK) -->
<article class="product-card" data-category="DATA_CURATION MODELING_ENGINES">
<div class="card-header">
<div class="tag-container">
<span class="tech-tag lifecycle">DATA_CURATION + MODELING_ENGINES</span>
<span class="tech-tag stack">Python / Medallion Lakehouse / GNN / ER</span>
</div>
<h3>DataIntegrationToolkit (DITK)</h3>
<p class="description">
    Unified, high-performance Lakehouse Engine for Scalable Entity Resolution (ER), Graph Representation Learning (GNN &amp; GraphOG), Biomedical NLP Knowledge Integration, and Bioinformatics Proteomics built on a tiered Medallion storage model (Bronze &rarr; Silver &rarr; Gold).
</p>
</div>
<div class="snippet-container">
<pre><span class="keyword">import</span> dataintegrationtoolkit <span class="keyword">as</span> ditk
lakehouse = ditk.<span class="function">Lakehouse</span>(storage_root=<span class="string">"./lakehouse"</span>)
bronze = lakehouse.<span class="function">ingest</span>(source=<span class="string">"records.csv"</span>, tier=<span class="string">"bronze"</span>)
silver = lakehouse.<span class="function">resolve_entities</span>(bronze, blocker=<span class="string">"minhash_lsh"</span>, matcher=<span class="string">"dwm"</span>)
gold = lakehouse.<span class="function">export_knowledge_graph</span>(silver, format=<span class="string">"gnn_pyg"</span>)</pre>
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
</article>
"""

    target = "</article>\n<!-- PRODUCT 2:"
    if target in catalog_html:
        catalog_html = catalog_html.replace(target, "</article>\n" + ditk_card + "<!-- PRODUCT 3:")
        # Adjust numbering on existing products:
        catalog_html = catalog_html.replace("<!-- PRODUCT 3: EyeArt Engine -->", "<!-- PRODUCT 4: EyeArt Engine -->")
        catalog_html = catalog_html.replace("<!-- PRODUCT 4: RaymarcherVR Engine -->", "<!-- PRODUCT 5: RaymarcherVR Engine -->")
        catalog_html = catalog_html.replace("<!-- PRODUCT 5: CudaParticles Engine -->", "<!-- PRODUCT 6: CudaParticles Engine -->")
        catalog_html = catalog_html.replace("<!-- PRODUCT 6: ModER-GraphER -->", "<!-- PRODUCT 7: ModER-GraphER -->")
        catalog_html = catalog_html.replace("<!-- PRODUCT 7: XLPM-VisIntX Suite", "<!-- PRODUCT 8: XLPM-VisIntX Suite")
    else:
        print("[ERROR] Could not find insertion anchor in catalog HTML!")
        return 1

    cur.execute("UPDATE page_sections SET content_html = ? WHERE page_slug='storefront' AND section_key='catalog'", (catalog_html,))

    # 2. Update license_modal section
    cur.execute("SELECT content_html FROM page_sections WHERE page_slug='storefront' AND section_key='license_modal'")
    modal_row = cur.fetchone()
    if modal_row:
        modal_html = modal_row[0]
        opt_target = '<option value="AILifecycleKit ($499 / dev seat)">AILifecycleKit ($499 / dev seat)</option>'
        opt_replacement = '<option value="AILifecycleKit ($499 / dev seat)">AILifecycleKit ($499 / dev seat)</option>\n<option value="DataIntegrationToolkit ($999 / dev seat)">DataIntegrationToolkit ($999 / dev seat)</option>'
        if opt_target in modal_html:
            modal_html = modal_html.replace(opt_target, opt_replacement)
        modal_html = modal_html.replace('onclick="closeLicenseModal()"></button>', 'onclick="closeLicenseModal()">&times;</button>')
        cur.execute("UPDATE page_sections SET content_html = ? WHERE page_slug='storefront' AND section_key='license_modal'", (modal_html,))

    conn.commit()
    conn.close()
    print("[SUCCESS] DataIntegrationToolkit added to storefront catalog and license modal in SQLite!")
    return 0

if __name__ == "__main__":
    exit(main())
