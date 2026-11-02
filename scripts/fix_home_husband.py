import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = r'Assistant Professor of Computer &amp; Information Science \| NSF Principal Investigator \| AI in Life Sciences Researcher \| National Security Advocate \| Islamic Scholar \| Writer \| Educator \| Engineer'
replacement = r'Husband | Assistant Professor of Computer &amp; Information Science | NSF Principal Investigator | AI in Life Sciences Researcher | National Security Advocate | Islamic Scholar | Writer | Educator | Engineer'

if 'Husband | Assistant' not in content:
    content = re.sub(target, replacement, content)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated home.html with Husband")
else:
    print("Already updated home.html")
