# A.11 · Sitemap de imágenes y vídeo

Fecha de reconstrucción: 2026-08-29  
Idea original: ampliar el sitemap con extensiones `image:` / `video:` para mejorar descubrimiento de media estratégica.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: `CONDITIONAL`; documentación/auditoría, no implementación automática.

## Veredicto reconciliado

**CONDITIONAL. NO AÑADIR IMAGE/VIDEO SITEMAPS POR CHECKLIST.**

La investigación de #135 mantuvo A.11 como válida técnicamente, pero condicionada a demostrar un problema de descubrimiento real. La inspección actual confirma que `scripts/build-sitemap.py` solo genera `<loc>` y `<lastmod>` y no usa namespaces de imagen/vídeo. Que la capacidad no exista no demuestra que haga falta.

La decisión debe separar dos casos:

- **imagen:** auditar media editorial estratégica y su descubribilidad/relevancia antes de tocar el sitemap;
- **vídeo:** no crear sitemap de vídeo mientras no haya watch pages o vídeo principal indexable que lo justifique.

## 1. Hipótesis original de #135

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` propuso:

> Si `build-sitemap.py` no genera ya `image:` / `video:` sitemap extensions, añadirlas para mejorar descubrimiento en Google Images/Video, especialmente portadas y booktrailers.

Era una hipótesis, no una tarea aprobada.

## 2. Evolución cronológica en #135

### 2.1 · Revisión exhaustiva → `CONDITIONAL`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` corrigió el impulso inicial:

- image/video sitemaps son formatos válidos;
- tienen más sentido para media difícil de descubrir;
- primero hay que inventariar media estratégica;
- no complicar `sitemap.xml` sin evidencia.

Valor estimado: medio. Coste: medio.

### 2.2 · Override específico A.11 → trigger estricto

`docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` mantuvo `CONDITIONAL` y cerró la ambigüedad:

1. inventariar portadas, retratos, prensa y vídeo editorial;
2. comprobar cómo aparecen en HTML;
3. confirmar si Google puede descubrirlos mediante `<img>` / página normal;
4. comprobar Search Console/Bing si existe problema real;
5. añadir extensiones solo a los elementos afectados.

Para vídeo dejó una regla explícita: **no crear sitemap de vídeo solo porque exista una intro decorativa**. Si se busca elegibilidad de vídeo, primero debe existir contenido de vídeo principal/watch page real.

### 2.3 · Matriz final → `CONDICIONAL`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` mantuvo:

- image sitemap solo si la auditoría demuestra imágenes importantes poco descubribles;
- video sitemap solo con watch pages/vídeos reales;
- no crear por checklist.

### 2.4 · Casos públicos → imágenes grandes sí importan, pero no prueban necesidad de sitemap

`docs/IDEAS-MEJORA-WEB-CASOS-EVIDENCIA-Y-LIMITES-2026-08-28.md` conservó dos casos oficiales de Google Discover:

- Kirbie’s Cravings: +79% CTR tras habilitar previews grandes;
- Istoé: +30% CTR y +332% clics en seis meses.

#135 fue explícita: estos casos demuestran que una buena imagen/previsualización puede cambiar presentación y CTR; **no demuestran que añadir un image sitemap produzca esos resultados** ni permiten extrapolar porcentajes a esta web.

La acción transferible fue auditar:

- `max-image-preview:large`;
- relevancia de la imagen;
- resolución/crop;
- cobertura en URLs editoriales.

### 2.5 · Decimocuarta pasada R.72 → relevancia semántica antes que otro pipeline

`docs/IDEAS-MEJORA-WEB-DECIMOCUARTA-PASADA-2026-08-28.md` añadió un hallazgo importante relacionado:

- Google puede recibir señales de imagen principal mediante `primaryImageOfPage`, `image` en la entidad principal y `og:image`;
- la imagen debe representar realmente la página, no limitarse a ser grande;
- detectar `reuseCount > 1` debe ser trigger de revisión, no fallo automático;
- no generar cards genéricas «título sobre gradiente» para cumplir un checklist.

