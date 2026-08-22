# CONTENT PARITY — LIBROS + LAS MANECILLAS DEL RECUERDO V1

Fecha de revisión: 2026-08-22
Base fijada: `0ec22de14a36f8c913777f413e070273ece4f219` (`implementacion-web-2026`)
Referencia histórica comparada: `main` `645b7d84c7441fe6e2cd87752823d9bfa6e2e0da`

## Autoridad y criterio

La autoridad factual de esta revisión es `editorial-facts.json` de la base, leído pero no modificado. Para Manecillas fija: Monza Ediciones, publicación 2026-09-03, ISBN 979-8-90514-935-1, 272 páginas, PVP editorial 16 €, formato Paperback y géneros Novela coral / Ficción especulativa / Narrativa familiar. `purchaseUrl` continúa `null`: no se publica `Offer`, disponibilidad comercial ni retailer inventado.

También se contrastaron `MANECILLAS-MIGRATION.md`, `MIGRATION-MATRIX.md`, los fixtures V1 de Libro/Libros, `data/content-registry.json`, `data/navigation.json`, `main` y los materiales de Drive de lanzamiento, fragmentos, proceso, club y prensa. Las capas globales se usaron solo como lectura.

Una documentación de Drive del 16/08 todavía marcaba el formato como pendiente. Eso queda supersedido para esta tarea por `editorial-facts.json`, cuya revisión actual confirma `Paperback`. No se modifica la documentación histórica desde este scope.

## Inventario BEFORE → AFTER

| Área | BEFORE en base | AFTER |
| --- | --- | --- |
| `/libros/` jerarquía | Manecillas 01, Samuel 02 | Se conserva: Manecillas principal, Samuel secundario |
| Copy temporal del catálogo | «David Porto Díaz publica … el 3 de septiembre» | Copy estable: Manecillas «publicada el 3 de septiembre de 2026» |
| Schema Manecillas en ItemList | ISBN, editorial, páginas, fecha | + `bookFormat`, géneros e imagen, todos ya autorizados |
| Schema Samuel en ItemList | ISBN, formato, editorial, año | + 422 páginas e imagen, coherentes con facts actuales |
| Offer/compra Manecillas | Ausente | Ausente; `purchaseUrl` sigue null |
| Jaula en catálogo | No visible | Sigue fuera del catálogo; registry continúa `noindex`, `sitemap:false` |
| Hero Manecillas | Portada oficial responsive + copy estable | Se conserva; preload pasa a ser responsive mediante `imagesrcset`/`imagesizes` |
| Ficha editorial | Editorial, género, páginas, ISBN, publicación, PVP | + formato «Tapa blanda», porque la autoridad actual lo confirma |
| Sinopsis | Sinopsis de página + sinopsis editorial de cubierta | Se conservan ambas; no se reescriben |
| Fragmento en ficha | Apertura + enlace a tres fragmentos | Se conserva sin tocar texto literario |
| Anchors históricos | `#aviso`, `#muestra`, `#sinopsis-editorial`, `#newsletter-manecillas` | Conservados |
| Disponibilidad | Copy interno «No se inventan retailers» | Copy editorial para lector; PVP identificado como editorial y formato visible |
| Samuel dentro de ficha Manecillas | Related + segunda gran promoción con Amazon | Solo Related, según contrato V1; se elimina el upsell duplicado |
| Share/copy | Preparado en scaffold V1 pero ausente en página pública | Progressive enhancement: compartir nativo o copiar enlace; no afecta no-JS |
| Newsletter | Hook/source `manecillas` | Conservado; copy estable sobre compra solo cuando haya destinos verificados |
| OG/Twitter/canonical/Book | Correctos | Conservados; no se inventan hechos nuevos |

## Contenido recuperado

La comparación con `main` confirma que el salto a V1 ya había recuperado y mejorado la información pública útil: ficha completa, portada oficial responsive, sinopsis, ficha editorial, fragmentos, newsletter y acceso a Samuel. No se reintroduce el framing prelaunch de `main` («próxima», «en proceso») ni copy factual antiguo que ya fue sustituido por autoridades posteriores.

Samuel permanece accesible desde `/libros/`, su ficha, capítulo 1, Noveris y los recursos de club. Ser secundario no significa quedar oculto.

## Contenido ampliado en esta tarea

- Paridad visible ↔ JSON-LD del catálogo para formato/géneros/imagen de Manecillas y páginas/imagen de Samuel.
- Formato de Manecillas visible en la ficha y disponibilidad.
- Preload de portada responsive para no forzar la derivada 1024 px en todos los dispositivos.
- Acción local de compartir/copiar como mejora progresiva, sin dependencia ni `fetch`.
- Copy estable de disponibilidad y newsletter.

## Contenido movido o reducido

La segunda sección promocional grande de Samuel dentro de la ficha de Manecillas se retira. Samuel sigue presente en `#relacionado`, que es la ubicación definida por el contrato V1 para «Otra obra». Se elimina la duplicación, no el acceso a Samuel.

## Material preparado: clasificación y condición

