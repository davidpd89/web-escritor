# 02 — Rastreo, indexación, canónicas y sitemaps

## Objetivo

Hacer que Google reciba una señal coherente sobre:

- qué URLs existen;
- cuáles deben rastrearse;
- cuáles deben indexarse;
- cuál es la versión canónica;
- cuáles han cambiado de verdad;
- cuáles han desaparecido;
- cuáles son internas/gated/noindex.

La disciplina aquí reduce desperdicio de rastreo, duplicidad, stale snippets y errores de consolidación. No «sube posiciones» de forma mágica; evita que el resto del trabajo compita contra una arquitectura ambigua.

---

# 1. Modelo de estados recomendado

Cada entrada del `content-registry` debe resolverse a uno de estos estados públicos SEO.

| Estado | HTTP | robots | sitemap | canonical | enlaces internos |
|---|---:|---|---|---|---|
| public/indexable | 200 | index,follow | sí | self | sí |
| public/noindex | 200 | noindex,follow | no | self o según caso | contextual |
| gated/internal | no publicado o auth | n/a/noindex | no | n/a | no público |
| moved | 301/308 | n/a | no old URL | destination | solo destination |
| gone | 404/410 | n/a | no | no | retirar |
| temporary outage | 503 | n/a | no cambio | n/a | n/a |

No usar un 200 con mensaje «página no encontrada».

---

# 2. `robots.txt`

Estado actual:

- `User-agent: *` permitido;
- sitemap declarado;
- bots de IA documentados de forma separada.

Para Google Web Search esto es suficiente. No se necesita una sección `Googlebot` específica para «mejor SEO».

## Reglas

1. No usar `robots.txt` para retirar una URL del índice.
2. Si una URL debe salir de Google mediante `noindex`, Google debe poder rastrearla para ver ese `noindex`.
3. No bloquear CSS/JS necesarios para renderizado.
4. No publicar rutas operativas solo porque robots las bloquee. `robots.txt` no es control de acceso.
5. No añadir `crawl-delay`: Googlebot no lo utiliza como control estándar.
6. No bloquear parámetros a ciegas; no existe ya la antigua herramienta URL Parameters de Search Console.

---

# 3. Sitemap

## 3.1 Fuente

El sitemap debe derivarse de `data/content-registry.json` + hechos de build, no de un `find *.html`.

Condición:

- `status=public`;
- `sitemap=true`;
- URL indexable;
- source presente en public dist;
- status final 200;
- canonical self.

## 3.2 No incluir

- `noindex`;
- staging;
- gated;
- deprecated;
- redirects;
- 404/410;
- URLs con fragment `#...` como entidades separadas;
- URLs con parámetros tracking;
- URLs duplicadas;
- JSON/llms/feeds salvo que exista una razón específica de Search, no por completitud.

## 3.3 Home

Normalizar:

`https://davidportodiaz.com/`

No mantener la variante sin slash en `<loc>` mientras la canonical lleva slash.

## 3.4 `lastmod`

Google indica que usa `lastmod` cuando es consistentemente exacto.

Debe reflejar cambio significativo en:

- contenido principal;
- structured data relevante;
- enlaces principales/arquitectura de la página;
- disponibilidad/factual data importante.

No debe cambiar por:

- build sin cambios sustanciales;
- actualización del footer global si no altera la página de forma material;
- whitespace;
- fecha de copyright;
- mera regeneración;
- commit que solo toca tests/docs.

### Diseño recomendado

Añadir al registry o al source factual un campo del tipo:

```json
"seoLastModified": "2026-08-27"
```

solo si el proyecto puede mantenerlo con rigor.

Alternativa: generarlo de una autoridad editorial por familia.

Si no existe una fuente fiable, omitirlo es mejor que mentir.

## 3.5 No usar

Google ignora `priority` y `changefreq`; no añadirlos para decorar.

---

# 4. Canonicalización

Google combina múltiples señales:

- redirects: señal fuerte;
- `rel=canonical`: señal fuerte;
- sitemap: señal débil;
- consistencia interna: refuerzo.

