# 07 — Imágenes, vídeo, Discover, News y superficies visuales

## Objetivo

No tratar Google como diez enlaces azules únicamente. La misma URL/contenido puede participar en:

- Search web;
- Google Images;
- Discover;
- resultados con imagen;
- vídeo;
- News cuando corresponda;
- AI surfaces cubiertas en `docs/ai-discoverability/`.

---

# 1. Imágenes: estado actual

La web ya tiene:

- portadas en WebP/AVIF/JPG;
- `og:image`;
- `twitter:image`;
- `ImageObject` en varias entidades;
- alt text;
- image preload/fetchpriority en heroes;
- workflow de image format ladder;
- `max-image-preview:large` en páginas editoriales principales.

Esta es una base sólida.

---

# 2. Google Images: principios

Google necesita:

- descubrir la imagen;
- poder rastrearla;
- entender su contexto;
- una landing page indexable cuando corresponde.

## 2.1 Usar elementos HTML estándar

Para imágenes importantes usar `<img src>`/`srcset`.

Google no trata una imagen CSS background como equivalente para indexación de imágenes.

Las imágenes decorativas pueden seguir en CSS.

## 2.2 Contexto

La imagen debe estar cerca de texto que explique:

- qué representa;
- entidad;
- obra;
- evento.

No depender exclusivamente de filename/alt.

## 2.3 Alt

El alt es accesibilidad primero y también ayuda a contexto.

Bueno:

`Portada de Las manecillas del recuerdo, novela de David Porto Díaz`

Malo:

`libro novela libro escritor novela coral comprar libro David Porto Díaz mejor novela 2026`

## 2.4 Filename

Descriptivo y estable cuando se crea un asset nuevo.

No renombrar todas las imágenes existentes solo para meter keywords si eso rompe cache/links sin beneficio claro.

---

# 3. Imágenes prioritarias

## Autor

- retrato oficial;
- alt factual;
- Person.image;
- alta calidad;
- formatos responsivos;
- misma identidad visual en perfiles externos cuando sea viable.

## Libros

- portada frontal limpia;
- OG horizontal;
- fotos promocionales reales/creativas cuando aporten;
- Book.image;
- landing correcta.

## Eventos

- foto real del evento;
- lugar/persona/libro contextualizados;
- no stock genérico si existe foto propia.

## Cuaderno

No reutilizar la misma imagen genérica de Noveris para 20 artículos si podemos producir una imagen realmente representativa.

La repetición no es una penalización, pero reduce diferenciación visual.

---

# 4. Discover

No hay solicitud ni schema especial para entrar en Discover.

El contenido indexable y conforme puede ser elegible automáticamente.

Google recomienda:

- titles/headings que reflejen la esencia;
- no clickbait;
- temas actuales o historias bien contadas/información única;
- imágenes relevantes de alta calidad.

## Imágenes Discover

Recomendación oficial 2026:

- al menos 1200 px de ancho;
- más de 300.000 píxeles totales;
- idealmente formato horizontal 16:9 útil para recorte;
- `max-image-preview:large`.

### Acción

Auditar los artículos con potencial Discover:

- image width;
- horizontal crop;
- calidad;
- relevancia;
- OG/schema.

---

# 5. Discover para este proyecto

Tipos con mayor encaje:

- lanzamiento de libro;
- experiencia real en Feria del Libro;
- detrás de cámaras con imágenes propias;
- procesos creativos visuales;
- artículos oportunos dentro del nicho;
- novedades literarias propias;
- eventos.

Menor encaje:

- contador de palabras evergreen;
- fichas de directorio puramente utilitarias;
- páginas legales.

No modificar evergreen para «hacerlo Discover».

---

# 6. February 2026 Discover update

Google registró un Discover update iniciado el 05/02/2026 y de aproximadamente 21d17h.

La documentación/guía actual pone énfasis en:

- utilidad;
- originalidad;
- relevancia;
- evitar clickbait.

Regla: medir Discover separado de Web Search. Una caída/subida Discover no debe interpretarse automáticamente como cambio de ranking web.

---

# 7. Google News

