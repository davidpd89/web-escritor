# MAPA DE INTEGRACIÓN — LAB HOME V1 → `web-escritor`

Estado: plan exacto de migración. No autoriza escritura en GitHub y no sustituye QA visual/humano.

## 0. Baseline técnico verificado

Repositorio: `davidpd89/web-escritor`.

- producción/baseline público: `main`;
- rama objetivo de integración: `implementacion-web-2026`;
- HEAD verificado en esta pasada: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`;
- `main`: no tocar durante el lab;
- staging del proyecto: rama `implementacion-web-2026` según auditoría 64;
- `/lab/diseno-home-v1/`: todavía no existe en la rama activa.

Toda decisión de integración se contrasta contra la rama objetivo, no contra una fotografía antigua de `main`. Si el HEAD cambia antes de escribir GitHub, refrescar primero `BRANCH-AUDIT.md`.

## 1. Principio

La web activa es estática, extensa y acumula SEO, schema, formularios, herramientas y comportamiento real. El rediseño no entra como reemplazo masivo de `index.html`, `styles.css` y `script.js`.

Orden correcto:

1. mantener este paquete como autoridad de Drive;
2. cuando se autorice GitHub, montar únicamente `/lab/diseno-home-v1/` en `implementacion-web-2026`;
3. reutilizar assets ya existentes en la rama;
4. validar V1-A/V1-B + Gate 0;
5. escoger una sola dirección;
6. extraer componentes/tokens ganadores;
7. migrar shell y Home conservando `<head>`, schema, URLs, datos y backends;
8. retirar código antiguo únicamente cuando la función tenga sustituto probado;
9. migrar Manecillas como primera familia Libro;
10. extender a las demás familias solo después de los gates.

## 2. Árbol de repo propuesto para el lab

```text
/lab/diseno-home-v1/
  index.html
  components.html
  README.md
  INTEGRATION.md
  BRANCH-AUDIT.md
  QA.md
  /css/
    fonts-lab.css
    tokens.css
    home.css
    variants.css
    components.css
  /js/
    fixtures.js
    lab.js
  /data/
    media-manifest.json
    routes.json
  /scripts/
    validate_lab.py
