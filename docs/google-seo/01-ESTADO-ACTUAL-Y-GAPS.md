# 01 — Estado actual y gaps SEO

**Corte:** 27/08/2026  
**Base revisada:** `main` en `3a4fdfaf48d8c85c240158bbebf97c556f03dd00` al abrir esta rama.  
**Objetivo:** documentar qué existe realmente antes de proponer cambios.

---

# 1. Diagnóstico general

`davidportodiaz.com` ya no está en una fase en la que el mayor retorno venga de añadir metadatos básicos. La infraestructura actual cubre una gran parte de los fundamentos SEO:

- contenido HTML indexable;
- URLs limpias;
- canonical;
- sitemap;
- robots;
- titles;
- meta descriptions;
- headings;
- breadcrumbs;
- structured data;
- mobile/responsive;
- HTTPS;
- imágenes optimizadas;
- performance QA;
- link QA;
- accesibilidad;
- contenido editorial;
- fuentes externas;
- entidad del autor.

La siguiente mejora debe concentrarse en cinco problemas de orden superior:

1. **verdad publicada vs. verdad ya procesada por Google**;
2. **cumplimiento estricto de structured data**;
3. **asignación clara de intención a cada URL**;
4. **autoridad/calidad diferencial de contenidos que compiten en queries genéricas**;
5. **medición/experimentación disciplinadas**.

---

# 2. Lo que está bien y debe preservarse

## 2.1 HTML principal accesible

El sitio no es una SPA opaca. Las páginas de autor, libros, artículos y herramientas exponen el contenido principal en HTML.

Ejemplo: `/herramientas/contador-palabras/` contiene en el HTML:

- H1;
- explicación de la utilidad;
- privacidad;
- metodología;
- enlaces a siguientes herramientas.

La funcionalidad interactiva necesita JS, pero el valor descriptivo no desaparece si el script no se ejecuta.

**Decisión:** preservar server-first/static-first para contenido indexable.

## 2.2 Canonicals explícitas

Las páginas revisadas incluyen `rel=canonical` self-referential coherente con su URL pública.

Ejemplos:

- `/`;
- `/autor.html`;
- `/libros/samuel-entre-mundos/`;
- `/las-manecillas-del-recuerdo/`;
- artículos;
- herramientas.

No sustituir esta disciplina por una dependencia exclusiva de sitemaps o redirects.

## 2.3 Robots granular

Las principales páginas editoriales utilizan:

`index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1`

Esto favorece flexibilidad de snippets e imágenes grandes.

Las superficies retiradas/privadas utilizan `noindex` cuando corresponde.

Ejemplo:

`/cuaderno/sistema-de-magia-noveris/` está explícitamente retirado y `noindex,follow`.

**Decisión:** no reactivar páginas solo porque en el pasado tuvieran contenido o tráfico. La decisión editorial manda.

## 2.4 Sitemap controlado por un registry

`data/content-registry.json` ya distingue:

- status;
- searchIndex;
- sitemap;
- territorio;
- parent/hub;
- discoverability;
- sourceFile.

Esto es una base excepcional para automatizar SEO sin recorrer el filesystem a ciegas.

## 2.5 Jerarquía editorial

Hay hubs explícitos:

- Obras;
- Cuaderno;
- Temas;
- Herramientas;
- Editoriales;
- Convocatorias;
- Recomendaciones;
- Autor/Prensa/Eventos.

Esto es mejor para SEO y UX que una colección plana de páginas.

## 2.6 Structured data de entidad

La home y Autor ya conectan:

- `WebSite`;
- `WebPage`;
- `Person`;
- `Book`;
- `ProfilePage`;
- `sameAs`;
- `subjectOf`;
- identificadores y fuentes externas.

Los libros incluyen:

- nombre;
- autor;
- ISBN;
- editorial;
- fecha;
- páginas;
- formato;
- género;
- imagen;
- URL.

Esto debe preservarse y mantenerse factual.

## 2.7 Breadcrumbs

Las páginas revisadas tienen breadcrumbs visibles y muchas también `BreadcrumbList`.

Eso ayuda a:

- navegación;
- comprensión de jerarquía;
- contexto de resultado;
- internal linking.

## 2.8 Enlaces afiliados cualificados

Los enlaces Amazon revisados usan `rel="sponsored nofollow ..."`.

Google recomienda `sponsored` para enlaces pagados/afiliados. No retirar ese atributo con la intención de pasar PageRank.

## 2.9 QA existente

El repositorio ya tiene workflows para:

- broken links;
- global discoverability;
- findability browser QA;
- Lighthouse;
- accessibility;
- CSP;
- content indexes;
- machine authority;
- editorial facts;
- image format ladder;
- recommendations;
- public artifact;
- tool tests;
- identity/browser QA;
- etc.

La futura automatización SEO debe añadir checks de alto valor, no duplicar estos tests.

---

# 3. Hallazgos P0

## SEO-001 — reviews de Amazon dentro de `Book.review`

**Severidad:** P0 / compliance structured data.

Archivo:

`libros/samuel-entre-mundos/index.html`

Situación:

el JSON-LD de `Book` contiene múltiples objetos `Review` con:

- autores de Amazon;
- textos de reseña;
- rating 5/5;
- publisher `Amazon España`.

Google mantiene `Review`/`AggregateRating` para `Book`, pero establece:

- el review marcado debe ser visible;
- no se deben agregar reviews o ratings de otros sitios web;
- reviews falsas o incentivadas no declaradas están prohibidas.

### Acción

Eliminar `Book.review` cuando la fuente sea otro sitio.

No sustituirlo por:

- `aggregateRating` de Amazon;
- `aggregateRating` de Goodreads;
- promedio manual;
- `Review` con copy reescrito;
- una copia de las estrellas del retailer.

### Qué sí puede quedar

Una sección editorial visible tipo:

> Reseñas de lectores en otras plataformas

con enlaces y citas breves correctamente atribuidas, si se desea y se cumplen copyright/políticas. Eso no debe marcarse como un review capturado por nuestra web.

### Acceptance criteria

- no `review`/`aggregateRating` derivados de terceros en Book schema;
- Rich Results Test sin errores;
- tests de machine authority actualizados si esperan esas reviews;
- Search Console Manual Actions revisado;
- deploy verificado.

---

## SEO-002 — stale facts en copias rastreadas

**Severidad:** P0 / distribución.

Durante la auditoría se encontraron snapshots públicos antiguos que todavía mostraban:

- una versión previa de la home;
- `/fragmento/` asociado a `Libros Indie, 2026`.

El repo actual fija Samuel en 2025.

### Riesgo

Google puede reescribir title links/snippets utilizando:

- `<title>`;
- H1/texto visible;
- anchors internos;
- anchors externos;
- información ya procesada.

Una corrección factual puede tardar en propagarse.

### Acción

Crear lista de URLs de hechos críticos:

- `/`;
- `/autor.html`;
- `/libros/`;
- `/libros/samuel-entre-mundos/`;
- `/fragmento/`;
- `/las-manecillas-del-recuerdo/`;
- `/las-manecillas-del-recuerdo/fragmentos/`;
- `/premios.html`;
- `/prensa.html`;
- `/ai/`.

Para cada release factual:

1. verificar repo;
2. verificar public dist;
3. verificar URL producción;
4. comprobar status/canonical/meta/schema;
5. inspección URL;
6. solicitar recrawl solo cuando sea prioritario;
7. verificar SERP posteriormente;
8. registrar closure.

---

# 4. Hallazgos P1

## SEO-003 — slash de home no idéntico en sitemap

Canonical:

`https://davidportodiaz.com/`

Sitemap actual:

`https://davidportodiaz.com`

Es una variación pequeña, pero la disciplina canonical debe ser byte-consistent siempre que sea posible.

### Fix recomendado

El generador del sitemap debe producir exactamente:

`https://davidportodiaz.com/`

para la home.

---

## SEO-004 — `lastmod` inconsistente

Hay URLs con `<lastmod>` y otras sin él.

Esto no es por sí mismo un error. El problema es que no existe todavía una política visible que explique de dónde sale la fecha y cuándo se modifica.

### Requisito

Definir `seoLastModified` o equivalente en una fuente canónica/generada, o derivarlo de un campo editorial confiable.

No usar:

- mtime del checkout;
- fecha del build;
- fecha del commit que toca CSS global;
- fecha diaria artificial.

---

## SEO-005 — eventos no tienen páginas dedicadas

`eventos.html` contiene múltiples `Event` con URLs `eventos.html#...`.

Google recomienda/require para su experiencia Event que cada evento tenga una URL única y una página centrada en ese evento.

### Decisión

Para eventos futuros relevantes:

`/eventos/<fecha>-<slug>/`

El archivo `eventos.html` pasa a ser hub/agenda.

No generar cientos de páginas retrospectivas.

---

## SEO-006 — FAQPage permanece en páginas donde la apariencia ya no existe

Ejemplo:

`/cuaderno/que-es-el-portal-fantasy/`

contiene `FAQPage`.

Google retiró FAQ rich results en mayo de 2026.

