import os
import shutil

base_dir = r'G:\My Drive\Documents\Projects\Research\Videos'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\videos'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

copies = [
    (os.path.join(base_dir, 'VisInt-X', 'XLPMinaction.mp4'), 'XLPM-Action.mp4'),
    (os.path.join(base_dir, 'CaveInABox', 'Mar 20, 2017 2_28 PM.webm'), 'CaveInABox.webm'),
    (os.path.join(base_dir, 'Walmart', 'Feb 15, 2017 7_40 PM.webm'), 'Walmart-Vis.webm'),
    (os.path.join(base_dir, 'EyeAdaptUI', 'Scenario1.fxml - SimDirector 6_19_2018 5_06_40 PM.mp4'), 'Eye-Tracking-Sim.mp4')
]

for src, dest_name in copies:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(dest_dir, dest_name))

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

videos_section = '''
            <!-- Section 7: Research Demos & Videos -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-orange-500 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-video text-orange-500 mr-3"></i> Research Demos &amp; Visualizations
                    </h2>
                    <span class="text-xs bg-orange-100 text-orange-800 font-semibold px-2.5 py-1 rounded-full">Recordings</span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <!-- XLPM Video -->
                    <div class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden flex flex-col">
                        <div class="aspect-video bg-black flex items-center justify-center relative">
                            <video controls class="w-full h-full object-cover">
                                <source src="../../videos/XLPM-Action.mp4" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="p-4">
                            <h3 class="font-bold text-gray-900 mb-1">XLPM Perception Metric in Action</h3>
                            <p class="text-sm text-gray-600">Demonstration of the objective image quality assessment metric mapping perceptual errors in real-time.</p>
                        </div>
                    </div>

                    <!-- CAVE in a Box Video -->
                    <div class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden flex flex-col">
                        <div class="aspect-video bg-black flex items-center justify-center relative">
                            <video controls class="w-full h-full object-cover">
                                <source src="../../videos/CaveInABox.webm" type="video/webm">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="p-4">
                            <h3 class="font-bold text-gray-900 mb-1">CAVE-in-a-Box Virtual Reality</h3>
                            <p class="text-sm text-gray-600">Portable and cost-effective Cave Automatic Virtual Environment for immersive 3D data visualization.</p>
                        </div>
                    </div>
                    
                    <!-- Walmart Visualization -->
                    <div class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden flex flex-col">
                        <div class="aspect-video bg-black flex items-center justify-center relative">
                            <video controls class="w-full h-full object-cover">
                                <source src="../../videos/Walmart-Vis.webm" type="video/webm">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="p-4">
                            <h3 class="font-bold text-gray-900 mb-1">Retail Geography Visualization</h3>
                            <p class="text-sm text-gray-600">Visualizing high-dimensional geographic data and store distributions mapping supply chains.</p>
                        </div>
                    </div>

                    <!-- Eye Tracking Sim -->
                    <div class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden flex flex-col">
                        <div class="aspect-video bg-black flex items-center justify-center relative">
                            <video controls class="w-full h-full object-cover">
                                <source src="../../videos/Eye-Tracking-Sim.mp4" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="p-4">
                            <h3 class="font-bold text-gray-900 mb-1">Eye-Tracking Flight Simulation</h3>
                            <p class="text-sm text-gray-600">Capturing gaze transition entropy in flight simulations to construct adaptive user interfaces.</p>
                        </div>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = videos_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Videos section.")
