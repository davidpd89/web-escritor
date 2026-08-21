# AUDITORÍA DE RAMA ACTIVA — LAB HOME V1

Actualizado: 21/08/2026.
Repositorio: `davidpd89/web-escritor`.
Rama objetivo para integración futura: `implementacion-web-2026`.
HEAD verificado en esta pasada: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.
`main`: baseline público; no es la rama sobre la que debe prepararse el delta técnico.

Este fichero existe para impedir que el rediseño se integre contra una fotografía antigua del repositorio. No autoriza commit, push, merge ni deploy.

## 1. Conclusión ejecutiva

El lab 37 sigue siendo válido como sistema aislado, pero cuatro supuestos iniciales necesitaban corrección:

1. `/herramientas/` YA existe en `implementacion-web-2026`, contiene 17 herramientas y aparece en `sitemap.xml`. Deja de ser bloqueo del mapa.
2. Las cuatro cubiertas planas oficiales de Manecillas YA están integradas en `/assets/portada-las-manecillas-del-recuerdo-{320,512,768,1024}.webp`. El lab debe reutilizarlas y no crear una segunda jerarquía `/assets/las-manecillas/` en el repo.
3. `/donde-empieza-la-jaula/` NO existe en la rama activa ni dentro de `/libros/`. Sigue siendo el único nodo editorial planificado que bloquearía una Home pública si mantiene href real.
4. El CSS/JS actual de la rama no es la base visual de V1. Es la implementación anterior que se conserva como baseline funcional mientras el lab decide la nueva dirección.

## 2. Evidencia de la Home activa

La Home de `implementacion-web-2026` ya incorpora varias correcciones editoriales útiles que deben preservarse durante el rediseño:

- descriptor global `Escritor`;
- copy permanente de Manecillas: `Publicada el 3 de septiembre de 2026`;
- meta/OG/Twitter orientados a Manecillas;
- schema `WebSite`, `WebPage`, `Person`, `Book` y preguntas;
- canonical y `viewport-fit=cover`;
- enlaces a Manecillas y Samuel;
- fotografía del autor precargada;
- speculation rules para rutas prioritarias.

No se debe sustituir el `<head>` por el del lab. El lab aporta composición y componentes, no una nueva autoridad SEO.

## 3. Deuda visual que NO debe heredarse a V1

### `styles.css`

La hoja global activa todavía usa el sistema anterior:

- `Cormorant Garamond` + `Inter`;
- `color-scheme: dark` global;
- fondo con múltiples gradients;
- grid/textura CSS global;
- `backdrop-filter: blur(20px)` en header;
- radios 14/20px y botones `border-radius:999px`;
- shadows de cards/hover;
- CTA con gradient;
- elevación `translateY` en hover;
- cards uniformes para credenciales y otros bloques.

Todo eso sirve como baseline actual, pero entra en conflicto con los contratos 06/16/19/24/29 vigentes: Paper/Ink, radios mínimos, sin card elevation universal, sin pills rutinarias, sin gradients como firma, sin glass y sin lift genérico.

Decisión: **NO PORTAR esos tokens ni esas primitivas al sistema V1.** Mantenerlos en producción hasta migrar cada familia; eliminarlos después por trazabilidad, nunca mediante limpieza global previa.

## 4. Deuda específica de Manecillas

`assets/manecillas-extras.css` es una capa histórica útil para la web actual, pero queda SUPERADA para el rediseño V1. Contiene:

- hex históricos de Manecillas usados directamente en componentes;
- gradients decorativos;
- bordes y marcos temáticos;
- theme cards;
- textura/papel simulada por gradients;
- múltiples sombras;
- tratamiento local que puede convertir la obra en una skin separada.

La ficha actual además precarga y usa `manecillas-book-mockup.webp` en el hero, mientras Book Master V1 exige portada oficial plana como objeto dominante y prohíbe mockup 3D/perspectiva como tratamiento principal.

Decisión de migración:

- NO borrar `manecillas-extras.css` ahora;
- NO importarlo en el lab;
- NO copiar su paleta a `tokens.css`;
- cuando la familia Libro V1 sustituya Manecillas, retirar selectores históricos solo después de comprobar que no quedan consumidores;
- el hero V1 usa la cubierta plana oficial y ratio real.

## 5. Deuda de Home actual

La Home activa usa actualmente:

