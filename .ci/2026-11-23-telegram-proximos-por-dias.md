# Telegram · Próximos lanzamientos por días (2026-11-23)

**Cambio** (`scripts/reading_telegram.py`): el resumen semanal de los lunes pasa de un mensaje largo a
1. una cabecera (rayas, emojis, rango de fechas, nº de libros y días, y todas las etiquetas: generales + una por género presente);
2. un mensaje por fecha (de la más cercana a la más lejana) con el día arriba una sola vez, libros agrupados por género y títulos en MAYÚSCULAS con enlace de Amazon. Sin etiquetas.
Si un día no cabe en un mensaje, entra primero un libro de cada género (por rondas) y lo que sobra se omite sin aviso.
Claves de entrega: `weekly-<lunes>` (cabecera) y `weekly-<lunes>-<fecha>` (cada día); las recoge `digest_candidate_keys`.

**Verificado**: `pytest tests/test_reading_telegram*.py tests/test_telegram_guardian.py` → 81 passed. Vista previa con libros de ejemplo revisada.
**No verificado**: envío real (el primer lunes con el formato nuevo es el 30/11 a las 11:30); aspecto en el móvil; Discord (#proximos-lanzamientos recibe los mismos mensajes, no probado).
**Pendiente**: nada técnico; mirar el 30/11 que cabecera y días lleguen en orden.

## Adenda 23/11 (canales y Discord)
- Discord: la invitación g7dEWxj3F caducaba en ~8 días (los docs decían permanente). Creada https://discord.gg/3DNkNcyQsX (sin caducidad, usos ilimitados; verificado por API). Idioma del servidor → Español y descripción puesta. Descubrimiento imposible aún: faltan 1000 miembros, 8 semanas (hasta 28/12) y 2FA para moderación. Servidor: 2 miembros.
- Telegram: 10/22 canales públicos (límite de 10 usernames por cuenta; 20 con Premium). infantil y ensayo ya públicos; los 12 restantes siguen por enlace privado.
- Pendiente: decidir Premium/otra cuenta; alta en Disboard/top.gg/TGStat (requiere autorizar apps con la cuenta Discord/Telegram).
- Pendiente: CI de PR #1544, leer comentarios, fusionar antes del lunes 30/11.
