import os

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\business\business.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find out how the business.html looks in full.
print(content[8000:15000])

