# 03 — Arquitectura, interlinking y query roles

## Objetivo

Hacer que cada URL tenga un trabajo reconocible para:

- usuarios;
- Google;
- arquitectura del sitio;
- medición.

La web tiene suficiente contenido para beneficiarse de clusters, pero también suficiente solapamiento potencial como para empezar a canibalizarse si se crean páginas por cada variación de búsqueda.

---

# 1. Modelo de arquitectura

## Nivel 0 — Home

`/`

Responsabilidades:

- identidad del autor;
- obra principal actual;
- acceso a Obras, Cuaderno, Herramientas y Autor;
- señal de marca;
- WebSite/Person.

No debe intentar rankear para todas las queries de escritura/fantasía.

## Nivel 1 — Hubs principales

- `/libros/`
- `/cuaderno/`
- `/herramientas/`
- `/autor.html`
- `/editoriales/`
- `/convocatorias-escritores/`
- `/recomendaciones/`

Cada hub debe:

- explicar su propósito;
- enlazar las mejores hojas;
- priorizar según utilidad, no cronología únicamente;
- evitar una lista plana inmanejable;
- contener enlaces HTML rastreables.

## Nivel 2 — Topic/subhubs

Ejemplos:

- `/cuaderno/temas/`
- `/cuaderno/temas/fantasia-de-portales/`
- fichas/grupos de editoriales;
- categorías de herramientas solo cuando haya masa crítica.

No crear hubs vacíos con dos enlaces y 300 palabras SEO.

## Nivel 3 — Leaf pages

- artículos;
- libro;
- herramienta;
- ficha editorial;
- recomendación;
- evento futuro;
- guía de club.

---

# 2. Query role

Cada URL indexable necesita un `queryRole` conceptual.

No es necesario publicarlo en JSON, pero puede añadirse al registry para QA.

Valores posibles:

- `brand-entity`;
- `book-title`;
- `definition`;
- `comparison`;
- `recommendation`;
- `how-to`;
- `tool`;
- `directory-hub`;
- `directory-entity`;
- `fresh-list`;
- `event`;
- `press`;
- `topic-hub`;
- `sample`;
- `reference`.

La regla es que dos URLs no deberían compartir exactamente el mismo rol + misma entidad/tema salvo una razón fuerte.

---

# 3. Matriz inicial de roles

## Marca/autor

| URL | Query role | Intención |
|---|---|---|
| `/` | brand-entity | web oficial / autor / obras |
| `/autor.html` | brand-entity-detail | biografía y trayectoria |
| `/premios.html` | reference | premios/reconocimientos |
| `/prensa.html` | press | medios/materiales |
| `/eventos.html` | event-hub | agenda |
| `/ai/` | machine/reference | autoridad factual; no target humano principal |

## Obras

| URL | Query role | Intención |
|---|---|---|
| `/libros/` | works-hub | libros del autor |
| `/las-manecillas-del-recuerdo/` | book-title | título + información oficial |
| `/las-manecillas-del-recuerdo/fragmentos/` | sample | leer fragmento |
| `/libros/samuel-entre-mundos/` | book-title | título + información + compra |
| `/fragmento/` | sample | capítulo 1 Samuel |
| `/universo/noveris/` | reference | universo/lore |
| `/clubes-de-lectura/samuel-entre-mundos/` | how-to/resource | club de lectura |

## Portal fantasy

| URL | Query role | Primary intent |
|---|---|---|
| `/cuaderno/que-es-el-portal-fantasy/` | definition | qué es portal fantasy |
| `/cuaderno/portal-fantasy-vs-fantasia-epica/` | comparison | diferencias |
| `/cuaderno/temas/fantasia-de-portales/` | topic-hub | explorar contenido del tema |
| `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/` | analysis | contexto/rasgos en español |
| `/recomendaciones/portal-fantasy-espanol/` | recommendation | qué leer |
| `/libros/samuel-entre-mundos/` | book-title | obra concreta |

## Magia

| URL | Role |
|---|---|
| `/recomendaciones/magia-con-coste/` | recommendation |
| `/cuaderno/worldbuilding-noveris-ciudad-magica/` | analysis/case-study |
| `/cuaderno/sistema-de-magia-noveris/` | retired/noindex |
| herramientas relacionadas | tool, no artículo sustituto |

---

# 4. Canibalización

No asumir canibalización solo porque dos páginas compartan palabras.

Existe un problema cuando:

