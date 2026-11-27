"""Presupuesto del sitio publicado (R5-1, .ci/fable-direccion-2026-11-18.md §2.0).

GitHub Pages admite 1 GB por sitio y cada libro añade su ficha. El despliegue mide el artefacto construido y no sube
uno de más de 900 MB; publica la medida como artefacto de Actions «presupuesto-sitio». La carga nocturna la descarga
y solo da de alta los libros que caben por debajo de 850 MB (los de fecha más cercana: los elige
`catalogo_amazon.priorizar`). Sin medida no hay altas: se falla cerrado.

El tope de 250 altas por día (18/11) racionaba el espacio cuando las portadas iban en el artefacto (~100 KB por libro).
Con las portadas en el almacén el freno que importa es el espacio medido: un tope fijo dejaba 9.600 libros ya
encontrados esperando mientras sobraban 400 MB (27/11). Queda como opción: READING_TOPE_ALTAS_DIA=N; vacío o 0 = sin
tope.

    python scripts/presupuesto_sitio.py medir --dist .preview-dist --out presupuesto-sitio.json
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # módulos hermanos también al cargarlo con importlib
import gh_listas  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MB = 1024 * 1024
MAX_MB = 900        # el despliegue falla por encima
FRENO_MB = 850      # la carga deja de dar altas por encima
LEDGER = 'altas-por-dia.json'  # en el estado de la carga (catalogo_estado.FILES)
ARTEFACTO = 'presupuesto-sitio'


def publicados(catalogo):
    return sum(1 for libro in catalogo.get('libros', []) if libro.get('estado') == 'publicado')


def medir(dist, catalogo):
    dist = Path(dist)
    por_carpeta, total, ficheros = {}, 0, 0
    for path in dist.rglob('*'):
        if not path.is_file():
            continue
        size = path.stat().st_size
        rel = path.relative_to(dist).parts
        carpeta = rel[0] if len(rel) > 1 else '.'
        por_carpeta[carpeta] = por_carpeta.get(carpeta, 0) + size
        total += size
        ficheros += 1
    libros = publicados(catalogo)
    return {'bytes': total, 'ficheros': ficheros,
            'por_carpeta': dict(sorted(por_carpeta.items(), key=lambda kv: -kv[1])),
            'libros': libros, 'coste_por_libro': total // libros if libros else 0}


def comprobar(medida, max_mb=MAX_MB):
    if medida['bytes'] > max_mb * MB:
        return [f"El sitio ocupa {medida['bytes'] / MB:.0f} MB (> {max_mb} MB): Pages admite 1 GB"]
    return []


def tope_dia(env=None):
    """Tope opcional de altas por día (READING_TOPE_ALTAS_DIA). None = sin tope; un valor raro también."""
    valor = (os.environ if env is None else env).get('READING_TOPE_ALTAS_DIA', '').strip()
    try:
        n = int(valor)
    except ValueError:
        return None
    return n if n > 0 else None


def por_espacio(medida, libros_ahora, freno_mb=FRENO_MB):
    """Libros que caben por debajo del freno. Los publicados desde la medida cuentan a su coste medio."""
    if not medida or not medida.get('coste_por_libro'):
        return 0
    coste = medida['coste_por_libro']
    estimado = medida['bytes'] + max(0, libros_ahora - medida['libros']) * coste
    return max(0, freno_mb * MB - estimado) // coste


def altas_max(medida, libros_ahora, hechas_hoy, tope=None, freno_mb=FRENO_MB):
    """Libros nuevos que caben hoy: el espacio manda; `tope` (por día, opcional) solo si se pide."""
    libres = por_espacio(medida, libros_ahora, freno_mb)
    return libres if tope is None else max(0, min(tope - hechas_hoy, libres))


CLAVES = ('bytes', 'libros', 'coste_por_libro')


def valida(medida):
    """La medida si trae sus cifras como enteros no negativos; si no, None (sin medida no hay altas)."""
    if not isinstance(medida, dict):
        return None
    for clave in CLAVES:
        valor = medida.get(clave)
        if not isinstance(valor, int) or isinstance(valor, bool) or valor < 0:
            return None
    return medida


def leer_medida(path):
    try:
        return valida(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError, ValueError):
        return None


def ultima_medida(runs=5):
    """La medida del último despliegue terminado que la trae (gh); None si no hay ninguna legible.

    Cuenta también un despliegue fallido: el que no subió por pasar de 900 MB es justo la medida que frena las altas."""
    try:
        def gh(*args):
            return subprocess.run(['gh', *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=60).stdout
        ids = [str(r['databaseId']) for r in gh_listas.ultimas(  # ventana a propósito: los últimos `runs` despliegues
            gh, 'run', 'list', '--workflow', 'deploy-pages.yml', '--status', 'completed', '--json', 'databaseId', n=runs)]
    except (OSError, subprocess.SubprocessError):
        return None
    for run in ids:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                got = subprocess.run(['gh', 'run', 'download', run, '-n', ARTEFACTO, '-D', tmp],
                                     cwd=ROOT, capture_output=True, text=True, timeout=120)
            except (OSError, subprocess.SubprocessError):
                continue
            path = Path(tmp) / f'{ARTEFACTO}.json'
            medida = leer_medida(path) if got.returncode == 0 else None
            if medida:
                return medida
    return None


def _ledger(work):
    """Altas por día. Un fichero ilegible o con cifras raras no tumba la carga: se queda lo válido."""
    try:
        datos = json.loads((Path(work) / LEDGER).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict):
        return {}
    return {dia: n for dia, n in datos.items() if isinstance(n, int) and not isinstance(n, bool) and n >= 0}


def cupo_de_hoy(work, day, libros_ahora):
    medida = ultima_medida()
    tope, hechas = tope_dia(), _ledger(work).get(day, 0)
    libres = por_espacio(medida, libros_ahora)
    cupo = altas_max(medida, libros_ahora, hechas, tope)
    if not medida:
        causa = 'sin medida del último despliegue'
    elif cupo < libres:
        causa = f'tope READING_TOPE_ALTAS_DIA={tope}, hechas hoy {hechas}'
    else:
        causa = f'espacio: {libres} libros caben bajo {FRENO_MB} MB'
    print(f'Presupuesto del sitio: {cupo} altas posibles hoy ({causa})', flush=True)
    return cupo


def anotar(work, day, altas):
    """Suma las altas de la noche; guarda solo los últimos 14 días.

    Se escribe aparte y se sustituye de una vez: un corte a mitad no deja un registro truncado que mañana valdría
    como vacío y doblaría el cupo de la noche."""
    ledger = _ledger(work)
    ledger[day] = ledger.get(day, 0) + altas
    ledger = dict(sorted(ledger.items())[-14:])
    Path(work).mkdir(parents=True, exist_ok=True)
    destino = Path(work) / LEDGER
    tmp = destino.with_name(destino.name + '.tmp')
    tmp.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, destino)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Presupuesto del sitio publicado')
    sub = parser.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('medir')
    m.add_argument('--dist', default='.preview-dist')
    m.add_argument('--catalogo', default=str(ROOT / 'data/reading-catalogue.json'))
    m.add_argument('--out', default=f'{ARTEFACTO}.json')
    m.add_argument('--max-mb', type=int, default=MAX_MB)
    args = parser.parse_args(argv)
    medida = medir(args.dist, json.loads(Path(args.catalogo).read_text(encoding='utf-8')))
    Path(args.out).write_text(json.dumps(medida, indent=2) + '\n', encoding='utf-8')
    print(f"Sitio: {medida['bytes'] / MB:.1f} MB, {medida['ficheros']} ficheros, {medida['libros']} libros, "
          f"{medida['coste_por_libro'] / 1024:.1f} KB por libro")
    errores = comprobar(medida, args.max_mb)
    for error in errores:
        print(f'::error::{error}')
    return 1 if errores else 0


if __name__ == '__main__':
    sys.exit(main())
