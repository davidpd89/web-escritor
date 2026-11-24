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

## Altas en directorios (23/11, canales públicos `*_libros_dp`)
- list.tg (Books): 10/10 recibidas, en revisión (`?ok=1`).
- TGmetrix: 10/10 enviadas (`?ok=1`).
- TG Inspector: todos y proximos aceptados; el resto topó con límite de envíos diario (reintentar mañana: novedades, thriller, romantica, fantasia, terror, cienciaficcion, infantil, ensayo).
- telegramchannels.io (Education, español): 10 enviados; los 8 primeros sin mensaje de confirmación legible, infantil y ensayo respondieron «ya enviado/recibido». Sin comprobar.
- TeleSeeker: 10 enviados, atascados en verificación Turnstile; sin confirmar (revisar a las 24 h).
- TGStat: David dice que envió los 10 (sin verificar).
- Discord (invitación permanente `https://discord.gg/3DNkNcyQsX`, Edge 9250 limpio sin extensiones para pasar Cloudflare): Discadia (`dcd.gg/club-de-lectura-david-porto`), Disboard (`/bump` cada 2 h), discord.me (publicado), discordservers.com (100 %, vanity disc.gg/club-lectura) publicados; top.gg en revisión (1-2 semanas). Roles de los bots recortados a cero permisos (Discadia, Disboard, DiscordServers x2); top.gg solo Crear invitación.
- Pendientes Telegram: tg.place, tgmania, telegramchannels.me, telegramgroups.co, TGbox; reintentar TG Inspector.
- Pendientes Discord: discordplace.com, discordbotlist.com, discolisting.com, discordfinder.net, serverdrop.gg, disradar.com (mín. 10 miembros), discords.com, discordservers.io, thediscordlist.com, discordhome.com (dclist.gg: ruta /add da 404, buscar la correcta).
- Pendiente: PR #1544 (CI, comentarios, fusionar antes del lunes 30/11 11:30).

## Actualización 24/11 (Discord)
- Publicados: DiscordPlace (bump 2 h), ServerDrop (`serverdrop.gg/server/club`, bump 6 h, bot con 3 permisos mínimos), discords.com (pública, tags Community/Learning, desc. ES, invitación automática), discordservers.io (`/server/99590-club-de-lectura-david-porto`, bot DSL recortado a cero).
- En revisión: DiscoListing, top.gg. Descartados: discordfinder.net (caído), dclist.gg (/add 404).
- Roles de bots (DiscordServers ×2, Place, DSL) recortados; DS.ME solo «Crear invitación».
- Pendiente Discord: thediscordlist.com, discordhome.com, discordbotlist.com, disradar.com (mín. 10 miembros; hay 9), bumps periódicos.
- Pendiente Telegram: TG Inspector (8 canales con límite diario), comprobar TeleSeeker/telegramchannels.io/TGStat, telegramchannels.me, tg.place, etc.
- Edge 9250 (mío) sigue abierto; cerrar al terminar. 9232/9240 son de David.
- 24/11 tarde: thediscordlist.com enviado a revisión (sin bot, invitación permanente; tags books/reading/spanish; categorías Community+Books). discordhome.com publicado (listing 58193, bump manual cada 2 h, rol DH Bump a cero; invitación del bot discord.gg/6HXM3Pct5q). Pendiente: discordbotlist.com, disradar.com (≥10 miembros).

- discordbotlist.com (24/11): formulario enviado 2 veces, sigue "not listed" (probable exigencia de bot en el servidor); descartado.
- Pendiente: disradar.com (≥10 miembros), TG Inspector (límite diario), TeleSeeker/TGStat verificación, telegramchannels.me y otros directorios TG, bumps periódicos (Disboard/Place/Home 2 h, ServerDrop 6 h, Discadia 1/día), PR #1544 fusionar antes del 30/11 11:30.

## Actualización 24/11 (automatización)
- Disradar listado (bot con solo «Crear invitación»; servidor ya >=10 con bots). discordbotlist descartado.
- Automatización en `C:\GIT\RRSS_DavidPorto\SISTEMA_PROMO_COMUNIDAD\` (ver README): tareas «RRSS Promo Discord bumps» (30 min), «RRSS Promo Telegram altas» (diaria 10:15), «RRSS Promo avisos ntfy» (1 h). Pestaña «comunidad» en el panel RRSS (#com) para lo manual (voto Discords.com); panel reiniciado.
- Altas TG: tginspector 5/10 (límite diario, sigue mañana), tgplace 3/10 (límite), tgmania 10/10, telegramchannels.io en curso; list.tg y TGmetrix 10/10; TeleSeeker verifica solo.
- Cloudflare: fallaba por extensiones en 9232 y por no esperar al token Turnstile; en 9250 limpio + espera funciona.
- PR #1544: Pagefind obsoleto por deriva de main → merge de main (conflicto en recomendaciones/index.html resuelto con la versión de main + invitación permanente) y push; auto-merge squash activado. Comprobar tras CI y tras el 30/11 11:30.
- Pendiente: top.gg/DiscoListing/thediscordlist en revisión; TGStat (/add 404, necesita cuenta); ampliar directorios.

## Actualización 24/11 (tarde)
- Voto discords.com automatizado (votos_web.py, 6 h). Consulta a GPT: nuevos sitios en RRSS/SISTEMA_PROMO_COMUNIDAD/gpt_sitios_2026-11-24.md.
- Añadidos TeleNavo (comprobado: "en cola de revisión"; limita por ritmo) y search-t.me (envío sin error, sin confirmación visible). Altas TG cada 2 h.
- Pendiente: PR #1544 (CI) antes del 30/11 11:30; login de directorios Discord nuevos (Dizord, Discords.ai, DiscordBase…).
