import os
import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\media\media.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I want to find the section starting with <!-- Featured: Nile University Interview Presentations
# and ending right before <!-- Invited Talks & Lectures Record from CV -->

pattern = re.compile(r'<!-- Featured: Nile University Interview Presentations.*?<!-- Embedded Slide Preview Frame.*?</div>\s*</div>\s*(?=<!-- Invited Talks & Lectures)', re.DOTALL)

new_section = r'''<!-- Faculty Candidate Presentations -->
            <div class="bg-gradient-to-br from-white via-sky-50 to-white p-6 sm:p-8 rounded-xl shadow-lg border border-sky-200">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <span class="inline-block bg-amber-100 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
                        <i class="fas fa-chalkboard-teacher mr-1"></i> Faculty Candidate Job Talks
                    </span>
                </div>
                <h2 class="text-2xl font-bold text-gray-900 mb-2">Faculty Candidate Presentations</h2>
                <p class="text-gray-700 text-sm leading-relaxed mb-5">
                    Downloadable Microsoft PowerPoint (<code>.pptx</code>) and interactive slide decks for various faculty and research presentations.
                </p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
                    <!-- Nile University - 10 Min -->
                    <div class="bg-white p-5 rounded-xl border-2 border-indigo-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-indigo-100 text-indigo-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Nile University (Fall 2026)</span>
                                <span class="text-xs font-mono text-gray-500">10 Mins</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">10-Minute Executive Self-Brief</h3>
                            <p class="text-xs text-gray-600 mb-4 leading-relaxed">
                                Executive synthesis of Teaching, Research, and Administrative Governance for the Dean & Provost.
                            </p>
                        </div>
                        <div class="space-y-2.5 pt-3 border-t border-gray-100">
                            <a href="talk/summary.html" target="_blank" class="w-full inline-flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-desktop mr-2"></i> View Interactive Slides
                            </a>
                        </div>
                    </div>

                    <!-- Nile University - 20 Min -->
                    <div class="bg-white p-5 rounded-xl border-2 border-sky-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-sky-100 text-sky-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Nile University (Fall 2026)</span>
                                <span class="text-xs font-mono text-gray-500">20 Mins</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">20-Minute Committee Job Talk</h3>
                            <p class="text-xs text-gray-600 mb-4 leading-relaxed">
                                Full technical presentation on Neuro-Symbolic Graph Learning and Data Quality.
                            </p>
                        </div>
                        <div class="space-y-2.5 pt-3 border-t border-gray-100">
                            <a href="talk/talk.html" target="_blank" class="w-full inline-flex items-center justify-center bg-sky-600 hover:bg-sky-700 text-white font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-desktop mr-2"></i> View Interactive Slides
                            </a>
                        </div>
                    </div>

                    <!-- Job Talk Spring 2023 -->
                    <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-gray-100 text-gray-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Spring 2023</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">Faculty Job Talk</h3>
                        </div>
                        <div class="pt-3 border-t border-gray-100 mt-4">
                            <a href="../../documents/Job-Talk-Ebeid-Spring-2023.pptx" target="_blank" class="w-full inline-flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300 font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-file-powerpoint mr-2 text-orange-600"></i> Download PPTX
                            </a>
                        </div>
                    </div>

                    <!-- Job Talk Fall 2022 -->
                    <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-gray-100 text-gray-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Fall 2022</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">Faculty Job Talk</h3>
                        </div>
                        <div class="pt-3 border-t border-gray-100 mt-4">
                            <a href="../../documents/Job-Talk-Ebeid-Fall-2022.pptx" target="_blank" class="w-full inline-flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300 font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-file-powerpoint mr-2 text-orange-600"></i> Download PPTX
                            </a>
                        </div>
                    </div>
                    
                    <!-- Paper Presentation Spring 2022 -->
                    <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-gray-100 text-gray-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Spring 2022</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">UNT Bozdag Lab Paper Presentation</h3>
                        </div>
                        <div class="pt-3 border-t border-gray-100 mt-4">
                            <a href="../../documents/Paper-Presentation-UNT-Bozdag-Lab-Spring-2022-Ebeid.pptx" target="_blank" class="w-full inline-flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300 font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-file-powerpoint mr-2 text-orange-600"></i> Download PPTX
                            </a>
                        </div>
                    </div>

                    <!-- Job Talk Winter 2021 -->
                    <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <span class="bg-gray-100 text-gray-800 text-xs font-bold px-2.5 py-0.5 rounded-full uppercase">Winter 2021</span>
                            </div>
                            <h3 class="text-lg font-bold text-gray-900 mb-1">Faculty Job Talk</h3>
                        </div>
                        <div class="pt-3 border-t border-gray-100 mt-4">
                            <a href="../../documents/Job-Talk-Ebeid-Winter-2021.pptx" target="_blank" class="w-full inline-flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300 font-semibold px-4 py-2.5 rounded-lg shadow transition text-sm">
                                <i class="fas fa-file-powerpoint mr-2 text-orange-600"></i> Download PPTX
                            </a>
                        </div>
                    </div>
                </div>
            </div>
'''

if pattern.search(content):
    content = pattern.sub(new_section, content)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated media.html successfully.")
else:
    print("Could not find the target section to replace.")
