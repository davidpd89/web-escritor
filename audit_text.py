import re, glob

files = glob.glob('**/*.html', recursive=True)
files = [f for f in files if '.git' not in f]

def extract_text(html):
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return re.sub(r'<[^>]+>', ' ', html)

patterns = [
    (r'\baqui\b', 'aqui sin acento'),
    (r'\btambien\b', 'tambien sin acento'),
    (r'\bdemas\b', 'demas sin acento'),
    (r'[a-z]\.[A-Z]', 'falta espacio tras punto'),
]

for f in sorted(files):
    try:
        with open(f, encoding='utf-8') as fh:
            content = fh.read()
        text = extract_text(content)
        for pat, label in patterns:
            for m in re.finditer(pat, text):
                ctx = text[max(0,m.start()-50):m.end()+50].strip().replace('\n',' ')
                if len(ctx) > 5:
                    print(f'{f} | {label}: ...{ctx}...')
    except Exception as e:
        print(f'ERROR {f}: {e}')
