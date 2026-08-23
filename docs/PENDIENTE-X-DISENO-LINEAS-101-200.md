# X — Diseño final · líneas 101–200

Fuente auditada: `PENDIENTE DISEÑO GPT.txt`, líneas **101–200 exactas**.
Base: `implementacion-web-2026@4694799edc6d9c9e729b896cadda1eef9726d083`.

> Este documento no interpreta la línea 201 ni ningún contenido posterior.

## Clasificación del bloque

### YA CUBIERTO POR #82

Las líneas 106–148 no crean otro owner. Pertenecen a la PR de diseño final de Home/cartografía:

- View Transitions semánticas Home → Manecillas y Home → Autor;
- hero reveal;
- aparición/dibujo selectivo de rutas;
- continuidad visual de portada/retrato;
- preview visual real de Explorar;
- materialidad/motion de Home.

Owner: **#82 — W — Diseño final 1–100: Home, cartografía, motion y materialidad**.

No duplicar aquí JS/CSS de Home, cartografía ni View Transitions.

### SUPERADO POR EL REPO REAL

Las líneas 152–182 describen dos carencias que ya no existen en `implementacion-web-2026`:

1. `.explore-preview` ya no usa `aria-live="polite"` ni `aria-atomic="true"` en el shell actual.
2. `/accesibilidad/` ya existe, es indexable y contiene estándar aplicado, alcance, limitaciones conocidas, contacto y fecha. El footer/autoridad de navegación ya contempla `site-accessibility`.

No abrir deuda nueva por esos dos puntos.

## X.1 — DEUDA NUEVA REAL: procedencia visual + pipeline cromático reproducible

Las líneas 186–200 sí describen un hueco vigente: el repo no contiene una autoridad clara que permita responder, para cada asset visual que entra en el diseño final:

- de qué fuente sale;
- si es material real, adaptación, composición o pieza generada;
- qué transformaciones están autorizadas;
- qué crop es admisible;
- qué derechos/licencia/evidencia tenemos;
- qué muestras cromáticas se extrajeron realmente;
- cuáles se seleccionaron y por qué;
- a qué tokens CSS terminan alimentando.

Esto es importante porque la fase final sí va a usar fotografía, portadas, material editorial, fondos, composiciones y adaptaciones visuales. El objetivo no es restringir creatividad sino volverla trazable y reproducible.

## Decisión visual vigente

No existe una prohibición general de contenido generado o editado con IA/herramientas generativas.

Se permite, cuando exista una necesidad concreta de diseño:

- partir de fotografías, portadas o referencias visuales reales;
- extraer estructura/JSON/especificaciones de una referencia y reconstruirla adaptada al sistema de David;
- retocar luz, encuadre, profundidad, fondo, composición y textura;
- crear fondos, abstracciones, ornamentos o piezas gráficas nuevas;
- combinar recursos reales y generados siempre que el resultado sea coherente, fino y deliberado.

Lo que debe evitarse:

- estética «IA genérica» reconocible y sin relación con la identidad editorial;
- inventar fotografías documentales, prensa, manuscritos, firmas, objetos históricos o material que parezca una evidencia real cuando no lo es;
- registrar como «fuente real» una pieza generada;
- ocultar una procedencia dudosa bajo un nombre de archivo ambiguo.

## Contrato de implementación

Crear una autoridad única, preferiblemente `data/media-provenance.json` (el nombre puede cambiar si al implementar existe una autoridad posterior mejor), con una entrada por asset de producción relevante.

Cada entrada debe poder expresar como mínimo:

```json
{
  "id": "...",
  "productionAsset": "assets/...",
  "sourceAsset": "assets/... | external-reference | generated",
  "sourceKind": "photo | cover | scan | press | illustration | generated-background | composite | other",
  "origin": "...",
  "rightsStatus": "confirmed | restricted | pending | unknown",
  "rightsEvidence": "...",
  "derivationType": "original | crop | retouch | recolor | composite | generated | reference-adaptation",
  "allowedTransformations": ["crop", "retouch", "recolor"],
  "cropPolicy": "...",
  "colorExtraction": {
    "method": "...",
    "rawSamples": ["#......"],
    "selectedSamples": ["#......"],
    "tokenMapping": {"--token": "#......"}
  },
  "notes": "..."
}
```

Los nombres exactos del schema pueden ajustarse, pero no debe perderse ninguna de esas capacidades semánticas.

## Reglas de verdad

1. No inventar derechos, autoría, procedencia ni licencia.
2. `unknown`/`pending` es válido; una afirmación falsa no.
3. Un asset con derechos no confirmados no puede promocionarse automáticamente a producción por el mero hecho de estar en `assets/`.
4. Un asset generado debe declararse como tal, aunque derive visualmente de referencias reales.
5. Una composición debe registrar sus fuentes principales cuando sean trazables.
6. No convertir este manifest en una excusa para bloquear recursos puramente decorativos triviales: el nivel de detalle debe ser proporcional al riesgo/valor del asset.

## Pipeline cromático reproducible

El sistema final debe poder repetir la extracción de color de, al menos:

- portada oficial de `Las manecillas del recuerdo`;
- retratos/fotografías realmente utilizados como pilares de la identidad;
- otros assets que aporten una paleta territorial deliberada.

El pipeline debe conservar:

1. asset fuente;
2. método/versión de extracción;
3. muestras crudas;
4. muestras descartadas/seleccionadas o, como mínimo, seleccionadas con criterio documentado;
5. conversión a espacio/formato usado por la web;
6. token CSS de destino.

No basta con pegar hexadecimales a mano en `v1-tokens.css` sin poder explicar de dónde salen si se presentan como colores derivados de la obra/fotografía.

## Relación con PR existentes

- **#82**: consume esta autoridad para materialidad/color, pero no debe inventarla de forma paralela.
- **#67**: sigue siendo owner de escalera AVIF/WebP y frescura/provenance técnica de derivados de formato. Esta PR X es owner de procedencia editorial/visual y extracción cromática, no del encoder.
- **#61**: sigue siendo owner de dimensiones/srcset/sizes.
- **#60**: sigue siendo informe de huérfanos; no borrar assets porque este manifest aún no los cite.
- **#78**: QA responsive/edge states, no procedencia.

## Definition of Done

La PR no estará lista hasta que:

- exista una autoridad máquina única para procedencia visual;
- los assets de identidad realmente usados por Home/Manecillas/Autor estén registrados;
- no se inventen derechos ni licencias;
- exista un método reproducible de extracción cromática;
- `rawSamples`/`selectedSamples` o equivalentes queden persistidos para las fuentes principales;
- los tokens derivados indiquen qué fuente los originó;
- haya checker/tests que detecten al menos assets de identidad sin manifest, referencias a `sourceAsset` inexistentes y estados inválidos;
- el sistema distinga claramente original, adaptación, composición y generado;
- #82 pueda consumirlo sin duplicar datos.

## Estado

Esta PR comienza como **DRAFT / contrato de implementación**.

No toca `main`, no despliega producción, no activa auto-merge y no modifica todavía la estética publicada.
