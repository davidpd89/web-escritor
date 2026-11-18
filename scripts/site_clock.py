#!/usr/bin/env python3
"""Canonical civil clock for date-sensitive public content."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SITE_TIMEZONE = "Europe/Madrid"
_SITE_ZONE = ZoneInfo(SITE_TIMEZONE)
# R5-13: el despliegue fija el día una vez (fecha de Madrid) y toda la cadena de materializar lo hereda; así la CI
# puede construir «mañana» y el deploy no mezcla dos días si la cadena cruza la medianoche.
DIA_FIJADO = "CATALOGO_HOY"


def dia_fijado(entorno=None) -> date | None:
    """El día fijado por el despliegue (CATALOGO_HOY) o None. Mal escrito aborta (ValueError): nunca otro día."""
    valor = (os.environ if entorno is None else entorno).get(DIA_FIJADO, "")
    return date.fromisoformat(valor) if valor else None


def site_today(now: datetime | None = None) -> date:
    """Return the site's civil date in Europe/Madrid.

    Única lectura del reloj en la cadena de construcción (guarda AST en tests/test_reading_dia_despliegue.py).
    Sin `now`, manda el día fijado por el despliegue. Tests may inject an aware datetime to exercise
    UTC/day-boundary and DST transitions deterministically.
    """
    if now is None:
        fijado = dia_fijado()
        if fijado:
            return fijado
        now = datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("site_today() requires an aware datetime")
    return now.astimezone(_SITE_ZONE).date()


# Fallo de clase «reloj» (16/11): cuando una ficha cruzaba un umbral de fecha,
# toda PR quedaba roja hasta que radar-clock-refresh regeneraba, y ese cron se
# retrasa horas. Las comprobaciones de PR aceptan generados de hasta
# GRACIA_DIAS días atrás; quien decide refrescar y la auditoría postdeploy
# usan RELOJ_ESTRICTO=1 (solo hoy), así la frescura sigue vigilada.
GRACIA_DIAS = 2


def clock_window(now: datetime | None = None) -> list[date]:
    """Fechas civiles aceptables para generados que dependen del reloj, hoy primero."""
    today = site_today(now)
    if os.environ.get("RELOJ_ESTRICTO") == "1":
        return [today]
    return [today - timedelta(days=n) for n in range(GRACIA_DIAS + 1)]
