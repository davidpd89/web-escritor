# Pendiente Q — Auditoría GPT líneas 1801–EOF

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `pendiente funcionalidad gpt.txt`, líneas 1801–1969. **La fuente termina en la línea 1969; no existen líneas 1970–2000.**

## Regla de alcance

Este documento registra únicamente deuda que sigue siendo real después de contrastar el TXT con repo, tests, Drive ya saneado y todas las PR abiertas. No duplica trabajo que ya tenga propietario.

No tocar `main`, no desplegar producción y no activar auto-merge desde esta rama.

---

## 1. Documento 63 — continuación del export open-source

**Clasificación: YA DETECTADO — #73 P.2.**

Las líneas 1801–1828 continúan el documento 63 y no justifican una PR nueva para el export.

- **63-A** — cierre de dependencias runtime: ya forma parte de #73 P.2.
- **63-B** — SilabaJS / terceros / licencia: ya forma parte de #73 P.2.
- **63-C** — empaquetar tests reproducibles de cada herramienta cuando existan: requisito adicional del mismo P.2, comunicado en #73.

Evidencia actual:

- `scripts/build-open-source-export.py` solo copia los elementos declarados en `t.files`;
- `data/open-source-tools.json` no declara tests por herramienta;
- sí existen tests funcionales de varias herramientas exportables (`test-legibilidad.mjs`, `test-pov-distribucion.mjs`, `test-dialogo.mjs`, `test-repeticiones.mjs`, `test-variedad-lexica.mjs`, etc.);
- `tests/test-build-open-source-export.py` valida el proceso de staging, pero no empaqueta ni ejecuta desde el staging los tests propios de cada herramienta.

Criterio de cierre añadido a #73: el paquete debe poder incluir tests reproducibles y sus dependencias mínimas, y ejecutarlos aislado del repo completo. `export:false` y `license:null` permanecen gated hasta decisión humana.

---

## 2. Documento 64 — criterio útil, fotografía operativa obsoleta

**Clasificación: DEUDA NUEVA Q.1 — IMPLEMENTADA EN ESTA PR.**

El criterio metodológico del documento 64 sigue siendo válido: una ruta o un fichero parecido no demuestra que el contrato esté implementado.

La fotografía operativa de las líneas 1830–1883 ya estaba obsoleta: hablaba de ocho PR (#54–#60 y #1). Antes de abrir #74 se refrescaron #1 y #54–#73; la propia apertura de #74 demuestra por qué una lista manual nunca puede ser la autoridad viva.

El Google Doc 64 de Drive ya fue saneado el 23/08 y ahora registra la auditoría **completa hasta EOF 1969**, incluyendo #74 y la reutilización de #73/#61/#58.

### Evidencia reproducible de la deuda original

El antiguo `docs/WEB-2026-HANDOFF-REMAINING-WORK.md` se presentaba como:

> `HANDOFF AUTORITATIVO DE TRABAJO PENDIENTE`

pero contenía:

- snapshot `e9207278747646b76a0f22ebf3703b3e19c0c3db`;
- «Ahora mismo, ninguno» como trabajo activo;
- «La única PR viva es la #1»;
- un orden de ejecución construido para un estado anterior.

### Q.1 — implementación realizada

Se ha cerrado sin destruir historia:

1. el blob antiguo completo (`9f3944c9ea0c872c95c8b35918488ae4105788eb`) se conserva **sin modificar** en `docs/archive/WEB-2026-HANDOFF-REMAINING-WORK-2026-08-22.md`;
2. `docs/WEB-2026-HANDOFF-REMAINING-WORK.md` se sustituye por un handoff corto y estable;
3. autoridad operativa = HEAD actual de `implementacion-web-2026` + todas las PR abiertas con esa base + CI/QA del SHA concreto;
4. los SHA, listados de PR y «siguiente orden» escritos quedan definidos como snapshots históricos;
5. toda tarea antigua debe reclasificarse `HECHO / YA DETECTADO / DEUDA NUEVA / PARCIAL / GATED / SUPERADO / OUT OF SCOPE` antes de programar;
6. si una PR ya posee la deuda, se reutiliza y no se duplica;
7. Metricool/publicación social queda `OUT OF SCOPE` del proyecto web;
8. el nuevo handoff no mantiene una cola manual de PR que haya que editar cada vez que cambia GitHub.

Además, el body de la PR #1 se actualizó para que tampoco funcione como tracker estático: exige refrescar HEAD + PR abiertas + CI/QA antes de cualquier release y conserva `DRAFT / DO NOT MERGE / NO PRODUCCIÓN`.

---

## 3. MASTER-00 — estado histórico

**Clasificación actual: SUPERADO / CORREGIDO EN DRIVE.**

Las líneas 1885–1909 eran correctas respecto a la copia antigua: `00_INDICE_Y_DECISIONES.md` mezclaba decisiones con un snapshot del 16/08.

Durante esta misma auditoría maestra se actualizó el fichero en Drive, conservando su ID, para separar:

- decisiones conceptuales vigentes;
- snapshot histórico;
- autoridad operativa actual.

Ya no debe abrirse una PR ni recrearse otro tracker por esta observación.

---

## 4. MASTER-16 — §§50–51

**Clasificación actual: PARCIAL / YA ASIGNADO — #61 H.1.**

Las líneas 1911–1953 detectaban una ambigüedad real: el documento histórico exigía nombres y scripts que no existen actualmente (`split-runtime.py`, `split-runtime-css.py`, etc.) sin aclarar si seguían siendo arquitectura vigente.

`16_IMPLEMENTACION_CODIGO_LISTA.md` ya fue saneado en Drive el 23/08:

- §50 queda absorbido parcialmente por #61 H.1; no se deben reconstruir nombres/scripts históricos por fidelidad documental;
- §51 queda PARCIAL y se coordina con #61: el contrato que importa es decidir el CSS del modal de Samuel por alcance con evidencia, no cumplir literalmente el antiguo script ni una cifra arbitraria de bytes.

Se dejó comentario de coordinación en #61 para que §51 no quede huérfano.

No abrir deuda paralela.

---

## 5. Blocker de release

**Clasificación: YA DETECTADO — #58 / #1.**

Las líneas 1871–1883 no descubren un segundo blocker:

- smoke post-deploy y `build-public-dist.py --check-contents` → #58;
- #1 sigue DRAFT / DO NOT MERGE;
- ningún informe estático anterior equivale a certificación final de producción.

No duplicar.

---

## Resultado final de la fuente

La fuente termina en la línea 1969. No hay un bloque posterior 1970–2000 que auditar.

Deuda nueva independiente real del tramo:

- **Q.1 — handoff vivo:** IMPLEMENTADA en #74, manteniendo el snapshot antiguo íntegro en `docs/archive/`.

Reutilizado sin duplicar:

- 63-A / 63-B / 63-C → #73 P.2;
- runtime/CSS §§50–51 → #61 H.1;
- post-deploy → #58.

Superado durante la auditoría documental:

- MASTER-00 en Drive;
- ambigüedad documental de MASTER-16, reencaminada a owners reales;
- estado operativo del Google Doc 64, corregido mediante addendum 23/08 y actualizado hasta EOF;
- body obsoleto de #1, ahora basado en autoridad viva.

**EOF exacto: línea 1969.**
