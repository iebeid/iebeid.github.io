import sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    import pypdf
    p = r'C:\Users\islam\OneDrive\Desktop\All\_Facebook Posts and Attachment Styles_ .pdf'
    reader = pypdf.PdfReader(p)
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    import re
    urls = re.findall(r'facebook\.com/[^\s"\'<>)]*', text, re.I)
    print("Found FB URLs:", set(urls))
    names = re.findall(r'.{0,40}facebook.{0,40}', text, re.I)
    for n in names[:5]:
        print("Context:", n)
except Exception as e:
    print("Error:", e)
