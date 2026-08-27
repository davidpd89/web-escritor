# 01 — Auditoría visual del estado actual

**Corte:** 27/08/2026  
**Ámbito:** implementación real en `main`, no mockups ni intención documental.

## 1. Diagnóstico principal

La web no parte de un diseño pobre. Parte de un **sistema editorial técnicamente sólido cuya ambición visual se distribuye de forma desigual**.

La Home tiene una dirección de arte más reconocible. Varias familias interiores, en cambio, han resuelto correctamente accesibilidad, reflow y consistencia, pero se han acercado demasiado a una misma gramática:

```text
masthead grande
→ línea
→ sección blanca
→ línea
→ sección blanca
→ línea
→ siguiente sección
```

En desktop esa gramática puede seguir funcionando por la rejilla, los márgenes y la relación entre columnas. En mobile, cuando las columnas colapsan a una sola, desaparecen muchas de las tensiones que daban jerarquía.

El fallo no es «falta color». Es **pérdida de composición al reducir dimensiones**.

## 2. Lo que ya funciona y debe preservarse

### 2.1. Sistema de tokens

`assets/v1-tokens.css` ya contiene:

- superficies;
- color semántico;
- stack tipográfico;
- escala fluida;
- spacing;
- medidas editoriales;
- gutter;
- motion;
- controles;
- focus;
- z-index.

No debe abrirse un rediseño empezando por sustituir tokens por preferencias de una herramienta.

### 2.2. Base accesible

`assets/v1-base.css` ya resuelve bien:

- box sizing;
- focus visible;
- targets de control;
- wrapping de texto largo;
- formularios;
- reduced motion;
- escalado de inputs;
- ausencia de dependencia visual de JavaScript para contenido básico.

### 2.3. HTML y SEO

Las familias contienen HTML semántico, headings reales, navegación, breadcrumbs, contenido server-rendered y schema. El trabajo visual debe preservar esa base.

### 2.4. Familias diferenciadas

Existen capas específicas para:

- Home;
- libros;
- Samuel;
- identidad;
- Cuaderno/artículos;
- herramientas;
- páginas de recursos.

Por tanto, no necesitamos introducir un framework de componentes para conseguir variedad. Ya hay puntos de extensión adecuados.

### 2.5. Home

`assets/v1-home.css` demuestra que el lenguaje editorial puede ser más rico sin cards genéricas:

- river grid;
- relaciones de escala desiguales;
- celdas de media y texto;
- una superficie tintada contextual;
- promo band;
- variaciones de densidad;
- media integrada en la geometría;
- navegación editorial propia.

La Home debe servir como **prueba de posibilidad**, no como template que copiar a todas las páginas.

## 3. Gaps por sistema

## 3.1. Responsive: reflow correcto, composición insuficiente

En `v1-families.css`, `v1-editorial.css` e `v1-identity.css` abundan decisiones mobile del tipo:

```css
grid-template-columns: 1fr;
display: block;
position: static;
```

Son decisiones correctas para evitar roturas, pero eliminan relaciones espaciales sin crear otras nuevas.

### Síntoma

Una página que en desktop expresaba jerarquía mediante:

- columna marginal;
- cuerpo dominante;
- folio;
- media lateral;
- metadata vertical;

pasa en móvil a:

```text
metadata
texto
imagen
texto
links
siguiente sección
```

Todo comparte ancho, alineación y superficie.

### Consecuencia

El usuario puede leerlo, pero cuesta responder visualmente:

- ¿qué es protagonista?;
- ¿qué es contexto?;
- ¿dónde termina una escena?;
- ¿qué relación hay entre bloques?;
- ¿qué merece detenerse a mirar?;
- ¿qué es navegación y qué es contenido?;

## 3.2. Jerarquía móvil demasiado dependiente del tamaño de heading

La implementación utiliza titulares fluidos muy grandes como principal señal de jerarquía.

Eso funciona en una portada editorial cuando hay suficiente espacio compositivo. En móvil, si varias escenas recurren a titulares grandes y al mismo gutter, el tamaño deja de diferenciar y pasa a ser ruido dominante.

No se propone reducir todos los titulares. Se propone medir **relaciones**:

