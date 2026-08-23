# Pendiente T — Auditoría Claude líneas 1–200

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `claude pending.txt`, líneas 1–200 exactas.

## Regla de alcance

Se ha leído exactamente el bloque 1–200 y se ha contrastado contra:

- HEAD real de `implementacion-web-2026`;
- todas las PR abiertas antes de esta rama (#1 y #54–#76);
- código, workflows y configuración actuales;
- documentación histórica de Drive solo cuando era necesaria para entender el contrato original.

No se convierte una receta antigua en obligación solo porque exista en `CODIGO PROPUESTO 2026-08-15/`. Cada hallazgo se clasifica contra la implementación actual.

No tocar `main`, no desplegar producción y no activar auto-merge.

---

## T.1 — Agenda del autor: falta la integración interna «Añadir al calendario»

**Clasificación: DEUDA NUEVA / mejora funcional verificable.**

### Qué dice la fuente

Las líneas 59 y 69 marcan `build-event-calendars.py` como uno de los pocos scripts propuestos que no llegó a `scripts/` y cuyo efecto tampoco estaba confirmado como sustituido.

La documentación de integración conservada en Drive define un contrato concreto, distinto de la herramienta pública `/herramientas/eventos-ics/`:

- fuente de verdad: los `Event` JSON-LD de `eventos.html`;
- solo generar `.ics` para eventos futuros reales con `eventStatus = https://schema.org/EventScheduled`;
- salida canónica: `/assets/events/calendar/<fragmento-del-id>.ics`;
- la tarjeta visible del mismo evento ofrece «Añadir al calendario»;
- no duplicar fecha/hora en JS ni en una API externa;
- CI debe ejecutar `build-event-calendars.py --check` dentro del job de contenido existente, no abrir otro workflow;
- `--check` debe fallar si hay un `EventScheduled` sin `.ics`, si el `.ics` diverge del JSON-LD o si queda un `.ics` huérfano después de completar/cancelar/retirar un evento.

### Evidencia actual

En el HEAD auditado:

- `eventos.html` sí existe y usa `Event` JSON-LD como autoridad;
- los dos eventos visibles comprobados están correctamente marcados como `EventCompleted`;
- no existe `scripts/build-event-calendars.py`;
- no aparece infraestructura equivalente de generación automática de calendarios desde `eventos.html`;
- la herramienta pública `/herramientas/eventos-ics/` resuelve otro caso: un escritor genera su propio evento, no sincroniza la agenda oficial de David;
- actualmente no hay `EventScheduled` real que justifique inventar un evento para probar producción.

### Implementación correcta

Construir la infraestructura sin inventar contenido:

1. `scripts/build-event-calendars.py` debe parsear el JSON-LD de `eventos.html` y seleccionar únicamente `@type: Event` con `eventStatus = EventScheduled`.
2. El nombre del `.ics` debe derivarse de forma segura y determinista del fragmento del `@id` canónico.
3. El `.ics` debe representar al menos `UID`, `DTSTAMP`, `DTSTART`, `DTEND` cuando exista, `SUMMARY`, `DESCRIPTION`, `LOCATION` y `URL`, con escaping iCalendar correcto y soporte de fechas de día completo frente a datetimes con zona.
4. No copiar fechas a un segundo JSON ni hardcodearlas en JS: el JSON-LD sigue siendo la fuente.
5. `--check` no debe escribir y debe detectar: archivo ausente, contenido desincronizado y huérfanos.
6. Integrar el check en el workflow de contenido ya existente junto a sitemap/feed, evitando un workflow paralelo.
7. Añadir tests de fixture para:
   - un `EventCompleted` que no genera nada;
   - un `EventScheduled` de día completo;
   - un `EventScheduled` con hora/zona;
   - caracteres que requieran escaping;
   - `.ics` huérfano;
   - `@id` sin fragmento o fragmento inválido → error claro.
8. La acción visible «Añadir al calendario» debe aparecer únicamente cuando exista un `.ics` generado para ese mismo evento. No añadir botones a eventos pasados.
9. Hasta que exista un evento futuro real, el resultado correcto en producción puede ser **cero `.ics` y cero botones**, con tests verdes.

### Criterio de cierre

- builder determinista + `--check`;
- tests de fixtures en verde;
- CI de contenido wireado;
- ningún evento ficticio añadido;
- los eventos completados actuales siguen sin mostrar «Añadir al calendario»;
- cuando se añada un `EventScheduled` de fixture, se demuestra que el `.ics` y el enlace se sincronizan.

---

## T.2 — Reconciliar el presupuesto de rendimiento documentado con Lighthouse CI

**Clasificación: DEUDA NUEVA / inconsistencia de contrato y QA.**

### Qué dice la fuente

Las líneas 162–170 detectan una discrepancia reproducible entre `07_ARQUITECTURA_TECNICA_Y_CODIGO.md` y `lighthouserc.json`.

El documento de arquitectura define como **objetivos de laboratorio móvil**:

- rendimiento ≥ 90;
- LCP ≤ 2,5 s;
- CLS < 0,1;
- TBT < 200 ms;
- JavaScript propio inicial < 50 KiB comprimido como objetivo;
- imagen LCP dimensionada y preferiblemente < 200 KiB.

También establece que los Core Web Vitals reales, cuando existan, sustituyen a Lighthouse para decidir impacto de usuario.

El HEAD actual aplica en `lighthouserc.json`:

- performance `minScore: 0.85` → `warn`;
- LCP `maxNumericValue: 3500` → `warn`;
- CLS `0.1` → `error`;
- TBT `400` → `warn`.

Por tanto CLS coincide, pero performance/LCP/TBT permiten resultados peores que los objetivos documentados.

### Lo que NO debe hacerse

No cambiar 0.85→0.90, 3500→2500 y 400→200 a ciegas.

Un presupuesto puede ser:

- objetivo aspiracional;
- warning de regresión;
- gate bloqueante de release.

Mezclar esas tres cosas sin medir el HEAD convertiría CI en ruido o, al contrario, dejaría una falsa sensación de cumplimiento.

### Implementación correcta

1. Ejecutar Lighthouse CI sobre las URLs clave actuales con el número de runs ya definido y registrar medianas/dispersión reales.
2. Separar explícitamente:
   - **target editorial/performance**;
   - **warning de regresión en CI**;
   - **gate bloqueante**, si procede.
3. Decidir una sola autoridad documentada para esos valores. Si el presupuesto 2,5 s / 200 ms / 90 sigue vigente, acercar CI a él con evidencia y, si hace falta, por fases. Si se decide que el presupuesto era aspiracional, documentarlo como tal y justificar los umbrales CI actuales.
4. No rebajar accesibilidad/SEO/CLS para «compensar».
5. Añadir una regresión/config check que evite que documentación y `lighthouserc.json` vuelvan a divergir silenciosamente cuando ambos pretendan expresar el mismo contrato.
6. Coordinar con owners de rendimiento existentes sin duplicar scope:
   - runtime e imágenes → #61;
   - minificación medida → #70;
   - post-deploy/readiness → #58/#1;
   - esta deuda solo es autoridad de presupuesto/gates.
7. Si la medición demuestra que una URL concreta necesita una excepción temporal, la excepción debe ser explícita, fechada y ligada a una causa/owner; no ampliar el presupuesto global para ocultarla.

### Criterio de cierre

- evidencia Lighthouse del HEAD relevante;
- decisión explícita target vs warning vs gate;
- `lighthouserc.json` y documentación alineados;
- ninguna relajación silenciosa de otros gates;
- QA que impida drift futuro de la autoridad elegida.

---

## Hallazgos reutilizados — NO abrir deuda paralela

### Assets sin referenciar — líneas 4–17

**YA DETECTADO → #60.**

El snapshot de ~394 MiB de assets sin referencias sigue siendo útil como evidencia, pero #60 ya posee la herramienta de informe y la decisión expresa de no borrar nada hasta revisión humana. No crear otro auditor ni eliminar `assets/alicia_capitulo_*` automáticamente.

### BRAINSTORMING — líneas 18–40

**SUPERADO COMO BACKLOG / BANCO DE IDEAS.**

El propio fichero dice que no todo debe implementarse. Además, `BRAINSTORMING.md` ya fue saneado en Drive para que una idea no se convierta automáticamente en tarea. Rutas como `/publicar-un-libro/`, `/radar-literario/`, `/escritores/`, `/laboratorio/`, `/datos/`, `/ahora/`, `/preguntas/`, `/descubrir/` o el hub general `/recursos/` siguen siendo candidatos de investigación, no «código faltante comprometido» por este bloque.

No inventar hubs vacíos.

### Runtime JS/CSS — líneas 53, 58, 69, 131, 137, 148–166

**YA DETECTADO → #61 H.1.**

La ausencia literal de `split-runtime.py`, `split-runtime-css.py` o `optimize-critical-interactions.py` no obliga a reconstruir esos nombres históricos. #61 ya posee el contrato moderno de runtime por alcance. La estructura modular de `07` se declara además «futura opcional».

### `check-production-launch.py`

**YA DETECTADO / SUSTITUIDO → #58 + #1 + #74.**

El objetivo es evidencia real de release y smoke sobre staging/HEAD final, no preservar un filename antiguo.

### `check-runtime-scoping.py`

**YA DETECTADO → #61 H.1.**

No duplicar.

### `check-article-dates.py`

**YA DETECTADO → #57 D.1.**

No duplicar.

### `submit-indexnow.py`

**GATED / NO IMPLEMENTAR A CIEGAS.**

La propia integración propuesta exige comprobar primero si el dominio ya envía IndexNow mediante Cloudflare/CMS/Bing Webmaster Tools para evitar una segunda fuente duplicada. El repo actual no contiene una integración IndexNow propia. #76 ya registra esta cautela en el bloque Claude 401–600.

Hasta confirmar la integración externa real, no añadir key/workflow custom solo porque exista un prototipo en Drive.

### `validate-article-correction.py`

**YA DETECTADO → #66 K.1 + coordinación #75.**

El protocolo de evidencia/correcciones públicas ya tiene owner. No duplicar un validador solo por su nombre histórico.

### FAQPage — líneas 76–91 y 159–167

**YA DETECTADO → #66 K.2.**

Mantener FAQ visible y retirar únicamente schema legacy según el contrato de esa PR.

### Newsletter honeypot / rate limit / DOI — líneas 114–137, 151–153, 168

**YA DETECTADO → #55.**

No crear un segundo Worker ni un segundo contrato de payload.

### Analítica — líneas 157 y contexto

**YA DETECTADO → #63.**

La taxonomía global decide el naming actual; no restaurar literalmente `buy_open_[book]`, etc., sin pasar por ese owner.

### Baseline / compatibilidad — líneas 162, 169

**YA DETECTADO → #66 K.3.**

La carencia real es compatibilidad práctica/cross-engine; no confundir `pa11y-baseline.yml` con Web Platform Baseline. #66 ya posee el contrato Chromium/Firefox/WebKit y la compatibilidad profunda.

### Arquitectura genérica `DP_BOOKS` / buy-dialog Manecillas — línea 171

**SUPERADA/OPCIONAL.**

Manecillas tiene un flujo honesto específico sin URLs comerciales falsas y `07` etiqueta la extracción modular como futura. No reconstruir un catálogo genérico solo para coincidir con un prototipo antiguo.

### Pagefind / búsqueda interna — línea 103 y documento 07

**GATED / REEVALUAR, NO DEUDA DE ESTE BLOQUE.**

El sitio ya superó el umbral aproximado de 20 piezas que justificaba reevaluar búsqueda, pero el propio documento ofrece varias opciones y dice que Pagefind no es requisito. Esto necesita una decisión de UX/información propia, no una implementación oportunista dentro de esta auditoría.

### Datos editoriales, legales y externos — líneas 175–199

**GATED / NO CÓDIGO AUTÓNOMO.**

Compra real, formato/retailers, permiso de portada, corrección física de cubierta, citas de prensa, agenda futura, revisión jurídica de la base legal y Search Console requieren datos o decisión externa. No inventar hechos para cerrar un check.

Noveris/canon ya tiene owner en #66 K.4.

Metricool/publicación social permanece `OUT OF SCOPE` del proyecto web.

---

## Resultado del bloque 1–200

Deuda nueva independiente real:

- **T.1 — agenda oficial: generación/sincronización `.ics` desde `EventScheduled` canónico.**
- **T.2 — reconciliar objetivos de rendimiento con Lighthouse CI mediante medición y una autoridad única.**

Todo lo demás queda absorbido, superado, gated o fuera de alcance según lo indicado arriba.

**STOP exacto: línea 200. No usar líneas 201+ para decidir este bloque.**
