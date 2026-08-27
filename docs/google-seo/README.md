# Google SEO — plan maestro 2026 para davidportodiaz.com

**Fecha de corte:** 27 de agosto de 2026  
**Sitio:** `https://davidportodiaz.com/`  
**Ámbito:** posicionamiento orgánico en Google Search, sus superficies derivadas y la capacidad de que la web, David Porto Díaz y sus libros sean descubiertos correctamente por búsquedas relevantes.  
**Estado:** autoridad operativa y backlog. Esta carpeta no sustituye los datos reales de Search Console ni promete posiciones.

## Objetivo

Convertir el SEO de `davidportodiaz.com` en un sistema continuo que conecte:

`hechos y contenido útil → arquitectura → rastreo → indexación → comprensión → ranking → apariencia SERP → clic → satisfacción → autoridad → medición → mejora`

No perseguimos una posición aislada ni una colección de trucos. El objetivo es aumentar de forma sostenible:

- la visibilidad de David Porto Díaz como entidad/autor;
- la visibilidad de **Las manecillas del recuerdo** y **Samuel entre mundos**;
- el descubrimiento por búsquedas no de marca;
- la autoridad temática del Cuaderno;
- el tráfico evergreen de herramientas y recursos para escritores;
- el descubrimiento de editoriales, convocatorias y recursos verificados;
- la presencia de eventos, imágenes y contenidos originales en superficies de Google;
- el CTR de resultados en los que ya somos competitivos;
- la proporción de URLs estratégicas correctamente rastreadas, indexadas y canonizadas;
- la autoridad externa real mediante menciones y enlaces editoriales legítimos.

## Qué NO es esta carpeta

No es:

- otra copia del plan de Search Console;
- otra copia del plan de visibilidad en IA;
- una lista de keywords para repetir en todas las páginas;
- una recomendación de publicar cientos de páginas;
- una promesa de «posición 1»;
- una justificación para comprar backlinks;
- una guía para manipular reseñas, schema o fechas;
- una invitación a convertir toda idea relacionada con libros/escritura en una URL indexable.

### Relación con las dos autoridades ya existentes

- `docs/search-console/` explica **cómo observar Google**: propiedades, informes, API, BigQuery, indexación y operaciones dentro de Search Console.
- `docs/ai-discoverability/` explica **cómo ser descubrible/citable/recomendable en sistemas generativos**, incluido Google AI.
- `docs/google-seo/` explica **qué debe hacer el sitio y su estrategia editorial para mejorar orgánicamente en Google Search**.

Las tres deben convivir. Ninguna debe duplicar o contradecir a las otras.

---

# Resumen ejecutivo

La web ya parte de una base SEO considerablemente mejor que la típica web de autor:

- HTML principal accesible sin depender de renderizado cliente;
- HTTPS;
- canonicals;
- robots y sitemap;
- `max-image-preview:large` en páginas editoriales principales;
- títulos y descripciones específicos;
- `Person`, `Book`, `Article`, `BreadcrumbList`, `ProfilePage`, `WebApplication` y `Event` según superficies;
- imagen/OG/Twitter;
- breadcrumbs visibles;
- una arquitectura en `data/content-registry.json`;
- hubs de Obras, Cuaderno, Herramientas, Editoriales, Convocatorias y Recomendaciones;
- contenido first-party sobre Noveris, procesos y universo de los libros;
- herramientas que funcionan localmente y explican metodología;
- referencias externas reales del autor y Samuel;
- QA de enlaces, discoverability, contenido, accesibilidad, rendimiento y artefacto público;
- Search Console y AI-discoverability ya documentados.

Por tanto, la siguiente fase SEO no consiste en «poner SEO». Consiste en elevar la precisión, la calidad, la autoridad y la disciplina operativa.

## Hallazgos prioritarios de esta auditoría

### P0 — retirar `Review` de Amazon del JSON-LD de Samuel

`libros/samuel-entre-mundos/index.html` incorpora varias reseñas de Amazon dentro de la propiedad `review` del `Book`.

