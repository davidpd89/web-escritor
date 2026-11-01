# Textos propios v3 y guía SEO/GEO de las fichas — 2026-11-01

## Cambios (PR #1053, rama `feat/textos-calidad`)
- `scripts/reading-texts.py` (VERSION 3):
  - Módulos nuevos: `para_quien`, `que_formato_elegir` y `lecturas_afines`. Cobertura de 181/181 fichas, todas con 2 módulos o más.
  - No se admite abstenerse. Los errores de validación vuelven en `corregir` en el siguiente prompt, con un máximo de 4 intentos por versión de las fuentes.
  - Se rechazan los textos que hablan de las fuentes («la sinopsis no aclara…», «no se especifica…») y las muletillas de texto generado («sin duda», «sumérgete», «un viaje», «no solo… sino»…).
  - `lecturas_afines` tiene que nombrar un título de `afines_catalogo` y guarda los ids en `enlaces`.
  - Una reparación con menos bloques nunca sustituye a un texto guardado.
- `scripts/build-reading-catalogue.py`:
  - El título del afín enlaza a su ficha.
  - El bloque se oculta si el afín deja de estar publicado.
- `scripts/templates/reading-texts-prompt.md`: reescrito con el objetivo de búsqueda y de IA.

## Verificado
- `test_reading*.py`: 237 tests OK.
- `--check` del catálogo, del shell y del sitemap: OK.
- `check-asset-versions`: OK.
- Fallan en local, por un problema del entorno de Windows (`stdout` None en subprocess) y no por este cambio: `tests/test-atlas-pages.py` y `tests/test-check-noveris-magic-quarantine.py`.

## Bucle
- Se lanzó el bucle v3 desde `C:\GIT\wt-textos2` (GPT web, puerto 9240, lotes de 5, 24 h, sin publicar):
  - salida en `.local/reading-texts/out`;
  - log en `.local/reading-texts-run.log`.
- El bucle v2 (`wt-seo-ia`) ya no estaba en marcha. Sus 84 salidas no se publican (55 eran abstenciones).
- **Pendiente:** revisar una muestra antes de `publish`.

## Guía SEO/GEO aplicada a las fichas (fuentes oficiales)
- **Google, funciones de IA:**
  - no hay requisitos extra: la página tiene que estar indexada y poder mostrar un snippet;
  - los datos estructurados tienen que coincidir con el texto visible.
- **Google, políticas de spam:**
  - evitar el *scaled content abuse* y la *thin affiliation*;
  - un afiliado que aporta valor ofrece comparativas, navegación y precio. De ahí salen `lecturas_afines`, `que_formato_elegir` y la caja de formatos.
- **Google, reseñas:**
  - incluir factores de decisión y alternativas;
  - aquí no hay valoraciones inventadas: solo factores verificables.
- **Bing (02/2026):**
  - respuesta clara arriba y hechos explícitos;
  - entidades con el mismo nombre siempre;
  - IndexNow;
  - panel AI Performance de Bing Webmaster.
- **Paper GEO (arXiv 2311.09735):** las cifras y los hechos citables mejoran la visibilidad (+30–40 %); el relleno de palabras clave la empeora (−8 %).
- **Reglas en el prompt:**
  - la primera frase responde a la pregunta;
  - las cifras y los nombres salen literalmente de las evidencias;
  - nunca se habla de las fuentes;
  - estilo variado;
  - de 2 a 4 frases.

## Arreglos del 02/11
- `GENERIC_NAMES`: ISBN, Kindle, Amazon, ebook… dejan de rechazarse como entidades sin respaldo. Test incluido.
- `git()` lee en UTF-8. El bucle se caía con `UnicodeDecodeError` cp1252 al leer el catálogo con ñ. Test incluido; se comprobó que falla sin el arreglo.
- El bucle se relanzó a las 00:44 (`.local/reading-texts-run2.log`). Va a unos 4 de 5 guardados por lote.
- `test_reading*.py`: 241 OK.

## Pendientes
1. Muestra del bucle v3 → publicar (`reading-texts.py publish`) → PR con los textos.
2. Comprobar que se fusionan la #1052 (formatos/UI; el último push alinea la QA con «Goodreads · ver opiniones») y la #1053.
3. Ingesta masiva con la Creators API (respetando 1 petición/s y 8640/día).
4. IndexNow tras publicar los textos. Revisar el panel AI Performance de Bing.
5. Revisión visual de la caja de formatos y los filtros en móvil.
