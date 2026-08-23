# Pendiente V — `human-site-stats` no puede depender del reloj del runner

Fecha: 2026-08-23  
Base: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`

## Problema

Al validar #77, `content-index-check.yml` falló en `build-human-site-stats.py --check` aunque los dos pasos nuevos de calendarios habían pasado.

La causa es independiente de #77: el builder usa `date.today().isoformat()` como valor por defecto de `--date`, y ese valor forma parte tanto del HTML como del JSON generado. Los artefactos actuales fueron generados el 2026-08-22. El 2026-08-23, sin ningún cambio en libros, artículos o herramientas, `--check` reconstruye el bloque con otra fecha y declara desactualizados:

- `data/site-human-stats.generated.html`;
- `data/site-human-stats.generated.json`;
- el bloque generado de `autor.html`.

Por tanto un checkout idéntico puede pasar CI un día y fallar al siguiente. Eso contradice el propósito declarado del propio script: estadísticas reproducibles.

## Evidencia

El log del workflow de #77 mostró:

- calendario del sitio: PASS (`0 EventScheduled`, estado correcto);
- tests de calendario: 6/6 PASS;
- después: `FAIL: HTML desactualizado`, `FAIL: JSON desactualizado`, `autor.html desactualizado` en `build-human-site-stats.py --check`.

El JSON versionado conserva `generated_on: 2026-08-22`; el checker ejecutado el 23/08 usaba implícitamente 2026-08-23.

## Solución

Mantener la semántica pública actual sin introducir frescura falsa:

- una **regeneración normal** sin `--date` sigue registrando la fecha real del día;
- un **`--check`** sin `--date` reutiliza `generated_on` del JSON generado que está validando;
- un `--date YYYY-MM-DD` explícito sigue teniendo prioridad;
- fechas inválidas o JSON generado corrupto fallan de forma explícita.

Así `--check` compara contenido derivado contra contenido derivado y deja de depender del reloj del runner.

## Qué no hacer

- No actualizar los tres artefactos cada madrugada solo para satisfacer CI.
- No fijar una fecha constante en código.
- No eliminar `generated_on` ni cambiar el copy público sin necesidad.
- No relajar el check de valores reales de libros, artículos, herramientas o muestras.

## Archivos

- `scripts/build-human-site-stats.py`
- `tests/test-human-site-stats-date-stability.py`

No es necesario modificar los artefactos generados: precisamente deben seguir siendo válidos al día siguiente si sus estadísticas no cambiaron.

## Tests

La regresión cubre:

1. `--check` reutiliza una fecha versionada anterior;
2. `--date` explícito gana siempre;
3. `generated_on` inválido se rechaza.

Además, el propio paso existente de `content-index-check.yml` es el test de integración: debe pasar con los artefactos del 22/08 ejecutándose el 23/08.

## Criterios de aceptación

- `build-human-site-stats.py ... --check` pasa aunque el día actual sea posterior a `generated_on`, si las estadísticas no han cambiado.
- Un cambio real en las estadísticas sigue haciendo fallar el check.
- Una regeneración real sigue actualizando `generated_on` salvo que se proporcione `--date`.
- No se toca `main`, no hay deploy y la PR permanece DRAFT hasta revisar CI.