Google admite `Review` para `Book`, pero su directriz vigente dice expresamente:

> **Don't aggregate reviews or ratings from other websites.**

Además, Google advierte que los problemas de structured data pueden provocar una acción manual sobre la elegibilidad para rich results.

Acción:

- retirar del JSON-LD de `Book` cualquier `Review`/rating procedente de Amazon u otro sitio de terceros;
- no crear `aggregateRating` con Amazon/Goodreads/Casa del Libro;
- las reseñas externas pueden seguir citándose de forma visible y editorial cuando exista base para ello, con fuente y enlace, pero no presentarse como reviews recopiladas por `davidportodiaz.com`;
- validar la ficha con Rich Results Test y Search Console después del deploy.

Esto es el hallazgo de cumplimiento SEO más claro de esta auditoría.

### P0 — cerrar la brecha entre repo correcto y resultado de Google actualizado

Durante la investigación se recuperaron copias rastreadas antiguas:

- una home con mensajes y datos anteriores;
- `/fragmento/` todavía asociado en una copia a `Libros Indie, 2026` cuando el contrato actual fija Samuel en 2025.

Esto no demuestra que el origin actual esté incorrecto. Demuestra que **actualizar el repo no equivale a actualizar inmediatamente el índice, title link o snippet de Google**.

Flujo obligatorio para cambios factuales importantes:

`source of truth → build → deploy → verify production → sitemap/lastmod → URL Inspection → recrawl → verificar SERP → cerrar stale fact`

No volver a considerar cerrada una corrección SEO de una fecha, editorial, disponibilidad o título solo porque `main` esté correcto.

### P1 — canonicalización exacta de la home en sitemap

Actualmente:

- canonical: `https://davidportodiaz.com/`
- sitemap: `https://davidportodiaz.com`

Google puede normalizarlo, pero no hay razón para introducir una variante innecesaria. La URL del sitemap debe ser exactamente la canónica.

### P1 — `lastmod` debe convertirse en señal fiable o no usarse

El sitemap mezcla URLs con y sin `<lastmod>`.

Google solo utiliza `lastmod` si es consistentemente exacto y refleja cambios significativos. Ignora `priority` y `changefreq`.

Recomendación:

- generar `lastmod` desde una fuente explícita editorial/build;
- cambiarlo solo cuando cambie contenido principal, datos estructurados o enlaces relevantes;
- no cambiarlo por cada deploy, copyright, hash, whitespace o regeneración sin cambio sustancial;
- no inventar `lastmod` para completar el XML.

### P1 — eventos futuros con URL dedicada

`eventos.html` actualmente contiene varios objetos `Event` cuyo `url` apunta a fragmentos del mismo documento.

La experiencia de eventos de Google exige una URL única y una página centrada en un único evento.

Para nuevos eventos confirmados:

- crear `/eventos/<slug>/`;
- contenido visible del evento;
- `Event` completo y coherente;
- fecha/hora/zona horaria;
- ubicación real;
- organizador y performer;
- `eventStatus` y `eventAttendanceMode`;
- oferta/entrada solo si existe;
- imagen real;
- enlazar desde `eventos.html`;
- al finalizar, conservar la página como archivo si mantiene valor.

No hace falta migrar retrospectivamente todo el histórico solo para obtener un rich result.

### P1 — no gastar esfuerzo en FAQ rich results

Algunas páginas todavía incluyen `FAQPage`.

Google retiró los FAQ rich results el **7 de mayo de 2026** y está retirando esa apariencia de sus APIs/herramientas.

Las preguntas frecuentes visibles pueden seguir siendo útiles para lectores. El schema FAQ ya no debe justificar esfuerzo SEO ni nuevas implementaciones.

### P1 — Search intent / query role por URL

La web ya posee múltiples páginas relacionadas con portal fantasy, magia, herramientas y recursos. Eso es una ventaja solo si cada URL tiene un trabajo distinto.

Antes de crear contenido nuevo se debe responder:

