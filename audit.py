"""Audit all HTML files for common issues"""
import re, os

def audit_html(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Corrupted chars (FFFD replacement)
    fffd_count = html.count('\ufffd')
    if fffd_count:
        issues.append(f'  CORRUPTED CHARS: {fffd_count} U+FFFD found')

    # 2. Double-encoded UTF-8 patterns
    bad_chars = [
        ('\u00e2\u20ac\u201d', 'em-dash corrupto'),
        ('\u00e2\u02c6\u2019', 'minus corrupto'),
        ('\u00e2\u20ac\u02dc', 'left-quote corrupto'),
        ('\u00e2\u20ac\u2122', 'right-quote corrupto'),
        ('\u00c3\u00a9', 'e-acute double-enc'),
        ('\u00c3\u00b3', 'o-acute double-enc'),
    ]
    for bad, name in bad_chars:
        cnt = html.count(bad)
        if cnt:
            issues.append(f'  CORRUPTED CHAR: "{name}" x{cnt}')

    # 3. img without alt
    no_alt = re.findall(r'<img(?![^>]*\balt=)[^>]*>', html)
    if no_alt:
        issues.append(f'  IMG NO ALT: {len(no_alt)} images')

    # 4. Empty heading tags
    empty_h = re.findall(r'<h[1-6][^>]*>\s*</h[1-6]>', html)
    if empty_h:
        issues.append(f'  EMPTY HEADINGS: {len(empty_h)}')

    # 5. Missing title
    if '<title>' not in html:
        issues.append('  MISSING <title>')

    # 6. Dagger typo in text
    if '\u2020' in html:
        issues.append('  POSSIBLE TYPO: dagger char \u2020 in HTML')

    # 7. Multiple H1
    h1s = re.findall(r'<h1[^>]*>', html)
    if len(h1s) > 1:
        issues.append(f'  MULTIPLE H1: {len(h1s)}')

    # 8. Long title tag
    title_m = re.search(r'<title>([^<]+)</title>', html)
    if title_m:
        tlen = len(title_m.group(1))
        if tlen > 65:
            issues.append(f'  TITLE TOO LONG: {tlen} chars: {title_m.group(1)[:80]}')

    # 9. Inline event handlers (bad practice)
    inline_events = re.findall(r'on(?:click|load|error)="[^"]{40,}"', html)
    if inline_events:
        issues.append(f'  LONG INLINE HANDLERS: {len(inline_events)}')

    # 10. Target=_blank without rel=noopener
    bad_links = re.findall(r'target="_blank"(?![^>]*rel=["\'][^"\']*noopener)', html)
    if bad_links:
        issues.append(f'  BLANK WITHOUT NOOPENER: {len(bad_links)}')

    # 11. Dead email obfuscation check (data-n + data-d pairs)
    email_links = re.findall(r'href="#"[^>]*data-n=', html)
    # These are fine, just count

    return issues


pages = []
for root, dirs, files in os.walk('C:/GIT/web-escritor'):
    dirs[:] = [d for d in dirs if d not in ['.git', 'assets', 'guias', 'press-kit', 'fonts']]
    for f in files:
        if f.endswith('.html'):
            pages.append(os.path.join(root, f))

for page in sorted(pages):
    rel = page.replace('C:\\GIT\\web-escritor\\', '').replace('C:/GIT/web-escritor/', '')
    issues = audit_html(page)
    if issues:
        print(f'\n=== {rel} ===')
        for i in issues:
            print(i)
    else:
        print(f'OK: {rel}')
