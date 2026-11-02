import os

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\business\business.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                    <div class="bg-white p-6 rounded-xl shadow-md border border-gray-100">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-check-circle text-emerald-500 text-2xl"></i>
                            <h3 class="text-xl font-bold text-gray-900">ITIL Foundation Certificate</h3>
                        </div>
                        <p class="text-sm font-semibold text-sky-600 mb-2">IT Service Management (ITSM)</p>
                        <p class="text-gray-600 text-sm leading-relaxed">Certified in IT service lifecycle frameworks, continual service improvement, incident governance, and enterprise delivery standards.</p>
                    </div>
                </div>'''

replacement = '''                    <div class="bg-white p-6 rounded-xl shadow-md border border-gray-100">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-check-circle text-emerald-500 text-2xl"></i>
                            <h3 class="text-xl font-bold text-gray-900">ITIL Foundation Certificate</h3>
                        </div>
                        <p class="text-sm font-semibold text-sky-600 mb-2">IT Service Management (ITSM)</p>
                        <p class="text-gray-600 text-sm leading-relaxed">Certified in IT service lifecycle frameworks, continual service improvement, incident governance, and enterprise delivery standards.</p>
                    </div>

                    <!-- In Progress Certifications -->
                    <div class="bg-slate-50 p-6 rounded-xl shadow-sm border border-slate-200 border-l-4 border-l-amber-500">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-hard-hat text-slate-500 text-2xl"></i>
                            <h3 class="text-xl font-bold text-gray-900">Professional Engineer (PE)</h3>
                        </div>
                        <p class="text-sm font-semibold text-amber-600 mb-2">
                            <i class="fas fa-spinner fa-spin mr-1"></i> In Progress &mdash; NCEES
                        </p>
                        <p class="text-gray-600 text-sm leading-relaxed">Currently preparing for the NCEES Professional Engineer (PE) licensure examination to formalize engineering credentials.</p>
                    </div>

                    <div class="bg-slate-50 p-6 rounded-xl shadow-sm border border-slate-200 border-l-4 border-l-amber-500">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fas fa-chalkboard-teacher text-slate-500 text-2xl"></i>
                            <h3 class="text-xl font-bold text-gray-900">ITIL Practitioner / Next Level</h3>
                        </div>
                        <p class="text-sm font-semibold text-amber-600 mb-2">
                            <i class="fas fa-spinner fa-spin mr-1"></i> In Progress &mdash; ITSM
                        </p>
                        <p class="text-gray-600 text-sm leading-relaxed">Working towards the next level of ITIL certification to expand expertise in IT service management and strategic delivery.</p>
                    </div>
                </div>'''

if target in content:
    content = content.replace(target, replacement, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated the certifications section.")
else:
    print("Target string not found in the file.")
