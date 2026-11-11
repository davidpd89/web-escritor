"""Estado de las publicaciones que corren en el equipo de David, para que la autorreparación las vigile.

Los workflows de GitHub dejan su ejecución en Actions; las publicaciones locales (textos SEO a las 21:00, auditoría de
Amazon a las 18:00) solo escribían en su publish.log y nadie miraba si fallaban: del 09/11 al 11/11 los textos fallaron
tres noches seguidas sin que se intentara ningún arreglo. Cada publicación deja aquí un JSON con la forma de una
ejecución de `gh run list` (status, conclusion, createdAt…), más el comando para relanzarla y la cola del registro.
"""
from __future__ import annotations

import datetime as dt, json, os, sys, traceback
from contextlib import contextmanager
from pathlib import Path

ESTADO_DIR = Path(os.environ.get('AUTOREPAIR_ESTADO_DIR') or
                  Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'web-escritor-autorepair')
LOCALES = ESTADO_DIR / 'locales'


def cola(ruta: Path | None, caracteres=20000) -> str:
    try:
        return ruta.read_text(encoding='utf-8', errors='replace')[-caracteres:] if ruta else ''
    except OSError:
        return ''


def escribir(nombre: str, datos: dict, carpeta: Path | None = None):
    carpeta = carpeta or LOCALES
    carpeta.mkdir(parents=True, exist_ok=True)
    tmp = carpeta / f'{nombre}.json.tmp'
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(carpeta / f'{nombre}.json')


def leer(nombre: str, carpeta: Path | None = None) -> dict | None:
    try:
        return json.loads(((carpeta or LOCALES) / f'{nombre}.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


@contextmanager
def vigilado(nombre: str, registro: Path, argv: list[str], cwd: Path, carpeta: Path | None = None):
    """Envuelve una publicación local: en marcha al entrar; éxito o fallo (con la cola del registro) al salir."""
    inicio = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    base = {'nombre': nombre, 'databaseId': f'{nombre}-{inicio}', 'createdAt': inicio, 'url': str(registro),
            'argv': argv, 'cwd': str(cwd), 'registro_ruta': str(registro)}
    escribir(nombre, {**base, 'status': 'in_progress', 'conclusion': None}, carpeta)
    try:
        yield
    except BaseException:
        sys.stdout.flush(); sys.stderr.flush()
        escribir(nombre, {**base, 'status': 'completed', 'conclusion': 'failure',
                          'registro': cola(registro) + '\n' + traceback.format_exc()}, carpeta)
        raise
    escribir(nombre, {**base, 'status': 'completed', 'conclusion': 'success'}, carpeta)
