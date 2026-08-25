# The Yale Review — «From the Archives»

Auditoría de referencia visual y editorial para `https://yalereview.org/from-the-archives`.

Fecha de inspección: 2026-08-25  
Tipo de documento: investigación / referencia clean-room  
Uso: informar decisiones de diseño de `davidportodiaz.com`; **no copiar DOM, CSS, JS, assets ni tipografías propietarias**.

---

## 0. Cómo leer esta auditoría

Este documento separa deliberadamente tres niveles de certeza para evitar convertir observaciones visuales en supuestos “valores exactos”:

- **A — verificado**: dato confirmado por la web actual, por una fuente oficial de The Yale Review/Yale o por el caso oficial de Pentagram.
- **B — observable**: patrón de estructura/jerarquía que se ve en la página actual y puede describirse con seguridad, aunque no dispongamos aquí del `computed style` exacto.
- **C — estimación de reproducción**: rango útil si queremos recrear el efecto visual en nuestro propio sistema; **no afirma que sea el valor CSS exacto de Yale Review**. Antes de convertirlo en token definitivo hay que medirlo con DevTools en el navegador local.

La intención es extraer principios y medidas reproducibles sin copiar implementación propietaria.

---

# 1. Fuentes y procedencia

## 1.1 Fuente primaria: página inspeccionada

`https://yalereview.org/from-the-archives`

La página actual presenta, en este orden semántico verificable:

1. header global;
2. título de página `From the Archives`;
3. pieza de vídeo destacada;
4. bloque `Archival Feature of the Week`;
5. una larga secuencia de piezas archivísticas y piezas de contexto `Annotating the Archives`;
6. una cita editorial de Meghan O’Rourke con `Read More` e imagen;
7. continuidad con más piezas de Virginia Woolf;
8. bloque `Browse` con filtros;
9. listado cronológico `From the Archives` con categoría, título, subtítulo, autor y fecha;
10. paginación;
11. footer global;
12. promoción persistente del número actual.

Este orden se ha verificado en el contenido actual indexado de la página.

## 1.2 Fuente oficial de identidad: Pentagram

Pentagram atribuye el rediseño de The Yale Review al equipo de Michael Bierut. El caso oficial confirma:

- nuevo sistema editorial y nueva plantilla;
- voluntad de acercar la revista a la escala y tactilidad de un libro tradicional;
- incorporación de arte/elementos visuales como parte estructural del sistema;
- **GT Cinetype** para logo/nameplate;
- texto en la tipografía serif personalizada de Yale diseñada por Matthew Carter;
- expansión deliberada hacia una experiencia digital.

## 1.3 Fuente oficial Yale sobre tipografía

Yale confirma que su serif institucional fue diseñada por **Matthew Carter** y que la familia histórica `YaleNew` evolucionó a `Yale 2024`. Para tamaños grandes existe `Yale Display`, de contraste más alto, serifas más afiladas y tracking más cerrado.

Esto permite distinguir con seguridad dos roles tipográficos de la identidad:

- voz de marca/display geométrica: GT Cinetype;
- voz editorial/lectura: Yale / YaleNew / descendientes actuales de la familia Yale.

No asumimos que todos los elementos de la web actual carguen exactamente la versión Yale 2024: el dato seguro es la familia/linaje tipográfico y su función.

## 1.4 Intención editorial declarada por The Yale Review

En el lanzamiento digital, Meghan O’Rourke y Yale describieron una experiencia buscadamente:

- calmada;
- contemplativa;
- sin pop-ups ni sobrecarga;
- sin sensacionalismo;
- pensada para hacer sentir que hay “un tesoro de gran escritura a un clic”.

Esta declaración es importante porque explica muchas decisiones visuales: baja densidad de chrome, primacía del texto, reglas en vez de cajas, jerarquía editorial y poca decoración instrumental.

---

# 2. ADN visual general

## 2.1 La página se comporta como una revista, no como una app

**B — observable.**

No hay una gramática principal de cards redondeadas, sombras, elevaciones, pills o módulos SaaS. El sistema se apoya en:

- tipografía;
- alineación;
- cambios de escala;
- reglas finas;
- agrupaciones editoriales;
- aire;
- repetición de metadatos;
- imágenes/arte como contrapunto.

