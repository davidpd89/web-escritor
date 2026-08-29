# A.11 · Revalidación de producción · 2026-08-29

## Veredicto

**CONDITIONAL · TRIGGER_NOT_MET · NO_CODE**

A.11 sigue siendo una capacidad técnicamente válida, pero el `main` vivo no demuestra hoy un problema que justifique añadir extensiones `image:` o `video:` al sitemap.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.
- `scripts/build-sitemap.py`.
- Home, ficha de Manecillas y ficha de Samuel.
- `scripts/check-responsive-images.py` y autoridades existentes de imagen/social cards.
- búsqueda de `VideoObject`, `<video>` y embeds de YouTube en el repo.
- documentación oficial vigente de Google Search Central.

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

## Vídeo · trigger no cumplido

La búsqueda actual no encuentra:

- `VideoObject`;
- `<video>`;
- embeds `youtube.com/embed`.

Google exige para elegibilidad de vídeo una watch page indexada donde el vídeo esté embebido y sea el contenido principal. También recomienda sitemap/structured data como mecanismos de metadata para vídeos reales, no para decorar páginas que no son watch pages.

Con el estado actual, crear `video:` produciría un pipeline sin contenido elegible que describir.

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

Reabrir cuando exista al menos una watch page pública/indexable cuyo propósito principal sea reproducir un vídeo real.

## Fuentes primarias revalidadas

- Google Search Central · Image sitemaps: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps`.
- Google Search Central · Video sitemaps and alternatives: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/video-sitemaps`.
- Google Search Central · Video SEO best practices: `https://developers.google.com/search/docs/appearance/video`.
- Google Search Central · Image SEO best practices: `https://developers.google.com/search/docs/appearance/google-images`.

## Cierre

A.11 queda correctamente **condicionada**, pero el trigger no está activo en producción. No hay implementación pendiente hoy. La PR puede revisarse/mergearse como autoridad documental y guardrail de reapertura.