- alternan en la misma query sin intención distinta;
- ninguna consolida señales;
- Google elige una URL menos útil;
- CTR/ranking se fragmentan;
- anchors internos son ambiguos;
- títulos casi duplicados.

## Diagnóstico

Usar Search Console:

1. query concreta;
2. dimension Page;
3. comparar clicks/impressions/position;
4. analizar fechas;
5. revisar SERP;
6. decidir.

## Resoluciones

Orden de preferencia:

1. aclarar title/H1/copy/anchors;
2. mejorar rol diferente;
3. internal link hacia canonical semantic owner;
4. fusionar si el contenido realmente duplica;
5. redirect permanente de la URL retirada;
6. noindex solo si la página sigue siendo útil fuera de Search.

No usar canonical cross-page para «arreglar» páginas que deberían fusionarse sin entender la intención.

---

# 5. Internal linking

Google indica que los links ayudan a descubrir páginas y a entender relevancia.

## 5.1 Reglas de anchor

Preferir:

- `qué es el portal fantasy`;
- `Samuel entre mundos`;
- `herramientas para escritores`;
- `directorio de editoriales`.

Evitar abusar de:

- `haz clic aquí`;
- `más información`;
- anchors keyword-exact repetidos artificialmente en cada página.

El anchor debe ser natural dentro de la frase.

## 5.2 Contextual > footer-only

Un link contextual relevante transmite mejor relación semántica y ayuda más al usuario que confiar solo en footer/sitemap.

Para páginas prioritarias, exigir al menos:

- link del hub;
- 2–5 links contextuales desde contenidos relacionados cuando existan;
- breadcrumbs.

## 5.3 No sobreenlazar

No convertir cada mención de «fantasía» en un link.

Una página con docenas de links repetitivos:

- diluye lectura;
- no aporta una jerarquía clara;
- parece optimización mecánica.

---

# 6. Grafo recomendado

## Obras

`Home → Obras → Libro → Fragmento / Universo / Club / Eventos / Recomendaciones`

Y backlinks contextuales:

`Cuaderno → Libro`

cuando el artículo realmente lo menciona.

## Cuaderno

`Home → Cuaderno → Tema → Artículo`

`Artículo ↔ Artículo relacionado`

`Artículo → Obra` solo si relevante.

## Herramientas

`Home → Herramientas → herramienta`

`herramienta → siguiente herramienta lógica`

Ejemplo:

`contador → repeticiones → variedad léxica → limpiador/manuscrito`

No enlazar cada herramienta con las 25 restantes.

## Editoriales

`Home/Explorar → Herramientas/Editoriales → ficha`

`ficha → metodología`

`ficha → convocatoria` si hay relación factual.

---

# 7. Click depth

Crear un reporte de profundidad real a partir del public artifact.

## Objetivos orientativos

- primary hubs: 1 click;
- books/author: 1–2;
- important topic hubs: <=2;
- priority articles/tools: <=3;
- long-tail entity pages: <=4 si el hub las organiza bien.

Esto no es una regla de ranking de Google; es una heurística de arquitectura.

---

# 8. Hubs: requisitos mínimos

Un hub indexable debe tener:

- propósito claro;
- introducción breve útil;
- organización significativa;
- enlaces crawlable;
- contenido suficiente para decidir adónde ir;
- title/H1 distinto de hojas;
- no duplicar los primeros párrafos de cada hijo.

## No crear

- páginas de etiqueta con un solo artículo;
- categorías generadas por cada keyword;
- archivos cronológicos sin utilidad;
- paginación indexable infinita.

---

# 9. Topic authority

No se construye repitiendo una keyword, sino cubriendo un tema desde perspectivas realmente útiles.

## Portal fantasy cluster

Ya existe una buena base:

- definición;
- comparación;
- caso propio;
- recomendaciones;
- mundo de ficción;
- libro.

Siguiente expansión posible solo si hay calidad:

- anatomía de un buen portal narrativo;
- cómo evitar que un portal sea un deus ex machina;
- decisiones reales tomadas al escribir Noveris;
- lectura comparada desde experiencia real.

No publicar `qué es portal fantasy para principiantes`, `portal fantasy explicado`, `significado de portal fantasy`, etc. como URLs separadas.

## Escritura/herramientas

El cluster se construye por tareas:

- analizar texto;
- limpiar manuscrito;
- diálogo;
- POV;
- personajes;
- metadatos;
- prensa;
- publicación/editoriales.