- H1 vs deck;
- H2 vs cuerpo;
- heading vs media;
- heading vs metadata;
- espacio antes/después;
- ancho de bloque;
- alineación;
- frecuencia de titulares grandes por viewport.

## 3.3. Ritmo demasiado uniforme

`--section-gap` y los paddings fluidos ayudan a consistencia, pero una secuencia larga con gaps similares produce cadencia mecánica.

Una publicación editorial necesita distinguir:

- pausa larga;
- transición corta;
- continuidad;
- corte de capítulo;
- inserto documental;
- nota;
- pieza protagonista.

No se resuelve creando diez nuevos spacing tokens por estética. Se resuelve asignando **roles de ritmo** a escenas.

## 3.4. Superficie demasiado homogénea en páginas interiores

La mayor parte de las páginas internas trabaja sobre blanco y separadores discretos.

Eso no es un problema por sí mismo. The Paris Review, LRB y muchas publicaciones pueden ser muy jerárquicas sobre superficies casi neutras.

El problema aparece cuando coinciden:

- mismo fondo;
- mismo gutter;
- mismo ancho;
- misma alineación;
- mismo hairline;
- mismo heading treatment;
- misma separación vertical.

La solución debe cambiar alguna de esas variables con intención. No necesariamente el color.

## 3.5. Hairline como separador universal

Los bordes de 1 px aparecen como lenguaje frecuente.

Son útiles, pero si todas las divisiones se explican con la misma línea, la línea deja de expresar importancia.

Auditar:

- cuándo una línea realmente organiza;
- cuándo la separación puede salir de espacio;
- cuándo la media crea el corte;
- cuándo una alineación distinta es suficiente;
- cuándo una ruta/costura puede conectar dos escenas;
- cuándo sí hace falta un borde fuerte.

## 3.6. Media insuficientemente integrada en interiores

Hay fotografías, portadas y material real, pero en varias familias se comportan como «imagen dentro de un bloque».

Preguntas de auditoría por imagen:

1. ¿qué papel editorial cumple?;
2. ¿es evidencia, protagonista, contexto o decoración?;
3. ¿necesita ratio natural?;
4. ¿debe romper gutter?;
5. ¿necesita crop diferente en 390/768/1440?;
6. ¿debe aparecer antes o después del texto en mobile?;
7. ¿su tamaño expresa la importancia adecuada?;
8. ¿es la mejor imagen disponible o solo la que ya estaba en el repo?;

## 3.7. Autor / identidad

La capa `v1-identity.css` mejora mucho la familia al convertir cards genéricas en ledgers. Aun así, en mobile varios layouts vuelven a una misma columna.

Oportunidades de exploración:

- retrato como presencia compositiva, no avatar + foto;
- cronología con fecha integrada en la escena;
- cambios de medida de bio;
- inserciones documentales reales;
- obra con jerarquía desigual;
- prensa y eventos con temporalidad más visible.

## 3.8. Cuaderno y artículos

La versión desktop del artículo dispone de TOC, folio y columna de lectura. En mobile:

- TOC se vuelve bloque normal;
- folio desaparece;
- cuerpo ocupa una columna;
- FAQs/end se apilan.

Es correcto funcionalmente, pero hay una oportunidad clara de conservar orientación mediante:

- etiqueta de progreso editorial;
- metadata compacta;
- secciones con cambios de medida;
- figuras con tratamiento más fuerte;
- notas/inserts que rompen el flujo de forma controlada;
- cierre visual de secciones sustantivas.

No debe convertirse cada H2 en una card.

## 3.9. Herramientas

La funcionalidad está bien resuelta y el diseño evita dashboards pesados.

El riesgo visual es que herramienta, resultados, explicación y siguiente paso compartan demasiado lenguaje.

Necesitamos que la página comunique claramente tres estados espaciales:

```text
1. tarea
2. resultado
3. contexto / metodología / siguiente paso
```

La interfaz funcional debe dominar mientras se usa; el contenido SEO no debe parecer la continuación indistinta del formulario.

## 3.10. Prensa y eventos

Los ledgers son adecuados. La oportunidad está en usar la naturaleza temporal/documental como firma:

- fecha;
- lugar;
- material real;
- estado;
- fuente;
- archivo.

No necesita cards de eventos ni timeline de app.

## 3.11. Libros

