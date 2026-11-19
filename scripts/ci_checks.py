"""Qué checks de una PR dicen que está rota.

Los revisores externos (DeepSource, SonarCloud, CodeRabbit, Code scanning…) escriben sus propios checks y estados en
cada commit. Son avisos para leer, no la verificación: uno en rojo por estilo no puede cerrar una PR de reparación ni
hacer que un lote verde se descarte y se regenere (14/11: «DeepSource: Python» en rojo en una PR sin cambios de
Python). Cuentan solo:

- Los check runs de GitHub Actions (llevan `workflowName`; los de apps externas no).
- Los estados de commit que escribe el propio publicador (`propios`), p. ej. los REQUIRED_JOBS de un dispatch.
"""
ROJO = {'FAILURE', 'ERROR', 'TIMED_OUT', 'STARTUP_FAILURE', 'ACTION_REQUIRED'}


def nombre(check):
    return check.get('name') or check.get('context') or '?'


def cuenta(check, propios=()):
    """True si el check es de nuestra CI (Actions o un estado propio), no de un revisor externo."""
    if check.get('__typename') == 'StatusContext' or ('context' in check and 'name' not in check):
        return check.get('context') in set(propios)
    return bool(check.get('workflowName'))


def estado(check):
    return (check.get('conclusion') or check.get('state') or '').upper()


def rojos(rollup, propios=(), rojo=ROJO):
    """Nombres de los checks propios en rojo de un `statusCheckRollup`."""
    return sorted({nombre(c) for c in rollup or [] if cuenta(c, propios) and estado(c) in rojo})


def pendientes(rollup, propios=()):
    """Checks propios que aún no han terminado."""
    return [c for c in rollup or [] if cuenta(c, propios)
            and ((c.get('status') or 'COMPLETED').upper() != 'COMPLETED' or estado(c) in ('PENDING', 'EXPECTED', ''))]


def verdes(rollup, propios=()):
    """Nombres de los checks propios que terminaron en verde. Sin ninguno (lista vacía, todo cancelado u omitido) no
    hay prueba de que la PR funcione."""
    return sorted({nombre(c) for c in rollup or [] if cuenta(c, propios) and estado(c) == 'SUCCESS'})