No por cientos de preguntas long-tail artificiales.

---

# 10. Site purpose

Google recomienda que un sitio tenga un propósito/audiencia reconocibles.

La web puede legítimamente atender lectores y escritores porque es el ecosistema de un autor, pero debe mantener un centro claro:

> obras + lectura + proceso/escritura + recursos editoriales útiles.

## Fuera de alcance SEO

No expandir a:

- tecnología genérica;
- viajes;
- salud;
- finanzas;
- noticias generales;
- IA genérica;
- cualquier tema solo porque tenga volumen.

Aunque una keyword tuviera mucho tráfico, debilitaría el propósito y no beneficiaría al usuario objetivo.

---

# 11. Arquitectura de recomendaciones

Las páginas de recomendaciones son sensibles por el sesgo obvio de un autor que recomienda su propio libro.

## Gate

Cada lista debe declarar/mostrar de forma natural:

- criterio de selección;
- qué significa el rasgo;
- por qué cada obra encaja;
- limitaciones;
- afiliación cuando corresponda;
- relación de David con Samuel si se incluye.

No hacer que Samuel sea #1 por defecto.

### Test conceptual

Eliminar Samuel de la página.

¿Sigue siendo una buena página para el usuario?

Si no, probablemente es una landing promocional disfrazada de recomendación.

---

# 12. Arquitectura de directorios

## Hubs

`/editoriales/`

Debe responder:

- qué contiene;
- cómo se verifica;
- cómo filtrar;
- fecha de revisión;
- límites.

## Entity page

Cada editorial necesita valor propio.

Mínimo recomendado:

- nombre;
- país;
- géneros si están verificados;
- recepción de manuscritos: sí/no/desconocido;
- método;
- fuente oficial;
- `verifiedAt`;
- notas específicas;
- status.

## No indexar

Una ficha con:

`Nombre + una descripción genérica + enlace`

si se generan cientos iguales.

---

# 13. Arquitectura de eventos

## Hub

`/eventos.html`

- próximos;
- archivo reciente;
- CTA profesional.

## Evento individual futuro

`/eventos/2026-09-XX-presentacion-manecillas-.../`

Role: event.

Debe recibir links desde:

- hub;
- libro relevante;
- home temporalmente si es prioritario;
- artículo posterior si se publica crónica.

Después del evento:

- marcar completed;
- conservar si tiene fotos/crónica/valor;
- no mantener una landing vacía para siempre.

---

# 14. Titles y roles

Title no debe intentar cubrir múltiples roles.

Malo:

`Portal fantasy: qué es, mejores libros, diferencias, Samuel entre mundos, fantasía juvenil...`

Mejor:

- definición page → definición;
- recommendations → libros;
- comparison → comparación.

Esto ayuda a Google a elegir la URL adecuada y mejora CTR humano.

---

# 15. Automatización propuesta

## `scripts/seo/build-link-graph.py`

Input:

- public dist;
- content registry.

Output JSON/Markdown:

```json
{
  "url": "/libros/samuel-entre-mundos/",
  "territory": "obras",
  "depthFromHome": 2,
  "inboundInternal": 17,
  "inboundAnchors": [...],
  "outboundInternal": 12,
  "hub": "/libros/"
}
```

Flags:

- orphan;
- depth high;
- no link from hub;
- ambiguous anchor;
- link to noindex;
- link to redirect;
- child not linking parent/hub.

## `data/seo-query-roles.json`

Opcional, si se considera útil:

```json
{
  "/cuaderno/que-es-el-portal-fantasy/": {
    "role": "definition",
    "topic": "portal-fantasy"
  }
}
```

No guardar keywords exhaustivas; solo responsabilidad editorial.

---

# 16. Search Console integration

Crear reportes:

- query → pages;
- page → top queries;
- query with >1 competing page;
- hub vs leaf performance;
- internal linking priority based on impressions.

No auto-fusionar páginas basándose en una semana de datos.

---

# 17. Acceptance criteria

- cada URL indexable tiene un rol;
- ningún nuevo contenido se publica sin parent/hub;
- páginas prioritarias no son orphan/near-orphan;
- query overlaps se validan con Search Console;
- anchors son descriptivos y naturales;
- no hubs vacíos;
- no pages-per-keyword;
- recomendaciones tienen utilidad independiente;
- directorios tienen valor verificable por ficha;
- eventos nuevos tienen arquitectura dedicada cuando proceda;
- el grafo se puede auditar automáticamente.
