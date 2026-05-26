"""Art of SEO Ch5 - Keyword Research (pages 209-269)"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    for i in range(208, 269):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            print(f'=== PAGE {i+1} ===')
            print(safe[:2500])
            print()
