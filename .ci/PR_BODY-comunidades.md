# Comunidad lectora: /comunidad/, 17 canales de Telegram y servidor de Discord

## Resumen

Este PR tiene dos partes.

- **Implementado** (commit a4fd0305e): la página `/comunidad/` y los enlaces hacia ella desde el pie, `/redes-sociales/` y `/recomendaciones/`.
- **Definición** (`docs/comunidades-plan.md`), pendiente de luz verde:
  - canales y su ritmo según el volumen real del catálogo;
  - bots;
  - cómo unirse;
  - configuración completa de Discord;
  - plataformas;
  - dónde mostrar los grupos;
  - SEO;
  - prompts de imagen para cada canal.

Sin workflows nuevos. Ningún secreto, token ni `chat_id` en el repositorio.

## Implementado

- **`/comunidad/`**
  - Generada por `scripts/build-community-page.py` desde `data/communities.json`, con estilos en `assets/v1-community.css`.
  - Sección Telegram: «al día» y «por género».
  - Sección Discord.
  - «Cómo funciona», preguntas frecuentes y JSON-LD (`CollectionPage` + `BreadcrumbList`).
  - **Botones honestos:** «Unirme» solo aparece si hay un enlace público. El validador rechaza dominios ajenos y los grupos «previstos» que tengan enlace.
- **Pie:** iconos de Telegram y Discord que llevan a `/comunidad/#telegram` y `#discord`.
- **`/redes-sociales/`:** tarjetas de comunidad.
- **`/recomendaciones/`:** tercera línea en la cabecera; el enlace inferior apunta ahora a `/comunidad/`.
- **Registro y descubrimiento:** registro, navegación, mapa del sitio, sitemap, allowlist de publicación y versiones de los assets.
- **Pruebas:** `tests/test-community-page.py` y una excepción de Yellowtail en el contrato de tipografías.

## Creado (2 de noviembre de 2026, desde el Edge de David)

- **Telegram:**
  - **17 canales de difusión**, todos con su descripción y con `@DavidPortoLibrosBot` como administrador publicador:
    - 5 de «al día»: Novedades, Todos los libros, Ofertas de hoy, Próximos lanzamientos, Más votados.
    - 12 por género.
  - Carpeta compartible «Libros DP»: <https://t.me/addlist/lja92v39DGE4YmM0>. Es el botón «Unirme a todos».
  - 10 canales públicos (`t.me/<usuario>`), que es el límite sin Premium, y 7 por invitación (`t.me/+…`). Los 17 tienen foto.
- **Discord: «Club de lectura · David Porto»**
  - Categorías: Inicio, Al día, Por género (12), Charla (2 foros) y Moderación.
  - Icono nuevo (el banner personalizado exige nivel de boost; queda generado en `assets/community-avatars/discord-banner.jpg`), roles, 3 reglas de AutoMod con alertas al canal de registro, modo lento, temas de los canales, mensajes de #normas y #bienvenida.
  - Invitación permanente: <https://discord.gg/g7dEWxj3F>.
- **Imágenes:** 18 avatares en WebP (`assets/community-avatars/`, 380 KB en total), solo tipografía: el género en grande, un color por canal de la misma gama (OKLCH) y «davidportodiaz.com» abajo; legibles a 48 px. Se regeneran con `python scripts/build-community-avatars.py [--preview hoja.png]`, que también crea el banner de Discord. En la página se muestran en cada tarjeta.
- **Horario de publicación:**
  - de lunes a viernes a las 11:30 y los fines de semana a las 18:30 (Madrid);
  - Próximos, los lunes;
  - Más votados (nota de Goodreads en `reading-market.json → ratings`), los sábados.
  - El horario aparece en la página y en la descripción de cada canal.
- Detalle completo y plan en `docs/comunidades-plan.md` (secciones 10 y 11).

## Verificación (local)

- PASS:
  - `build-community-page.py --check`
  - `build-sitemap.py --check`
  - `build-public-dist.py --check-assetsignore`
  - `build-reading-catalogue.py --check`
  - `check-asset-versions.py`
  - `check-navigation-coverage.py`
- Pruebas que pasan:
  - `test-community-page`
  - `test-header-footer-support-nav`
  - `test-public-artifact-contract`
  - `test-v1-font-family-token-contract`
  - `test-staging-publication-gate`
