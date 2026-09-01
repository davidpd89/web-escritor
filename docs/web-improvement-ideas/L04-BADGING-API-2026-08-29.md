# L.4 · Badge de contenido nuevo en la PWA

Fecha de reconstrucción: 2026-08-29  
Revalidación: 2026-08-30  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## Veredicto

**`REJECT · NO_CANONICAL_UNREAD_STATE · LIMITED_PLATFORM_COVERAGE · RSS_ALREADY_COVERED · NO_CODE`.**

#135 rechazó Badging API por beneficio bajo y soporte desigual. La razón decisiva sigue siendo de producto: el sitio no mantiene un estado canónico de «contenido nuevo/no leído» que justifique mostrar una insignia persistente.

La tecnología no debe convertirse en producto por existir.

## Hipótesis original

Usar Badging API para señalar contenido nuevo en el icono de la PWA instalada, con menos intrusión que una notificación Push.

## Evolución histórica

- revisión 108/108 → `REJECT`;
- matriz intermedia → `DEFERIR`;
- autoridad final → `REJECT`;
- revalidación independiente → rechazo mantenido.

El hilo constante es el mismo: soporte desigual + ausencia de semántica útil de «no leído» + coste de mantener estado mayor que el valor demostrado.

## Revalidación oficial actual

MDN continúa marcando `Navigator.setAppBadge()` y Badging API como **Limited availability / no Baseline**:

- https://developer.mozilla.org/en-US/docs/Web/API/Badging_API
- https://developer.mozilla.org/en-US/docs/Web/API/Navigator/setAppBadge
- https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Display_badge_on_app_icon

El soporte no es simplemente «sí/no»: Apple soporta Badging en web apps añadidas a Home Screen desde iOS/iPadOS 16.4; en escritorio existen entornos Chrome/Edge compatibles; Android puede mostrar badges ligados a notificaciones pero no expone el API de forma equivalente en todos los entornos.

La compatibilidad es una restricción, no el argumento principal para rechazar L.4.

## Estado actual de `main`

Revalidado sobre `main@291c8c677aaa7df635142687d1a6848e80ffcaa2` (tree `68d02e1fe8ac2cfa239f4a716929e992abb672fd`).

El sitio dispone de:

- `manifest.json`;
- `service-worker.js`;
- modo `standalone`;
- shortcuts PWA;
- newsletter;
- RSS real del Cuaderno;
- contenido editorial público.

No se localiza uso de `setAppBadge`/`clearAppBadge` ni un owner de estado equivalente a `lastSeenAt`, `readAt`, `unreadCount`, `newContentSinceLastVisit` o `badgeAcknowledgedAt`.

No hace falta una cuenta de usuario para implementar un badge local, pero sí una definición y un owner de estado. Ese contrato no existe hoy. Inventarlo únicamente para colocar un número o punto en el icono sería arquitectura al servicio de una decoración.

## Corrección de revalidación · RSS sí existe

Una búsqueda inicial no devolvió el feed y llevó a documentar RSS erróneamente como ausente. La comprobación directa posterior de O.1 corrige ese punto.

`main` contiene:

```text
scripts/build-feed.py
cuaderno/feed.xml
assets/rss.xsl
/cuaderno/ -> rel=alternate application/rss+xml
footer -> RSS del Cuaderno
```

El builder ofrece `--check`, excluye `noindex` y `CollectionPage`, limita y ordena el output de forma determinista.

RSS es por tanto un canal real de distribución pull. Esto no resuelve por sí solo la semántica de un badge, pero sí ofrece una alternativa abierta para descubrir novedades sin crear estado unread.

## Por qué una fecha global no basta

«Hay un artículo publicado después del 20/08» no equivale necesariamente a «tienes 1 contenido sin leer» porque:

- publicar y leer son hechos distintos;
- `localStorage` sería dispositivo-específico;
- borrar storage reiniciaría el estado;
- una actualización editorial no equivale a una pieza nueva;
- eventos, noticias, libros y artículos tienen semánticas distintas;
- un contador requiere una regla inequívoca de incremento y limpieza.

## Alternativas más simples

Si aparece una necesidad real de destacar una novedad, empezar por mecanismos que no requieran estado unread persistente:

- etiqueta temporal «Nuevo»;
- fecha visible;
- bloque de novedades;
- actualización en Home;
- RSS del Cuaderno;
- newsletter, una vez estabilizado el crossfinding #206.

## Relación con L.1

Badging no debe usarse para esquivar el rechazo de Push. Ambos requieren definir primero qué evento merece señalarse al usuario y quién mantiene su estado. L.1 además confirma que RSS ya cubre la distribución pull editorial.

## Relación con L.3

Tener PWA instalada y shortcuts no convierte automáticamente el sitio en una aplicación con estado unread.

## Trigger de reapertura

Solo reconsiderar si concurren estas condiciones:

1. existe una conducta recurrente real que el badge ayudaría a resolver;
2. «nuevo/no leído» tiene definición canónica;
3. existe un owner de estado comprensible y testeable;
4. se define cuándo incrementa, caduca y limpia;
5. la cobertura de plataformas objetivo es suficiente;
6. hay fallback visible para entornos sin soporte;
7. pruebas con usuarios demuestran valor;
8. almacenamiento y privacidad están documentados si se persiste estado.

En el proyecto actual estos triggers no se cumplen.

## Qué NO hacer

- usar badge `1` cada vez que se publica algo sin semántica de lectura;
- mantener contador local solo para justificar el API;
- añadir Badging como complemento automático de shortcuts;
- inferir lectura por scroll;
- combinarlo con Push sin estrategia de notificaciones;
- degradar navegación si no hay soporte;
- polyfillar una señal de sistema que la plataforma no expone;
- volver a afirmar que RSS no existe sin inspeccionar `/cuaderno/feed.xml` y su builder.

## Si algún día existiera un modelo de estado

Definir antes de código:

```text
what counts as new
scope (site/category/book)
state owner
where state lives
multi-device semantics (if any)
expiry/reset
privacy implications
badge set rule
badge clear rule
fallback UI
```

## Trazabilidad preservada

- hipótesis original;
- revisión `REJECT`;
- matriz `DEFERIR`;
- autoridad final `REJECT`;
- revalidación independiente;
- estado PWA actual;
- soporte oficial actual;
- corrección RSS basada en inspección directa de O.1.

## Recomendación para Clara/Claude

**No implementar Badging API.** El sitio ya dispone de RSS para distribución pull; si aparece una necesidad distinta de señalizar «no leído», definir primero el modelo de estado y demostrar valor antes de incorporar Badging.