import os

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\sitemap.xml'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '<loc>https://iebeid.github.io/pages/home/home.html</loc>' in line:
        skip = True
        # remove the previous <url> tag
        if new_lines and '<url>' in new_lines[-1]:
            new_lines.pop()
        continue
    if skip and '</url>' in line:
        skip = False
        continue
    if not skip:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
