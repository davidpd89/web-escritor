"""Art of SEO - read table of contents to map chapter pages"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    total = len(pdf.pages)
    print(f'Total pages: {total}')
    # Read first 20 pages for TOC
    for i in range(20):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            print(f'=== PAGE {i+1} ===')
            print(safe[:3000])
            print()
