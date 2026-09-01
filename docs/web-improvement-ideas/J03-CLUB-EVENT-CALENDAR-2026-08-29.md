# J.3 · Calendario `.ics` para sesiones reales del club

**Estado histórico final de PR #135:** `PARTIAL_AUDIT`  
**Matriz intermedia:** `IMPLEMENTAR BAJO COSTE`  
**Conclusión:** la infraestructura ya existe; no construir otra integración. Cuando exista una sesión real del club, declararla en la autoridad de eventos y reutilizar el pipeline actual.

## 1. Hipótesis original

J.3 proponía un botón “Añadir a mi calendario” para sesiones de club, mediante `.ics` descargable y sin proveedor externo.

A primera vista parecía una implementación nueva de bajo coste. La inspección profunda del repositorio cambió el diagnóstico: el sitio ya dispone de un sistema de calendarios más general y robusto.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Generar `.ics` simple para una sesión del club. |
| Revisión 108/108 | `PARTIAL_AUDIT` | Ya existe `/herramientas/eventos-ics/`; reutilizar misma fuente. |
| Matriz operativa | `IMPLEMENTAR BAJO COSTE` | `.ics` encaja y no necesita tercero. |
| Repo cross-check profundo | infraestructura ya implementada | `build-event-calendars.py` genera ICS desde EventScheduled JSON-LD y tiene tests. |
| Override de repo | `PARTIAL_AUDIT` reafirmado | Solo falta que exista una sesión real que declarar. |
| Autoridad final | `PARTIAL_AUDIT` | No abrir un “calendario del club” nuevo. |
| Revalidación independiente | mantenido | Estados J mantenidos. |

La diferencia `IMPLEMENTAR BAJO COSTE` → `PARTIAL_AUDIT` es material: técnicamente la idea es buena, pero **la capacidad ya está construida**. Lo pendiente es verificar/usar la autoridad cuando exista un evento real.

## 3. Estado real de `main` al 29/08/2026

`main@291c8c677aaa7df635142687d1a6848e80ffcaa2` confirma:

### `scripts/build-event-calendars.py`

- fuente única por defecto: `eventos.html`;
- extrae nodos JSON-LD `Event`;
- solo genera para `eventStatus = EventScheduled`;
- ignora completed/cancelled;
- exige `@id` utilizable;
- valida `startDate/endDate`;
- exige offset/Z en DATE-TIME;
- normaliza a UTC;
- genera UID estable;
- usa DTSTAMP estable;
- escapa texto;
- hace line folding RFC5545;
- incluye SUMMARY, DESCRIPTION, LOCATION, URL;
- comprueba que existe enlace visible con `data-calendar-download`;
- soporta `--check`;
- detecta `.ics` huérfanos.

### Tests históricos/localizados por #135

- `tests/test-event-calendars.py`;
- `tests/test-evento-ics-rfc5545.mjs`.

### Herramienta manual

Existe además `/herramientas/eventos-ics/`.

### Autoridad de eventos actual

`eventos.html` ya documenta firmas, ferias, presentaciones, clubes y encuentros como familia editorial. En la inspección actual, los eventos JSON-LD recuperados en el fragmento revisado están marcados como `EventCompleted`; no se ha identificado una sesión futura concreta del club que justifique generar un ICS nuevo ahora.

## 4. La arquitectura correcta

La fuente de verdad debe seguir siendo:

```text
eventos.html / autoridad de eventos
        ↓
EventScheduled JSON-LD
        ↓
build-event-calendars.py
        ↓
/assets/events/calendar/<fragment>.ics
        ↓
enlace visible data-calendar-download
```

No crear:

```text
club-event.json
club-calendar.js
club-ics-builder.py
```

si duplican la autoridad general.

## 5. Trigger correcto

J.3 se activa cuando existe un evento factual, por ejemplo:

- sesión de club confirmada;
- presentación/encuentro con club;
- lectura guiada con fecha/hora;
- AMA/live con fecha si realmente requiere calendario;
- evento de biblioteca/instituto confirmado.

Antes de declararlo deben conocerse, cuando aplique:

