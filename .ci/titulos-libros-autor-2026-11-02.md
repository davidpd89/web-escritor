# Fichas: títulos SEO con autor y Open Graph de libro — 2026-11-02

Rama `feat/titulos-libros-autor`, a partir de main 7adb3e168.

## Cambios
- **`book_title`:** cuando un título no cabe en 75 caracteres, ahora se acorta en este orden y siempre conserva el autor:
  1. quita la nota de edición («edición especial/limitada/coleccionista…»);
  2. quita la serie entre paréntesis;
  3. quita el subtítulo.
  - Si aun así no cabe, recorta el título y mantiene el autor.
  - El ISBN solo aparece si el título acortado coincide con el de otra ficha del mismo autor, o si el autor es demasiado largo.
  - Antes, 12 fichas tenían de título «Título… · 978…», sin autor. Ahora quedan 2 con ISBN (Ciencias del comportamiento, por el nombre largo del autor, y As the Gods Will), y los 181 títulos siguen siendo distintos.
- **Fichas con `og:type=book`**, más `book:isbn`, `book:author` (la URL de la página de autor) y `book:release_date`. Los datos salen del mismo `Book` del JSON-LD. Las páginas de autor y de editorial siguen como `website`.
- **Tests:**
  - `tests/test_reading_intake_pipeline.py`: el título conserva el autor, pierde la nota de edición y la serie, y la edición especial no choca con la normal. En todo el catálogo, los títulos son únicos, no pasan de 75 caracteres y nombran al autor (como mucho 2 excepciones).
  - `tests/test_reading_open_graph_book.py` (nuevo).

## Verificado
- `pytest tests/test_reading*.py`: 239 OK.
- `test-reading-catalogue`: PASS. `editoriales-parity`: OK.
- `--check` del catálogo, el shell, el sitemap y pagefind, más los presupuestos, las versiones de assets, el orden de páginas, la codificación y `check-social-cards`: OK.

## Pendiente
- Confirmar la CI de la PR.
- Pueden aparecer conflictos de HTML generado con las #1052–#1059, que también regeneran fichas. Si pasa, regenerar sobre main.
