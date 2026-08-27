# 05 — SERP: titles, snippets, sitelinks, featured snippets y Preferred Sources

## Objetivo

Mejorar cómo se representa una URL cuando ya es elegible y relevante.

Distinguir:

- **ranking**: si Google decide mostrar la URL y dónde;
- **appearance**: title link, snippet, favicon, breadcrumb, rich result, imagen;
- **CTR**: si el resultado convence al usuario.

Cambiar una meta description puede mejorar representación/CTR, pero no se documenta aquí como un factor directo de ranking.

---

# 1. Title links

Google genera title links automáticamente y puede usar:

- `<title>`;
- título visual/H1;
- headings;
- `og:title`;
- texto prominente;
- otros textos de la página;
- anchor text interno;
- anchor text externo;
- WebSite structured data para site name/contexto.

Por tanto, el title no se optimiza de forma aislada.

## Reglas

- único por página;
- descriptivo;
- conciso;
- sin keyword stuffing;
- sin boilerplate enorme;
- coincide con la intención;
- entidad/marca solo cuando ayuda;
- no prometer algo que la página no entrega.

## Inventario recomendado

Generar:

`url | current title | H1 | Google shown title | primary queries | impressions | CTR | action`

### No cambiar

una página que ya recibe buen CTR/relevancia solo porque una tool SEO diga que el title tiene 67 caracteres.

Google no trabaja con una longitud fija universal como criterio de calidad.

---

# 2. Titles actuales: dirección

## Home

Actual:

`David Porto Díaz | Las manecillas del recuerdo y Samuel entre mundos`

Es razonable para:

- marca;
- dos obras;
- entidad.

No convertirla en:

`David Porto Díaz escritor gallego Madrid fantasía juvenil novela coral autor libros...`

## Autor

`David Porto Díaz | Escritor`

Buena orientación de entidad.

## Samuel

`Samuel entre mundos — Portal fantasy juvenil español | David Porto Díaz`

Combina title intent + género sin sobrecargar.

## Manecillas

`Las manecillas del recuerdo · Novela de David Porto Díaz`

Protege exact title.

## Herramientas

Auditar caso a caso con queries.

Una herramienta puede beneficiarse de un title más descriptivo, pero no aplicar una plantilla `X gratis online 2026` a todas las páginas.

---

# 3. H1

El H1 debe expresar claramente el trabajo de la página.

No es obligatorio que sea byte-identical al `<title>`.

Google puede usarlo como fuente de title link.

## Regla

Una sola jerarquía visual principal comprensible.

No añadir varios H1 con variaciones de keyword para «cubrir términos».

---

# 4. Meta descriptions

Google crea snippets principalmente a partir del contenido visible y puede usar la meta description si considera que describe mejor la página.

Por tanto:

- description única;
- factual;
- específica;
- útil;
- puede incluir datos relevantes;
- no repetir title sin aportar nada;
- no lista de keywords.

## Páginas prioritarias

Mantener artesanalmente:

- home;
- autor;
- libros;
- book pages;
- principales hubs;
- artículos con demanda;
- herramientas top;
- editoriales/convocatorias hubs.

Para cientos de fichas de directorio, una generación templada puede ser aceptable solo si usa datos reales y genera descripciones útiles/no duplicadas.

---

# 5. Snippet control

El sitio ya utiliza `max-snippet:-1` en páginas principales.

Eso da libertad a Google.

Opciones avanzadas:

- `nosnippet` — no mostrar snippet;
- `max-snippet` — limitar longitud;
- `data-nosnippet` — impedir que una sección concreta se utilice.

## Casos donde `data-nosnippet` podría ser útil

Solo evaluar si Google insiste en mostrar en el snippet:

- navegación;
- disclaimers repetidos;
- texto de newsletter irrelevante;
- contenido dinámico no representativo.

No aplicar masivamente. Puede reducir la capacidad de Google de generar un snippet útil.

---

# 6. Featured snippets

No existe markup para «obtener featured snippet».

Google decide.

## Cómo aumentar elegibilidad naturalmente

- respuesta clara cerca de la pregunta;
- definición directa;
- pasos reales;
- tablas cuando son la mejor forma;
- headings semánticos;
- contenido completo debajo de la respuesta corta.

Ejemplo potencial:

`¿Qué es el portal fantasy?`

La página ya tiene una intención excelente para una respuesta inicial clara.

No reducir todo el artículo a bloques de 40 palabras escritos para snippet.

---

# 7. Sitelinks

Google los genera automáticamente.

Factores prácticos bajo nuestro control:

- arquitectura lógica;
- titles/headings informativos;
- links internos a páginas importantes;
- anchors claros;
- contenido no repetitivo.

## Sitelinks deseables para marca

Hipótesis, no control:

- Obras;
- Autor;
- Manecillas;
- Samuel;
- Cuaderno;
- Herramientas.

No existe un schema para forzar esos seis.

## Acción

Revisar qué sitelinks aparecen actualmente en búsqueda de marca y comprobar si Google está priorizando una URL secundaria inesperada.

---

# 8. Site name

La home ya usa `WebSite` con:

- `name`;
- `alternateName`;
- URL.

Google genera site name automáticamente a partir de múltiples fuentes.

No crear múltiples WebSite names contradictorios.

Preferencia:

`David Porto Díaz`

No alternar sistemáticamente entre:

- David Porto;
- David Porto escritor;
- Samuel entre mundos;
- David Porto Díaz | Escritor.

Las variantes pueden aparecer como alternateName, pero la identidad principal debe ser estable.

---

# 9. Favicon

Ya existe favicon.

Revisar:

- accesible a Google;
- estable;
- cuadrado;
- no cambia frecuentemente;
- representa la marca.

No es un factor de ranking, pero forma parte del resultado.

---