Desde finales de marzo de 2025 Google News utiliza páginas de publicación generadas automáticamente.

Ya no se presenta Publisher Center como un mecanismo para «enviar el sitio a Google News».

El contenido elegible se considera automáticamente.

## Decisión

No crear un proyecto «dar de alta Cuaderno en Google News» siguiendo tutoriales antiguos.

---

# 8. ¿Debe Cuaderno aspirar a Google News?

No como objetivo principal.

El Cuaderno es una publicación editorial de autor, no una redacción de noticias.

Puede producir piezas con encaje News si realmente son:

- actuales;
- originales;
- transparentes;
- con fechas/byline;
- relevantes.

Ejemplos:

- anuncio confirmado de un evento;
- lanzamiento;
- crónica original de Feria;
- noticia propia del autor.

No transformar artículos evergreen en «noticias» cambiando fechas.

---

# 9. Transparencia News

Google News pide claridad sobre:

- fechas;
- bylines;
- autores;
- publicación/editor;
- entidad detrás del contenido;
- contacto.

El sitio ya tiene:

- Autor;
- contacto;
- byline/schema en artículos;
- fechas.

Mantener esa transparencia.

---

# 10. News sitemap

No crear ahora por defecto.

Solo si existe una producción consistente de contenidos news-eligible que lo justifique.

Un sitemap normal ya cubre indexación web.

No confundir News sitemap con permiso/aceptación en Google News.

---

# 11. Video: oportunidad condicionada

Google puede mostrar vídeo en:

- Search;
- Videos;
- Images;
- Discover.

Pero no tenemos que producir vídeo por SEO si no existe una estrategia editorial real.

## Casos de alto valor potencial

- presentación/entrevista;
- lectura de fragmento autorizada;
- explicación de Noveris;
- proceso de escritura;
- herramienta explicada;
- Feria/evento;
- book trailer realmente bueno.

---

# 12. Watch pages

Para que un vídeo pueda acceder a features específicas, Google recomienda una página dedicada donde ver ese vídeo sea el propósito principal.

Si en el futuro hay una biblioteca de vídeos:

`/videos/<slug>/`

con:

- vídeo visible;
- title/description únicos;
- transcript;
- thumbnail estable;
- VideoObject;
- enlaces a libro/artículo relacionados.

No crear watch pages para clips de 5 segundos decorativos.

---

# 13. YouTube vs self-hosted

YouTube puede ser la plataforma lógica para alcance.

Una misma pieza puede:

- vivir en YouTube;
- tener watch/article page en la web;
- enlazarse mutuamente.

Google puede indexar ambas versiones.

No asumir que embeber YouTube transfiere automáticamente ranking a la página.

## Ventaja web

La página propia puede añadir:

- transcript;
- contexto;
- fuentes;
- enlaces al libro;
- imágenes;
- materiales.

---

# 14. Transcript

Un transcript real y revisado:

- mejora accesibilidad;
- permite lectura;
- aporta contenido indexable;
- ayuda a entender el vídeo.

No publicar un transcript automático lleno de errores sin revisión.

---

# 15. VideoObject

Solo para vídeos reales.

Campos principales:

- name;
- description;
- thumbnailUrl;
- uploadDate;
- duration;
- embedUrl/contentUrl según caso.

Las URLs de media y thumbnail deben ser estables.

---

# 16. Key Moments

Google puede detectar momentos automáticamente y también existen mecanismos de markup/description según plataforma.

No priorizar hasta tener vídeos suficientemente largos/valiosos.

Para entrevistas/charlas, capítulos claros son útiles también para humanos.

---

# 17. ImageObject en libros

Manecillas ya usa `primaryImageOfPage` y Book.image.

Samuel usa `ImageObject`.

Revisar:

- content URL estable;
- dimensiones correctas;
- no referencias a source bloqueada;
- imagen visible.

---

# 18. OG como fuente de imagen preferida

Google puede considerar imágenes indicadas en:

- structured data `image`;
- `og:image`;
- contenido.

La documentación de 2026 reforzó prácticas para preferred image.

## Regla