El resultado es “plano” en términos de UI, pero no plano visualmente: la profundidad la da la relación entre tipos, blancos, líneas, imágenes y densidades.

### Lección aplicable

Para nuestro proyecto, si queremos acercarnos a este nivel de sobriedad editorial, la prioridad no debe ser “añadir componentes”, sino **reducir la necesidad de contenedores** y dejar que la retícula y la tipografía expliquen la jerarquía.

---

# 3. Paleta cromática

## 3.1 Paletas oficiales vinculadas al rediseño

**A — verificado por Pentagram Archive.**

Pentagram publica para piezas del proyecto The Yale Review, entre otras, estas paletas:

### Paleta A

- `#0E0F0D` — negro verdoso / tinta profunda
- `#B4B3B2` — gris cálido medio
- `#565E57` — gris verde oscuro
- `#888674` — oliva grisáceo
- `#648376` — verde grisáceo
- `#CFA875` — ocre / arena
- `#678D88` — verde azulado apagado
- `#EDEDEC` — blanco grisáceo

### Paleta B

- `#BCBBBC` — gris claro
- `#131110` — negro cálido
- `#5D544F` — marrón grisáceo oscuro
- `#956F59` — arcilla
- `#D6661A` — naranja quemado
- `#D0935B` — ocre tostado
- `#E7D4B0` — crema arena
- `#FAFCFC` — blanco frío casi puro

Estas paletas son **del proyecto de identidad**, no una extracción garantizada del CSS actual de `/from-the-archives`.

## 3.2 Lectura cromática de la página web

**B/C.** La web actual mantiene una base extremadamente neutra donde la tinta y el fondo dominan y el color aparece como acento/editorial, no como superficie decorativa constante.

Patrón que interesa:

- fondo principal muy claro;
- texto principal casi negro;
- líneas en gris claro/medio;
- color reservado a momentos concretos, arte, promoción o identidad;
- contraste alto para títulos, pero sin recurrir a negros absolutos sobre blancos clínicos en todos los bloques.

### Rango clean-room recomendable si se quisiera reproducir el efecto

**C — no es copia CSS.**

- paper: `#F7F6F1` – `#FBFAF6`
- ink: `#11110F` – `#1A1916`
- rule: `#C9C7C0` – `#D8D5CC`
- muted: `#6E6B63` – `#858176`
- accent muted teal: entorno `#648376` / `#678D88`
- warm accent: entorno `#CFA875` / `#D0935B`
- strong accent when justified: entorno `#D6661A`

No deberíamos importar estos hex como tokens del proyecto sin pasar antes por nuestro sistema V1/V6 y comprobar contraste WCAG.

---

# 4. Tipografía

## 4.1 Logo / nameplate

**A — verificado.**

Pentagram confirma **GT Cinetype** para el logo/nameplate de The Yale Review. Su rasgo conceptual principal es que las letras se construyen con segmentos rectos que el ojo interpreta como curvas.

Efecto visual:

- lineal;
- ligero;
- distintivo a gran tamaño;
- alto reconocimiento sin un bloque pesado de marca;
- mezcla de modernidad técnica y rareza histórica.

### Qué NO hacer

No debemos instalar, copiar ni recrear GT Cinetype sin licencia. Tampoco construir un clon vectorial del logo.

### Qué sí podemos aprender

El logo funciona porque **contrasta** con el serif editorial. No intenta que marca y contenido hablen con la misma voz.

## 4.2 Texto editorial

**A — verificado en el proyecto de identidad.**

Pentagram especifica el serif personalizado de Yale diseñado por Matthew Carter para el texto. Yale identifica esa familia como Yale/YaleNew y su evolución actual Yale 2024.

Características del sistema serif que explican su utilidad:

- herencia old-style;
- alta legibilidad;
- modulación clara;
- serifas con personalidad;
- suficiente autoridad para titulares;
- buena lectura en texto largo.

## 4.3 Yale Display

**A — fuente institucional Yale.**

Yale describe su Display como:

- serifas más afiladas;
- mayor contraste entre trazos gruesos y finos;
- x-height alta;
- letter-spacing más estrecho;
- optimizada para tamaños superiores a unas 24 pt.

Esto encaja con la sensación visual de grandes títulos editoriales tensos y compactos.

