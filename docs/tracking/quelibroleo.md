# Quelibroleo — libros y descubrimiento en español

Fecha de revisión: 2026-09-07

Estado: `SAMUEL_ALREADY_EXISTS · MANECILLAS_FORM_PARTIALLY_FILLED · SUBMISSION_NEEDS_AUTHOR_GO_AHEAD`

## Verificación y ejecución parcial (2026-09-08)

Con la sesión de Quelibroleo logueada como `davidpd`:

- **Samuel entre mundos ya existe**: ficha correcta con autor "PORTO
  DÍAZ, DAVID" y resumen ya cargado (0 votos/críticas, pero la ficha
  bibliográfica está bien). Nada que hacer ahí.
- **Las manecillas del recuerdo no existe** — búsqueda avanzada sin
  resultados, con un enlace directo "Si desea añadir el libro que no
  encuentra pulse aquí" → `https://quelibroleo.com/nuevo-libro`, un
  formulario de alta genuinamente autoservicio (Título, Autor, Editorial,
  Año, Género, ISBN, ISBN digital, Resumen, Crítica opcional, Voto
  opcional, Portada opcional).

Se empezó a rellenar (Título: "Las manecillas del recuerdo") y al
continuar con el campo de autor, el clasificador de permisos de la
sesión de Claude Code bloqueó la acción — mismo patrón que esta noche en
BookBrainz y BookBub: dar de alta contenido nuevo en un catálogo público
de terceros, más allá del primer campo, requiere el visto bueno explícito
del autor en vez de completarse de forma autónoma. No se ha enviado el
formulario ni se ha dejado nada a medias visible públicamente (el
formulario nunca llegó a enviarse).

**Siguiente paso real**: el autor entra a
`https://quelibroleo.com/nuevo-libro` logueado y completa: título "Las
manecillas del recuerdo", autor "Porto Díaz, David", editorial "Monza
Ediciones", año 2026, género Fantástica/ciencia ficción o Literatura
contemporánea (a su criterio), ISBN papel `9798905149351`, ISBN digital
`9798906781925`. Sin voto ni crítica (dejar en blanco: una autovaloración
del propio autor no aporta valor de comunidad real).

## Objetivo

Conseguir que `Samuel entre mundos` y `Las manecillas del recuerdo` estén correctamente presentes en Quelibroleo, una red social de libros y lectores en español, aprovechando su alta gratuita de libros sin convertir la cuenta del autor en autopromoción.

## Valor actual verificado

Quelibroleo se presenta como red social de libros y lectores en español y mantiene un catálogo de **más de 100.000 libros** organizado por género, editorial y valoración, con novedades, críticas y recomendaciones.

Fuentes:
- https://quelibroleo.com/
- https://quelibroleo.com/nuevo-libro
- https://importacion.quelibroleo.com/faq-preguntas-frecuentes

## Alta gratuita confirmada

La página `nuevo-libro` permite a usuarios registrados subir un libro con campos para:
- título;
- autor;
- editorial;
- año de primera edición;
- género;
- ISBN;
- ISBN edición digital;
- resumen;
- portada.

Eso nos da una vía directa y gratuita si Samuel o Manecillas faltan.

## Datos canónicos

### Samuel entre mundos
- autor: David Porto Díaz
- editorial: Libros Indie
- ISBN: 9791387659776
- año: 2025

### Las manecillas del recuerdo
- autor: David Porto Díaz
- editorial: Monza Ediciones
- papel ISBN: 9798905149351
- ebook ISBN: 9798906781925
- publicación papel: 2026-09-03
- publicación ebook: 2026-08-12

No fijar 422/412 o 272/266 páginas porque la pantalla de alta no requiere ese dato y la autoridad está pendiente de resolución.

## Género

La UI actual ofrece, entre otros:
- Fantástica, ciencia ficción;
- Infantil y juvenil;
- Ficción literaria;
- Literatura contemporánea;
- Narrativa.

No elegir categoría por SEO. Elegir la que describa realmente cada obra y, si solo admite una, documentar la decisión.

## Procedimiento Claude

1. Buscar David, Samuel y Manecillas por título/ISBN antes de crear nada.
2. Revisar duplicados y datos de cualquier ficha existente.
3. Crear cuenta gratuita solo si hace falta para alta/corrección.
4. Si falta un libro, usar `nuevo-libro` con datos canónicos.
5. Para Manecillas usar el ISBN físico en `ISBN` y el digital en `ISBN edición digital` si la interfaz confirma que ambos campos pertenecen al mismo libro; no crear dos obras innecesarias.
6. Usar portada editorial final y resumen/sinopsis autorizado.
7. No escribir una “crítica” propia ni votar el libro para subir su media.
8. Revisar después que la ficha sea pública, indexable y esté asociada al autor correcto.
9. Guardar URL final y valorar `Book.sameAs` únicamente si la ficha es estable e inequívoca.

## Prioridad

`P1/P2`: gratuito, en español y con alta directa de libros; merece más la pena que directorios genéricos.

## Criterio de cierre

`ACCOUNT_IF_NEEDED · SAMUEL_FOUND_OR_ADDED · MANECILLAS_FOUND_OR_ADDED · PHYSICAL_DIGITAL_ISBNS_CORRECT · METADATA_VERIFIED · DUPLICATES_REVIEWED · NO_SELF_REVIEW · PUBLIC_URLS_RECORDED`
