"""Art of SEO Ch7 - Algorithm Updates (pages 305-409, scan key sections)"""
import pdfplumber

# Read every 3rd page to get a survey of the chapter's content
with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    pages_to_read = list(range(304, 409, 2))  # every other page
    for i in pages_to_read:
        text = pdf.pages[i].extract_text()
        if text and text.strip():
            safe = text.encode('ascii', 'replace').decode('ascii')
            # Only print pages with substantive content (headings/concepts)
            if len(safe.strip()) > 200:
                print(f'=== PAGE {i+1} ===')
                print(safe[:2000])
                print()
