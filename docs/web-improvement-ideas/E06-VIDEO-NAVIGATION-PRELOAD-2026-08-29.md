# E.6 — Vídeo, Service Worker y Navigation Preload

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`  
Estado efectivo: **`PARTIAL_AUDIT`**

## 1. Por qué E.6 cambió de significado

La idea original hablaba de “lazy-load real del vídeo de intro de Home”. Al contrastarla con el repositorio, #135 encontró que la familia media/PWA ya había sufrido y corregido problemas reales, especialmente caché obsoleta y Range requests.

Por ello E.6 dejó de ser:

> implementar lazy-loading de vídeo

para convertirse en:

> medir el comportamiento real de vídeo/media y navegación con Service Worker; no reabrir el sistema salvo que un trace demuestre un contributor concreto.

La autoridad final añadió además una posibilidad específica: **Navigation Preload** para cold navigation network-first, pero solo si se demuestra mejora y se consume `preloadResponse` correctamente.

Esta PR es docs-only.

## 2. Veredicto

**`PARTIAL_AUDIT`**.

La infraestructura ya existe y tiene historia de correcciones. No construir otro sistema de caché/media.

Preguntas abiertas:

- ¿cuántos bytes de vídeo/poster se transfieren en carga inicial real?
- ¿el vídeo compite con LCP o main-thread work?
- ¿qué ocurre en cold navigation cuando el Service Worker arranca?
- ¿Navigation Preload reduciría espera de navegación network-first?
- ¿el navegador/origen maneja correctamente Range y media actual?

Sin trace, no tocar.

## 3. Hipótesis original

E.6 se formuló inicialmente como:

- confirmar que el vídeo de intro no bloquea hilo principal;
- asegurar que no se convierte en LCP si no es contenido principal;
- aplicar lazy-load/preload apropiado.

Era una hipótesis basada en un patrón común, todavía sin incorporar las correcciones PWA concretas del repo.

## 4. Evolución histórica

| Fase | Estado | Motivo |
|---|---|---|
| Idea original | optimizar/lazy-load vídeo | Evitar coste de media en Home. |
| Revisión 108/108 | `PARTIAL_AUDIT` | SW/media ya corregido; medir preload/poster/video/LCP antes de tocar. |
| Matriz intermedia | `YA_CUBIERTO/VERIFICAR` | No reabrir sin trace. |
| Autoridad final | `PARTIAL_AUDIT` | Añade cold navigation y Navigation Preload como hipótesis medible. |
| Revalidación independiente | mantenida | La arquitectura PWA existente se conserva. |
| `main` actual | `PARTIAL_AUDIT` | Media/Range bypass existe; Navigation Preload no se ha localizado. |

## 5. Genealogía de problemas reales

La historia de `service-worker.js` demuestra por qué E.6 no debe tratarse como una optimización aislada.

### `b3db6b63f8993ecd88493139f20e7622ff4a6261`

Commit que documenta el fallo observado:

- el vídeo funcionaba en Incognito pero no en un móvil ya visitado;
- el Service Worker servía assets cache-first sin revalidación;
- el dispositivo conservaba bytes antiguos;
- se elevó la versión de cache como corrección inmediata.

Ese diagnóstico es especialmente valioso porque Incognito, al no usar el mismo SW/cache persistente, ayudó a distinguir un problema de bytes/caché de un problema del vídeo en sí.

### `dd4b2f7c538547baeeb76baa01d7a5e34cd86f1e`

`fix: stop serving mutable assets indefinitely from PWA cache`

Endurece la estrategia para evitar que assets mutables queden servidos indefinidamente.

Esta genealogía debe preservarse: “optimizar vídeo” sin considerar SW puede reintroducir la clase de bug ya resuelta.

## 6. Estado actual de Service Worker

`service-worker.js` actual usa:

- navigation network-first;
- network-first para CSS/JS;
- stale-while-revalidate en assets apropiados;
- cachés versionadas;
- fallback offline;
- bypass explícito para media y Range requests.

Condición relevante actual:

```text
request has Range
OR destination is video/audio
→ bypass generic Cache API handling
```

Esto evita tratar una petición parcial de media como un asset binario normal cacheado de forma incorrecta.

## 7. Range requests

Los reproductores suelen solicitar rangos de bytes para seek/streaming. Un Service Worker que intercepte y responda incorrectamente puede romper:

- reproducción;
- seek;
- reanudación;
- compatibilidad móvil;
- validación de contenido parcial.

La solución actual evita que el camino genérico del SW se apropie de esas peticiones.

D.6/E.6 no debe reintroducir cache-first para vídeo por perseguir offline completo.

## 8. Navigation Preload

La autoridad final de #135 introdujo esta hipótesis específica.

Problema potencial:

1. el navegador inicia una navegación;
2. tiene que arrancar el Service Worker;
3. el SW decide network-first;
4. solo entonces inicia fetch;
5. ese startup puede añadir latencia en cold navigation.

Navigation Preload permite que la petición de red pueda empezar en paralelo al arranque del worker.

Pero habilitarlo sin consumir `event.preloadResponse` no aporta el beneficio esperado y puede crear tráfico duplicado.

## 9. Estado actual de Navigation Preload

La revisión de `main` no ha localizado:

- `registration.navigationPreload.enable()`;
- `event.preloadResponse`.

Eso **no significa que deba implementarse**. Solo confirma que la hipótesis de la autoridad final no está ya materializada.

El estado sigue siendo `PARTIAL_AUDIT` porque falta demostrar que startup del SW sea un contributor relevante.

## 10. Auditoría de vídeo correcta

Para la ruta que contenga vídeo/intro real:

### Network

- bytes del poster;
- bytes de vídeo antes de interacción/viewport;
- número/tipo de Range requests;
- cache headers;
- request priority;
- momento de inicio.

### Render

- elemento LCP real;
- CLS;
- main-thread work asociado;
- decode/render delay cuando sea visible.

### Mobile

- conexión lenta simulada;
- viewport pequeño;
- autoplay policy si aplica;
- reduced motion si el diseño lo requiere;
- data saver/comportamientos nativos donde sea observable.

## 11. Auditoría de cold navigation

Comparar al menos:

```text
A. primera visita sin SW controlador
B. visita con SW ya instalado/warm
C. cold start del SW
D. offline
```

Para Navigation Preload interesa especialmente C.

Registrar:

- navigation request start;
- worker startup;
- response start;
- TTFB;
- LCP;
- duplicate requests.

## 12. Gate para Navigation Preload

Implementar solo si:

```text
NETWORK_FIRST_NAVIGATION
AND COLD_SW_STARTUP_ADDS_MEASURABLE_DELAY
AND NAV_PRELOAD_REDUCES_DELAY
AND preloadResponse_IS_CONSUMED
AND NO_DUPLICATE_FETCH
AND OFFLINE_FALLBACK_STILL_WORKS
```

## 13. Blueprint mínimo si se justifica

Activación durante `activate`/setup según contrato del SW y luego, en navegación:

```js
const preload = await event.preloadResponse;
if (preload) {
  return preload;
}
return fetch(event.request);
```

El código anterior es conceptual; cualquier implementación debe integrarse con `networkFirstPage()` y sus caches/fallbacks actuales, no sustituirlos de forma ad hoc.

## 14. No hacer con Navigation Preload

- activarlo “porque existe”;
- activar y no leer `preloadResponse`;
- lanzar además un `fetch()` inmediato que duplique request;
- romper offline fallback;
- usarlo en requests que no son navegación;
- mezclar el experimento con cambios simultáneos de vídeo/caché/HTML que impidan atribución.

## 15. No hacer con vídeo

- precachear vídeos completos sitewide;
- cache-first de Range/media;
- forzar preload `auto` sin medir;
- cargar vídeo pesado solo por efecto visual;
- asumir que `loading=lazy` existe/aplica igual que en `<img>`;
- sustituir poster bien optimizado por frame/video inicial más caro;
- convertir el vídeo en candidato LCP accidental;
- reencodear sin comparar calidad/compatibilidad;
- invalidar caches manualmente como solución permanente.

## 16. Relación con E.3

Si el poster/imagen inicial es LCP, su prioridad pertenece a E.3. Si el vídeo se descarga antes de ese recurso y compite con él, E.6 puede reducir/posponer media.

No añadir `fetchpriority=high` al vídeo como reacción automática.

## 17. Relación con E.5

Un performance budget puede mostrar que media domina bytes, pero E.6 decide comportamiento de carga y SW. No meter vídeo completo en un budget de shell si no se descarga en ese momento.

## 18. Relación con PWA/offline

La investigación histórica de #135 sobre L.2 concluyó que contenido visitado offline ya está cubierto mediante network-first y cache de páginas.

Eso no obliga a que vídeo sea offline-first. Media pesada tiene contratos diferentes.

## 19. Criterio de éxito

Para un cambio de media:

- menor transferencia inicial si esa era la causa;
- LCP igual o mejor;
- reproducción sigue funcionando;
- Range/seek correcto;
- móvil correcto;
- no stale media persistente.

Para Navigation Preload:

- cold navigation mejora de forma repetible;
- warm navigation no empeora;
- no duplicados;
- offline sigue correcto.

## 20. Pasadas tardías

La autoridad final es la fuente específica que añade Navigation Preload a E.6. Las pasadas PWA posteriores mantienen la filosofía de no expandir offline/cache sin necesidad.

La revalidación independiente conserva E.6.

## 21. Estado de verdad

- `DOCUMENTED`: sí.
- infraestructura SW/media base implementada en main: sí.
- `IMPLEMENTED_IN_PR`: no.
- Navigation Preload implementado: no localizado.
- `CONFIGURED_LIVE`: no se inspeccionan aquí headers/media live.
- `VERIFIED_E2E`: no.

## 22. DoD de futura auditoría

- trace de carga vídeo/poster;
- bytes y Range observados;
- LCP identificado;
- cold/warm SW comparados;
- Navigation Preload solo si hay contributor;
- `preloadResponse` consumido si se implementa;
- no requests duplicados;
- PWA/offline tests verdes;
- reproducción/seek móvil verificados;
- no reabrir cache-first de media.

## 23. Fuentes históricas

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- historial PWA/Range recuperado por #135.

Evidencia actual/genealógica:

- `service-worker.js`;
- commit `b3db6b63…`;
- commit `dd4b2f7c…`;
- `main` `291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## 24. Conclusión

E.6 permanece **`PARTIAL_AUDIT`**. El sitio ya aprendió de un fallo real de media cacheada y tiene un contrato más seguro para Range/video. La siguiente mejora no es reescribirlo: es medir bytes, LCP y cold navigation. Navigation Preload solo entra si el arranque del Service Worker aparece en un trace como contributor y la implementación consume correctamente la respuesta precargada sin duplicar tráfico.