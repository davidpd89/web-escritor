# Relacionados del mismo público — 2026-11-02

## Cambios
- **«También te puede interesar»** (`related_books` en `scripts/build-reading-catalogue.py`):
  - Cada categoría compartida pesa log(N/df). Compartir «Hockey» pesa más que compartir «Romance». Antes se contaban las etiquetas y el empate se resolvía por orden alfabético.
  - No se mezclan públicos (infantil / juvenil / adultos) ni libros con más de 4 años de diferencia en la edad mínima, salvo que sean del mismo autor.
  - Es el mismo criterio que usan los afines de los textos v3 (PR #1053).
- Regenerado: catálogo, shell, sitemap y pagefind.
- Test nuevo: `tests/test_reading_related_books.py`.

## Verificado
- `pytest tests/test_reading*.py`: OK. Test nuevo: 2 OK; con el código de main, 2 fallos.
- `test-reading-catalogue.py`: PASS. Los `--check` del catálogo, el shell, el sitemap, pagefind, los presupuestos, las versiones de assets, page-order y la codificación: OK.

## Detectado sin arreglar (lo decide David)
- `newtab()` (~línea 506) lleva un backspace literal en la regex `r'<a\x08[^>]*>'` desde cbdde254a (22/10). Por eso los enlaces internos del contenido nunca abren en pestaña nueva. No lo cambio: abrir en la misma pestaña es lo recomendado por accesibilidad (WCAG G201). Si se deja así, conviene borrar el código muerto.

## Pendientes
- CI de la PR y merge.
