# 09 — Tipografía, ritmo y densidad

## 1. Objetivo

La tipografía actual ya tiene una tesis:

- Instrument Serif — display/editorial;
- Manrope — UI/metadatos;
- Newsreader — lectura;
- Allura — usos de firma muy concretos.

Por tanto esta PR **no recomienda una nueva fuente**.

La pregunta es si el stack actual se utiliza con una jerarquía suficientemente rica en cada familia y viewport.

## 2. Problema observado

La escala display es uno de los principales recursos de identidad. En mobile puede perder eficacia si:

- muchos H1/H2 tienen una masa parecida;
- un heading ocupa gran parte del viewport;
- el resto de señales de jerarquía desaparecen al colapsar grids;
- metadata, body y media se alinean siempre al mismo gutter;
- varias secciones repiten heading grande + cuerpo + border.

No confundir «tipografía grande» con «jerarquía fuerte».

## 3. Auditoría computed-style

Crear una extracción por página/viewport de:

```text
selector/tag
font-family
font-size
line-height
font-weight
letter-spacing
width/max-width
number of lines
bounding box height
margin before/after
color/contrast role
```

Agrupar por:

- H1;
- H2;
- H3;
- deck/lead;
- body;
- metadata;
- eyebrow;
- CTA;
- caption;
- quotes;
- ledger labels.

## 4. Relaciones, no valores aislados

Medir razones aproximadas:

```text
H1 / body
H2 / body
lead / body
metadata / body
heading height / viewport height
heading block / media block
```

No establecer un ratio «correcto» universal. Comparar familias y detectar cuándo todo converge a la misma escala.

## 5. Primera pantalla

Para 390×844 medir:

- altura header;
- breadcrumb;
- H1;
- deck;
- metadata;
- acciones;
- primer asset;
- cuánto contenido principal aparece antes del fold aproximado.

El fold no es una frontera rígida, pero ayuda a detectar cuando un título consume toda la entrada sin necesidad.

## 6. Heading wrap

Revisar títulos reales largos.

Objetivo:

- cortes naturales;
- evitar una palabra aislada cuando el navegador puede equilibrar;
- no partir sílabas arbitrariamente por diseño;
- no reducir font-size hasta perder identidad solo para una línea menos.

Herramientas actuales como `text-wrap: balance/pretty` pueden utilizarse cuando su soporte y fallback sean adecuados, pero no sustituir revisión real.

## 7. Español

La microtipografía debe seguir el documento 35 de Drive como autoridad.

Revisar:

- comillas;
- rayas;
- puntuación;
- cifras;
- fechas;
- abreviaturas;
- viudas/huérfanas cuando el medio permita control razonable;
- espacios inseparables donde sean útiles;
- títulos con nombres propios;
- ISBN/precios como unidades legibles.

No meter JavaScript de line-breaking general para «perfeccionar» titulares.

## 8. Medida de lectura

Para cuerpo largo mantener una medida editorial controlada.

No hacer que el texto ocupe 100% del viewport desktop porque sobra espacio.

En mobile la línea se aproxima naturalmente al gutter, pero revisar:

- 320;
- text spacing;
- zoom;
- fuentes fallback.

## 9. Ritmo entre párrafos y headings

Una página editorial debe diferenciar:

- continuidad de párrafo;
- cambio de subsección;
- cambio de capítulo;
- nota;
- cita;
- figura;
- fuente;
- cierre.

Si todos los H2 usan exactamente `margin: 2.5em 0 .7em`, el artículo puede seguir necesitando otra señal macro para capítulos largos.

No significa variar arbitrariamente cada heading. Puede haber roles.

## 10. Densidad

Definir densidad como combinación de:

- caracteres/área;
- número de elementos;
- tamaño relativo;
- espacios;
- líneas/bordes;
- media;
- acciones;
- metadata.

Una página plana puede estar muy espaciada. «Más whitespace» no garantiza ritmo si todo tiene el mismo whitespace.

## 11. Alternancia de densidad

Ejemplo conceptual:

```text
apertura concentrada
→ pausa/media
→ lectura
→ inserto corto
→ lectura
→ cierre amplio
```

Esto produce una silueta más legible que:

```text
4rem
sección
4rem
sección
4rem
sección
```

## 12. Eyebrows y mayúsculas

La web usa labels uppercase/letter-spaced como señal editorial.

Auditar frecuencia.

