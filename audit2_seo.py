import re, glob

files = glob.glob('**/*.html', recursive=True)
files = [f for f in files if '.git' not in f]

print('=== Images without alt ===')
for f in sorted(files):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    imgs = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
    for img in imgs:
        if 'alt=' not in img.lower():
            print(f'  {f}: {img[:120]}')

print()
print('=== Pages missing meta description ===')
for f in sorted(files):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    if 'name="description"' not in content:
        print(f'  MISSING: {f}')

print()
print('=== Pages missing title ===')
for f in sorted(files):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    if '<title>' not in content:
        print(f'  MISSING: {f}')

print()
print('=== Pages missing canonical ===')
for f in sorted(files):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    if 'canonical' not in content:
        print(f'  MISSING: {f}')

print()
print('=== Pages missing Open Graph og:title ===')
for f in sorted(files):
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    if 'og:title' not in content:
        print(f'  MISSING: {f}')
