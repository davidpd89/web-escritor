# Escalera de formatos AVIF → WebP (L.1, 2026-08-23)

## Alcance frente a otras piezas relacionadas

- **#61 H.3** (`scripts/check-responsive-images.py`) sigue siendo la
  autoridad de **geometría responsive**: `width`/`height`, `srcset`/
  `sizes`, coherencia de `loading`/`fetchpriority`. Este documento **no
  duplica** esos checks.
- **L.1** se limita a la **escalera de formatos**: qué imágenes deben
  ofrecer AVIF además de WebP, cómo se generan y cómo se verifica que no
  falten ni queden desincronizadas del fallback.

## Política de elegibilidad

Solo las rutas WebP listadas explícitamente en
`data/image-format-ladder.json` (`eligible_sources`) reciben un AVIF
hermano. **No** se convierte `/assets/` de forma indiscriminada. Quedan
excluidos por diseño:

- imágenes de OG/redes sociales (necesitan una URL estable en un formato
  de amplio soporte para scrapers externos que no entienden AVIF);
- materiales de trabajo / imágenes no publicadas;
- cualquier PNG/JPEG que deba conservarse por transparencia, fidelidad o
  compatibilidad, y donde convertir no compense.

La lista actual cubre la cubierta de *Las manecillas del recuerdo* en sus
4 tamaños responsive (320/512/768/1024px), usada en Home y en las
superficies principales de Manecillas. El retrato de Home
(`david-porto-foto-portada-sinfondo`) ya tenía su AVIF desde antes de esta
PR y sigue el mismo patrón.

## Pipeline

- `scripts/build-image-format-ladder.py`: genera el `.avif` que falte para
  cada fuente elegible (Pillow, calidad 60 por defecto), preservando
  dimensiones exactas. `--check` no escribe, solo falla si falta alguno.
- `scripts/check-image-format-ladder.py`: gate de CI. Verifica que:
  1. cada fuente elegible tiene su `.avif` en disco con las mismas
     dimensiones que el `.webp`;
  2. toda referencia HTML a esa fuente dentro de un `<picture>` tiene un
     `<source type="image/avif">` con el mismo `media` **inmediatamente
     antes** en el documento (para que el navegador lo priorice sobre el
     WebP cuando lo soporte);
  3. el `<img>` de fallback sigue siendo WebP — AVIF nunca sustituye al
     fallback, solo se añade como `<source>` adicional.

## Verificación real

- Ahorro de peso real medido (mismo contenido, mismas dimensiones):
  320px −41 %, 512px −38 %, 768px −36 %, 1024px −35 %.
- Verificado en navegador real (`qa/image-format-ladder-browser.mjs`,
  Chromium): la Home solicita efectivamente el `.avif` de la cubierta, no
  el `.webp`, y el aspect ratio renderizado no cambia.
- No se ha tocado ninguna URL de `og:image`/`twitter:image`/JSON-LD
  `image`/`contentUrl`: siguen apuntando al `.webp` estable.

## Cómo añadir una nueva superficie elegible

1. Añadir la ruta WebP a `eligible_sources` en
   `data/image-format-ladder.json`.
2. `python scripts/build-image-format-ladder.py` genera el `.avif`.
3. En el HTML, anteponer un `<source type="image/avif" media="...">` (o
   sin `media` para el `<source>` que precede al `<img>` de fallback) con
   la misma condición de `media` que su `<source>`/`<img>` WebP
   equivalente.
4. `python scripts/check-image-format-ladder.py --check` debe quedar en
   verde.