Si cada sección empieza con eyebrow, deja de ser señal y se convierte en textura repetitiva.

Preguntar:

- ¿desambigua territorio/estado?;
- ¿aporta jerarquía?;
- ¿puede eliminarse?;

## 13. Meta y datos

Manrope funciona bien para metadata, pero la composición importa más que la familia.

Opciones:

- margen desktop;
- inline mobile;
- ledger;
- pequeñas columnas;
- fecha como ancla.

No convertir metadata en chips/pills por legibilidad.

## 14. Citas

La cita no necesita card.

Puede diferenciarse por:

- medida;
- familia display/reading;
- indent;
- filete;
- espacio;
- atribución.

Evitar enormes comillas decorativas generadas por pseudo-elemento si no aportan.

## 15. Fragmentos literarios

Deben tener registro propio, distinto del texto explicativo.

Variables posibles:

- medida;
- tamaño;
- leading;
- margen;
- folio/capítulo si existe;
- separación.

No cambiar el texto literal para mejorar composición.

## 16. Tablas/listados

Typography responsive debe priorizar escaneo.

En mobile:

- labels claros;
- stacking deliberado;
- no repetir headings vacíos;
- no reducir a 11 px para mantener columnas.

## 17. Font loading

Revisar fallback stack y métricas.

Preguntas:

- ¿el fallback provoca H1 mucho más alto?;
- ¿cambia botones/nav?;
- ¿genera CLS?;
- ¿se pueden usar font metric overrides si realmente compensa?

No optimizar por teoría sin medir.

## 18. Performance de fuentes

No añadir pesos/estilos por refinamiento si no se usan.

Auditar:

- número de archivos;
- subsets;
- preload;
- `font-display`;
- pesos realmente presentes;
- CSS que pide pesos sintéticos.

Diseño y rendimiento son la misma decisión aquí.

## 19. Typography evidence report

Proponer script futuro:

```text
scripts/design/audit-typography.mjs
```

Output machine-readable:

```json
{
  "route": "/autor.html",
  "viewport": 390,
  "h1": {
    "fontSize": 0,
    "lineHeight": 0,
    "lines": 0,
    "height": 0,
    "viewportShare": 0
  }
}
```

Los números reales deben salir del navegador, no rellenarse en documentación.

## 20. Rhythm evidence report

Para cada escena:

```json
{
  "id": "bio",
  "top": 0,
  "height": 0,
  "gapBefore": 0,
  "gapAfter": 0,
  "background": "...",
  "alignment": "...",
  "dominantType": "...",
  "mediaRole": null
}
```

Permite detectar 8 escenas con el mismo perfil.

## 21. Qué explorar antes de cambiar tipografía

Si una página se siente plana, probar en Figma:

1. variar medida;
2. variar posición;
3. cambiar orden;
4. crear margen editorial;
5. romper gutter con media;
6. reducir frecuencia de labels;
7. variar ritmo;
8. reforzar protagonista;
9. reducir un heading secundario;
10. cambiar relación con imagen.

Solo si el sistema sigue fallando, abrir discusión de fuentes.

## 22. Anti-slop tipográfico

Rechazar:

- serif display gigantesca en cada bloque;
- sans condensada añadida «para contraste» sin sistema;
- 5 familias;
- outline text;
- texto vertical decorativo;
- marquee tipográfico;
- palabras gigantes recortadas por viewport sin función;
- tracking excesivo;
- all caps en párrafos;
- gradiente dentro de texto;
- mezcla de italic/script para parecer literario;
- drop caps en todas las páginas.

El drop cap actual de artículos debe seguir siendo una firma local, no expandirse a todo el sitio.

## 23. Review checklist

```text
[ ] H1 tiene peso adecuado a la tarea
[ ] H2 no compite sistemáticamente con H1
[ ] lead y body se distinguen
[ ] metadata es escaneable
[ ] measure correcta
[ ] 320 funciona
[ ] 200% funciona
[ ] text spacing funciona
[ ] fallback funciona
[ ] no hay overflow
[ ] labels no saturan
[ ] fragmentos/citas tienen registro propio
[ ] ritmo macro perceptible en long screenshot
```

## 24. Criterio final

La tipografía no debe demostrar que tenemos una fuente bonita.

Debe organizar el tiempo de lectura: **entrar, orientarse, detenerse, leer, cambiar de registro y salir**.