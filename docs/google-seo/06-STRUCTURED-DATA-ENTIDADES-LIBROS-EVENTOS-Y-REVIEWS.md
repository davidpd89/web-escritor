# 06 — Structured data, entidades, libros, eventos y reviews

## Principio

Structured data sirve para ayudar a Google a comprender contenido y, en tipos compatibles, hacerlo elegible para determinadas apariencias.

No:

- garantiza rich result;
- garantiza ranking;
- permite declarar hechos que el usuario no ve;
- convierte una página mediocre en una buena página.

Google advierte que un abuso de structured data puede provocar una acción manual específica de rich results.

---

# 1. Tipos relevantes en 2026

Google mantiene en su Search Gallery, entre otros:

- Article;
- Breadcrumb;
- Event;
- Image metadata;
- Organization;
- ProfilePage;
- Review snippet;
- SoftwareApplication;
- Video;
- Product/Merchant, bajo condiciones.

También mantiene la documentación de Book actions/feed para proveedores de libros.

No asumir que cualquier tipo schema.org tiene una feature Google.

---

# 2. Matriz del sitio

| Surface | Schema principal | Estado |
|---|---|---|
| Home | WebSite, WebPage, Person, Book | preservar/auditar |
| Autor | ProfilePage, Person, Breadcrumb | bueno |
| Samuel | WebPage, Book, Breadcrumb, FAQ | Book bueno; reviews corregir; FAQ deuda |
| Manecillas | WebPage, Book, Breadcrumb | bueno |
| Cuaderno article | Article + Breadcrumb | bueno |
| Herramientas | WebApplication/SoftwareApplication family | revisar Google eligibility |
| Eventos | WebPage + Event | mejorar URLs individuales |
| Recomendaciones | Article/List semantics | evitar fake reviews |
| Directorios | WebPage/ItemList según contenido real | no sobre-marcar |

---

# 3. P0: `Book.review` de Samuel

## Hallazgo

La ficha incorpora reseñas cuyo publisher es Amazon España.

Google: **“Don't aggregate reviews or ratings from other websites.”**

## Fix

Retirar todos esos objetos `Review` del JSON-LD.

### También prohibido

- copiar Goodreads ratings;
- calcular media Amazon + Goodreads;
- crear AggregateRating manual;
- cambiar `publisher` a David para ocultar origen;
- marcar como first-party reviews textos capturados en otro sitio.

## Visible editorial content

Si la página muestra citas reales de plataformas externas:

- pueden mantenerse como testimonios/citas con atribución, siempre respetando derechos y fuente;
- no necesitan `Review` schema;
- no inventar rating si no se muestra/licencia.

---

# 4. Reviews propias en el futuro

Si algún día `davidportodiaz.com` recopila opiniones directamente:

- consentimiento/moderación;
- contenido visible;
- author;
- rating real;
- política anti-spam;
- no incentivar sin disclosure;
- no ocultar negativas;
- no mezclar con terceros como si fueran propias.

No recomiendo abrir reviews solo para conseguir estrellas. Añade UGC/moderación/privacidad con un coste real.

---

# 5. Book

El Book schema actual de Samuel y Manecillas es útil para describir:

- title;
- author;
- ISBN;
- datePublished;
- publisher;
- numberOfPages;
- format;
- language;
- genre;
- image;
- canonical URL.

## Reglas

- hechos idénticos a contenido visible;
- ISBN exacto;
- fecha no derivada del reloj;
- publisher real;
- retailer solo cuando verificado;
- no Offer si no somos merchant/si no existe oferta controlada;
- no fake aggregateRating.

## `sameAs`

Para la obra puede apuntar a referencias inequívocas:

- retailer;
- Goodreads;
- Open Library;
- LibraryThing;
- catálogo pertinente.

No usar `sameAs` para páginas simplemente relacionadas.

---

# 6. Book actions de Google

La documentación de Google sobre Book actions está orientada a **proveedores de libros con una selección amplia** y un feed específico para acciones de compra/préstamo.

