# C.1 · Calendario editorial ligado al lanzamiento de Las manecillas del recuerdo

Fecha de reconstrucción: 2026-08-29  
Idea original: crear una secuencia editorial pre/post lanzamiento de *Las manecillas del recuerdo*.  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.

## Veredicto

#135 concluyó que el problema no era «inventar otro calendario»: el proyecto ya tenía autoridades, materiales y gates de lanzamiento. La tarea correcta era ejecutar esas autoridades y mantener hechos editoriales consistentes.

La matriz intermedia llegó a marcar C.1 como `IMPLEMENTAR`; esa contradicción debe conservarse porque explica el refinamiento posterior. La autoridad final la devuelve a `ALREADY_COVERED`: no duplicar planificación técnica existente.

## Hipótesis original

`IDEAS-MEJORA-WEB-2026-08-27.md` proponía una secuencia de Cuaderno —adelantos, proceso creativo, inspiración— ligada a la publicación de Manecillas con Monza Ediciones en septiembre de 2026.

El valor pretendido era coordinar web, contenido y lanzamiento alrededor de una fecha real, no publicar artículos genéricos por calendario SEO.

## Cronología en #135

### Primera revisión → `ALREADY_COVERED`

La revisión 108/108 detectó que el lanzamiento ya tenía gate/runbooks y cerró:

> ejecutar la autoridad existente el 03/09; no crear un segundo calendario.

### Matriz intermedia → `IMPLEMENTAR`

La matriz posterior formuló trabajo útil de esta forma:

> calendario pre/post lanzamiento basado en hechos disponibles y fechas reales; separar campaña editorial de actualización factual del sitio.

Esta formulación es válida como **contenido del runbook**, pero no demuestra que falte una segunda infraestructura.

### Autoridad final → `ALREADY_COVERED`

`PR135-FINAL-AUTHORITY-2026-08-28.md` cerró:

> «Lanzamiento de Manecillas ya tiene estado/runbooks. Ejecutar y actualizar hechos; no duplicar otro calendario técnico.»

### Revalidación independiente

La falsación final mantuvo C.1–C.10. No reabrió C.1.

Secuencia:

```text
idea: crear calendario
→ repo/proyecto ya tiene planificación y gates
→ ALREADY_COVERED
→ matriz expresa acciones editoriales concretas como IMPLEMENTAR
→ autoridad final aclara: ejecutar autoridad existente, no duplicarla
→ revalidación mantiene
```

## Evidencia del proyecto conservada

`docs/CONTENT-PARITY-MANECILLAS-V1.md` documenta una autoridad factual/editorial madura:

- editorial: Monza Ediciones;
- fecha de publicación: 2026-09-03;
- ISBN: 979-8-90514-935-1;
- 272 páginas;
- PVP editorial: 16 €;
- formato: tapa blanda;
- `purchaseUrl` nulo mientras no exista destino verificado;
- ficha pública y fragmentos publicados;
- borradores de proceso `READY_PARA_PUBLICAR`, pero no activados automáticamente;
- hub «Cómo se escribió» gated hasta tener al menos cuatro notas reales del Cuaderno;
- guía de club gated hasta después del lanzamiento/activación real;
- press assets/high-res gated por derechos/clearance;
- assets sociales temporales solo desde campaña/calendario correspondiente.

Esto explica por qué C.1 no necesita otro sistema: ya existe separación explícita entre publicado, ready, gated, descartado y material interno.

## Regla fundamental: campaña ≠ verdad factual

#135 insiste en separar:

### Actualización factual del sitio

Hechos como fecha de publicación, editorial, ISBN, formato, páginas, PVP, disponibilidad comercial, retailers y eventos solo cambian cuando una autoridad real los confirma.

### Campaña editorial

Piezas como proceso de escritura, inspiración, adelantos, newsletter, posts sociales, materiales de club, prensa y «detrás del libro» pueden programarse, pero no deben alterar hechos ni activar URLs gated por sí solas.

