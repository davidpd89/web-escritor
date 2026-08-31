# A.11 · Revalidación de producción · 2026-08-29

Corrección factual: 2026-08-31.

## Veredicto

**CONDITIONAL · IMAGE_TRIGGER_NOT_MET · HOME_VIDEO_EXISTS_BUT_NOT_A_WATCH_PAGE · NO_MEDIA_SITEMAP_CODE**

A.11 sigue siendo una capacidad técnicamente válida, pero el `main` vivo no demuestra hoy un problema que justifique añadir extensiones `image:` o `video:` al sitemap.

La corrección del 31/08 es importante: la revisión inicial afirmó que no existía `<video>` en `main`. Sí existe una intro cinematográfica en HOME. Esa media, sin embargo, no convierte HOME en una watch page ni activa por sí sola un video sitemap.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.
- `scripts/build-sitemap.py`.
- Home, ficha de Manecillas y ficha de Samuel.
- `scripts/check-responsive-images.py` y autoridades existentes de imagen/social cards.
- inventario directo de `VideoObject`, `<video>`, `assets/video/` y embeds de terceros.
- documentación oficial vigente de Google Search Central, incluida la actualización de Video SEO de agosto de 2026.

## Imagen · trigger no cumplido

Google define los image sitemaps como una ayuda especialmente útil para imágenes que no podría descubrir normalmente, por ejemplo imágenes alcanzadas mediante JavaScript.

Las imágenes estratégicas inspeccionadas no están ocultas de esa forma:

- Manecillas expone la portada en un `<picture>` con `<img>` real, `src` estable, `alt`, dimensiones, preload y `fetchpriority=high`;
- la misma página declara `og:image`, `Book.image` y `WebPage.primaryImageOfPage`;
- Samuel expone portada e imágenes editoriales como `<img>` normales y declara `og:image` + `Book.image`;
- Home conserva imágenes editoriales relevantes en HTML rastreable/no-JS aunque su composición principal se mejore con JavaScript;
- las superficies estratégicas usan `max-image-preview:large`;
- el repo ya tiene checks de responsive images, social cards, formatos y assets.

Por tanto, **la mera ausencia de `image:image` no constituye deuda**. No se ha demostrado una imagen estratégica que solo sea alcanzable mediante interacción/JS o que Google no pueda descubrir por HTML/metadata normal.

## Vídeo · inventario corregido

`VideoObject` no aparece en el inventario inspeccionado y tampoco se han localizado embeds `youtube.com/embed` como superficie propietaria. Pero HOME sí contiene:

```html
<video class="intro__video" muted playsinline preload="auto" poster="assets/hero-tinta-poster.jpg?v=2" data-hero-video>
  <source src="assets/video/hero-tinta-david-porto.webm?v=2" type="video/webm" />
  <source src="assets/video/hero-tinta-david-porto.mp4?v=2" type="video/mp4" />
</video>
```

Los assets existen en `main`:

- `assets/video/hero-tinta-david-porto.webm` (~602 KB);
- `assets/video/hero-tinta-david-porto.mp4` (~630 KB).

#163 no introdujo el vídeo: su patch de `index.html` solo cambia el query de `v1-home.css`. Por tanto esta intro ya pertenecía al baseline de A.11 y la afirmación anterior `<video> = 0` queda invalidada.

## Por qué el trigger de video sitemap sigue sin cumplirse

La guía vigente de Google Search Central (`https://developers.google.com/search/docs/appearance/video`) aclara que para ser elegible para video features:

- la watch page debe estar indexada;
- el vídeo debe estar embebido en una watch page;
- una watch page tiene como propósito principal mostrar un único vídeo;
- páginas donde el vídeo es complementario al resto del contenido no son watch pages.

HOME es la entrada editorial general al sitio y la secuencia de tinta funciona como intro/complemento de marca. Ver ese vídeo no es la razón principal por la que el usuario visita la URL.

No se debe fabricar una landing de vídeo, `VideoObject` ni un sitemap `video:` únicamente para convertir esta intro en una superficie SEO. El fichero ya está referenciado directamente mediante `<video>/<source>` y Google puede localizar vídeos referenciados por elementos HTML comunes; la ausencia de un video sitemap no es aquí una deuda demostrada.

La clasificación de accesibilidad de la intro pertenece a F.3 y su compatibilidad Safari/iPhone a #163. Son owners distintos de A.11.

## Decisión de arquitectura

No modificar hoy `scripts/build-sitemap.py`.

Si el trigger futuro aparece:

1. extender el generador actual; no crear un inventario paralelo;
2. derivar media desde HTML/autoridades ya existentes;
3. mantener canonical/noindex/public-dist como filtros;
4. emitir namespaces solo cuando existan entradas reales;
5. añadir fixtures/tests de XML, determinismo y drift;
6. para vídeo, exigir primero watch page + thumbnail estable + `contentUrl` o `embedUrl` verificable.

## Triggers de reapertura

### Imagen

Reabrir si se identifica una imagen editorial importante que:

- no esté presente en HTML rastreable/renderizado sin interacción;
- dependa de carga JS que dificulte descubrimiento;
- o presente evidencia reproducible de descubrimiento deficiente en Search Console/Google Images.

### Vídeo

Reabrir cuando exista al menos una watch page pública/indexable cuyo propósito principal sea reproducir un vídeo real y haya una necesidad de discovery/metadata que el HTML normal no resuelva suficientemente.

## Fuentes primarias revalidadas

- Google Search Central · Image sitemaps: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps`.
- Google Search Central · Video sitemaps and alternatives: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/video-sitemaps`.
- Google Search Central · Video SEO best practices: `https://developers.google.com/search/docs/appearance/video`.
- Google Search Central · Image SEO best practices: `https://developers.google.com/search/docs/appearance/google-images`.

## Cierre

A.11 queda correctamente **condicionada**, pero el trigger de sitemap multimedia no está activo. La corrección de inventario no cambia el resultado de producto: existe media de vídeo en HOME, pero no una watch page que justifique `video:`.

La PR puede revisarse/mergearse como autoridad documental y guardrail de reapertura. Mantener DRAFT hasta revisión final.