# Telegram · Próximos lanzamientos por días (2026-11-23)

**Cambio** (`scripts/reading_telegram.py`): el resumen semanal de los lunes pasa de un mensaje largo a
1. una cabecera (rayas, emojis, rango de fechas, nº de libros y días, y todas las etiquetas: generales + una por género presente);
2. un mensaje por fecha (de la más cercana a la más lejana) con el día arriba una sola vez, libros agrupados por género y títulos en MAYÚSCULAS con enlace de Amazon. Sin etiquetas.
Si un día no cabe en un mensaje de Telegram, lo que sobra se omite y una línea final indica cuántos libros faltan.
Claves de entrega: `weekly-<lunes>` (cabecera) y `weekly-<lunes>-<fecha>` (cada día); las recoge `digest_candidate_keys`.

**Verificado**: `pytest tests/test_reading_telegram*.py tests/test_telegram_guardian.py` → 81 passed. Vista previa con libros de ejemplo revisada.
**No verificado**: envío real (el primer lunes con el formato nuevo es el 30/11 a las 11:30); aspecto en el móvil; Discord (#proximos-lanzamientos recibe los mismos mensajes, no probado).
**Pendiente**: nada técnico; mirar el 30/11 que cabecera y días lleguen en orden.