## Gates preservados

### Compra

PVP editorial ≠ oferta comercial. Mientras `purchaseUrl` sea `null`, no inventar Amazon/retailer/stock/Offer.

### «Cómo se escribió»

No activar el hub solo porque exista un fixture. El contrato documentado exige masa editorial real antes de hacerlo público.

### Club de lectura

Material preparado no equivale a publicado. Mantener gate temporal/producto.

### Prensa/high-res

No distribuir assets sin clearance de derechos.

### Social temporal

Un creativo «ya disponible» no debe contaminar páginas evergreen antes de que el estado editorial lo permita.

## Qué podría contener el calendario, sin crear una segunda autoridad

Cuando se ejecute la campaña, cada entrada debería referenciar una fuente real y un estado:

```text
fecha
canal
pieza
source/canonical
status = DRAFT | APPROVED | SCHEDULED | PUBLISHED | CANCELLED
rightsGate
factDependencies
owner
```

Esto puede vivir en la autoridad de campaña ya existente. C.1 no autoriza otro JSON si ya existe un mecanismo equivalente.

## Relación con C.2

C.2 «detrás del libro» es un tipo de contenido potencial. C.1 es coordinación temporal. No fusionar ambos IDs.

## Relación con A.4

Una publicación programada no autoriza a falsear `datePublished/dateModified`. Lifecycle/frescura pertenece a A.4.

## Relación con H/email y O/social

Newsletter/social son canales de distribución. C.1 no redefine su consentimiento, tracking o arquitectura.

## Riesgos que #135 evita

- crear un segundo calendario divergente;
- publicar por obligación aunque no haya material de calidad;
- convertir prelaunch copy en copy evergreen;
- activar una URL gated porque «toca en calendario»;
- inventar retailer o disponibilidad;
- confundir asset preparado con asset autorizado;
- cambiar fechas para aparentar actualidad;
- mezclar spoilers/material privado en piezas públicas.

## Revalidación actual

A fecha 2026-08-29, el lanzamiento del 3 de septiembre de 2026 aún es futuro. Esta PR documental **no afirma que las acciones externas estén ejecutadas**.

El repo sigue mostrando una arquitectura de paridad/gating suficiente para sostener la conclusión histórica. Cualquier estado `CONFIGURED_LIVE` o `VERIFIED_E2E` debe requerir evidencia cuando llegue el momento; Git no prueba envíos, publicaciones sociales o configuración de cuentas.

## Pasadas posteriores revisadas

Cuarta–duodécima: no cambian C.1; investigan otras capacidades.  
Decimotercera–decimoquinta: no convierten C.1 en una nueva infraestructura.  
Casos/evidencia, fuentes adicionales, repos evaluados y blueprints: sin override específico adicional para C.1.

## Trazabilidad

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `ALREADY_COVERED`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR` intermedio y separación campaña/facts;
- `docs/CONTENT-PARITY-MANECILLAS-V1.md` — evidencia de gates/materiales/autoridad factual;
- `data/web-improvement-decisions-2026-08-28.json` — final machine-readable;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — `ALREADY_COVERED` final;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — mantenida.

## Definition of Done de la reconstrucción

- [x] hipótesis original;
- [x] `ALREADY_COVERED` inicial;
- [x] `IMPLEMENTAR` intermedio preservado;
- [x] reconciliación de la contradicción;
- [x] gates de compra, proceso, club, prensa y social preservados;
- [x] separación campaña ↔ hechos;
- [x] autoridad final y revalidación;
- [x] no se crea segundo calendario.

## Recomendación para Clara/Claude

**No construir C.1 desde cero.** Revisar las autoridades de lanzamiento vigentes, ejecutar únicamente lo que corresponda a la fecha/estado real y actualizar hechos desde sus fuentes. Si falta una pieza operativa concreta, extender el runbook propietario en lugar de crear una planificación paralela.