```

No crear otra copia de las cubiertas en GitHub. El lab consume los assets que la rama ya tiene en `/assets/`.

`/lab/` debe llevar `noindex`, quedar fuera de sitemap y fuera de navegación pública.

## 3. Qué preservar del `<head>` público

El `<head>` del lab es mínimo. Nunca se pega encima del `<head>` de producción.

Preservar/auditar explícitamente:

- `<html lang="es">`;
- viewport + `viewport-fit=cover`;
- canonical;
- title/meta description;
- robots;
- Open Graph/Twitter;
- favicon/manifest;
- preload que siga siendo válido;
- speculation rules si siguen justificadas;
- JSON-LD completo y sus `@id` canónicos;
- analytics/medición aprobada;
- datos editoriales de Manecillas/Samuel;
- verificaciones técnicas existentes.

La Home activa de la rama ya contiene copy permanente de Manecillas y descriptor global `Escritor`; el rediseño debe conservar esas correcciones.

## 4. Qué NO se hereda en el lab

No cargar:

- `/styles.css`;
- `/assets/manecillas-extras.css`;
- `/script.js`;
- service worker de producción;
- Explore actual generado por JS;
- navegación inferior móvil inyectada;
- back-to-top;
- reading progress;
- quizzes/tools no relacionados con la Home;
- gradientes, pills, elevaciones, grids/texturas y radios históricos como vocabulario V1.

Motivo: contaminarían el A/B y convertirían el nuevo sistema en una skin del anterior.

## 5. Conflictos verificados contra la rama activa

### 5.1 `styles.css`

La implementación anterior sigue usando:

- Cormorant Garamond + Inter;
- `color-scheme: dark` global;
- gradients de fondo;
- textura/grid CSS global;
- `backdrop-filter` en header;
- radios grandes y botones `999px`;
- shadows/elevación de cards;
- CTA con gradient y lift en hover;
- bloques de credenciales/cards repetidos.

No se «arregla» esa hoja antes del piloto. Se mantiene como sistema actual hasta sustituir bloques por V1. Cuando una familia esté migrada, retirar selectores antiguos mediante búsqueda de consumidores reales.

### 5.2 `assets/manecillas-extras.css`

Es capa histórica, no input de V1. Contiene paleta histórica directa, gradients, marcos, theme cards, papel CSS y sombras. No copiar esos valores a tokens V1.

La ficha actual además usa `manecillas-book-mockup.webp` como hero. Book Master V1 gobierna la migración futura: portada plana oficial, ratio real, sin mockup 3D como objeto dominante.

### 5.3 Home actual

La rama todavía presenta:

- hero con fondo raster;
- retrato + mockup;
- tres CTA hermanos;
- trust strip con cards;
- banda de métricas;
- `Empieza por aquí` en cards.

Sirve de baseline funcional/SEO, no de composición para V1. El contrato 19 sustituye esa gramática tras ganar el A/B.

## 6. JavaScript global — tabla de sustitución

`script.js` contiene trabajo real. No se borra a ciegas.

| Función actual | Decisión V1 |
|---|---|
| `scheduleTask()` | conservar si sigue aportando a runtime; no es diseño |
| service worker | fuera del lab; reevaluar en integración |
| email obfuscation | conservar donde exista contacto |
| nav móvil `.nav-toggle` | sustituir solo al aprobar shell V1 |
| Explore `div` generado por JS | sustituir por `<dialog>`; nunca ejecutar ambos |
| inyección de mapa del sitio al footer | consolidar en HTML estable al migrar footer |
| hash scroll sync | conservar si sigue solucionando comportamiento real |
| bottom nav móvil | no adoptada por defecto; retirar solo tras QA móvil |
| back-to-top | condicional; no Home por defecto |
| reading progress | conservar opt-in en lectura larga |
| newsletter/Brevo | conservar endpoint/contrato; rediseñar UI por separado |
| quizzes/tools | mantener en sus rutas; no mezclar con shell/Home |

## 7. Media — paths reales de la rama

Cubiertas oficiales ya integradas:

- `/assets/portada-las-manecillas-del-recuerdo-320.webp`
- `/assets/portada-las-manecillas-del-recuerdo-512.webp`
- `/assets/portada-las-manecillas-del-recuerdo-768.webp`
- `/assets/portada-las-manecillas-del-recuerdo-1024.webp`

Retrato A/B seleccionado y trazado:

- `/assets/david-porto-foto-portada-sinfondo.webp`

`media-manifest.json` conserva IDs de Drive como procedencia, pero sus `target_path` deben coincidir con estas rutas. Las copias guardadas dentro del paquete 37 en Drive son respaldo; no instruyen a duplicar assets en GitHub.

## 8. Fuentes

Sistema activo: Cormorant Garamond + Inter.

V1 de lab: Instrument Serif + Manrope + Newsreader.

Durante lab puede usarse carga remota únicamente para comparar. Antes de producción:

1. verificar licencias/fuentes oficiales;
2. self-host WOFF2;
3. incluir Latin Extended necesario;
4. cargar solo pesos/ejes usados;
5. medir CLS/fallback;
6. Gate 35 + zoom 200 %;
7. retirar fuentes antiguas solo cuando no tengan consumidores.

## 9. Rutas de la cartografía

`data/routes.json` es la autoridad machine-readable.

### Confirmadas en `implementacion-web-2026`

- `/las-manecillas-del-recuerdo/`
- `/libros/samuel-entre-mundos/`
- `/autor.html`
- `/cuaderno/`
- `/herramientas/`
- `/prensa.html`
- `/eventos.html`

`/herramientas/` ya contiene 17 utilidades y está en `sitemap.xml` de la rama. No es bloqueo de integración.

### Bloqueo real

- `/donde-empieza-la-jaula/` → 404/no existe en la rama activa.

El lab puede conservar el nodo marcado como `data-route-planned="true"` para probar geometría. La Home pública no puede promocionarse con ese href hasta crear una página mínima autorizada o cambiar/eliminar el destino. No inventar portada, género, fecha, lore ni schema.

## 10. Riesgo de fuga del lab

`.assetsignore` actual NO excluye `lab/`.

Durante staging esto es deliberadamente útil: permite revisar `/lab/diseno-home-v1/` por HTTP real.

Gate preproducción, después del QA:

- opción A: eliminar el lab del conjunto que se promueve; o
- opción B: añadir `lab/` a `.assetsignore` en el paso final.

No añadir la exclusión antes de terminar QA de staging.

Siempre:

- `noindex`;
- fuera de sitemap;
- fuera de nav pública;
- HTTP production check final si debe quedar inaccesible.

## 11. Migración de Home — orden exacto

### H0 — snapshot de rama activa

Registrar:

- SHA;
- canonical/title/meta;
- JSON-LD;
- H1/H2/H3;
- enlaces internos;
- texto indexable;
- imágenes/alt;
- newsletter;
- comportamiento JS global relevante;
- Lighthouse/CWV baseline;
- capturas 390/768/1440.

### H1 — shell

Migrar únicamente:

- skip link;
- header;
- navegación primaria;
- Explorar `<dialog>`;
- footer;
- focus/touch/no-JS.

No tocar hero todavía si el shell no pasa Gate 1.

### H2 — Home ganadora

Aplicar una sola variante después del A/B.

Migrar:

- hero;
- seam/costura;
- mapa/ruta;
- río editorial;
- newsletter UI compatible con backend;
- estados H0/H1/H6.

No mezclar A+B sin nueva prueba.

### H3 — limpieza

Solo después de sustitución funcional:

- retirar CSS antiguo sin consumidores;
- retirar JS reemplazado;
- evitar dos Explore/nav simultáneos;
- consolidar listeners;
- revisar bundle/runtime;
- volver a medir CWV.

### H4 — familia Libro / Manecillas

Después de Home:

- sustituir mockup hero por cubierta oficial plana;
- llevar metadata de cards a ledger;
- eliminar theme cards/gradients no compatibles;
- conservar schema, sinopsis, fragmentos, ISBN, fecha, editorial y enlaces;
- validar 320/390/768/1024/1440/1728;
- solo entonces retirar `manecillas-extras.css` donde deje de tener consumidores.

## 12. Selectores — estrategia anti-regresión

No hacer replace global de `.button`, `.section`, `.hero`, `.card`, `.site-header` o similares: `styles.css` los reutiliza en muchas rutas.

Preferencia:

1. namespace V1 temporal o nombres inequívocos;
2. migrar un bloque/familia;
3. QA de rutas;
4. medir;
5. eliminar clases antiguas solo al demostrar cero consumidores.

## 13. Specimen ejecutable

`components.html` prueba Gate 0 sin media:

- primary/secondary/text action;
- disabled;
- breadcrumb;
- related route;
- metadata ledger;
- input/help/privacy;
- estados y recuperación;
- editorial/functional note;
- blockquote;
- details;
- stress de títulos/copy.

No publicar como Storybook ni convertirlo en producto. Es instrumento de QA.

## 14. Validación previa a promoción

Obligatorio:

- refrescar HEAD y `BRANCH-AUDIT.md`;
- `validate_lab.py` PASS;
- Gate 0 sin media;
- A/B iguales salvo variables autorizadas;
- doc 18 QA;
- doc 28 ≥88/100;
- doc 33 H0/H1/H6;
- doc 34 hostile content;
- doc 35 microtipografía;
- doc 36 runtime móvil;
- teclado;
- screen reader smoke;
- no-JS esencial;
- reduced motion;
- 320 CSS px;
- zoom 200 %;
- `/herramientas/` 200 en staging;
- `/donde-empieza-la-jaula/` sigue bloqueando promoción mientras sea 404 y el mapa enlace allí;
- lab fuera de sitemap/nav;
- assets de cubierta 200;
- no regresión de canonical/schema/SEO;
- newsletter/analytics/privacy equivalentes;
- Lighthouse/CWV sin regresión material.

## 15. Definition of Done de Home

No está terminada porque «se ve mejor». Está terminada cuando:

- variante ganadora supera score;
- mobile parece diseñado, no reducido;
- H0/H6 funcionan;
- Gate 0 mantiene firma sin assets;
- no hay destinos contractuales rotos;
- `<head>` conserva autoridad;
- no existen dos sistemas de navegación simultáneos;
- código reemplazado se retira de forma trazable;
- ninguna otra familia cambia accidentalmente;
- existe comparación antes/después de SEO, UX, performance y accesibilidad;
- el lab no se filtra a producción si la decisión final es ocultarlo.

## 16. Regla de GitHub

Drive es la autoridad de preparación en esta fase.

Cuando se autorice escritura:

- trabajar en `implementacion-web-2026`;
- primera escritura: lab aislado;
- commits pequeños;
- staging primero;
- nunca `main` directo;
- nunca merge hasta superar gates.


## 17. Contrato selector/función → V1

La integración ya no depende solo de este documento narrativo. `MIGRATION-MATRIX.md` y `data/migration-map.json` fijan para cada bloque actual: origen, tarea, componente V1, acción, condición de retirada y prueba obligatoria.

Regla: ante discrepancia entre una limpieza de código improvisada y la matriz, gana la matriz hasta que una auditoría de consumidores demuestre que puede actualizarse. Nunca eliminar un IIFE, selector, formulario o hook de analytics solo porque la Home V1 ya no lo renderice.


## 18. Delta de integración — shell móvil y formularios

### Navegación primaria

El shell V1 NO elimina la navegación primaria en móvil. En ≤1023 px se recompone en dos niveles: marca + `Explorar` y, debajo, `Obra` / `Cuaderno` / `Herramientas` como enlaces HTML directos. `Explorar` nunca puede convertirse en requisito para alcanzar una ruta principal.

Durante migración, no retirar la navegación móvil/bottom-nav legacy hasta comprobar que este shell directo cubre las rutas y que no existe una segunda navegación ejecutándose a la vez. La retirada se decide con `MIGRATION-MATRIX.md`, no por apariencia.

### Formularios

Las primitivas visuales de control están centralizadas en `css/base.css`. Las familias solo aportan layout de la sección. Prohibido volver a definir estilos completos de input, submit, consentimiento o status dentro de `home.css`, `book.css` u otros CSS de familia.

Home lab adopta los hooks `newsletter-form-home`, `nl-email-home`, `nl-gdpr-home`, `nl-status-home`. Libro mantiene los equivalentes de Manecillas. En lab, `lab.js` valida email + consentimiento pero no llama a endpoint alguno.

En producción, la sustitución visual del newsletter debe conservar el contrato funcional real de `script.js`/Brevo/analytics y sus `sourceLabel`; el JS de laboratorio NO sustituye ese backend.


## Delta — tipografía V1 y retrato A/B

Fuente de integración tipográfica: `data/font-contract.json`. No derivar archivos/pesos desde memoria ni desde el CSS legacy.

- Instrument Serif: display, 400 normal + 400 italic; nunca fake bold.
- Manrope: UI/body, 400/500/600/700.
- Newsreader: lectura, 400/600 normal + 400 italic real.
- `css/fonts-lab.css`: remote import permitido exclusivamente en laboratorio.
- producción: self-host WOFF2; Latin/Latin-ext necesario para español; `font-display: swap`; preload solo de familias realmente críticas above-the-fold; Newsreader no se precarga globalmente.
- ningún CSS de familia puede introducir `fonts.googleapis.com`.

El retrato de Home se mantiene en `/assets/david-porto-foto-portada-sinfondo.webp`. `media-manifest.json` prueba que su ancho intrínseco (433 px) supera el máximo CSS declarado (430 px); no reemplazarlo por otra foto solo por tener más resolución. Cualquier cambio de retrato reabre únicamente el gate de media/composición, no la dirección de arte completa.


## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.


## DELTA DE INTEGRACIÓN — SOURCE/GENERO/03-09

- Home V1 declara `data-newsletter-source="home"`; Libro V1 declara `data-newsletter-source="manecillas"`. Son marcadores de contrato para no perder el binding existente, no parámetros adicionales enviados al backend.
- En producción mantener `submitNewsletter(..., "manecillas")` y el payload permitido `{ email, source }`.
- Sustituir únicamente el success copy de Manecillas por: «Te has suscrito correctamente. Recibirás las novedades de Las manecillas del recuerdo y de David Porto Díaz.»
- El ledger de Manecillas incluye `Género — Novela coral · Ficción especulativa`, porque ya existe en la página/canon actual.
- El 03/09 no hay cambio editorial de estado. Solo se introducen retailers verificados y se activa/ajusta la acción de compra. Si no hay URL verificada, no se inventa destino.

### Delta Gate 3 — preservación estructurada de Manecillas

Al migrar la ficha de Manecillas no basta con copiar Book schema. Preservar exactamente:

- `WebPage @id = https://davidportodiaz.com/las-manecillas-del-recuerdo/`;
- `WebPage.primaryImageOfPage` → cubierta oficial 1024×1536;
- `WebPage.breadcrumb` → `Inicio / Libros / Las manecillas del recuerdo`;
- breadcrumb HTML visible con la misma jerarquía y `/libros/` como nivel intermedio;
- muestra visible con `data-nosnippet` mientras no exista una decisión SEO explícita que lo cambie;
- enlace HTML rastreable a `/las-manecillas-del-recuerdo/fragmentos/`.

