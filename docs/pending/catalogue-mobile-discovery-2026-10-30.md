# Encargo de producto: ver libros antes de atravesar todos los filtros

Estado: **IMPLEMENTADO** (ver «Implementación»). P1 de UX, recorrido principal del catálogo.
Base: `c369f933e52073604adc2972f902191289992e08`.

## Problema medido

En producción `/recomendaciones/`, Chromium, alto 844 px, JS activo, movimiento
reducido y peticiones externas bloqueadas. Posición absoluta de la primera tarjeta
y altura del sidebar, con getBoundingClientRect y scrollY tras load:

| Ancho | Primera tarjeta desde inicio | Altura de filtros |
|---|---:|---:|
| 390 px | 1.985 px | 1.228 px |
| 768 px | 1.799 px | 1.212 px |
| 1280 px | 668 px | 812 px |

El visitante móvil pasa por más de dos alturas de pantalla antes de ver un libro.
Antes aparecen tipos, facetas, precios, novedades, extensión y acciones. En desktop
el sidebar convive con el catálogo; en móvil/tableta lo antecede entero.
No se ha medido abandono/conversión: no inventar porcentajes ni causalidad comercial.

## Objetivo del encargo

Rediseñar el descubrimiento móvil/tableta para mostrar pronto libros y permitir
refinar sin obligar a atravesar todas las opciones. No es simplemente reducir
tipografía/padding ni ocultar funcionalidades. Diseñar y justificar una solución
coherente con V1 (por ejemplo búsqueda prioritaria + acceso a filtros resumidos).

- Conservar búsqueda por título/autor/ISBN visible y fácil de encontrar.
- Acceso claro a filtros y orden, resumen de filtros activos, recuento y restablecer.
- Definir apertura/cierre, foco, Escape y navegación si se elige panel/modal.
- Mantener campos, multiselección, test de lectura, URL compartible y paginación.
- Verificar estados vacío/cargando/error, filtros largos y teclado virtual.
- Auditar patrón equivalente del Atlas para reutilización sin imponer la misma
  solución si su contenido no lo necesita. No mezclar corrección de foco #999.

## Aceptación y evidencia de producto

- [ ] Propuesta visual antes de implementar: pantallas 390/768/1280 y recorrido.
- [x] Primera tarjeta visible al primer scroll corto en configuración por defecto;
      fijar presupuesto geométrico justificado (referencia: <=1.000 px a 390×844).
- [x] Buscar, filtrar, combinar, quitar filtros, ordenar y abrir ficha sin obstáculos.
- [x] Sin trampas de foco, controles fuera de viewport o saltos fuertes al abrir filtros.
- [x] Sin JS: libros/enlaces siguen disponibles y no hay acciones falsas.
- [ ] Capturas antes/después, teclado, reflow 320px, texto ampliado y lectores si disponibles.
- [x] Tests de catálogo ampliados con geometría y recorridos reales, no solo screenshots.
- [x] Presupuesto JS/CSS/CLS y rendimiento no empeoran; versiones y artefactos al día.
- [ ] CI y comprobación de producción antes de cerrar la implementación.

Archivos de partida: `scripts/templates/reading-catalogue.html.tmpl`,
`scripts/build-reading-catalogue.py`, `assets/reading-catalogue.css`,
`assets/reading-catalogue.js` y QA de recomendaciones/catálogo. No parchear solo
HTML generado. Coordinar con #1001 (normalización de URL), no duplicar ese fix.

Importancia SEO: mejora propuesta de usabilidad y descubrimiento interno, no una
promesa de posiciones. Si hay acceso a analítica consentida/Search Console, usar
baseline de entradas/dispositivos y medir después sin añadir trackers nuevos.

Esta PR es el encargo para otra IA: diseño, implementación, pruebas y despliegue
pendientes. No fusionar el documento como si solucionara la experiencia.

## Implementación

Solución: búsqueda prioritaria + panel «Filtros» plegable solo en ≤900 px.

- `scripts/build-reading-catalogue.py` genera, dentro del mismo `fieldset`, un botón
  `[data-catalogue-refine-toggle]` (`aria-expanded`/`aria-controls`) y envuelve
  facetas, precio, novedades, extensión, «Más filtros» y acciones en
  `#catalogue-refine`. La búsqueda queda fuera del panel y el orden sigue en la
  cabecera de resultados. Sin JS el botón está deshabilitado y el panel oculto en
  móvil (los filtros sin JS ya eran controles deshabilitados), así que las fichas
  enlazadas suben sin ofrecer acciones falsas.
- `assets/reading-catalogue.css` (v=15): en escritorio el botón no existe y el panel
  se ve siempre; en ≤900 px el panel se oculta salvo `data-open`.
- `assets/reading-catalogue.js` (v=21): `apply()` resume «· N activo(s)» en el botón
  (también con filtros que llegan por URL); clic/Enter/Space abren y cierran; Escape
  dentro del panel lo cierra y devuelve el foco al botón. Abrir no desplaza la
  búsqueda (sin saltos). Hash compartible, paginación (#1001) y test de lectura sin
  cambios.

Geometría (Chromium, alto 844, local): primera tarjeta 949 px a 320/390 px y 780 px a
768 px (antes 2.040/1.985/1.799); escritorio sin cambios (668 px). Presupuesto:
≤1.000 px móvil, ≤700 px escritorio.

Regresión: `qa/catalogue-mobile-discovery.mjs` (en recommendations-browser-qa.yml)
falla en main («320px: la primera tarjeta empieza a 2040 px») y pasa en la rama:
geometría 320/390/768/1280, recorrido de teclado (abrir, faceta, resumen, URL,
Escape + foco, Restablecer, ordenar, ficha), filtros por URL y sin JS. Los tests de
catálogo que interactúan con filtros en móvil abren «Filtros» como el lector.
Las capturas base `recomendaciones__mobile/tablet` se regeneran desde el job de CI.

Auditoría del Atlas: `/atlas-literario/` tiene el mismo patrón (a 390 px, formulario
de 1.120 px y primera tarjeta a 1.722 px). Reutiliza las clases `catalogue-*`, así
que el mismo panel es aplicable, pero su formulario tiene otra estructura; queda
como seguimiento propio para no mezclarlo con este encargo.
