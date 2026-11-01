# 2026-10-31 · Catálogo: etiquetas, Goodreads, ingesta y matriz de dispositivos

Rama `feat/catalogo-tests-etiquetas-fuentes` (worktree `C:\GIT\web-escritor-cat2`).

## Cambios
- **Tarjetas:** se quita la etiqueta de edad de la tarjeta. Se conserva en filtros, categorías y ficha. Como máximo 3 etiquetas por tarjeta.
- **Caja de datos (antes beige):** sin fondo, con filetes arriba y abajo y etiquetas `dt` en azul del sitio.
- **Goodreads:**
  - El refresco va por lotes, con TTL de 30 días y los libros sin nota primero.
  - Reintenta con backoff ante 429/503.
  - La caché descarta las respuestas truncadas (Content-Length).
  - La tarjeta sin nota no pinta "consultar ficha"; la caja queda oculta y no reserva altura.
  - La ventana de frescura es de 720 h.
  - Resultado: 47 notas actualizadas; 49 libros siguen sin nota y se reintentarán en las siguientes ejecuciones.
- **Por qué seguía en 96 libros:**
  - Las PR del bot (#979, #984, #1006) se cerraban porque fallaba `visual-regression-qa`, un test intermitente.
  - Ahora `publish-radar-refresh.py` relanza una vez los jobs fallidos en el mismo commit; sigue exigiendo verde real.
  - Los topes de ingesta pasan de 8 a 20 libros nuevos y de 120 a 160 peticiones.
  - La ingesta local añadió 25 libros: el catálogo queda en 121.
- **SEO:** el JSON-LD `Book` gana `genre`, `keywords`, `audience` y `sameAs`.
- **Accesibilidad táctil:** los enlaces de autoría y editorial tienen un área de 24 px o más y `max-width:100%`, que corrige el desbordamiento a 320 px con fuente al 200 %.
- **QA nueva:** `qa/catalogue-device-matrix.mjs`, con 11 perfiles (320 px, iPhone SE/13/13 apaisado, Pixel 7, Galaxy S9+, iPad Mini, iPad Pro 11 apaisado, escritorio a 1280, 1440 y 1920).
  - Comprueba que no haya scroll horizontal, etiquetas de edad, cajas de nota vacías ni objetivos de menos de 24 px.
  - Comprueba el Book JSON-LD, CLS ≤ 0,1, DCL ≤ 4 s y que no haya errores de consola, tanto en el hub como en la ficha.
  - Queda añadida a `recommendations-browser-qa.yml`.
- **Assets:** `reading-catalogue.css?v=21` y `reading-catalogue.js?v=25`, con hashes registrados.

## Verificado en local (servidor propio 127.0.0.1:4183)
- **Builders y checks:**
  - `--check` en verde para catálogo, page-order, site-shell, sitemap (499 URLs), pagefind (446 páginas), atlas, section-nav y editoriales.
  - `tests/test-reading-catalogue.py` pasa.
  - `unittest test_reading*`: 190 tests OK.
  - Tests del radar (publicación y UTF-8) pasan.
  - `check-asset-versions` y `check-performance-budgets` pasan (0 errores).
- **Navegador, todos PASS:**
  - reading-catalogue-browser, reading-commerce-browser, catalogue-ratings-trust, reading-intake-browser
  - reading-catalogue-v2-browser, reading-type-selector-browser, catalogue-mobile-discovery
  - catalogue-pagination-shareable-url, catalogue-device-matrix
  - reading-failure-resilience-browser: lee `QA_BASE_URL`, no `QA_ORIGIN`.
- **Matriz de dispositivos:** CLS entre 0 y 0,02; DCL entre 457 y 732 ms.

## Fallos encontrados y corregidos
- Nombre de autor largo con `inline-block` desbordaba a 320 px/200 % → `max-width:100%`.
- Test del radar colgado por un `time.sleep` real → parcheado en el test.

## Pendiente
- CI de la PR y merge; verificación en vivo (estrellas visibles y número de libros).
- Los motivos "Sello no presente" de la ingesta son antiguos; se reintentan solos a los 3 días.

## Investigación (Casa del Libro, Todostuslibros, Lecturalia, StoryGraph, Goodreads) — siguientes mejoras baratas
- **Filtros:**
  - Por ánimo/ritmo, como StoryGraph (ya hay tipo de lector; falta "ritmo").
  - Por número de páginas en rangos.
  - "Disponible en librería independiente", como Todostuslibros.
- **Tarjeta:** nota, número de valoraciones y año visibles; la sinopsis, en la ficha.
- **Ficha:**
  - "Si te gustó X" con libros del mismo sello o etiqueta.
  - Bloque de ediciones (ISBN y formato).
  - Fecha de publicación en `datePublished`.
- **SEO:**
  - `BreadcrumbList` en la ficha.
  - `ItemList` paginado con `url` por libro.
  - Páginas de etiqueta indexables solo con 6 o más libros.
- **Fuentes gratuitas a evaluar:** Open Library (search/editions), Google Books volumes, los RSS de novedades de cada sello y DILVE (requiere alta).
