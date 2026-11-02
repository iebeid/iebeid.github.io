import os
import shutil
import zipfile

base_dir = r'G:\My Drive\Documents\Projects\Research\Data\Internal'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\data'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Create CovidNLPGraph Sample zip
covid_dir = os.path.join(base_dir, 'CovidNLPGraph')
covid_zip_path = os.path.join(dest_dir, 'CovidNLPGraph_Sample.zip')
with zipfile.ZipFile(covid_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for f in ['Entity_bc5cdr.xlsx', 'Entity_bc5cdr.csv']:
        src_path = os.path.join(covid_dir, f)
        if os.path.exists(src_path):
            zipf.write(src_path, arcname=f)

# Copy GDWM results Excel
gdwm_src = os.path.join(base_dir, 'GDWM', 'Combined_GDWM.xlsx')
if os.path.exists(gdwm_src):
    shutil.copy(gdwm_src, os.path.join(dest_dir, 'GDWM_Results.xlsx'))

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

data_section = '''
            <!-- Section 9: Open Research Data & Assets -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-amber-500 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-database text-amber-500 mr-3"></i> Open Research Datasets
                    </h2>
                    <span class="text-xs bg-amber-100 text-amber-800 font-semibold px-2.5 py-1 rounded-full">Data &amp; Assets</span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <!-- CovidNLPGraph -->
                    <div class="bg-amber-50/30 p-5 rounded-lg border border-amber-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-amber-200 flex items-center justify-center text-amber-600 flex-shrink-0">
                            <i class="fas fa-project-diagram text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">CovidNLPGraph Sample Data</h3>
                            <p class="text-xs text-gray-600 mb-3">Extracted biomedical entities and network relations from COVID-19 literature datasets.</p>
                            <a href="../../data/CovidNLPGraph_Sample.zip" class="text-amber-700 hover:text-amber-900 font-bold text-xs uppercase tracking-wider">
                                Download Dataset (.zip) <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>

                    <!-- GDWM Results -->
                    <div class="bg-amber-50/30 p-5 rounded-lg border border-amber-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-amber-200 flex items-center justify-center text-amber-600 flex-shrink-0">
                            <i class="fas fa-table text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">GDWM Evaluation Results</h3>
                            <p class="text-xs text-gray-600 mb-3">Aggregated simulation results and tabular data from the Gaze Directed Window Management (GDWM) experiments.</p>
                            <a href="../../data/GDWM_Results.xlsx" class="text-amber-700 hover:text-amber-900 font-bold text-xs uppercase tracking-wider">
                                Download Data (.xlsx) <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- Chem2Bio2RDF (Placeholder/Link) -->
                    <div class="bg-amber-50/30 p-5 rounded-lg border border-amber-100 shadow-sm flex items-start gap-4 md:col-span-2">
                        <div class="w-12 h-12 bg-white rounded-lg border border-amber-200 flex items-center justify-center text-amber-600 flex-shrink-0">
                            <i class="fas fa-network-wired text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">Chem2Bio2RDF Graph Data</h3>
                            <p class="text-xs text-gray-600 mb-3">Due to the large size (8GB+) of the comprehensive Chem2Bio2RDF biological network data, including MEDLINE relationships, full graph dumps and node/edge mappings are available upon request for research reproducibility.</p>
                        </div>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = data_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Data section.")