# 10. Breadcrumbs en SERP

El sitio ya tiene breadcrumbs.

Preservar:

- jerarquía visible;
- `BreadcrumbList` donde proceda;
- nombres humanos;
- URLs canónicas.

No usar breadcrumbs con keywords inventadas que no representen navegación real.

---

# 11. Rich results

No confundir rich result con ranking.

Una apariencia enriquecida puede mejorar visibilidad/CTR, pero Google no garantiza mostrarla.

Prioridades del sitio:

- Article;
- Breadcrumb;
- Book/Review donde sea legítimo;
- Event;
- ProfilePage;
- SoftwareApplication;
- image metadata;
- video si llega a existir.

No implementar schemas que Google ya no utiliza solo porque schema.org los soporte.

---

# 12. FAQ rich results

Estado 2026:

- retirados de resultados el 07/05/2026;
- apariencia/API en retirada.

Decisión:

- mantener FAQ visible si sirve al usuario;
- no añadir FAQPage para ganar SERP space;
- retirar deuda cuando convenga;
- no medir rich-result success con FAQ.

---

# 13. Preferred Sources

En 2026 Google permite a usuarios seleccionar fuentes preferidas para Top Stories y está desplegando el concepto también en AI Overviews/AI Mode.

El 20/08/2026 Google añadió documentación para un botón interactivo personalizado.

## Caso posible

`Cuaderno` podría ofrecer un CTA discreto a lectores recurrentes:

> Seguir a David Porto Díaz como fuente preferida en Google

## Gate

Antes de implementarlo:

1. comprobar que `davidportodiaz.com` es elegible;
2. comprobar disponibilidad geográfica/cuenta;
3. usar la integración oficial;
4. situarlo donde tenga sentido editorial, no en cada página;
5. no decir «esto hará que salgamos primeros».

## Ubicación propuesta

- Cuaderno hub;
- quizá footer editorial del Cuaderno;
- no herramientas puras;
- no legales;
- no popups intrusivos.

---

# 14. Byline/date

Para artículos:

- byline visible cuando relevante;
- fecha de publicación visible;
- actualización visible si es material;
- Article schema consistente.

Google puede mostrar byline dates basándose en varias señales.

No utilizar una fecha futura/reciente falsa.

---

# 15. Query-based snippet testing

Una misma página puede mostrar snippets distintos por query.

Por tanto, un experimento de description debe evaluar:

- query cluster;
- clicks;
- impressions;
- CTR;
- position;
- dispositivo;
- país cuando sea relevante.

No comparar CTR global antes/después sin controlar cambio de ranking/mix de queries.

---

# 16. CTR opportunity model

Crear segmentos, no score mágico.

## Oportunidad A

- posición competitiva;
- muchas impressions;
- CTR bajo relativo a la propia query;
- title/snippet no satisface intent.

Acción: test title/description/content intro.

## Oportunidad B

- impressions subiendo;
- posición 8–20;
- CTR naturalmente bajo.

Acción: mejorar contenido/authority/internal links antes que obsesionarse con title.

## Oportunidad C

- title reescrito por Google.

Acción: comprobar divergencia entre title, H1, prominent text y anchors.

---

# 17. Brand SERP

Auditar trimestralmente:

- home;
- site name;
- favicon;
- sitelinks;
- Knowledge Panel;
- social profiles;
- book results;
- news/articles;
- images;
- stale facts.

Query sets:

- `David Porto Díaz`;
- `David Porto Díaz escritor`;
- `David Porto libros`.

No hacer búsquedas repetidas logueado como única fuente; usar Search Console y revisiones neutrales.

---

# 18. Book SERP

Para cada libro revisar:

- official page;
- retailer/editorial;
- Goodreads/catálogos;
- images;
- snippets;
- fecha/editorial/ISBN;
- Knowledge Graph/Book panels si aparecen;
- queries relacionadas.

## Samuel

El sitio tiene huella externa fuerte.

Objetivo: que la página oficial sea una referencia clara, no competir agresivamente contra el retailer por todas las intenciones comerciales.

## Manecillas

Post-lanzamiento:

- confirmar indexación;
- comprobar title/snippet;
- editorial/retailer consistent;
- construir huella externa.

---

# 19. Tool SERP

Para herramientas, el snippet debe explicar utilidad inmediatamente.

Ejemplo:

- qué mide;
- que es gratis si es factual;
- procesamiento local si diferencia;
- resultado que obtiene el usuario.

No añadir «mejor», «#1» o «profesional» sin evidencia.

---

# 20. Directory SERP

Para editoriales/convocatorias el elemento diferencial debe aparecer en snippet/copy:

- verificado;
- fecha de revisión;
- filtros;
- fuente oficial;
- estado.

Evitar títulos que simulan actualidad automática:

`Las 500 editoriales que aceptan manuscritos en 2026`

si no se han verificado 500.

---

# 21. Experimentos

Cada test:

```yaml
id: SEO-TITLE-001
url: /herramientas/contador-palabras/
hypothesis: "..."
primary_query_cluster: "..."
start: YYYY-MM-DD
end_min: YYYY-MM-DD
baseline: {...}
change: "..."
algorithm_context: "none / update"
result: keep|revert|iterate
```

No ejecutar 15 title tests en una misma URL a la vez.

---

# 22. Acceptance criteria

- title/H1 intent-aligned;
- descriptions únicas en URLs prioritarias;
- no keyword stuffing;
- se conoce cuándo Google reescribe titles importantes;
- sitelinks se revisan como outcome, no como markup;
- featured snippet no se vende como controlable;
- FAQ schema no recibe inversión nueva;
- Preferred Sources solo tras eligibility;
- fechas/bylines honestos;
- CTR tests segmentados por query/position;
- brand/book SERPs revisados periódicamente.
