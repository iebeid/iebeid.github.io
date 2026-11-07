import os
import shutil

base_dir = r'G:\My Drive\Documents\Projects\Research\Images'
dest_dir = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\images\research'

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

copies = [
    (os.path.join(base_dir, 'MedGraph', 'knowledge-graph.jpg'), 'MedGraphArchitecture.png'),
    (os.path.join(base_dir, 'EyeAdaptUI', 'Assets', 'heatmap-normal-sus-1.JPG'), 'heatmap-normal-sus-1.jpg'),
    (os.path.join(base_dir, 'VisInt-X', 'figure1.png'), 'ClusterWebGL-figure1.png'),
    (os.path.join(base_dir, 'VisInt-X', '3dmol-edited.png'), '3dmol-edited.png')
]

for src, dest_name in copies:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(dest_dir, dest_name))
        print(f"Copied {src} to {dest_name}")
    else:
        print(f"File not found: {src}")

