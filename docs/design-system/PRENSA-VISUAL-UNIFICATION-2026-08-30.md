# Prensa · unificación visual 2026-08-30

## Alcance y trazabilidad

Esta intervención pertenece a la cadena apilada `DISEÑO -` y parte exactamente del HEAD `694d915f2beb9f7f79d6dbf562c54c73194f3dfe` de #276 Eventos.

Superficie: `/prensa.html`.

Objetivo: convertir el kit de prensa existente en un **dossier editorial / kit de medios** profesional, escaneable y documental, sin alterar hechos, bios aprobadas, fichas técnicas, disponibilidad de libros, enlaces, canonical, JSON-LD, contacto, controles de copia, impresión ni funcionamiento sin JavaScript.

La intervención no convierte Prensa en dashboard, escaparate de tarjetas equivalentes ni landing promocional genérica.

## Límite editorial de cobertura

Se mantiene el gate fijado por #185: el diseño no puede presentar como cobertura periodística independiente piezas de autor, menciones de comunidad, fichas de catálogo, páginas editoriales o referencias no verificadas.

Por ese motivo, `#cobertura` se trata como un **índice documental mixto** y deliberadamente subordinado. La jerarquía visual no equipara sus entradas con impactos de earned press.

No se añade ni se inventa cobertura externa.

## Diagnóstico del baseline

El baseline específico se construyó sobre la autoridad funcional existente `qa/identity-public-browser.mjs` y añadió una lectura de diseño propia de Prensa.

La superficie heredada era funcional, pero presentaba tres problemas principales:

1. La gramática dependía casi por completo de la capa compartida Identity y no tenía owner visual propio.
2. Los distintos tipos de contenido —datos rápidos, bios, fichas, imágenes, entrevistas, recursos, menciones y contacto— tendían a parecer registros equivalentes en lugar de piezas de un dossier con distinta autoridad.
3. El stress de zoom al 200 % descubrió un overflow horizontal real de **100 px** en 390 px de viewport. El origen estaba en el mínimo fijo de la rejilla `trust-strip`; la solución final queda absorbida por el owner local de Prensa, sin relajar el gate de reflow.

Durante la fase de baseline apareció además una lectura de CLS de Autor que no se reprodujo al reejecutar la autoridad sin cambios. No se modificó producción ni se relajó el umbral para ocultarla.

## Ownership y aislamiento

Prensa dispone ahora de un owner local:

- `assets/v1-press.css`

El scope está fijado de forma estática mediante:

- `main[data-page="press"]`

`prensa.html` solo incorpora dos cambios estructurales respecto de la base:

1. carga de `/assets/v1-press.css` después de `v1-identity.css`;
2. `data-page="press"` en `main#contenido`.

La auditoría del patch final confirma que no se modifican bios, fechas, ISBN, fichas, URLs, menciones, disponibilidad, texto editorial ni metadatos.

La capa común Identity sigue siendo la autoridad de comportamiento compartido. Autor, Premios y Eventos permanecen como controles explícitos de aislamiento.

## Dirección visual

### Masthead

El encabezado se trata como portada de dossier: azul editorial como autoridad principal, acento dorado y regla horizontal de archivo. La jerarquía tipográfica conserva Instrument Serif para display, Newsreader para lectura y la UI del sistema para controles.

### Datos rápidos

Los seis datos dejan de leerse como una banda de KPIs. Se presentan como ficha editorial compacta y documental, con divisiones de registro y jerarquía tipográfica estable.

### Bios y materiales

Las bios y materiales reutilizables se mantienen como piezas copiables del dossier, con cabecera lateral, estados claros y acciones funcionales. Las fotografías reales siguen siendo contenido documental, nunca fondos decorativos.

### Fichas de libros

`Las manecillas del recuerdo` se presenta como la ficha editorial actual y principal. `Samuel entre mundos` conserva una ficha completa secundaria. La diferencia es únicamente jerárquica/visual: no cambia publicación, comercio, disponibilidad ni datos técnicos.

### Entrevistas

Las preguntas sugeridas mantienen `details` nativo y se tratan como índice de conversación, no como colección de tarjetas.

### Recursos y charlas

