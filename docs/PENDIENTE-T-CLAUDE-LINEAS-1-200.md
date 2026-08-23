# Pendiente T — Auditoría Claude líneas 1–200

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente primaria: `claude pending.txt`, líneas 1–200 exactas.

## Regla de alcance

Este cierre usa únicamente el bloque 1–200 para la auditoría del TXT. La documentación histórica se consulta solo para reconstruir el contrato funcional de nombres antiguos; no sustituye al código vivo.

Autoridad: HEAD de `implementacion-web-2026` + PR abiertas + código/builders/tests/workflows reales.

No tocar `main`, no desplegar producción y no activar auto-merge.

---

## T.1 — Agenda oficial / `.ics`

**Clasificación: PARCIAL en #77 — infraestructura implementada; activación pública GATED.**

### Problema real

Las líneas 59/69 mencionan `build-event-calendars.py`. El nombre no era la exigencia, pero la función sí seguía faltando en HEAD.

La especificación histórica de agenda distingue dos capas:

1. **infraestructura interna**: leer los `Event` JSON-LD canónicos de `eventos.html`, generar `.ics` solo para `EventScheduled` y comprobar sincronía/huérfanos;
2. **activación pública**: publicar `.ics` y el enlace «Añadir al calendario» solo cuando exista un evento futuro real y confirmado.

La herramienta pública `/herramientas/eventos-ics/` no sustituye esa capa interna: sirve para que cualquier escritor genere manualmente HTML + JSON-LD + ICS en el navegador.

En el HEAD auditado `eventos.html` solo contiene `EventCompleted`, por lo que **0 `.ics` y 0 botones públicos sigue siendo el resultado correcto hoy**. Eso no impide tener preparada y testeada la infraestructura.

### Implementación añadida a #77

- `scripts/build-event-calendars.py`
  - fuente única: JSON-LD de `eventos.html`;
  - solo exporta `EventScheduled`;
  - ignora eventos completados/cancelados;
  - DATE → evento de día completo;
  - DATE-TIME exige offset/Z y se normaliza a UTC;
  - UID determinista desde `@id`;
  - DTSTAMP estable desde `dateModified`/`startDate`;
  - escaping RFC 5545;
  - CRLF y plegado de líneas UTF-8 a 75 octetos;
  - salida `/assets/events/calendar/<fragmento>.ics`;
  - `--check` detecta archivos ausentes, desactualizados y huérfanos;
  - exige que todo `EventScheduled` tenga el enlace visible canónico con `data-calendar-download`;
  - cero dependencias externas.
- `tests/test-event-calendars.py`
  - datetime con offset;
  - día completo y DTEND exclusivo;
  - eventos completados ignorados;
  - enlace visible obligatorio para `EventScheduled`;
  - missing/stale/orphan;
  - rechazo de datetime sin offset;
  - límite físico de 75 octetos.
- `.github/workflows/content-index-check.yml`
  - ejecuta `build-event-calendars.py --check`;
  - ejecuta la suite específica.

### Gates que permanecen

No se añade ningún evento ficticio. El primer `EventScheduled` real exige datos confirmados y QA humano de importación en Apple Calendar/iOS, Google Calendar/Android y Outlook, además de hora, ubicación, tildes, teclado/táctil.

La analítica `event_calendar_open`, si se activa, debe coordinarse con la taxonomía canónica de #63 y medir solo la apertura del recurso, nunca afirmar que el usuario añadió el evento.

### Criterio de cierre T.1

- CI verde con builder y tests;
- ningún `.ics` falso para los `EventCompleted` actuales;
- al existir el primer evento real: JSON-LD `EventScheduled`, enlace visible y `.ics` derivado de la misma autoridad.

---

## T.2 — Presupuesto Lighthouse vs arquitectura documentada

**Clasificación: DEUDA NUEVA / GATED POR DECISIÓN DE CONTRATO. Owner: #77.**

### Evidencia reproducible

Las líneas 162–170 señalan una discrepancia real. `07_ARQUITECTURA_TECNICA_Y_CODIGO.md` documenta como objetivos móviles:

