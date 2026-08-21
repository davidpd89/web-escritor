import hashlib, json, pathlib, re, sys, zipfile

path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'qa-artifacts/press-kit-qa.zip')
assert path.is_file(), f'ZIP no encontrado: {path}'

with zipfile.ZipFile(path) as z:
    assert z.testzip() is None, 'ZIP corrupto'
    names = z.namelist()
    required = {
        'README.txt','datos/autor.json','datos/libro.json',
        'textos/biografia-corta.txt','textos/sinopsis.txt',
        'PERMISOS_ASSETS.txt','MANIFEST.json','CHECKSUMS_SHA256.txt'
    }
    missing = required.difference(names)
    assert not missing, f'faltan: {sorted(missing)}'
    assert all(not n.startswith(('/', '\\')) for n in names), 'ruta absoluta'
    assert all('..' not in pathlib.PurePosixPath(n).parts for n in names), 'path traversal'
    assert all('\\' not in n for n in names), 'separador inseguro'
    assert all('\x00' not in n for n in names), 'NUL en nombre'
    assets = [n for n in names if n.startswith('assets/')]
    assert len(assets) >= 4, f'assets insuficientes: {assets}'
    assert len(assets) == len(set(assets)), 'nombres duplicados'
    assert all(pathlib.PurePosixPath(n).suffix.lower() in {'.jpg','.png','.webp','.pdf'} for n in assets), f'extensión insegura: {assets}'
    assert not any(n.lower().endswith(('.html','.htm','.svg','.js')) for n in assets), f'asset ejecutable: {assets}'
    assert any(re.search(r'cover-portada-nandu(?:-2)?\.webp$', n) for n in assets), assets
    assert any(re.search(r'cover-portada-nandu-2\.webp$', n) for n in assets), assets
    assert any(n.endswith('author-ana-nandu.jpg') for n in assets), assets  # el fixture original se llama .html pero MIME=image/jpeg
    assert any(n.endswith('other-dossier.pdf') for n in assets), assets

    author = json.loads(z.read('datos/autor.json'))
    book = json.loads(z.read('datos/libro.json'))
    assert author['name'] == 'Ana Ejemplo'
    assert author['pressContact'] == 'prensa@example.test'
    assert book['title'] == 'La casa de prueba'
    assert book['publisher'] == 'Editorial Ejemplo'
    assert book['isbn'] == '9781234567890'
    assert book['publicationDate'] == '2026-09-03'
    assert book['price'] == '16 €'
    assert 'LOCAL_QA_SENTINEL_582931' in book['description']

    manifest = json.loads(z.read('MANIFEST.json'))
    assert manifest['author'] == 'Ana Ejemplo'
    assert manifest['book'] == 'La casa de prueba'
    manifest_paths = {x['path'] for x in manifest['files']}
    assert all(n in manifest_paths for n in assets)

    checksum_text = z.read('CHECKSUMS_SHA256.txt').decode('utf-8')
    checksums = {}
    for line in checksum_text.splitlines():
        digest, name = line.split('  ', 1)
        checksums[name] = digest
    assert 'MANIFEST.json' in checksums
    target = assets[0]
    actual = hashlib.sha256(z.read(target)).hexdigest()
    assert checksums[target] == actual, f'checksum incorrecto: {target}'
    for name, digest in checksums.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == digest, f'checksum incorrecto: {name}'

    readme = z.read('README.txt').decode('utf-8')
    assert 'Ana Ejemplo' in readme and 'La casa de prueba' in readme
    assert 'textos/biografia-corta.txt' in readme
    assert z.read('textos/biografia-corta.txt').decode('utf-8').strip()
    assert 'LOCAL_QA_SENTINEL_582931' in z.read('textos/sinopsis.txt').decode('utf-8')
    assert z.read('PERMISOS_ASSETS.txt').decode('utf-8').strip()

print('PRESS KIT ZIP QA: OK')