OG no es solo social. Debe apuntar a un asset:

- representativo;
- crawlable;
- suficientemente grande;
- estable.

---

# 19. Image sitemap: decisión

Antes de construirlo, medir si Google Images ya descubre:

- portadas;
- autor;
- eventos;
- assets principales.

Si sí, no añadir complejidad por ritual.

Si no:

- generar image sitemap desde public dist/registry;
- solo imágenes relevantes;
- no incluir assets decorativos/iconos;
- no introducir URLs privadas/source.

---

# 20. Licensable image metadata

Solo si existe una política real de licencia/uso de imágenes.

Google admite metadata de licencia mediante structured data/IPTC.

No inventar una licencia solo para obtener badge.

Para press kit puede ser útil definir de forma editorial:

- qué fotos se pueden usar;
- condiciones;
- crédito.

Entonces sí puede evaluarse metadata coherente.

---

# 21. Social/video platform Search

Search Console 2026 incorpora Platform Properties para medir Instagram/TikTok/X/YouTube en Google.

Esto se gestiona en `docs/search-console/`.

SEO editorial debe asegurar que perfiles públicos mantengan:

- nombre consistente;
- bio clara;
- links oficiales;
- titles de libros correctos;
- no datos contradictorios.

No duplicar tracking aquí.

---

# 22. Pinterest

Dado el carácter visual de portadas/frases/universo:

Pinterest puede producir imágenes indexables/referencias externas.

Regla:

- contenido visual propio;
- enlace canónico al recurso adecuado;
- descriptions humanas;
- no generar miles de pins keyword-stuffed.

No se presenta Pinterest como factor directo de Google ranking.

---

# 23. Image performance

SEO visual no debe empeorar CWV.

Usar:

- responsive srcset;
- width/height para evitar CLS;
- formatos modernos;
- lazy loading below fold;
- preload/fetchpriority solo hero/LCP;
- compresión razonable.

No preloadear diez imágenes.

---

# 24. Image alt contract

Crear auditoría:

- imágenes informativas: alt útil;
- decorativas: alt vacío cuando proceda;
- portadas: title + autor;
- retrato: nombre/rol si aporta;
- no filename como alt;
- no keyword stuffing.

---

# 25. Oportunidades editoriales visuales

## Manecillas

- portada;
- libro físico 3D/fotografía realista;
- reloj/objeto central;
- presentación;
- firma;
- imágenes de proceso editorial autorizables.

## Samuel

- portada;
- Noveris;
- Feria del Libro;
- club;
- mapa/lore solo si es canónico.

## Herramientas

Capturas o ilustraciones solo si ayudan a comprender. Una herramienta de texto no necesita una imagen stock de una máquina de escribir.

---

# 26. No hacer

- clickbait de Discover;
- imágenes sexualizadas/impactantes irrelevantes para ganar clics;
- cambiar title por curiosidad vacía;
- stock genérico masivo;
- imágenes generadas que simulan hechos reales/eventos;
- vídeo vacío por SEO;
- News submission manual obsoleto;
- fechas artificialmente frescas;
- NewsArticle para todo el Cuaderno;
- VideoObject para GIFs decorativos.

---

# 27. Automatización

## `scripts/seo/audit-media.py`

Por URL:

- `<img>` count;
- hero image;
- width/height;
- alt;
- srcset;
- loading;
- OG image;
- schema image;
- size/dimensions known;
- Discover >=1200 candidate;
- CSS-only important image warning.

## `data/media-registry.json` opcional

Solo para assets editoriales clave:

- entity;
- role;
- source;
- dimensions;
- rights;
- credit;
- public.

---

# 28. Acceptance criteria

- portadas/autor rastreables con `<img>`/schema/OG;
- artículos prioritarios tienen imágenes representativas;
- candidatos Discover cumplen imagen grande cuando posible;
- no clickbait;
- News no se trata como formulario de alta;
- dates/bylines transparentes;
- vídeo se implementa solo con corpus real;
- future watch pages si hay estrategia;
- no image sitemap sin necesidad demostrada;
- SEO de imágenes no degrada LCP/CLS.
