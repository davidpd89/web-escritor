"""Art of SEO Ch3 - Your SEO Toolbox (pages 128-172)"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    for i in range(127, 172):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            print(f'=== PAGE {i+1} ===')
            print(safe[:3000])
            print()
