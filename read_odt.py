import zipfile
import xml.etree.ElementTree as ET
import sys

def read_odt(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            content_xml = z.read('content.xml')
            root = ET.fromstring(content_xml)
            
            # Simple text extraction
            text = []
            for elem in root.iter():
                if elem.text:
                    text.append(elem.text)
                if elem.tail:
                    text.append(elem.tail)
            return "".join(text)
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
         print(read_odt(sys.argv[1]))
    else:
         print(read_odt('projeto.odt'))
