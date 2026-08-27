# 01 — Estado actual y gaps de AI discoverability

**Corte:** 2026-08-27  
**Propósito:** distinguir lo que ya está bien resuelto en el proyecto de lo que todavía limita descubrimiento, citación o recomendación en sistemas con IA.

---

## 1. Resumen ejecutivo

La web ya dispone de una infraestructura de autoridad considerable: entidad Person, entidades Book, ISBN, editorial, fechas, `sameAs`, `subjectOf`, sitemaps, robots orientado a crawlers de IA, `llms.txt`, `llms-full.txt`, `/ai/`, press-kit JSON y contenido editorial propio.

El cuello de botella principal no es «falta un archivo para IA». Los principales gaps son:

1. **frescura entre repo, producción, cachés e índices externos**;
2. **ausencia de observabilidad específica de Copilot/Bing AI e IndexNow**;
3. **falta de benchmark transversal para saber qué asistentes entienden bien o mal la entidad**;
4. **corroboración externa todavía limitada para Manecillas frente a Samuel**;
5. **contenido original con potencial citable que puede crecer mucho más**;
6. **trust signals editoriales incompletos a nivel de dominio —p. ej. política de correcciones visible—**;
7. **llms/machine surfaces útiles como interoperabilidad, pero con riesgo de sobrevalorar su efecto real**;
8. **no hay todavía una disciplina de crawler/WAF/log monitoring**;
9. **las recomendaciones de libros dependen también de ecosistemas de retailers/reseñas externos, no solo del sitio oficial**.

---

## 2. Inventario de fortalezas existentes

### 2.1 `robots.txt`

El archivo actual permite acceso general y además declara explícitamente:

- OAI-SearchBot;
- ChatGPT-User;
- GPTBot;
- PerplexityBot;
- Applebot-Extended;
- ClaudeBot;
- Claude-SearchBot;
- Claude-User;
- Google-Extended.

También declara `sitemap.xml`.

#### Valor

- OpenAI puede rastrear mediante OAI-SearchBot.
- Anthropic puede buscar/indexar mediante Claude-SearchBot y recuperar a petición de usuario mediante Claude-User.
- PerplexityBot puede indexar.
- el acceso general permite Applebot, Bingbot, Googlebot y otros crawlers ordinarios salvo bloqueo externo.

#### Matiz

El archivo mezcla bots de **search/retrieval** con bots/tokens de **model training**. Esto no es incorrecto, pero necesita una política explícita: permitir GPTBot, ClaudeBot, Google-Extended o Applebot-Extended no debe justificarse como táctica de ranking porque los proveedores separan esas finalidades.

---

## 3. `llms.txt` y `llms-full.txt`

### Lo bueno

- contienen hechos concretos;
- diferencian premio del autor de premios de las novelas;
- incluyen ISBN, editorial, páginas y disponibilidad;
- desambiguan Noveris;
- enlazan fuentes y perfiles externos;
- advierten que el archivo no garantiza ingestión/ranking.

### Gap conceptual

Google Search declaró en junio/julio de 2026 que **ignora `llms.txt` para visibilidad/ranking**, aunque no perjudica mantenerlo para otros sistemas.

No se ha localizado documentación oficial equivalente de OpenAI, Anthropic o Perplexity que garantice que la mera existencia de `/llms.txt` haga que una página sea mejor posicionada orgánicamente.

### Decisión

**PRESERVAR**, pero tratarlo como:

- interfaz machine-friendly;
- resumen factual;
- superficie útil para agentes/herramientas que decidan leerlo;
- ayuda humana para verificadores;

no como «factor GEO».

### Gap editorial residual

`llms-full.txt` todavía contiene terminología de mantenimiento como «contrato temporal» o «contrato editorial». La PR #109 ya trabajó esta superficie; esta iniciativa no debe duplicar cambios sin revisar el estado posterior a merge.

---

## 4. `/ai/`

### Fortalezas

La versión de repo actual:

- es indexable;
- tiene canonical;
- define WebPage JSON-LD;
- enlaza `llms` y press-kit;
- presenta ledger factual del autor y las obras;
- evita prometer ingestión/ranking;
- desambigua hechos.

### Gap de frescura observado

Durante esta investigación, el snapshot público recuperado para `/ai/` seguía mostrando una versión antigua con, entre otros:

- Samuel en 2026;
- Manecillas en proceso;
- email anterior;
- formulaciones «Cuándo recomendar Samuel entre mundos»;
- comparables formulados como instrucciones a modelos;
- datos dinámicos antiguos de valoraciones.

Al mismo tiempo, el rastreo de la home del 27/08 mostraba ya el nuevo shell y hechos actuales.

### Interpretación correcta

Esto **no demuestra** que el origen de `/ai/` siga sirviendo esa versión en este instante. Sí demuestra algo operacionalmente importante: un sistema de retrieval puede tener una vista vieja de una URL durante bastante tiempo.

### Acción

Crear un protocolo de `publish → verify origin → notify → recrawl → rebenchmark`.

---

## 5. Knowledge graph actual

La home ya contiene un grafo amplio:

### `WebSite`

- nombre y alternateName;
- URL;
- author;
- idioma;
- descripción.

### `Person`

- nombre;
- URL;
- imagen;
- jobTitle;
- descripción;
- lugar de nacimiento;
- residencia;
- nacionalidad;
- ocupación;
- conocimientos;
- premios/reconocimientos;
- `sameAs`;
- `subjectOf`.

### `Book`

Samuel:

- ISBN;
- editorial;
- fecha;
- páginas;
- imagen;
- género;
- formato;
- URL;
- referencias exactas de la obra.

Manecillas:

- ISBN;
- Monza;
- fecha 03/09/2026;
- 272 páginas;
- imagen;
- géneros;
- URL.

### Conclusión

No priorizar «más schema». Priorizar:

- coherencia;
- generación desde datos canónicos;
- evitar relaciones incorrectas;
- que el contenido visible confirme el JSON-LD;
- verificar con validators;
- actualizar solo cuando exista un hecho real.

---

## 6. Identidad externa actual

### Autor

Ya existen enlaces hacia:

- Wikidata;
- ORCID;
- Amazon Author Central;
- Goodreads;
- Babelio;
- StoryGraph;
- Instagram;
- Facebook;
- TikTok;
- Threads;
- Bluesky;
- Pinterest;
- LinkedIn.

### Samuel

Existe corroboración en:

- editorial;
- Amazon;
- Casa del Libro;
- Goodreads;
- Open Library;
- LibraryThing;
- Qué Libro Leo;
- ISFDB;
- cobertura externa.

### Manecillas

El sitio tiene los datos editoriales, pero la obra necesita acumular naturalmente el mismo tipo de huella externa después de publicación:

- ficha editorial;
- retailers verificados;
- bibliotecas/catálogos cuando existan;
- Goodreads/Babelio/StoryGraph/LibraryThing/Open Library si procede y los datos son correctos;
- reseñas reales;
- prensa;
- clubes;
- entrevistas;
- eventos.

No crear perfiles falsos o duplicados solo por «entidad».

---

## 7. Contenido interno con potencial de citación

### Muy valioso

- guía de portal fantasy;
- artículos sobre fantasía juvenil española;
- Noveris;
- herramientas para escritores;
- directorio de editoriales;
- convocatorias;
- recomendaciones;
- metodología editorial;
- clubes de lectura;
- fragmentos;
- artículos sobre experiencias reales —Feria del Libro, proceso de escritura, etc.

### Por qué

Google aconseja expresamente contenido **non-commodity**, con perspectiva o experiencia propias. Los asistentes de búsqueda necesitan fuentes que aporten algo que una síntesis genérica no tenga ya.

### Gap

Parte del contenido de herramientas/directorios puede convertirse en commodity si solo replica datos que existen en otros sitios. Para tener potencial citable debe aportar:

- verificación propia;
- fecha;
- metodología;
- contexto;
- comparación útil;
- experiencia;
- ejemplos originales;
- actualización demostrable.