- nombre;
- fecha;
- hora/zona;
- ubicación o modalidad online;
- URL pública correcta;
- estado Scheduled;
- organizador;
- instrucciones necesarias.

No publicar un placeholder para “próximamente”.

## 6. Qué debe hacer una futura PR de evento

1. añadir/actualizar el evento en la autoridad actual;
2. usar `EventScheduled` correcto;
3. añadir CTA visible “Añadir al calendario” donde tenga sentido;
4. ejecutar builder;
5. ejecutar `--check` y tests RFC5545;
6. comprobar descarga real;
7. probar importación al menos en calendarios representativos cuando sea posible;
8. al cancelar/completar, actualizar primero la autoridad y regenerar;
9. evitar `.ics` huérfanos.

## 7. Cancelación y cambios

El sistema actual omite completed/cancelled en generación. Para un evento que ya fue distribuido hay una consideración operativa adicional:

- actualizar página/estado visible inmediatamente;
- no confiar en que borrar un `.ics` ya descargado modifique calendarios del usuario;
- si se necesita actualización calendar-subscription/sequence avanzada, eso sería una capacidad distinta y requeriría reevaluación.

J.3 original era descarga simple, no un servicio de calendario sincronizado.

## 8. Accesibilidad y UX

El enlace de calendario:

- debe tener texto comprensible;
- no debe depender solo de icono;
- debe indicar si descarga archivo cuando sea útil;
- debe convivir con fecha/hora visible en HTML;
- el `.ics` no sustituye la información humana de la página;
- no debe aparecer para eventos pasados/cancelados.

## 9. Privacidad

La descarga `.ics` estática es especialmente adecuada porque:

- no requiere cuenta;
- no requiere Google Calendar API;
- no requiere Microsoft Graph;
- no expone el calendario personal del visitante;
- no necesita OAuth;
- no introduce un nuevo tercero.

No sustituir esta solución por botones de terceros salvo una necesidad nueva demostrada.

## 10. Relación con otras ideas

- **J.2:** un club por sesiones puede usar un ICS por reunión real.
- **J.5:** un AMA con fecha podría usar el mismo pipeline; un AMA puramente asíncrono no lo necesita.
- **C.1/Q.4:** eventos de lanzamiento deben seguir autoridad/runbook factual.
- **E.8/I.2:** la solución estática evita sumar third parties.

## 11. Qué no hacer

- No crear otro builder ICS exclusivo del club.
- No introducir Google Calendar API/OAuth para una descarga simple.
- No publicar eventos hipotéticos.
- No generar para EventCompleted/EventCancelled.
- No editar `.ics` a mano si deriva de JSON-LD.
- No mantener fecha/hora distinta entre HTML, JSON-LD e ICS.
- No tratar la existencia de `/herramientas/eventos-ics/` como única autoridad de agenda.

## 12. Definition of Done para una sesión real

- [ ] evento real confirmado;
- [ ] declarado una sola vez en autoridad de eventos;
- [ ] `EventScheduled` y timestamps válidos;
- [ ] enlace visible `data-calendar-download`;
- [ ] builder genera exactamente un ICS esperado;
- [ ] `--check` verde;
- [ ] tests RFC5545 verdes;
- [ ] fecha/hora/ubicación coinciden entre UI, JSON-LD e ICS;
- [ ] no hay `.ics` huérfanos;
- [ ] no se añade tercero/OAuth;
- [ ] estado se actualiza al completar/cancelar.

## 13. Trazabilidad #135

Revisados:

- banco original J.3;
- revisión 108/108: `PARTIAL_AUDIT` y reutilización de `/herramientas/eventos-ics/`;
- matriz final: `IMPLEMENTAR BAJO COSTE`;
- repo cross-check: infraestructura detallada;
- overrides de repo: `build-event-calendars.py`, tests y regla de reutilización;
- autoridad machine-readable;
- autoridad humana final: `PARTIAL_AUDIT`;
- revalidación independiente: estado mantenido.

## 14. Cierre

J.3 es un buen ejemplo de por qué se está reconstruyendo #135 idea por idea: la idea era buena, pero **implementarla otra vez sería un error**. El trabajo futuro consiste en declarar correctamente una sesión real y dejar que el sistema de eventos ya existente genere el calendario.