- Fallos solo por la codificación de Windows, que pasan con `PYTHONUTF8=1`:
  - `presskit-numeric-mutants`
  - `eventos-ferias-fragment-navigation`
- **Pendiente:** `test-pagefind-artifact-corruption`. Hay que regenerar el índice Pagefind con `pagefind@1.6.0` antes de fusionar.

## Interacción y crecimiento (investigación, `docs/comunidades-plan.md` §12)

- **Hecho en Discord:** foro **#sugerencias** con etiquetas de tipo (💡 Idea, 📚 Libro para el club, 🛠️ Mejora del servidor) y de estado solo para moderación (👀 En estudio, ✅ Aceptada, 🚀 Hecha, ❌ Descartada). Etiqueta obligatoria, reacción 👍 por defecto y publicación semilla. Es el «voz y voto» de los miembros.
- **Bots (decisión del 2 de noviembre, §10.5): de momento, ninguno externo más.**
  - El único bot que trae clics a Amazon es el propio: `/libro` en Discord y `@DavidPortoLibrosBot` en Telegram, con enlace directo y el tag `davidporto-21`.
  - Lurkr se queda: ya está configurado y no publica nada.
  - Apollo, Fumiko o Marginalia, Carl-bot (starboard) y Suggestions se revisan cuando haya conversación diaria. Sin MEE6.
- **Rituales semanales:** se empieza por martes, jueves y domingo; libro del mes votado y revisión mensual «Lo que habéis cambiado».
- **Diferenciales:**
  - perfil lector en `/libro`;
  - botones «otro parecido / menos romance» en Telegram;
  - buddy reading;
  - biblioteca viva en la web;
  - catálogo legal frente a los canales de PDF pirata.
- **Descubrimiento de Discord:** exige 1000 miembros y 8 semanas, así que hasta entonces el SEO lo hace `/comunidad/`. Dónde anunciarse y las normas de Amazon Afiliados están en `docs/comunidades-directorios.md`.

## Al ejecutar la PR (checklist completa)

1. [ ] Sincronizar la rama con `main` y resolver conflictos.
2. [ ] Regenerar Pagefind con `pagefind@1.6.0` y pasar `test-pagefind-artifact-corruption`.
3. [ ] Repetir las comprobaciones locales de «Verificación» y lanzar la CI en GitHub Actions hasta verla en verde.
4. [ ] `powershell -ExecutionPolicy Bypass -File bots/deploy-community-bot.ps1`. Lo hace David porque pide secretos:
   - worker;
   - secretos;
   - Interactions Endpoint;
   - invitar la app y registrar `/libro`;
   - webhook y comandos de Telegram;
   - después, `/setinline` en @BotFather.
5. [ ] Probar `/libro busco: fantasía para 11 años` en Discord y `@DavidPortoLibrosBot terror` en Telegram.
6. [ ] Webhooks de Discord y secretos `READING_TELEGRAM_CHANNELS_JSON` y `READING_DISCORD_WEBHOOKS_JSON`, que gestiona David.
7. [ ] Aceptar las directrices de Comunidad de Discord (canales de anuncios y Onboarding).
8. [ ] Fusionar y publicar. Comprobar `/comunidad/` en producción.
9. [ ] Después de publicar:
   - grupo de debate de Telegram con Temas (plan §10.6);
   - mensaje índice fijado;
   - reacciones limitadas (§12.7).
10. [ ] Eventos recurrentes con los Eventos nativos de Discord (tertulia mensual y lectura silenciosa semanal). Bots externos de §12.2 solo cuando haya conversación diaria.
11. [ ] Alta en directorios y anuncios: lista en `docs/comunidades-directorios.md` → «Dónde anunciarse».
12. [ ] Amazon Afiliados: dar de alta Discord y Telegram como sitios (§12.10). Todos los enlaces de compra ya van directos a Amazon con el tag `davidporto-21`, así que este paso va antes de promocionar.

## Pendiente fuera de esta PR

- [ ] Worker de publicación por canal y horario (siguiente PR).
- [ ] Perfil lector y botones de refinado en el bot (siguiente PR del bot).
- [ ] Línea base de 4 semanas de métricas (§12.9) antes de fijar objetivos.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