- fondo hero raster/decorativo;
- retrato + mockup del libro;
- tres CTA hermanos (`Conocer`, `Recibir novedades`, `Samuel`);
- trust strip de tres cards;
- banda posterior de credenciales numéricas;
- sección `Empieza por aquí` con cards;
- múltiples bloques que compiten antes de llegar a la arquitectura editorial nueva.

No se considera un fallo de la web actual: es el sistema anterior. Pero **no debe condicionar el lab**. El contrato 19 gana: una acción primaria, jerarquía desigual, cartografía, río editorial mínimo y ausencia de grid de cards simultáneas.

## 6. JavaScript global — funciones que hay que preservar o retirar con sustituto

`script.js` de la rama activa contiene funcionalidad real y no puede eliminarse por estética:

| Función actual | Estado en V1 |
|---|---|
| `scheduleTask()` | conservar patrón si sigue aportando; no es identidad visual |
| registro de service worker | fuera del lab; reevaluar en integración |
| email obfuscation | conservar donde se use |
| nav móvil `.nav-toggle` | sustituir solo al aprobar shell V1 |
| Explore generado por JS con `div`/panel | sustituir por `<dialog>` nativo; no ejecutar ambos |
| footer map link inyectado | consolidar en markup estable cuando migre footer |
| hash scroll sync | conservar si sigue resolviendo un bug real |
| mobile bottom nav inyectada | V1 no la adopta por defecto; retirar solo tras QA móvil |
| back-to-top global | no adoptar en Home salvo necesidad demostrada |
| reading progress opt-in | conservar para lectura larga; no es Home |
| newsletter/Brevo | conservar contrato backend y estados; rediseñar solo la UI |
| quizzes/tools | mantener en rutas propias; evitar cargar/inicializar en Home si no corresponde |

## 7. Rutas verificadas en la rama activa

Confirmadas en `implementacion-web-2026`:

- `/las-manecillas-del-recuerdo/`
- `/libros/samuel-entre-mundos/`
- `/autor.html`
- `/cuaderno/`
- `/herramientas/`
- `/prensa.html`
- `/eventos.html`

`/herramientas/` contiene 17 utilidades en el hub y está presente en el sitemap de la rama. Es destino real del mapa V1.

No confirmada / 404 en la rama:

- `/donde-empieza-la-jaula/`

No existe tampoco como subcarpeta de `/libros/` en el árbol verificado.

## 8. Sitemap

El `sitemap.xml` de la rama activa ya contiene:

- `/herramientas/`;
- múltiples herramientas individuales;
- `/las-manecillas-del-recuerdo/` y fragmentos;
- Cuaderno, Samuel, Autor, Prensa, Eventos y demás rutas de producto.

El lab NO se añade al sitemap.

## 9. Riesgo de publicación accidental del lab

`.assetsignore` de la rama activa NO excluye `lab/`.

Eso es útil durante QA porque, si se integra el lab en la rama de staging, `/lab/diseno-home-v1/` podrá servirse y revisarse. Pero crea un gate previo a producción:

**antes de promover la implementación final, elegir una de estas dos opciones:**

A. eliminar del commit final los ficheros de lab que no deban quedar en producción; o
B. añadir `lab/` a `.assetsignore` en el último paso, después de terminar QA visual en staging.

No añadir `lab/` a `.assetsignore` antes del QA porque impediría revisar el propio prototipo en staging.

En ambos casos:

- lab con `noindex` siempre;
- lab fuera de sitemap;
- lab fuera de navegación pública;
- comprobación HTTP final: producción no debe servirlo si la decisión es ocultarlo.

## 10. Asset policy corregida

Rutas que el lab debe consumir en la rama activa:

- `/assets/portada-las-manecillas-del-recuerdo-320.webp`
- `/assets/portada-las-manecillas-del-recuerdo-512.webp`
- `/assets/portada-las-manecillas-del-recuerdo-768.webp`
- `/assets/portada-las-manecillas-del-recuerdo-1024.webp`
- `/assets/david-porto-foto-portada-sinfondo.webp` como retrato candidato, no imprescindible.

Las copias de Drive dentro de `37/assets/las-manecillas/` quedan como respaldo de procedencia del paquete, no como instrucción para duplicar paths en GitHub.

## 11. Qué cambia ya en el paquete 37

