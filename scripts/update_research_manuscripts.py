import os
import shutil

base_dir = r'G:\My Drive\Documents\Projects\Research\Manuscripts'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\documents'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

copies = [
    (os.path.join(base_dir, 'Internal', 'UTQualifyingPaper2020', 'Main', 'Qualifying-Paper-Ebeid.pdf'), 'UT-Qualifying-Paper.pdf'),
    (os.path.join(base_dir, 'Internal', 'VisInt-X', 'XLPM-SPIE-IST-submission.pdf'), 'XLPM-SPIE-IST-Manuscript.pdf'),
    (os.path.join(base_dir, 'External', 'GRAPH-NEURAL-NETWORKS', '2305.10498v3.pdf'), 'Graph-Neural-Networks-Review.pdf')
]

for src, dest_name in copies:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(dest_dir, dest_name))

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

manuscript_section = '''
            <!-- Section 5: Manuscripts & Preprints -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-indigo-600 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-file-alt text-indigo-600 mr-3"></i> Selected Manuscripts &amp; Theses
                    </h2>
                    <span class="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2.5 py-1 rounded-full">Preprints &amp; Drafts</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

                    <!-- UT Qualifying Paper -->
                    <div class="bg-indigo-50/50 p-6 rounded-lg shadow-sm border border-indigo-100 flex flex-col justify-between">
                        <div>
                            <h3 class="font-bold text-gray-900 text-lg mb-2">Knowledge Graph Mining</h3>
                            <p class="text-sm text-gray-700 mb-4">A comprehensive qualifying paper and survey of graph neural network methods for mining biomedical knowledge graphs.</p>
                        </div>
                        <a href="../../documents/UT-Qualifying-Paper.pdf" target="_blank" class="inline-flex items-center gap-2 text-indigo-700 hover:text-indigo-900 font-semibold text-sm">
                            <i class="fas fa-file-pdf"></i> Read Manuscript
                        </a>
                    </div>

                    <!-- XLPM Paper -->
                    <div class="bg-indigo-50/50 p-6 rounded-lg shadow-sm border border-indigo-100 flex flex-col justify-between">
                        <div>
                            <h3 class="font-bold text-gray-900 text-lg mb-2">XLPM Perception Metric</h3>
                            <p class="text-sm text-gray-700 mb-4">Draft submission for the XLPM objective image quality assessment metric based on human visual contrast sensitivity.</p>
                        </div>
                        <a href="../../documents/XLPM-SPIE-IST-Manuscript.pdf" target="_blank" class="inline-flex items-center gap-2 text-indigo-700 hover:text-indigo-900 font-semibold text-sm">
                            <i class="fas fa-file-pdf"></i> Read Manuscript
                        </a>
                    </div>
                    
                    <!-- GNN Review -->
                    <div class="bg-indigo-50/50 p-6 rounded-lg shadow-sm border border-indigo-100 flex flex-col justify-between">
                        <div>
                            <h3 class="font-bold text-gray-900 text-lg mb-2">Graph Neural Networks Review</h3>
                            <p class="text-sm text-gray-700 mb-4">External literature review resources compiled for research in GNN capabilities and architectures.</p>
                        </div>
                        <a href="../../documents/Graph-Neural-Networks-Review.pdf" target="_blank" class="inline-flex items-center gap-2 text-indigo-700 hover:text-indigo-900 font-semibold text-sm">
                            <i class="fas fa-file-pdf"></i> Read Review
                        </a>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = manuscript_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Manuscripts section.")
