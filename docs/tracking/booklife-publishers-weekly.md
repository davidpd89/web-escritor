# BookLife — fichas gratuitas de autor/libros

Fecha de revisión: 2026-09-07 (revisión: 2026-09-14)

Estado: `ACCOUNT_CREATED_BY_OWNER · ADD_PROJECT_BUTTON_BROKEN_ON_SITE · BLOCKED_NOT_OWNER_ACTIONABLE`

## Intento de ejecución (2026-09-14)

Cuenta ya creada por el propietario ("David Porto") y sesión iniciada.
Se intentó pulsar "Create New Project" en el Profile para dar de alta
Samuel/Manecillas. El botón es un componente JS ("ProjectWizard") que
debería abrir un modal (`#add-project-wizard`) con el formulario de
título/ISBN — pero el modal se queda permanentemente en `display: none`
pase lo que pase: clic normal, clic tras hover, distintos tamaños de
viewport. Confirmado que el clic sí llega al elemento correcto (no hay
nada superpuesto tapándolo) — es la propia inicialización JS del sitio
la que no está reaccionando, no un problema de esta sesión.

**No es algo que yo pueda arreglar** (es código del sitio de BookLife,
no nuestro) y no se ha intentado forzar la apertura del modal
manualmente vía consola — eso saltaría la inicialización real del
asistente y probablemente rompería el envío del formulario. Recomiendo
que pruebes tú directamente desde tu propio navegador (podría ser un
bloqueador de anuncios, una extensión, o simplemente que el sitio
necesite una interacción humana real); si a ti tampoco te funciona,
es un bug para reportar a soporte de BookLife (`Contact Us` en el
sitio), no algo que puedas arreglar desde tu lado tampoco.

## Cierre de esta ronda

`ACCOUNT_READY · ELIGIBILITY_QUESTION_STILL_OPEN · SITE_BUG_BLOCKS_PROJECT_CREATION · NEEDS_OWNER_TO_TEST_OR_CONTACT_SUPPORT`

## Objetivo

Usar únicamente las funciones gratuitas de BookLife que puedan dar una página externa indexable y útil a David Porto Díaz y sus libros. No usar concursos, PW Select, BookLife Reviews ni promociones de pago.

## Qué es gratuito y sí aporta valor

La FAQ oficial de BookLife confirma que el alta de libros es gratuita y sin límite. Cada proyecto puede tener una página pública con:
- portada;
- descripción;
- información de venta para todos los formatos;
- extracto;
- reseñas;
- noticias.

BookLife además indica que al añadir una noticia o reseña esta puede aparecer en la portada del sitio. Las páginas de proyectos son navegables por categoría, edad, título y autor.

Fuentes:
- https://booklife.com/about-us/booklife-faqs.html
- https://booklife.com/project-browse

## Lo que queda expresamente FUERA

No pagar por:
- BookLife Reviews;
- BookLife Prize (la edición actual cobra entrada; fuera de alcance);
- PW Select;
- servicios/proveedores/promoción patrocinada.

El objetivo de esta PR es solo el listing gratuito.

## Punto de elegibilidad a verificar

BookLife se dirige principalmente a autores indie/self-published. Samuel y Manecillas tienen sello editorial (`Libros Indie` y `Monza Ediciones`), así que Claude debe comprobar en la cuenta/flujo real que BookLife acepta crear proyectos públicos para estas obras sin falsear su modalidad de publicación.

No marcar `self-published` si editorialmente no corresponde solo para conseguir la ficha.

## Datos preparados

### Samuel entre mundos
- Autor: David Porto Díaz
- Editorial: Libros Indie
- ISBN: 9791387659776
- Año: 2025
- Formato: tapa blanda
- URL oficial: https://davidportodiaz.com/libros/samuel-entre-mundos/

### Las manecillas del recuerdo
Papel:
- Editorial: Monza Ediciones
- ISBN: 9798905149351
- ASIN: B0HHY9MYLM
- fecha: 2026-09-03
- PVP actual: 15,99 €
- URL oficial: https://davidportodiaz.com/las-manecillas-del-recuerdo/

Kindle:
- ISBN: 9798906781925
- ASIN: B0HHM71F46
- fecha: 2026-08-12
- precio actual: 2,99 €
- URL oficial: https://davidportodiaz.com/las-manecillas-del-recuerdo/kindle/

No fijar páginas de una ficha externa hasta cerrar las discrepancias #428/#404/#429.

## Procedimiento Claude

1. Crear/iniciar cuenta gratuita a nombre de David Porto Díaz.
2. Antes de crear proyectos, buscar si Samuel o Manecillas ya existen para evitar duplicados.
3. Confirmar que la modalidad editorial de cada obra es elegible para un proyecto público gratuito.
4. Si sí:
   - crear/completar perfil de autor;
   - crear un proyecto por obra, no uno por formato salvo que la UI realmente lo requiera;
   - añadir papel/ebook como formatos con sus identificadores/enlaces correctos;
   - usar portada editorial final;
   - descripción/sinopsis verificable;
   - enlace a web oficial;
   - extracto solo si tenemos derecho a publicarlo;
   - reseñas/noticias únicamente reales y atribuibles.
5. No inventar reviews ni copiar reseñas de terceros sin permiso.
6. No pagar nada cuando la UI ofrezca upsells.
7. Guardar URLs públicas finales y verificar que son indexables/estables.
8. Valorar `Person.sameAs`/`Book.sameAs` solo si las páginas finales son canónicas e inequívocas.

## Valor SEO/discovery esperado

No se promete ranking. El valor razonable es:
- una ficha externa pública adicional;
- datos coherentes de autor/obra/formatos;
- enlaces de venta/web;
- descubrimiento dentro de la categoría Sci-Fi/Fantasy/Horror cuando corresponda;
- potencial aparición de news/reviews en BookLife.

## Criterio de cierre

Si es elegible:
`FREE_ACCOUNT · AUTHOR_PROFILE_COMPLETE · SAMUEL_PROJECT_COMPLETE · MANECILLAS_PROJECT_COMPLETE · FORMATS_LINKED · WEBSITE_LINKED · PUBLIC_URLS_RECORDED · NO_PAID_FEATURES`

Si no encaja por modalidad editorial:
`NO_GO_ELIGIBILITY · REASON_DOCUMENTED · ZERO_SPEND`
