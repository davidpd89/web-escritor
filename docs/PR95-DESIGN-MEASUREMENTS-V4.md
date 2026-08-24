# PR95 — Sistema editorial V4: medidas, navegación y assets

Fecha de cierre de diseño: 24/08/2026.

Referencias funcionales y visuales estudiadas:
- London Review of Books — https://www.lrb.co.uk/
- MUBI Notebook — https://mubi.com/es/notebook

Este documento no pretende copiar CSS, branding ni tipografías propietarias. Extrae dos principios y fija una implementación propia para davidportodiaz.com:

1. **LRB**: densidad editorial, jerarquía basada en tipografía/reglas/papel y navegación global + navegación local persistente.
2. **MUBI Notebook**: ritmo de imagen editorial, entrada por categoría/título/autor o contexto y fotografías que separan territorios sin convertir la web en una landing de tarjetas.

Las cifras siguientes son el contrato de nuestra web. No son una afirmación de que LRB o MUBI utilicen exactamente esos píxeles.

---

## 1. Cabecera global

### Escritorio ≥ 900 px

| Elemento | Medida cerrada |
|---|---:|
| Utility header | **50 px** de alto |
| Área táctil Asistente/Home/Menu | **44 × 44 px mínimo** |
| Comprar | **36 px** de alto visible, dentro de barra de 50 px |
| Masthead Home | aprox. **102–112 px** según logo real |
| Logo central | ancho máx. **800 px**, alto máx. **86 px** |
| Nav Home | **40 px** de alto |
| Texto nav | **0,82 rem** (~13 px) |
| Submenú | **238 px mínimo**, 320 px máximo |
| Fila submenú | **38 px mínimo** |
| Puente hover menú→submenu | **8 px** |

Estado inicial de Home: utility + masthead + nav permanecen como una unidad editorial sticky.

Estado compacto: tras superar la altura real del masthead, masthead/nav se retiran visualmente y queda utility header + hamburger. No hay salto de layout porque se transforma la capa interior en lugar de reducir bruscamente el contenedor.

### Tablet 640–899 px

- Utility: **52 px**.
- Hamburger visible desde el inicio además de la navegación editorial.
- Nav Home: **40 px**.
- Texto: **0,78 rem**.
- El nav no se convierte en tarjetas ni botones grandes.
- Los submenús siguen accesibles por teclado/touch mediante disclosure.

### Teléfono ≤ 639 px

- Utility: **54 px**.
- Home muestra logo + utility/hamburger.
- Los cinco territorios horizontales se ocultan: no se fuerzan cinco palabras en 320–390 px.
- La navegación global pasa a `Explorar`, que abre desde la izquierda.
- Las páginas interiores mantienen una barra contextual horizontal de **40 px**, desplazable lateralmente si los destinos no caben.

Motivo: en móvil es preferible una navegación global clara mediante hamburger a reducir la tipografía a tamaños inadecuados o provocar overflow.

---

## 2. Navegación local persistente

La navegación local se deriva de la IA existente en `data/navigation.json`. No crea una segunda arquitectura paralela.

### Familias

**Obras**
- Todas las obras
- Las manecillas del recuerdo
- Samuel entre mundos

**Las manecillas del recuerdo**
- La novela
- Fragmentos
- Ficha de prensa

**Samuel entre mundos**
- El libro
- Capítulo 1
- Noveris
- Club de lectura
- Guía imprimible

**Cuaderno**
- Archivo
- Temas
- Recomendaciones

**Herramientas**
- Herramientas
- Editoriales
- Convocatorias
- Metodología

**Autor**
- Autor
- Premios
- Eventos
- Prensa

**Prensa y agenda**
- Prensa
- Eventos
- Ferias
- Premios

### Comportamiento

- Altura desktop: **42 px**.
- Altura mobile: **40 px**.
- Sticky inmediatamente debajo del utility header.
- El destino actual usa `aria-current="page"`.
- Hover/focus cambia el tono de papel, no mueve la pieza.
- En móvil: overflow horizontal deliberado, sin scrollbar visible; el destino activo se lleva al área visible.
- No aparece en Home porque allí ya existe la navegación editorial principal.
- No aparece en páginas legales/sistema que no pertenecen a una familia editorial.

