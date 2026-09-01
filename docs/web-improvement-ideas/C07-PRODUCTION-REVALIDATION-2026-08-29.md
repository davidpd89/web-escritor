# C.7 · Revalidación de producción — mapa / línea temporal del universo

Fecha: 2026-08-29  
Base inspeccionada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #182  
Estado: **MAP_ALREADY_IMPLEMENTED · ACCESSIBLE_TEXT_EQUIVALENT_EXISTS · TIMELINE_TRIGGER_NOT_MET · NO_CODE**

## Veredicto

La parte «mapa funcional de Noveris» ya está implementada de forma suficiente y canónica en `/universo/noveris/`.

No se debe crear otro mapa, micrositio o visualización por simetría. La parte «línea temporal» sigue condicionada a una necesidad editorial real, canon estable y una estrategia de spoilers.

## Evidencia directa de `main`

`universo/noveris/index.html` contiene una figura real:

- asset `/assets/mapa-funcional-noveris-ciudad-fantastica.webp`;
- dimensiones explícitas `1448x1086`;
- `loading="lazy"` y `decoding="async"`;
- alt que identifica Grimlor, Hospital Arcano, Archivos de la Memoria, estadio de Glíder y Barrera;
- título visible «Cómo se organiza Noveris»;
- párrafo explicativo;
- `figcaption`.

La información no termina en la imagen. La misma página incluye además:

- bloque «Ciudad de control»;
- sección HTML `#mapa` «Zonas y puntos de control»;
- tarjetas textuales para Colegio Grimlor, Hospital Arcano, La Raíz de Noveris y Estadio de Glíder;
- sección de historia de la Guerra de los Cristales;
- glosario canónico `DefinedTermSet`;
- contenido textual de sistema mágico, facciones, barrera y canalizadores.

Por tanto el visual tiene equivalente textual y vive dentro del hub canónico correcto.

## CSS y reflow

`assets/noveris.css` confirma:

- `.lore-figure img { width:100%; height:auto }`;
- copy/figcaption con `overflow-wrap:anywhere`;
- bento de tres columnas que colapsa a una columna por debajo de 900px;
- glosario que colapsa a una columna por debajo de 640px;
- tabla dentro de wrapper con overflow horizontal;
- reglas `@media print`.

No hace falta otro componente de mapa para resolver responsive/accessibility.

## Canon

La página ya es el owner de:

- geografía funcional;
- glosario;
- historia pública;
- facciones;
- sistema mágico.

C.7 y B.9 deben seguir convergiendo aquí. Crear `/mapa-noveris/` duplicaría contexto y owner.

## Spoilers

La guía visible declara que puede leerse sin revelar arco argumental/desenlace. Eso no autoriza a añadir futuras localizaciones, relaciones o eventos sin una revisión de spoilers.

Cualquier visualización futura debe revisar por separado:

- canon publicable;
- dato privado/spoiler;
- alt/metadata que puedan filtrar información oculta;
- fecha/versión del canon.

## Línea temporal

No existe obligación de producirla porque exista el mapa.

Trigger mínimo:

```text
chronology is genuinely hard to understand in prose
AND stable public canon exists
AND spoiler boundary is explicit
AND text equivalent exists
AND maintenance owner exists
```

Mientras no se cumpla, `NO_ACTION`.

## Qué NO hacer

- segundo mapa de Noveris;
- mapa IA decorativo sin fidelidad canónica;
- inventar regiones o distancias;
- timeline para «engagement» sin necesidad;
- datos embebidos solo dentro de una imagen;
- URL por cada localización;
- convertir borradores privados en canon público;
- duplicar el glosario de B.9.

## DoD

- [x] mapa inspeccionado directamente;
- [x] equivalente textual inspeccionado;
- [x] CSS responsive inspeccionado;
- [x] owner canónico identificado;
- [x] timeline separado del mapa ya implementado;
- [x] gate de spoilers/canon preservado;
- [x] no se crea visualización redundante;
- [ ] CI final del HEAD de esta revalidación.

## Decisión final

**MAP_ALREADY_IMPLEMENTED · ACCESSIBLE_TEXT_EQUIVALENT_EXISTS · TIMELINE_TRIGGER_NOT_MET · NO_CODE**
