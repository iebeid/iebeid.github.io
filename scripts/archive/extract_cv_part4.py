import zipfile
import xml.etree.ElementTree as ET

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

text = extract_text_from_docx(r'G:\My Drive\Documents\Projects\Career\Curriculum Vitae\CV_Ebeid.docx')
print(text[12000:16000])