Las páginas de libro ya tienen una base diferenciada. La auditoría debe comprobar:

- si la portada adquiere suficiente presencia en mobile sin enterrar título/CTA;
- si el cambio entre ficha, sinopsis, fragmento y disponibilidad se percibe;
- si Samuel conserva dignidad propia sin imitar a Manecillas;
- si la media disponible se integra como objeto real;
- si la ficha técnica parece editorial, no ecommerce.

## 4. Auditoría instrumental que debe ejecutarse

## 4.1. Capture matrix

Capturar como mínimo:

- 320×568;
- 390×844;
- 430×932;
- 768×1024;
- 1024×768;
- 1440×900;
- 1728×1117;
- 667×375 landscape;
- 844×390 landscape.

Páginas piloto:

- Home;
- Manecillas;
- Samuel;
- Autor;
- Cuaderno;
- un artículo largo;
- Herramientas hub;
- una herramienta abierta;
- Prensa;
- Eventos;
- un directorio/ficha de editorial.

## 4.2. Geometry report

Extraer mediante Playwright/DevTools:

- bounding boxes de `main > section` y equivalentes;
- top/bottom gap;
- background/color efectivo;
- ancho útil;
- heading size/line-height;
- paragraph size/line-height;
- número de líneas de H1/H2;
- ancho de imagen;
- ratio visible;
- distancia media↔texto;
- número de hairlines visibles por pantalla;
- cambio de alineación entre escenas;
- viewport occupancy del primer bloque;
- overflow;
- sticky/fixed coverage.

El objetivo no es convertir diseño en números. Es detectar repeticiones invisibles a simple vista.

## 4.3. Long-scroll contact sheet

Generar una captura full-page por viewport y montar una tira reducida.

A escala pequeña deben percibirse:

- cambios de ritmo;
- zonas dominantes;
- media;
- silencios;
- cortes.

Si toda la página aparece como una franja gris/blanca de densidad homogénea, la jerarquía macro falla aunque cada bloque aislado se vea bien.

## 4.4. Grayscale test

Revisar capturas en escala de grises.

Pregunta: ¿la jerarquía sigue siendo reconocible sin color?

Si no, el diseño depende demasiado de superficie/acento.

## 4.5. Blur / squint test

Aplicar blur visual a la captura o verla reducida.

Debe seguir percibiéndose:

- protagonista;
- 2.º nivel;
- cortes de escena;
- media principal;
- cierre.

## 4.6. Typography-frequency test

Contar por una longitud aproximada de viewport:

- titulares display > X escala relativa al body;
- eyebrows;
- mayúsculas;
- CTAs;
- líneas divisorias.

No para imponer un máximo universal, sino para detectar saturación de señales.

## 5. Matriz de gravedad

### P0

- mobile no conserva suficiente jerarquía compositiva;
- falta sistema reproducible de observación visual real;
- falta captura comparable entre familias;
- falta validación en dispositivo real dentro del proceso visual.

### P1

- ritmo vertical uniforme;
- uso excesivo del mismo tipo de separador;
- media interior poco integrada;
- typography dominance en algunos mastheads;
- falta visual-regression gate centrado en diseño.

### P2

- refinamiento microtipográfico;
- continuidad de objetos entre páginas;
- motion de firma puntual;
- pruebas con usuarios de preferencias/claridad;
- automatización del design-evidence pack.

## 6. Qué NO concluye esta auditoría

No concluye que:

- haya que cambiar de tipografía;
- el blanco sea incorrecto;
- el azul actual sea incorrecto;
- haya que meter fondos alternos;
- haya que añadir cards;
- la Home deba copiarse a interiores;
- una herramienta generativa deba rediseñar la web;
- más animación implique más calidad.

La conclusión es más concreta:

> **La implementación debe recuperar la jerarquía definida por el sistema editorial cuando el espacio cambia, en lugar de limitarse a conservar el contenido dentro del viewport.**

## 7. Criterio de cierre

La auditoría se considera resuelta cuando podemos observar una captura móvil larga de cada familia y distinguir claramente, sin leer todos los textos:

- apertura;
- protagonista;
- escenas secundarias;
- transición;
- cierre;
- siguiente ruta.

Y cuando esa claridad se consigue sin recurrir a una plantilla repetitiva ni a decoración artificial.