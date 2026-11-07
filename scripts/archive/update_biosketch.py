import io
import re

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update 2003-2008 NCEES FE exam
old_bs = '<p><span class="font-semibold text-gray-800">Aug 2003 – Jul 2008:</span> Earned <strong>B.Sc. in Electrical & Computer Engineering</strong> from <strong>Ain Shams University</strong> with a <em>Distinctive Capstone Project Award</em> for an Intersection Collision Avoidance System (ICAS).</p>'
new_bs = '<p><span class="font-semibold text-gray-800">Aug 2003 – Jul 2008:</span> Earned <strong>B.Sc. in Electrical & Computer Engineering</strong> from <strong>Ain Shams University</strong> with a <em>Distinctive Capstone Project Award</em> for an Intersection Collision Avoidance System (ICAS) and passed the international NCEES Fundamentals of Engineering (FE) examination.</p>'
content = content.replace(old_bs, new_bs)

# Update EAC / VR section
old_eac = '<p><span class="font-semibold text-gray-800">October 2016:</span> Research on multi-projector auto-calibration algorithms at the <strong>Emerging Analytics Center (EAC)</strong>; published <strong>XLPM / VisInt-X</strong> in <em>IS&T Electronic Imaging (EI 2016)</em> and <em>MCBIOS (2015–2016)</em>.</p>'
new_eac = '<p><span class="font-semibold text-gray-800">2015 – 2016:</span> Researcher at the <strong>Emerging Analytics Center (EAC)</strong> developing immersive CAVE Virtual Reality applications, including <strong>CAVE Fluid Simulation</strong>, <strong>Endoscope SLAM</strong>, <strong>RealSense/Kinect 3D Reconstruction</strong>, <strong>EmotivVR</strong>, and <strong>Leap Motion Interfaces</strong>. Presented work at <strong>SIGGRAPH 2015</strong>, <strong>NVIDIA GDC</strong>, and <strong>ICAT</strong>; published <strong>XLPM / VisInt-X</strong> in <em>IS&T Electronic Imaging (EI 2016)</em> and <em>MCBIOS</em>.</p>'
content = content.replace(old_eac, new_eac)

# Update core tags with VR and Graphics specific terms
match = re.search(r'(<div class="bg-white p-6 rounded-xl shadow-md border border-gray-100">\s*<h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">\s*<i class="fas fa-tools text-sky-600"></i> Core Competencies\s*</h3>\s*<div class="flex flex-wrap">.*?)(</div>)', content, re.DOTALL)
if match:
    tags = match.group(1)
    new_tags = '''<span class="tag">Virtual Reality (VR)</span>
                                <span class="tag">CAVE Systems</span>
                                <span class="tag">CUDA</span>
                                <span class="tag">WebGL</span>
                                <span class="tag">SLAM</span>
                                <span class="tag">3D Reconstruction</span>
                                '''
    content = content[:match.end(1)] + new_tags + content[match.end(1):]

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated home.html with Biosketch info.")
