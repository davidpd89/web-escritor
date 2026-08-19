#!/usr/bin/env python3
import re, sys

path = 'herramientas/index.html'
txt = open(path, encoding='utf-8').read()
hrefs = re.findall(r'href=["\']([^"\']+)["\']', txt)
bad = [h for h in hrefs if not (h.startswith('/') or h.startswith('http') or h.startswith('#'))]
if bad:
    print('BAD_HREFS', bad)
    sys.exit(2)
print('HREF-OK')
sys.exit(0)
