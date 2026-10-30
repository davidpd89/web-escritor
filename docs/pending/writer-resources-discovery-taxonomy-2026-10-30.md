# Encargo de producto: encontrar dónde enviar sin conocer 104 etiquetas

Estado: **IMPLEMENTADO** en la PR #1009 (ver «Implementación» al final). P1 de UX de recursos para escritores.
Base examinada: `f4a2ea43f3699e06fd96ccba0aab6c14d4b87f36`, 30/10/2026.

## Alcance e impacto observado

En producción, Chromium móvil 390×844, JS activo, service workers bloqueados,
sin peticiones fuera del origen:

- `/editoriales/`: 150 fichas y 105 opciones en género, incluida «Todos».
- Primera ficha a unos 1.646 px del inicio; página completa de unos 84.991 px.
- `/convocatorias-escritores/`: 51 opciones en género, incluida «Todos»;
  el recorrido inicial mostraba 80 convocatorias. Recuento sujeto al día.
- Las etiquetas editoriales mezclan géneros, subgéneros, públicos y formas:
  narrativa/adulta/contemporánea/breve/en español, fantasía/fantástico/fantasía
  oscura, infantil/literatura infantil, etc. No todas son sinónimos.

`assets/editoriales.js` exige `genres.includes(g)` sobre etiquetas normalizadas.
`assets/radar-convocatorias.js` también filtra los géneros declarados por etiqueta.
No hay un nivel de familia temática que explique alcance y relaciones.

## Caso concreto de descubrimiento

Seleccionar «fantasía» deja 54 editoriales. Entre las fichas NO incluidas por no
llevar esa etiqueta exacta se encuentran:

| Ficha | Etiquetas que sí declara |
|---|---|
| Ediciones Siruela | narrativa, fantástico, ensayo, literatura infantil |
| Editorial Andrómeda | romantasy, fantasía oscura, romance, dark romance |
| Cetus Editorial | fantasía oscura, terror, ciencia ficción, ucronía, folclore |
| Editorial Vanadis | ciencia ficción, fantasía oscura, romantasy y otras |
| Dilatando Mentes Editorial | terror, weird, fantasía oscura, ficción especulativa |

No afirmar que todas aceptan cualquier manuscrito de fantasía ni que estén abiertas:
el filtro temático no sustituye estado, condiciones ni fuente. El problema es que
el usuario necesita adivinar varias etiquetas para explorar una familia de interés.
No se ha medido abandono, éxito de envíos o impacto SEO.

## Encargo a la IA implementadora

1. Diseñar una taxonomía de DESCUBRIMIENTO: familias amplias, subgéneros y alias
   justificados, manteniendo intacta la expresión literal de cada fuente.
2. Separar tema/género, público, formato y recepción cuando sea relevante; no
   colapsar conceptos diferentes como narrativa breve y novela sin criterio.
3. Presentar pocas familias comprensibles primero y refinamiento opcional; que
   se pueda buscar «fantasía» sin conocer toda la nomenclatura editorial.
4. Hacer explícita la diferencia entre coincidencia amplia y etiqueta exacta.
   En la ficha siempre prevalecen requisitos y condiciones oficiales verificadas.
5. Rediseñar acceso móvil a filtros/resultados y compararlos con escritorio;
   no solucionar el exceso de opciones simplemente reduciendo tipografía.
6. Aplicar el contrato al directorio y al radar con adaptadores apropiados, sin
   alterar bots, horarios, scraping ni verificación automática de fuentes.
7. Conservar URL compartible, filtros de estado/país/envío directo, orden,
   fuentes, fecha de revisión y funcionamiento sin JS.

## Evidencia y aceptación

- [ ] Inventario de etiquetas actuales, agrupaciones propuestas y ambigüedades.
- [ ] Propuesta visual 390/768/1280 y recorrido «tengo una novela de fantasía».
- [ ] La búsqueda amplia descubre variantes relevantes y explica por qué aparecen.
- [ ] Ninguna agrupación convierte una etiqueta en garantía de aceptación o apertura.
- [ ] Estado de recepción/fechas y requisitos se ven antes de decidir enviar.
- [ ] Pruebas de sinónimos, subgéneros, combinaciones y negativos que no deben incluirse.
- [ ] Regresiones URL, restablecer, orden, teclado, reflow y contenido sin JS.
- [ ] Medidas antes/después de opciones iniciales y distancia hasta resultados;
      comprobar rendimiento con 150 fichas y el radar completo.
- [ ] Taxonomía y texto fuente conservados por constructores; paridad y CI.
- [ ] SHA desplegado y recorridos de búsqueda verificados por quien implementa.

Archivos de partida: `data/editoriales.json`, `scripts/build-editoriales.py`,
`assets/editoriales.js`, `assets/editoriales.css`, constructor/datos del radar,
`assets/radar-convocatorias.js` y QA de ambas familias.

Este encargo NO duplica #1004: aquel modifica catálogo de lectura, este recursos
de envío editorial. Reutilizar patrones V1 si conviene, no crear un diseño aislado.
Tampoco crear páginas SEO por cada alias ni cambiar indexación por defecto.

Otra IA continúa aquí con investigación, diseño, implementación y pruebas.
El commit actual es solo documental; no fusionarlo como funcionalidad terminada.
## Implementación (PR #1009)

- **Inventario y taxonomía**: `data/genre-families.json` recoge 13 familias (forma, género y
  público) y documenta las ambigüedades, entre ellas fantasía oscura, realismo mágico, novela
  corta, new adult y las etiquetas que se quedan sin familia. Ninguna etiqueta de la fuente se
  reescribe. Romantasy pertenece a Fantasía y a Romántica.
- **Código compartido**: `scripts/genre_families.py` genera el selector con dos grupos: primero
  «Familias (coincidencia amplia)», con valores `familia:<id>`, y después «Etiqueta exacta de la
  fuente», donde siguen las 104 etiquetas literales. También genera el mapa JSON que usa el
  cliente.
- **/editoriales/**: la familia Fantasía muestra 61 fichas (la etiqueta exacta «fantasía» sigue
  dando 54) e incluye Siruela, Andrómeda, Cetus, Vanadis y Dilatando Mentes. Cada ficha resalta
  las etiquetas que coinciden y lo explica: «Aparece en «Fantasía y fantástico» porque declara:
  …. Comprueba estado y condiciones antes de enviar.». La búsqueda libre también encuentra por el
  nombre de la familia. La familia se guarda en la URL (`#genero=familia:fantasia`), se combina
  con los demás filtros y «Limpiar» la quita junto con las notas.
- **/convocatorias-escritores/**: funciona igual. La familia Relato reúne relato corto,
  microrrelato, narrativa breve, etc., y la nota dice «las bases declaran: …».
- **Sin JS**: no se ve ninguna nota ni el JSON, y las fichas siguen completas.
- **Medidas a 390×844 en local**, con el mismo constructor y datos en las dos ramas:
  - main: primera ficha a 1.820 px;
  - rama: primera ficha a 1.808 px.
  - La ayuda ocupa una línea corta. Estado, país y orden pasan a dos columnas a partir de 360 px.
  - No hay scroll horizontal.
- **Regresión**: `qa/writer-resources-genre-families.mjs` falla con main («el selector separa
  familias y etiquetas exactas») y pasa en la rama.
- **Tests ajustados**:
  - `qa/data-radar-pairwise-filters.mjs` expande las opciones `familia:` con la taxonomía;
  - el contrato de diseño espera dos columnas de filtros a partir de 360 px.
