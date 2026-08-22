# Pendiente L — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 801–1000

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Alcance estricto: líneas 801–1000. No reabrir conclusiones intermedias que el propio documento corrige dentro de este mismo tramo, no duplicar PR abiertas y no mezclar tareas de Metricool/redes sociales con el proyecto web.

## 1. Lectura correcta del tramo

Las líneas 801–866 son una fotografía intermedia. El propio fichero la corrige desde la línea 871 en adelante después de integrar trabajo anterior y volver a auditar 29–31. Para esta ronda manda la conclusión posterior del mismo bloque, contrastada de nuevo contra el HEAD actual.

Por tanto:

- el antiguo email visible `samuelentremundos@gmail.com` **ya no aparece en el repo actual**: no reabrir ese bug;
- la deriva de radios 4/6/8 frente a un redline anterior queda **SUPERADA como deuda de esta ronda**, porque la auditoría posterior del propio fichero declara el documento 29 cubierto y no conserva ese punto como pendiente;
- la antigua referencia a PR #51/#52 abiertas es histórica: no utilizarla como estado actual;
- `data/content-registry.json` y `relatedIds` sí siguen siendo relevantes, pero la consolidación del relationship graph ya está registrada como deuda conocida en auditorías anteriores: **no duplicar**.

## 2. Estado real comprobado

### Documento 29 — COMPONENT REDLINES V1

**Clasificación: HECHO / SUPERADO.**

El sistema actual usa tokens V1, controles de 44/48 px, foco visible, responsive, reduced-motion y shell V1. `assets/v1-tokens.css` mantiene `--radius-control:4px`, `--radius-input:6px`, `--radius-special:8px`, pero dentro de este tramo la conclusión posterior del propio documento ya no conserva la discrepancia como deuda nueva.

No abrir trabajo para “volver” automáticamente a 0/2/4 ni a otra tabla antigua sin una autoridad posterior explícita.

### Documento 30 — MEDIA + VIDEO PRODUCTION SYSTEM V1

**Clasificación: PARCIAL.**

Hecho:

- hay uso real de `<picture>` y formatos modernos en superficies importantes;
- la Home usa AVIF para la fotografía del autor con WebP de fallback;
- hay tamaños WebP específicos para la cubierta de Manecillas;
- no existe autoplay decorativo ni infraestructura de vídeo vacía obligatoria.

Ya detectado:

- `media-manifest` / derechos / procedencia / focal points / safe areas / roles / créditos sigue siendo deuda conocida de gobernanza; no duplicar aquí;
- geometría responsive (`width`/`height`, `srcset`/`sizes`) ya está recogida en #61 H.3; no duplicar esa parte.

**DEUDA NUEVA L.1 — escalera de formatos AVIF → WebP no sistematizada.**

La Home demuestra la inconsistencia actual:

- retrato: `<source type="image/avif" ...>` + `<img ...webp>`;
- cubierta: varias fuentes WebP por viewport, sin fuente AVIF equivalente.

No existe en `scripts/` un pipeline/contrato único que garantice para imágenes raster elegibles:

1. AVIF como primera opción cuando exista/sea rentable;
2. WebP como fallback;
3. tamaños responsive coherentes cuando aporten valor;
4. preservación de dimensiones/aspect ratio;
5. exclusiones explícitas para PNG/JPEG que deban conservarse por transparencia, fidelidad, compatibilidad o coste de conversión.

#### Implementación requerida L.1

- Extender el trabajo de imágenes sin pisar #61 H.3: #61 sigue siendo autoridad de geometría responsive; L.1 se limita a **format ladder / pipeline / verificación de formatos**.
- Definir una regla machine-checkable para imágenes raster públicas elegibles.
- No convertir indiscriminadamente todo `assets/`: excluir assets sociales, materiales de trabajo, imágenes no publicadas y casos donde AVIF no compense.
- Para imágenes públicas elegibles, generar o exigir AVIF + WebP fallback y mantener `width`/`height` estables.
- Añadir checker que detecte una superficie marcada como “modern-format-required” sin AVIF/WebP coherente.
- No romper OG/social cards ni referencias externas que necesiten una URL estable concreta.

#### Criterios de aceptación L.1

- [ ] existe una política de elegibilidad clara;
- [ ] al menos Home y superficies principales de Manecillas quedan cubiertas o justificadamente excluidas;
- [ ] AVIF no reemplaza el fallback WebP;
- [ ] el checker puede fallar con un fixture/regresión deliberada;
- [ ] no se duplican los checks de `srcset`/`sizes`/dimensiones de #61 H.3.

