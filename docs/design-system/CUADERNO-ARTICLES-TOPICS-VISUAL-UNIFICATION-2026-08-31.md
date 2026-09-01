# Cuaderno · artículos y temas — contrato de unificación visual · 2026-08-31

## Trazabilidad

Esta intervención continúa la cadena `DISEÑO -` después de #278 Ferias.

Base de apertura: `1ba8483b019b8d307a2194ac96d0f58e0c6a2ba7` de `design/ferias-visual-unification-2026-08-30`.

La PR #269 (`DISEÑO - Cuaderno · unificación visual del índice editorial`) dejó `/cuaderno/` técnicamente cerrado y aisló deliberadamente los artículos individuales. Su propio contrato usa `/cuaderno/que-es-el-portal-fantasy/` como control de aislamiento. Esta nueva superficie no reabre el índice: completa la familia que #269 dejó fuera.

No mergear fuera de orden. Mantener Draft hasta revisión automatizada, visual y física.

## Objetivo

Unificar visualmente los artículos largos y las colecciones temáticas del Cuaderno con el sistema editorial azul/negro/dorado establecido por #163 y desarrollado por #269, preservando su función principal: lectura larga, consulta, navegación temática y autoridad editorial.

No convertir los artículos en landing pages, dashboards ni colecciones de cards. El cuerpo de lectura debe seguir siendo predominantemente tipográfico y neutro; azul y dorado deben construir jerarquía, aperturas, rails, reglas, estados y continuidad, no colorear todo el texto.

## Superficies públicas detectadas

Según el sitemap del HEAD heredado, la familia pública/indexable incluye al menos:

### Artículos

- `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`
- `/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/`
- `/cuaderno/portal-fantasy-vs-fantasia-epica/`
- `/cuaderno/que-es-el-portal-fantasy/`
- `/cuaderno/worldbuilding-noveris-ciudad-magica/`

### Colecciones temáticas

- `/cuaderno/temas/`
- `/cuaderno/temas/fantasia-de-portales/`

Antes de modificar producción, reconciliar esta lista con el sitemap y `meta[name="robots"]` reales del HEAD de la rama. No incorporar automáticamente rutas `noindex` o borradores solo porque existan en el árbol.

## Fuera de alcance

- `/cuaderno/` — cerrado por #269.
- `/recomendaciones/` y sus listas — familia propia; tendrá una PR separada.
- contenido editorial, afirmaciones, fechas, citas y enlaces, salvo bug factual demostrado.
- generación de nuevas URLs o nuevos artículos.
- SEO/schema salvo regresión demostrada.
- rediseño del shell global.

## Owners y arquitectura existentes

Los artículos consumen principalmente:

- `assets/v1-editorial.css`
- shell V1 y navegación contextual de Cuaderno
- runtime existente de lectura/TOC/share/print cuando corresponda.

Las colecciones temáticas consumen:

- `assets/v1-cuaderno-topics.css`
- `data-family="cuaderno-topics"`
- shell V1 y navegación contextual de Cuaderno.

La solución debe aprovechar estos owners existentes. Evitar una hoja por artículo y evitar reglas globales que contaminen `/cuaderno/`, Recomendaciones u otras familias.

## Hallazgos objetivos ya verificados

### 1. Capitular con azul legacy

`assets/v1-editorial.css` conserva en la primera letra de la prosa:

```css
color:#0075b8;
```

Ese color pertenece a la identidad anterior y no coincide con el azul editorial aprobado `#1d4f96`.

Debe corregirse de forma scopeada y comprobarse contraste/legibilidad sobre el fondo real.

### 2. Temas conserva theme-color beige anterior

`/cuaderno/temas/` declara:

```html
<meta name="theme-color" content="#F4EFE7">
```

La página usa `v1-cuaderno-topics.css` y todavía no ha pasado por la unificación final de la cadena. Reconciliar el `theme-color` con el shell actual sin introducir un color arbitrario ni alterar PWA fuera de esta familia.

### 3. #269 confirma aislamiento deliberado

La ausencia de tratamiento azul/dorado en artículos no es motivo para modificar #269: esa PR declaró expresamente que `cuaderno-index.css` solo se carga en el índice y que los artículos mantienen el sistema compartido de lectura.

Esta PR debe completar esa separación de forma explícita y mantener un control de aislamiento de vuelta hacia `/cuaderno/`.

## Dirección visual

### Artículos largos

