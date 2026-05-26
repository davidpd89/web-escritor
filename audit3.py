"""Check for common content issues"""
import re, os

pages = ['index.html','autor.html','ferias.html','premios.html','prensa.html',
         'eventos.html','libros/samuel-entre-mundos/index.html',
         'universo/noveris/index.html','fragmento/index.html',
         'clubes-de-lectura/samuel-entre-mundos/index.html',
         'empieza-aqui/index.html']

issues = []
for fname in pages:
    with open(fname, 'r', encoding='utf-8') as f:
        html = f.read()

    if re.search(r'PLACEHOLDER|TODO|FIXME|XXX', html, re.I):
        issues.append(f'{fname}: HAS PLACEHOLDER/TODO')

    internal_links = re.findall(r'href="(/[^"#?]+)"', html)
    for link in internal_links:
        if link.startswith('/assets') or link.startswith('/guias'):
            continue
        local = 'C:/GIT/web-escritor' + link.rstrip('/')
        if not (os.path.exists(local) or os.path.exists(local + '.html') or
                os.path.exists(local + '/index.html') or os.path.exists(local + '/')):
            if not link.startswith('/#') and '.' in link.split('/')[-1]:
                issues.append(f'{fname}: POSSIBLE BROKEN LINK: {link}')

print('Issues found:')
for i in issues:
    print(i)
if not issues:
    print('No issues found')