## Contrato

Una URL indexable debe:

- devolver 200;
- incluir canonical absoluta HTTPS;
- aparecer en sitemap con exactamente la misma URL;
- recibir enlaces internos hacia esa forma;
- usar esa forma en schema/OG;
- no exponer duplicados accesibles sin necesidad.

## Variantes a comprobar en producción

Para cada URL crítica:

- HTTP → HTTPS;
- `www` → no-www si esa es la autoridad;
- `/index.html` → `/` cuando aplique;
- trailing slash;
- mayúsculas/minúsculas;
- parámetros de tracking;
- antiguas rutas históricas.

### Resultado esperado

Una sola URL final estable.

---

# 5. Redirects

## 5.1 Permanent move

Usar 301/308 server-side cuando una URL tenga sustituto claro.

Ejemplos de futuras migraciones:

- slug de artículo mejorado;
- consolidación de dos herramientas;
- cambio de ruta de un libro;
- detalle de evento movido.

## 5.2 No redirigir todo a home

Una URL eliminada sin reemplazo debe devolver 404/410.

Redirigir cualquier cosa a la home:

- confunde al usuario;
- puede convertirse en soft 404;
- dificulta entender la arquitectura.

## 5.3 Mapa de redirects

Mantener una tabla versionada:

`old_url → new_url → reason → date → permanent`

Testear chains.

### Gate

- 0 redirect chains >1 salto en rutas nuevas;
- no loops;
- internal links siempre a destination final.

---

# 6. 404, 410 y soft 404

## 404

Usar cuando el recurso no existe/no se encuentra.

## 410

Útil cuando la retirada es deliberada y definitiva.

No es obligatorio usar 410; 404 también permite que Google retire una URL.

## 200 noindex retired page

Puede ser correcto cuando la URL se conserva para explicar una retirada temporal y sigue ofreciendo navegación útil, como el actual artículo retirado de Noveris.

No convertir toda retirada en 404 por automatismo.

## Soft 404

Auditar:

- páginas con muy poco contenido que dicen «no disponible» pero devuelven 200 indexable;
- redirects irrelevantes;
- resultados vacíos de herramientas/directorios con URL indexable.

---

# 7. Noindex

## Buen uso actual

- legal cuando no se desea en Search;
- beta;
- staging/editorial hold;
- artículos retirados.

## Regla

Noindex no es mecanismo de seguridad.

Si algo contiene:

- secretos;
- datos personales;
- archivos internos;
- QA;
- migrations;
- source;

no debe publicarse, aunque tenga noindex.

El allowlist-first del public artifact sigue siendo la barrera principal.

---

# 8. Páginas temporales y prelaunch

Para Manecillas:

- la URL puede existir antes del lanzamiento;
- no hay necesidad de retirar/indexar por fecha automáticamente;
- los hechos deben ser coherentes con el contrato editorial;
- la disponibilidad comercial solo aparece cuando se verifique.

No cambiar una página de indexable a noindex solo porque el libro aún no pueda comprarse.

---

# 9. JavaScript y renderizado

Google renderiza JavaScript desde hace años, pero:

- el contenido principal ya está en HTML;
- esta propiedad debe preservarse;
- status/canonical/meta no deben depender de hidratación;
- `<a href>` real para navegación;
- tool JS debe mejorar la utilidad, no crear el único contenido indexable.

## No hacer

- title/meta generados solo después de interacción;
- links como `div onclick` sin href;
- contenido SEO oculto en payload JS que no ve el usuario;
- render condicionado al user-agent.

---

# 10. Crawl depth

Una URL estratégica debería estar accesible idealmente en:

- <=3 enlaces desde home por rutas razonables;
- <=2 desde su hub principal.

No porque Google tenga un número mágico de clicks, sino porque una arquitectura profunda suele indicar menor prioridad y peor descubrimiento.

## Prioritarias

