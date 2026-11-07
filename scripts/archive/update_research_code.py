import os
import shutil
import zipfile

base_dir = r'G:\My Drive\Documents\Projects\Research\Code\Internal'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\code'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

projects_to_zip = [
    (os.path.join(base_dir, 'GRAPH-NEURAL-NETWORKS', 'multivariategcn'), 'multivariategcn.zip'),
    (os.path.join(base_dir, 'COMPUTATIONAL-BIOLOGY', 'protgram-directgcn'), 'protgram-directgcn.zip'),
    (os.path.join(base_dir, 'INFORMATION-VISUALIZATION', 'EyeAdaptEngine'), 'EyeAdaptEngine.zip')
]

for src_path, zip_name in projects_to_zip:
    if os.path.exists(src_path):
        zip_path = os.path.join(dest_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(src_path):
                if '.git' in root or '.idea' in root or 'node_modules' in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, src_path)
                    zipf.write(file_path, arcname)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

code_section = '''
            <!-- Section 10: Code Repositories & Software -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-slate-600 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-code text-slate-600 mr-3"></i> Code Repositories &amp; Software
                    </h2>
                    <span class="text-xs bg-slate-200 text-slate-800 font-semibold px-2.5 py-1 rounded-full">Source Code</span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

                    <!-- Multivariate GCN -->
                    <div class="bg-slate-50 p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center gap-3 mb-2">
                                <i class="fab fa-python text-2xl text-slate-700"></i>
                                <h3 class="font-bold text-gray-900 text-base">Multivariate GCN</h3>
                            </div>
                            <p class="text-xs text-gray-600 mb-4">Implementation of a Graph Neural Network capable of handling multivariate features for robust network representation learning.</p>
                        </div>
                        <a href="../../code/multivariategcn.zip" class="inline-flex items-center gap-2 text-slate-700 hover:text-slate-900 font-bold text-xs uppercase tracking-wider">
                            <i class="fas fa-download"></i> Download Source (.zip)
                        </a>
                    </div>

                    <!-- ProtGram DirectGCN -->
                    <div class="bg-slate-50 p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center gap-3 mb-2">
                                <i class="fas fa-dna text-2xl text-slate-700"></i>
                                <h3 class="font-bold text-gray-900 text-base">ProtGram DirectGCN</h3>
                            </div>
                            <p class="text-xs text-gray-600 mb-4">A novel graph-based framework for structural and sequence-based protein function prediction and interaction modeling.</p>
                        </div>
                        <a href="../../code/protgram-directgcn.zip" class="inline-flex items-center gap-2 text-slate-700 hover:text-slate-900 font-bold text-xs uppercase tracking-wider">
                            <i class="fas fa-download"></i> Download Source (.zip)
                        </a>
                    </div>
                    
                    <!-- EyeAdaptEngine -->
                    <div class="bg-slate-50 p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center gap-3 mb-2">
                                <i class="fas fa-eye text-2xl text-slate-700"></i>
                                <h3 class="font-bold text-gray-900 text-base">EyeAdaptEngine</h3>
                            </div>
                            <p class="text-xs text-gray-600 mb-4">A cognitive ergonomic engine for real-time gaze tracking and adaptive user interfaces, originally used in flight simulator research.</p>
                        </div>
                        <a href="../../code/EyeAdaptEngine.zip" class="inline-flex items-center gap-2 text-slate-700 hover:text-slate-900 font-bold text-xs uppercase tracking-wider">
                            <i class="fas fa-download"></i> Download Source (.zip)
                        </a>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = code_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Code section.")
