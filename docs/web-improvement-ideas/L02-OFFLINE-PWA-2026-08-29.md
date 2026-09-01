# L.2 · Modo offline para contenido visitado

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.

## Veredicto

#135 terminó concluyendo que la idea original ya está sustancialmente implementada: las páginas visitadas usan estrategia network-first y se guardan en `PAGE_CACHE`; si falla la red se devuelve la copia visitada y, si no existe, `/offline.html`.

La acción correcta es **mantener y auditar esta autoridad**, no ampliar la PWA hacia un modelo offline-first ni precachear todo el Cuaderno.

## Hipótesis original

La lista inicial proponía permitir que los artículos ya visitados pudieran volver a leerse sin conexión —metro, avión, zonas sin cobertura— aprovechando que el sitio ya disponía de PWA.

## Evolución histórica

### Revisión inicial → `PARTIAL_AUDIT`

La primera revisión ya detectó que existía Service Worker y caché, pero pedía medir la experiencia offline antes de ampliar persistencia.

### Matriz → `YA_CUBIERTO`

La inspección más profunda encontró que la conducta exacta ya estaba implementada:

- navegación network-first;
- caché de respuestas correctas;
- fallback a copia visitada;
- `/offline.html` si no hay copia.

### Override de repo → `ALREADY_COVERED`

#135 documentó explícitamente `service-worker.js` como la autoridad existente y ordenó no crear una segunda implementación.

### Autoridad final → `ALREADY_COVERED`

> «Offline/PWA existe y el cache/Range ya fue endurecido. No ampliar caching agresivamente.»

La revalidación independiente mantuvo este estado.

## Estado actual de `main`

`service-worker.js` continúa confirmando el contrato:

```text
request.mode === "navigate"
→ networkFirstPage(request)
→ fetch red
→ putIfCacheable(PAGE_CACHE)
→ si falla: PAGE_CACHE.match(request)
→ si no existe: STATIC_CACHE /offline.html
```

El shell precacheado es deliberadamente pequeño:

- `/offline.html`;
- `manifest.json`;
- iconos;
- fuentes mínimas necesarias para el offline shell.

Las páginas editoriales **no** se precachean.

## Incidente histórico que condiciona L.2

El repositorio conserva comentarios y correcciones tras un incidente real de stale cache: assets mutables podían permanecer con bytes antiguos si el SW los trataba cache-first.

El diseño actual responde a ese aprendizaje:

- CSS/JS → network-first;
- assets → stale-while-revalidate;
- páginas → network-first;
- vídeo/audio/Range → fuera de CacheStorage genérico;
- API/dynamic JSON → fuera de cache PWA.

Por eso «más offline» no es automáticamente mejor.

## Contrato que debe preservarse

### Páginas

La red manda cuando está disponible. La caché es fallback.

### Assets

Pueden reutilizarse offline, pero se refrescan en background cuando hay red.

### APIs

Nunca deben servirse desde `PAGE_CACHE`.

### Vídeo/audio/Range

No pasan por la ruta genérica de CacheStorage, evitando respuestas parciales incorrectas.

### Cachés ajenas

La activación solo elimina nombres pertenecientes al namespace del proyecto; no debe borrar caches arbitrarias del origen.

## Qué significa `ALREADY_COVERED`

No significa que la PWA sea perfecta ni que debamos congelarla. Significa:

- no abrir una implementación de «modo offline» nueva;
- cualquier cambio necesita un fallo reproducible;
- extender el Service Worker existente, nunca otro SW;
- proteger los tests/regresiones de #117 y trabajo posterior.

## Auditoría útil si se retoma

Journey mínimo:

1. online visitar una página del Cuaderno;
2. confirmar respuesta 2xx y cache de navegación;
3. pasar offline;
4. recargar la misma URL;
5. comprobar contenido completo y assets esenciales;
6. visitar una URL nunca vista;
7. comprobar `/offline.html`;
8. volver online;
9. comprobar que bytes mutables se refrescan.

También probar:

- back/forward;
- actualización de SW;
- cache cleanup;
- CSS/JS tras deploy;
- navegación en móvil real.

## Métricas antes de ampliar

Solo plantear más persistencia si hay evidencia de uso/valor, por ejemplo:

- usuarios que vuelven offline;
- sesiones en movilidad;
- feedback explícito;
- fallo concreto de una página visitada que debería sobrevivir.

No precachear contenido por número de artículos ni por «PWA score».

## Qué NO hacer

- precachear todo `cuaderno/`;
- cache-first para HTML editorial;
- cache-first para JS/CSS mutables;
- cachear API responses;
- cachear Range/video sin implementación específica;
- almacenar formularios/PII para «offline submit»;
- crear un toggle «modo offline» que duplique el comportamiento del SW;
- ampliar cache sin strategy/versioning tests.

## Relación con E.6

E.6 documenta vídeo/Range y Navigation Preload como auditoría separada. L.2 no debe reintroducir media al cache genérico.

## Relación con L.1/L.4

Offline, Push y Badging son capacidades distintas. Tener PWA/Service Worker no convierte las otras dos en necesidades automáticas.

## Relación con performance

Más cache puede mejorar relectura, pero también puede servir contenido desactualizado. El contrato del sitio prioriza corrección del contenido/editorial y freshness de deploy sobre una experiencia offline agresiva.

## Trazabilidad preservada

- hipótesis original de contenido visitado offline;
- revisión `PARTIAL_AUDIT`;
- matriz `YA_CUBIERTO`;
- override profundo de repo;
- autoridad final `ALREADY_COVERED`;
- incidente stale-cache y correcciones;
- Service Worker actual `v13`;
- revalidación independiente.

## Recomendación para Clara/Claude

**No construir otro modo offline.** Mantener `service-worker.js` como autoridad y ampliar únicamente ante un fallo/uso medido. No volver a un modelo cache-first ni precache masivo.