1. ¿qué intención resuelve?;
2. ¿qué URL existente ya compite por esa intención?;
3. ¿la nueva pieza añade algo que la URL anterior no puede resolver?;
4. ¿debe ser una nueva URL, una sección, una actualización, una herramienta o una página noindex?;
5. ¿qué hub la va a enlazar?;
6. ¿qué evidencia/experiencia propia aporta?

### P1 — fortalecer páginas que ya tienen ventaja diferencial

Prioridad alta para tráfico no de marca:

- definiciones y análisis de portal fantasy;
- worldbuilding/Noveris;
- magia con coste;
- herramientas para escritores;
- metodología/recursos editoriales;
- editoriales verificadas;
- convocatorias verificadas;
- recomendaciones de lectura con metodología real;
- clubes de lectura;
- contenido de primera mano sobre publicación, ferias y escritura.

La ventaja no está en producir «más SEO», sino en que estas páginas puedan aportar información, experiencia o utilidad que un resumen genérico no tiene.

---

# Los cuatro territorios SEO

## 1. Entidad y marca

Objetivo: que Google comprenda inequívocamente quién es David Porto Díaz, qué obras son suyas y cuáles son los hechos actuales.

URLs clave:

- `/`
- `/autor.html`
- `/libros/`
- `/premios.html`
- `/prensa.html`
- `/eventos.html`
- `/ai/`

Queries orientativas:

- David Porto Díaz
- David Porto escritor
- libros David Porto Díaz
- David Porto autor
- premios David Porto Díaz

No se crean páginas separadas para variantes del nombre.

## 2. Obras y descubrimiento lector

URLs clave:

- `/las-manecillas-del-recuerdo/`
- `/las-manecillas-del-recuerdo/fragmentos/`
- `/libros/samuel-entre-mundos/`
- `/fragmento/`
- `/universo/noveris/`
- `/clubes-de-lectura/...`
- `/recomendaciones/...`

Objetivos:

- búsquedas exactas de título;
- género/subgénero;
- temas/tropes;
- intención de lectura;
- comparación/descubrimiento;
- disponibilidad legítima;
- clubes y eventos.

## 3. Autoridad editorial / Cuaderno

URLs clave:

- `/cuaderno/`
- `/cuaderno/temas/`
- artículos de portal fantasy;
- fantasía juvenil española;
- worldbuilding;
- crónicas/eventos;
- futuras piezas de proceso editorial y escritura.

Objetivo: construir autoridad temática mediante material original, no una fábrica de artículos de keyword.

## 4. Utilidad para escritores

URLs clave:

- `/herramientas/`
- herramientas individuales;
- `/editoriales/`
- `/convocatorias-escritores/`
- `/metodologia-editorial/`
- `/recursos/`

Objetivo: captar demanda evergreen con utilidad real y convertir esa audiencia en reconocimiento del sitio/autor sin contaminar la intención de cada herramienta con promoción excesiva.

---

# Prioridades

## P0 — seguridad/compliance/verdad

- [ ] Retirar reviews de terceros del JSON-LD de Samuel.
- [ ] Verificar producción de home, Autor, Samuel, Manecillas, fragmentos y `/ai/` frente a `main`.
- [ ] Ejecutar URL Inspection sobre URLs con hechos antiguos conocidos.
- [ ] Cerrar snapshots/SERP obsoletos de fechas, editorial y publicación.
- [ ] Revisar Manual Actions y Security Issues en Search Console.
- [ ] Mantener `noindex`/gated fuera del sitemap y de enlaces promocionales públicos.

## P1 — mayor impacto orgánico

- [ ] Normalizar home del sitemap con `/`.
- [ ] Diseñar `lastmod` fiable.
- [ ] Crear matriz `query-role` por URL y detectar canibalización con Search Console.
- [ ] Auditar titles/H1/meta descriptions por familia usando datos de impresión/CTR.
- [ ] Auditar profundidad e inbound internal links de URLs prioritarias.
- [ ] Construir clusters alrededor de hubs existentes, sin páginas puerta.
- [ ] Mejorar el valor diferencial de herramientas/directorios generados.
- [ ] Crear páginas dedicadas para eventos futuros confirmados.
- [ ] Auditar structured data contra la galería 2026 de Google.
- [ ] Reforzar imágenes representativas de autor/libros/artículos.
- [ ] Crear estrategia de autoridad externa legítima para Manecillas.
- [ ] Reclamar Knowledge Panel si existe y es reclamable.
- [ ] Evaluar Preferred Sources para Cuaderno solo si Google declara el dominio elegible.

