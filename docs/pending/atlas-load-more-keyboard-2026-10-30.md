# Encargo: continuidad de teclado al ampliar resultados del Atlas

Estado: **IMPLEMENTADO en esta rama**. Prioridad P2: navegación accesible.
Política: al revelar una tanda (teclado o puntero, intermedia o última) el foco va
al enlace de la primera entrada nueva; el estado `role=status` pasa a
«N resultados · se muestran X» / «· se muestran todos» solo tras ampliar (sin
anuncio extra al cargar ni al filtrar). Restablecer, que se deshabilita a sí
mismo, devuelve el foco a la búsqueda. Regresión en `qa/atlas-catalogue-browser.mjs`
(roja contra main: foco `BODY`; verde a 390 y 1280 px, con fixture de 126
entradas para la tanda intermedia). `atlas-catalogue.js` a `?v=3`.
Lector de pantalla real: **NO verificado** (sin NVDA/VoiceOver en este entorno).
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Reproducción confirmada en producción

Ruta `/atlas-literario/`, Chromium, movimiento reducido y service workers
bloqueados. Solo peticiones al propio origen; sin alterar la página publicada.

1. Se muestran 24 de las 42 tarjetas del catálogo actual.
2. Dar foco al botón `[data-atlas-more]` y activarlo con Enter.
3. Las 42 tarjetas pasan a estar visibles y el contenedor del botón se oculta.
4. `document.activeElement.tagName` pasa a `BODY`.

Salida literal de la comprobación:

```text
ATLAS BEFORE 24
ATLAS AFTER {"shown":42,"focus":"BODY","buttonVisible":false}
```

El foco deja de tener un destino visible útil cuando el usuario pide más
resultados. No se ha medido todavía la frase anunciada por un lector de pantalla
ni el siguiente Tab en todos los motores; no inventar esas consecuencias.

## Causa y cobertura

`assets/atlas-catalogue.js`:
- Handler `more`: incrementa `limit` y llama a `apply()`.
- `apply()` oculta `moreWrap` cuando `shownNow >= shown`.
- No se trata el foco del botón ocultado ni se conduce a las entradas nuevas.
- El contador tiene `role=status`/`aria-live=polite`: NO falta esa semántica.
  Pero expresa total de coincidencias (42), no cuántas se acaban de revelar.

`qa/atlas-catalogue-browser.mjs` comprueba la cantidad tras hacer click en Mostrar
más, a 390 y 1280 px. No verifica teclado, destino del foco ni su continuidad
cuando se oculta el botón. No cambiar el test a un assert estático de ARIA.

## Encargo a la IA implementadora

- Definir una política coherente para teclado al revelar una tanda: foco en una
  entrada nueva/encabezado apropiado o alternativa razonada. Evitar saltar al
  comienzo de la página y no enfocar un elemento oculto.
- Distinguir última tanda de tandas intermedias donde el botón permanece.
- Mantener foco/navegación previsibles también al cambiar filtros o restablecer.
- Anunciar la ampliación si el contador total no cambia; no duplicar anuncios
  ni confundir coincidencias totales con cantidad mostrada.
- Preservar la mejora progresiva: sin JS siguen visibles todas las tarjetas.
- No sustituir el patrón por otro sistema de paginación sin justificar alcance.

## Criterios de aceptación

- [ ] Regresión roja que use foco + Enter y detecte el foco BODY actual.
- [ ] Última tanda: destino visible, lógico y accesible; siguiente Tab previsible.
- [ ] Tanda intermedia y total <=24, con fixtures si cambia el catálogo.
- [ ] Filtrar/restablecer no deja foco en un control oculto o deshabilitado.
- [ ] Validar a 390 y 1280 px, teclado y puntero; sin regresiones de scroll/reflow.
- [ ] Comprobar anuncio con lector real si disponible; declarar su límite si no.
- [ ] Filtros combinados, URL, estado vacío y sin JS siguen pasando.
- [ ] Actualizar versiones/hashes y paridad; CI antes de deploy y SHA comprobado.

Esta PR solo prepara el encargo para otra IA. Continuar aquí con implementación,
pruebas y publicación; no fusionar el documento como si solucionara el fallo.