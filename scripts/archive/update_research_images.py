import os
import shutil

base_dir = r'G:\My Drive\Documents\Projects\Research\Images'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\images\research'
html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Pick a few distinct images that represent different research tasks
copies = [
    (os.path.join(base_dir, 'MedGraph', 'MedGraphArchitecture.png'), 'MedGraphArchitecture.png'),
    (os.path.join(base_dir, 'EyeAdaptUI', 'heatmap-normal-sus-1.JPG'), 'heatmap-normal-sus-1.jpg'),
    (os.path.join(base_dir, 'ClusterWebGL', 'figure1.png'), 'ClusterWebGL-figure1.png'),
    (os.path.join(base_dir, 'Xlpmol', '3dmol-edited.png'), '3dmol-edited.png')
]

for src, dest_name in copies:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(dest_dir, dest_name))

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

images_section = '''
            <!-- Section 8: Research Image Gallery -->
            <section class="mt-8">
                <div class="flex items-center justify-between border-b-2 border-pink-500 pb-2 mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-camera-retro text-pink-500 mr-3"></i> Research Image Gallery
                    </h2>
                    <span class="text-xs bg-pink-100 text-pink-800 font-semibold px-2.5 py-1 rounded-full">Visualizations</span>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">

                    <!-- MedGraph Architecture -->
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition group">
                        <div class="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                            <img src="../../images/research/MedGraphArchitecture.png" alt="MedGraph Architecture" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                        </div>
                        <div class="p-3 border-t border-gray-100">
                            <h3 class="font-bold text-gray-900 text-sm mb-1 line-clamp-1">MedGraph Architecture</h3>
                            <p class="text-xs text-gray-600 line-clamp-2">Deep learning pipeline for biomedical knowledge graph completion.</p>
                        </div>
                    </div>

                    <!-- Eye-Tracking Heatmap -->
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition group">
                        <div class="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                            <img src="../../images/research/heatmap-normal-sus-1.jpg" alt="Eye-Tracking Heatmap" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                        </div>
                        <div class="p-3 border-t border-gray-100">
                            <h3 class="font-bold text-gray-900 text-sm mb-1 line-clamp-1">Gaze Heatmap</h3>
                            <p class="text-xs text-gray-600 line-clamp-2">Eye-tracking spatial heatmap analysis from flight simulation experiments.</p>
                        </div>
                    </div>
                    
                    <!-- ClusterWebGL Visualization -->
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition group">
                        <div class="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                            <img src="../../images/research/ClusterWebGL-figure1.png" alt="ClusterWebGL" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                        </div>
                        <div class="p-3 border-t border-gray-100">
                            <h3 class="font-bold text-gray-900 text-sm mb-1 line-clamp-1">ClusterWebGL</h3>
                            <p class="text-xs text-gray-600 line-clamp-2">Web-based large-scale biological network and pathway rendering.</p>
                        </div>
                    </div>

                    <!-- XLPMol 3D -->
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition group">
                        <div class="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                            <img src="../../images/research/3dmol-edited.png" alt="XLPMol 3D" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                        </div>
                        <div class="p-3 border-t border-gray-100">
                            <h3 class="font-bold text-gray-900 text-sm mb-1 line-clamp-1">Molecular Structure</h3>
                            <p class="text-xs text-gray-600 line-clamp-2">Interactive 3D molecular structure visualization and rendering.</p>
                        </div>
                    </div>

                </div>
            </section>
'''

target = '''        </div>
    </main>'''

replacement = images_section + "\n" + target

if target in content:
    content = content.replace(target, replacement, 1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated research.html with Images section.")
