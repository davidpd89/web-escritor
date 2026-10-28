# Investigación REP-01 — aprovechar Pagefind existente (24-10-2026)

**Estado**: preselección técnica documentada; todavía no se ha demostrado una carencia de búsqueda.

## Qué hay ya

El sitio usa Pagefind, lo compila mediante `scripts/build-pagefind-index.py`, tiene pruebas de relevancia y búsqueda en `qa/pagefind-search-relevance-browser.mjs` y fija la dependencia en `package.json`. No instalar un segundo buscador ni reescribir su UI por moda.

## Código original inspeccionado en el repositorio upstream

- Repositorio canónico: https://github.com/Pagefind/pagefind (trasladado desde la organización CloudCannon).
- Licencia MIT, archivo `LICENSE`, blob Git `1bd8b4bc2b5b3ceba855e753ece50ab0e0e8b46f`.
- Archivo `docs/content/docs/api.md`, blob Git `e1e128648341f46e33013cdc230e13db0e5082ae`.
- Archivo `docs/content/docs/filtering.md`, blob Git `7216f150f8a98b13336dcf38b849219996fe9e54`.
- Archivo `docs/content/docs/sorts.md`, blob Git `deaa16cf605a214054dc96bb39fdc3fd0e5e31ad`.
- Documentación pública actual: https://pagefind.app/docs/filtering/ y https://pagefind.app/docs/sorts/.

**Fragmentos LITERALES upstream, NO adaptaciones**:

API JS (docs/content/docs/api.md):
```js
const pagefind = await import("/pagefind/pagefind.js");

pagefind.init();
```

HTML de atributos para filtros (docs/content/docs/filtering.md):
```html
<h1>My Blog Post</h1>
<p>
    Author:
    <span data-pagefind-filter="author">bglw</span>
</p>
```

Ordenación (docs/content/docs/sorts.md):
```html
<p data-pagefind-sort="date">2022-10-20</p>
```

No se ha copiado código de biblioteca a producción, y el muestreo documental **no equivale** a una auditoría completa de Rust/JS, tests y distribución. Revisar versión efectiva `pagefind` de `package-lock.json` y compatibilidad API antes de integrar.

## Dos caminos

- **A. Mejorar el índice que ya existe**: medir un pequeño conjunto de consultas reales, revisar etiquetas/facetas y corregir solo casos concretos. No cambia librería.
- **B. Nueva interfaz facetada** si la A no cubre tareas demostradas: usar capacidades integradas `data-pagefind-filter`/`data-pagefind-sort` y comprobar contraste, foco, estados y tamaño del bundle. Sin importar un framework nuevo.

Antes de PR hija: baseline de 20-25 consultas, distribución por sección, medición de relevancia y pruebas existentes en verde. El índice solo admite mejoras SEO en las páginas de destino si estas aportan contenido real; filtrar en el navegador no crea páginas indexables por sí solo.
