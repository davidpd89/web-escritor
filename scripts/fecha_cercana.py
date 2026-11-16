"""Fechas cercanas primero: la única clave de orden por fecha de publicación (altas, sinopsis, auditoría).

Hoy, mañana y pasado; luego el futuro de más cercano a más lejano; luego el pasado de más reciente a más antiguo;
al final lo que no tiene fecha legible (vacía, `None`, texto roto). Acepta fechas de mes (AAAA-MM) y de año (AAAA).
"""
from __future__ import annotations

from datetime import date, timedelta


def periodo(fecha):
    """(primer día, último día) de una fecha completa, de un mes (AAAA-MM) o de un año (AAAA); None si no se lee."""
    try:
        partes = [int(x) for x in str(fecha or '').split('-')[:3]]
        if len(partes) == 3:
            dia = date(*partes)
            return dia, dia
        if len(partes) == 2:
            inicio = date(partes[0], partes[1], 1)
            return inicio, (inicio.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if len(partes) == 1:
            return date(partes[0], 1, 1), date(partes[0], 12, 31)
    except (TypeError, ValueError):
        return None  # fecha imposible (2026-02-30, mes 13): cuenta como ilegible
    return None


def cercania(fecha, hoy):
    """Clave de orden: hoy, mañana y pasado; luego el futuro de más cercano a más lejano; luego el pasado de más
    reciente a más antiguo; al final lo que no tiene fecha legible. Una fecha incompleta (mes o año) cuenta por su
    día más cercano a hoy: «2026-11» un 2 de noviembre es hoy."""
    tramo = periodo(fecha)
    if not tramo:
        return (3, 0)
    inicio, fin = tramo
    if inicio <= hoy <= fin:
        return (0, 0)
    if inicio > hoy:
        dias = (inicio - hoy).days
        return (0 if dias <= 2 else 1, dias)
    return (2, (hoy - fin).days)


def de_libro(book, hoy):
    """`cercania` de un libro: su fecha completa o, si no hay, la parcial (mes o año)."""
    return cercania(book.get('fecha_publicacion') or book.get('fecha_publicacion_parcial'), hoy)
