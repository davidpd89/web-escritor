# 2026-10-31 · Catálogo: Duomo, Periférica y 141 libros

Continúa `.ci/2026-10-31-catalogo-etiquetas-goodreads-ingesta.md` (PR #1019).

## PR
- **#1019** `feat/catalogo-tests-etiquetas-fuentes`:
  - Cubre las etiquetas, la caja de datos, Goodreads, la matriz de dispositivos y el paso a 121 libros.
  - Último fix: `tests/test_goodreads_redirect_preflight_zone.py` pasa a inspeccionar `fetch_once`. Con el backoff, `urlopen` vive allí; ese test era el que tumbaba python-tests en CI.
- **#1020** `feat/catalogo-fuentes-duomo-periferica`:
  - Parte de #1019 y añade Duomo, Periférica y la materia por Thema; el catálogo llega a 141 libros.
  - Rebasada con `git rebase --onto origin/main 49b5693db` tras el squash de #1019.
- **#1019 fusionada (0ad4df853) y desplegada.** Comprobado en vivo con Playwright: 121 tarjetas, 0 etiquetas de edad, 0 «consultar ficha», sin desbordamiento a 390 px y css v=17.

## Cambios (#1020)
- **`scripts/reading_generic_source.py`:**
  - Revisados `duomo-es` y `periferica-es`.
  - Fecha con precisión de mes (`MM/AAAA`).
  - La materia sale del código Thema.
  - `_infer_subject` puntúa: «historia», «estudio» y «análisis» ya no deciden «Ensayo».
- **`data/reading-intake-config.json`:** las dos fuentes nuevas. Periférica lleva `default_format: tapa-blanda`, y la sinopsis se lee del bloque `#description`.
- **Tests:**
  - El fixture `tests/fixtures/generic-ficha-periferica.html` cubre Munda: fecha por mes, encuadernación por defecto y sinopsis.
  - Hay un test nuevo de materia por mayoría.
  - En Nórdica, la materia esperada es «Narrativa» (por Thema FBA).
- **Ingesta local:** 20 libros nuevos (9 de Periférica, 2 de Duomo, 3 de Nórdica, 3 de Anagrama y otros) con todos los artefactos regenerados.

## Verificado en local (servidor propio 127.0.0.1:4183)
- **Builders y checks:**
  - `--check` en verde para catálogo, page-order, shell, sitemap (539), pagefind (537), editoriales (150), atlas y section-nav.
  - `check-asset-versions` y `check-performance-budgets` pasan (0 errores).
- **Python:** `unittest discover` completo OK; `test_reading*` suma 192 tests.
- **Navegador, todos PASS:**
  - reading-catalogue-browser, catalogue-device-matrix, reading-intake-browser, catalogue-ratings-trust
  - reading-commerce-browser, reading-catalogue-v2-browser, reading-type-selector-browser, catalogue-mobile-discovery
  - catalogue-pagination-shareable-url: un timeout puntual; pasa al relanzarla
  - reading-failure-resilience-browser
- **SEO:** la ficha ya publica Book, BreadcrumbList y WebPage. `datePublished` solo aparece con fecha completa y ya pasada, que es lo correcto para las novedades futuras.

## Bug en vivo: las estrellas no se veían (corregido en #1020)
- **Síntoma en producción:** 0 notas visibles. El HTML sí tenía la nota (p. ej. «Goodreads ★★★★★ 3,91 (178)»), pero la caja seguía con `hidden`.
- **Causa:** `refresh()` pinta primero sin `reading-market.json` y oculta las cajas vacías de las tarjetas. Cuando llegaba el mercado, `renderMarket` las rellenaba pero no les quitaba `hidden`.
- **Arreglo:** `assets/reading-catalogue.js` pone `box.hidden = false` antes de pintar, y el asset pasa a `v=26` con su hash registrado.
- **QA:** `qa/catalogue-ratings-trust.mjs` exige que la nota verificada sea visible. Falla sin el arreglo («390px: la nota verificada queda oculta») y pasa con él.
- **Después del arreglo, todo en verde:** pagefind regenerado (537 páginas, `--check` en verde), ratings-trust, catalogue-browser, device-matrix, commerce, type-selector y v2-browser.

## Fallos
- CI #1019 python-tests: el test leía el código fuente de `fetch` → corregido (`49b5693db`).
- Primer intento de QA sin Playwright: la junction de node_modules estaba mal escapada en bash → se recreó con PowerShell.

## En vivo (davidportodiaz.com/recomendaciones/, tras merge 07cbff885 y despliegue 41196845958)
- **A 390 y a 1280 px:**
  - 141 libros, `reading-catalogue.js?v=28`.
  - 29 notas Goodreads visibles y 0 cajas con nota ocultas.
  - 0 etiquetas de edad, 0 «consultar ficha» y 0 px de scroll horizontal.
- **Notas:** los 112 libros restantes aún no tienen nota verificada. El refresco por lotes, con 30 días de TTL y los libros sin nota primero, las irá completando.

## Pendiente
- Editoriales descartadas por ahora:
  - Valdemar, Acantilado, Impedimenta y Plataforma: no publican fecha de edición.
  - Asteroide: no da año ni encuadernación.
  - Alianza: el ISBN solo está en la URL y el og:image no va por https.
  - Blackie, Errata Naturae y Alba: no respondían.
- Mejoras de UX pendientes de la investigación:
  - Filtro de ritmo.
  - Rangos de páginas.
  - Número de valoraciones en la tarjeta.
  - «Si te gustó X».

## Seguimiento: sincronización automática a 161 libros
- **La sincronización programada fallaba.** La ingesta de Planeta creaba la categoría `tema-manga`. #1028 lleva «Manga», «Manga Shonen/Seinen/…» y «Cómic manga» a `comic-y-novela-grafica` y añade un test.
- **Fallo de QA en el PR del bot #1029.** El popup de newsletter tapaba las casillas en `qa/reading-type-selector-browser.mjs`. #1031 lo desactiva en la prueba, igual que la intro.
- **#1029 quedó en conflicto con main.** Se cerró, se relanzó la sincronización (run 41233675860, en verde) y su nuevo PR #1033 se fusionó (00e25187e). Ya hay 161 libros publicados.
- **QA local contra la rama de 161 libros, todo PASS:**
  - type-selector
  - catalogue-browser
  - v2
  - intake (160 importados, 41 editoriales)
  - ratings-trust
  - device-matrix
  - commerce
  - mobile-discovery
  - pagination
  - failure-resilience
- **En vivo, tras el despliegue de 00e25187e:**
  - A 390 y a 1280 px: 161 libros, `js?v=26`, 51 notas visibles, 0 ocultas, 0 etiquetas de edad, 0 «consultar» y 0 overflow.
  - Matriz de dispositivos contra producción: PASS en 11 perfiles.
- **Notas Goodreads:** 110 libros siguen sin nota verificada. El refresco por lotes las irá completando.
