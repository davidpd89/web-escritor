"""Art of SEO - find all chapter headings to build chapter map"""
import pdfplumber, re

with pdfplumber.open('guias/Art-of-SEO.pdf') as pdf:
    total = len(pdf.pages)
    # Find chapter headings by looking for "CHAPTER" text
    for i in range(total):
        text = pdf.pages[i].extract_text()
        if not text:
            continue
        if re.search(r'^CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|\d+)', text, re.M | re.I):
            lines = text.splitlines()
            for j, line in enumerate(lines[:5]):
                if re.search(r'CHAPTER', line, re.I):
                    print(f'Page {i+1}: {line.strip()} | {lines[j+1].strip() if j+1 < len(lines) else ""}')
                    break
