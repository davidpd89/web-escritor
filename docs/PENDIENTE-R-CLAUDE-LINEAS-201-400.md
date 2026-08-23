# Auditoría Claude — líneas 201–400

Fecha: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente original del bloque: `claude pending.txt`, líneas 201–400 exactas.

## Reconciliación posterior

Este bloque se cerró originalmente sin usar líneas 401+. Después de completar secuencialmente todo el fichero hasta EOF 746, se revisaron contradicciones internas de la propia fuente.

La conclusión inicial de que `/las-manecillas-del-recuerdo/como-se-escribio/` constituía una deuda nueva independiente **no se sostiene al leer el resto del informe**.

---

## R.1 — `/las-manecillas-del-recuerdo/como-se-escribio/`

**Clasificación final: GATED EDITORIAL / NO DEUDA DE CÓDIGO ACTUAL.**

### Evidencia del bloque 201–400

La ruta no existe y tampoco hay builder/checker específico. El material histórico proponía un hub de proceso enlazado a notas reales del Cuaderno, con un umbral mínimo de contenido.

Aislando solo 201–400, eso podía parecer una decisión «en tierra de nadie».

### Evidencia posterior que resuelve la ambigüedad

La propia fuente aclara más adelante:

- línea 505: el hub no existe pero está **«Correctly GATED_CON_CONDICIÓN»**, porque necesita ≥4 notas reales del Cuaderno;
- línea 563: vuelve a indicar que `como-se-escribio-manecillas` no existe porque las precondiciones editoriales no se han cumplido y que su ausencia es **«legitimately still-pending editorial content, not an oversight»**;
- la misma fuente remite a `docs/CONTENT-PARITY-MANECILLAS-V1.md` como registro vigente de ese gate.

Por tanto, no debe crearse ahora:

- una landing vacía;
- un registry entry ficticio solo para «recordar» el pendiente;
- un builder sin contenido;
- enlaces deshabilitados o placeholders públicos;
- cuatro artículos artificiales para alcanzar el umbral.

### Contrato futuro que sí debe conservarse

Cuando existan ≥4 notas de proceso reales, publicables e indexables, entonces la activación debería:

1. usar el shell/registry V1 vigentes;
2. enlazar piezas reales mediante URLs/IDs canónicos;
3. incluir enlace contextual desde la ficha de Manecillas;
4. mantener enlaces `<a href>` rastreables;
5. entrar en sitemap/indexación solo cuando el contenido sea real;
6. usar `dateModified` real;
7. tener QA de enlaces, canonical, robots y grafo interno.

Hasta que cambie el gate editorial, **no hay implementación que hacer**.

---

## Hallazgos del bloque que ya tienen owner

### Protocolo de correcciones editoriales

**YA DETECTADO → #66 K.1**, coordinado con #57 D.1. El comentario ya trasladado a #66 conserva los requisitos de evidencia, fechas, nota pública y validación.

### `.github/workflows/update-dates.yml`

**YA DETECTADO → #54.**

### Popup / runtime global

**YA DETECTADO → #61 H.1.**

### `FAQPage` legacy

**YA DETECTADO → #66 K.2.**

### Deploy / DOI / readiness

**YA DETECTADO → #55 + #58 + #1/#74.**

---

## Corregido o no accionable

### `broken-links.yml`

**SUPERADO.** El workflow actual usa `fail: true` y `failIfEmpty: true`.

### Backlog de artículos y calendario editorial

**EDITORIAL / OUT OF SCOPE de código.** No generar páginas vacías ni publicar drafts automáticamente.

### Social / Metricool

**OUT OF SCOPE** del proyecto web.

### Bio/identidad

Decisión editorial, no hueco técnico autónomo de este bloque.

---

## Resultado final 201–400

**Deuda nueva independiente real: ninguna.**

- `/como-se-escribio/` → GATED editorial correctamente registrado por la arquitectura vigente;
- correcciones → #66/#57;
- `update-dates` → #54;
- runtime/popup → #61;
- FAQ → #66;
- deploy/DOI/readiness → #55/#58/#1/#74.

La PR asociada a este bloque debe conservarse solo como registro de auditoría o cerrarse; **no debe disparar implementación del hub antes de que existan las ≥4 notas reales exigidas por el gate**.

**Corte original respetado: línea 400. Reconciliación hecha únicamente después de completar secuencialmente el fichero hasta EOF 746.**
