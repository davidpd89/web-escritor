# Comunidades Telegram y Discord — 2026-11-02

Rama local `feat/comunidades-telegram-discord` en el worktree `C:\GIT\wt-comunidades`.
- Sin push.
- Sin workflows lanzados.

## Cambios

- **Nueva página `/comunidad/`**
  - Fuentes:
    - generador `scripts/build-community-page.py`;
    - datos `data/communities.json`;
    - estilos `assets/v1-community.css`.
  - Contenido:
    - Telegram: Novedades, Ofertas de hoy y Los más votados.
    - Telegram: 12 canales por género (cocina, religión, poesía, thriller…).
    - Discord: 4 bloques.
    - Preguntas frecuentes.
    - JSON-LD de tipo CollectionPage y BreadcrumbList.
  - Solo hay botón «Unirme» si existe un enlace público. Ahora mismo ninguno tiene enlace, así que no se muestra ningún botón.
- **Pie**: iconos de Telegram y Discord que enlazan a `/comunidad/#telegram` y `/comunidad/#discord`.
- **`/redes-sociales/`**: tarjetas «Comunidad de Telegram» y «Comunidad de Discord».
- **`/recomendaciones/`**:
  - tercera línea en la cabecera: «¿Quieres estar al día de todo? Únete…»;
  - el enlace inferior ahora lleva a `/comunidad/`.
- **Navegación y publicación**:
  - registro, navegación, mapa del sitio y sitemap (621 URLs);
  - allowlist de `build-public-dist.py` y `.assetsignore`;
  - versión y hash de los assets.
- **Documentación**:
  - `docs/comunidades-telegram-discord.md`: configuración de Telegram y Discord, WhatsApp y otras plataformas, y SEO;
  - nota en `docs/telegram-libros-base.md`.
- **Pruebas**:
  - nuevo `tests/test-community-page.py`;
  - excepción de Yellowtail para `v1-community.css` en el contrato de tipografías.

## Verificado (local)

- PASS:
  - `build-community-page.py --check`
  - `build-sitemap.py --check`
  - `build-public-dist.py --check-assetsignore`
  - `build-reading-catalogue.py --check`
  - `check-asset-versions.py`
  - `check-navigation-coverage.py`
  - `test-header-footer-support-nav`
  - `test-public-artifact-contract`
  - `test-community-page`
  - `test-v1-font-family-token-contract`
- Suite completa `tests/test-*.py`: 317 OK y 5 fallos antes de los arreglos.
  - Arreglado: el contrato de tipografías.
  - Solo por la codificación de Windows: `presskit-numeric-mutants` y `eventos-ferias-fragment-navigation` pasan con `PYTHONUTF8=1`.
  - `staging-publication-gate` 7b: fallaba porque `comunidad/index.html` aún no estaba versionado (el builder usa `git ls-files`). Tras el commit a4fd0305e: **OK**.
  - `pagefind-artifact-corruption`: el índice Pagefind ha quedado desactualizado (ver Pendiente).

## Pendiente

- **Índice Pagefind**: regenerar con `python scripts/build-pagefind-index.py`. Hace falta `pagefind@1.6.0`; el `node_modules` del checkout principal tiene otra versión.
- **Enlaces de invitación**: David debe dar los enlaces públicos (`t.me/...`, `discord.gg/...`) y rellenar `invite` en `data/communities.json`. La sesión de Telegram está en el puerto 9240.
- **Reglas de cada grupo**: más adelante.
- **Bots**: canales por género, ofertas y más votados (necesita una fuente con licencia), y webhooks de Discord.
- **Publicación**: push y PR cuando la CI esté libre; vista previa visual de `/comunidad/` en móvil.

## Fase de definición (misma fecha)

- Nuevo `docs/comunidades-plan.md`. Recoge la definición completa:
  - canales por fases según el volumen del catálogo;
  - bots;
  - cómo unirse;
  - Discord paso a paso;
  - plataformas;
  - dónde mostrar los grupos;
  - SEO;
  - prompts de imagen;
  - checklist de implementación;
  - dudas abiertas en la sección 10.
- Borrador de la descripción del PR en `.ci/PR_BODY-comunidades.md` (local, ignorado por git).
- Commit local. **Sin push, sin PR y sin workflows.**
- No se han creado canales ni generado imágenes: falta la luz verde de David.

## Ejecución (misma fecha, Edge en CDP 9221)

### Hecho y verificado