- Mantener Newsreader/serif y negro/neutros como soporte principal de lectura.
- H1, deck, metadatos y apertura deben ganar continuidad con el sistema azul/dorado sin competir con el cuerpo.
- La capitular puede utilizar el azul editorial; comprobar que no parezca un elemento decorativo desconectado.
- TOC: tratarlo como índice editorial/rail de navegación, no como sidebar SaaS.
- `aria-current` del TOC debe ser visible y accesible.
- notas, blockquotes y figuras: rails/reglas coherentes; brackets no son el patrón por defecto para imágenes editoriales.
- tablas: conservar función y reflow; evitar scroll horizontal innecesario a zoom 200 %.
- reading progress: conservar runtime y adaptar solo presentación si todavía filtra un color legacy.
- share/print: conservar reservas anti-CLS y estados funcionales ya existentes.
- newsletter/continuidad final: coherente con #269 pero sin copiar mecánicamente su composición.

### Colecciones temáticas

- Tratar `/cuaderno/temas/` como índice editorial de colecciones, no como grid promocional.
- Mantener el folio y los ledgers/itinerarios como estructura documental.
- Introducir azul/dorado mediante jerarquía, reglas, rails y estados, no mediante fondos masivos.
- El topic detail debe sentirse como itinerario de lectura dentro del Cuaderno.
- No convertir los pasos en cards salvo necesidad funcional demostrada.

### Yellowtail

Uso selectivo. Puede servir para una apertura o acción editorial, pero no debe invadir la prosa, TOC, metadatos ni listas. Verificar legibilidad real, font swap y CLS.

## Tokens de referencia

- azul editorial: `#1d4f96`
- azul profundo: `#0d2c57`
- dorado canónico: `#b8860b`
- fondo pálido cuando proceda: `#eefaff`
- texto y metadatos: conservar negros/neutros del sistema.

No aplicar estos valores a ciegas si el owner ya dispone de tokens locales equivalentes; preferir variables scopeadas y evitar hardcodes repetidos.

## Contrato factual/SEO a preservar

Por ruta, proteger como mínimo:

- canonical;
- `meta robots`;
- único H1;
- Article/WebPage/FAQ/Breadcrumb JSON-LD existente;
- `datePublished` / `dateModified`;
- enlaces internos y externos;
- imágenes y `alt`;
- RSS link cuando exista;
- `data-reading-progress` donde corresponda;
- TOC/anchors;
- `data-nosnippet` si aparece en alguna ruta;
- impresión/share;
- navegación contextual Cuaderno;
- newsletter y shell compartido.

No “mejorar” contenido o schema durante una PR visual salvo bug independiente y demostrado.

## QA requerido

Crear un contrato browser específico de esta familia sin sustituir las autoridades existentes.

### Viewports mínimos

- 1728
- 1440
- 1280
- 1024
- seams reales que revele el CSS
- 768/767
- 601/600 si existe cambio de layout
- 411/410
- 390
- 360
- 320

### Casos representativos

No hace falta capturar cada artículo en cada viewport si comparten exactamente owner/estructura. Seleccionar representantes que cubran las variantes reales:

- un artículo largo con TOC/FAQ;
- un artículo con figuras o tabla si existe;
- `/cuaderno/temas/`;
- `/cuaderno/temas/fantasia-de-portales/`;
- `/cuaderno/` como control de aislamiento.

Si al inventariar se detectan arquitecturas distintas, ampliar la matriz en vez de asumir homogeneidad.

### Gates

- cero overflow horizontal;
- zoom 200 %;
- text spacing WCAG;
- teclado/focus;
- no-JS donde el contenido deba seguir disponible;
- fuentes cargadas/estables antes de medir geometría;
- CLS sin regresiones por share/print/font swap;
- reading progress funcional, no una segunda implementación;
- TOC/anchors funcionales;
- print legible;
- aislamiento hacia `/cuaderno/` y Recomendaciones;
- imágenes lazy cargadas/decodificadas antes de screenshots de evidencia;
- screenshots full-page en desktop/tablet/móvil y seams relevantes.

No relajar umbrales para obtener PASS. No usar `overflow:hidden` para ocultar defectos de reflow.

## Revisión humana

Después de QA automático revisar al menos:

- 1440×1000;
- 1280×800;
- 1024×768;
- 768×1024;
- 390×844;
- 360×800;
- seams reales.

Comprobar especialmente ritmo de lectura, anchura de prosa, relación TOC/prosa, longitud de títulos, capitular, jerarquía de metadatos, tablas, blockquotes, figuras, continuidad final y sensación de publicación editorial — no de plantilla de blog.

La revisión de screenshots no sustituye el contrato físico `docs/design-system/REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.

## Definition of Done

- rutas públicas de artículos/temas reconciliadas;
- fugas legacy eliminadas sin recolorear la prosa;
- sistema azul/dorado reconocible pero contenido;
- lectura larga preservada o mejorada;
- `Cuaderno` hub no contaminado;
- Recomendaciones no contaminadas;
- SEO/schema/contenido preservados;
- responsive/zoom/text spacing/teclado/print verdes;
- evidencia visual generada y revisada;
- CI verde sobre HEAD final;
- revisión física pendiente explícita o completada con evidencia real;
- PR permanece Draft y sin merge automático.
