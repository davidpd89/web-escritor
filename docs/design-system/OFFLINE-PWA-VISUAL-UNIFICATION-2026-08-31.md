# Offline PWA — contrato de unificación visual y actualización de caché

Fecha: 2026-08-31
Estado: contrato preparado; implementación pendiente
Cadena: continúa después de `DISEÑO - AI` (#289)

## Superficies técnicas

- `/offline.html`
- `service-worker.js` únicamente en lo necesario para distribuir de forma correcta una nueva versión del fallback offline

## Baseline verificado

`offline.html` es una superficie autocontenida y deliberadamente pequeña:

- `noindex, follow`;
- CSS inline;
- fuentes locales mínimas (`Instrument Serif` y `Manrope`);
- `color-scheme: light`;
- `theme-color: #080a0c`;
- accent legacy `#0075b8`;
- glow radial cian basado en `rgba(0,117,184,...)`;
- tarjeta central, marca `DP`, mensaje de estado y dos acciones;
- safe-area padding;
- `prefers-reduced-motion`;
- sin JS las acciones se ocultan porque dependen de runtime;
- con JS permite reintentar, volver atrás y reaccionar a `online`.

## Dependencia PWA crítica

`service-worker.js` precachea `/offline.html` dentro del `APP_SHELL` junto con manifest, iconos y las dos fuentes. El cache actual usa `david-porto-pwa-v13` y la instalación es atómica mediante `cache.addAll()`.

Por tanto, si esta PR modifica `offline.html` pero deja inalterado el script/versión del service worker, clientes que ya tengan el worker actual pueden conservar la copia vieja del fallback y no recibir el rediseño.

La implementación debe decidir explícitamente el mecanismo de actualización y probarlo. Si el contrato actual requiere bump de `CACHE_VERSION`, hacerlo de forma mínima y documentada; no tocar estrategias de caching ajenas a esta necesidad.

## Dirección visual

**Estado de recuperación editorial**, no una mini landing ni un error dramático.

Objetivos:

1. coherencia inmediata con la identidad azul/dorado actual;
2. mensaje comprensible en una situación de fallo de red;
3. acción primaria clara y secundaria discreta;
4. diseño extremadamente robusto sin dependencias de red;
5. mínimos bytes y recursos;
6. funcionamiento correcto en safe areas y viewport pequeño.

Eliminar/reconciliar la fuga `#0075b8` y revisar si `theme-color #080a0c` sigue teniendo sentido con una superficie `color-scheme: light` y fondo blanco. No aplicar gradientes o decoración compleja por consistencia estética.

## Preservar estrictamente

- `noindex, follow`;
- funcionamiento sin red real;
- fallback desde navegación fallida;
- fuentes precacheadas mínimas;
- safe-area insets;
- `navigator.onLine`/evento `online` y `aria-live`;
- lógica de reintento;
- ocultación de `Volver atrás` cuando no hay historial;
- reduced motion;
- experiencia no-JS legible;
- política de cache para APIs, media y páginas fuera de lo estrictamente necesario.

No convertir esta PR en refactor general del service worker.

## Implementación esperada

Mantener la autonomía de `offline.html`: no cargar CSS principal, analytics, imágenes remotas, newsletter ni shell interactivo.

Revisar:

- colores/tokens locales equivalentes al sistema actual;
- theme-color;
- jerarquía de marca/mensaje/estado;
- card vs composición más editorial y simple;
- focus;
- touch targets;
- estados online/offline;
- textos largos;
- landscape móvil;
- forced colors;
- contraste.

## QA requerido

### Visual/reflow

- 1440×1000;
- 1024×768;
- 390×844 y 360×800;
- 320 px;
- landscape móvil bajo;
- zoom 200 %;
- text spacing;
- teclado/focus;
- reduced motion;
- forced-colors smoke;
- cero overflow;
- safe areas.

### Funcional

Probar en contexto controlado:

1. instalación limpia del service worker;
2. `APP_SHELL` completo y atómico;
3. navegación online normal;
4. navegación a ruta no cacheada con red cortada → entrega `offline.html`;
5. `Reintentar` sin red;
6. recuperación de red/evento `online`;
7. historial ausente/presente para `Volver atrás`;
8. no-JS con mensaje legible;
9. upgrade desde cache/worker anterior al nuevo, verificando que el nuevo `offline.html` se entrega realmente;
10. caches no relacionados no se borran.

No simular un PASS de offline sirviendo directamente `/offline.html`; el QA principal debe ejercer el flujo real del service worker.

## Aislamiento

No cambiar estrategias de caché de API, media, CSS/JS, assets o páginas salvo que una prueba demuestre un defecto directamente relacionado. No tocar manifest/iconos salvo necesidad verificada.

## Cierre

Mantener Draft y sin merge. No cerrar hasta que visual + actualización PWA + fallback real estén verdes. Revisión física final en iOS/Android/PWA cuando sea posible bajo `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.