- **Telegram:**
  - 17 canales con descripción y el bot como administrador.
  - Carpeta «Libros DP»: <https://t.me/addlist/lja92v39DGE4YmM0>.
  - 10 usernames públicos (es el límite sin Premium); 7 canales por invitación `t.me/+`.
  - 17 fotos.
- **Discord:**
  - Servidor completo: estructura, icono y banner, roles, AutoMod, modo lento, temas, normas y bienvenida.
  - Invitación permanente: <https://discord.gg/g7dEWxj3F>, creada por David Porto.
  - Propiedad traspasada a «David Porto», que también tiene el rol Administración. La cuenta antigua ha salido del servidor, sus invitaciones están revocadas y su sesión del Edge, cerrada; quedan 0 webhooks y 0 apps.
  - Avatar de David Porto puesto. #normas y #bienvenida, publicados de nuevo desde David Porto.
  - Modo Comunidad activo: correo verificado, «Solo menciones», permisos arriesgados quitados a @everyone y directrices aceptadas con autorización de David.
  - Canales de anuncios: #anuncios, #novedades, #todos-los-libros, #ofertas, #proximos-lanzamientos y #mas-votados.
- **Página:**
  - `assets/community-avatars/`: 18 WebP y el banner.
  - `communities.json` se regenera desde el estado de Telegram con `mk_communities.py`, un script del scratchpad.
  - Avatares en las tarjetas y horario en las preguntas frecuentes.
  - `test-community-page` pasa (PASS).
  - Revisada visualmente en escritorio y en móvil.
- `docs/comunidades-plan.md`:
  - nueva sección 10, «Estado real»;
  - nueva sección 11, pendientes.

### Pendiente

- Si se quieren los 17 canales públicos, hace falta Telegram Premium (o liberar usernames).
- Mensaje de bienvenida fijado en cada canal de Telegram: lo publicará el worker en su primer envío.
- Discord: David borra a mano los 2 mensajes antiguos de la cuenta anterior en #normas y #bienvenida. El Onboarding es opcional.
- David debería cambiar la contraseña de Discord, porque se escribió en el chat.
- Webhooks de Discord y los dos secretos: los gestiona David.
- Worker de publicación, Pagefind, push, PR y CI.
- **Ningún** id privado, token ni webhook en el repositorio. Los ids de los canales están solo en `state.json` del scratchpad.


## Tramo 2 (2 de noviembre de 2026): bot buscador y onboarding

### Hecho y comprobado
- Discord: roles de géneros (12), avisos 🔔 (4) y niveles (5, separados); onboarding **activado** con 3 preguntas (géneros → canal+rol, avisos con sonido → roles 🔔, extras), 9 canales por defecto, cartel y 5 tareas. Revisión de Discord en verde.
- Notificaciones por defecto «Solo @mentions» (guardado, sin cambios pendientes). CHARLA hereda permisos del servidor: @everyone escribe.
- Bot buscador: `scripts/build-bot-index.py`, `data/bot-books.json` (181 libros), `bots/book-finder.mjs`, `bots/community-bot-worker.mjs`, `bots/register-discord-commands.mjs`, `wrangler.community-bot.example.jsonc`. Tests `test-book-finder` y `test-community-bot-worker`: PASS.
- `docs/comunidades-plan.md` §10.2–10.6: estado del onboarding, guía de despliegue paso a paso, bots recomendados y Telegram.

### No hecho / pendiente
- Worker **no desplegado** y `/libro` no registrado (el cartel ya lo menciona): pasos de §10.4, los hace David con sus secretos.
- Páginas de recursos del onboarding: Discord no ofrece canales elegibles; se omiten.
- Bot de niveles (Lurkr recomendado) sin añadir: necesita el OK de David (OAuth).
- Grupo de comentarios de Telegram sin crear (§10.6).
- Seguir: borrar 2 mensajes antiguos, cambiar la contraseña de Discord, push/PR.

### Fuentes
- https://peakbot.pro/blog/lurkr-vs-arcane-discord-leveling-bot-2026
- https://peakbot.pro/blog/best-discord-leveling-bots-2026
- https://guide-how-to-use-discord.pages.dev/guides/how-to-use-discord-server-setup-bots-roles-community-management

## Tramo 3 (2 de noviembre de 2026): Lurkr, script de despliegue y directorios

