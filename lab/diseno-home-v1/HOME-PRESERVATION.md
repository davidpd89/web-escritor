# HOME — BASELINE SEO / SEMÁNTICA / FUNCIONES PARA EL REDISEÑO V1

Rama auditada: `implementacion-web-2026`
HEAD: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`
Objetivo: impedir dos errores opuestos: perder señales SEO/entidad valiosas o conservar markup estructurado que ya no corresponde al contenido visible de la Home V1.

## 1. Preservar como contrato de identidad

- canonical `https://davidportodiaz.com/`;
- robots index/follow y preview directives de producción;
- idioma `es`;
- autor `David Porto Díaz`;
- entidad `#website`;
- entidad `#webpage`;
- entidad `#author`;
- entidad `#book-manecillas`;
- entidad `#book-samuel` cuando Samuel siga representado de forma sustantiva en el HTML;
- publisher canonical de Libros Indie donde corresponda;
- OG/Twitter con imagen real y alt coherente;
- sitemap/canonical/favicon/manifest salvo decisión técnica separada;
- `sameAs` del autor y datos biográficos verificables;
- title/meta description: conservar como baseline y reescribir solo mediante cambio SEO/editorial explícito, no por el rediseño visual.

## 2. No copiar automáticamente al nuevo `<head>`

### Fonts/preloads legacy

Los preload actuales de Cormorant/Inter (`cg-normal-latin.woff2`, `inter-normal-latin.woff2`) pertenecen a la tipografía vieja. V1 debe sustituirlos por la estrategia real de Instrument Serif/Manrope/Newsreader una vez cerrada licencia/hosting/subsetting. No mantener ambos stacks.

### `theme-color`

El valor oscuro actual `#080a0c` pertenece a la superficie legacy. Se recalcula desde el token/superficie final V1 después del gate visual; no se conserva por inercia.

### CSS legacy

`styles.css` y `assets/manecillas-extras.css` no entran en el lab. En producción se retiran por consumidores, nunca desde `<head>` antes de completar la migración.

## 3. Schema: paridad visible obligatoria

El rediseño cambia drásticamente cuánto contenido vive en Home. Por tanto cada nodo actual se clasifica:

### Mantener/adaptar

- `WebSite`.
- `WebPage`.
- `Person #author`.
- `Book #book-manecillas` si la obra actual conserva presencia sustantiva.
- `Book #book-samuel` solo con propiedades que sigan justificadas por la presencia visible o por una arquitectura de entidad aprobada.
- `ItemList #bibliography` si la Home sigue mostrando claramente ambas obras como bibliografía; si el mapa solo ofrece links mínimos, revisar/mover a `/libros/`.

### Condicional: eliminar/mover si el bloque visible desaparece

- reviews de Samuel incrustadas en el nodo `Book`: no conservar en Home si desaparecen las reseñas visibles; su lugar natural puede ser la ficha de Samuel.
- `Event` de Feria del Libro de Madrid 2026: no mantener en Home solo porque existía; si el evento ya no se representa de forma sustantiva, dejarlo en la página de evento/archivo.
- `FAQPage`: no conservar FAQs de Samuel/Noveris si la Home V1 elimina el FAQ visible. Nunca usar JSON-LD oculto como sustituto de contenido retirado.

Regla: **preservación SEO no significa preservación ciega de schema duplicado**. Significa conservar entidades canónicas y mover señales al lugar semánticamente correcto cuando cambia la arquitectura visible.

## 4. Copy actual que sirve de baseline

Title actual:
`David Porto Díaz | Las manecillas del recuerdo y Samuel entre mundos`

Meta description actual:
`Web oficial de David Porto Díaz. Las manecillas del recuerdo, novela coral de vidas conectadas con Monza Ediciones (3 de septiembre de 2026), y Samuel entre mundos, publicada con Libros Indie.`

OG title actual:
`David Porto Díaz — Las manecillas del recuerdo`

OG image actual:
`https://davidportodiaz.com/assets/og-manecillas.webp`

La Home V1 no puede introducir un title/description más «bonito» pero menos informativo como efecto colateral de diseño.

## 5. Structured facts actuales a proteger

### Autor

- `@id`: `https://davidportodiaz.com/#author`.
- `jobTitle`: `Escritor`.
- URL: home canónica.
- imagen actual de entidad.
- born/home/nationality/sameAs/awards: conservar si siguen verificados; no tocar desde el rediseño.

### Manecillas

- `@id`: `https://davidportodiaz.com/#book-manecillas`.
- URL canónica de ficha.
- Monza Ediciones.
- ISBN `979-8-90514-935-1`.
- 272 páginas.
- fecha `2026-09-03`.
- formato Paperback.
- cubierta oficial 1024.

### Samuel

- `@id`: `https://davidportodiaz.com/#book-samuel`.
- ficha canónica `/libros/samuel-entre-mundos/`.
- ISBN y publisher canonical actuales se conservan en sus páginas de entidad aunque la Home reduzca su detalle.

## 6. Funciones de `<head>` / runtime que el lab no modela pero producción debe conservar

- speculation rules: revisar destinos tras arquitectura; no borrar sin decisión, no prerenderizar rutas bloqueadas;
- favicon/apple touch/manifest;
- service worker gestionado por `script.js`;
- GoatCounter/Metricool según contrato de privacidad actual;
- CSP/headers si están fuera del HTML;
- preconnects únicamente para terceros que sigan cargándose;
- preload de LCP actualizado a la imagen que realmente sea LCP en la variante ganadora.

## 7. LCP: no heredar preload antiguo

La Home actual precarga el retrato. Home V1-A/B puede hacer que el LCP real sea título, retrato o cubierta. El preload final se decide con medición de la variante ganadora. No precargar retrato + cubierta + fondos «por si acaso».

## 8. Gate antes de reemplazar la Home

Comparar OLD vs NEW automáticamente/manual:

- canonical;
- robots;
- title/meta;
- OG/Twitter;
- entidades @id canónicas;
- ISBN/editorial/fecha de libros;
- links internos relevantes;
- H1 y headings;
- texto visible que justifica schema;
- manifest/favicon;
- analytics/privacy;
- newsletter source/hooks;
- LCP preload;
- sitemap/route status.

Cualquier nodo schema eliminado debe tener una razón: `moved-to-canonical-page`, `visible-content-removed`, `superseded`, o `factual-fix`. Nunca «se perdió al cambiar el HTML».

## 9. Resultado deseado

Una Home V1 más corta puede tener **menos JSON-LD que la Home actual** y ser semánticamente mejor. El gate no compara cantidad; compara exactitud, identidad y ausencia de regresiones.



## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.