El sitio oficial de un autor con dos obras no debe invertir en construir ese feed como si fuera un gran proveedor.

## Estado

`DEFER / N/A` salvo que el modelo comercial cambie.

La estrategia actual:

- Book schema factual;
- retailer links visibles;
- publisher/ISBN consistency;
- buena página oficial;
- catálogos externos.

---

# 7. Person

`Person` es clave para desambiguación del autor aunque no sea por sí solo un «rich result de escritor» configurable.

Campos útiles actuales:

- name;
- url;
- image;
- jobTitle;
- description;
- birthPlace;
- homeLocation;
- sameAs;
- subjectOf;
- award;
- knowsAbout.

## Reglas

- no añadir credenciales dudosas;
- no exagerar expertise;
- no usar `award` para finalista como si fuera ganador;
- no atribuir un premio al libro cuando es del autor;
- no publicar datos personales privados por «entity SEO».

---

# 8. ProfilePage

`autor.html` usa `ProfilePage` + Person.

Google reconoce ProfilePage para páginas centradas en una persona/organización asociada al sitio.

La página del autor encaja razonablemente con ese caso.

Preservar:

- mainEntity Person;
- foco en una persona;
- bio real;
- author content links;
- breadcrumb.

---

# 9. WebSite / site name

Home debe ser la autoridad del `WebSite`.

Mantener estable:

- `@id`;
- name;
- alternateName razonable;
- url;
- author.

No crear múltiples objetos WebSite contradictorios en cada página.

---

# 10. Article

Cuaderno usa Article.

Campos prioritarios:

- headline;
- description;
- datePublished;
- dateModified;
- author;
- image cuando aplica;
- URL;
- inLanguage.

## Mejoras

Auditar artículos prioritarios para:

- `image` de calidad;
- author enlazado a Person/ProfilePage;
- dates visibles y coherentes;
- headline coincidente con contenido.

No modificar dateModified por cada deploy.

---

# 11. FAQPage

Google retiró FAQ rich results en mayo de 2026.

Por tanto:

- no es una inversión SEO futura;
- puede mantenerse temporalmente si otra integración lo usa;
- las FAQs visibles siguen siendo contenido útil;
- retirar el JSON-LD no exige retirar preguntas.

Añadir un test que no obligue a seguir generando FAQPage eternamente.

---

# 12. BreadcrumbList

Alta prioridad, bajo riesgo.

Asegurar:

- positions secuenciales;
- name humano;
- item canonical;
- coincide con jerarquía visible;
- leaf último correcto.

No poner keywords distintas de la navegación real.

---

# 13. Event

## Estado actual

`eventos.html` contiene dos Event históricos con URLs a anchors del mismo documento.

Google para su experiencia Event pide una URL única y página centrada en un evento.

## Futuro patrón

Hub:

`/eventos.html`

Detalle:

`/eventos/<slug>/`

### Structured data

- name;
- startDate;
- endDate cuando corresponda;
- timezone;
- eventStatus;
- eventAttendanceMode;
- location;
- organizer;
- performer;
- image;
- description;
- offers solo si reales;
- URL self.

### Estado

Actualizar:

- scheduled;
- postponed;
- rescheduled;
- cancelled;
- completed según schema compatible/contexto.

No borrar una página cancelada inmediatamente si usuarios necesitan la información.

---

# 14. SoftwareApplication / WebApplication

Las herramientas usan `WebApplication` en ejemplos revisados.

Google documenta la feature `SoftwareApplication`.

Schema.org `WebApplication` pertenece a la familia de aplicaciones, pero debemos validar cada tipo con Rich Results Test y no asumir que Google mostrará un rich result solo por la relación ontológica.

## Campos

Mantener:

- name;
- description;
- url;
- applicationCategory;
- operatingSystem;
- isAccessibleForFree;
- author.

Si Google exige propiedades adicionales para eligibility, añadir solo datos reales.

No inventar rating/precio.

---

# 15. Organization

No hace falta crear una Organization ficticia llamada «David Porto Díaz» solo porque Google soporte Organization.

