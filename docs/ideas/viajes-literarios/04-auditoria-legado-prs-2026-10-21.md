# 04 · Auditoría del legado y dependencias PR — 21/10/2026

## Hallazgo central: EXISTE un atlas previo real, aún no publicado

**PR [#59](https://github.com/davidpd89/web-escritor/pull/59)** (cerrada y fusionada, rama base histórica `implementacion-web-2026`) incluye F.3 y deja operativo un andamiaje de Atlas Literario, con pruebas; **no ha publicado fichas**. Se comprueba en main:

| Pieza presente | Función real | Limitación comprobada por lectura de código |
| --- | --- | --- |
| [data/atlas-literario.json](https://github.com/davidpd89/web-escritor/blob/main/data/atlas-literario.json) | 12 ideas en `status: planned`, seis categorías | Es backlog de artículos, NO un modelo de POIs relacionales, ni catálogo público |
| [scripts/build-atlas-literario.py](https://github.com/davidpd89/web-escritor/blob/main/scripts/build-atlas-literario.py) | Valida slugs únicos, categoría, tipo relación, URL HTTPS y requisitos mínimos de imagen de publicados; genera índice `dist/atlas-literario/index.html` y JSON filtrado | **No genera fichas individuales**, pese a que `card()` enlaza a `/atlas-literario/<slug>/`. No validar si una fuente efectivamente demuestra la relación, derechos fotográficos, coordenadas, fecha ISO, obras/autores o relación múltiple |
| [assets/atlas-literario.js](https://github.com/davidpd89/web-escritor/blob/main/assets/atlas-literario.js) | Búsqueda normalizada y filtro de una sola categoría sobre tarjetas HTML | Sin filtro ciudad/libro/autor, sin mapa, sin facetas combinadas n:m; los enlaces no deben activarse sin página real |
| [assets/atlas-literario.css](https://github.com/davidpd89/web-escritor/blob/main/assets/atlas-literario.css) | Tarjetas y grid móvil básico | Plantilla cromática antigua; no está integrada con diseño editorial actual, CSP y shell por sí misma |
| [tests/test-atlas-literario.py](https://github.com/davidpd89/web-escritor/blob/main/tests/test-atlas-literario.py) | Prueba de metadatos mínimos + exclusión de planned | Solo dos grupos focalizados; no cubre URLs destino, seguridad del contenido, datos relacionales, ni sincronización y SEO |

**Detalle importante por lectura del código:** `card()` intenta renderizar `/assets/atlas-literario-placeholder.webp` si falta imagen. La consulta a la ruta en main devolvió 404; como `published` exige `image.src`, el fallback no debería sustituir a contenido real. No usar imagen ficticia de respaldo público.

`build()` tampoco pasa por el shell generado de la web actual ni integra registro de contenido, mapa humano, Pagefind y sitemap. Puede generar páginas aisladas en `dist/`, pero eso NO equivale a haberlas desplegado. No prometer que la infraestructura esté lista para lanzamiento.

**Decisión técnica recomendada:** reutilizar el **concepto, dataset semilla y lógica positiva de aislamiento de borradores**, refactorizarlo cuando se apruebe desarrollo. No replicar ciegamente el render de índice; primero establecer entidades independientes de lugar, destino, obra, autor, relación y fuente con catálogo existente como autoridad.

## Ruta y nomenclatura: decisión antes del primer contenido público

Código legado fija `/atlas-literario/` como canonical y destino de tarjeta. La PR #666 propuso `/viajes-literarios/` como idea. **Ninguna de las dos rutas parece publicada por este builder.** Recomendación provisional: preferir **/atlas-literario/** para evitar doble concepto técnico y aprovechar nombre existente, mostrar al usuario «Viajes literarios» como título editorial y enlazar desde Cuaderno. Alternativa B: /viajes-literarios/ si se considera imprescindible; implica modificar builder, internal links, canonical, tests y futuros redirects. **No crear ambas rutas indexadas simultáneamente.** Comprobar rutas generadas y estado SEO real antes de decidir.

## Relaciones entre PR (consultadas en GitHub el 21/10/2026)

| PR | Estado observado | Dependencia/actuación futura |
| --- | --- | --- |
| [#59 — F.3 Atlas original](https://github.com/davidpd89/web-escritor/pull/59) | fusionada | **Referencia de partida directa**; documentación, script, test y assets |
| [#660 — Catálogo libro/UX](https://github.com/davidpd89/web-escritor/pull/660) | fusionada | Reusar entidades e IDs /recomendaciones/libros/; conservar UX/filtros |
| [#661 — Ingesta automática](https://github.com/davidpd89/web-escritor/pull/661) | fusionada | Estudiar pipeline, snapshot, validación, PR writer y cron existentes; NUNCA crear un segundo autopublisher competidor |
| [#662 — Pinterest vía RSS](https://github.com/davidpd89/web-escritor/pull/662) | abierta, draft | Eventual canal de difusión: feed **diferente** por tipo y destino, solo tras verificar límites/estado real; no modificar esta rama |
| [#665 — UX/ratings catálogo](https://github.com/davidpd89/web-escritor/pull/665) | abierta, draft | Reconocer cambios de modelo/IDs y datos de libros solo cuando se fusionen; no consumir su schema como vigente |
| [#666 — Esta investigación](https://github.com/davidpd89/web-escritor/pull/666) | abierta, draft | Capturar hallazgos y decisiones sin ejecutar Jobs o tocar sitio |

**Dependencias con la web:** `data/content-registry.json`, `data/navigation.json`, `scripts/build-site-shell.py`, `scripts/build-section-context-nav.py`, `scripts/build-sitemap.py`, `scripts/build-pagefind-index.py`, `scripts/build-reading-catalogue.py`, generadores de páginas y su QA correspondiente. Leer versión main **del día del comienzo de implementación**, no asumir que ramas 662/665 permanecen iguales.

## Puntos de seguridad/consistencia a cubrir en PR futura

- Reemplazar solo enlaces a fichas que **existen y están aprobadas**. Rechazar índices que generen enlaces a contenido inexistente.
- Añadir proceso de plantillas de detalle reutilizando shell/tokens; no copiar HTML antiguo a la web moderna.
- Sistema de campos n:m y búsqueda ciudad, libro, autor, categoría, certeza. Deduplicación de POIs, no solo de artículos.
- Convertir source_urls en evidencias **relación-lugar** con fecha y tipo; control editorial separado del simple HTTPS.
- Proteger privacidad de domicilios actuales/autores vivos; precisión reducida si la ubicación es sensible.
- Añadir licencias/fotografías con ficha de atribución; imagen opcional si no hay alternativa autorizada.
- Estudiar generación de páginas, canonical, indexabilidad y sitemap en conjunto con catálogo de libros.
- Evitar cron propio que fusione a main sin revisión y evite colisiones con la ingesta de #661.
- En fase posterior, pruebas de publicación solo cuando el propietario active desarrollo; **esta PR solo documenta**.

**Sin acciones realizadas aquí:** no se ha generado/ejecutado el Atlas, no se han ejecutado tests/CI, no se ha cambiado ni publicado código ni datos.
