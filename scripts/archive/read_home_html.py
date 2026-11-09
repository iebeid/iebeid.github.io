import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('pages/home/home.html', 'r', encoding='utf-8') as f:
    home_html = f.read()

print("Length of pages/home/home.html:", len(home_html))
print("Content of pages/home/home.html:")
print(home_html)
