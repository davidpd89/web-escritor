# Encargo: SVG de personajes autónomo y visualmente equivalente

Estado: **IMPLEMENTADO** (2026-10-30). Prioridad P2: exportación funcional defectuosa.

- `assets/mapa-personajes.js`: `portableSvg()` escribe los estilos calculados de líneas, círculos, flechas y textos como atributos de presentación (omitiendo los valores iniciales de SVG), retira `class`, `style`, `tabindex` y `data-*`, añade `width`/`height`, fondo, `<title>` y `<desc>` con `textContent`. Sin CSS, fuentes, scripts ni recursos externos.
- `qa/tools-structure-browser.mjs`: importa un mapa con alianza, secreto, rivalidad dirigida y nombres con `<>&` y acentos; exporta; abre el SVG en un contexto aislado con la red abortada y compara trazo, discontinuidad, grosor, relleno y opacidad con la pantalla; contraste de textos >= 4,5:1; título y nombres escapados. Rojo con el código de main, verde en la rama.
- No verificado: apertura manual en visores de escritorio (Inkscape, Vista previa, Illustrator).
Base examinada: `85a335e8309b10f10961f58029810f7c50e3dbc6`.

## Fallo confirmado

En `/herramientas/personajes/`, el botón Exportar SVG clona `#character-map`,
añade xmlns y serializa. El dibujo depende de reglas CSS externas de
`assets/mapa-personajes.css`, con selectores `html.v1 .map-edge line`,
`html.v1 .map-node circle`, etc. No se incluyen estilos ni atributos gráficos
equivalentes en el SVG exportado. Copiar literalmente esos selectores al SVG
tampoco bastaría: el documento SVG autónomo no tiene un ancestro `html.v1`.

## Evidencia de navegador (30/10, producción)

Se importó un mapa sintético v1: Ana, Bruno, relación amistad dirigida «Aliados».
Se interceptó en memoria el Blob creado por el handler real de Exportar SVG,
sin guardar ficheros ni enviar contenido. Resultado:

```text
SVG ON PAGE: stroke = rgb(85, 121, 138)
SVG EXPORT: hasStyle=false, hasStrokeAttribute=false, hasExternalStyle=false
SVG ISOLATED: stroke=none, nodeFill=rgb(0, 0, 0)
```

La copia se abrió en un iframe sin las hojas CSS del sitio. Las líneas dejan de
dibujarse (`stroke:none`) y los círculos usan relleno negro por defecto. Los
nombres también usan valores predeterminados que no garantizan contraste.
No se ha probado aún cada visor de escritorio, pero el defecto de autosuficiencia
está confirmado con un segundo contexto de documento.

## Encargo a la IA implementadora

- Exportar una imagen autónoma: estilos esenciales embebidos con selectores
  válidos para SVG, o atributos de presentación resueltos. Elegir estrategia
  explícita y mantenible para evitar divergencia con el diseño de pantalla.
- Resolver variables CSS a valores portables; preservar colores, anchos,
  discontinuidades, flechas, etiquetas y tipografía con fallback legible.
- No enlazar hojas/fuentes del sitio ni depender de clases del HTML exterior.
- Conservar viewBox, geometría, filtro/foco visible y caracteres escapados.
- Mantener equivalencia accesible: nombre/descripción y texto legible.
- Sin scripts ni contenido activo procedente de nombres o etiquetas del usuario.

## Pruebas que faltan

`qa/tools-structure-browser.mjs`, tramo de exportación, solo exige `<svg` y
`<title>Ana</title>` en el archivo. Esas aserciones pasan aunque no haya líneas
visibles. Ampliar a abrir la exportación fuera de la página y comprobarla allí.

- [ ] Regresión roja sobre el archivo que produce el botón real.
- [ ] Documento aislado sin CSS/red: relaciones visibles y nombres contrastados.
- [ ] Cubrir relación dirigida y estilos de al menos rivalidad/alianza/secreto.
- [ ] Nombres largos, tildes y caracteres `<>&` no rompen el XML ni ejecutan contenido.
- [ ] Capturas antes/después, pantalla frente a exportación; sin cambios de estética arbitrarios.
- [ ] JSON, importación, arrastre y filtrado siguen funcionando.
- [ ] Versionado/hashes, pruebas y CI antes de publicar; verificar el SHA tras deploy.

Esta PR solo contiene el encargo. Continuar esta rama con implementación y
evidencia; no fusionar como tarea completada. Es independiente del encargo de
importación segura (#997), aunque ambas soluciones pueden editar
`assets/mapa-personajes.js`: coordinar merge/rebase y no mezclar los alcances.