### Documento 31 — UI COPY + MICROCOPY V1

**Clasificación: PARCIAL.**

Gran parte del documento está superada por decisiones posteriores de navegación, Home y newsletter, y no debe restaurarse palabra por palabra.

**DEUDA NUEVA L.2 — microcopy del asistente sin autoridad única.**

El estado actual no coincide de forma estable con el contrato residual citado por el documento 31:

- el HTML publica `Asistente de la web — David Porto Díaz`;
- el JS de `assets/assistant.js` reescribe el hero a `¿Qué buscas?`;
- la introducción pasa a `Pregúntame por los libros...`;
- el placeholder pasa a `Escribe tu pregunta…`;
- el HTML fuente contiene además `¿Qué quieres encontrar?`, pero el runtime sustituye la estructura.

El problema no es que una de esas frases sea objetivamente peor, sino que **HTML fuente, runtime y contrato editorial no tienen una autoridad explícita única**. Eso dificulta mantener accesibilidad, tests y copy sin drift.

#### Implementación requerida L.2

1. Elegir la microcopy vigente del asistente con la UX actual como contexto; no revertir automáticamente a texto antiguo solo por coincidir con el documento 31.
2. Definir una fuente de verdad única para:
   - nombre visible del asistente;
   - título/hero;
   - introducción;
   - label del campo;
   - placeholder;
   - CTA/aria-label de envío;
   - nombre accesible del chat/panel.
3. Evitar que el HTML declare una experiencia y `assistant.js` la sustituya por otra distinta sin contrato.
4. Añadir test de copy/semántica que compruebe los strings canónicos relevantes y sus nombres accesibles.
5. Conservar la funcionalidad conversacional actual, local-first, estados de carga/error y no-autoapertura.

#### Criterios de aceptación L.2

- [ ] una única autoridad define la microcopy canónica;
- [ ] HTML y runtime no discrepan tras inicialización;
- [ ] title/meta/heading/labels accesibles usan nomenclatura coherente;
- [ ] test de regresión cubre los textos/labels contractuales;
- [ ] no se restaura navegación/newsletter antigua del documento 31.

### Documento 32 — CONNECTION SYSTEM V1 (inicio hasta línea 1000)

**Clasificación: YA DETECTADO / PARCIAL.**

`data/content-registry.json` existe y define `relatedIds`, pero el valor por defecto sigue siendo `[]` y la relación editorial todavía no funciona como autoridad efectiva para todas las conexiones. `scripts/check-internal-graph.py` valida enlaces HTML, huérfanos y canonicals; no convierte por sí mismo `relatedIds` en grafo editorial gobernado.

Esto **no es deuda nueva de L**: la consolidación de `relatedIds`, validación de IDs/tipos/duplicados/límites y consumo progresivo ya estaba registrada como deuda conocida. No abrir otra PR por ello.

La ronda se detiene exactamente en la línea 1000; no anticipar el resto del documento 32 ni 33–34.

## 3. No duplicar con PR abiertas

- #61 H.3: geometría responsive de imágenes (`width`/`height`, `srcset`/`sizes`). L.1 solo cubre formato/pipeline AVIF→WebP.
- #66 K.3: matriz de compatibilidad Chromium/Firefox/WebKit; no pertenece a L.
- #63: taxonomía analítica.
- #55/#56: newsletter/DOI/popup.
- #58: smoke post-deploy.
- #60: informe de assets huérfanos; no borrar ni convertir masivamente assets por esa lista.
- relationship graph / `relatedIds`: deuda ya conocida, no crear duplicado.

## 4. Orden recomendado

1. **L.2 microcopy del asistente** — pequeño, aislado y fácil de verificar.
2. **L.1 ladder AVIF→WebP** — coordinar con #61 H.3 para que formato y responsive no creen dos checkers contradictorios.

## 5. Definition of Done de esta PR

Esta PR es un brief de auditoría, no implementación. Solo puede considerarse resuelta cuando:

- L.1 está implementado con política + checker y coordinación explícita con #61 H.3;
- L.2 tiene autoridad única de copy + test;
- no se reabren radios/email antiguos ni relationship graph como tareas duplicadas;
- QA aplicable está en verde;
- no se toca `main`, no se despliega producción y no se activa auto-merge desde esta rama.
