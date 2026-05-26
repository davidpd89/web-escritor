"""Art of SEO Ch8 - Site Auditing (pages 410-510, scan key sections)"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    # Read every other page to get a good survey
    pages_to_read = list(range(409, 510, 2))
    for i in pages_to_read:
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            if len(safe.strip()) > 200:
                print(f'=== PAGE {i+1} ===')
                print(safe[:2200])
                print()
