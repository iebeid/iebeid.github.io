import io
import re

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# find Core Competencies div
match = re.search(r'(<div class="bg-white p-6 rounded-xl shadow-md border border-gray-100">\s*<h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">\s*<i class="fas fa-tools text-sky-600"></i> Core Competencies\s*</h3>\s*<div class="flex flex-wrap">.*?)(</div>)', content, re.DOTALL)

if match:
    tags = match.group(1)
    new_tags = '''<span class="tag">Hibernate</span>
                                <span class="tag">Oracle PL/SQL</span>
                                <span class="tag">ETL & OLAP</span>
                                <span class="tag">webMethods</span>
                                <span class="tag">BSCS</span>
                                <span class="tag">C# / .NET</span>
                                '''
    
    # insert before the closing div
    content = content[:match.end(1)] + new_tags + content[match.end(1):]
    with io.open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Tags added successfully.")
else:
    print("Core Competencies not found.")