## P2 — madurez

- [ ] Auditor automático de canonical/sitemap/status/meta/schema por artefacto público.
- [ ] Grafo de internal linking con depth/inbound/anchor report.
- [ ] Registro versionado de cambios SEO + anotación en Search Console.
- [ ] Dashboard de cohortes por territorio.
- [ ] Sistema de experimentos de title/snippet con ventanas y criterios de reversión.
- [ ] Image sitemap solo si aporta descubrimiento de imágenes que el HTML no expone adecuadamente.
- [ ] Workflow de páginas de eventos.
- [ ] Evaluar vídeo solo cuando exista un corpus real.
- [ ] Revisar elegibilidad/huella Google News/Discover sin crear una «publicación» artificial.

---

# KPI

No usar una sola métrica.

## Crecimiento

- clicks orgánicos;
- impressions;
- clicks non-brand;
- nuevas queries relevantes;
- páginas que empiezan a recibir demanda;
- tráfico hacia Obras desde consultas genéricas;
- CTR contextual por query/posición/SERP;
- conversiones soft: fragmento, retailer, newsletter, evento, herramienta completada.

## Salud técnica

- URLs prioritarias indexadas;
- canónica elegida = canónica declarada;
- exclusiones esperadas vs inesperadas;
- 4xx/5xx/soft 404;
- sitemap sin URLs noindex/gated/redirect;
- `lastmod` fiable;
- CWV field data;
- rich-result errors;
- mobile parity.

## Autoridad

- nuevos referring domains legítimos;
- enlaces a páginas profundas, no solo home;
- cobertura de Manecillas en fuentes independientes;
- exactitud de Knowledge Panel cuando exista;
- consultas de marca y combinaciones autor+título.

## Calidad editorial

- piezas con experiencia/investigación propia;
- actualización factual documentada;
- fuentes primarias;
- porcentaje de directorios con `verifiedAt` vigente;
- páginas retiradas/noindex en lugar de contenido obsoleto engañoso;
- ausencia de contenido masivo sin valor diferencial.

---

# Principios de decisión

1. **Search Console manda sobre suposiciones de demanda.**
2. **Una URL debe resolver una intención clara.**
3. **No crear una URL nueva cuando una página existente pueda mejorar.**
4. **La experiencia propia vale más que reescribir lo que ya existe en diez sitios.**
5. **Las herramientas deben resolver tareas; el texto SEO acompaña, no sustituye la utilidad.**
6. **Las recomendaciones deben ser útiles aunque Samuel no fuese uno de los libros incluidos.**
7. **Los directorios deben verificar, filtrar, comparar o actualizar; compilar no basta.**
8. **La entidad del autor se construye con consistencia y corroboración, no repitiendo su nombre.**
9. **Structured data describe contenido real; no crea una realidad nueva.**
10. **Links comprados para ranking no forman parte de esta estrategia.**
11. **No cambiar fechas para parecer fresco.**
12. **No interpretar una fluctuación durante un update como efecto causal de nuestro último commit.**

---

# Documentos

