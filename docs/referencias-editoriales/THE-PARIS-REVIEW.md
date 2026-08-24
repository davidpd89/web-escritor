# The Paris Review — análisis para adaptación clean-room

Fecha de observación: 2026-08-24  
Referencia principal: https://www.theparisreview.org/

## Por qué está aquí

The Paris Review es probablemente la referencia conceptual más cercana al objetivo de `davidportodiaz.com`: una identidad literaria con historia, una home que mezcla presente y archivo, una organización clara por géneros/series y una estética impresa trasladada a pantalla sin disfrazar la web de papel antiguo.

Su valor no está en una animación concreta. Está en que el sistema editorial hace que contenido muy distinto parezca parte de la misma publicación.

## Fuentes verificadas

### Sitio público actual — fuente A

https://www.theparisreview.org/

La navegación pública separa:

- The Daily → Latest / Columns;
- The Quarterly → Issues / Interviews / Fiction / Poetry / Letters & Essays / Art & Photography;
- Authors;
- Audio;
- About;
- Events;
- Newsletters;
- Store.

La Home actual mezcla explícitamente tres procedencias: “On the Daily”, “In the Current Issue” y “From the Archive”, además de un stream posterior de piezas. Esta distinción visible es una referencia muy fuerte para nuestro proyecto porque evita que actualidad y fondo editorial compitan como si fueran lo mismo.

### Entrevista de diseño de 2010 — fuente A

https://www.theparisreview.org/blog/2010/09/22/jennifer-over-and-our-new-web-site/

La propia revista entrevistó a Jennifer Over, de Tierra Innovation, sobre el rediseño. De esa fuente salen varios principios que siguen siendo relevantes como criterio de diseño:

- mezclar contenido evergreen del número con contenido más efímero de The Daily;
- facilitar el acceso al archivo y recuperarlo en portada;
- diseño “rough and ready”, considerado pero no excesivamente pulido;
- fondos simples y reglas;
- evitar texturas/acabados que pretendan hacer la pantalla táctil;
- crear un entorno donde destaque el texto;
- permitir que la paleta evolucione con la cubierta del número;
- trasladar elementos del impreso de manera natural y moderna, no anacrónica;
- tratar jerarquía y tipografía como fundamento del diseño;
- aprovechar contrastes fuertes de escala.

No copiamos los estilos de 2010. Conservamos la lógica detrás de ellos.

### Rediseño/archivo de 2016 — fuente A

https://www.theparisreview.org/blog/2016/11/28/new-paris-review-look-great-paris-review-taste/

La publicación anunció en 2016 el nuevo sitio y su archivo digital completo.

### Caso de Tierra Innovation — fuente A

https://www.tierra-innovation.com/work/the-paris-review-responsive-new-cms/

Tierra documenta que comenzó a trabajar con The Paris Review en 2009, creó sitio y CMS, y volvió a actualizar CMS y web en 2016 en colaboración con Strick & Williams, responsables del diseño de esa iteración. El caso también documenta interfaz responsive, paywall, acceso de suscriptores al archivo y búsqueda de más de doscientos números por década/año y género.

Este dato es útil para arquitectura de información, no como invitación a replicar su CMS o paywall.

## Patrones observables que merece trasladar

### 1. Tres capas de relevancia: ahora / obra / archivo

La Home de Paris Review etiqueta el origen editorial de cada pieza. Nuestra traducción puede ser:

- **Ahora** → Cuaderno reciente, noticia real, evento real;
- **Obra actual** → Manecillas como foco principal;
- **Del archivo** → Samuel, textos anteriores, entrevistas, fragmentos o recursos relacionados.

Código propio:

```html
<section class="editorial-triad" aria-label="Selección editorial">
  <article class="editorial-triad__item">
    <p class="ed-kicker">Ahora</p>
    <h2><a href="/cuaderno/.../">Una nota reciente</a></h2>
  </article>

  <article class="editorial-triad__item editorial-triad__item--lead">
    <p class="ed-kicker">Obra actual</p>
    <h2><a href="/las-manecillas-del-recuerdo/">Las manecillas del recuerdo</a></h2>
  </article>

  <article class="editorial-triad__item">
    <p class="ed-kicker">Del archivo</p>
    <h2><a href="/libros/samuel-entre-mundos/">Samuel entre mundos</a></h2>
  </article>
</section>
```

```css
.editorial-triad {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  border-block: 1px solid currentColor;
}

.editorial-triad__item {
  grid-column: span 3;
  padding: 1.25rem 1.5rem 1.5rem 0;
}

.editorial-triad__item + .editorial-triad__item {
  padding-inline-start: 1.5rem;
  border-inline-start: 1px solid currentColor;
}

.editorial-triad__item--lead { grid-column: span 6; }

@media (max-width: 800px) {
  .editorial-triad { display: block; }
  .editorial-triad__item,
  .editorial-triad__item--lead {
    padding: 1rem 0;
    border-inline-start: 0 !important;
  }
  .editorial-triad__item + .editorial-triad__item {
    border-block-start: 1px solid currentColor;
  }
}
```

La retícula de 12 columnas es una decisión propia; la referencia que tomamos de Paris Review es la convivencia explícita de varias temporalidades editoriales.

### 2. Regla y tipografía antes que “container chrome”

