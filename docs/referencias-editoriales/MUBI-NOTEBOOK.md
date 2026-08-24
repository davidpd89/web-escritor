# MUBI Notebook — análisis para adaptación clean-room

Fecha de observación: 2026-08-24  
Referencia principal: https://mubi.com/es/notebook

## Por qué está aquí

MUBI Notebook es la referencia del grupo más útil para estudiar cómo una publicación cultural puede ser muy visual y, a la vez, seguir sintiéndose editorial. No interesa copiar el ecosistema de streaming de MUBI; interesa entender cómo Notebook utiliza imagen, tipografía, clasificación y formatos heterogéneos como una publicación coherente.

## Fuentes verificadas

### Sitio público actual — fuente A

https://mubi.com/es/notebook

En la página pública se observan, entre otros elementos:

- identidad específica “Notebook” dentro de MUBI;
- subtítulo editorial “Our Daily International Film Publication”;
- búsqueda específica de artículos;
- acceso a Explore;
- newsletter propia;
- Popular Tags;
- misión explícita de publicar texto, imágenes, sonido y vídeo.

Esto confirma que Notebook no se estructura solo como un blog cronológico: funciona como una publicación con búsqueda, taxonomía, descubrimiento y varios medios.

### Creative Lab de MUBI — fuente A

https://lab.mubi.com/
https://lab.mubi.com/about

El Creative Lab se define como el estudio creativo interdisciplinar interno de MUBI, formado por diseñadores y editores de vídeo. El archivo público clasifica trabajos por áreas como editorial, notebook, identity, key art, trailer y video essay.

La página About también registra premios D&AD para números de Notebook. Esto es importante para la investigación porque conecta la publicación con un sistema de dirección de arte sostenido, no con una suma accidental de plantillas.

### AGI y D&AD — fuente A

https://a-g-i.org/design/notebook-issue-3
https://www.dandad.org/work/d-ad-awards-archive/notebook

AGI documenta el Issue 3 como trabajo editorial para MUBI y vincula el proyecto con Pablo Martín. D&AD describe Notebook como un espacio editorial de encuentros cinematográficos y acredita a MUBI como lead/cliente/agencia de diseño.

### Tecnología detectada a nivel de dominio — fuente B

https://www.datafragment.com/technology-lookup/mubi.com

Snapshot disponible: 2025-02-27. Detecta en `mubi.com` tecnologías como React, Next.js, Emotion, Node.js, AWS, Nginx/OpenResty, Webpack, Module Federation y Sentry.

**Cautela:** el fingerprint mostrado por Datafragment indica como primera ruta detectada `https://mubi.com/en/us`. No demuestra por sí solo que cada ruta de Notebook use exactamente todos esos componentes. Para decisiones visuales nos importa más la interfaz pública que replicar su stack.

## Patrones observables que merece trasladar

### 1. Submarca editorial dentro de una marca mayor

Notebook tiene identidad propia sin romper el ecosistema MUBI. Para `davidportodiaz.com`, la equivalencia útil sería que “Cuaderno” o ciertos dossiers tengan identidad editorial reconocible sin convertirse en micrositios independientes.

Adaptación propuesta:

```html
<header class="publication-head">
  <a class="publication-head__parent" href="/">David Porto Díaz</a>
  <p class="publication-head__edition">Cuaderno</p>
  <p class="publication-head__strap">Notas sobre escritura, libros y oficio.</p>
</header>
```

La jerarquía padre → publicación → descripción evita un logo distinto para cada territorio.

### 2. Varios formatos, una misma gramática

Notebook declara texto, imágenes, sonido y vídeo como parte de la misma publicación. La lección no es añadir vídeo a todo, sino que una misma gramática editorial puede describir piezas diferentes.

Código propio sugerido:

```html
<article class="story" data-format="video">
  <p class="story__kicker">Cuaderno · Vídeo</p>
  <h2 class="story__title"><a href="/cuaderno/.../">Cómo nace una escena</a></h2>
  <p class="story__dek">Una pieza breve sobre ritmo, memoria y reescritura.</p>
  <p class="story__meta">Vídeo · 4 min</p>
</article>
```