1. [`01-ESTADO-ACTUAL-Y-GAPS.md`](./01-ESTADO-ACTUAL-Y-GAPS.md)
2. [`02-RASTREO-INDEXACION-CANONICAS-Y-SITEMAPS.md`](./02-RASTREO-INDEXACION-CANONICAS-Y-SITEMAPS.md)
3. [`03-ARQUITECTURA-INTERLINKING-Y-QUERY-ROLES.md`](./03-ARQUITECTURA-INTERLINKING-Y-QUERY-ROLES.md)
4. [`04-CONTENIDO-PEOPLE-FIRST-AUTORIDAD-TEMATICA-Y-KEYWORDS.md`](./04-CONTENIDO-PEOPLE-FIRST-AUTORIDAD-TEMATICA-Y-KEYWORDS.md)
5. [`05-SERP-TITLES-SNIPPETS-SITELINKS-FEATURED-Y-PREFERRED.md`](./05-SERP-TITLES-SNIPPETS-SITELINKS-FEATURED-Y-PREFERRED.md)
6. [`06-STRUCTURED-DATA-ENTIDADES-LIBROS-EVENTOS-Y-REVIEWS.md`](./06-STRUCTURED-DATA-ENTIDADES-LIBROS-EVENTOS-Y-REVIEWS.md)
7. [`07-IMAGENES-VIDEO-DISCOVER-NEWS-Y-SUPERFICIES.md`](./07-IMAGENES-VIDEO-DISCOVER-NEWS-Y-SUPERFICIES.md)
8. [`08-CWV-PAGE-EXPERIENCE-MOBILE-RENDERING-Y-PERFORMANCE.md`](./08-CWV-PAGE-EXPERIENCE-MOBILE-RENDERING-Y-PERFORMANCE.md)
9. [`09-AUTORIDAD-ENLACES-PR-REPUTACION-Y-KNOWLEDGE-PANEL.md`](./09-AUTORIDAD-ENLACES-PR-REPUTACION-Y-KNOWLEDGE-PANEL.md)
10. [`10-MEDICION-EXPERIMENTOS-UPDATES-Y-RECOVERY.md`](./10-MEDICION-EXPERIMENTOS-UPDATES-Y-RECOVERY.md)
11. [`11-BACKLOG-IMPLANTACION-CLAUDE.md`](./11-BACKLOG-IMPLANTACION-CLAUDE.md)
12. [`12-SPAM-POLICIES-MITOS-Y-ANTI-PATRONES.md`](./12-SPAM-POLICIES-MITOS-Y-ANTI-PATRONES.md)
13. [`13-FUENTES-OFICIALES-Y-CORTE-2026-08-27.md`](./13-FUENTES-OFICIALES-Y-CORTE-2026-08-27.md)
14. [`14-GOOGLE-PRODUCTS-Y-OPORTUNIDADES-CONDICIONALES.md`](./14-GOOGLE-PRODUCTS-Y-OPORTUNIDADES-CONDICIONALES.md)

---

# Contexto algorítmico al corte

No evaluar cambios de finales de agosto sin tener en cuenta que Google acaba de completar el **August 2026 spam update**:

- inicio: 18/08/2026;
- duración oficial: 2 días y 16 horas;
- cerrado: 21/08/2026.

Otros updates de ranking de 2026 registrados por Google:

- June 2026 spam update;
- May 2026 core update;
- March 2026 core update;
- March 2026 spam update;
- February 2026 Discover update.

A 27/08/2026 el Search Status Dashboard no muestra incidentes activos.

Regla: anotar updates oficiales en el histórico de medición y no diagnosticar causalidad durante ventanas de rollout sin segmentar datos.

---

# Criterio de éxito

El plan estará implantado cuando:

- los P0 se hayan cerrado con evidencia en producción/Search Console;
- cada URL estratégica tenga query role, canonical, index state y hub claros;
- no haya structured data de reviews de terceros;
- los sitemaps reflejen exactamente las URLs indexables canónicas;
- `lastmod` sea fiable o se omita;
- los eventos futuros relevantes puedan ser elegibles mediante páginas dedicadas;
- el contenido nuevo supere un gate people-first antes de publicarse;
- los directorios/herramientas demuestren valor original;
- el linking interno concentre autoridad en hubs y páginas prioritarias;
- la estrategia externa se base en cobertura/reseñas/enlaces auténticos;
- title/snippet experiments se basen en Search Console y no en opiniones;
- CWV se mida con field data además de CI;
- cada update algorítmico relevante quede anotado;
- no se introduzcan prácticas de spam por intentar acelerar resultados.
