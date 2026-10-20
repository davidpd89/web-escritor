# Catálogo de lecturas: contrato para el futuro Drive

Fase 1 de la PR #659. La fuente es `data/reading-catalogue.json` (`schema_version: 1`). No hay conexión a Drive ni publicación en Pinterest. El catálogo empieza vacío y conserva las guías actuales. Las pruebas usan libros sintéticos únicamente en directorios temporales y respuestas de navegador interceptadas, nunca en el contenido público.

## Hojas y columnas exactas

Crear posteriormente tres pestañas con estos nombres. Una fila por entidad o relación. No crear aún un Drive como parte de esta PR.

**Categorias**

`id, slug, nombre, tipo, descripcion, orden, activa`

- `id` y `slug`: claves únicas estables, minúsculas ASCII y guiones, sin espacios ni tildes. `nombre` y `descripcion` admiten tildes.
- `tipo`: `genero`, `tematica`, `temporada`, `edad`, `contenido` o `epoca`. Se pueden añadir categorías sin modificar el código. Un nuevo tipo requiere ampliar el contrato.
- `orden`: entero. `activa`: booleano `TRUE` / `FALSE` en Sheets, `true` / `false` en JSON.
- Novedades no es una categoría asignable: el filtro «Últimos lanzamientos» usa los 180 días anteriores, incluido el día de publicación, según la fecha civil de Madrid. Excluye fechas futuras y libros sin fecha verificada. No depende del alta en el catálogo. Las categorías de época (por ejemplo, clásicos) son editoriales y explícitas.

**Libros**

Columnas mínimas para guardar un borrador:

`id, slug, titulo, autores, estado`

Obligatorias adicionales para `listo` y `publicado`:

`descripcion_breve, descripcion_original_confirmada, edicion, portada_local, portada_fuente_url, portada_edicion_verificada, autorizacion_o_base_uso, portada_fecha_revision, portada_ancho, portada_alto, fuente_bibliografica_url, fecha_verificacion, fecha_actualizacion`

Columnas opcionales:

`url_amazon_afiliada, isbn13, editorial, fecha_publicacion, fuente_publicacion_url, idioma, edad_recomendada, fuente_edad_url, avisos_contenido, lectura_personal_confirmada, evidencia_lectura, autoria_propia, resenas, fragmento_url`

- `autores`: nombres separados por `|` en Sheets; lista de cadenas en JSON. No separar nombres por comas.
- `estado`: `borrador`, `listo`, `publicado`. Solo `publicado` genera HTML, enlaces y registro público. `listo` pasa las mismas validaciones, pero permanece fuera del catálogo. No hay ruta pública de previsualización de borradores.
- `descripcion_breve`: texto original, 40–1200 caracteres, sin HTML. No copiar sinopsis comerciales ni presentar opiniones personales sin constancia. Se usa también en la ficha, metadatos y lectura en voz alta.
- Confirmaciones y `autoria_propia`: booleanos. Las confirmaciones de edición y descripción original deben ser `TRUE` para publicar. `lectura_personal_confirmada` no se infiere; si es verdadera exige `evidencia_lectura` interna. La evidencia y la justificación de uso no se imprimen en la web.
- Fechas: `AAAA-MM-DD` reales. `fecha_publicacion` exige `fuente_publicacion_url`. No rellenar un día ficticio si solo se conoce el año: dejar ambos vacíos hasta verificar. `fecha_actualizacion` refleja una revisión editorial real.
- `edad_recomendada`: texto orientativo, por ejemplo una recomendación editorial documentada; exige `fuente_edad_url`. Las etiquetas de edad no sustituyen este dato. `avisos_contenido` permite explicar intensidad, violencia u otros contenidos relevantes sin afirmar que una edad sea una garantía universal.
- `edicion` identifica la edición cuya portada, ISBN y enlace se han revisado. ISBN-13 sin guiones, checksum válido y único. **Una obra, una ficha**: no crear otras fichas por edición, temporada o idioma. En esta versión se publica una edición seleccionada; un modelo de múltiples ediciones se ampliará antes de importar variantes.
- `portada_local`: `/assets/reading-covers/<clave-estable>.webp` (también JPG/PNG). Imagen real optimizada, con dimensiones exactas; el validador abre el archivo y comprueba formato, integridad y tamaño. No duplicar rutas ni bytes entre libros. Conservar fuente, edición, base de uso y fecha de revisión. Una URL pública no acredita por sí sola autorización. No usar portadas generadas ni alterar la cubierta.
- URLs externas: HTTPS sin credenciales. `fuente_bibliografica_url` apunta a la edición verificable, preferiblemente editorial o biblioteca.
- `url_amazon_afiliada`: opcional; enlace de producto `amazon.es/dp/<ASIN>?tag=<tag-real>` (también `gp/product`) o corto `amzn.to` generado y comprobado por el propietario. No inventar tag ni enlaces. Los cortos se revisan manualmente hasta su destino final y edición. Sin URL no se imprime botón Amazon ni divulgación de compra de esa ficha. No se importan precios, disponibilidad ni puntuaciones.
- `resenas`: celda con un array JSON de objetos `{"titulo":"…","url":"https://…","fecha_verificacion":"AAAA-MM-DD"}`; vacío equivale a `[]`. Son enlaces externos verificados y rotulados como tales, sin copiar el texto ni fabricar estrellas o schema Review. `fragmento_url` enlaza a la muestra oficial; no se descarga ni se reproduce automáticamente texto ajeno.

