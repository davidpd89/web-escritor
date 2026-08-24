# Referencias editoriales para el rediseño web

Fecha de apertura de investigación: 2026-08-24  
Rama: `research-editorial-reference-sites`  
Base: `implementacion-web-2026`

## Objetivo

Este directorio conserva una investigación de referencias para que el rediseño de `davidportodiaz.com` pueda evolucionar hacia una experiencia editorial digital —más cercana a una revista literaria, un libro o un periódico cultural contemporáneo que a una landing convencional de autor— sin depender de memoria, capturas aisladas ni imitaciones no trazables.

Las cuatro referencias iniciales son:

- MUBI Notebook — https://mubi.com/es/notebook
- London Review of Books — https://www.lrb.co.uk/
- The Paris Review — https://www.theparisreview.org/
- The Yale Review — https://yalereview.org/

Esta documentación debe crecer con nuevas observaciones, capturas, pruebas responsive, mediciones y prototipos. No es una especificación cerrada ni autoriza a copiar código propietario.

## Estado de los repositorios públicos

A fecha 2026-08-24 no se ha localizado un repositorio público oficial que contenga el código de producción de ninguna de las cuatro webs anteriores.

Se buscaron nombres, dominios y organizaciones relacionadas en GitHub. Hay que distinguir con cuidado repositorios que mencionan una publicación de repositorios que implementan realmente su web.

- MUBI mantiene una organización pública: https://github.com/mubi . No se ha confirmado en ella un repositorio público de `mubi.com`/Notebook.
- Para LRB aparece `https://github.com/MartinPaulEve/LRB`, pero su README confirma que es un dataset/scraper académico de reseñas y redes de reviewers; **no es el código de `lrb.co.uk`**.
- No se ha confirmado un repositorio público oficial de la web de The Paris Review.
- No se ha confirmado un repositorio público oficial de la web de The Yale Review.

Por tanto, este trabajo usa un enfoque **clean-room**: estudiamos únicamente información pública observable y documentación pública sobre los proyectos; después escribimos patrones propios para `davidportodiaz.com`.

## Qué significa “fuente” en estos documentos

Cada afirmación debería poder clasificarse en uno de estos niveles:

### A — Fuente primaria / confianza alta

Incluye:

- HTML y contenido visible en la web pública actual.
- Páginas oficiales de la propia publicación.
- Casos de estudio publicados por el estudio o equipo que diseñó/desarrolló el proyecto.
- Comunicaciones oficiales de la institución.

Puede sostener afirmaciones como “la navegación expone Archivo”, “el equipo describe el sitio como una experiencia de lectura calmada” o “Tierra construyó el CMS y paywall”.

### B — Detección técnica externa / confianza media

Servicios de fingerprinting tecnológico pueden detectar React, Next.js, CDN, analytics, etc. Son útiles como pista, pero suelen analizar el dominio o la home, no necesariamente cada sección. Nunca deben convertirse en una afirmación absoluta sobre Notebook, un artículo concreto o el CMS completo.

Ejemplo:

- https://www.datafragment.com/technology-lookup/mubi.com

### C — Inferencia visual / confianza contextual

Son conclusiones derivadas de observar composición, jerarquía, ritmo, responsive o comportamiento. Ejemplos:

- “la home funciona como una portada editorial”; 
- “la densidad se sostiene mediante reglas y jerarquía tipográfica”; 
- “este patrón podría mapearse a Obras/Cuaderno”.

Estas inferencias son útiles, pero deben escribirse como decisiones de diseño, no como hechos internos de la web estudiada.

## Regla de propiedad intelectual

No copiar:

- hojas CSS completas;
- JavaScript minificado o bundles;
- componentes propietarios reconstruidos línea por línea;
- tipografías sin licencia;
- ilustraciones, fotografías, iconos o assets ajenos;
- textos editoriales ajenos como contenido de producción.

Sí hacer:

1. observar el patrón;
2. describir qué problema resuelve;
3. documentar la fuente pública que permite observarlo;
4. escribir HTML/CSS/JS propio con nombres y estructura propios;
5. adaptarlo a la arquitectura, tokens, contenido y accesibilidad de `davidportodiaz.com`;
6. probarlo en móvil, teclado, reduced motion y navegadores reales.

El código de `prototype.html` y `prototype.css` de este directorio es código original del proyecto, no código extraído de las webs de referencia.

## Qué queremos aprender de cada referencia

| Referencia | Principal aprendizaje | Posible aplicación propia |
|---|---|---|
| MUBI Notebook | Publicación multimedia, imagen como pieza editorial, formatos heterogéneos bajo una identidad muy controlada | Home visual, Cuaderno, piezas con vídeo/audio, tratamiento de imágenes y portadas |
| London Review of Books | Densidad editorial, archivo, contributors/subjects, lectura larga y navegación de publicación | Archivo de contenidos, interlinking, listados densos, descubrimiento de textos antiguos |
| The Paris Review | Mezcla “actual + número + archivo”, reglas, tipografía, identidad impresa trasladada sin disfraz retro | Home, Obra actual como “current issue”, Cuaderno como “Daily”, resurfacado de archivo |
| The Yale Review | Calma, claridad, folios/series, jerarquía muy legible y experiencia anti-ruido | Dirección visual general, artículos, dossiers, navegación sencilla, bloques especiales |