Colores de familia:
- Manecillas → rosa empolvado.
- Samuel/Prensa → azul editorial.
- Herramientas → salvia.
- Obras/Cuaderno → arena/papel.
- Autor → rosa suave.

---

## 3. Escala tipográfica

La web deja de usar tamaño como sustituto de jerarquía. Instrument Serif, Newsreader y Manrope ya están self-hosted; se reutilizan.

| Uso | Familia | Rango |
|---|---|---:|
| UI / metadata | Manrope | 11–13 px |
| Texto normal | Newsreader/Manrope según componente | 16–17 px |
| Lead | Newsreader | 16–19 px |
| H3 editorial | Instrument Serif | 20–27 px |
| H2 sección | Instrument Serif | 26–38 px |
| H1 página interior | Instrument Serif | 33–52 px |
| H1 libro | Instrument Serif | 34–57 px |
| Título banner Home | Instrument Serif | 34–58 px |

Reglas:
- No volver a `6rem–8rem` para H1 de páginas interiores.
- Line-height de titulares: **0,95–1,08**.
- Texto de lectura: **1,46–1,58**.
- Anchura de lectura: objetivo **~68ch**.
- Metadata siempre claramente menor; la separación se consigue con peso/espacio/color, no con mayúsculas gigantes.

---

## 4. Banners Home: rectángulo final antes de tener fotos

El diseño puede mergearse en staging sin fotografías definitivas porque el hueco tiene tamaño final y etiqueta el asset que falta.

### Fuente maestra

**2400 × 900 px · WebP · relación 8:3**.

Nombres definitivos:
- `assets/banners/manecillas-home-banner.webp`
- `assets/banners/samuel-home-banner.webp`
- `assets/banners/memoria-tierras-norte-home-banner.webp`
- `assets/banners/herramientas-home-banner.webp`

También se acepta `.jpg` con el mismo nombre base.

### Zona segura de composición

Una sola imagen debe sobrevivir a desktop y móvil:
- sujeto/objeto principal dentro del **58 % central horizontal**;
- contenido esencial dentro del **70 % central vertical**;
- no incluir texto imprescindible dentro de la fotografía;
- no colocar caras/objetos clave en los extremos laterales;
- el texto se mantiene como HTML accesible.

### Altura de render

| Viewport | Altura banner |
|---|---:|
| ≥ 1440 | **400 px** |
| 1200–1439 | **360 px** |
| 900–1199 | **320 px** |
| 640–899 | **290 px** |
| 350–639 | **250 px** |
| ≤ 349 | **230 px** |

`object-fit: cover` + `object-position: center center`.

Mientras falte el asset definitivo:
- se mantiene exactamente la altura final;
- se ve el fondo cromático del territorio;
- aparece arriba a la derecha `Banner pendiente · … · 2400 × 900 px · foco central`;
- un mockup vertical o un OG temporal NO se considera banner final y se oculta visualmente;
- cuando aparece un archivo desde `/assets/banners/`, el placeholder desaparece sin reflow.

---

## 5. Otros formatos de imagen

### Portadas

- Fuente preferida: **1200 × 1800 px**, relación **2:3**.
- No forzar crop: `object-fit: contain` cuando se muestra el libro completo.
- Display típico desktop: **240–320 px** de ancho.
- Display móvil: **180–240 px**.

### Retrato de autor

- Fuente: **1800 × 2400 px**.
- Relación: **3:4**.
- Hueco CSS actual: `aspect-ratio:3/4`.
- Sin esquinas redondeadas.

### Retrato de prensa

- Fuente: **1600 × 2000 px** o superior.
- Relación: **4:5**.
- Hueco CSS: `aspect-ratio:4/5`.

### Fotos de evento

- Fuente recomendada: **1500 × 2000 px** (3:4) para verticales.
- Si una foto es horizontal: **1800 × 1200 px** (3:2).
- El grid conserva la foto como material documental; no se aplica zoom decorativo agresivo.