**LibroCategorias**

`libro_id, categoria_id`

Una fila por relación. Un libro puede tener varias categorías del mismo tipo. No repetir parejas; todas las claves deben existir. Para publicar debe haber al menos una categoría activa. En el futuro importador se convierten las tres hojas en las listas JSON `libros`, `categorias` y `libro_categorias`. Las columnas desconocidas fallan: no volcar notas o seguimiento privado al dataset público por accidente.

## Generación y revisión de la fase de importación

1. Exportar y convertir las tres hojas: fechas como texto ISO, booleanos nativos JSON, `autores` como lista, celdas opcionales vacías omitidas, `resenas` como array. La conversión/importación masiva se implementará en otra PR.
2. Revisar originales, permisos, fuentes, edades y destinos afiliados. Añadir las imágenes locales verificadas. No cambiar `id` ni `slug` de fichas ya publicadas.
3. Ejecutar `python scripts/build-reading-catalogue.py`. Genera el hub y las fichas `/recomendaciones/libros/<slug>/`, y actualiza las entradas `reading-book-*` de `data/content-registry.json`. Detecta páginas huérfanas y exige revisar retiradas antes de borrar URLs.
4. El generador mantiene los enlaces a las fichas en un bloque del mapa humano del sitio (desplegable nativo) y sus entradas en el registro. Añadir las nuevas páginas e imágenes a Git antes de regenerar los índices, que parten de archivos versionados. Ejecutar `python scripts/build-site-shell.py`, `python scripts/build-section-context-nav.py`, `python scripts/build-sitemap.py` y `python scripts/build-pagefind-index.py`. El sitemap XML incluye las fichas indexables y Pagefind las incorpora al buscador.
5. Ejecutar `python scripts/build-reading-catalogue.py --check`, `python tests/test-reading-catalogue.py`, `node qa/reading-catalogue-browser.mjs` y los controles habituales de publicación. Revisar visualmente móvil y escritorio antes de fusionar.

Las fichas incluyen portada con tamaño explícito, canonical propio, Book/WebPage/BreadcrumbList, metadatos sociales y retorno al catálogo. Los filtros combinan dimensiones con AND y usan fragmentos (`#genero=…`), sin crear páginas indexables por cada combinación. Sin JavaScript siguen estando todas las fichas y enlaces en HTML. Las páginas editoriales de categorías podrán incorporarse cuando tengan contenido suficiente.

La lectura en voz alta usa las voces disponibles en el navegador tras pulsar «Escuchar descripción». Solo lee la descripción original; no se incorpora un proveedor ni un servicio propio de TTS. Si el navegador no admite esta función los controles permanecen ocultos. Los fragmentos externos conservan su enlace oficial.

Pinterest se configurará después: cada pin apuntará a la ficha web canónica que contiene la portada, y esa ficha ofrecerá el enlace afiliado cuando exista. En esta fase no se publican pines ni se crean tableros.

Referencias verificadas: [navegación por filtros, Google](https://developers.google.com/crawling/docs/faceted-navigation), [políticas de Amazon Afiliados](https://afiliados.amazon.es/help/operating/policies). La estructura facilita descubrimiento y evita duplicados; no garantiza posiciones de búsqueda.