## 4.4 Jerarquía tipográfica observada

**B.**

La página repite un sistema coherente:

1. **H1 de página**: gran display serif; muy por encima de cualquier metadata.
2. **H2 de bloque** (`Archival Feature of the Week`, `Browse`, `From the Archives`): display serif de segundo nivel.
3. **categoría/kicker** (`From the Archives`, `Annotating the Archives`, `Video`, `Essays`): pequeño, funcional y repetible.
4. **títulos de pieza**: serif de display o semidisplay, con peso no excesivamente bold.
5. **deck/subtítulo**: serif más pequeño, todavía editorial.
6. **autor**: jerarquía propia, separada del deck.
7. **fecha**: secundaria y fría; nunca compite con título/autor.

### Regla clave

No resuelven la jerarquía únicamente con “más bold”. Cambian **escala, posición, ancho de columna y aire**.

---

# 5. Retícula y geometría

## 5.1 Principio general

**B.**

La página no se percibe como una sucesión de componentes aislados. Se percibe como una **superficie editorial continua**.

Hay tres comportamientos de ancho:

- zonas de lectura/títulos relativamente contenidas;
- composiciones destacadas que ocupan más anchura;
- zonas de archivo/listado que se vuelven más regulares y sistemáticas.

Esto crea cambio de ritmo sin abandonar la misma retícula base.

## 5.2 Márgenes exteriores

**C — estimación de reproducción.**

En desktop, el sistema visual sugiere gutters generosos pero no extremos. Para reproducir la sensación:

- viewport 1440: gutter útil aproximado `40–72px`;
- viewport 1024: `28–48px`;
- mobile 390: `16–24px`.

El punto no es el número exacto, sino que **todos los bloques tocan las mismas líneas maestras**. La consistencia de borde izquierdo es más importante que maximizar aire.

## 5.3 Ancho de contenido

**C.**

La experiencia parece trabajar mejor con un contenedor editorial amplio —aprox. 1180–1320 px en desktop— y columnas internas que reducen el ancho de lectura.

No hay una “card max-width 1200” repetida; hay una retícula sobre la que los bloques usan spans diferentes.

## 5.4 Columnas

**B/C.**

La página combina:

- 1 columna para encabezados y momentos editoriales fuertes;
- 2 columnas para relaciones de pieza principal + contexto/acompañamiento;
- composiciones multicolumna para grupos de archivo;
- 1 columna regular en el listado cronológico inferior.

El interés está en que no todas las piezas reciben el mismo tamaño.

---

# 6. Líneas y divisores

## 6.1 Rol de las reglas

**B.**

Las líneas son uno de los recursos fundamentales de jerarquía. Sustituyen muchas funciones que otras webs resolverían con cajas o backgrounds.

Se emplean como:

- separador de secciones;
- límite superior/inferior de grupos;
- refuerzo de columnas;
- separador entre items;
- elemento de ritmo.

## 6.2 Grosor

**C.**

La mayor parte del lenguaje debería reproducirse con hairlines de aproximadamente `1px`, reservando reglas de `2px` o mayor contraste para cabeceras/rupturas importantes.

La línea no debe parecer decorativa; tiene que coincidir con una transición semántica.

## 6.3 Color de línea

**C.**

Nunca la trataría como negro absoluto. Funciona mejor en un gris cálido con contraste suficiente para organizar pero no para competir con la tinta.

---

# 7. Cabecera global

## 7.1 Arquitectura

**A/B — verificada en la página actual.**

La cabecera expone dos capas de navegación/conversión:

- marca `The Yale Review`;
- `Support Us`, `Subscribe`, `Donate`;
- bloque `About Us` con accesos como Our Story, Subscriptions, Submissions, Fellowships, Newsletters;
- buscador;
- navegación editorial por familias: Nonfiction, Essays, Criticism, Fiction, Poetry, Poem of the Week, Interviews, Archives, Folios, Issues, etc.

La navegación no intenta esconder el tamaño real de la publicación. Hay una arquitectura editorial extensa y explícita.

## 7.2 Lección UX

La densidad del header es aceptable porque:

- el contenido está agrupado por sentido;
- la marca es visualmente dominante;
- acciones económicas (`Subscribe`, `Donate`) están separadas del catálogo editorial;
- búsqueda existe como salida directa.

