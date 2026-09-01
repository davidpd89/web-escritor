# J.3 · Revalidación de producción — calendario ICS para clubes

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`

## Veredicto

`ALREADY_CAPABLE · ICS_PIPELINE_CANONICAL · NO_SCHEDULED_CLUB_EVENT_TRIGGER · NO_NEW_CALENDAR`

## Evidencia directa

`scripts/build-event-calendars.py` ya implementa el pipeline correcto:

- `eventos.html` es la fuente canónica mediante JSON-LD `Event`;
- solo `EventScheduled` genera `.ics`;
- `EventCompleted` y `EventCancelled` no generan calendarios;
- valida fechas/offsets, `@id`, UID, RFC5545, enlaces visibles y huérfanos;
- dispone de `--check` y de salida determinista en `assets/events/calendar/`.

En el `eventos.html` auditado, los eventos declarados son históricos (`EventCompleted`). No hay una sesión de club futura confirmada que deba producir un ICS.

## Decisión

No crear:

- un segundo builder para clubes;
- `agenda.ics` paralelo;
- Google Calendar API/OAuth;
- recordatorios inventados;
- un evento de prueba publicado.

## Activación futura

Cuando exista una sesión real y confirmada:

1. declararla en la autoridad general `eventos.html` con `EventScheduled` y datos verificables;
2. añadir el enlace visible de descarga que exige el pipeline;
3. ejecutar `scripts/build-event-calendars.py`;
4. validar con `--check` y tests existentes;
5. pasar a `EventCompleted` después del evento y regenerar, eliminando el ICS ya no aplicable.

Una sesión de club es un tipo de evento dentro del sistema general, no una razón para crear otro calendario.

## Cierre

La capacidad técnica de J.3 ya existe. El único trigger pendiente es editorial/operativo: una fecha real. Hasta entonces, el estado correcto es cero ICS futuros y cero eventos ficticios.