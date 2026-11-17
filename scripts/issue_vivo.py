#!/usr/bin/env python3
"""Un solo issue vivo por etiqueta: el aviso de un empleado automático que se lee sin abrir Actions.

Un empleado que solo deja su informe en un artefacto o en el resumen de la ejecución no avisa a nadie: nadie entra
a mirarlo. Con este módulo cada empleado mantiene un issue con su etiqueta: lo abre cuando encuentra algo, lo
actualiza mientras siga encontrándolo y lo cierra cuando vuelve a estar limpio. Nunca abre dos.

Solo publica desde main (o en local, sin GITHUB_REF_NAME): una ejecución despachada desde una rama de prueba no
debe abrir ni cerrar el aviso de main.
"""
import os
import subprocess

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
    abierto = llamar('issue', 'list', '--repo', repo, '--label', etiqueta, '--state', 'open', '--json', 'number',
                     '-q', '.[0].number').stdout.strip()
    cuerpo = recortar(texto)
    if hay_aviso and abierto:
        return llamar('issue', 'edit', abierto, '--repo', repo, '--title', titulo, '--body', cuerpo)
    if hay_aviso:
        return llamar('issue', 'create', '--repo', repo, '--title', titulo, '--body', cuerpo, '--label', etiqueta)
    if abierto:
        return llamar('issue', 'close', abierto, '--repo', repo, '--comment', cierre)
    return None
