# Investigación de GPT — fichas de libros, SEO y escalabilidad

**P2 · DRAFT · NO MERGEAR.** Coordinación: [#691](https://github.com/davidpd89/web-escritor/pull/691). Dependencias: catálogo [#687](https://github.com/davidpd89/web-escritor/pull/687), precios/valoraciones [#683](https://github.com/davidpd89/web-escritor/pull/683), Planeta [#680](https://github.com/davidpd89/web-escritor/pull/680), control QA [#613](https://github.com/davidpd89/web-escritor/pull/613).

## Gap concreto

Ya existen fichas de libro, de autor y de editoriales; enlazado ISBN/sello/autor; `Book`, `Person`, sitemap, portadas y búsqueda. La **PR #687 no fusionada** propone fichas homogéneas, PVP editorial, más categorías y 55 libros. No debemos recrearlo ni afirmar que está desplegado. Quedan sin cerrar: **medir render masivo**, controlar contenido repetido y duplicados en distintas ediciones, enlazado bidireccional entre **dos registros editoriales**, verificación de datos por campo, coherencia de precio/valoración y QA de usabilidad.

## Definición de ficha útil — misma estructura, sin contenido artificial

**Libro:** portada oficial de la edición, título, autor/es enlazados, edición/ISBN/idioma/páginas/fecha con precisión real, editorial y grupo cuando proceda, sinopsis con atribución, géneros/temas basados en fuentes, botón a tienda, valoración atribuida por proveedor si hay verificación, libros relacionados, fecha y fuentes de revisión. Distinguir ficha bibliográfica, reseña propia y oferta comercial.

**Autor:** identidad y fuentes, libros presentes en nuestro catálogo, temas derivados, editoriales relacionadas y biografía corta verificada; estados vacíos naturales.

**Editorial:** grupo/sellos, catálogo de libros y autores enlazados, web/contacto general verificado y **sección aparte** para manuscritos con fecha y estado. No afirmar que no acepta manuscritos si no consta.

**Navegación:** rutas canónicas y breadcrumbs consistentes; datos estructurados `Book`, `Person`, `Organization` solo con datos visibles/sostenibles. No añadir estrellas de Goodreads/Google como `aggregateRating` propio; respetar reseñas consentidas. Canonical entre libro físico/eBook se decide por obra/edición, no por coincidencia de título. No hacer SEO con miles de fichas de un párrafo repetido.

## Experimentos priorizados

- **F1:** inventario de 31 libros en `main` y 55 de #687; medir cobertura de datos por atributo, homogéneo vs vacío, enlaces internos rotos y formatos ISBN; contrastar diferencias con la plantilla existente, no proponer cambios redundantes.
- **F2:** benchmark local de 200/500/1000 libros (HTML, tamaño DOM, memoria, JS, Pagefind, paginación visible 24, LCP/INP/CLS y móvil). Decidir paginación estática/índices particionados solo cuando haya números.
- **F3:** contratos de enlaces cruzados autor ↔ libro ↔ sello/grupo y de duplicado por obra/ISBN, fallbacks accesibles y fuente por campo.
- **F4:** matriz UX/SEO con 3 fichas representativas y casos sin precio, sin bio, sin ratings, varias ediciones, sinopsis atribuida y portada sin permiso. Proponer cambios mínimos al builder; fixture sintético y pruebas sin red.
- **F5:** integrar exclusivamente lo que no exista tras fusionar #687 y tras resolver #683; **no** implementar segunda solución de precio ni automatización diaria paralela.

## Fuentes y restricciones

- [Google Search — políticas antispam](https://developers.google.com/search/docs/essentials/spam-policies) y [structured data reseñas](https://developers.google.com/search/docs/appearance/structured-data/review-snippet): indexabilidad y marcación de datos veraces; no garantía de fragmentos enriquecidos.
- [Google Books Volume](https://developers.google.com/books/docs/v1/reference/volumes) para contrastar ediciones/metadatos y valorar cobertura, pero su `saleInfo` corresponde a Google Play y no a Amazon.
- [Open Library](https://openlibrary.org/developers/api) para consultar metadatos de forma limitada; no backend masivo; obras y ediciones distintas.
- [DILVE / ONIX 3.1](https://web.dilve.es/onix/estandar-versiones-editeur/) para feeds estructurados **autorizados**, sujeto a licencia.
- Investigar código público adicional **solo si** prueba necesidad real y licencia compatible; registrar alternativas con rendimiento y riesgo.

**Salida:** informe corto de medidas + fixture/offline QA + propuesta de cambios verificables, sin difundir contenido duplicado. **No se ha ejecutado build, pruebas, Actions ni despliegue.**