```css
.story__kicker,
.story__meta {
  font-family: var(--font-ui, system-ui, sans-serif);
  font-size: .75rem;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.story__title {
  max-inline-size: 18ch;
  font-family: var(--font-display, Georgia, serif);
  font-size: clamp(2rem, 4vw, 4.8rem);
  line-height: .96;
  text-wrap: balance;
}
```

El atributo `data-format` sirve para semántica interna/analytics/estilos puntuales, pero no obliga a mostrar un badge con forma de píldora.

### 3. Imagen protagonista sin convertir todo en cards

Notebook funciona bien como referencia de “media first”: una imagen puede definir una pieza y el texto actuar como sistema de lectura de esa imagen.

Para Obras:

```html
<article class="work-feature">
  <figure class="work-feature__media">
    <img src="/assets/..." alt="Portada de Las manecillas del recuerdo">
  </figure>
  <div class="work-feature__copy">
    <p class="ed-kicker">Obra destacada</p>
    <h2>Las manecillas del recuerdo</h2>
    <p>Descripción editorial breve y factual de la obra.</p>
    <a href="/las-manecillas-del-recuerdo/">Entrar en la obra</a>
  </div>
</article>
```

```css
.work-feature {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(16rem, .75fr);
  gap: clamp(1.5rem, 4vw, 5rem);
  align-items: end;
  padding-block: clamp(2rem, 6vw, 7rem);
  border-block-start: 1px solid currentColor;
}

.work-feature__media img {
  inline-size: 100%;
  block-size: auto;
  display: block;
}

@media (max-width: 800px) {
  .work-feature { grid-template-columns: 1fr; }
}
```

No hay sombra genérica, borde redondeado ni contenedor “card”. La composición depende de escala, proporción y alineación.

### 4. Explore como descubrimiento editorial

La presencia visible de Explore y Popular Tags recuerda que una publicación con archivo necesita caminos de descubrimiento.

Aplicación posible:

- “Explorar por obra”;
- “Explorar por tema”;
- “Explorar por formato”;
- “Explorar por fecha” solo como una de las opciones.

Esto debería reutilizar la arquitectura real del repo y no crear taxonomías vacías.

Código conceptual:

```html
<nav class="topic-index" aria-label="Explorar el Cuaderno">
  <a href="/cuaderno/?tema=escritura">Escritura</a>
  <a href="/cuaderno/?tema=lectura">Lectura</a>
  <a href="/cuaderno/?tema=proceso">Proceso</a>
  <a href="/cuaderno/">Ver todo</a>
</nav>
```

Antes de implementar filtros query-string hay que comprobar que el backend/build actual los soporte o elegir páginas estáticas reales.

## Qué NO trasladar

- No necesitamos replicar Next.js/React/Emotion por el hecho de que MUBI los use a nivel de dominio.
- No convertir la Home del autor en una plataforma de streaming.
- No usar negro + cinematografía en todas las páginas solo porque MUBI lo hace bien en su ecosistema.
- No copiar assets, key art o fotografías de MUBI.
- No multiplicar categorías si no existe contenido suficiente.

## Mapeo directo al proyecto

| Notebook | David Porto |
|---|---|
| Notebook como publicación | Cuaderno como territorio editorial |
| Explore | Explorar / relaciones entre artículos, libros y herramientas |
| Popular Tags | Temas reales y curados, no nube de etiquetas automática |
| texto/imagen/sonido/vídeo | artículos, fragmentos, vídeo editorial, recursos de obra |
| dirección de arte unificada | tokens V1 + composición específica por pieza |

## Hipótesis a validar con DevTools

No están verificadas todavía y deben medirse antes de convertirlas en reglas:

- anchos de columnas y contenedores;
- ratios recurrentes de imagen;
- escalas tipográficas exactas;
- breakpoints reales;
- comportamiento de hover/focus;
- fuentes cargadas por Notebook específicamente;
- qué HTML llega renderizado inicialmente y qué partes hidrata JS.

Para cada medición futura, registrar URL + viewport + propiedad computed + fecha. No copiar hojas CSS enteras.

## Resultado que buscamos

La adaptación buena de MUBI Notebook no debería hacer que alguien diga “esto es MUBI”. Debería conseguir que la web de David pueda alternar texto, fotografía, portadas, vídeo y archivo con la misma naturalidad con la que una revista alterna reportajes, ensayos e imágenes.
