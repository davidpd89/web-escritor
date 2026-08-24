# The Yale Review — análisis para adaptación clean-room

Fecha de observación: 2026-08-24  
Referencia principal: https://yalereview.org/

## Por qué está aquí

The Yale Review es la referencia más clara del grupo para el objetivo “elegante, sencillo y fácil”. Su interfaz no necesita ruido visual para comunicar que existe dirección de arte. La sensación editorial sale de la jerarquía, el ritmo, las series/folios, la relación entre imagen y texto y una navegación relativamente directa.

Para `davidportodiaz.com` interesa especialmente como antídoto contra dos extremos: una web de autor demasiado corporativa o una web “premiable” que sobrecarga la lectura con efectos.

## Fuentes verificadas

### Sitio público actual — fuente A

https://yalereview.org/

La navegación actual expone:

- Nonfiction → Essays / Criticism;
- Fiction;
- Poetry → Poem of the Week;
- Interviews;
- Archives;
- Folios;
- Issues → Current Issue / All Issues;
- About;
- Search;
- Subscribe / Donate.

La Home actual organiza contenido por capas: issue estacional, piezas destacadas, un Folio temático, Current Issue, entrevistas y From the Archives.

### Nota de lanzamiento — fuente A

https://yalereview.org/article/editors-note

Meghan O’Rourke explica la intención digital del proyecto: una versión online plenamente pensada que mezcla piezas del impreso con audio, vídeo y contenido exclusivo de web. La formulación más importante para nuestra investigación es el deseo explícito de una experiencia donde la buena escritura esté a un clic, **sin pop-ups, sobrecarga de información ni sensacionalismo**.

### Yale News — fuente A

https://news.yale.edu/2021/06/28/tyr-gives-readers-digital-space-read-and-contemplate

Yale describe el lanzamiento de 2021 como un sitio que conserva la calidad literaria de la edición impresa y añade capas digitales: audio de poetas, vídeo de lecturas/entrevistas/conversaciones y recuperación de piezas del archivo.

### Pentagram — fuente A

https://www.pentagram.com/work/the-yale-review/story

Pentagram documenta el rediseño de la publicación para su 200 aniversario. El caso explica que se creó una plantilla completamente nueva, con un tamaño menor y más cercano a un libro impreso fácil de llevar, e incorporación de arte y otros elementos visuales.

El caso es principalmente de identidad/publicación impresa. No debe atribuirse automáticamente a Pentagram cada detalle del frontend actual si una fuente no lo confirma.

### Infraestructura observable — fuente B limitada

https://www.ipaddress.com/website/yalereview.org/

El lookup de dominio observado en agosto de 2026 informa servidor Cloudflare y DNS Cloudflare. Esto solo es infraestructura de dominio; no identifica por sí mismo framework, CMS o arquitectura frontend.

El HTML público actual también expone imágenes servidas desde `d181q449nqu6en.cloudfront.net`. Eso permite afirmar que esa CDN participa en la entrega de imágenes observadas, pero no reconstruir el backend completo.

## Patrones observables que merece trasladar

### 1. Calma como requisito funcional

La declaración “sin pop-ups, información overload y sensacionalismo” encaja especialmente bien con una web literaria. Para nuestro sitio significa:

- no interrumpir la lectura con newsletter modal al entrar;
- no convertir cada scroll en animación;
- no mostrar cinco CTAs compitiendo;
- dejar que una pieza fuerte sea suficiente para dominar un viewport;
- ofrecer caminos siguientes al final o en márgenes naturales.

Código base de una sección calmada:

```css
.reading-section {
  padding-block: clamp(3.5rem, 9vw, 10rem);
}

.reading-section + .reading-section {
  border-block-start: 1px solid color-mix(in srgb, currentColor 24%, transparent);
}

.reading-section__inner {
  inline-size: min(100% - 2rem, 82rem);
  margin-inline: auto;
}
```

### 2. Folio como agrupación curada

The Yale Review utiliza “Folios” para reunir contenidos. El concepto se puede adaptar de forma legítima a agrupaciones reales:

- dossier “Las manecillas del recuerdo”;
- fragmentos + artículos + recursos sobre una misma obra;
- especial “Feria del Libro 2026” si existe material suficiente;
- dossier de proceso creativo.

No hace falta llamarlo “Folio” públicamente. Podemos usar “Dossier”, “Especial” o un nombre propio más natural en español.

```html
<section class="dossier" aria-labelledby="dossier-title">
  <header class="dossier__head">
    <p class="ed-kicker">Dossier</p>
    <h2 id="dossier-title">Las manecillas del recuerdo</h2>
    <p>Una entrada curada a la obra: libro, fragmentos y Cuaderno.</p>
  </header>

  <div class="dossier__contents">
    <a href="/las-manecillas-del-recuerdo/">La obra</a>
    <a href="/las-manecillas-del-recuerdo/fragmentos/">Fragmentos</a>
    <a href="/cuaderno/.../">Proceso y contexto</a>
  </div>
</section>
```

### 3. Lead: categoría → título → dek → autor

La Home actual hace muy visible una secuencia editorial simple: categoría, titular, subtítulo/dek y autor. Nuestro sitio puede usar el mismo principio sin imitar su estilo exacto.

