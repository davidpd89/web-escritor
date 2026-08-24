# London Review of Books — análisis para adaptación clean-room

Fecha de observación: 2026-08-24  
Referencia principal: https://www.lrb.co.uk/

## Por qué está aquí

La LRB es la referencia más útil de este grupo para estudiar **densidad editorial sin sensación de dashboard**. Su Home contiene mucho texto, archivo, issue, blog y navegación temática, pero la lectura sigue estando organizada por jerarquía, autoría y ritmo editorial.

No buscamos hacer `davidportodiaz.com` tan densa como la LRB. Buscamos aprender a mostrar más contenido sin recurrir a una cuadrícula interminable de tarjetas.

## Fuentes verificadas

### Sitio público actual — fuente A

https://www.lrb.co.uk/

La navegación pública expone claramente:

- Latest Issue;
- Archive;
- Contributors;
- Subjects;
- Shop/Bookshop;
- búsqueda avanzada y búsqueda por contributor;
- archivo de cubiertas.

En la Home se mezclan piezas destacadas, “From the blog”, “In the latest issue” y “From the archive”. Eso demuestra una idea especialmente aprovechable: **la fecha no es el único criterio de relevancia**.

### About — fuente A

https://www.lrb.co.uk/about

La LRB describe su producto como publicación de ensayos largos, reseñas, memoir/reportage, poemas, cartas y diarios, disponible en print, online y app. También documenta que la web integra blog, tienda, podcasts, documentales cortos y vídeo de eventos.

Su masthead público lista actualmente roles específicos de producto y tecnología —Head of Product Delivery, Technical Architect, Senior Frontend Engineer, Senior Backend Engineer, Technical Business Analyst y Senior QA Engineer—. Esto confirma que la experiencia digital es un producto mantenido, no una simple exportación del papel.

### Accesibilidad — fuente A

https://www.lrb.co.uk/accessibility

La página documenta navegación mediante access keys y guía para cambio de tamaño de texto. No proponemos copiar literalmente su esquema de access keys —es un patrón histórico y puede entrar en conflicto con atajos de navegador/asistencia—, pero sí conservar la intención: una publicación textual debe tratar teclado, salto al contenido y zoom como requisitos de primera clase.

### Relanzamiento de 2019 — fuentes A/B contextual

https://www.riotcommunications.com/2019/08/07/london-review-of-books-announces-40th-anniversary-celebrations/

Riot anunció que la LRB relanzaría `lrb.co.uk` por primera vez en una década, con una revisión completa de su presencia web, incluyendo blog, newsletters, archivo y podcasts.

https://www.inpublishing.co.uk/articles/taking-it-nice-and-slow-14962

La entrevista con Reneé Doegar explica que el nuevo sitio debía permitir mejores herramientas online, análisis del user journey, recommendation engines y optimización móvil, dentro de una cultura de test e iteración.

## Patrones observables que merece trasladar

### 1. “Portada” con piezas de diferente peso

En vez de un mosaico donde todas las entradas pesan lo mismo, una Home editorial puede declarar una pieza principal y luego secundarios.

Código propio:

```html
<section class="front-page" aria-labelledby="front-page-title">
  <h2 id="front-page-title" class="section-rule">En portada</h2>

  <article class="front-page__lead">
    <p class="ed-kicker">Obra actual</p>
    <h3>Las manecillas del recuerdo</h3>
    <p class="ed-dek">Descripción editorial breve de la obra.</p>
  </article>

  <div class="front-page__secondary">
    <article>…Samuel entre mundos…</article>
    <article>…Cuaderno…</article>
  </div>
</section>
```

```css
.front-page {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(16rem, 1fr);
  column-gap: clamp(2rem, 5vw, 6rem);
}

.front-page__secondary {
  border-inline-start: 1px solid currentColor;
  padding-inline-start: clamp(1rem, 2.5vw, 2rem);
}

.front-page__secondary > * + * {
  margin-block-start: 2rem;
  padding-block-start: 2rem;
  border-block-start: 1px solid color-mix(in srgb, currentColor 35%, transparent);
}

@media (max-width: 800px) {
  .front-page { grid-template-columns: 1fr; }
  .front-page__secondary {
    margin-block-start: 2rem;
    padding: 2rem 0 0;
    border-inline-start: 0;
    border-block-start: 1px solid currentColor;
  }
}
```

La idea procede del principio observable de jerarquía editorial, no de copiar la retícula exacta de la LRB.

### 2. Archivo como contenido vivo

La Home de LRB recupera explícitamente piezas “From the archive”. Para nuestro proyecto, esto puede resolver un problema frecuente de webs de autor: artículos antiguos buenos desaparecen por debajo del scroll cronológico.

Patrón propio:

