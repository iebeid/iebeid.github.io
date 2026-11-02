import os
import shutil

base_dir = r'G:\My Drive\Documents\Projects\Research\Presentations\Internal'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\documents'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

copies = [
    (os.path.join(base_dir, 'MedGraph', 'MedGraph-Masters-Final-Presentation-Fall-2021-Ebeid.pptx'), 'MedGraph-Final-Presentation.pptx'),
    (os.path.join(base_dir, 'VisInt-X', 'XLPM-Map-Viewer-Final.pptx'), 'XLPM-Map-Viewer-Final.pptx'),
    (os.path.join(base_dir, 'EyeAdaptUI', 'UTA eye-tracking 2018.pptx'), 'UTA-Eye-Tracking-2018.pptx'),
    (os.path.join(base_dir, 'BiomedicalKnowledgeGraphCompletion', 'Bioinformatics_Poster_2020.pptx'), 'Bioinformatics_Poster_2020.pptx')
]

for src, dest_name in copies:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(dest_dir, dest_name))

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

presentations_section = '''
            <!-- Section 6: Research Presentations & Posters -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-emerald-600 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-project-diagram text-emerald-600 mr-3"></i> Conference Talks &amp; Presentations
                    </h2>
                    <span class="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-1 rounded-full">Slides &amp; Posters</span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <!-- MedGraph Presentation -->
                    <div class="bg-emerald-50/40 p-5 rounded-lg border border-emerald-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0">
                            <i class="fas fa-file-powerpoint text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">MedGraph: Medical Knowledge Graph Completion</h3>
                            <p class="text-xs text-gray-600 mb-3">Master's final defense presentation detailing the MedGraph architecture for embedding medical entities.</p>
                            <a href="../../documents/MedGraph-Final-Presentation.pptx" class="text-emerald-700 hover:text-emerald-900 font-bold text-xs uppercase tracking-wider">
                                Download Slides <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>

                    <!-- Bioinformatics Poster -->
                    <div class="bg-emerald-50/40 p-5 rounded-lg border border-emerald-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0">
                            <i class="fas fa-image text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">Biomedical Knowledge Graph Completion</h3>
                            <p class="text-xs text-gray-600 mb-3">Research poster (2020) illustrating deep learning approaches to predicting missing links in biological networks.</p>
                            <a href="../../documents/Bioinformatics_Poster_2020.pptx" class="text-emerald-700 hover:text-emerald-900 font-bold text-xs uppercase tracking-wider">
                                Download Poster <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>

                    <!-- Eye Tracking Presentation -->
                    <div class="bg-emerald-50/40 p-5 rounded-lg border border-emerald-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0">
                            <i class="fas fa-file-powerpoint text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">Eye-Tracking &amp; Adaptive UI (ETRA)</h3>
                            <p class="text-xs text-gray-600 mb-3">Slide deck exploring gaze transition entropy and eye-tracking applications in virtual reality environments.</p>
                            <a href="../../documents/UTA-Eye-Tracking-2018.pptx" class="text-emerald-700 hover:text-emerald-900 font-bold text-xs uppercase tracking-wider">
                                Download Slides <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>

                    <!-- XLPM Presentation -->
                    <div class="bg-emerald-50/40 p-5 rounded-lg border border-emerald-100 shadow-sm flex items-start gap-4">
                        <div class="w-12 h-12 bg-white rounded-lg border border-emerald-200 flex items-center justify-center text-emerald-600 flex-shrink-0">
                            <i class="fas fa-file-powerpoint text-2xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-gray-900 text-base mb-1">XLPM Image Quality Map Viewer</h3>
                            <p class="text-xs text-gray-600 mb-3">Presentation covering the VisInt-X project and the perceptual metric map viewer developed for image analysis.</p>
                            <a href="../../documents/XLPM-Map-Viewer-Final.pptx" class="text-emerald-700 hover:text-emerald-900 font-bold text-xs uppercase tracking-wider">
                                Download Slides <i class="fas fa-download ml-1"></i>
                            </a>
                        </div>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = presentations_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Presentations section.")
