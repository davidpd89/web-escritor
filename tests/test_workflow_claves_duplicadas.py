"""Ningún workflow repite una clave en el mismo mapa.

PyYAML se queda con la última y no avisa, pero GitHub rechaza el fichero entero
("workflow file issue") y el workflow deja de correr. Pasó al rehacer #1392 sobre
main: `permissions:` acabó con `issues: write` dos veces.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / '.github' / 'workflows').glob('*.y*ml'))


class _SinDuplicados(yaml.SafeLoader):
    pass


def _mapa(loader, node, deep=False):
    vistas = {}
    for clave_nodo, _ in node.value:
        clave = loader.construct_object(clave_nodo, deep=deep)
        if clave in vistas:
            raise yaml.constructor.ConstructorError(
                None, None,
                f'clave duplicada {clave!r} (líneas {vistas[clave] + 1} y {clave_nodo.start_mark.line + 1})',
                clave_nodo.start_mark)
        vistas[clave] = clave_nodo.start_mark.line
    return loader.construct_mapping(node, deep=deep)


_SinDuplicados.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapa)


def test_hay_workflows():
    assert WORKFLOWS


def test_ningun_workflow_repite_claves():
    errores = []
    for ruta in WORKFLOWS:
        try:
            yaml.load(ruta.read_text(encoding='utf-8'), Loader=_SinDuplicados)
        except yaml.YAMLError as exc:
            errores.append(f'{ruta.name}: {exc}')
    assert not errores, '\n'.join(errores)


def test_detecta_la_duplicada():
    texto = 'permissions:\n  issues: write\n  issues: write\n'
    try:
        yaml.load(texto, Loader=_SinDuplicados)
    except yaml.constructor.ConstructorError as exc:
        assert 'issues' in str(exc)
    else:
        raise AssertionError('no detectó la clave duplicada')
