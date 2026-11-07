import os
import shutil
import zipfile

base_dir = r'G:\My Drive\Documents\Projects\Teaching'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\documents'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\teaching\teaching.html'

# Copy the assignment
assignment_src = os.path.join(base_dir, 'Assignments', 'VideoFlick', '81.docx')
assignment_dest = os.path.join(dest_dir, 'VideoFlick_Assignment.docx')
if os.path.exists(assignment_src):
    shutil.copy(assignment_src, assignment_dest)

# Zip the code directories
code_dirs = ['ThinkPython', 'SparkMLlib', 'DeepLearningClass']
for c_dir in code_dirs:
    src_path = os.path.join(base_dir, 'Code', c_dir)
    zip_path = os.path.join(dest_dir, f"{c_dir}.zip")
    if os.path.exists(src_path):
        # shutil.make_archive(zip_path.replace('.zip', ''), 'zip', src_path)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(src_path):
                if '.git' in root or '.idea' in root:
                    continue
                for file in files:
                    if file.endswith('.py') or file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, src_path)
                        zipf.write(file_path, arcname)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

projects_section = '''
            <!-- Example Projects & Assignments -->
            <section id="projects" class="bg-white p-8 rounded-xl shadow-md border-t-4 border-sky-600 mt-12">
                <h2 class="section-title text-left mb-6"><i class="fas fa-laptop-code text-sky-600 mr-2"></i> Example Projects &amp; Assignments</h2>
                <div class="text-gray-700 space-y-4 mb-6">
                    <p>
                        A selection of practical assignments and code examples provided to students across various computer science and data science courses. These materials emphasize hands-on learning, ranging from introductory Python programming to advanced distributed machine learning.
                    </p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- ThinkPython -->
                    <div class="border border-gray-200 p-5 rounded-lg shadow-sm hover:shadow-md transition bg-gray-50/50">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fab fa-python text-2xl text-blue-600"></i>
                            <h3 class="font-bold text-gray-900 text-lg">ThinkPython Code Examples</h3>
                        </div>
                        <p class="text-sm text-gray-600 mb-4">Sample code implementations and exercises designed for introductory programming students following the ThinkPython curriculum.</p>
                        <a href="../../documents/ThinkPython.zip" class="inline-flex items-center gap-2 text-sky-600 hover:text-sky-800 font-semibold text-sm">
                            <i class="fas fa-file-archive"></i> Download Code (ZIP)
                        </a>
                    </div>

                    <!-- SparkMLlib -->
                    <div class="border border-gray-200 p-5 rounded-lg shadow-sm hover:shadow-md transition bg-gray-50/50">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-bolt text-2xl text-orange-500"></i>
                            <h3 class="font-bold text-gray-900 text-lg">Spark MLlib Examples</h3>
                        </div>
                        <p class="text-sm text-gray-600 mb-4">Distributed machine learning examples using Apache Spark MLlib, demonstrating scalable data processing techniques.</p>
                        <a href="../../documents/SparkMLlib.zip" class="inline-flex items-center gap-2 text-sky-600 hover:text-sky-800 font-semibold text-sm">
                            <i class="fas fa-file-archive"></i> Download Code (ZIP)
                        </a>
                    </div>

                    <!-- DeepLearningClass -->
                    <div class="border border-gray-200 p-5 rounded-lg shadow-sm hover:shadow-md transition bg-gray-50/50">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-brain text-2xl text-purple-600"></i>
                            <h3 class="font-bold text-gray-900 text-lg">Deep Learning Class</h3>
                        </div>
                        <p class="text-sm text-gray-600 mb-4">Code repositories for deep learning course modules, covering neural network architectures and training loops.</p>
                        <a href="../../documents/DeepLearningClass.zip" class="inline-flex items-center gap-2 text-sky-600 hover:text-sky-800 font-semibold text-sm">
                            <i class="fas fa-file-archive"></i> Download Code (ZIP)
                        </a>
                    </div>

                    <!-- VideoFlick Assignment -->
                    <div class="border border-gray-200 p-5 rounded-lg shadow-sm hover:shadow-md transition bg-gray-50/50">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-film text-2xl text-red-600"></i>
                            <h3 class="font-bold text-gray-900 text-lg">VideoFlick Architecture Assignment</h3>
                        </div>
                        <p class="text-sm text-gray-600 mb-4">A system architecture and database design assignment requiring students to model a video streaming platform.</p>
                        <a href="../../documents/VideoFlick_Assignment.docx" class="inline-flex items-center gap-2 text-sky-600 hover:text-sky-800 font-semibold text-sm">
                            <i class="fas fa-file-word"></i> Download Assignment (DOCX)
                        </a>
                    </div>
                </div>
            </section>
'''

target_tag = '''                </div>
            </section>

        </div>
    </main>'''

replacement_tag = '''                </div>
            </section>
''' + projects_section + '''
        </div>
    </main>'''

if target_tag in content:
    content = content.replace(target_tag, replacement_tag, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated teaching.html and packaged examples.")