- Autor;
- Obras;
- Manecillas;
- Samuel;
- Cuaderno;
- Herramientas;
- Editoriales;
- Convocatorias;
- Recomendaciones;
- Eventos;
- topic hubs principales.

---

# 11. Crawl budget

Para un sitio de este tamaño no es el problema principal.

No invertir tiempo en «optimizar crawl budget» como si tuviéramos millones de URLs.

Sí evitar:

- duplicados infinitos;
- parámetros indexables;
- calendarios infinitos;
- facetas crawlables sin valor;
- URLs generadas por estado de herramienta;
- búsqueda interna indexable;
- feeds duplicados enlazados masivamente.

---

# 12. Parámetros

Si en el futuro se usan filtros:

- no crear URLs indexables para cada combinación salvo que tengan intención y contenido únicos;
- canonical al estado base cuando sea una vista de UI;
- no enlazar masivamente combinaciones;
- usar History API con cuidado;
- Search Console ya no ofrece la antigua herramienta URL Parameters.

---

# 13. Sitemap especializado

## Image sitemap

No crear por defecto.

Evaluarlo si:

- imágenes clave no se descubren mediante `<img>` normal;
- hay assets editoriales que merecen Google Images;
- las imágenes están en CDN/paths poco enlazados.

Las portadas y foto de autor principales ya están referenciadas en HTML/schema/OG, por lo que el beneficio debe medirse.

## Video sitemap

Solo cuando exista una estrategia real de vídeo alojado/embed con páginas indexables.

## News sitemap

Solo si el Cuaderno llega a producir un flujo real de noticias aptas para Google News. No crear un News sitemap para artículos evergreen por estética SEO.

---

# 14. Producción vs repo

## Problema

GitHub no es lo que Google indexa.

## Pipeline de verificación

Para una URL crítica:

1. contenido en `main`;
2. public artifact correcto;
3. deploy finalizado;
4. fetch producción;
5. status HTTP;
6. canonical;
7. robots meta;
8. title/H1;
9. JSON-LD;
10. sitemap;
11. URL Inspection;
12. recrawl;
13. SERP.

## Registro

Crear un pequeño `seo-release-verification` para cambios de:

- ISBN;
- fecha;
- editorial;
- retailer;
- premio;
- nombre/título;
- URL/canonical;
- noindex;
- redirects.

---

# 15. Automatización recomendada

## `scripts/seo/build-sitemap.py`

Responsabilidades:

- leer content registry;
- confirmar source/public dist;
- solo indexables;
- canonical normalization;
- exact home slash;
- lastmod factual;
- deterministic output;
- `--check`.

## `scripts/seo/audit-indexability.py`

Reportar por URL:

- registry id;
- sitemap expected;
- file;
- robots meta;
- canonical;
- status esperado;
- mismatches.

## `tests/test-seo-indexability-contract.py`

Assertions:

- sitemap no contiene noindex;
- sitemap no contiene fragment URLs;
- sitemap no contiene gated;
- canonical de sitemap coincide;
- home slash;
- no duplicate loc;
- every public indexed registry source can map to a canonical public URL;
- every noindex registry entry omitted.

---

# 16. Search Console

No duplicar `docs/search-console/`.

Para esta capa técnica se usa Search Console para verificar:

- Pages/Indexing;
- Sitemaps;
- selected canonical;
- URL Inspection;
- Crawl Stats;
- HTTPS;
- Manual Actions;
- Security Issues.

La definición del cambio está en esta carpeta; la operación del producto está en `docs/search-console/`.

---

# 17. Acceptance criteria

La capa rastreo/indexación queda madura cuando:

- una sola canonical por recurso;
- sitemap exacto y deterministic;
- home normalizada;
- noindex fuera del sitemap;
- gated fuera de public artifact;
- redirects sin chains;
- 404/410 semánticos;
- no soft 404 sistemáticos;
- `lastmod` fiable o ausente;
- status y canonical no dependen de JS;
- producción se verifica después de releases factuales;
- los stale facts conocidos se han cerrado en Google, no solo en Git.