### Acción

- mantener las preguntas visibles si ayudan;
- no crear nuevas FAQ por SEO;
- se puede retirar el JSON-LD FAQ para reducir deuda si no sirve a otra integración;
- no tratar su desaparición en Search Console como pérdida de ranking.

---

## SEO-007 — riesgo de canibalización semántica

Familia portal fantasy actual:

- `/cuaderno/que-es-el-portal-fantasy/`
- `/cuaderno/portal-fantasy-vs-fantasia-epica/`
- `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`
- `/cuaderno/temas/fantasia-de-portales/`
- `/recomendaciones/portal-fantasy-espanol/`
- `/libros/samuel-entre-mundos/`
- `/universo/noveris/`

Esto es una buena arquitectura potencial, pero necesita roles explícitos.

### Query role recomendado

| URL | Job principal |
|---|---|
| `que-es-el-portal-fantasy` | definición/explicación |
| `portal-fantasy-vs-fantasia-epica` | comparación de géneros |
| `fantasia-juvenil...` | análisis del contexto español + rasgos |
| `temas/fantasia-de-portales` | hub |
| `recomendaciones/portal-fantasy-espanol` | selección/recomendación de lectura |
| `samuel` | intención de obra/título |
| `noveris` | universo/entidad de ficción |

Validar con queries reales de Search Console antes de fusionar/dividir.

---

## SEO-008 — páginas de herramientas necesitan evitar comoditización

Ejemplo positivo: contador de palabras explica:

- qué hace;
- procesamiento local;
- definición de métricas;
- velocidad de lectura usada;
- siguientes pasos.

### Gate para cada herramienta

Debe ofrecer al menos dos de estos activos:

- funcionalidad real;
- procesamiento/privacidad diferencial;
- metodología explicada;
- ejemplos;
- interpretación del resultado;
- exportación/flujo útil;
- enlaces a siguientes acciones coherentes.

No crear una herramienta que sea una caja vacía rodeada de 1.500 palabras SEO.

---

## SEO-009 — directorios/editoriales pueden caer en scaled-content si se relaja la metodología

La web dispone de:

- directorio de editoriales;
- fichas de editoriales;
- convocatorias;
- metodología editorial.

Eso puede convertirse en una ventaja SEO muy fuerte si aporta:

- fuentes primarias;
- estado actual;
- fecha de verificación;
- qué acepta/no acepta;
- canal real de envío;
- país/género;
- notas específicas;
- historial de cambio.

Se convertiría en un riesgo si se generan fichas masivas a partir de scraping/resúmenes sin valor.

### Gate

No indexar una ficha nueva hasta cumplir un mínimo factual definido.

---

## SEO-010 — títulos de herramientas/hubs deben auditarse por query, no por estética

Ejemplo actual:

`Contador de palabras — Herramientas`

Puede ser suficiente, pero el title link es uno de los activos de CTR/relevancia más claros.

No cambiar por intuición a:

`Contador de palabras y caracteres online gratis 2026 | ...`

sin evidencia.

Proceso:

1. impressions por query;
2. position distribution;
3. CTR;
4. SERP intent;
5. title actual mostrado por Google;
6. experimento de 28 días mínimo cuando volumen lo permita.

---

## SEO-011 — entidad fuerte, pero Knowledge Panel debe verificarse externamente

La web ya tiene:

- ProfilePage;
- Person;
- Wikidata;
- ORCID;
- Author Central;
- Goodreads;
- redes;
- fuentes de prensa.

No se afirma que exista Knowledge Panel.

### Acción manual

Buscar `David Porto Díaz` en Google en contexto neutro.

Si existe panel y ofrece `Reclamar este panel de información`:

- reclamarlo con cuenta controlada;
- usar Search Console/perfil oficial para verificación;
- revisar errores;
- no intentar crear un panel mediante spam de entidades.

---

# 5. Hallazgos P2

## SEO-012 — auditor SEO machine-readable del public dist

Crear un script de sólo lectura que genere un reporte por URL con:

- status esperado;
- robots meta;
- canonical;
- title;
- H1;
- description;
- language;
- OpenGraph;
- image;
- structured data types;
- sitemap inclusion;
- lastmod;
- depth;
- inbound internal links;
- outbound links;
- source registry id.

No debe modificar HTML automáticamente.

## SEO-013 — grafo de internal linking

Necesitamos conocer:

- profundidad desde home;
- profundidad desde hub;
- inbound link count;
- anchors;
- orphan/near-orphan pages;
- links hacia noindex/redirect/404;
- hubs sin distribución suficiente.

Se puede generar desde public dist después del build.

