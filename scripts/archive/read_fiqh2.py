import zipfile
import xml.etree.ElementTree as ET
import sys

def extract_text(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for paragraph in tree.findall('.//w:p', namespaces):
            texts = [node.text for node in paragraph.findall('.//w:t', namespaces) if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        return str(e)
text = extract_text(r'G:\My Drive\Documents\Projects\Scholarship\Manuscripts\Fiqh\imams.docx')
sys.stdout.buffer.write(text.encode('utf-8'))