Para David Porto esto respalda separar **identidad / navegación / conversión**, en vez de poner todas las acciones al mismo nivel.

---

# 8. Título de página

## 8.1 `From the Archives`

**B.**

El título no aparece dentro de una tarjeta, hero ilustrado o gran bloque de color. La página empieza por establecer nombre/territorio editorial y enseguida entra en contenido.

La marca de sección funciona por:

- gran escala;
- serif display;
- blanco alrededor;
- alineación con la retícula.

### Lección

Un H1 editorial fuerte puede sustituir un hero artificial. Si una sección ya tiene identidad y contenido potente, no necesita “hero por obligación”.

---

# 9. Pieza de vídeo de apertura

## 9.1 Función

**A/B.**

Tras el H1 aparece una pieza etiquetada `Video`: `Bringing The Yale Review's Archives to Life`.

Eso convierte el comienzo de página en una **entrada editorial curada**, no en un listado.

## 9.2 Jerarquía

- tipo de contenido pequeño (`Video`);
- título dominante;
- subtítulo/descripción;
- recurso audiovisual como pieza real, no como decoración.

La página comunica “archivo vivo” desde el primer bloque.

---

# 10. `Archival Feature of the Week`

## 10.1 Cambio de ritmo

**B.**

Es la primera ruptura editorial grande después del vídeo. Funciona como “dossier de portada” dentro del territorio Archivo.

Contiene piezas archivísticas y piezas explicativas, por ejemplo:

- obra primaria (`From the Archives`);
- anotación/contexto (`Annotating the Archives`);
- título;
- deck cuando existe;
- autor.

## 10.2 Alternancia de fuente primaria y comentario

Este es un patrón editorial especialmente valioso: no presentan el archivo como una base de datos, sino como una conversación entre:

- pieza histórica;
- curaduría contemporánea;
- contexto;
- autoría.

Es una forma de dar profundidad sin añadir widgets.

---

# 11. Microarquitectura de cada pieza

**B — repetida a lo largo de la página.**

Orden típico:

1. categoría;
2. título;
3. deck si existe;
4. autor;
5. separador/regla cuando corresponde.

En el listado inferior se añade:

6. fecha.

## 11.1 Categoría

- pequeña;
- constante;
- no parece botón;
- actúa como etiqueta editorial, no como chip.

## 11.2 Título

- elemento más visible del item;
- varias líneas permitidas;
- no se fuerza truncado;
- se deja que el ritmo tipográfico decida la altura.

## 11.3 Deck

No todas las piezas lo tienen. Eso evita relleno artificial. Cuando existe, explica el ángulo y crea una segunda velocidad de lectura.

## 11.4 Autor

Se separa suficientemente del título/deck para que la autoría sea escaneable.

## 11.5 Fecha

En el bloque `Browse` aparece después de autoría; visualmente es metadata terminal.

---

# 12. Ritmo y densidad

## 12.1 No hay una única densidad de sección

**B.**

La página alterna:

- piezas protagonistas;
- pequeños grupos de piezas;
- agrupaciones temáticas de un autor;
- interludios editoriales;
- listado cronológico final.

Esto evita el efecto “10 cards idénticas”.

## 12.2 El blanco no es vacío

Se usa como herramienta para:

- separar ideas;
- marcar cambios de escala;
- hacer legibles los títulos largos;
- permitir que una línea horizontal tenga peso.

### Aplicación

En nuestro proyecto hay que distinguir entre “aire editorial útil” y “espacio SaaS sin contenido”. Yale Review usa el primero: el blanco siempre ayuda a una relación tipográfica o semántica.

---

# 13. Agrupaciones temáticas

**A/B.**

En la página actual se observan cadenas temáticas: política americana, Thom Gunn, Thomas Mann, Virginia Woolf, etc.

La repetición de autor/categoría y los separadores convierten esas cadenas en mini-dossiers sin necesidad de encabezados gigantes o fondos distintos para cada uno.

### Principio

La proximidad + secuencia editorial puede sustituir a un contenedor visual.

---

# 14. Cita editorial / interludio

La página introduce una cita de Meghan O’Rourke sobre la revista como práctica social y comunal, junto a `Read More` e imagen.

**B.** Este bloque hace tres cosas:

- rompe la monotonía de listados;
- recuerda la tesis editorial del archivo;
- introduce una imagen en un entorno predominantemente tipográfico.

Es un **interludio con propósito**, no una llamada promocional arbitraria.

### Aplicación directa

Nuestros interludios deberían responder a la misma pregunta: “¿qué argumento editorial recuerda o conecta este bloque?”, no “¿dónde ponemos otro banner?”.

---

# 15. Imágenes

## 15.1 Función

**A/B.**

El rediseño de Pentagram incorpora deliberadamente arte y elementos visuales. En la web, las imágenes funcionan como:

- evidencia/documento;
- portada/arte de issue;
- ruptura de ritmo;
- contexto de una pieza;
- soporte de una promoción editorial.

No son fondos decorativos genéricos.

## 15.2 Tratamiento

**B/C.**

La gramática general favorece:

- bordes rectos;
- proporciones de imagen respetadas;
- ausencia de grandes radios decorativos;
- captions/metadatos discretos;
- imagen alineada con retícula.

### Aplicación

Esto valida una dirección que ya estamos usando: imágenes con tratamiento editorial, no “thumbnails de producto” redondeadas.

---

# 16. `Browse`: cambio de modo

## 16.1 La página cambia de curaduría a exploración

**A/B.**

Tras el recorrido editorial aparece `Browse` con controles de filtro y un listado regular.

Es una decisión UX muy buena: primero **inspira**, después **permite buscar**.

No obliga al visitante a empezar por filtros antes de entender el valor del archivo.

## 16.2 Controles

La interfaz expone selects y botón `Apply`.

Principio relevante:

- controles claramente instrumentales;
- separados del contenido;
- no convierten toda la página en una app de búsqueda;
- el contenido sigue siendo protagonista.

---

# 17. Listado inferior

**A/B.**

El listado inferior repite una plantilla estable:

- categoría;
- título;
- deck;
- autor;
- fecha.

Este es el lugar donde la regularidad es útil porque el objetivo cambia de descubrimiento curado a consulta.

### Regla de diseño

**Irregularidad arriba, regularidad abajo.**

Es una de las ideas más transferibles de la página.

---

# 18. Paginación

La página expone páginas numéricas (`1`, `2`, `3`, etc.).

**B.** No intenta ocultar el tamaño del archivo mediante infinite scroll. Esto favorece:

- orientación;
- URLs estables;
- retorno al punto de exploración;
- accesibilidad;
- indexabilidad.

Para un sitio editorial/archivo, la paginación explícita es una ventaja, no una antigüedad.

---

# 19. Footer

**A/B.**

El footer incluye:

- About Us;
- Newsletters;
- Events;
- Book Prize;
- Store;
- Donate;
- Advertise;
- Contact;
- redes sociales;
- copyright;
- Terms of Service;
- Privacy Policy;
- Accessibility Notice;
- Artificial Intelligence Policy.

La amplitud refuerza la idea de que el footer es una **segunda arquitectura de información**, no un cierre decorativo.

### Aplicación

Nuestro footer debe seguir funcionando como mapa de respaldo y no depender del menú JS para descubrir contenido.

---

# 20. Promoción del número actual

**A/B.**

La página termina/convive con una promoción del issue actual (`Our Summer Issue`) con:

- descripción breve;
- `Purchase`;
- `Read Online`.

Está fuera del flujo principal del archivo, pero conectado a la lógica comercial de la revista.

### Lo importante

La conversión llega **después de haber dado valor editorial** y se relaciona con el producto central de la publicación.

---

# 21. Jerarquía de enlaces y acciones

## 21.1 Enlaces editoriales

La mayoría de títulos son enlaces sin necesidad de botones envolventes.

## 21.2 Botones reales

Se reservan para acciones claramente transaccionales o de aplicación:

- Subscribe;
- Donate;
- Apply;
- Purchase;
- Read Online.

### Principio

No convertir cada navegación en botón. El estilo del control explica su semántica.

---

# 22. Bordes, radios y sombras

**B/C.**

La identidad observada favorece:

- radios mínimos o nulos;
- sombras prácticamente ausentes como gramática editorial;
- separación mediante hairlines;
- bloques definidos por retícula, no por elevación.