## SEO-014 — experiment log

Cada cambio SEO con intención de ranking/CTR debe tener:

- fecha;
- URLs;
- hipótesis;
- métrica primaria;
- ventana;
- query set;
- contexto algorítmico;
- resultado;
- keep/revert/iterate.

---

# 6. Inventario por familia

## Home

### Bien

- title específico;
- description;
- canonical;
- WebSite;
- Person;
- Book;
- sameAs;
- subjectOf;
- imágenes.

### Revisar

- SERP title real vs title declarado;
- snippet real;
- stale copy;
- sitemap slash;
- site name;
- sitelinks;
- prioridad de enlaces internos visible en HTML.

## Autor

### Bien

- ProfilePage + Person;
- bio;
- canonical;
- social/identifiers;
- subjectOf.

### Revisar

- Knowledge Panel;
- consistencia de todos los perfiles externos;
- qué datos personales son realmente útiles/públicos;
- `hasCredential` solo si está respaldado y aporta valor; no convertir credenciales menores en señal de autoridad literaria.

## Samuel

### Bien

- title orientado a intención;
- description;
- Book completo;
- ISBN;
- publisher;
- genre;
- sameAs;
- fragmento;
- enlaces comerciales verificados;
- Noveris/cluster.

### Corregir

- reviews de Amazon en schema.

### Revisar

- snippet stale de 2026;
- anchors hacia fragmento/Noveris/recomendaciones;
- imágenes/Google Images;
- exactitud de SERP de título.

## Manecillas

### Bien

- Book;
- ISBN;
- Monza;
- 272 páginas;
- imagen;
- fragmentos;
- canonical;
- fecha.

### Pendiente condicionado

- retailer solo cuando esté verificado;
- huella externa post-lanzamiento;
- recrawl alrededor del 03/09;
- event/press coverage;
- Google Books/catalogos si publisher/rights lo permiten.

## Cuaderno

### Bien

- Articles;
- fechas;
- hubs;
- topic pages;
- breadcrumbs;
- RSS;
- contenido first-party.

### Riesgos

- overlap entre páginas;
- publicar por keyword en vez de por valor;
- fake freshness;
- FAQ schema obsoleto;
- piezas que hablan de temas demasiado alejados del propósito del sitio.

## Herramientas

### Bien

- utilidad real;
- WebApplication en ejemplos;
- privacidad local;
- contenido HTML;
- interlinking.

### Mejorar

- query-role;
- titles/descriptions basados en datos;
- metodología y ejemplos;
- linkability;
- documentación propia que permita citarlas como referencia.

## Editoriales/convocatorias

### Bien

- metodología;
- fuentes;
- valor para escritores;
- potencial de actualización.

### Riesgo

- scaled content;
- datos caducados;
- páginas demasiado parecidas;
- scrape sin valor;
- afirmar aceptación de manuscritos sin fuente actual.

## Recomendaciones

### Bien

- intención de lector clara;
- cluster con Samuel.

### Riesgo

- sesgo promocional;
- review content superficial;
- comparables sin experiencia real;
- enlaces afiliados sin metodología;
- recomendar Samuel en todas las listas.

Regla: una página de recomendaciones debe seguir siendo útil si eliminásemos temporalmente el libro propio.

## Eventos

### Bien

- agenda;
- hechos históricos;
- Event schema.

### Mejorar

- futuras páginas dedicadas por evento;
- archive behavior;
- fecha/status;
- enlazado desde libro/autor/cuaderno cuando tenga sentido.

---

# 7. Deuda que NO debe confundirse con bug

- `noindex,follow` en contenido retirado es correcto.
- no todas las URLs necesitan `lastmod`.
- no todos los schemas generan rich result.
- meta description no garantiza snippet.
- structured data no garantiza rich result.
- posición media no es ranking fijo.
- Lighthouse no sustituye CrUX/Search Console CWV.
- que una URL no tenga rich result no implica mala indexación.
- una página con pocas palabras puede ser excelente si resuelve la tarea.
- una página larga puede ser mala aunque tenga 3.000 palabras.
- el sitemap no obliga a Google a indexar.
- `index,follow` no obliga a Google a indexar.

---

# 8. Definition of Done de esta auditoría

La auditoría documental se considera útil si Claude puede:

1. localizar el archivo afectado;
2. saber por qué un cambio es necesario;
3. saber qué no debe hacer;
4. implementar el cambio sin reinterpretar la estrategia;
5. añadir tests;
6. verificar public dist;
7. verificar producción;
8. comprobar Search Console cuando sea necesario;
9. dejar evidencia del resultado.