No usar el mockup 3D como primary image ni renombrar la miga «Libros» a «Obra» por coherencia estética. `check_preservation.py --manecillas <candidato>` debe pasar antes de retirar la ficha legacy.


### Preservación de deep links de Manecillas

Al migrar `/las-manecillas-del-recuerdo/`, conservar `#aviso`, `#muestra`, `#sinopsis-editorial` y `#newsletter-manecillas`. Si la sección V1 tiene otro id principal, mantener un alias de altura cero dentro del destino y aplicar `scroll-margin` suficiente para el header sticky. No eliminar un anchor público solo porque la nueva arquitectura use otro nombre interno.

La dedicatoria existente se conserva una sola vez en `.book-dedication`; `manecillas-quote-band` no migra. En estado comercial pendiente, el hero enlaza a newsletter y no a compra. `data/manecillas-preservation.json`, `data/migration-map.json`, `scripts/check_preservation.py` y `scripts/validate_lab.py` son autoridad ejecutable para este bloque.

## Actualización 21/08/2026 — extensión de familias y builder contract

Baseline: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

La integración ya no puede tratar Samuel como una variante de Manecillas ni Premios como una variante de Prensa. Usar los scaffolds/contratos dedicados `book-samuel.html` y `awards.html`.

La rama actual ha endurecido el contrato de páginas generadas. En Herramientas, antes de modificar una salida, comprobar si su autoridad es `scripts/build-writer-tools.py`, `scripts/build-tools-hub.py` u otro builder/dataset. Cambiar fuente + regenerar + ejecutar `--check`; no parchear solo el HTML generado.

