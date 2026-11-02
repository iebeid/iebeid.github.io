import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\education\education.html'

with open(html_path, 'r', encoding='Windows-1252') as f:
    content = f.read()

new_content = r'''
            <!-- Section 0: Current & Upcoming Academic Pursuits -->
            <section class="bg-gradient-to-r from-sky-50 to-white p-8 rounded-xl shadow-md border-l-4 border-indigo-500">
                <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                    <i class="fas fa-hourglass-half text-indigo-600 mr-3"></i> Current &amp; Upcoming Academic Pursuits
                </h2>
                <div class="space-y-6">
                    <div class="flex items-start">
                        <div class="bg-indigo-100 text-indigo-600 rounded-full w-10 h-10 flex items-center justify-center mr-4 flex-shrink-0">
                            <i class="fas fa-chart-line text-lg"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Master of Science in Statistics (Enrolled)</h3>
                            <div class="text-sm font-semibold text-indigo-700 mb-1">The University of Texas at Austin</div>
                            <p class="text-sm text-gray-700 leading-relaxed">
                                Currently enrolled in a Master's degree program focusing on advanced statistical methods and mathematical modeling.
                            </p>
                        </div>
                    </div>
                    
                    <div class="flex items-start">
                        <div class="bg-amber-100 text-amber-600 rounded-full w-10 h-10 flex items-center justify-center mr-4 flex-shrink-0">
                            <i class="fas fa-book-open text-lg"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Master's in Islamic Jurisprudence (Upcoming)</h3>
                            <div class="text-sm font-semibold text-amber-700 mb-1">Al-Azhar University</div>
                            <p class="text-sm text-gray-700 leading-relaxed">
                                Preparing to enroll in a Master's program dedicated to the comprehensive study of Islamic Jurisprudence.
                            </p>
                        </div>
                    </div>

                    <div class="flex items-start">
                        <div class="bg-emerald-100 text-emerald-600 rounded-full w-10 h-10 flex items-center justify-center mr-4 flex-shrink-0">
                            <i class="fas fa-certificate text-lg"></i>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Degree Equivalence Accreditation</h3>
                            <p class="text-sm text-gray-700 leading-relaxed mt-1">
                                Currently working on the formal accreditation and equivalence processes for my previous Ph.D. and Master's degrees.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
'''

target = r'(<div class="max-w-4xl mx-auto space-y-12">)'
match = re.search(target, content)
if match:
    content = content[:match.end()] + "\n" + new_content + content[match.end():]
    with open(html_path, 'w', encoding='Windows-1252') as f:
        f.write(content)
    print("Updated education.html")
else:
    print("Target for education.html not found")
