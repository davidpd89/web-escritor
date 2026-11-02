# GEO: índice del catálogo para IAs (`recomendaciones/llms.txt`) — 2026-11-02

Rama `feat/geo-indice-catalogo`, a partir de main c036bb6e4.

## Problema
`llms.txt` y `llms-full.txt` solo enlazaban la portada `/recomendaciones/`. Ninguna superficie para máquinas listaba las 181 fichas: un asistente de IA tenía que rastrear el HTML para encontrar un libro concreto.

## Cambios
- **`build-reading-catalogue.py` genera `recomendaciones/llms.txt`:** una línea por libro publicado, ordenada por título. Cada línea lleva el enlace a la ficha, los autores, la editorial, el año, el formato, las páginas, el ISBN, el género y los temas, la edad y la sinopsis de la editorial (atribuida y recortada a 300 caracteres).
  - Sin enlaces de afiliado, sin precios ni fechas de revisión, sin imágenes.
  - Incluye la frase de no atribución a David Porto Díaz.
  - Se regenera con el builder y se valida con `--check`.
- **Enlaces al índice:**
  - en `llms.txt`, plegado en la línea del catálogo para no pasar del límite de concisión (5998 caracteres; el límite es 6000);
  - en `llms-full.txt`, en dos sitios.
- **`publish-reading-refresh.py`:** el refresco automático del catálogo puede publicar el fichero (está en `EXACT`).
- **`build-public-dist.py`:** clasifica el fichero como `machine-readable`. Ya era público, por el prefijo `recomendaciones/`.
- **Tests:**
  - `tests/test_reading_llms_index.py` (nuevo): hay una entrada por ficha con autores, editorial, ISBN y sinopsis; el texto es plano, sin Amazon ni HTML; los dos llms.txt raíz lo enlazan.
  - `test-reading-publication`: incluye la ruta nueva.

## Verificado
- `pytest tests/test_reading*.py`: 240 OK.
- Pasan `test-reading-catalogue`, `test-reading-publication`, `test-machine-authority`, `editoriales-parity` y `jaula-privacy`.
- Pasan `check-public-text-encoding`, `global-discoverability`, `editorial-facts`, `internal-graph`, `orphan-assets` y `--check-assetsignore`.
- Pasan los `--check` del catálogo, el shell, el sitemap y el orden de páginas, más los presupuestos, las versiones de assets y `social-cards`.

## Pendiente
- Confirmar la CI.
- Cuando se publiquen los textos propios (#1053), valorar si el índice debe incluir también el resumen «Antes de elegir».
- `llms.txt` queda a 2 caracteres del límite de concisión: la próxima línea que se añada obligará a recortar otra.
