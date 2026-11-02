import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = r'Assistant Professor of Computer & Information Science \| NSF Principal Investigator'
replacement = r'Husband | ' + target

if 'Husband | Assistant' not in content:
    content = content.replace(target, replacement)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated home.html")
else:
    print("Already updated home.html")

