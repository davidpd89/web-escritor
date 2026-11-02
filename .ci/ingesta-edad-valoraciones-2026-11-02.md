# Ingesta, edad recomendada y valoraciones — 2026-11-02

## Cambios
- **PR #1058** (`feat/planeta-edad`): edad recomendada de Planeta.
  - La temática «De 9 a 12 años», «A partir de 14 años» o «Desde N años» pasa a `edad_recomendada` y deja de ser una materia.
  - `age_band()` crea la categoría `edad-…` con orden 140 + edad mínima. Desde 12 años se marca `juvenil`.
  - La meta ya no dice «para de 0 a 3 años».
  - Backfill de 9 fichas de Planeta con `fuente_edad_url`. Franjas nuevas: 6–8 y 9–12.
  - El test de orden de franjas lee el primer número del id: antes, «a-partir-de-N» contaba como 0.
- **PR #1057** (`wt-ingesta`): hasta 60 fichas nuevas por noche y un motivo para cada `sin_oferta` en `prices-report.json`.
- **PR #1052**: regenerados `assets/page-order.generated.js` y `editoriales/duomo-ediciones/index.html`. Estaban desfasados tras normalizar los autores en mayúsculas (`JØRN LIER HORST`).

- **PR #1058, commits posteriores:**
  - Las sinopsis ya no dejan espacios antes de la puntuación cuando el original lleva `<em>`. Corregidas 26 fichas.
  - `datePublished` admite fechas de solo mes (las 9 de Periférica).
  - QA de navegador `qa/catalogue-facet-count-parity.mjs`, conectado a `recommendations-browser-qa.yml`. Recorre las 70 opciones de filtro con libros y comprueba el recuento de la etiqueta, el contador, las tarjetas visibles, el enlace con `#faceta=valor` y la búsqueda sin resultados. Detecta un filtro de grupo roto a propósito.
  - `backfill-reading-metadata.py`:
    - rellena `sinopsis_completa` cuando falta, pero respeta `resumen_propio`, igual que la ingesta;
    - decodifica con `errors='replace'`.
  - `editorial_synopsis` descarta el texto si contiene U+FFFD: Penguin sirve «Sana tus células» con un byte UTF-8 cortado.
  - `lib-0001` (Coraline) no tiene sinopsis completa a propósito: es un resumen propio.

## Verificado
- `wt-edad`:
  - `pytest tests/test_reading*.py`: 244 tests OK (último commit);
  - `--check` del catálogo, el shell, el sitemap y pagefind, más los presupuestos y las versiones de assets: OK.
- `wt-fichas-ui`:
  - `test-editoriales-builder-parity-v1`: OK;
  - `build-editoriales.py --check`: OK;
  - `build-page-order.py --check`: OK.

## Fallos y motivos
- Todas las PR fallan en CI con «radar public output is stale for real execution date 2026-11-02». Depende de la fecha y se resuelve cuando se fusione la #1056 (refresco del radar). Después hay que actualizar las PR con main.
- Fuentes de valoraciones alternativas a Goodreads, descartadas:
  - Google Books sin clave da 429;
  - Open Library solo cubre 1 de cada 15 fichas.
  - Goodreads sigue siendo la única. El reto WAF se trata como fallo (#1054).
- Edad: 89 de 181 fichas siguen sin ella, porque la editorial no la publica (Anagrama, Nórdica, Duomo, Periférica…). No se inventa.

## Pendientes
1. Fusionar la #1056 y actualizar con main las #1052, #1053, #1054, #1055, #1057 y #1058.
2. Cuando entre la #1057: `gh workflow run reading-catalogue-sync.yml` y revisar los motivos de `sin_oferta`.
3. Bucle de textos v3 (`wt-textos2`, puerto 9240): revisar una muestra, `publish`, abrir la PR y lanzar IndexNow.

## Enlaces
- https://github.com/davidpd89/web-escritor/pull/1058
- https://github.com/davidpd89/web-escritor/pull/1057
- https://github.com/davidpd89/web-escritor/pull/1056