## Principios transversales que sí encajan con David Porto

### 1. Una cabecera editorial, no una barra SaaS

La identidad del autor debe leerse como la cabecera de una publicación. El nombre puede tener más presencia que el menú y el menú puede organizarse por territorios editoriales reales: Obras, Autor, Cuaderno, Herramientas y Prensa.

### 2. Retícula editorial en lugar de “cards” repetidas

No convertir cada pieza en un rectángulo redondeado. Usar:

- reglas horizontales;
- columnas;
- cambios de escala tipográfica;
- imágenes con proporciones deliberadas;
- metadatos visibles;
- bloques que comparten una retícula pero no una plantilla visual idéntica.

### 3. Jerarquía explícita

Cada pieza debe poder componerse con una gramática simple:

```html
<article class="ed-story">
  <p class="ed-kicker">Cuaderno · Oficio</p>
  <h2 class="ed-story__title">Título del artículo</h2>
  <p class="ed-story__dek">Una frase que explica por qué merece abrirse.</p>
  <p class="ed-meta">12 min de lectura · Actualizado 2026</p>
</article>
```

Kicker, titular, entradilla y metadato forman una jerarquía reconocible incluso sin imagen.

### 4. Actualidad y archivo deben convivir

Una web de autor gana profundidad si no parece que todo nació esta semana. El patrón editorial útil es:

- pieza/obra actual;
- selección reciente;
- archivo recuperado por afinidad;
- contexto estable de autor/obra.

No ordenar toda la experiencia únicamente por fecha descendente.

### 5. “Papel” como sistema, no como textura falsa

La referencia a libro/periódico se construye mejor mediante proporción, márgenes, columnas, reglas, folios, pies de foto y tipografía que mediante papel envejecido, manchas o adornos pseudoantiguos.

### 6. Cada obra puede aportar un acento, no una web distinta

The Paris Review documentó históricamente una paleta capaz de cambiar con la cubierta del número. Para este proyecto la adaptación segura sería mantener una base Paper/Ink común y permitir que cada obra aporte un acento controlado.

### 7. Multimedia cuando pertenece a la pieza

MUBI Notebook y The Yale Review integran formatos más allá del texto. En nuestro caso vídeo, audio o animación deben aparecer cuando mejoren una historia, una obra o un proceso; no como ornamentación obligatoria de cada bloque.

### 8. Lectura larga con ancho controlado

Para cuerpos de artículo largos, punto de partida propio:

```css
.ed-article__body {
  inline-size: min(100%, 68ch);
  margin-inline: auto;
  font-size: clamp(1.05rem, 0.98rem + 0.22vw, 1.2rem);
  line-height: 1.72;
}
```

No se afirma que ninguna referencia use exactamente `68ch`; es una decisión clean-room inspirada por el objetivo común de lectura prolongada.

## Prototipo base incluido

`prototype.html` y `prototype.css` prueban una gramática propia con:

- masthead;
- navegación editorial;
- lead principal;
- rail de Obras;
- listado de Cuaderno;
- bloque de archivo;
- responsive sin JS esencial;
- ausencia deliberada de tarjetas redondeadas y efectos de “app”.

No debe copiarse directamente a producción. Antes de integrar un patrón hay que mapearlo a los tokens V1, al shell real y a los owners de diseño correspondientes.

## Protocolo para ampliar esta investigación

Cuando otra persona continúe el trabajo debe registrar, como mínimo:

1. fecha de observación;
2. URL exacta;
3. viewport aproximado;
4. qué se observa literalmente;
5. qué se infiere;
6. qué parte merece adaptación;
7. código propio de prueba;
8. impacto en accesibilidad/responsive/performance;
9. relación con una página/componente real del repo;
10. procedencia y derechos de cualquier asset propuesto.

Para una pasada técnica más profunda con DevTools del navegador:

- inspeccionar DOM semántico, sin copiarlo en bloque;
- anotar `font-family`, tamaños, `line-height`, anchos y gaps mediante computed styles;
- identificar breakpoints por comportamiento, no solo por nombres de clases;
- observar Network para saber qué recursos son propios/terceros;
- no descargar ni versionar fuentes propietarias;
- registrar si una tecnología se detecta en una ruta concreta o solo a nivel de dominio;
- probar teclado, zoom 200 %, `prefers-reduced-motion`, 320 px y desktop ancho;
- capturar únicamente material necesario para análisis interno y respetar derechos de los assets.

## Fuentes iniciales

### MUBI / Notebook

- https://mubi.com/es/notebook
- https://lab.mubi.com/
- https://lab.mubi.com/about
- https://a-g-i.org/design/notebook-issue-3
- https://www.dandad.org/work/d-ad-awards-archive/notebook
- https://github.com/mubi
- https://www.datafragment.com/technology-lookup/mubi.com

### London Review of Books

