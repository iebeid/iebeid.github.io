with open('pages/portal/portal.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of pages/portal/portal.html:", len(text))
print(text[:400])
