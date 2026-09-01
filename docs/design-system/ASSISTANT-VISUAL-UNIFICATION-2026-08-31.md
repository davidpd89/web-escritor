# Asistente — contrato de unificación visual · 2026-08-31

## Trazabilidad

Continúa la cadena `DISEÑO -` después de Findability.

`/asistente/` es `noindex`, pero es una interfaz real enlazada desde el header. Tiene interacción y CSS propios, así que debe revisarse como familia independiente y no dentro de Herramientas individuales.

Mantener Draft y no mergear fuera de orden.

## Objetivo

Unificar visualmente el Asistente con el sistema editorial azul/negro/dorado, preservando búsqueda, respuestas, fuentes, estados, accesibilidad, privacidad y comportamiento funcional actual.

Debe sentirse como instrumento editorial de consulta, no como chat SaaS genérico.

## Hallazgos verificados

`assets/assistant.css` conserva identidad anterior, entre otros:

- `--dp-petrol`;
- `--dp-sky`;
- fallbacks `#0075b8`;
- foco `#4D372C`.

Reconciliar esas fugas de forma scopeada. No reemplazar colores en masa sin revisar contraste y semántica.

## Dirección visual

Referencia:

- azul editorial `#1d4f96`;
- azul profundo `#0d2c57`;
- dorado `#b8860b`;
- pálido `#eefaff`;
- negro/neutros para texto y metadatos.

La consulta debe ser la acción principal. La respuesta debe leerse como documento, no como burbuja decorativa. Las fuentes deben distinguirse claramente y mantener enlaces accesibles. Estados inicial, carga, vacío, error y respuesta deben reconocerse también sin depender solo del color.

Yellowtail no debe usarse en consultas, respuestas, fuentes, controles ni estados críticos.

## Preservar

- `noindex`;
- canonical si existe;
- búsqueda y motor actual;
- fuentes/enlaces;
- estados de carga/error/vacío;
- `aria-live` y focus management;
- navegación por teclado;
- acceso desde header;
- parámetros de URL si existen;
- privacidad;
- CSP y analytics existentes;
- `data-*` y selectores usados por el runtime.

Una PR visual no debe reescribir el motor.

## Móvil

Revisar expresamente:

- input cómodo;
- teclado virtual;
- safe areas;
- targets táctiles;
- focus visible;
- ausencia de solapamientos fixed/sticky;
- lectura de respuestas largas y fuentes.

## QA requerido

Crear contrato browser específico y mantener autoridades funcionales existentes.

Cobertura mínima:

- 1440/1280;
- 1024/768;
- 844×390 landscape;
- 430/390/360/320;
- seams reales;
- zoom 200 %;
- text spacing WCAG;
- teclado/focus;
- reduced motion si existe motion;
- cero overflow.

Capturar estados reproducibles: inicial, input con foco, respuesta con fuentes, enlace largo, sin resultados, error y carga. No inventar estados que el runtime no produzca.

## Aislamiento

Verificar que los estilos no se filtren a:

- herramientas individuales;
- `/herramientas/` hub;
- shell/header fuera de los hooks previstos.

## Revisión humana

Probar el flujo completo: entrar desde header, escribir, enviar, leer, abrir fuentes, volver y repetir. En móvil, hacerlo con teclado abierto y en portrait/landscape.

La certificación de teclado virtual/safe areas requiere hardware real según `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Definition of Done

- fugas petrol/sky/#0075b8/#4D372C reconciliadas;
- consulta/respuesta/fuentes jerarquizadas;
- motor y datos funcionales intactos;
- `noindex` preservado;
- teclado/live regions/focus verdes;
- responsive/zoom/text-spacing sin overflow;
- herramientas/hub aislados;
- evidencia revisada;
- CI verde;
- Draft y sin merge hasta revisión física.
