# Encargo: imprimir la sesión de club que acaba de generarse

Estado: **BORRADOR, SIN IMPLEMENTAR**. Prioridad P1 funcional.
Base examinada: `c369f933e52073604adc2972f902191289992e08`.

## Reproducción confirmada

Producción, `/clubes-de-lectura/preparar-sesion/`, Chromium, sin service worker
y sin solicitudes fuera del origen:

1. Pulsar Preparar sesión con los valores por defecto.
2. `[data-club-session-output]` se muestra correctamente.
3. Aplicar el medio print con Playwright, equivalente al CSS de vista de impresión.

```text
CLUB SCREEN true
CLUB PRINT {"resultVisible":false,"parentPanelDisplay":"none"}
```

El botón Imprimir del módulo `assets/club-session-builder.js` invoca
`window.print()` cuando existe una sesión. Pero en `assets/v1-tools.css`,
`@media print` impone `display:none` a todas las `.tool-panel`. En el HTML de esta
página el resultado está DENTRO de una `.tool-panel`, así que no puede imprimirse.
No basta con dar display:block al resultado si su ancestro continúa oculto.

La medición confirma visibilidad CSS; no se ha generado un PDF ni se ha probado
una impresora física en esta fase de detección. No afirmar que todo el PDF está
vacío: pueden imprimirse otras partes de la página, pero la sesión queda excluida.

## Encargo a la IA implementadora

- Definir un contrato de impresión para resultados anidados de herramientas.
- Mantener visible la sesión y ocultar formularios, botones y chrome que no aportan.
- Elegir corrección contextual/compartida según inventario de otros consumidores
  de `.tool-panel`. No mostrar indiscriminadamente todos los paneles al imprimir.
- Preservar tipografías legibles, contraste y saltos de página; no partir títulos
  de bloque innecesariamente ni imprimir contenido oculto de estados anteriores.
- Conservar pantalla móvil/escritorio y política local: no enviar datos del libro.

## Aceptación y pruebas

- [ ] Regresión roja sobre generación real + medio print: resultado visible.
- [ ] Generar PDF y comprobar que contiene título sintético y preguntas generadas.
- [ ] Probar sesiones de 30, 60 y 90 min y textos largos, sin recortes.
- [ ] Sin formularios/botones/chrome ni datos de estados ocultos en el PDF.
- [ ] Prueba negativa antes de generar: no imprimir resultado inexistente.
- [ ] Revisar CSS compartido en otras herramientas; no romper sus exportaciones.
- [ ] Evidencia antes/después, versiones/hashes y gates antes de publicar.
- [ ] Verificar el SHA desplegado y repetir recorrido de impresión.

Archivos de partida: `clubes-de-lectura/preparar-sesion/index.html`,
`assets/club-session-builder.js`, `assets/club-session-builder.css`,
`assets/v1-tools.css` y QA de herramientas/impresión existente.

Esta PR solo contiene el encargo. Otra IA continúa esta rama con solución,
pruebas y publicación. No fusionar el documento como si solucionara el defecto.