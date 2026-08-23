# Política de compatibilidad cross-browser (K.3, 2026-08-23)

## Principio

El sitio sigue un enfoque práctico alineado con "Baseline / ampliamente
disponible", no una promesa de soportar cualquier navegador histórico:

- **Funcionalidad esencial** (navegación, lectura, formularios principales,
  acceso al contenido): debe funcionar en Chromium, Firefox y WebKit
  recientes, sin depender de una única API/motor.
- **Features recientes o experimentales** (p. ej. `scheduler.postTask`,
  Speculation Rules API, `:has()` avanzado): se usan como *progressive
  enhancement* — su ausencia no puede bloquear navegación, lectura,
  formularios ni acceso a contenido. Se degradan de forma inocua.
- El reflow profundo en Chromium (`qa/sitewide-reflow-browser.mjs`, que usa
  CDP) **no se sustituye ni se degrada** por este smoke cross-engine: son
  gates complementarios, no equivalentes. Lighthouse tampoco sustituye a un
  test de compatibilidad cross-engine — mide una superficie distinta
  (rendimiento/mejores prácticas en Chromium), no ejecución real en
  Firefox/WebKit.

## Feature detection existente

- `scheduler.postTask` (`script.js`, función `scheduleTask`): se usa con
  fallback explícito a `setTimeout` cuando `window.scheduler?.postTask` no
  existe. Ningún evento de analítica ni interacción depende de que la API
  exista.
- Animaciones/transiciones: el sitio respeta `prefers-reduced-motion` vía
  CSS; ningún control funcional (navegación, formularios, diálogos) depende
  de que una animación se complete para quedar operativo.
- `<dialog>` (diálogo "Explorar", modal de compra): API con soporte amplio
  en los tres motores objetivo; no requiere polyfill para el smoke definido
  aquí.

## Smoke cross-engine

`qa/cross-engine-smoke.mjs` ejecuta, en **Chromium + Firefox + WebKit**, un
conjunto representativo de rutas críticas (no todas las rutas × todos los
motores, para no encarecer CI sin aportar valor):

- `/`
- `/las-manecillas-del-recuerdo/`
- `/las-manecillas-del-recuerdo/fragmentos/`
- `/libros/samuel-entre-mundos/`
- `/cuaderno/`
- `/recomendaciones/` y `/recomendaciones/portal-fantasy-espanol/`
- `/herramientas/` y `/herramientas/legibilidad/`
- `/asistente/` en modo local/inactivo seguro (sin red externa)

En cada ruta y motor se verifica como mínimo:

- la página carga (HTTP 200 servido localmente, DOM listo);
- el shell de navegación existe y es utilizable (`header`, enlaces
  principales);
- el diálogo "Explorar" abre, gestiona foco (el primer enlace del diálogo
  recibe el foco al abrir) y cierra devolviendo el foco al disparador;
- los enlaces críticos de la ruta son accesibles (existen, tienen `href`
  no vacío);
- no aparecen excepciones JS no capturadas durante la carga ni la
  interacción con "Explorar";
- no hay overflow horizontal en un viewport móvil representativo
  (`document.documentElement.scrollWidth <= innerWidth + 1`);
- los controles/formularios esenciales de la ruta (cuando existen) no
  quedan deshabilitados o inutilizables.

## Ejecución local vs CI

Este entorno de desarrollo local bloquea la descarga de los binarios de
Firefox/WebKit de Playwright (proxy TLS con certificado autofirmado,
mismo bloqueo ya documentado para Puppeteer). Por tanto:

- la parte **Chromium** del smoke se ha verificado en local con el
  ejecutable portable de Edge (`QA_CHROMIUM_EXECUTABLE_PATH`), igual que el
  resto de la suite Playwright del repositorio;
- las partes **Firefox** y **WebKit** no se han podido ejecutar en esta
  sesión local por la restricción de red descrita arriba;
- el workflow de CI (`.github/workflows/cross-engine-smoke.yml`) instala
  los tres motores con `npx playwright install --with-deps` en el runner de
  GitHub Actions, que no tiene esta restricción, y ejecuta el smoke
  completo en los tres motores en cada PR relevante.

Cuando el repositorio se ejecute en un entorno sin esa restricción de red,
`node qa/cross-engine-smoke.mjs` ejecuta los tres motores directamente.
