# Radar clock 2026-10-23 (integración)

Fecha: 2026-10-23. Dominio de producción: https://davidportodiaz.com

## Cambios
- PRs #727 y #728 (automáticos): idénticos en convocatorias (retiran "Luz de luna", vence 22/10), con conflictos y Pagefind construido ANTES de las páginas de recomendaciones fusionadas (el `--check` fallaba con 22 páginas sin indexar). Cerrados sin fusionar, ramas borradas.
- Regenerado sobre main 644e022c con `build-radar-opportunities.py --today 2026-10-23` + `build-pagefind-index.py` (350 páginas). Salida de convocatorias idéntica a #727. PR #729 cerrado (rama sin el prefijo exigido por `publish-radar-refresh.py`); PR #730 fusionado (squash) -> cedda69c.
- Luz de luna: no se pudo leer la fuente oficial (curl sin contenido); la retirada es por fecha ya vencida, sin prórroga comprobada.

## Verificado (ejecutado)
- Local: check-radar-clock-current, check-professional-resources, pagefind --check, git diff --check, 7 tests Python radar/ICS y test-radar-dates.mjs: OK.
- CI vía publish-radar-refresh sobre a49c0dc3: 10/10 workflows PASS (merge gate, artifact contract, reflow, pa11y, lighthouse, visual, pro-resources, convocatorias-browser, content-index, broken-links).
- Deploy Pages cedda69c: build, deploy, Verify production y IndexNow: success.
- Producción: opportunities.json generated_for=2026-10-23; ICS 76 eventos = repo; páginas de recomendaciones, ficha de libro (Amazon, Goodreads de autor), editorial Planeta Cómic y autor responden 200.

## Fallos / incidencias
- Post-deploy deep audit fallaba en 644e022c (reloj caducado). Sobre cedda69c: 2 jobs (adaptive-formats, rotating-production-sample) fallaron por 503 transitorios de GitHub Pages en assets (`samuel-entre-mundos.webp`, `hero-tinta-final.jpg`) a las 06:52Z; 200 al reprobar. Se relanzó solo `--failed` (run 39913954194).
- Sitewide Reflow QA sobre cedda69c: sigue en curso (~55-63 min es lo normal en main); no bloqueado.
- `publish-radar-refresh.py` fallaba en Windows por cp1252 (UnicodeDecodeError). Corregido: `gh()` usa `encoding='utf-8', errors='replace'`; test `tests/test-publish-radar-refresh-utf8.py` (falla sin el arreglo, pasa con él).
- `gh pr close -d` cambia a main local; evitar renombrar ramas después.
- La fusión devolvió "policy prohibits" unos segundos tras el último PASS (latencia de estados); reintento OK.

## Pendiente / no comprobado
- Resultado final del rerun del deep audit y del Reflow QA: consultar `gh run list --commit cedda69c...`.
- Cálculo de tokens: no disponible desde la sesión.

## Navegador real (Playwright/Chromium contra producción, desktop 1280 y móvil 375)
- /recomendaciones/: 24 fichas; género OR (terror + fantasía juvenil, URL con ambos valores); AND entre facetas (3→1); contador de casilla = fichas mostradas; recarga y atrás/adelante restauran el estado; sin scroll horizontal; sin 4xx/5xx. PASS.
- Ficha de libro (Coraline): 200, Goodreads y Amazon. Autor y editorial Planeta Cómic: 200; enlace a Planeta presente. deadlines.ics: 200, text/calendar, 76 VEVENT. PASS.