- https://www.lrb.co.uk/
- https://www.lrb.co.uk/about
- https://www.lrb.co.uk/accessibility
- https://www.lrb.co.uk/sitemap
- https://www.riotcommunications.com/2019/08/07/london-review-of-books-announces-40th-anniversary-celebrations/
- https://www.inpublishing.co.uk/articles/taking-it-nice-and-slow-14962

### The Paris Review

- https://www.theparisreview.org/
- https://www.theparisreview.org/blog/2010/09/22/jennifer-over-and-our-new-web-site/
- https://www.theparisreview.org/blog/2016/11/28/new-paris-review-look-great-paris-review-taste/
- https://www.tierra-innovation.com/work/the-paris-review-responsive-new-cms/

### The Yale Review

- https://yalereview.org/
- https://yalereview.org/article/editors-note
- https://www.pentagram.com/work/the-yale-review/story
- https://news.yale.edu/2021/06/28/tyr-gives-readers-digital-space-read-and-contemplate
- https://yalereview.org/about/masthead

## Siguiente nivel de trabajo

Esta PR debe servir como biblioteca de decisiones, no como un depósito de inspiración sin destino. Las siguientes ampliaciones útiles son:

- medir con DevTools una muestra estable de Home + artículo + archivo de cada referencia;
- guardar una tabla comparativa de tipografía/spacing/layout por breakpoint;
- convertir los patrones aprobados en componentes reales usando los tokens V1;
- comparar cada adaptación con la web actual y con los contratos de diseño existentes;
- documentar qué referencia motivó cada decisión, pero mantener el resultado visual inequívocamente propio.

## Nota de decisión — 2026-08-24 (override explícito)

El propietario del proyecto pidió explícitamente, en sesión de producto, la máxima fidelidad visual posible a MUBI para `assets/v1-tokens.css` y el resto del sistema V1 ("réplica visual máxima, asumiendo el riesgo"), aceptando conscientemente que esto **contradice** la sección "Qué NO trasladar" de `MUBI-NOTEBOOK.md` (en particular "no usar negro + cinematografía en todas las páginas" y "no debería hacer que alguien diga esto es MUBI") y la regla de propiedad intelectual de este documento.

Qué se hizo bajo este override:

- paleta B/N pura + MUBI Blue (`#001489`) como único acento, tomado de fuentes públicas de terceros que documentan la identidad de marca de MUBI (no de su código fuente);
- pila tipográfica igual al *fallback* que el propio MUBI sirve quien no tiene licencia de Riforma (`Arial, Helvetica, "Lucida Grande", sans-serif`) — no se ha copiado ni distribuido la fuente Riforma, que es de pago;
- radio 0 y sin sombras en todo el sistema;
- mayúsculas + binario de peso 300/500 en titulares, navegación y botones.

Qué se mantiene sin cambios respecto a la regla de propiedad intelectual original: no se ha copiado CSS/JS de mubi.com, ni assets, ni fotografías, ni copy editorial. El código de `assets/v1-*.css` sigue siendo escrito desde cero para este repo.

Este override es una decisión de producto puntual para esta iteración, no una revocación de la política clean-room para futuras referencias (LRB, Paris Review, Yale Review) ni para trabajo futuro sobre MUBI Notebook como referencia editorial (ver `MUBI-NOTEBOOK.md`).

### Ampliación — misma sesión: estructura y colocación, no solo tokens

El propietario pidió ir más allá de color/tipografía y llevar también los patrones estructurales de MUBI (bandas alternas negro/blanco a pantalla completa, tarjeta editorial con imagen, hero dominado por imagen) al **contenido real** del sitio. Aplicado en `index.html`, `cuaderno/index.html` y `autor.html`:

- **Bandas alternas**: nueva sección `.declaration-band` en Home (`assets/v1-home.css`), banda negra a pantalla completa con foto real de evento (feria de Aranjuez, misma imagen/alt que `ferias.html`) entre el río editorial y las FAQ. No se ha inventado ninguna fotografía "de comunidad" genérica: se reutiliza contenido real del propio sitio.
- **Tarjeta editorial con imagen**: `.river-item` (Home) y `.cuaderno-feature`/`.id-card` en `#libros` de `autor.html` ganan una miniatura real (portadas de los libros, foto de autor, foto real de la crónica de feria) donde existe un activo genuino; los ítems sin imagen real (antología externa, guías conceptuales del Cuaderno) se quedan en formato solo-texto, en línea con la mezcla de formatos heterogéneos documentada arriba para MUBI Notebook — no se fabrica imaginería para rellenar huecos.
- **Hero más dominado por imagen**: `.home-hero__copy` pasa de 6 a 5 columnas de 12 en escritorio, dejando más peso visual a `.hero-media`.
- **Folios grandes en el archivo de texto**: `.cuaderno-entry__index` (las 4 guías sin foto propia) pasa a un numeral tipográfico grande (`var(--font-display)`, peso 500) como recurso gráfico en vez de una imagen inventada.

Ningún cambio toca `.id-cards`/`.id-card` de forma global: la miniatura de `#libros .id-card__media` está scopeada a esa sección concreta de `autor.html` para no afectar a herramientas, editoriales, mapa del sitio ni el resto de usos compartidos de esa clase.
