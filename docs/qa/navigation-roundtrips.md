# Recorridos de navegación y vuelta

Complementa la paridad estática del shell, `section-context-parity.mjs` y las
pruebas de foco inicial. No repite medidas generales de colores, fuentes o
distancias: las auditorías de formato/reflujo existentes ya las realizan. El
hueco cubierto es hacer recorridos entre documentos desde las páginas nuevas y
comprobar después el historial y la recuperación interactiva de los menús.

## Cobertura

Fuentes: Cuaderno, catálogo, índice de autores, índice de editoriales del
catálogo, una ficha real de libro incorporado automáticamente y su autor. Los destinos se obtienen de
`data/navigation.json` y `data/content-registry.json`, sin adivinar rutas por
etiquetas. Se excluyen los enlaces a la propia página.

- 390 y 1280 px: enlaces reales del pie, incluyendo el índice editorial del catálogo.
- En la portada a 1280 px: las cuatro opciones del submenú superior de Libros recomendados.
- Cada viaje: clic, destino, Atrás, Adelante, Atrás y reapertura de Explorar.
- En la portada de escritorio se vuelve a abrir y cerrar también el submenú superior.
- Se verifica que Escape devuelve el foco al botón de Explorar después del viaje.
- Desde el catálogo se selecciona un ISBN y orden antes de salir y se comprueba
  que los controles, resultados, hash y parámetro de origen se conservan.
- Se detectan errores HTTP de documentos y errores JS sin capturar.

Los clics son normales, sin `force`, de modo que un enlace tapado o no utilizable
falla en el paso correspondiente. La paridad de texto/destino del menú se
comprueba en el DOM interactivo de la portada. Las plantillas interiores no
incluyen ese masthead: se prueban sus controles reales (pie y Explorar) sin
considerar un error la ausencia intencionada del menú de portada.

## Reproducción e informe

```sh
npm ci
npx playwright install chromium
node qa/reading-navigation-roundtrips.mjs
```

El script abre su propio servidor local en un puerto libre y lo cierra al
terminar. Bloquea servicios externos y service workers: se comprueban navegación
y código propios, no disponibilidad de analítica ni comportamiento offline.

En `.ci/navigation-roundtrips/` quedan JSON y Markdown con commit, ancho,
fuente, destino, superficie, texto pulsado y título de llegada. En fallos añade
la fase exacta, URL, error, errores de página/HTTP y captura. Todos los viajes se
intentan aunque uno falle. El proceso termina con código 1 ante hallazgos.
Los informes se actualizan al terminar cada viaje, de modo que una interrupción
conserve resultados parciales y la cobertura prevista/completada sea explícita.

El workflow informativo corre en cambios pertinentes, semanalmente los viernes
a las 07:23 UTC y manualmente. Conserva artefactos 30 días y no cambia los
controles obligatorios. Chromium puede restaurar o recargar documentos al usar
el historial; no se presenta esta prueba como una certificación de BFCache ni
de todos los motores/dispositivos.

## Decisión editorial que el test no debe inventar

La configuración actual dirige la opción superior **Editoriales** a
`/editoriales/` (directorio de manuscritos). El directorio editorial del catálogo
está en `/recomendaciones/editoriales/` y tiene entrada propia en el pie. El test
comprueba esos destinos autorizados y los hace visibles en su matriz; no declara
un enlace roto solo porque pueda discutirse su etiqueta o ubicación. Si se
decide cambiar esa UX, se cambia primero el registro de navegación y después se
verifica el nuevo recorrido.

## Validación inicial

El 22/10/2026 pasan los 58 recorridos de la matriz local sobre el producto de
`72ab6be7`: 27 en móvil y 31 en escritorio. Incluye una ficha automática de
Arturo Pérez-Reverte y su página de autor, además de los índices nuevos. La
configuración actual no ha producido fallos funcionales en esos recorridos.
