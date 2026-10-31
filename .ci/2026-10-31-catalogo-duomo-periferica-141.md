# 2026-10-31 · Catálogo: Duomo, Periférica y 141 libros

Continúa `.ci/2026-10-31-catalogo-etiquetas-goodreads-ingesta.md` (PR #1019).

## PR
- **#1019** `feat/catalogo-tests-etiquetas-fuentes`:
  - Cubre las etiquetas, la caja de datos, Goodreads, la matriz de dispositivos y el paso a 121 libros.
  - Último fix: `tests/test_goodreads_redirect_preflight_zone.py` pasa a inspeccionar `fetch_once`. Con el backoff, `urlopen` vive allí; ese test era el que tumbaba python-tests en CI.
- **#1020** `feat/catalogo-fuentes-duomo-periferica`:
  - Parte de #1019 y añade Duomo, Periférica y la materia por Thema; el catálogo llega a 141 libros.
  - Hay que rebasarla sobre main cuando #1019 entre (pagefind y sitemap con `--theirs` y regenerar).

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

## Fallos
- CI #1019 python-tests: el test leía el código fuente de `fetch` → corregido (`49b5693db`).
- Primer intento de QA sin Playwright: la junction de node_modules estaba mal escapada en bash → se recreó con PowerShell.

## Pendiente
- CI y merge de #1019, después rebase de #1020, su CI y su merge.
- Verificación en vivo de `/recomendaciones/`: 141 libros, sin etiqueta de edad y estrellas visibles.
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