El ejemplo real encontrado en #135 fue que dos artículos de Cuaderno compartían `assets/og-worldbuilding-noveris-ciudad-fantastica.jpg`. Esto no prueba error, pero sí justifica una revisión humana de relevancia.

### 2.6 · Autoridad final → `CONDITIONAL`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó:

> Image/video sitemap solo si una auditoría demuestra assets/watch-pages importantes mal descubiertos. No crear por checklist.

`data/web-improvement-decisions-2026-08-28.json` mantiene el mismo estado.

### 2.7 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` revisó A.1–A.12 y **no cambió A.11**. Las correcciones materiales de esa falsación fueron otras ideas.

Secuencia final:

```text
hipótesis: añadir image/video extensions
→ revisión: técnicamente válidas, pero condicionales
→ override: trigger estricto de descubribilidad
→ casos: media grande/relevante puede importar, sin atribuir efecto al sitemap
→ R.72: auditar imagen preferida y relevancia semántica
→ autoridad final: CONDITIONAL
→ revalidación: se mantiene
```

## 3. Estado real de `main` en 2026-08-29

### Sitemap actual

`scripts/build-sitemap.py`:

- genera `sitemap.xml` determinista;
- usa namespace estándar `http://www.sitemaps.org/schemas/sitemap/0.9`;
- deriva URLs de HTML público/canonical;
- excluye `noindex`, feeds y superficies no públicas;
- usa `dateModified` fiable para `<lastmod>`;
- solo emite `<loc>` y `<lastmod>`;
- no contiene namespace ni elementos `image:` / `video:`.

Esto confirma la premisa técnica original: la extensión no existe.

### Autoridades de imagen existentes que deben reutilizarse

No crear un segundo inventario paralelo. Ya existen, entre otros:

- `data/image-format-ladder.json`;
- `scripts/build-image-format-ladder.py`;
- `scripts/check-image-format-ladder.py`;
- `scripts/check-responsive-images.py`;
- `scripts/check-social-cards.py`;
- builders de social cards;
- metadata OG/Twitter;
- `ImageObject`/imágenes en JSON-LD donde procede;
- `max-image-preview:large` en superficies estratégicas.

Cualquier futuro image sitemap debe derivarse de autoridades existentes + HTML público, no de una nueva lista manual de assets.

### Vídeo

La búsqueda actual no localiza `VideoObject` en el repo. La ausencia de un archivo `.mp4` local por sí sola tampoco sería prueba suficiente: un futuro embed externo podría ser indexable. El gate correcto es inventariar **páginas públicas donde el vídeo sea contenido principal**, no extensiones de archivo.

## 4. Fuentes primarias revalidadas

Google Search Central:

- Image sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps
- Video sitemaps: https://developers.google.com/search/docs/crawling-indexing/sitemaps/video-sitemaps
- Google Images / image SEO: https://developers.google.com/search/docs/appearance/google-images
- Guía IA generativa 2026: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

Principios que importan:

- image sitemaps son especialmente útiles para imágenes que Google podría no descubrir normalmente;
- video sitemaps ayudan a aportar información sobre vídeos, en especial cuando son nuevos/difíciles de descubrir;
- cumplir formato no garantiza indexación ni aparición;
- en búsqueda generativa no existe un sitemap «especial de IA»; imágenes/vídeos útiles y de calidad siguen las reglas normales de Search.

## 5. Gate de decisión futuro

### 5.1 · Imagen

Antes de implementar:

1. extraer por URL indexable:
   - `og:image`;
   - schema `image` / `primaryImageOfPage`;
   - `<img>` principal;
   - dimensiones;
   - bytes/formato;
   - `alt`;
   - número de reutilizaciones;
   - propietario semántico;
