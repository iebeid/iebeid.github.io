import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = tree.findall('.//w:t', ns)
            return ' '.join([t.text for t in texts if t.text])
    except Exception as e:
        return str(e)

files = [
    r'G:\My Drive\Documents\Projects\Career\Biosketch\portfolio.txt',
    r'G:\My Drive\Documents\Projects\Career\Biosketch\job-list.txt',
    r'G:\My Drive\Documents\Projects\Career\Biosketch\biography.docx',
    r'G:\My Drive\Documents\Projects\Career\Biosketch\professional-narrative.docx',
    r'G:\My Drive\Documents\Projects\Career\Biosketch\Dr.docx'
]

for f in files:
    print(f'--- {os.path.basename(f)} ---')
    if f.endswith('.txt'):
        try:
            with open(f, 'r', encoding='utf-8') as txt_file:
                print(txt_file.read()[:2000])
        except Exception as e:
            print(f"Error reading txt: {e}")
    else:
        print(extract_text_from_docx(f)[:2000])
    print('...\n')