Esto aporta una sensación impresa/papel sin necesidad de texturas visuales pesadas.

---

# 23. Motion

La declaración editorial de Yale favorece calma y ausencia de distracciones. Aunque esta auditoría no afirma valores de duración concretos sin `computed style`, el sistema conceptual sugiere:

- motion subordinado;
- nada de pulsos permanentes;
- nada que compita con lectura;
- transición solo cuando ayuda a comprender navegación/estado.

Para nuestra web: conservar `prefers-reduced-motion` y evitar añadir animaciones por imitación estética.

---

# 24. Responsive: comportamiento esperado del sistema

## 24.1 Principio

**B/C.**

La experiencia editorial no debería convertirse en mini desktop. En móvil, las prioridades son:

- una columna;
- conservar la jerarquía de categoría → título → deck → autor → fecha;
- reglas de ancho completo dentro del gutter;
- botones/inputs con targets adecuados;
- navegación global condensada sin eliminar destinos;
- imágenes a ancho de columna;
- títulos sin truncado.

## 24.2 Valores clean-room que conviene medir/probar en nuestra adaptación

- gutter móvil: 16–24 px;
- touch target mínimo: 44 px;
- body: 17–20 px según serif real;
- line-height lectura: 1.45–1.65;
- títulos: usar `clamp()` y medida en `ch`, no tamaños fijos por dispositivo.

De nuevo: son rangos de reproducción, no valores extraídos del CSS de Yale Review.

---

# 25. Accesibilidad y legibilidad

The Yale Review enlaza explícitamente una `Accessibility Notice` desde el footer. En la experiencia observada hay varias decisiones que favorecen accesibilidad aunque deban medirse con herramientas si quisiéramos certificarlas:

- estructura de headings clara;
- enlaces textuales descriptivos;
- paginación explícita;
- filtros con controles nativos;
- ausencia de sobrecarga visual;
- texto sin truncado agresivo;
- predominio de alto contraste tinta/papel.

No se afirma aquí conformidad WCAG de la web de Yale Review; solo se documentan patrones observados.

---

# 26. SEO / arquitectura editorial visible

**A/B.**

La estructura favorece indexación porque:

- cada pieza tiene URL propia;
- categorías son rutas reales;
- el archivo es navegable;
- existe paginación;
- las páginas de issue tienen tabla de contenidos;
- las piezas archivísticas se conectan con piezas contemporáneas;
- metadata visible incluye autor y fecha.

La UX y la indexación trabajan en la misma dirección.

---

# 27. Lo más valioso para `davidportodiaz.com`

No copiar la apariencia de Yale Review. Adoptar estos principios:

1. **Jerarquía sin cards.** Resolver más cosas con tipo + retícula + reglas.
2. **Irregularidad curada antes del listado regular.** Primero editorializar; después ofrecer archivo/filtros.
3. **Categoría pequeña, título fuerte, deck opcional, autor visible, fecha secundaria.**
4. **Líneas como estructura**, no como decoración.
5. **Imagen documental/editorial**, no thumbnail genérico.
6. **Interludio con tesis**, no banner de relleno.
7. **Conversión después de valor.**
8. **Footer como arquitectura alternativa.**
9. **Paginación estable para archivos extensos.**
10. **No truncar títulos literarios.**
11. **No homogeneizar todos los contenidos al mismo tamaño.**
12. **No usar color para suplir falta de jerarquía.**
13. **Marca y lectura pueden usar voces tipográficas distintas.**
14. **Calma como feature UX.**

---

# 28. Qué NO copiar

- GT Cinetype o cualquier fuente propietaria sin licencia.
- el logotipo/nameplate o su construcción.
- CSS/JS/DOM exacto.
- composición 1:1 de módulos.
- paleta completa como si fuera nuestra identidad.
- textos, imágenes o assets editoriales.
- medidas exactas inferidas sin comprobación.

La adaptación debe ser clean-room y pasar por nuestros tokens/componentes.

---

# 29. Comparación conceptual con nuestro sistema actual

## Ya alineado

- papel cálido / tinta;
- reglas editoriales;
- tipografía serif como voz principal;
- navegación por territorios;
- footer como red de respaldo;
- Home con agrupaciones de peso desigual;
- interludios editoriales;
- imágenes sin estética SaaS;
- preferencia por composición frente a card-grid.

