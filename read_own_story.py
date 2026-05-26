"""Read Own Your Story PDF - check if relevant for David"""
import pdfplumber

with pdfplumber.open('guias/Own Your Story.pdf') as pdf:
    total = len(pdf.pages)
    print(f'Total pages: {total}')
    # Read first 15 pages to understand topic
    for i in range(min(15, total)):
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            print(f'=== PAGE {i+1} ===')
            print(text[:2000])
            print()
