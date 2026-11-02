import os
import shutil

src_imams = r'G:\My Drive\Documents\Projects\Scholarship\Manuscripts\Fiqh\imams.docx'
src_poem = r'G:\My Drive\Documents\Projects\Scholarship\Poetry\Drafts\unnecessary-suffering-ebeid.docx'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\documents'

shutil.copy(src_imams, dest_dir)
shutil.copy(src_poem, dest_dir)

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\scholarship\scholarship.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

timeline_html = '''
                <!-- Timeline of Imams -->
                <div class="mt-8 p-6 rounded-xl border border-gray-200 bg-white shadow-sm">
                    <div class="flex items-center gap-3 mb-4">
                        <i class="fas fa-history text-emerald-600 text-xl"></i>
                        <h3 class="font-bold text-gray-900 text-lg">Chronological Timeline of Islamic Scholars (Imams)</h3>
                    </div>
                    <p class="text-sm text-gray-700 leading-relaxed mb-4">
                        A comprehensive chronological timeline of the great Imams and scholars of Islamic jurisprudence up to 1000 AH, detailing their contributions, foundational texts, and methodological schools. 
                    </p>
                    <a href="../../documents/imams.docx" class="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold px-4 py-2 rounded-lg border border-emerald-200 transition text-sm">
                        <i class="fas fa-file-word"></i> View Timeline Manuscript
                    </a>
                </div>
'''

target_thrust = '''                    </div>
                </div>
            </section>'''
            
replacement_thrust = '''                    </div>
                </div>''' + timeline_html + '''
            </section>'''

if target_thrust in content:
    content = content.replace(target_thrust, replacement_thrust, 1)

poetry_html = '''
                <!-- Selected Works -->
                <div class="mt-8">
                    <h3 class="font-bold text-gray-900 text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-leaf text-purple-600"></i> Selected Works &amp; Drafts
                    </h3>
                    <div class="space-y-4">
                        <div class="p-5 rounded-xl border border-purple-100 bg-purple-50/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div>
                                <h4 class="font-bold text-gray-900 text-base mb-1">Unnecessary Suffering</h4>
                                <p class="text-xs text-gray-600 mb-2">A reflective draft exploring themes of justice and humanity in the context of Gaza.</p>
                                <span class="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded uppercase">Poetry Draft</span>
                            </div>
                            <a href="../../documents/unnecessary-suffering-ebeid.docx" class="inline-flex items-center gap-2 text-purple-700 hover:text-purple-900 font-semibold text-sm transition">
                                <i class="fas fa-file-word"></i> Read Draft
                            </a>
                        </div>
                        
                        <div class="p-5 rounded-xl border border-purple-100 bg-purple-50/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div>
                                <h4 class="font-bold text-gray-900 text-base mb-1">Alienation &amp; Magazine Submissions</h4>
                                <p class="text-xs text-gray-600 mb-2">Various poetry submissions exploring cultural diaspora, memory, and heritage.</p>
                                <span class="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded uppercase">Submissions</span>
                            </div>
                        </div>
                    </div>
                </div>
'''

target_poetry = '''                <!-- Creative Verse Excerpt Card -->'''
replacement_poetry = poetry_html + "\n                <!-- Creative Verse Excerpt Card -->"

if target_poetry in content:
    content = content.replace(target_poetry, replacement_poetry, 1)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updates applied successfully.")