### Hecho y comprobado
- Guía del servidor: título duplicado de la tarea `/libro` corregido (verificado tras recargar).
- Lurkr presente en el servidor y configurado (verificado tras recargar el panel): niveles activos; XP solo en 18 canales (12 géneros + CHARLA + #recomendador-ia); XP en hilos sí, por comandos no; **sin anuncios de subida**; recompensas acumulables 1/5/10/20/35 → Lector/a novel, habitual, Ratón de biblioteca, Bibliófilo/a, Leyenda.
- Discord: rol de Lurkr movido justo encima de «Leyenda de la biblioteca» (guardado y verificado) y con «Gestionar roles». Onboarding sigue ACTIVADO.
- `bots/deploy-community-bot.ps1`: sintaxis PowerShell validada (0 errores de parser). Despliega worker, sube secretos con `wrangler secret bulk` (fichero temporal borrado), guía el Interactions Endpoint, invita la app, registra `/libro`, configura webhook y comandos de Telegram.
- `.gitignore`: `/wrangler.community-bot.jsonc`.
- `docs/comunidades-directorios.md`: textos, etiquetas y rutina para DISBOARD, Top.gg, Discadia, Descubrimiento de Discord y Telegram (TGStat, Telemetr, grupo de debate).
- `docs/comunidades-plan.md` §10.4, §10.5 y §11 actualizados.

### No comprobado / pendiente
- El script **no se ha ejecutado** (pide secretos de David): worker sin desplegar, `/libro` sin registrar, webhook de Telegram sin poner.
- `/setinline` en @BotFather, alta en directorios, grupo de debate de Telegram, borrar 2 mensajes antiguos, webhooks/secretos de avisos.
- Commit local sin push; sin PR.

## Tramo 4: interacción, bots y crecimiento

### Hecho
- **Discord:** foro **#sugerencias** en CHARLA. Verificado con captura.
  - Directrices.
  - 3 etiquetas de tipo y 4 de estado (estas, solo para moderación).
  - Etiqueta obligatoria y reacción 👍 por defecto.
  - Publicación semilla.
- **Investigación:** 2 consultas a ChatGPT, más fuentes de Discord, Telegram y Amazon. Volcada en `docs/comunidades-plan.md` §12:
  - bots gratuitos, uno por función;
  - rituales;
  - voz y voto;
  - diferenciales;
  - Discovery y SEO;
  - Telegram;
  - errores;
  - métricas;
  - Amazon Afiliados.
- `docs/comunidades-directorios.md`: dónde anunciarse (checklist) y normas de Amazon en Discord y Telegram.
- `.ci/PR_BODY-comunidades.md`: sección de interacción y checklist «Al ejecutar la PR» de 12 pasos.

### No comprobado / pendiente
- Bots externos (Apollo, Fumiko/Marginalia, Carl-bot…) **no instalados**: requieren el OAuth de David.
- Requisitos de Discovery y lista de redes admitidas por Amazon.es: tomados de la investigación y marcados «comprobar» al ejecutar la PR.
- Sin push ni PR, según lo pedido. Hay que ejecutar la PR cuando David lo diga.

## Tramo 5: enlaces directos a Amazon, decisión de bots y fotos

### Hecho
- **Enlaces de compra:** directos a Amazon con el tag `davidporto-21` en Discord y Telegram.
  - `scripts/reading_telegram.py` cierra cada envío con «Ver en Amazon · #publicidad».
  - Plan §12.3, §12.7 y §12.10 actualizados.
  - `tests/test_reading_telegram.py` pasa.
  - Commit 5085c0f71.
- **Bots:** no se instalan más bots externos, por simplicidad y porque dependen de que la gente participe (plan §10.5 y cuerpo del PR).
  - El bot propio (`/libro`, `@DavidPortoLibrosBot`) es el que trae clics a Amazon.
  - Lurkr se queda.
- **Fotos de Telegram:** avatares de solo texto en los 17 canales. Cada uno verificado con captura en el panel de información o en la lista.
- **Discord:** icono nuevo ya verificado; canales sin cambios.

### Notas técnicas (Telegram Web K, Edge por CDP 9221)
- Ahora la lista y el panel de información se ven a la vez. El lápiz de editar está en (799,44); el resto de coordenadas no cambia.
- Cambiar fotos seguidas da `FLOOD_WAIT`: hay que dejar unos 50 s entre canales.

### No comprobado / pendiente
- Desplegar el bot (`bots/deploy-community-bot.ps1`). Lo hace David.
- Dar de alta Discord y Telegram en Amazon Afiliados antes de promocionar.
- Push y PR cuando GitHub Actions esté libre.