```html
<article class="lead-story">
  <p class="ed-kicker">Obras · Contemporánea</p>
  <h1 class="lead-story__title">Las manecillas del recuerdo</h1>
  <p class="lead-story__dek">Una descripción factual y breve de la obra.</p>
  <p class="lead-story__byline">David Porto Díaz</p>
</article>
```

```css
.lead-story__title {
  margin: .3em 0 .2em;
  max-inline-size: 14ch;
  font-family: var(--font-display, Georgia, serif);
  font-size: clamp(3rem, 8vw, 8rem);
  font-weight: 400;
  line-height: .9;
  text-wrap: balance;
}

.lead-story__dek {
  max-inline-size: 42ch;
  font-family: var(--font-reading, Georgia, serif);
  font-size: clamp(1.15rem, 1rem + .5vw, 1.65rem);
  line-height: 1.35;
}
```

### 4. Series permanentes como caminos de navegación

“Poem of the Week”, “Shakespeare and Company Interviews” y “From the Archives” funcionan como series reconocibles. En nuestro proyecto solo conviene crear series si podemos sostenerlas.

Posibles series reales:

- Fragmentos;
- Diario de escritura, si se adopta como compromiso editorial;
- Recomendaciones/lecturas si ya existe suficiente catálogo;
- Tras la página / proceso de una obra.

Una serie debe tener landing estable, URL estable y relaciones reales con sus piezas.

### 5. Archivo presentado como tesoro, no como cementerio

Yale recupera nombres y piezas históricas en “From the Archives”. La adaptación es editorializar el archivo:

```html
<section class="archive-window">
  <header class="archive-window__header">
    <p class="ed-kicker">Del archivo</p>
    <h2>Una lectura para continuar</h2>
  </header>
  <article>
    <time datetime="2026">2026</time>
    <h3><a href="/cuaderno/.../">Título relacionado</a></h3>
    <p>Una frase de contexto que explica por qué vuelve ahora.</p>
  </article>
</section>
```

No usar “archivo” solo como tabla de fechas.

### 6. Imágenes como respiración, no como relleno

La Home combina piezas sin imagen con grupos visuales y hero images. La lección es permitir que **no todas las entradas necesiten thumbnail**.

Esto evita una de las marcas más visibles de plantilla/CMS: todas las cards con imagen 16:9 aunque el contenido no la necesite.

Regla propuesta:

- imagen solo si es oficial, original, documental o una pieza gráfica creada deliberadamente;
- si no aporta, composición tipográfica;
- ratios definidos por intención editorial, no por una única plantilla global.

### 7. Artículo largo con metadata completa

En una página de artículo de Yale se observan categoría, H1, dek, autor, hero/caption, cuerpo, bio, CTA, tags y fecha original. Nuestro patrón propio puede ser:

```html
<article class="article-page">
  <header class="article-page__header">
    <p class="ed-kicker">Cuaderno · Oficio</p>
    <h1>Título</h1>
    <p class="article-page__dek">Entradilla.</p>
    <p class="article-page__meta">
      <span>Por David Porto Díaz</span>
      <time datetime="2026-08-24">24 de agosto de 2026</time>
    </p>
  </header>
  <div class="article-page__body">…</div>
</article>
```

```css
.article-page__header {
  inline-size: min(100% - 2rem, 76rem);
  margin-inline: auto;
  padding-block: clamp(3rem, 8vw, 8rem);
}

.article-page__body {
  inline-size: min(100% - 2rem, 68ch);
  margin-inline: auto;
  font-family: var(--font-reading, Georgia, serif);
  font-size: clamp(1.05rem, 1rem + .2vw, 1.2rem);
  line-height: 1.72;
}
```

## Qué NO trasladar

- No inventar “folios” para parecer una revista.
- No copiar logo, tipografías propietarias ni identidad Yale.
- No usar el prestigio visual como excusa para reducir contraste o tamaño de fuente.
- No añadir modal de apoyo/suscripción porque otras revistas tengan modelos de membresía.
- No intentar averiguar un framework solo por adivinar nombres de bundles.

## Mapeo directo al proyecto

| Yale Review | David Porto |
|---|---|
| Current Issue | foco actual / Manecillas |
| Folios | dossiers curados de obra/tema |
| Poem of the Week / series | series solo si hay continuidad real |
| From the Archives | resurfacado de Cuaderno/Samuel/fragmentos |
| Essays/Criticism/Fiction/Poetry | territorios/tipos reales del contenido propio |
| Subscribe | newsletter no intrusiva y compra de obra donde proceda |

## Hipótesis a validar con DevTools

- familias tipográficas del frontend actual;
- escala exacta de títulos por breakpoint;
- anchos de artículo;
- cómo se componen las imágenes de CloudFront;
- lazy loading;
- estados focus;
- landmarks semánticos;
- composición móvil de Folios/Issues;
- si existe un CMS/framework detectable de forma fiable.

## Resultado que buscamos

Que la web pueda ser visualmente memorable sin parecer ansiosa por demostrarlo. De Yale nos interesa especialmente esta idea: **la sensación de calidad debe venir de una lectura tranquila, una jerarquía inevitable y una selección editorial fuerte**.
