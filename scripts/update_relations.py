import os
import re

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\relations\relations.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Academic, Scholarly & Social Networks section
pattern = r'(<!-- Section 3: Academic, Scholarly & Social Networks.*?)</section>\s*'
match = re.search(pattern, content, re.DOTALL)

if match:
    social_section = match.group(0)
    # Remove it from its current location
    content = content.replace(social_section, '')
    
    # Insert it before the closing </main> tag
    target = '        </div>\n    </main>'
    replacement = social_section + '\n' + target
    
    if target in content:
        content = content.replace(target, replacement, 1)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully moved Academic, Scholarly & Social Networks to the end of relations.html")
    else:
        print("Could not find the target location to insert.")
else:
    print("Could not find the Social Networks section.")