- `index.html`: referencias de cubierta pasan a los paths existentes de `/assets/`.
- `media-manifest.json`: schema v2 y target paths reales de la rama.
- `routes.json`: schema v2; Herramientas pasa a `verified-target-branch`; la ruta Jaula sigue ausente en la rama, pero el contenido ya está autorizado para construirla en staging (ver delta/contrato Jaula).
- `INTEGRATION.md`: branch-aware; deja de hablar de `main` como objetivo técnico.
- `QA.md`: añade gates específicos de staging, lab leakage y rutas reales.
- `validate_lab.py`: valida que el paquete no reintroduzca la jerarquía de assets duplicada ni vuelva a considerar Herramientas un bloqueo.

## 12. Próxima comprobación antes de escribir GitHub

Cuando el trabajo de Drive esté suficientemente cerrado y se autorice la integración:

1. refrescar HEAD de `implementacion-web-2026`;
2. repetir este delta si el SHA cambió;
3. montar SOLO `/lab/diseno-home-v1/` primero;
4. probar assets/rutas reales en staging;
5. hacer A/B y Gate 0;
6. elegir variante;
7. solo entonces preparar parches de Home/shell/familias.

No hay motivo para tocar `main` durante esta fase.


## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.


## DELTA 2d558b1 → f9b0646 — REAUDITORÍA 20/08/2026

Comparación GitHub: 13 commits por delante, 0 por detrás. La página `las-manecillas-del-recuerdo/index.html`, `script.js` y las cuatro cubiertas planas no cambiaron en ese intervalo. Los cambios se concentran en CI/Lighthouse, herramientas, editoriales, privacidad, builders y rutas auxiliares.

Entre los archivos cercanos al rediseño, `index.html` solo incorpora un ajuste de accesibilidad de la etiqueta de marca (`aria-label`) dentro del tramo revisado; `styles.css` recibe correcciones legacy/QA que deben conservarse para sus consumidores actuales mientras no hayan migrado a V1. No se copian esas reglas dentro de `base.css`, `shell.css`, `home.css` o `book.css` por inercia.

Conclusión: NO reabre dirección visual, Home A/B ni Book V1. Sí obliga a usar `f9b0646884d4ebc4a29664e4144798b5094286ea` como último HEAD auditado y a repetir el compare antes de escribir la rama si vuelve a avanzar.


## DELTA f9b0646 → 755d4ef — REAUDITORÍA 21/08/2026

La rama está **25 commits por delante** de `f9b0646`. La mayor parte del delta afecta CI, herramientas, builders y contenido auxiliar. El sitemap mantiene 55 rutas pero incorpora/actualiza las rutas de temas del Cuaderno. `Samuel entre mundos` recibe un ajuste mínimo de accesibilidad/Pa11y en el resultado del quiz (texto inicial `Resultado`), por lo que el contrato V1 debe preservar ese estado accesible.

El cambio operativo más importante para V1 es el contrato de generación: `scripts/build-writer-tools.py` y checks asociados son autoridad para salidas generadas. La implementación de Herramientas no puede hand-editar el HTML final y dejar el builder desincronizado.

No aparece motivo para reabrir la dirección visual Home/Libro. En aquella pasada se actualizó el baseline de integración a `755d4ef71de436f72dd5736d726a4b48523b2336`; el delta posterior figura a continuación.


## DELTA 755d4ef → 5c4a9af — REAUDITORÍA 21/08/2026

Comparación GitHub: **5 commits por delante, 0 por detrás**. Archivos afectados: `.github/workflows/content-index-check.yml`, `data/content-registry.json`, `data/navigation.json`, `data/ux-feature-retention.json` y `scripts/check-navigation-coverage.py`. No cambian `index.html`, Manecillas, Samuel, `styles.css`, `script.js`, builders de herramientas ni assets auditados por la V1.

El delta sí añade contratos que afectan a la integración futura: un registro canónico de contenidos, un registro de navegación/findability y una matriz de retención UX. Se incorporan al estado real del proyecto; no se sustituyen por el scaffold del lab.

**Jaula permanece deliberadamente fuera de `content-registry.json`, `navigation.json`, sitemap y árbol público porque `/donde-empieza-la-jaula/` sigue sin existir en la rama.** El scaffold de Drive continúa siendo `noindex` y su promoción solo se habilita tras crear la ruta en staging, pasar `jaula-preservation.json`, SEO/schema y cobertura de navegación.

Conclusión: el delta **no reabre Cartografía editorial viva, Home A/B ni la familia Libro**. El baseline auditado del paquete pasa a `5c4a9afca7c009bd78d5dd44ca4b6c656239527c` (tree `2012d1355f431f7c79c41c0d71d06674eced0725`).