Antes del primer write ejecutar, además del validador base:

```bash
python scripts/validate_extension.py
```

La extensión permite implementación en staging; no autoriza merge ni producción.


## Delta 21/08/2026 — Jaula autorizada

La constatación histórica «`/donde-empieza-la-jaula/` no existe en la rama activa» sigue siendo cierta en el baseline auditado, pero ya no falta autorización/contenido. El paquete incorpora `book-jaula.html`, `JAULA-PUBLIC-SPEC.md` y `data/jaula-preservation.json`.

Orden: crear primero la ruta en staging desde esos contratos; conservar `noindex` durante verificación; comparar el capítulo 1 con el hash/fuente; validar head/canonical/schema sin metadata editorial inventada; ejecutar cobertura de navegación; solo entonces valorar sitemap/enlace público. Mientras la rama no contenga la ruta, `routes.json` mantiene `promotionBlocked: true` para evitar href a 404.

## REGISTRY / FINDABILITY — DELTA AUTORITATIVO 21/08/2026

Desde HEAD `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`, la integración no puede tratar sitemap, navegación y páginas como listas independientes. La rama dispone de:

- `data/content-registry.json`: qué existe y con qué estado;
- `data/navigation.json`: qué se muestra en cada superficie;
- `scripts/check-navigation-coverage.py`: consistencia exacta entre registry, sitemap, herramientas y navegación;
- `data/ux-feature-retention.json`: qué funciones legacy se conservan, mueven, acotan, reemplazan o solo se consideran retirables.

Regla: **el V1 consume estos contratos; no crea un segundo registro dentro de `/lab/` como futura fuente de producción.** `routes.json` del paquete sigue siendo mapa de diseño/migración, no reemplazo del registry real.

### Alta de Jaula en dos pasos

1. **Staging no público:** crear la ruta y registrarla en `content-registry.json` con `status:noindex`, `searchIndex:false`, `sitemap:false`. No referenciarla aún desde `navigation.json`.
2. **Promoción autorizada:** después de preservación, HTTP 200, SEO/schema, browser QA y aprobación humana, actualizar contrato + registry + sitemap + navegación en el mismo tramo de integración.

Mientras `productionAllowed:false`, `check_preservation.py --jaula` debe exigir `noindex`; `check-navigation-coverage.py` debe impedir que una entrada no pública se cuele en header, Explorar, footer, HomeMap o navegación local.

No desactivar/relajar esos checks para acelerar la integración. Un fallo de coverage indica deriva real de arquitectura de información.
