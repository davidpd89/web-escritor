# SEO/GEO del catálogo: géneros rastreables, 1.120 páginas de autor, RSS e IndexNow — 2026-11-28

Rama `ccr-a446af60-ezzotf`, desde main a79c912ef.

## Diagnóstico (medido en el repo, no supuesto)
- 11.411 fichas; 9.225 de 2026 y 1.312 de 2027: el catálogo es, de hecho, de novedades y próximos lanzamientos.
- Las etiquetas de género enlazaban a `/recomendaciones/#genero=…` (fragmento): **0 URL rastreables por género**.
- 11.465 autores; solo 799 con página. 1.378 con ≥2 libros, solo 257 con página. Causa: solo la ingesta editorial
  (`update_authors`) creaba fichas; los libros que entran por Amazon (`catalogo_amazon.py`) nunca.
- RSS del catálogo (`assets/pinterest/feeds/*.xml`): todos sin un solo `<item>`.
- `scripts/indexnow.py derive` lanzaba error con >10.000 URL cambiadas y el deploy publicaba sin avisar a IndexNow.
- GitHub Models (`models.github.ai`) responde `200 OK` con cuerpo `OK\r\n` desde Actions: es la causa de que
  `empleados-expertos.yml` falle (25 y 27/11). El endpoint antiguo `models.inference.ai.azure.com` ya no resuelve.

## Cambios
- `scripts/build-reading-catalogue.py`
  - `/recomendaciones/generos/<slug>/` para cada género con ≥20 libros (33): próximos lanzamientos, novedades
    (30 días), lo más reciente, autores y editoriales con más títulos, géneros cercanos, FAQ visible con datos;
    JSON-LD `CollectionPage` + `ItemList` + `BreadcrumbList`; intro propia (`data/reading-genre-intros.json`).
  - `/recomendaciones/generos/` (índice) y RSS: `generos/<slug>/feed.xml` y `recomendaciones/novedades.xml`,
    con `<link rel="alternate">` en hubs y catálogo.
  - Las etiquetas de género de fichas, autores y editoriales enlazan al hub (`tag_href`); las tarjetas del índice
    siguen con el filtro JS.
  - Un género que baja del mínimo deja una página `noindex` que vuelve al filtro (sin huérfanos).
  - `recomendaciones/llms.txt`: enlaces a los 33 hubs; corregida la promesa «Para quién es» (solo cuando la hay).
- `scripts/reading_intake_pipeline.py`: `ensure_author_records` crea ficha bibliográfica a todo autor con ≥2 libros
  publicados con ficha editorial https; la ingesta lo aplica cada noche (aislado: un fallo va a `stats.errors`).
- `scripts/backfill-reading-author-pages.py` (+ `--check`): aplicado una vez → 1.120 fichas nuevas.
- `scripts/indexnow.py`: con >10.000 cambios, primero las URL nuevas y recorte declarado (`counts.truncated`).
- `scripts/build-section-context-nav.py`: «Géneros» en la barra de sección de `/recomendaciones/`.
- `scripts/publish-reading-refresh.py`, `scripts/materializar_generados.py`: rutas nuevas admitidas.
- `.github/workflows/gpt-rondas.yml` + `scripts/gpt_ronda.py`: canal para rondas con GPT (GitHub Models); hoy no
  sirve por el fallo de GitHub Models descrito arriba.
- Tests: `test_reading_genre_hubs.py`, `test_reading_author_pages_backfill.py`, `test_indexnow_truncado.py`.

## Rondas con GPT
- API de OpenAI: clave no concedida. GitHub Models: `200 OK` sin JSON (canal `gpt-rondas.yml` queda listo para cuando vuelva).
- Codex (ChatGPT) en la PR #1636: hace revisiones (`@codex review`), pero las preguntas abiertas exigen crear un
  entorno en chatgpt.com/codex/cloud/settings/environments (solo David).
- Ronda 1 (revisión): 2 P1 + 2 P2, todos reales y corregidos — autores en el punto común de la carga (`assemble()`,
  la carga usa `amazon_intake`), contratos `*_smoke.py`, fechas parciales, `dateModified` de hubs.
- Ronda 2 (revisión): 1 P2 real y corregido — 30 firmas corporativas pasan a `Organization` (`entidad`).

## Verificado (local)
- `materializar_generados.py` construye y comprueba: catálogo 0 pendientes, shell 13.886, sitemap 13.879 URL,
  Pagefind 13.740, versiones de assets OK; Atlas regenerado y su contrato OK; `check-global-discoverability` PASS.
- pytest de lectura + materializar + IndexNow (xdist): 852 OK; 7 fallos míos corregidos (`18b15a0b2`) y 1 de entorno
  (`test_bad_candidate…`: el proxy bloquea davidpd89.github.io; falla igual con main).
- Réplica de los 16 checks de la skill audit-website-aeo: hubs 16/16; fichas de libro fallan profundidad (≈200 palabras).

## Fallos y límites
- `check-image-format-ladder`: 1 incumplimiento también en main (no es de esta PR).
- QA de navegador local imposible (Playwright fijado sin su Chromium aquí): lo cubre la CI.

## Pendiente
- CI verde de la PR #1636 y `scripts/carga_en_curso.py` (sin `gh` aquí) antes de fusionar; skill `revisar-carga`.
- Rondas de estrategia con Codex: requieren el entorno de Codex (David). Preguntas listas en `.ci/gpt-rondas/`.
- Fichas de libro finas (≈90 % sin sinopsis): decidir enriquecer/consolidar/noindex; no se ha tocado.
- Bing Webmaster Tools (AI Performance) y Search Console: alta y medición, requiere a David.
- GitHub Models caído: también tumba `empleados-expertos.yml`.

## Enlaces
- PR: https://github.com/davidpd89/web-escritor/pull/1636
