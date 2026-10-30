# Encargo de producto: ver libros antes de atravesar todos los filtros

Estado: **BORRADOR, SIN IMPLEMENTAR**. P1 de UX, recorrido principal del catálogo.
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
- [ ] Primera tarjeta visible al primer scroll corto en configuración por defecto;
      fijar presupuesto geométrico justificado (referencia: <=1.000 px a 390×844).
- [ ] Buscar, filtrar, combinar, quitar filtros, ordenar y abrir ficha sin obstáculos.
- [ ] Sin trampas de foco, controles fuera de viewport o saltos fuertes al abrir filtros.
- [ ] Sin JS: libros/enlaces siguen disponibles y no hay acciones falsas.
- [ ] Capturas antes/después, teclado, reflow 320px, texto ampliado y lectores si disponibles.
- [ ] Tests de catálogo ampliados con geometría y recorridos reales, no solo screenshots.
- [ ] Presupuesto JS/CSS/CLS y rendimiento no empeoran; versiones y artefactos al día.
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