# Auditoría noindex + keyword research + interlinking (2026-09-07)

Fuentes: `data/content-registry.json`, `scripts/build-public-dist.py` (allowlist real de lo publicado), Bing Webmaster Tools (AI Performance + Search Performance), Google Search Console (Rendimiento, consultas + posición real), y un grafo de enlaces internos calculado directamente sobre el HTML fuente (no estimado).

## 1. Auditoría sitewide de noindex/nofollow/searchIndex:false/sitemap

Resultado: **sin hallazgos**. Se revisaron las tres capas de exclusión de forma independiente y las tres coinciden:

- 37 páginas HTML con `noindex` en el repo; descartadas una por una (404/offline/tests/`lab/` no publicado, páginas legales estándar, páginas de retirada deliberada ya documentadas, o reportes internos como `/herramientas/auditor-web/` que no son contenido para lector).
- 9 entradas de `content-registry.json` con `status` gated/`searchIndex:false`/`sitemap:false`; las 9 tienen una razón explícita y verificada (RSS, `/ai/`, legal, retirada temporal, ruta de staging aún sin publicar, herramienta deprecada y ya devuelve 404 en producción).
- Cero páginas indexables presentes en el dist público (`scripts/build-public-dist.py`) que no estén registradas en `content-registry.json` (comprobado programáticamente, no por muestreo).
- `robots.txt` sin ninguna regla `Disallow`.
- `scripts/build-sitemap.py --check` (que ya exige que el sitemap se derive exactamente del HTML indexable) pasa en verde.

No se ha convertido ninguna página a indexable porque no existe ninguna candidata real: el propio sistema de gates del repo ya lo garantizaba antes de esta sesión.

## 2. Keyword research + Bing AI Performance + Google Search Console

La herramienta de "Keyword Research" de Bing no respondió con sugerencias durante esta sesión (probado con varias frases semilla); se sustituyó por datos reales de comportamiento, que son más fiables que un estimador de volumen:

### Bing AI Performance (citas de Copilot/Bing, 3 meses)

Páginas citadas, de más a menos:

| Página | Citas |
| --- | --- |
| `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` | **29** |
| `/cuaderno/que-es-el-portal-fantasy/` | 10 |
| `/recomendaciones/portal-fantasy-espanol/` | 7 |
| `/recomendaciones/magia-con-coste/` | 3 |
| `/` | 2 |
| `/autor.html` | 1 |
| `/libros/samuel-entre-mundos/` | 1 |

La consulta que más cita esta web es "libros de fantasía juvenil", con un **18,52 % de cuota de citación**.

### Google Search Console — consultas reales con posición (no filtradas, 161 consultas totales revisadas)

Dos patrones claros y opuestos:

**A. Cluster ganador (posición 1-9, ya en página 1):** "sistema de magia" (1,7), "sistemas de magia"/"sistemas de poder"/"libros de fantasía y magia" (1,0), "fantasía" (2,0), "es un portal"/"la magia"/"high fantasy" (2,0), "magia" (4,2), "hard magic" (5,4), "noveris" (5,9), "portal fantasia" (5,9), "portal fantasy" (6,3), "portales fantasia" (6,5), "fantasia de portal" (7,2), "mapa de personajes" (8,6), "nocturna ediciones manuscritos" (4,8), "test tipo de lector" (9,0). Esto confirma que el contenido central del sitio (portal fantasy, sistema de magia, Noveris, y las páginas de `/editoriales/` para escritores que buscan editorial) ya rankea bien; el volumen absoluto es bajo porque son términos de nicho, no porque falte optimización on-page.

**B. Cluster perdedor, no accionable sin autoridad externa:** toda la familia "contador de palabras" (contador de palabras, contar palabras, cuenta palabras, contador palabras, contador de parrafos, recuento de palabras, contador de palabras pdf, etc. — más de 30 variantes) rankea entre la posición 24 y la 90, con cientos de impresiones acumuladas y cero clics. Es un término genérico de utilidad, extremadamente competido; no es arreglable con título/meta (ya están bien escritos) sino con autoridad de dominio, que es exactamente el hallazgo ya documentado en `docs/BACKLINK-AUTHORITY-GAP-2026-09-07.md`. Se decide **no perseguirlo** por esta vía ahora: los datos muestran que no es ganable a corto plazo.

Revisado también: la aparente inconsistencia entre "qué tipo de lector eres" (posición 38-39) y "test tipo de lector" (posición 9) para la misma página — no hay contenido duplicado ni error on-page (el título ya contiene la frase exacta); es variación normal de ranking en una página con poca autoridad entrante, no un bug.

## 3. Interlinking — hallazgo real y corregido

Grafo de enlaces internos calculado directamente sobre el HTML (no una estimación): la página **#1 en citas de IA** (`/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/`, 29 citas Bing) tenía **un solo enlace entrante** en todo el sitio (desde `/mapa-del-sitio/`, que no cuenta como enlace editorial real) — ni siquiera aparecía listada en el propio índice del Cuaderno (`/cuaderno/`), que se quedó desactualizado ("05 piezas publicadas" cuando ya había 6).

Corregido en esta sesión:
- Añadida al archivo de `/cuaderno/` (entrada 06, contador actualizado a "06 piezas publicadas", añadida al `hasPart` del `CollectionPage` JSON-LD).
- Añadidos enlaces contextuales recíprocos entre esta pieza y sus 5 vecinas temáticas más cercanas (`que-es-el-portal-fantasy`, `fantasia-juvenil-espanola-portales-magia-coste`, `portal-fantasy-vs-fantasia-epica`, `recomendaciones/portal-fantasy-espanol`, `recomendaciones/magia-con-coste`) — en varios casos rellenando una frase que ya prometía el enlace en prosa ("descubre qué se está escribiendo ahora en español") pero no lo tenía.
- Resultado: de 1 a 7 enlaces entrantes desde páginas indexables distintas.

Efecto colateral encontrado y corregido: `/cuaderno/worldbuilding-noveris-ciudad-magica/` enlazaba a `/cuaderno/sistema-de-magia-noveris/`, una pieza retirada deliberadamente (`noindex`, "contenido temporalmente retirado"). No rompía nada (la URL sigue respondiendo 200), pero llevaba al lector a un aviso de retirada en vez de contenido real. Redirigido a `/universo/noveris/#glosario`, que cubre el mismo tema (canalizadores, sistema de magia) y sí es indexable.

Las páginas que el usuario pidió explícitamente reforzar (Manecillas, Kindle, Fragmentos, lectores-beta) **ya estaban al máximo de refuerzo posible**: 60-89 enlaces entrantes cada una, porque forman parte de la cabecera/footer/diálogo Explorar que se repite en las ~60 páginas indexables del sitio. No había nada que mejorar ahí — confirmado con datos, no asumido.

## Verificación

`scripts/check-internal-graph.py`, `scripts/check-breadcrumb-parity.py`, `qa/section-context-parity.mjs`, `scripts/check-local-assets.py`, `scripts/check-heading-structure.py`, `scripts/build-article-tools.py --check`, `scripts/check-canonical-entity-ids.py`, `scripts/check-article-dates.py --check`, `scripts/build-site-shell.py --check`, `scripts/check-asset-versions.py`, `tests/test-faq-schema-retirement.py`, `scripts/check-recomendaciones-no-faqpage.py --check`: todos en verde tras los cambios.
