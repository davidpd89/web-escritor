#!/usr/bin/env python3
"""Un solo issue vivo por etiqueta: el aviso de un empleado automático que se lee sin abrir Actions.

Un empleado que solo deja su informe en un artefacto o en el resumen de la ejecución no avisa a nadie: nadie entra
a mirarlo. Con este módulo cada empleado mantiene un issue con su etiqueta: lo abre cuando encuentra algo, lo
actualiza mientras siga encontrándolo y lo cierra cuando vuelve a estar limpio. Nunca abre dos.

Solo publica desde main (o en local, sin GITHUB_REF_NAME): una ejecución despachada desde una rama de prueba no
debe abrir ni cerrar el aviso de main.

Desde un workflow en bash:
    python scripts/issue_vivo.py --etiqueta X --titulo T --cuerpo informe.md --aviso 1 --cierre "Limpio."
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh_listas  # noqa: E402

LIMITE_CUERPO = 60000  # GitHub rechaza cuerpos de más de 65.536 caracteres


def gh(*args):
    return subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', check=False)


def desde_main(entorno=None):
    entorno = os.environ if entorno is None else entorno
    return entorno.get('GITHUB_REF_NAME', 'main') == 'main'


def recortar(texto):
    if len(texto) <= LIMITE_CUERPO:
        return texto
    return texto[:LIMITE_CUERPO] + '\n\n…recortado: el informe completo está en el artefacto de la ejecución.\n'


def publicar(etiqueta, titulo, texto, hay_aviso, repo, cierre, descripcion='', color='B60205', llamar=gh,
             entorno=None):
    """Abre, actualiza o cierra el issue con `etiqueta`. Devuelve el CompletedProcess de la última orden o None."""
    if not desde_main(entorno):
        return None
    llamar('label', 'create', etiqueta, '--repo', repo, '--color', color, '--force', '--description', descripcion)
    # Ventana de 1 a propósito: solo importa si hay alguna abierta con la etiqueta.
    abiertas = gh_listas.ultimas(lambda *a: llamar(*a).stdout, 'issue', 'list', '--repo', repo, '--label', etiqueta,
                                 '--state', 'open', '--json', 'number', n=1)
    abierto = str(abiertas[0]['number']) if abiertas else ''
    cuerpo = recortar(texto)
    if hay_aviso and abierto:
        return llamar('issue', 'edit', abierto, '--repo', repo, '--title', titulo, '--body', cuerpo)
    if hay_aviso:
        return llamar('issue', 'create', '--repo', repo, '--title', titulo, '--body', cuerpo, '--label', etiqueta)
    if abierto:
        return llamar('issue', 'close', abierto, '--repo', repo, '--comment', cierre)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Abre, actualiza o cierra el issue vivo de una etiqueta.')
    parser.add_argument('--etiqueta', required=True)
    parser.add_argument('--titulo', required=True)
    parser.add_argument('--cuerpo', required=True, help='fichero markdown')
    parser.add_argument('--aviso', choices=('0', '1'), required=True, help='1 = hay algo que avisar')
    parser.add_argument('--cierre', required=True, help='comentario al cerrar')
    parser.add_argument('--descripcion', default='')
    parser.add_argument('--color', default='B60205')
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    args = parser.parse_args(argv)
    texto = Path(args.cuerpo).read_text(encoding='utf-8') if Path(args.cuerpo).exists() else 'Sin informe.'
    resultado = publicar(args.etiqueta, args.titulo, texto, args.aviso == '1', args.repo, args.cierre,
                         args.descripcion, args.color)
    if resultado is not None and resultado.returncode:
        print(f'issue_vivo: no se pudo publicar: {resultado.stderr.strip()[:300]}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
