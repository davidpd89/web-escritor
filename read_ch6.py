"""Art of SEO Ch6 - Technical SEO & Analytics (pages 270-304)"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    for i in range(269, 305):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            print(f'=== PAGE {i+1} ===')
            print(safe[:3000])
            print()
