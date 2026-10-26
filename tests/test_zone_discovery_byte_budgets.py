from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = {
    'robots.txt': 16 * 1024,
    'sitemap.xml': 512 * 1024,
    'cuaderno/feed.xml': 256 * 1024,
}


def main():
    errors = []
    for relative, maximum in BUDGETS.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f'{relative}: artefacto público inexistente')
            continue
        actual = path.stat().st_size
        if actual > maximum:
            errors.append(f'{relative}: {actual} bytes; presupuesto máximo {maximum} bytes; exceso {actual - maximum} bytes')
        else:
            print(f'OK {relative}: {actual}/{maximum} bytes')
    assert not errors, '\n'.join(errors)
    print('PASS: presupuestos de documentos de descubrimiento')


if __name__ == '__main__':
    main()
