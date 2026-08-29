# L.4 · Badge de contenido nuevo en la PWA

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## Veredicto

#135 rechazó usar Badging API: soporte limitado, beneficio bajo y —más importante— el sitio no mantiene un estado canónico de «contenido nuevo/no leído» que justifique mostrar una insignia persistente.

La tecnología no debe convertirse en producto por existir.

## Hipótesis original

Usar la Badging API para señalar contenido nuevo en el icono de la PWA instalada, con menos intrusión que una notificación push.

## Evolución histórica

### Revisión 108/108 → `REJECT`

- Limited availability / no Baseline;
- no existe estado «no leído» fiable;
- coste de mantener estado mayor que el valor.

### Matriz intermedia → `DEFERIR`

La matriz lo suavizó temporalmente:

> soporte limitado/beneficio bajo; requiere estado de novedades.

### Autoridad final → `REJECT`

> «Badging API sigue Limited Availability y no existe un estado de “novedad” suficientemente útil que justifique mantenerlo.»

La revalidación independiente mantuvo L.4 rechazada.

## Revalidación oficial actual

MDN continúa marcando Badging API como **Limited availability** y no Baseline porque no funciona en algunos navegadores ampliamente usados.

Fuente: https://developer.mozilla.org/en-US/docs/Web/API/Badging_API

MDN describe su caso típico como indicar que un estado de aplicación ha cambiado, por ejemplo mensajes nuevos. El problema del proyecto no es llamar `setAppBadge()`: es determinar de forma correcta qué significa «nuevo» para cada lector.

## Estado actual de `main`

El sitio sí dispone de:

- manifest;
- service worker;
- shortcuts;
- contenido editorial con fechas.

Pero no existe una cuenta/identidad de lector ni un modelo central de:

```text
lastSeenAt
lastReadArticle
unreadCount
newContentSinceLastVisit
badgeAcknowledgedAt
```

Inventar ese estado solo para poner un número/punto en el icono sería arquitectura al servicio de una decoración.

## Por qué una fecha global no basta

«Hay un artículo publicado después del 20/08» no significa necesariamente «tienes 1 contenido sin leer» porque:

- no sabemos qué piezas interesan al usuario;
- no sabemos cuáles ha leído en otro dispositivo;
- localStorage sería dispositivo-específico;
- borrar storage reinicia el estado;
- artículos actualizados no equivalen a nuevos;
- eventos/noticias/libros tienen semánticas distintas.

## Alternativa más simple

Si alguna vez existe una necesidad clara de destacar novedad, primero probar una señal **in-page** basada en hechos simples:

- «Nuevo» editorial y temporal;
- fecha visible;
- sección de novedades;
- newsletter/RSS;
- actualización en Home.

Esto evita mantener un unread model oculto.

La revalidación de #135 ya proponía precisamente un indicador in-page solo si se demuestra útil.

## Relación con L.1

Badging no debe usarse para esquivar el rechazo de Push. Ambos necesitan un concepto claro de qué merece interrumpir/señalar al usuario.

## Relación con D.4/P.2

Crear estado local persistente por Badging también abriría decisiones de almacenamiento que otras ideas dejaron condicionadas/rechazadas. No introducir `localStorage` por una insignia.

## Relación con L.3

Tener una PWA instalada y shortcuts no crea automáticamente una aplicación con estado unread.

## Trigger de reapertura

Solo reconsiderar si:

1. existe una conducta recurrente real;
2. «nuevo/no leído» tiene definición canónica;
3. el estado puede mantenerse de forma comprensible;
4. el soporte de plataformas objetivo es suficiente;
5. testing demuestra que la insignia ayuda;
6. existe UX para limpiar/actualizar el badge.

En el proyecto actual estos triggers no se cumplen.

## Qué NO hacer

- usar badge `1` cada vez que se publica algo;
- mantener contador local por artículos sin identidad;
- añadir Badging como «complemento» de shortcuts;
- inferir lectura por scroll;
- combinarlo con Push sin estrategia de notificaciones;
- degradar navegación si no hay soporte;
- presentar disponibilidad limitada como fallo que debamos polyfillar.

## Si algún día existiera un modelo de estado

Debería definirse antes de código:

```text
what counts as new
scope (site/category/book)
state owner
where state lives
multi-device semantics
expiry/reset
privacy implications
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
- MDN actual: Limited availability.

## Recomendación para Clara/Claude

**No implementar Badging API.** Si algún día hay una necesidad real de señalar novedades, empezar por una solución visible in-page y definir primero el modelo de estado; no construirlo para justificar el badge.