## Aspectos a revisar cuando vuelva a tocar diseño, no como blocker prelaunch

- si nuestros listados inferiores mantienen una regularidad tan clara como Yale Review;
- si categorías/decks/autores/fechas tienen roles tipográficos suficientemente distintos;
- si usamos demasiados contenedores donde bastaría una regla;
- si cada interludio tiene una tesis editorial real;
- si archivos y Cuaderno deberían usar paginación más explícita a medida que crezcan;
- si la conversión aparece demasiado pronto en algunas familias.

No se propone reabrir ahora el release por estos puntos.

---

# 30. Ficha de redline clean-room para futuras pruebas

Estos valores son **punto de partida de laboratorio**, no extracción de Yale Review:

| Variable | Rango de prueba |
|---|---:|
| `--ref-page-gutter-mobile` | 16–24px |
| `--ref-page-gutter-tablet` | 28–48px |
| `--ref-page-gutter-desktop` | 40–72px |
| `--ref-layout-max` | 1180–1320px |
| `--ref-rule` | 1px |
| `--ref-rule-strong` | 2px |
| `--ref-body-size` | 17–20px |
| `--ref-body-leading` | 1.45–1.65 |
| `--ref-metadata-size` | 11–14px |
| `--ref-title-measure` | 10–18ch según nivel |
| `--ref-touch-min` | 44px |

No copiar estos valores directamente a producción; primero compararlos con V1/V6, WCAG, responsive y contenido real.

---

# 31. Checklist de observación DevTools para una segunda pasada local

Si se quiere convertir esta referencia en una medición de precisión, abrir la página en navegador local y registrar:

1. familia real cargada por cada nivel tipográfico;
2. `font-size`, `line-height`, `font-weight`, `letter-spacing` de H1/H2/H3/body/metadata;
3. ancho máximo del wrapper a 1440/1728;
4. gutters exactos a 390/768/1024/1440/1728;
5. número de columnas y gaps del bloque destacado;
6. grosor/color exactos de reglas;
7. background y color de tinta computados;
8. dimensiones de imágenes y `object-fit`;
9. estados hover/focus de enlaces;
10. comportamiento de header al scroll;
11. breakpoints reales;
12. orden/reflow móvil;
13. estilos de selects y botón `Apply`;
14. paginación activa/hover/focus;
15. footer desktop/mobile;
16. promo de issue actual;
17. cualquier sticky/fixed;
18. `prefers-reduced-motion`;
19. contraste;
20. zoom 200–400%.

Hasta completar esa medición, este documento mantiene separados los datos A/B/C y no finge exactitud CSS.

---

# 32. Fuentes consultadas

- Página actual: https://yalereview.org/from-the-archives
- Home actual: https://yalereview.org/
- About / Our Story: https://yalereview.org/about
- Back Issues: https://yalereview.org/back-issues
- Annotating the Archives: https://yalereview.org/annotating-the-archives
- Editor's Note del lanzamiento digital: https://yalereview.org/article/editors-note
- Yale News sobre el lanzamiento digital: https://news.yale.edu/2021/06/28/tyr-gives-readers-digital-space-read-and-contemplate
- Pentagram — The Yale Review: https://www.pentagram.com/work/the-yale-review/story
- Pentagram Archive — paletas del proyecto: https://www.pentagram.com/archive/item/28384 y https://www.pentagram.com/archive/item/28383
- Yale Identity — Yale Typefaces: https://yaleidentity.yale.edu/core-identity-elements/yale-typefaces

---

# 33. Conclusión

La lección principal de `From the Archives` no es una combinación de colores ni una fuente concreta. Es una disciplina de edición visual: **la página cambia de densidad y jerarquía sin cambiar de idioma gráfico**.

Todo parece pertenecer a la misma publicación porque se mantienen constantes las reglas maestras —tipografía, alineación, tinta, líneas, metadatos y ritmo— mientras cada conjunto de contenido puede tener un peso diferente.

Para `davidportodiaz.com`, esa es la parte transferible y valiosa: una web puede ser variada, larga y rica sin sentirse inconsistente si la arquitectura visual permanece estable. La referencia refuerza la dirección editorial ya adoptada, pero no justifica abrir un rediseño nuevo antes del lanzamiento.