# E.6 · Revalidación de producción — vídeo, Service Worker y Navigation Preload

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **PARTIAL_AUDIT · MEDIA_RANGE_BYPASS_ALREADY_OWNED · NETWORK_FIRST_NAVIGATION_STABLE · NAV_PRELOAD_REQUIRES_COLD_START_EVIDENCE · NO_CODE**.

## 1. Estado real

El problema peligroso de E.6 ya está resuelto en `main`: `service-worker.js` no mete tráfico `Range`, vídeo o audio en el camino genérico de CacheStorage.

El worker actual:

- precachea solo un shell offline pequeño;
- usa network-first para navegación;
- usa network-first para CSS/JS mutables;
- usa stale-while-revalidate para assets normales;
- deja pasar API dinámicas;
- deja pasar cualquier petición con `Range` o destino `video`/`audio`.

Ese contrato debe preservarse. No reabrir cache-first para media ni precachear vídeo completo.

## 2. Navigation Preload

No se ha localizado en `main`:

- `registration.navigationPreload.enable()`;
- consumo de `event.preloadResponse`.

La documentación vigente de MDN mantiene el caso de uso: Navigation Preload permite iniciar la descarga de una navegación en paralelo al arranque del Service Worker y el handler debe consumir `preloadResponse` antes de lanzar un fetch alternativo.

Fuentes consultadas el 30/08/2026:
- https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers
- https://developer.mozilla.org/en-US/docs/Web/API/FetchEvent/preloadResponse

## 3. Por qué no se implementa ahora

La ausencia de Navigation Preload no es por sí sola un defecto. Primero debe observarse un cold start controlado donde:

1. la navegación está bajo un Service Worker ya instalado;
2. el arranque del worker añade latencia medible antes del fetch network-first;
3. esa latencia es material para TTFB/LCP;
4. un piloto con Navigation Preload reduce el contributor;
5. no aparecen peticiones duplicadas;
6. cache y fallback offline siguen comportándose igual.

Sin ese trace, añadirlo introduce otra ruta de respuesta y otra matriz de QA sin una mejora demostrada.

## 4. Gate si se activa

La integración correcta deberá:

- detectar soporte antes de habilitar;
- habilitar durante activación;
- consumir `event.preloadResponse` en navegación;
- integrar esa respuesta con `networkFirstPage()` en vez de crear una estrategia paralela;
- conservar escritura de respuesta válida en PAGE_CACHE cuando proceda;
- mantener fallback de caché/offline;
- probar cold/warm/offline y ausencia de duplicados.

## 5. Vídeo

El vídeo de Home solo debe tocarse con trace de red/render que demuestre un problema concreto: bytes iniciales excesivos, competencia con LCP, autoplay/decode cost, Range incorrecto o stale bytes. La existencia de media visual no basta para cambiar `preload`, reencodear o añadir caché.

## 6. Estado para integración

No hay cambio de runtime en esta PR. E.6 permanece `PARTIAL_AUDIT`: arquitectura base cubierta; Navigation Preload es una optimización condicional basada en cold-start evidence, no deuda obligatoria.