### PUBLICADO_CORRECTAMENTE

- `/las-manecillas-del-recuerdo/` — ficha pública V1.
- `/las-manecillas-del-recuerdo/fragmentos/` — tres fragmentos públicos aprobados.
- Portada web responsive 320/512/768/1024 y OG específico.
- Sinopsis editorial de cubierta.
- Newsletter Manecillas con source `manecillas`.
- Catálogo `/libros/` con Manecillas principal y Samuel secundario.

### READY_PARA_PUBLICAR

- Borradores editoriales de proceso derivados del manuscrito: están preparados como materiales, pero su publicación corresponde a la tarea de Cuaderno y a su calendario/editorial review. «Ready» no significa que deban activarse desde esta PR.
- Fixture del hub «Cómo se escribió»: el HTML/propuesta existe, pero su URL no debe activarse todavía; su estado efectivo sigue siendo gated según el siguiente bloque.

### GATED_CON_CONDICIÓN

- `/las-manecillas-del-recuerdo/como-se-escribio/`: mantener `noindex,follow` / no activar como hub público hasta que existan al menos cuatro notas reales del Cuaderno, indexables, en sitemap y enlazadas desde `/cuaderno/`. Solo entonces enlazar desde la ficha.
- Guía de club de lectura de Manecillas: material preparado; mantener `noindex,follow` hasta después del lanzamiento y hasta que el recurso se active para usuarios reales.
- ZIP/descargas de prensa y portada en alta resolución: no activar mientras la incidencia editorial de cubierta/handle no esté resuelta, no exista clearance de redistribución y el builder del press kit no pase.
- Assets sociales de «disponible» y otras campañas temporales: no introducirlos automáticamente en páginas evergreen; activarlos únicamente desde la campaña/calendario correspondiente.

### DESCARTADO_DOCUMENTADO

- La gran promoción de Samuel dentro de la ficha Manecillas: retirada por duplicar `#relacionado` y romper la jerarquía editorial V1. Samuel no se elimina del sitio.
- Framing antiguo de `main` que presentaba Manecillas como «próxima» o «en proceso»: superado por la autoridad actual.

### MATERIAL_INTERNO

- Scripts/fixtures de generación de social cards, mockups, hero y campaña.
- Scaffolds lab V1.
- Materiales privados con spoilers y matrices editoriales.
- Assets antiguos no referenciados: no se borran desde esta tarea.

### FALTA_REAL

- URL comercial verificada de Manecillas. Mientras `purchaseUrl` siga null no debe existir botón de compra, `Offer`, disponibilidad de retailer ni búsqueda de Amazon usada como sustituto.

## Fragmentos — contrato de preservación

La página pública mantiene exactamente tres IDs canónicos: `#fragmento-1`, `#fragmento-2`, `#fragmento-3`. El QA existente de fragmentos compara los `.excerpt-field` contra la base cuando la página existe y prueba índice, prev/next, deep links, Back/Forward, no-JS, teclado, responsive y hashes malformados. Esta tarea no modifica texto literario.

## Media

La portada pública usada es la derivada oficial 2:3. La ficha conserva `width`/`height`, `fetchpriority="high"` y `<picture>` responsive. El preload se alinea con esa selección mediante `imagesrcset` y `imagesizes` para evitar descargar 1024 px de forma incondicional en móvil.

No se borran mockups, fondos o derivados antiguos simplemente por no estar referenciados.

## CROSS_TASK_FINDINGS

1. `data/content-registry.json` describe Manecillas con job `comprar` aunque `purchaseUrl` sigue null. No se interpreta como autorización para inventar un destino comercial; la autoridad factual prevalece. La semántica del registry pertenece a una tarea global posterior.
2. La documentación Drive del 16/08 decía «formato pendiente» y la autoridad actual ya fija `Paperback`. No se edita el documento histórico desde este scope.
3. La incidencia editorial de cubierta/handle afecta al package de prensa y high-res, pero `prensa.html`, `press-kit/**` y la autoridad global están fuera de scope. Se mantiene el gate.
4. Cualquier cambio de `dateModified` exigiría regenerar `sitemap.xml`, que está prohibido en esta tarea. Por ello esta PR no altera `dateModified`; la capa global de fechas queda para la tarea que regenere sitemap de forma atómica.

## Gating explícito de comercio

PVP editorial ≠ `Offer` comercial. La ficha puede mostrar 16 € como dato editorial, pero no se deriva de él una disponibilidad, vendedor o URL. El CTA comercial solo se habilitará al registrar un destino real y verificable en la autoridad correspondiente.

## Criterio de cierre

La rama solo puede considerarse lista para revisión cuando:

- facts visibles y schema coincidan;
- no haya Jaula/PIEL pública en catálogo;
- no exista `Offer` Manecillas ni URL comercial inventada;
- los anchors históricos sigan vivos;
- fragmentos mantengan texto e IDs;
- no-JS, teclado, reflow, text-spacing, reduced-motion y navegación pasen;
- no haya errores de consola ni overflow en los viewports de la tarea;
- CI específico y checks existentes estén verdes.
