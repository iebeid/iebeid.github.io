import os
import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\downloads\downloads.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_section = r'''
            <!-- Category 1.5: Career Statements -->
            <section class="space-y-4 doc-group mb-12">
                <div class="flex items-center gap-2.5 pb-2 border-b-2 border-sky-600">
                    <i class="fas fa-file-signature text-sky-600 text-lg"></i>
                    <h2 class="text-xl font-bold text-gray-800">Career Statements</h2>
                </div>
                <ul class="space-y-3">
                    <!-- Research Statement -->
                    <li class="doc-item p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-sky-300 hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div class="flex items-start gap-3.5">
                            <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-lg flex-shrink-0 mt-0.5">
                                <i class="fas fa-file-word"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-900 text-base">Research Statement</h3>
                                <p class="text-xs text-gray-500 mt-0.5">Summary of my research accomplishments, current projects, and future research directions.</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
                            <span class="text-xs text-gray-400 font-mono font-medium">Docx</span>
                            <a href="../../documents/research-statement-2025.docx" target="_blank" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-sky-50 text-sky-700 hover:bg-sky-600 hover:text-white rounded-lg text-xs font-semibold transition border border-sky-200 hover:border-sky-600">
                                <i class="fas fa-download text-[11px]"></i> Download DOCX
                            </a>
                        </div>
                    </li>
                    
                    <!-- Teaching Statement -->
                    <li class="doc-item p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-sky-300 hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div class="flex items-start gap-3.5">
                            <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-lg flex-shrink-0 mt-0.5">
                                <i class="fas fa-file-word"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-900 text-base">Teaching Statement</h3>
                                <p class="text-xs text-gray-500 mt-0.5">My teaching philosophy, methodologies, and commitment to student success.</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
                            <span class="text-xs text-gray-400 font-mono font-medium">Docx</span>
                            <a href="../../documents/Teaching-Philosophy-Ebeid.docx" target="_blank" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-sky-50 text-sky-700 hover:bg-sky-600 hover:text-white rounded-lg text-xs font-semibold transition border border-sky-200 hover:border-sky-600">
                                <i class="fas fa-download text-[11px]"></i> Download DOCX
                            </a>
                        </div>
                    </li>
                    
                    <!-- Diversity Statement -->
                    <li class="doc-item p-4 bg-white rounded-xl shadow-sm border border-gray-100 hover:border-sky-300 hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div class="flex items-start gap-3.5">
                            <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-lg flex-shrink-0 mt-0.5">
                                <i class="fas fa-file-word"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-900 text-base">Diversity Statement</h3>
                                <p class="text-xs text-gray-500 mt-0.5">My dedication to fostering an inclusive, diverse, and equitable academic environment.</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 self-end sm:self-center flex-shrink-0">
                            <span class="text-xs text-gray-400 font-mono font-medium">Docx</span>
                            <a href="../../documents/diversity-statement-ebeid.docx" target="_blank" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-sky-50 text-sky-700 hover:bg-sky-600 hover:text-white rounded-lg text-xs font-semibold transition border border-sky-200 hover:border-sky-600">
                                <i class="fas fa-download text-[11px]"></i> Download DOCX
                            </a>
                        </div>
                    </li>
                </ul>
            </section>
'''

if '<!-- Category 1.5: Career Statements -->' not in content:
    target = '            <!-- Category 2: Presentations, Talks & Seminars -->'
    content = content.replace(target, new_section + '\n' + target)

    # update match count to 50 instead of 47
    content = content.replace('47 downloadable files cataloged', '50 downloadable files cataloged')
    content = content.replace('Showing all (47 files)', 'Showing all (50 files)')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated downloads.html")
else:
    print("Already updated.")

