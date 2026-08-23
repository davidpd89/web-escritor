# Pendiente T — Auditoría Claude líneas 1–200

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente primaria del bloque: `claude pending.txt`, líneas 1–200 exactas.

## Regla de alcance

El bloque se auditó inicialmente sin leer 201+ y se contrastó contra HEAD, PR abiertas, código/workflows actuales y documentación histórica solo cuando era necesaria para entender un contrato.

Después de completar secuencialmente **todo** `claude pending.txt` hasta su EOF real (línea 746), se hizo una reconciliación entre bloques para corregir contradicciones internas de la propia fuente. Esa reconciliación no cambia qué se leyó para decidir originalmente 1–200; evita conservar como deuda una sospecha que el propio fichero aclara más adelante.

No tocar `main`, no desplegar producción y no activar auto-merge.

---

## T.1 — Agenda oficial / «Añadir al calendario»

**Clasificación final: GATED / NO DEUDA DE CÓDIGO ACTUAL.**

### Por qué apareció como sospecha en 1–200

Las líneas 59 y 69 mencionan `build-event-calendars.py` entre los scripts propuestos que no llegaron a `scripts/` y cuyo efecto debía comprobarse antes de decidir si había backlog real.

La propuesta histórica describía una integración razonable:

- fuente de verdad en los `Event` JSON-LD de `eventos.html`;
- `.ics` solo para eventos futuros reales con `EventScheduled`;
- enlace visible «Añadir al calendario» únicamente para esos eventos;
- ningún duplicado manual de fechas;
- comprobación de sincronía cuando la funcionalidad esté activa.

En el HEAD auditado no existe `build-event-calendars.py` y los eventos reales comprobados están en `EventCompleted`.

### Reconciliación al llegar a 401–600

La propia fuente resuelve la ambigüedad más adelante:

- línea 461: «add-to-calendar .ics» está **correctamente no activado**, porque su gate exige un `EventScheduled` real;
- línea 493: vuelve a clasificar «add-to-calendar» como **correctamente no integrado pendiente de un evento futuro real**, explícitamente «not a code gap».

Por tanto, construir ahora un builder sin ningún evento futuro real sería convertir una receta histórica en infraestructura prematura.

### Contrato que debe conservarse para el futuro

Cuando exista el primer `EventScheduled` real, entonces sí habrá que decidir/implementar una solución reproducible. El contrato deseable queda registrado para no perderlo:

1. derivar el `.ics` de la autoridad canónica del evento, no copiar fechas a otro sistema;
2. no mostrar enlace en `EventCompleted`;
3. salida determinista y con escaping RFC 5545 correcto;
4. detectar `.ics` desincronizados o huérfanos si se adopta generación estática;
5. tests de día completo, datetime/zona, escaping y retirada/cancelación;
6. ningún evento ficticio para satisfacer CI.

Hasta entonces: **cero `.ics` y cero botones es el estado correcto**.

No abrir/implementar una PR independiente por T.1 antes de que cambie ese gate editorial.

---

## T.2 — Reconciliar el presupuesto de rendimiento documentado con Lighthouse CI

**Clasificación final: DEUDA NUEVA / inconsistencia de contrato y QA.**

### Evidencia

Las líneas 162–170 detectan una discrepancia reproducible entre `07_ARQUITECTURA_TECNICA_Y_CODIGO.md` y `lighthouserc.json`.

La arquitectura documenta como objetivos móviles:

- rendimiento ≥ 90;
- LCP ≤ 2,5 s;
- CLS < 0,1;
- TBT < 200 ms;
- JavaScript propio inicial < 50 KiB comprimido como objetivo;
- imagen LCP dimensionada y preferiblemente < 200 KiB.

El HEAD actual aplica:

- performance `minScore: 0.85` → `warn`;
- LCP `maxNumericValue: 3500` → `warn`;
- CLS `0.1` → `error`;
- TBT `400` → `warn`.

CLS coincide; performance, LCP y TBT permiten resultados peores que los objetivos documentados.

### Lo que NO debe hacerse

No cambiar 0.85→0.90, 3500→2500 y 400→200 a ciegas.

Hay que distinguir:

- target aspiracional/editorial;
- warning de regresión;
- gate bloqueante.

Además, los CWV reales, cuando existan, tienen más valor para impacto de usuario que una única ejecución de laboratorio.

### Implementación correcta