```html
<section class="archive-picks" aria-labelledby="archive-title">
  <div class="archive-picks__head">
    <p class="ed-kicker">Del archivo</p>
    <h2 id="archive-title">Para seguir leyendo</h2>
  </div>
  <ol class="archive-picks__list">
    <li><a href="/cuaderno/.../">Artículo relacionado con memoria</a></li>
    <li><a href="/fragmento/.../">Fragmento de una obra</a></li>
    <li><a href="/autor/.../">Una pieza de proceso o biografía</a></li>
  </ol>
</section>
```

La selección debería ser editorial o basada en relaciones reales del contenido; no una lista aleatoria que cambie en cada carga.

### 3. Contributor/Subject como modelo mental

LRB permite explorar por contributors y subjects. En una web de un solo autor no tiene sentido copiar Contributors, pero el modelo sí se puede transformar:

- por Obra;
- por Tema;
- por Tipo de contenido;
- por relación (“sobre esta obra”, “proceso”, “fragmentos”, “prensa”).

Esto favorece el interlinking humano y SEO sin llenar la web de tags sin curar.

### 4. La densidad se resuelve con reglas y texto, no con cajas

Un listado editorial puede ser compacto y seguir siendo escaneable:

```html
<ul class="ledger-list">
  <li class="ledger-list__item">
    <p class="ledger-list__meta">Cuaderno · 2026</p>
    <h3><a href="/cuaderno/.../">Título</a></h3>
    <p>Entradilla de una o dos líneas.</p>
  </li>
  <li class="ledger-list__item">…</li>
</ul>
```

```css
.ledger-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-block-start: 1px solid currentColor;
}

.ledger-list__item {
  display: grid;
  grid-template-columns: minmax(8rem, .35fr) minmax(0, .8fr) minmax(14rem, 1fr);
  gap: 1.25rem;
  padding-block: 1rem;
  border-block-end: 1px solid color-mix(in srgb, currentColor 30%, transparent);
}

@media (max-width: 700px) {
  .ledger-list__item { grid-template-columns: 1fr; gap: .35rem; }
}
```

Esta composición es especialmente adecuada para archivo, prensa, eventos o listados de artículos.

### 5. Issue como contenedor narrativo

LRB organiza parte de su universo alrededor del “Latest Issue”. Nuestra web no publica números periódicos, pero podemos adoptar la idea del **contenedor editorial temporal** sin fingir ser una revista real.

Ejemplos legítimos:

- “Ahora: Las manecillas del recuerdo”;
- “Dossier de lanzamiento”;
- “Cuaderno · selección de otoño” si existe una curación real;
- “Archivo de Feria del Libro 2026” si el contenido existe.

No usar “Issue 01” solo por estética si no hay un verdadero sistema de ediciones.

## Accesibilidad que debe superar a la referencia

La intención de la LRB es buena, pero nuestro estándar debe apoyarse en patrones actuales:

```html
<a class="skip-link" href="#contenido">Saltar al contenido</a>
<header>…</header>
<main id="contenido">…</main>
```

Y mantener:

- orden DOM coherente con el orden visual;
- foco visible;
- navegación completamente usable por teclado;
- zoom/reflow a 200–400 %;
- enlaces distinguibles sin depender solo del color;
- sin JS esencial para descubrir el contenido básico.

## Qué NO trasladar

- No copiar su volumen de navegación si nuestro catálogo no lo necesita.
- No implementar recommendation engines por imitación; primero resolver relaciones editoriales estáticas de alta calidad.
- No copiar access keys numéricas sin una auditoría moderna.
- No densificar la Home hasta perjudicar la prioridad de Manecillas.
- No convertir cada párrafo en “long read” por estética.

## Mapeo directo al proyecto

| LRB | David Porto |
|---|---|
| Latest Issue | Obra/foco actual |
| Archive | Cuaderno + archivo de contenidos + recursos anteriores |
| Contributors | No aplica literalmente; Autor/obras pueden ser ejes |
| Subjects | Temas reales de Cuaderno/Obras |
| From the blog | Cuaderno reciente |
| From the archive | Resurfacing editorial de piezas relacionadas |
| Podcasts/videos | Vídeo/audio solo cuando haya material propio |

## Hipótesis a medir después

- anchura de columnas de Home y artículo;
- relación de tamaños entre headline/byline/excerpt;
- tratamiento responsive de listas densas;
- ratio entre contenido visible e imagen;
- comportamiento real del menú y búsqueda con teclado;
- tecnologías concretas de frontend por ruta.

## Resultado que buscamos

Tomar de LRB la sensación de que **hay un mundo editorial detrás de la portada**. El visitante debería poder entrar por Manecillas y terminar descubriendo un fragmento, un artículo del Cuaderno o una pieza de archivo por relación natural, no porque la interfaz le haya lanzado una parrilla genérica de “más contenido”.