El sitio representa principalmente a una `Person`.

Si en el futuro existe una entidad empresarial real con identidad propia, se evalúa por separado.

No mezclar Persona y empresa para rellenar schema.

---

# 16. LocalBusiness

No usar.

David no debe crear un LocalBusiness/GBP en una vivienda privada para intentar aparecer en local pack si no existe un negocio que atiende clientes allí según las reglas de Google.

La residencia `Madrid` como dato biográfico no convierte la web en un LocalBusiness.

---

# 17. Product / Offer

## Samuel

El sitio enlaza a retailers, pero no es necesariamente el merchant que vende el producto.

No crear Offer propia con:

- precio de Amazon;
- stock de Amazon;
- shipping de Amazon.

## Manecillas

PVP 16 € es un hecho editorial, no una oferta.

Hasta que haya compra/retailer verificado, no convertirlo en availability/Offer.

---

# 18. Review snippet en recomendaciones

Las páginas de recomendaciones pueden incluir opiniones editoriales de David sobre libros.

Eso no significa que debamos marcar todas como Review schema.

Primero debe existir una review real, first-party, suficientemente desarrollada.

El sistema de reseñas de Google valora análisis original y expertise/experiencia, no listicles superficiales.

---

# 19. Image metadata

Para imágenes originales importantes se puede usar:

- ImageObject;
- creator/credit/copyright/licensing cuando sean verdaderos;
- contentUrl;
- caption/context visible.

No añadir metadata de copyright que no corresponda.

---

# 20. Video

Si se incorporan vídeos reales:

- VideoObject;
- thumbnailUrl;
- uploadDate;
- duration;
- contentUrl/embedUrl según corresponda;
- página donde vídeo sea contenido principal si se busca video rich feature.

No generar VideoObject para animaciones decorativas.

---

# 21. Structured data parity

Crear una tabla por hecho crítico:

`visible HTML == JSON-LD == press kit == editorial facts == llms == sitemap metadata donde aplique`

Hechos:

- author;
- title;
- ISBN;
- publisher;
- date;
- pages;
- status;
- retailer.

Los tests de machine authority existentes ya avanzan en esta dirección; SEO tests deben reutilizarlos.

---

# 22. Validación

## CI

Para cada tipo:

- parse JSON;
- `@context`;
- required local contract;
- no third-party reviews;
- canonical URL matches;
- dates valid;
- visible-content parity cuando se pueda testear.

## Externa

- Rich Results Test;
- URL Inspection rendered HTML;
- Search Console enhancement reports si aparecen.

No automatizar scraping del Rich Results Test si no hay API soportada.

---

# 23. Manual action protocol

Si aparece una acción manual structured data:

1. leer tipo exacto;
2. identificar patrones afectados;
3. corregir en templates/generators, no una URL suelta;
4. validar;
5. desplegar;
6. confirmar producción;
7. reconsideration request solo cuando esté realmente corregido.

No ocultar markup problemático con JS/UA detection.

---

# 24. Tests propuestos

## `tests/test-google-structured-data-policy.py`

- no Book.review con publisher/source externo conocido;
- no aggregateRating derivado de retailers;
- Book ISBN/date/publisher parity;
- ProfilePage mainEntity author;
- event detail pages future require unique canonical;
- no Offer without verified commercial fact;
- no Product markup on pure affiliate page unless contract permits.

## `scripts/seo/audit-schema.py`

Report:

- URL;
- types;
- ids;
- referenced entities;
- errors local contract;
- deprecated/no-value types;
- policy warnings.

---

# 25. Acceptance criteria

- Samuel third-party review markup eliminado;
- Book facts iguales en todas las superficies;
- FAQPage no se trata como oportunidad SEO;
- future Events tienen unique URL;
- WebApplication validado sin inventar propiedades;
- no fake Organization/LocalBusiness/Product/Offer;
- ProfilePage/Person estable;
- breadcrumbs válidos;
- structured data visible/factual;
- CI impide reintroducir third-party review aggregation.