La entrevista de diseño menciona deliberadamente “simple background shades and rules” y ausencia de texturas táctiles. Esto encaja directamente con nuestro rechazo a la típica tarjeta de producto.

Componente propio:

```css
.ed-section {
  padding-block: clamp(2.5rem, 7vw, 7rem);
}

.ed-section__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  padding-block: .65rem;
  border-block-start: 1px solid currentColor;
}

.ed-section__title {
  margin: 0;
  font-family: var(--font-display, Georgia, serif);
  font-size: clamp(2rem, 4vw, 4rem);
  line-height: 1;
}
```

### 3. Identidad impresa sin falso vintage

La fuente de 2010 es especialmente clara: integrar elementos de la revista impresa de forma natural y moderna, no anacrónica.

Aplicación a David:

- usar retícula, filetes, folios, pies de foto, capitulares o numeración cuando tengan función;
- usar Paper/Ink como sistema;
- no añadir textura de pergamino, bordes rotos, manchas de café o “papel viejo” como decoración general;
- la entrada de “pasar página” puede ser una firma puntual, no el comportamiento de cada navegación.

### 4. Acento cromático gobernado por la obra

La entrevista documenta que la paleta del sitio podía cambiar en función de la portada de cada nuevo número. La traducción propia más sensata es una base estable y un `--edition-accent` por contexto.

```css
:root {
  --paper: #f4f0e8;
  --ink: #151515;
  --edition-accent: #7a3f2f;
}

[data-edition="manecillas"] {
  /* El valor real debe salir de la portada oficial y del pipeline cromático. */
  --edition-accent: var(--book-accent-manecillas);
}

.ed-kicker,
.ed-link--accent {
  color: var(--edition-accent);
}
```

No fijar colores inventados en producción. El ejemplo solo demuestra el mecanismo.

### 5. Archivo navegable por más de un eje

Tierra documenta búsqueda por década/año y género. Para un autor con un corpus menor, una versión ligera puede funcionar mejor:

```html
<form class="archive-controls" aria-label="Filtrar contenidos">
  <label>
    <span>Tipo</span>
    <select name="tipo">
      <option value="">Todo</option>
      <option value="cuaderno">Cuaderno</option>
      <option value="fragmentos">Fragmentos</option>
      <option value="prensa">Prensa</option>
    </select>
  </label>
</form>
```

Antes de implementar controles hay que garantizar que existe una URL indexable/usable o una mejora progresiva. No hacer filtros JS que oculten el contenido a buscadores o sin-JS.

### 6. Contraste grande/pequeño

La entrevista de diseño habla del atractivo de colocar elementos grandes y fuertes junto a otros pequeños y delicados. Podemos formalizarlo sin imitar la revista:

```css
.ed-headline--lead {
  font-size: clamp(3.4rem, 8vw, 8.5rem);
  line-height: .88;
  letter-spacing: -.045em;
}

.ed-meta {
  font-size: .75rem;
  line-height: 1.4;
  letter-spacing: .06em;
  text-transform: uppercase;
}
```

La accesibilidad obliga a que el texto pequeño siga siendo legible y pueda escalar correctamente.

## Propuesta específica para la Home de David

La idea de “portada editorial” puede organizarse así:

1. intro visual opcional + Entrar;
2. masthead “David Porto Díaz”;
3. franja editorial Ahora / Obra actual / Del archivo;
4. gran feature de Manecillas con portada/fotografía oficial;
5. Cuaderno como stream editorial;
6. Samuel como pieza recuperada, no como producto desplazado;
7. archivo/enlaces de exploración;
8. newsletter integrada como cierre editorial, no modal invasivo.

Esta secuencia recoge la lógica Paris Review pero con el contenido y prioridades reales del proyecto.

## Qué NO trasladar

- No copiar su hand-drawn logo/frontispiece.
- No usar una paleta rotatoria si genera inconsistencia o problemas de contraste.
- No crear “Daily/Quarterly” falsos.
- No añadir paywall.
- No copiar su CMS ni asumir que su arquitectura técnica es adecuada para un sitio estático.
- No convertir cada bloque en una referencia retro de revista de 1953.

## Mapeo directo

| Paris Review | David Porto |
|---|---|
| The Daily | Cuaderno / actualidad editorial |
| Current Issue | Las manecillas del recuerdo / foco de lanzamiento |
| From the Archive | Samuel + piezas anteriores relevantes |
| Issues | Obras/dossiers reales; no números ficticios |
| Authors | Autor y perfiles/contexto, si aplica |
| Audio | Material propio cuando exista |
| genre archive | filtros/índices por tipo y tema reales |

## Hipótesis a validar con DevTools

- familia tipográfica exacta en la versión actual;
- proporciones de la franja superior de Home;
- anchos de columna y reglas responsive;
- tratamiento actual de portrait images;
- loading/lazy-loading de media;
- estados focus/hover;
- DOM y landmarks de artículo;
- comportamiento del paywall, únicamente como referencia UX, no para replicarlo.

## Resultado que buscamos

Que la web tenga la cualidad que la propia Paris Review defendía en su rediseño: **texto protagonista, jerarquía muy clara y herencia editorial reinterpretada para la pantalla**, no una simulación de papel ni una landing comercial disfrazada.
