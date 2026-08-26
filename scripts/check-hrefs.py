#!/usr/bin/env python3
import html
import re, sys

path = 'herramientas/index.html'
txt = open(path, encoding='utf-8').read()
hrefs = re.findall(r'href=["\']([^"\']+)["\']', txt)


def is_allowed(href: str) -> bool:
    if href.startswith(('/', 'http', '#')):
        return True
    # The footer email link is numeric-character-reference obfuscated
    # (&#109;&#97;...) so bots scraping raw HTML can't lift a plain mailto:
    # address; decode before checking so this still validates as a real link.
    decoded = html.unescape(href)
    return decoded.startswith('mailto:')


bad = [h for h in hrefs if not is_allowed(h)]
if bad:
    print('BAD_HREFS', bad)
    sys.exit(2)
print('HREF-OK')
sys.exit(0)
