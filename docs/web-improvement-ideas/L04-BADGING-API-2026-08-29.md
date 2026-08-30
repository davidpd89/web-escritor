# L.4 · Badge de contenido nuevo en la PWA

Fecha de reconstrucción: 2026-08-29  
Revalidación: 2026-08-30  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## Veredicto

**`REJECT · NO_CANONICAL_UNREAD_STATE · LIMITED_PLATFORM_COVERAGE · NO_CODE`.**

#135 rechazó usar Badging API por beneficio bajo y soporte desigual, pero la razón decisiva sigue siendo de producto: el sitio no mantiene un estado canónico de «contenido nuevo/no leído» que justifique mostrar una insignia persistente.

La tecnología no debe convertirse en producto por existir.

## Hipótesis original

Usar Badging API para señalar contenido nuevo en el icono de la PWA instalada, con menos intrusión que una notificación push.

## Evolución histórica

### Revisión 108/108 → `REJECT`

- disponibilidad no universal;
- no existe estado «no leído» fiable;
- coste de mantener estado mayor que el valor.

### Matriz intermedia → `DEFERIR`

La matriz lo suavizó temporalmente:

> soporte limitado/beneficio bajo; requiere estado de novedades.

### Autoridad final → `REJECT`

> «Badging API sigue Limited Availability y no existe un estado de “novedad” suficientemente útil que justifique mantenerlo.»

La revalidación independiente mantiene L.4 rechazada.

## Revalidación oficial actual

MDN continúa marcando `Navigator.setAppBadge()` y Badging API como **Limited availability / no Baseline** porque no funcionan en algunos navegadores ampliamente usados:

- https://developer.mozilla.org/en-US/docs/Web/API/Badging_API
- https://developer.mozilla.org/en-US/docs/Web/API/Navigator/setAppBadge
- https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Display_badge_on_app_icon

El soporte no es simplemente «sí/no»: Apple soporta Badging en web apps añadidas a Home Screen desde iOS/iPadOS 16.4; en escritorio MDN documenta soporte al instalar desde Chrome/Edge en Windows y macOS; Android puede mostrar badges ligados a notificaciones pero no expone actualmente este API en Chromium.

Por tanto la compatibilidad desigual es una restricción, no el argumento principal para rechazar L.4.

## Estado actual de `main`

Revalidado sobre `main@291c8c677aaa7df635142687d1a6848e80ffcaa2` (tree `68d02e1fe8ac2cfa239f4a716929e992abb672fd`).

El sitio sí dispone de:

- `manifest.json`;
- `service-worker.js`;
- modo `standalone`;
- shortcuts PWA;
- contenido editorial con fechas.

La búsqueda del repositorio no localiza uso de `setAppBadge`/`clearAppBadge` ni un owner de estado equivalente a `lastSeenAt`, `readAt`, `unreadCount`, `newContentSinceLastVisit` o `badgeAcknowledgedAt`.

No hace falta una cuenta de usuario para implementar un badge local, pero sí hace falta una definición y un owner de estado. Ese contrato no existe hoy.

Inventarlo únicamente para colocar un número o punto en el icono sería arquitectura al servicio de una decoración.

## Por qué una fecha global no basta

«Hay un artículo publicado después del 20/08» no equivale necesariamente a «tienes 1 contenido sin leer» porque:

- publicar y leer son hechos distintos;
- `localStorage` sería dispositivo-específico;
- borrar storage reiniciaría el estado;
- una actualización editorial no equivale a una pieza nueva;
- eventos, noticias, libros y artículos tienen semánticas distintas;
- un contador requiere una regla inequívoca de cuándo incrementa y cuándo se limpia.

## Alternativa más simple

Si aparece una necesidad real de destacar una novedad, probar primero una señal visible **in-page** basada en hechos simples:

- etiqueta editorial temporal «Nuevo»;
- fecha visible;
- bloque de novedades;
- actualización en Home;
- newsletter, donde el journey sea coherente con el contrato de privacidad/consentimiento.

Corrección de revalidación: **no se ha localizado RSS/Atom en `main`**, por lo que RSS no debe presentarse como canal existente. Podría evaluarse como alternativa futura de distribución pull, pero no es cobertura actual.

## Relación con L.1

Badging no debe usarse para esquivar el rechazo de Push. Ambos requieren primero definir qué evento merece señalarse al usuario y quién mantiene ese estado.

## Relación con L.3

Tener una PWA instalada y shortcuts no convierte automáticamente el sitio en una aplicación con estado unread.

## Trigger de reapertura

Solo reconsiderar si concurren estas condiciones:

1. existe una conducta recurrente real que el badge ayudaría a resolver;
2. «nuevo/no leído» tiene definición canónica;
3. existe un owner de estado comprensible y testeable;
4. se define cuándo se incrementa, caduca y limpia;
5. la cobertura de plataformas objetivo es suficiente para el caso real;
6. hay fallback visible para entornos sin soporte;
7. pruebas con usuarios demuestran que la insignia aporta valor;
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
- presentar RSS como infraestructura actual cuando no existe.

## Si algún día existiera un modelo de estado

Debe definirse antes de código:

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
- corrección de la falsa cobertura RSS.

## Recomendación para Clara/Claude

**No implementar Badging API.** Si aparece una necesidad real de señalar novedades, empezar por una solución visible in-page y definir primero el modelo de estado. Reabrir Badging únicamente cuando exista ese producto, no para crearlo alrededor del API.
