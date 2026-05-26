"""Art of SEO Ch2 - Search Fundamentals (pages 74-127)"""
import pdfplumber

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    for i in range(73, 127):  # pages 74-127 (0-indexed 73-126)
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            print(f'=== PAGE {i+1} ===')
            print(safe[:3000])
            print()
