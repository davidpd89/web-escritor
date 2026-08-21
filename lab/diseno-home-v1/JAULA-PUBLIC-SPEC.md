# Dónde empieza la jaula — contrato público V1

Estado: **AUTORIZADO PARA PREPARAR / NO PUBLICAR HASTA QUE EXISTA LA RUTA REAL EN STAGING**.
Ruta prevista: `/donde-empieza-la-jaula/`.
Estado editorial visible: `En desarrollo`.
Tipo factual permitido: `Novela en desarrollo`.
Autor: David Porto Díaz.

## Fuente canónica del contenido

Google Drive: `01 - DÓNDE EMPIEZA LA JAULA — MANUSCRITO ANÓNIMO UMBRIEL.docx`
ID: `1bfo_20JoPw3W_oHK8k-G1rd3v-K1Jfvx`

El manuscrito se identifica como novela y contiene 42 capítulos. Para la web V1 se autoriza únicamente el **capítulo 1 completo** como muestra pública en esta fase.

Contrato de extracción exacta:
- inicio: heading `CAPÍTULO 1`, cuyo primer párrafo comienza `El orbe salía del agua y subía.`;
- fin: inmediatamente antes del heading `CAPÍTULO 2`;
- no corregir, resumir ni reescribir el capítulo durante la integración web;
- si el manuscrito canónico cambia antes de publicar, volver a extraer el capítulo de la versión canónica y no mantener una copia antigua por inercia.

## Copy de cabecera autorizado

**En desarrollo**

# Dónde empieza la jaula

David Porto Díaz

Noa tiene diecinueve años, trabaja junto al muelle y carga con sueños que no consigue tratar como simples sueños. Entre turnos, familia y la memoria pública de los portadores, algo empieza a abrir una grieta en una vida medida hasta entonces por horarios, reparaciones y mareas.

CTA principal: `Leer el primer capítulo` → `#capitulo-1`.
CTA secundaria: `Volver a Obras` → `/libros/`.

## Arquitectura mínima

1. shell global vigente;
2. breadcrumb cuando corresponda;
3. cabecera factual anterior;
4. sin portada ficticia ni placeholder con iconografía narrativa;
5. `<section id="capitulo-1" aria-labelledby="jaula-capitulo-1">` con el capítulo 1 íntegro en HTML seleccionable/indexable;
6. cierre editorial breve + retorno a Obras;
7. relacionados únicamente si son relaciones reales y aprobadas;
8. sin compra, retailers, ISBN, editorial, fecha o promesa de publicación mientras no existan.

## SEO / schema

- H1 único: `Dónde empieza la jaula`.
- canonical a `/donde-empieza-la-jaula/` cuando la ruta se publique.
- meta title/description factuales; no claim de lanzamiento.
- capítulo visible en HTML, no canvas/imagen/accordion.
- no `Book` con `publicationDate`, ISBN o publisher inventados.
- puede usarse `WebPage` y, si aporta, `CreativeWork` con propiedades verificables únicamente.
- no duplicar el capítulo completo en otra URL indexable sin canonical/estrategia explícita.

## Media

No existe cubierta oficial aprobada para este contrato. La página debe demostrar que la familia Libro funciona sin portada. Si aparece una cubierta oficial, se integra más adelante sin rediseñar la arquitectura.

## Prohibido

- inventar portada, jaula, loba, orbe, hada o mapa como asset sintético;
- publicar lore de capítulos posteriores por completar la ficha;
- asignar género comercial específico no aprobado;
- obligar a newsletter para acceder al capítulo;
- presentar la obra como publicada, próxima o contratada;
- enlazar la ruta desde producción antes de comprobar que responde 200 y está incluida en el sistema de descubrimiento vigente.

## Gate de aceptación

La página debe aportar valor aun sin portada: estado claro, contexto breve y lectura real. Falla si parece un teaser vacío, una landing de captación o una ficha de libro publicado.
