import os
import re

ROOT = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io'

nav_items = [
    ('Home', 'home', 'home.html'),
    ('Relations', 'relations', 'relations.html'),
    ('Education', 'education', 'education.html'),
    ('Research', 'research', 'research.html'),
    ('Scholarship', 'scholarship', 'scholarship.html'),
    ('Teaching', 'teaching', 'teaching.html'),
    ('Service', 'service', 'service.html'),
    ('Business', 'business', 'business.html'),
    ('Hobbies', 'hobbies', 'hobbies.html'),
    ('Media', 'media', 'media.html'),
    ('Downloads', 'downloads', 'downloads.html'),
]

def generate_header(active_folder):
    desktop_links = []
    mobile_links = []
    
    for name, folder, file in nav_items:
        is_active = (folder == active_folder)
        href = f"../{folder}/{file}"
        
        if is_active:
            desktop_links.append(f'<a href="{href}" class="text-sky-600 font-semibold transition">{name}</a>')
            mobile_links.append(f'<a href="{href}" class="block px-3 py-2 text-sky-600 font-semibold bg-sky-50 rounded">{name}</a>')
        else:
            desktop_links.append(f'<a href="{href}" class="text-gray-600 hover:text-sky-600 transition">{name}</a>')
            mobile_links.append(f'<a href="{href}" class="block px-3 py-2 text-gray-600 hover:bg-sky-50 rounded">{name}</a>')
            
    desktop_html = '\n                    '.join(desktop_links)
    mobile_html = '\n                '.join(mobile_links)
    
    return f'''    <!-- Header & Navigation (Templated via js/template.js) -->
    <header id="navbar" class="sticky top-0 bg-white/90 backdrop-blur-sm shadow-lg z-50 transition-all duration-300">
        <div class="container mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex-shrink-0">
                    <a href="../home/home.html" class="flex items-center gap-2.5 sm:gap-3 group">
                        <div class="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full overflow-hidden flex-shrink-0">
                            <img src="../../images/Islamic-Pattern-08-min.jpg" alt="Islamic Pattern Emblem" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-lg sm:text-xl font-bold text-gray-800 group-hover:text-sky-700 transition">Islam Akef Ebeid</span>
                            <img src="../../images/arabic-name.png" alt="Arabic Name" class="inline-block h-7 sm:h-8 ml-0.5">
                        </div>
                    </a>
                </div>
                <nav class="hidden md:flex md:items-center md:space-x-8">
                    {desktop_html}
                </nav>
                <div class="md:hidden flex items-center">
                    <button id="mobile-menu-button" class="text-gray-600 hover:text-gray-900 focus:outline-none" aria-label="Toggle menu">
                        <i class="fas fa-bars text-xl"></i>
                    </button>
                </div>
            </div>
            <!-- Mobile Menu -->
            <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-2 border-t border-gray-100 pt-2">
                {mobile_html}
            </div>
        </div>
    </header>'''

footer_html = '''    <!-- Footer (Templated via js/template.js) -->
    <footer id="footer" class="bg-gray-800 text-white py-6">
        <div class="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p>&copy; <span id="year">2026</span> Islam Akef Ebeid. All Rights Reserved.</p>
        </div>
    </footer>

    <!-- Global Template Engine (Single Source of Truth for Header & Footer) -->
    <script src="../../js/template.js"></script>'''

for name, folder, file in nav_items:
    file_path = os.path.join(ROOT, 'pages', folder, file)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace <header id="navbar" ...> </header>
    header_pattern = re.compile(r'<!--\s*Header & Navigation.*?-->\s*<header id="navbar".*?</header>', re.DOTALL)
    if not header_pattern.search(content):
        header_pattern = re.compile(r'<header id="navbar".*?</header>', re.DOTALL)
        
    new_header = generate_header(folder)
    content, count_h = header_pattern.subn(new_header, content, count=1)
    if count_h == 0:
        print(f"Warning: Could not match header in {file}")

    # 2. Replace Footer and boilerplate script at bottom
    if folder == 'downloads':
        search_script_match = re.search(r'// Real-time Search / Filter functionality.*?(?=</script>)', content, re.DOTALL)
        search_code = search_script_match.group(0) if search_script_match else ''
        custom_footer = footer_html + f'''
    <script>
        {search_code}
    </script>
</body>
</html>'''
        footer_pattern = re.compile(r'<!--\s*Footer.*?-->\s*<footer.*?</html>', re.DOTALL)
        if not footer_pattern.search(content):
            footer_pattern = re.compile(r'<footer.*?</html>', re.DOTALL)
        content, count_f = footer_pattern.subn(custom_footer, content, count=1)
    else:
        full_footer = footer_html + '\n</body>\n</html>'
        footer_pattern = re.compile(r'<!--\s*Footer.*?-->\s*<footer.*?</html>', re.DOTALL)
        if not footer_pattern.search(content):
            footer_pattern = re.compile(r'<footer.*?</html>', re.DOTALL)
        content, count_f = footer_pattern.subn(full_footer, content, count=1)
        
    if count_f == 0:
        print(f"Warning: Could not match footer in {file}")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully templated {file} (folder: {folder})")

print("\nAll 11 pages successfully updated and templated without blue circular line around logo!")