---

## 8. Autoría y trust editorial

### Ya existe

- autor identificable;
- página de Autor;
- contacto;
- metodología editorial;
- prensa;
- política de privacidad/legal;
- fechas en parte del contenido.

### Falta o conviene reforzar

- política pública de correcciones y errores;
- firma/byline consistente en artículos;
- `datePublished` / `dateModified` visibles y machine-readable donde proceda;
- distinguir editorial/opinión/recomendación/publicidad/afiliación;
- disclosure de afiliados cerca de contenido comercial relevante;
- fuentes primarias citadas en fichas verificadas;
- no esconder cambios factuales críticos solo en commits.

Perplexity ha publicado en agosto de 2026 que su revisión de fuentes comprueba, entre otros criterios, si un dominio corrige errores, identifica autores y separa información de publicidad/opinión.

---

## 9. Bing/Copilot: gap de tooling

No se encontró en el repositorio una implementación/documentación de:

- IndexNow;
- Bing Webmaster Tools AI Performance.

### Prioridad

Alta.

Microsoft ofrece desde febrero de 2026 un informe AI Performance con:

- total citations;
- average cited pages;
- cited URLs;
- grounding queries;
- tendencias;
- y mejoras preview relacionadas con intents/topics/citation share.

Es la señal de IA más accionable que hoy proporciona un webmaster tool de propósito general.

---

## 10. IndexNow: gap técnico

No se localizó implementación de IndexNow.

### Por qué encaja especialmente aquí

Microsoft relaciona explícitamente IndexNow con frescura para Search y respuestas generativas.

Nuestra web tiene:

- eventos;
- convocatorias;
- directorios;
- fichas de obra;
- fechas de lanzamiento;
- páginas que cambian por disponibilidad;

por lo que la frescura sí es material.

### Requisito

No enviar todas las URLs a cada build. Enviar solo URLs cuyo contenido público haya cambiado de forma significativa o que hayan sido creadas/eliminadas.

---

## 11. WAF/CDN: gap de comprobación

Tener `Allow` en `robots.txt` no garantiza acceso si Cloudflare bloquea por:

- bot fight;
- managed rules;
- rate limit;
- country/network;
- challenge;
- IP reputation.

### Proveedores con fuentes IP publicadas relevantes

- OpenAI publica JSON para OAI-SearchBot y otros bots.
- Perplexity publica JSON para PerplexityBot y Perplexity-User.
- Anthropic dispone actualmente de `https://claude.com/crawling/bots.json` con prefijos publicados, aunque parte de su documentación textual puede ir por detrás.

### Política

No copiar rangos estáticos a un fichero y olvidarlos. Si Cloudflare necesita allowlist, generar/verificar desde endpoints oficiales y registrar `creationTime`.

---

## 12. Medición actual: gap fuerte

No existe todavía una autoridad del proyecto que responda:

- ¿ChatGPT menciona a David en qué consultas?
- ¿qué URL cita?
- ¿Claude tiene el año correcto?
- ¿Perplexity usa el sitio oficial o terceros?
- ¿Copilot cita Cuaderno o solo home?
- ¿qué prompts de recomendación hacen aparecer Samuel y por qué?
- ¿qué falsedades persisten?

### Solución

Benchmark fijo + AI Performance + Search Console GenAI + referrals + logs.

No depender de recuerdos anecdóticos de «ayer pregunté y salía».

---

## 13. Recommendation fit: oportunidad

Para que un libro pueda aparecer cuando alguien pregunta:

> «Recomiéndame fantasía juvenil española con portales y magia con un coste real»

el sitio debe expresar claramente atributos verificables.

Ya lo hacemos en Samuel, pero conviene que esos atributos aparezcan en páginas humanas de calidad:

- género;
- tropes;
- tono;
- ejes temáticos;
- protagonismo;
- presencia/no centralidad de romance;
- dificultad/ritmo solo si se puede sostener editorialmente;
- público sin inventar edad oficial;
- formato/páginas;
- por qué puede encajar;
- cuándo probablemente no encaja.