1. Ejecutar Lighthouse CI sobre las URLs clave actuales con los runs configurados y conservar evidencia reproducible.
2. Medir medianas/dispersión, no reaccionar a una sola ejecución ruidosa.
3. Decidir y documentar una sola autoridad para `target / warning / gate`.
4. Si 90 / 2,5 s / 200 ms siguen siendo objetivos vigentes, acercar CI a ellos con evidencia y, si hace falta, por fases.
5. Si eran aspiracionales, declararlo expresamente y justificar los límites CI actuales.
6. No relajar CLS, accesibilidad, SEO u otros gates para compensar.
7. Añadir una comprobación que evite drift silencioso entre documentación y configuración cuando ambas pretendan expresar el mismo contrato.
8. Las excepciones temporales deben ser explícitas, fechadas y con causa/owner.

### Coordinación

- runtime e imágenes → #61;
- minificación/medición → #70;
- post-deploy/readiness → #58/#1;
- T.2 solo posee la autoridad de presupuesto/gates, no esos scopes.

### Criterio de cierre

- evidencia Lighthouse del HEAD relevante;
- decisión explícita target vs warning vs gate;
- `lighthouserc.json` y documentación alineados;
- ninguna relajación silenciosa;
- QA que impida drift futuro.

---

## Hallazgos reutilizados — NO abrir deuda paralela

### Assets sin referenciar — líneas 4–17

**YA DETECTADO → #60.**

El snapshot de ~394 MiB sigue siendo evidencia útil, pero #60 ya posee el informe y la decisión de no borrar nada sin revisión humana.

### BRAINSTORMING — líneas 18–40

**SUPERADO COMO BACKLOG / BANCO DE IDEAS.**

El propio documento dice que no todo debe implementarse. No crear hubs/rutas vacías solo porque una idea exista.

### Runtime JS/CSS — líneas 53, 58, 69, 131, 137, 148–166

**YA DETECTADO → #61 H.1.**

No reconstruir literalmente `split-runtime.py`, `split-runtime-css.py` o `optimize-critical-interactions.py`; importa el contrato moderno de scoping.

### `check-production-launch.py`

**YA DETECTADO / SUSTITUIDO → #58 + #1 + #74.**

El objetivo es evidencia real de release y smoke, no preservar un filename histórico.

### `check-runtime-scoping.py`

**YA DETECTADO → #61 H.1.**

### `check-article-dates.py`

**YA DETECTADO → #57 D.1.**

### `submit-indexnow.py`

**GATED / NO IMPLEMENTAR A CIEGAS.**

La propia propuesta exige comprobar primero si Cloudflare/Bing ya resuelve IndexNow. El bloque 401–600 refuerza esa cautela.

### `validate-article-correction.py`

**YA DETECTADO → #66 K.1 + #75.**

### FAQPage

**YA DETECTADO → #66 K.2.**

### Newsletter honeypot / rate limit / DOI

**YA DETECTADO → #55.**

### Analítica

**YA DETECTADO → #63.**

No restaurar literalmente una nomenclatura histórica fuera de la taxonomía canónica.

### Baseline / compatibilidad

**YA DETECTADO → #66 K.3.**

La carencia útil es compatibilidad práctica/cross-engine, no un checker por nombre.

### Arquitectura genérica `DP_BOOKS` / buy-dialog Manecillas

**SUPERADA/OPCIONAL.**

Manecillas ya evita destinos comerciales falsos mediante su flujo específico; no introducir una abstracción genérica sin necesidad real.

### Pagefind / búsqueda interna

**GATED / REEVALUAR.**

Puede merecer una decisión de UX por volumen, pero no es deuda automática de este bloque.

### Datos editoriales, legales y externos

**GATED / NO CÓDIGO AUTÓNOMO.**

Compra real, retailers, portada, revisión jurídica, citas de prensa, eventos futuros y Search Console dependen de hechos/decisiones externas.

Noveris/canon → #66 K.4.  
Metricool/publicación social → `OUT OF SCOPE`.

---

## Resultado final del bloque 1–200 tras reconciliar el fichero completo

Deuda nueva independiente real:

- **T.2 — reconciliar objetivos de rendimiento con Lighthouse CI mediante medición y una autoridad única.**

Reclasificado tras evidencia posterior de la propia fuente:

- **T.1 — agenda `.ics`: GATED hasta existir un `EventScheduled` real; no es deuda de código actual.**

Todo lo demás queda absorbido, superado, gated o fuera de alcance según lo indicado arriba.

**Corte original respetado: línea 200. Reconciliación posterior hecha únicamente después de completar secuencialmente el fichero hasta EOF 746.**
