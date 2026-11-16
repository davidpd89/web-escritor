#!/usr/bin/env python3
"""¿Carga este reloj de la ingesta nocturna? (cron 00:17/01:47/03:17 UTC o dispatch `respaldo=true`)

Decide con el libro de la noche (`noche.json` en la rama `catalogo-estado`, scripts/noche.py), el mismo registro
que leen el reintento y la cadena, y no con listas de ejecuciones de Actions (Fable R4-1, F1: el juez contaba desde
las 00:00 UTC y el reintento desde la medianoche de Madrid, y las listas se truncaban en noches largas).

Solo descarta lo evidente (R5-9): no carga si esta noche (día de Madrid) la última terminó publicada o degradada,
o si ya van 3 fallidas. Una carga en curso o un despacho pendiente los resuelve el job `intake` con el turno. Si el libro no se puede leer, carga: el job `intake` vuelve a decidir con el
turno cogido (grupo de concurrencia), así que un reloj de más nunca produce una carga doble.

Escribe `run=true|false` en stdout (para $GITHUB_OUTPUT) y el motivo en stderr y en el resumen del job.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import noche  # noqa: E402


if __name__ == '__main__':
    raise SystemExit(noche.main(['juez']))
