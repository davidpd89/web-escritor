#!/usr/bin/env python3
import re, json, sys

def validate_file(path):
    with open(path, encoding='utf8') as f:
        s = f.read()
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', s, flags=re.I)
    ok = True
    for i, b in enumerate(blocks, 1):
        try:
            json.loads(b)
        except Exception as e:
            print(f'JSON-LD parse error in {path} block {i}:', e)
            ok = False
    if ok:
        print(f'JSON-LD OK: {path}')
    return ok

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: validate_jsonld.py <file1> [file2 ...]')
        sys.exit(2)
    overall = True
    for p in sys.argv[1:]:
        ok = validate_file(p)
        overall = overall and ok
    sys.exit(0 if overall else 1)
