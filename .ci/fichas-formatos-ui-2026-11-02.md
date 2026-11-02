# Fichas: formatos de compra y avisos de pestaña — 2026-11-02

PR #1052 (`feat/fichas-formatos-ui`): https://github.com/davidpd89/web-escritor/pull/1052

## Cambios
- **QA de navegador (`qa/reading-intake-browser.mjs`):**
  - el botón principal ahora nombra la edición («Comprar en Amazon · Tapa dura»);
  - el QA lo localiza por `a.catalogue-buy-link` y comprueba que su `textContent` empieza por «Comprar en Amazon»;
  - `innerText` no sirve, porque devuelve el texto en mayúsculas por el CSS.
  - Era el fallo de CI «recommendations» (TimeoutError en la línea 28).
- **«(otra pestaña)» en todo enlace con `target="_blank"` del catálogo (WCAG G201):**
  - aviso nuevo en los botones de compra de la ficha y de la tarjeta, las fuentes externas de la ficha, la nota biográfica, las «Fuentes y ediciones» de autor y las listas de libros de las páginas de autor y de editorial;
  - en los enlaces de texto, el aviso va en la constante `NEW_TAB` (`.visually-hidden`, definida en `v1-base.css`).
  - Test nuevo: `tests/test_reading_new_tab_hint.py`, que recorre `recomendaciones/index.html` y `recomendaciones/*/*/index.html`. Con las páginas anteriores, falla.

## Verificado
- `pytest tests/test_reading*.py`: 251 OK.
- `test-reading-catalogue`: PASS. `test-editoriales-builder-parity-v1`: OK.
- `--check` del catálogo, el shell, el sitemap y pagefind, más los presupuestos, las versiones de assets, el orden de páginas y la codificación: OK.
- `qa/reading-intake-browser.mjs` en local: PASS (180 libros importados, 46 editoriales).

## Pendiente
- Que la CI de la #1052 confirme los commits 5da68543a y bd8a3013f.
- `newtab()` sigue con un backspace literal en su regex, así que no marca los enlaces internos. Se deja así a propósito: forzar pestañas nuevas en los enlaces internos iría contra G201.
- La primera regeneración reescribió `?v=` dentro de `.ci/2026-10-31-catalogo-duomo-periferica-141.md`, quizá al subir la versión del JS. Revertido a mano; no se reproduce al repetir la cadena. Si vuelve a pasar, excluir `.ci/` de la herramienta que sube versiones.

## Arreglo pa11y (contraste del ✕)
- Fallo CI pa11y-baseline: 549 errores, todos el `✕` de formato no disponible (#8a8580 sobre #f4f4f2 = 3,32:1).
- `.catalogue-format.is-missing strong` pasa a #67635e (AA); CSS ?v=23 (bump-asset-version).
- Test nuevo `tests/test_reading_missing_format_contrast.py` (calcula el contraste WCAG desde el CSS).
- Verificado local: pytest test_reading* OK, catálogo/shell/sitemap/pagefind/page-order --check, budgets, asset-versions OK. Pendiente: CI pa11y en la PR.

## Merge con main (02/11, mañana)
- Conflicto en `reading_amazon_market.py`: se combinan el barrido con `discover` (rama) y `sin_oferta`/`answers` (main).
- Arreglo estructural: el límite diario lanzaba `LookupError`, de modo que cualquier `KeyError` del catálogo (una entrada de `formatos_compra` sin `url`) se tomaba por «fin de cupo» y cortaba la noche en silencio. Ahora hay `DailyLimitReached`, y las entradas sin `url` cuentan como «sin ASIN» y se rellenan con la oferta encontrada. Lo cubre `test_books_without_ebook_are_searched_in_the_kindle_store`.
- JSON del catálogo: fusión a tres bandas por registro, 0 choques. Builds, checks y `pytest tests/test_reading*.py` en verde en local.