Esto debe redactarse **para lectores**, no como prompt al sistema.

---

## 14. Comercio/recomendación de compra

OpenAI usa en shopping:

- datos de merchants mediante ACP;
- información pública de producto;
- fuentes comerciales externas;
- atributos como precio/disponibilidad/calidad y vendedor principal.

### Estado de esta web

- Samuel tiene links de retailers externos.
- Manecillas no debe inventar retailer hasta tener URL verificada.
- davidportodiaz.com no se ha establecido como merchant/checkout propio para estos libros.

### Decisión

- reforzar consistencia en editor/retailers/reseñas;
- no crear feed ACP propio sin autoridad comercial real;
- no añadir Product Offer falsa;
- revaluar si en el futuro se vende directamente.

---

## 15. Social y Meta AI

Meta AI está integrando contenido web en tiempo real mediante partnerships y sus productos usan cada vez más contenido público/original de sus propias plataformas.

Para el proyecto, la oportunidad real está en:

- Instagram/Facebook/Threads públicos coherentes;
- Reels originales;
- mencionar claramente título/autor/tema en copy humano;
- enlaces canónicos cuando la plataforma lo permita;
- no clonar el mismo post mecánicamente;
- acumular conversación real y cobertura real.

No se encontró un «Meta Webmaster submit» público para que una web pequeña sea priorizada orgánicamente en Meta AI.

---

## 16. Apple

Applebot puede alimentar Search, Siri, Spotlight y contexto actualizado para experiencias con modelos de IA de Apple.

### Estado

Global `Allow` ya permite Applebot.

### Matiz

`Applebot-Extended` controla posible uso para entrenamiento de modelos generales. No es el crawler de Search. Permitirlo o bloquearlo es decisión editorial independiente.

---

## 17. Brave / downstream search APIs

Brave tiene índice independiente y experiencias AI Answers/Ask Brave con citas.

Su crawler no presenta un UA diferenciado y usa crawlability similar a Googlebot como condición.

Esto refuerza una idea importante:

> la buena salud de indexación tradicional también distribuye el contenido hacia sistemas de IA que reutilizan índices o Search APIs.

No hace falta crear un «robots Brave» inexistente.

---

## 18. Estado por bloque

| Bloque | Estado | Acción |
|---|---|---|
| Identidad autor | fuerte | mantener/paridad externa |
| Identidad Samuel | fuerte | corregir terceros si divergen |
| Identidad Manecillas | media/creciendo | ampliar corroboración post-publicación |
| JSON-LD | fuerte | no sobreoptimizar; generar/paridad |
| `llms.txt` | útil, no ranking Google | preservar |
| `/ai/` | buena versión repo; frescura externa dudosa | verificar/recrawl |
| Crawlers OpenAI/Claude/Perplexity | permitidos | verificar WAF |
| Training bots | permitidos | decisión explícita, no ranking |
| IndexNow | ausente | implementar |
| Bing AI Performance | no documentado | configurar/revisar |
| Benchmark IA | ausente | crear |
| AI referrals | sin taxonomía específica | implementar reporting |
| Política de correcciones | incompleta/no localizada | crear |
| Contenido original | buena base | profundizar |
| Autoridad externa | buena en Samuel | ampliar de forma auténtica |
| Shopping AI | indirecto vía retailers | no feed propio todavía |
| Agent readiness | buena base accesible | auditar tareas críticas |

---

## 19. Definición de éxito de esta iniciativa

No es «David sale primero siempre».

Es:

- los hechos básicos se responden correctamente de manera consistente;
- cuando un asistente cita, el sitio oficial aparece como fuente primaria cuando corresponde;
- cuando recomienda, explica atributos reales;
- desaparecen los facts obsoletos;
- aumenta el conjunto de prompts legítimos donde las obras encajan;
- crece la citación de contenido experto del sitio;
- existe medición longitudinal;
- no se sacrifica reputación mediante spam GEO.