Los recursos para creadores y los formatos de charla se ordenan como registros funcionales del dossier, reduciendo el patrón de card soup.

### Cobertura y menciones

La sección es deliberadamente más silenciosa que las fichas editoriales y los materiales de prensa. Esta decisión hace visible que el listado mezcla naturalezas distintas y evita sugerir ocho impactos periodísticos equivalentes.

### Contacto

El cierre funciona como directorio de medios: finalidad, explicación y acción quedan claramente separadas y escaneables.

## Contrato preservado

La implementación mantiene:

- canonical `https://davidportodiaz.com/prensa.html`;
- un único H1 `Kit de prensa`;
- familia `identity` y navegación contextual activa;
- orden completo del dossier;
- seis datos rápidos;
- cuatro registros de bios/materiales;
- tres registros de sinopsis;
- cinco preguntas de entrevista;
- tres recursos para creadores;
- tres formatos de charlas;
- controles de copia y feedback `aria-live`;
- fallback sin Clipboard API;
- retrato editorial real;
- tres fotografías documentales de la Feria del Libro de Madrid 2026;
- mockups reales de `Las manecillas del recuerdo` y `Samuel entre mundos`;
- ISBN y datos técnicos de ambos libros;
- WebPage JSON-LD;
- contacto de prensa;
- impresión útil;
- funcionamiento sin JavaScript;
- navegación por teclado;
- funcionamiento con text spacing WCAG;
- reflow con zoom al 200 %;
- aislamiento frente a Autor, Premios y Eventos.

## Matriz visual y seams

El contrato específico recorre 15 anchuras:

- 1728;
- 1440;
- 1280;
- 1024;
- 901 / 900;
- 768;
- 701 / 700;
- 601 / 600;
- 411 / 410;
- 390;
- 320 px.

Se controlan especialmente:

- ledger de bios/materiales en 901/900;
- fact sheets en 701/700;
- galería documental en 901/900 y 601/600;
- rampa de hero en 411/410;
- móvil 390/320;
- no-JS a 390;
- zoom 200 % y text spacing en contextos separados.

Las imágenes lazy se cargan y decodifican antes de capturar evidencia.

## Evidencia de código + QA

HEAD de código/QA inspeccionado: `0daacdab2f12faf9bbd262f4ef8bd5567ccb14aa`.

Run `Prensa browser QA`: `33336702967`.

Artefacto final inspeccionado: `prensa-visual-evidence`, ID `9739298865`.

Digest: `sha256:2edbd54fccf4937beb2ecfc3e5e3e69b2eee9b9023733418f289b526dee30d86`.

El reporte `prensa-design-report.json` confirma:

- `phase: visual-system-contract`;
- 15 viewports;
- `failures: []`;
- overflow horizontal 0 en todas las mediciones;
- fuentes objetivo cargadas;
- geometría tipográfica idéntica antes/después de estabilización;
- seams responsivos conforme al contrato.

La evidencia visual fue revisada en desktop, tablet, seams, móvil, no-JS y controles de aislamiento.

## Hallazgos de QA corregidos

- Overflow real de 100 px a zoom 200 % descubierto por el baseline y eliminado sin rebajar el gate.
- Mutación accidental de una frase de la bio larga detectada al auditar el patch y revertida antes de certificar; el HTML final vuelve a ser factual y solo contiene las dos modificaciones estructurales descritas.
- Desincronización temporal del shell tras una edición manual de HTML detectada por los checks generados y corregida antes del HEAD de evidencia.
- Lecturas puntuales de CLS de Autor no reproducibles en rerun; no se usaron como excusa para alterar Autor ni relajar límites.

## Definition of Done técnico

Para considerar cerrada técnicamente la superficie deben cumplirse simultáneamente:

- owner local y scope estático;
- diff factualmente neutro;
- autoridad Identity verde;
- contrato específico de Prensa verde;
- evidencia visual revisada;
- reflow/zoom/text-spacing/no-JS sin regresiones;
- aislamiento de las superficies hermanas;
- workflows finales aplicables en verde.

La revisión humana en dispositivos reales permanece fuera del cierre CI y sigue pendiente según el contrato de revisión real del proyecto.