2. comprobar si el asset aparece en HTML rastreable sin interacción;
3. revisar páginas estratégicas: Home, Autor, Samuel, Manecillas, Cuaderno, prensa;
4. usar Search Console/Images cuando exista muestra suficiente;
5. implementar image sitemap solo para un gap demostrado.

### 5.2 · Vídeo

Reabrir únicamente cuando exista al menos una URL pública donde:

- el vídeo sea contenido principal, no decoración;
- haya título/descripcion/thumbnail estables;
- exista una URL de reproducción/embed verificable;
- la página sea indexable y elegible;
- haya una razón editorial para descubrimiento de vídeo.

Si no existe esa superficie, estado = `NO_ACTION`.

## 6. Arquitectura si el trigger se cumple

Extender `scripts/build-sitemap.py`, no crear un generador paralelo.

Requisitos:

- derivar media desde HTML/registry/manifest existentes;
- emitir namespaces solo si hay elementos reales;
- mantener sitemap determinista;
- filtrar assets de páginas `noindex`/gated/internal;
- URLs HTTPS canónicas;
- validar que el asset público existe;
- no añadir media meramente decorativa;
- conservar `--check` y comparación determinista;
- añadir tests fixtures específicos.

Para vídeo, si la complejidad hace más legible un sitemap separado, debe seguir derivándose de la misma autoridad pública y quedar enlazado/documentado sin duplicar URLs manualmente.

## 7. Tests si se implementa

- XML válido y namespaces correctos;
- media solo bajo URLs públicas/indexables;
- assets HTTPS del host o URL externa admisible según formato;
- nada de `noindex`/staging/internal;
- no duplicados;
- determinismo de build;
- `--check` detecta drift;
- `sitemap.xml` ordinario sigue en paridad con `content-registry`;
- checker de social/responsive images sigue verde;
- test de página con media ausente no genera entrada fantasma.

## 8. Qué NO hacer

- añadir todas las imágenes del sitio al sitemap por volumen;
- usar favicon/iconos/ornamentos como media estratégica;
- crear un video sitemap para una intro decorativa;
- inventar `VideoObject` sin vídeo real;
- generar una segunda base de datos de imágenes;
- asumir que image sitemap = mayor ranking;
- extrapolar +79%/+332% de los casos Discover;
- generar imágenes genéricas solo para tener una por URL;
- relajar canonical/noindex para «dar visibilidad» a media;
- enviar staging/private/gated.

## 9. Coste / beneficio

**Imagen:** coste medio; beneficio potencial medio si existe media importante difícil de descubrir. Sin ese gap, retorno marginal frente a HTML/OG/schema ya correctos.  
**Vídeo:** coste medio/alto y beneficio nulo hoy si no existe contenido de vídeo principal indexable.

## 10. Definition of Done de A.11

### Reconstrucción histórica

- [x] hipótesis original preservada;
- [x] revisión `CONDITIONAL` preservada;
- [x] override con trigger estricto preservado;
- [x] casos Discover y límites de transferibilidad preservados;
- [x] R.72 sobre imagen preferida/relevancia preservado;
- [x] autoridad final `CONDITIONAL` preservada;
- [x] revalidación independiente preservada.

### Trigger futuro

- [ ] inventario de media estratégica;
- [ ] evidencia de descubribilidad deficiente;
- [ ] decisión separada imagen/vídeo;
- [ ] solo entonces implementación y tests.

## 11. Trazabilidad del corpus de #135 revisado para A.11

Aportan contenido específico:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-CASOS-EVIDENCIA-Y-LIMITES-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-DECIMOCUARTA-PASADA-2026-08-28.md` (R.72);
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`.

También se revisaron fuentes primarias, fuentes adicionales, blueprints, cuarta–decimoquinta pasadas y repos/tooling; donde no aparece A.11 no añaden una decisión posterior distinta.

## 12. Recomendación de merge

**MERGE como reconstrucción completa de A.11, manteniendo `CONDITIONAL`.**

No hay implementación de sitemap multimedia que deba hacerse hoy únicamente porque `build-sitemap.py` no la tenga.