- performance ≥ 90;
- LCP ≤ 2,5 s;
- CLS < 0,1;
- TBT < 200 ms.

El `lighthouserc.json` del HEAD aplica:

- performance `0.85` → `warn`;
- LCP `3500 ms` → `warn`;
- CLS `0.1` → `error`;
- TBT `400 ms` → `warn`.

CLS está alineado; performance, LCP y TBT permiten resultados peores que los objetivos documentados.

### Por qué no se cambia a ciegas

El documento denomina esas cifras **objetivos**. Eso no prueba por sí solo que deban convertirse en gates bloqueantes de CI. Endurecer valores sin medir el HEAD podría transformar un target editorial en un bloqueo ruidoso y sin autoridad.

### Contrato de cierre

1. Obtener evidencia Lighthouse reproducible sobre las URLs clave y los runs configurados.
2. Separar explícitamente `target`, `warning` y `gate`.
3. Decidir una única autoridad para esos niveles.
4. Alinear `lighthouserc.json` y documentación con esa decisión.
5. Añadir protección contra drift si ambos artefactos expresan el mismo contrato.
6. No relajar CLS, accesibilidad, SEO ni otros gates para compensar.
7. Mantener CWV reales, cuando existan, por encima de una medición de laboratorio aislada para evaluar experiencia real.

Coordinación: runtime/imágenes → #61; medición/minificación → #70; post-deploy/release → #58/#1. T.2 no duplica esos scopes.

---

## Hallazgos absorbidos o no accionables

- Assets sin referenciar/peso → **YA DETECTADO #60**. No borrar automáticamente.
- BRAINSTORMING → **SUPERADO COMO BACKLOG**. Es banco de ideas, no cola de ejecución.
- Runtime/scoping y nombres históricos `split-runtime*` / `check-runtime-scoping.py` → **YA DETECTADO #61 H.1**.
- `check-production-launch.py` → **YA DETECTADO / FUNCIÓN ABSORBIDA #58 + #1**. Importa el smoke/readiness real, no el filename.
- `check-article-dates.py` → **YA DETECTADO #57**.
- `submit-indexnow.py` → **GATED**. La propia propuesta exige verificar antes si Cloudflare/Bing ya lo resuelve; no se crea una integración paralela sin evidencia.
- `validate-article-correction.py` → **YA DETECTADO #66 K.1 + #57** para el contrato verificado de evidencia, fechas y corrección pública. No se infiere un sistema más amplio solo por el nombre histórico.
- FAQPage legacy → **YA DETECTADO #66 K.2**.
- Newsletter honeypot/rate limit/DOI → **YA DETECTADO #55**.
- Analítica → **YA DETECTADO #63**.
- Baseline/compatibilidad → **YA DETECTADO #66 K.3**. El contrato útil es compatibilidad práctica/cross-engine; los datos Baseline pueden ser señal adicional, no un owner paralelo.
- `DP_BOOKS` / configuración genérica de compras → **SUPERADO/OPCIONAL** mientras no exista necesidad real distinta del flujo actual.
- Pagefind/búsqueda interna → **GATED / REEVALUAR POR ESCALA Y UX**, no defecto actual demostrado.
- Datos comerciales, legales, citas, eventos futuros y Search Console → **GATED** por hechos/decisiones externas.
- Noveris/canon → **YA DETECTADO #66 K.4**.
- Metricool/publicación social → **OUT OF SCOPE**.

---

## Cierre del bloque 1–200

Deuda independiente demostrada:

- **T.1**: infraestructura de calendarios del sitio. Implementada en esta misma PR; activación pública sigue gated hasta un evento real.
- **T.2**: incoherencia entre objetivos de rendimiento documentados y límites de Lighthouse CI. Sigue abierta hasta medir y fijar la autoridad `target/warning/gate`.

No se justifica otra PR para este bloque. #77 es el owner único de T.1/T.2.

**Corte respetado: línea 200. No se necesita leer la 201 para este cierre.**
