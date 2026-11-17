#!/usr/bin/env python3
"""Registro y latido de los empleados automáticos (los workflows y las apps que revisan la web).

Un empleado es un workflow de .github/workflows o una app externa (CodeRabbit, SonarCloud…). El registro
data/expertos.json dice a qué departamento pertenece cada uno; el latido mira en GitHub cuándo fichó por última
vez y cómo le fue. Nace de dos semanas de fallos que nadie veía: un vigilante que lleva días rojo o que dejó de
ejecutarse no vigila nada, y hasta ahora no había dónde verlo.

    python scripts/empleados_latido.py registro            # sin red: registro y workflows cuadran
    python scripts/empleados_latido.py latido --salida F   # con gh: informe en markdown del estado real
    python scripts/empleados_latido.py latido --issue      # además abre, actualiza o cierra el issue «latido»

Estados: ok · inestable (última ejecución roja) · rojo (RACHA o más rojas seguidas) · ausente (tiene horario y
no ha fichado en su plazo) · por PR (solo corre en PR: su estado se ve en cada PR, aquí no se juzga).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import issue_vivo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = ROOT / 'data' / 'expertos.json'
WORKFLOWS = ROOT / '.github' / 'workflows'
RACHA = 3  # rojas seguidas para dar a un empleado por caído; una sola puede ser la red
ETIQUETA = 'latido'
# Ejecuciones que no dicen nada del empleado: las canceló otra más nueva o no llegó a correr.
SIN_VEREDICTO = {'cancelled', 'skipped', 'neutral', 'stale', None}


def cargar_registro(ruta=REGISTRO):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def workflows_del_repo(carpeta=WORKFLOWS):
    """{nombre sin extensión: {'crons': [...], 'eventos': {...}}} leído de los propios ficheros."""
    encontrados = {}
    for fichero in sorted(Path(carpeta).glob('*.y*ml')):
        texto = fichero.read_text(encoding='utf-8')
        bloque = re.search(r'^(?:on|"on"|\'on\'):(.*?)(?=^\S|\Z)', texto, re.M | re.S)
        cuerpo = bloque.group(1) if bloque else ''
        eventos = set(re.findall(r'^  ([a-z_]+):', cuerpo, re.M)) or set(re.findall(r'[a-z_]+', cuerpo))
        encontrados[fichero.stem] = {'fichero': fichero.name, 'eventos': eventos,
                                     'crons': re.findall(r'cron:\s*[\'"]([^\'"]+)', cuerpo)}
    return encontrados


def plazo_dias(crons):
    """Días que puede pasar sin fichar: None sin horario, 2 si corre a diario, 9 si es semanal, 35 si mensual."""
    if not crons:
        return None
    plazos = []
    for cron in crons:
        campos = cron.split()
        if len(campos) != 5:
            continue
        _minuto, _hora, dia_mes, _mes, dia_semana = campos
        plazos.append(9 if dia_semana != '*' else 35 if dia_mes != '*' else 2)
    return min(plazos) if plazos else None


def fallos_registro(registro, workflows):
    """Lista de textos con lo que no cuadra entre el registro y el repositorio; vacía si todo cuadra."""
    fallos, asignados, vistos = [], set(), set()
    for dep in registro.get('departamentos', []):
        ident = dep.get('id', '?')
        if ident in vistos:
            fallos.append(f'departamento repetido: {ident}')
        vistos.add(ident)
        if not dep.get('nombre') or not dep.get('mision'):
            fallos.append(f'{ident}: falta nombre o misión')
        if not (dep.get('workflows') or dep.get('externos')) and not dep.get('vacante'):
            fallos.append(f'{ident}: sin empleados y sin «vacante» que diga por qué')
        for nombre in dep.get('workflows', []):
            asignados.add(nombre)
            if nombre not in workflows:
                fallos.append(f'{ident}: el workflow «{nombre}» no existe en .github/workflows')
        for item in dep.get('descartados', []) + dep.get('pendientes', []) + dep.get('cubiertos', []):
            if not item.get('herramienta') or not item.get('motivo'):
                fallos.append(f'{ident}: descartado, pendiente o cubierto sin herramienta o sin motivo')
    for nombre in sorted(set(workflows) - asignados):
        fallos.append(f'el workflow «{nombre}» no tiene departamento: añádelo a data/expertos.json')
    for nombre, dias in registro.get('plazos', {}).items():
        if nombre not in workflows:
            fallos.append(f'plazos: el workflow «{nombre}» no existe')
        elif not isinstance(dias, int) or dias < 1:
            fallos.append(f'plazos: «{nombre}» necesita un número entero de días')
    return fallos


def juzgar(ejecuciones, plazo, ahora):
    """Estado de un empleado con sus ejecuciones completadas fuera de PR, de la más nueva a la más vieja."""
    validas = [e for e in ejecuciones if e.get('conclusion') not in SIN_VEREDICTO]
    ultima = validas[0] if validas else None
    racha = 0
    for ejecucion in validas:
        if ejecucion['conclusion'] == 'success':
            break
        racha += 1
    exito = next((e for e in validas if e['conclusion'] == 'success'), None)
    datos = {'ultima': ultima and ultima['fecha'], 'exito': exito and exito['fecha'], 'racha': racha,
             'url': ultima and ultima.get('url')}
    if plazo and (not ultima or ahora - ultima['fecha'] > timedelta(days=plazo)):
        return 'ausente', datos
    if not ultima:
        return 'por PR', datos
    if racha >= RACHA or (racha and racha == len(validas) and len(validas) >= 2):
        return 'rojo', datos
    return ('inestable' if racha else 'ok'), datos


def ejecuciones_de(fichero, repo):
    """Últimas ejecuciones completadas en main, con gh.

    Se pide solo la rama main: sin ese filtro, las ejecuciones de las PR abiertas llenan la página
    y un workflow programado que sí ficha parece ausente."""
    salida = subprocess.run(
        ['gh', 'api', f'repos/{repo}/actions/workflows/{fichero}/runs?per_page=30&status=completed&branch=main',
         '-q', '.workflow_runs[] | [.event, .conclusion, .updated_at, .html_url, .head_branch] | @tsv'],
        capture_output=True, text=True, encoding='utf-8', check=False)
    if salida.returncode:
        raise RuntimeError(f'gh no pudo leer {fichero}: {salida.stderr.strip()[:200]}')
    filas = []
    for linea in salida.stdout.splitlines():
        evento, conclusion, fecha, url, rama = (linea.split('\t') + [''] * 5)[:5]
        if evento in ('pull_request', 'pull_request_target') or (evento == 'workflow_dispatch' and rama != 'main'):
            continue
        filas.append({'conclusion': conclusion or None, 'url': url,
                      'fecha': datetime.fromisoformat(fecha.replace('Z', '+00:00'))})
    return filas


def medir(registro, workflows, repo, ahora=None, leer=ejecuciones_de):
    ahora = ahora or datetime.now(timezone.utc)
    filas = []
    for dep in registro['departamentos']:
        for nombre in dep.get('workflows', []):
            info = workflows[nombre]
            plazo = registro.get('plazos', {}).get(nombre) or plazo_dias(info['crons'])
            if f"/{info['fichero']}@" in os.environ.get('GITHUB_WORKFLOW_REF', ''):
                # Quien pasa lista está trabajando ahora mismo: no puede darse por ausente a sí mismo.
                filas.append({'departamento': dep['nombre'], 'workflow': nombre, 'estado': 'ok', 'plazo': plazo,
                              'ultima': ahora, 'exito': ahora, 'racha': 0, 'url': None})
                continue
            try:
                estado, datos = juzgar(leer(info['fichero'], repo), plazo, ahora)
            except RuntimeError as error:  # un workflow ilegible no deja a los demás sin informe
                estado, datos = 'sin datos', {'ultima': None, 'exito': None, 'racha': 0, 'url': None,
                                              'error': str(error)}
            filas.append({'departamento': dep['nombre'], 'workflow': nombre, 'estado': estado, 'plazo': plazo, **datos})
    return filas


def dia(fecha):
    return fecha.strftime('%d/%m %H:%M') if fecha else '—'


def informe(filas, registro, ahora=None):
    ahora = ahora or datetime.now(timezone.utc)
    malos = [f for f in filas if f['estado'] in ('rojo', 'ausente', 'sin datos')]
    flojos = [f for f in filas if f['estado'] == 'inestable']
    cuenta = {}
    for fila in filas:
        cuenta[fila['estado']] = cuenta.get(fila['estado'], 0) + 1
    lineas = [f'# Latido de empleados · {ahora:%Y-%m-%d %H:%M} UTC', '',
              f'{len(filas)} empleados en {len(registro["departamentos"])} departamentos: '
              + ', '.join(f'{n} {estado}' for estado, n in sorted(cuenta.items())) + '.', '']
    for titulo, grupo in (('Caídos o sin fichar', malos), ('Última ejecución roja', flojos)):
        if not grupo:
            continue
        lineas += [f'## {titulo}', '', '| Departamento | Empleado | Estado | Rojas seguidas | Último éxito | Última |',
                   '|---|---|---|---|---|---|']
        for f in sorted(grupo, key=lambda f: (f['departamento'], f['workflow'])):
            enlace = f'[{dia(f["ultima"])}]({f["url"]})' if f.get('url') else dia(f['ultima'])
            lineas.append(f'| {f["departamento"]} | `{f["workflow"]}` | {f["estado"]} | {f["racha"]} | '
                          f'{dia(f["exito"])} | {enlace} |')
        lineas.append('')
    if not malos and not flojos:
        lineas += ['Todos los empleados con ejecuciones propias están en verde.', '']
    lineas += ['## Plantilla', '', '| Departamento | Empleados | ok | por PR | Apps externas | Vacantes y pendientes |',
               '|---|---|---|---|---|---|']
    for dep in registro['departamentos']:
        suyos = [f for f in filas if f['departamento'] == dep['nombre']]
        huecos = [p['herramienta'] for p in dep.get('pendientes', [])] + (['vacante'] if dep.get('vacante') else [])
        lineas.append(f'| {dep["nombre"]} | {len(suyos)} | {sum(f["estado"] == "ok" for f in suyos)} | '
                      f'{sum(f["estado"] == "por PR" for f in suyos)} | {", ".join(dep.get("externos", [])) or "—"} | '
                      f'{", ".join(huecos) or "—"} |')
    return '\n'.join(lineas) + '\n', malos


def gh(*args):
    return issue_vivo.gh(*args)


def publicar_issue(texto, malos, repo):
    """Un solo issue vivo con la etiqueta: se actualiza mientras haya caídos y se cierra cuando no queda ninguno."""
    return issue_vivo.publicar(ETIQUETA, f'Latido: {len(malos)} empleados caídos o sin fichar', texto, bool(malos),
                               repo, 'Todos los empleados vuelven a fichar en verde.',
                               'Empleados automáticos caídos o sin fichar')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('orden', choices=('registro', 'latido'))
    parser.add_argument('--salida')
    parser.add_argument('--issue', action='store_true')
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    args = parser.parse_args(argv)
    registro, workflows = cargar_registro(), workflows_del_repo()
    fallos = fallos_registro(registro, workflows)
    for fallo in fallos:
        print(f'registro: {fallo}', file=sys.stderr)
    if args.orden == 'registro' or fallos:
        print(f'registro: {len(workflows)} workflows, {len(registro["departamentos"])} departamentos, '
              f'{len(fallos)} fallos')
        return 1 if fallos else 0
    if not args.repo:
        args.repo = gh('repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').stdout.strip()
    filas = medir(registro, workflows, args.repo)
    texto, malos = informe(filas, registro)
    if args.salida:
        Path(args.salida).write_text(texto, encoding='utf-8', newline='\n')
    else:
        print(texto)
    if args.issue:
        resultado = publicar_issue(texto, malos, args.repo)
        if resultado is not None and resultado.returncode:
            print(f'latido: no se pudo publicar el issue: {resultado.stderr.strip()[:300]}', file=sys.stderr)
            return 1
    return 0  # el latido informa; quien falla es el empleado caído, no el que pasa lista


if __name__ == '__main__':
    raise SystemExit(main())
