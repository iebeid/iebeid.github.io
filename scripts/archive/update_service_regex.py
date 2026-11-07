import os
import re

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\service\service.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the existing Service Philosophy section
target_pattern = r'<!-- Service Philosophy -->.*?</section>'

philosophy_section = '''<!-- Service Philosophy & Expanding Circles -->
            <section class="bg-white p-8 rounded-xl shadow-md border-l-4 border-sky-600">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-12 h-12 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center text-xl flex-shrink-0">
                        <i class="fas fa-bullseye"></i>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-900">Expanding Circles of Service</h2>
                        <p class="text-sm text-gray-600 mt-0.5">My philosophy on integrating service into academic and intellectual life.</p>
                    </div>
                </div>

                <div class="text-gray-700 space-y-4 text-base leading-relaxed mb-8">
                    <p>
                        I view service not as an extracurricular obligation, but as an deeply integrated dimension of academic and intellectual life. Genuine impact emanates outward through concentric circles of influence. By beginning with those closest to us and expanding outward, we build sustainable, meaningful contributions at every level of society.
                    </p>
                </div>

                <!-- Concentric Circles Vertical Timeline -->
                <div class="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-sky-200 before:to-transparent">
                    
                    <!-- Circle 1 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-sky-600 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            1
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-gray-200 bg-gray-50 shadow-sm">
                            <h3 class="font-bold text-sky-800 text-lg mb-1"><i class="fas fa-chalkboard-teacher mr-2"></i> Class &amp; Research Lab</h3>
                            <p class="text-sm text-gray-600">Dedicating extended time to students through comprehensive office hours and organizing specialized research seminars to foster early inquiry.</p>
                        </div>
                    </div>

                    <!-- Circle 2 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-sky-500 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            2
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-gray-200 bg-gray-50 shadow-sm">
                            <h3 class="font-bold text-sky-700 text-lg mb-1"><i class="fas fa-building mr-2"></i> Department</h3>
                            <p class="text-sm text-gray-600">Participating actively in curriculum development committees and driving departmental recruitment efforts to ensure a robust academic pipeline.</p>
                        </div>
                    </div>

                    <!-- Circle 3 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-sky-500 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            3
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-gray-200 bg-gray-50 shadow-sm">
                            <h3 class="font-bold text-sky-700 text-lg mb-1"><i class="fas fa-university mr-2"></i> Institution</h3>
                            <p class="text-sm text-gray-600">Engaging in campus-wide sustainability initiatives and shaping institutional policy regarding the future of Artificial Intelligence in education.</p>
                        </div>
                    </div>

                    <!-- Circle 4 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-sky-400 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            4
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-gray-200 bg-gray-50 shadow-sm">
                            <h3 class="font-bold text-sky-600 text-lg mb-1"><i class="fas fa-network-wired mr-2"></i> Professional Network</h3>
                            <p class="text-sm text-gray-600">Serving the broader academic community through rigorous peer-review processes, editorial board roles, and conference organization.</p>
                        </div>
                    </div>
                    
                    <!-- Circle 5 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-teal-500 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            5
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-gray-200 bg-gray-50 shadow-sm">
                            <h3 class="font-bold text-teal-700 text-lg mb-1"><i class="fas fa-home mr-2"></i> Home Community</h3>
                            <p class="text-sm text-gray-600">Grounding intellectual work in local realities through active volunteerism, community outreach, and serving on faith organization committees.</p>
                        </div>
                    </div>

                    <!-- Circle 6 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-indigo-600 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            6
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-indigo-200 bg-indigo-50 shadow-sm">
                            <h3 class="font-bold text-indigo-800 text-lg mb-1"><i class="fas fa-flag-usa mr-2"></i> National Level</h3>
                            <p class="text-sm text-gray-700">Advocating for freedom of speech, academic inquiry, and peace. <strong>Crucially:</strong> advising on national security matters regarding the risks of AI, participating in cybersecurity initiatives, and collaborating constructively with government agencies.</p>
                        </div>
                    </div>
                    
                    <!-- Circle 7 -->
                    <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                        <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-white bg-purple-600 text-white font-bold shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                            7
                        </div>
                        <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-purple-200 bg-purple-50 shadow-sm">
                            <h3 class="font-bold text-purple-800 text-lg mb-1"><i class="fas fa-globe-americas mr-2"></i> Global &amp; International</h3>
                            <p class="text-sm text-gray-700">Embracing an overarching responsibility toward the world through writing, international media engagement, attending global conferences, and participating in UN initiatives when called upon.</p>
                        </div>
                    </div>

                </div>
            </section>'''

new_content, count = re.subn(target_pattern, philosophy_section, content, flags=re.DOTALL)

if count > 0:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated service.html")
else:
    print("Failed to replace using regex.")