### Imagen editorial de artículo

- Fuente recomendada: **1600 × 900 px** (16:9).
- Si la fotografía tiene valor documental y otra proporción, se conserva la proporción original en el cuerpo del artículo.

---

## 6. Ritmo Home

Secuencia cerrada:

1. Banner Manecillas.
2. Cluster 1+2 Manecillas.
3. Interludio Cuaderno.
4. Banner Samuel.
5. Cluster 1+2 Samuel.
6. Banner La memoria de las tierras del norte.
7. Cluster 1+2 antología/autor.
8. Banner Herramientas.
9. Cluster Herramientas.
10. Eventos.
11. Instalar web.
12. FAQ/newsletter ya existentes.
13. Footer.

Desktop cluster: columna principal ~50 % + dos piezas secundarias ~25 % + 25 %.
Tablet: principal completa y secundarias 50/50 cuando el ancho lo aconseje.
Mobile: una sola columna, sin mosaicos apretados.

No más de una pieza de color protagonista por cluster.

---

## 7. Hover, foco y tacto

Principio: **cambiar papel, no hacer saltar la interfaz**.

- No `translateY` de tarjetas.
- No sombras grandes de ecommerce.
- No escalado de titulares.
- Nav/subnav: azul editorial en hover/focus salvo color de familia.
- Cuaderno, themes, ledgers, relacionadas: iluminación tenue con el color de familia.
- Herramientas: salvia.
- Press/autor: rosa/azul según contexto.
- `:focus-visible` mantiene el foco AA ya existente.
- En dispositivos sin hover no se aplican estados dependientes de puntero.
- `prefers-reduced-motion` elimina transiciones.

---

## 8. Páginas interiores: patrón común

No se intenta convertir todas las páginas en una plantilla idéntica. Comparten un esqueleto de publicación:

1. Utility header.
2. Barra contextual si pertenece a familia.
3. Breadcrumb pequeño.
4. Masthead compacto: coordenada/eyebrow → H1 → lead → acciones.
5. Cuerpo propio de la familia.
6. Continuidad/relacionados cuando procede.
7. Newsletter contextual cuando procede.
8. Footer global.

Las familias mantienen identidad:
- libros → portada, metadatos, texto, fragmentos;
- Cuaderno → archivo/crónica/lectura;
- Herramientas → filtro + utilidades;
- Autor → retrato + biografía/trayectoria;
- Prensa → fichas, material descargable y datos verificables.

La textura común se consigue con papel, rules, tipografía y navegación, no obligando a cada página a utilizar las mismas cards.

---

## 9. Breakpoints de aceptación

Revisar siempre:
- **1728 × 1000**
- **1440 × 900/1000**
- **1024 × 768/900**
- **768 × 1024**
- **390 × 844/900**
- **320 × 800/900**
- landscape **844 × 390**
- zoom de texto/navegador **200 %**

En todos:
- sin scroll horizontal accidental;
- hamburger accesible;
- submenú desktop permite bajar el ratón hasta las opciones sin cerrarse;
- navegación contextual no tapa contenido;
- destino activo visible;
- banners no cambian altura al entrar la foto;
- foco visible;
- contraste AA;
- no CLS por imágenes sin dimensiones cuando el HTML disponga de ellas;
- reduced motion respetado.

---

## 10. Archivos que implementan este contrato

- `assets/v1-shell-lrb-v2.css`
- `assets/v1-lrb-material-v2.css`
- `assets/v1-home-editorial-v3.css`
- `assets/v1-home-editorial-v3.js`
- `assets/v1-editorial-interior-v4.css`
- `assets/v1-editorial-interior-v4.js`
- `assets/v1-editorial-placeholders-v4.css`
- `assets/v1-editorial-interactions-v4.css`
- `assets/v1-shell.css`
- `assets/v1-shell.js`
- `data/navigation.json`
- `tests/test-pr95-editorial-system.mjs`

Este documento debe prevalecer sobre comentarios antiguos que describan tamaños de banner o titulares mayores dentro de la propia PR #95.
