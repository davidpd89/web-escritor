# Asistente editorial V3 — auditoría, investigación y arquitectura

Fecha: 2026-08-24  
PR de trabajo: #94 · rama `assistant-editorial-ux-v2` · base `implementacion-web-2026`  
Estado: diseño/implementación incremental; IA remota sigue desactivada por defecto.

## 1. Objetivo

El asistente no debe intentar parecer un ChatGPT pequeño. Su trabajo real es más concreto y útil: entender cómo pide una persona algo relacionado con `davidportodiaz.com`, responder cuando existe una respuesta canónica y, cuando no existe, llevarla de forma natural al lugar correcto de la web.

La referencia visual es una publicación editorial contemporánea —especialmente la sobriedad de London Review of Books, MUBI Notebook, The Paris Review y The Yale Review—, no una interfaz SaaS de burbujas, pills y tarjetas flotantes.

Dirección pública de referencia:

- https://www.lrb.co.uk/
- https://mubi.com/es/notebook
- https://www.theparisreview.org/
- https://yalereview.org/

Estas webs se inspeccionan como productos públicos. No hay un repositorio de producción verificado y abierto de esas cuatro webs. El HTML/CSS/JS que el navegador descarga puede inspeccionarse con DevTools, pero eso no equivale al repositorio fuente ni da acceso a CMS, backend, templates privados o pipeline. La adaptación debe ser clean-room: reproducir patrones de jerarquía, ritmo, densidad y comportamiento, no copiar CSS/JS propietario.

## 2. Estado real auditado del bot

### 2.1 `/asistente/index.html`

La página estática ya es útil sin JavaScript: título, explicación, preguntas de ejemplo, formulario y límites. Con JS se transforma en una superficie conversacional. Esto es correcto para accesibilidad, SEO y resiliencia y debe conservarse.

### 2.2 `assets/assistant-config.js`

La IA remota está apagada por defecto (`remoteEnabled: false`). El cliente solo intenta `/api/assistant` si se activa explícitamente. Esto es importante: el modo normal no consume tokens ni una API de pago.

### 2.3 `assets/assistant-local-knowledge.mjs`

Es el primer nivel de respuesta. Actualmente reconoce frases mediante normalización + búsquedas de cadenas (`includes`) y algunas expresiones regulares. Ya resuelve libros, fragmentos, Noveris, autor, prensa, eventos, premios, editoriales, convocatorias, herramientas, recomendaciones, Cuaderno, saludos y aclaraciones de fragmento.

Puntos fuertes:

- determinista y auditable;
- instantáneo;
- 0 € por consulta;
- no envía la pregunta fuera del navegador;
- no puede inventar una URL si se conserva la lista canónica de fuentes;
- permite aclaraciones cortas con `pending`.

Deuda:

- demasiada lógica vive en una cascada de `if` + frases;
- sinónimos, alias, intenciones y respuestas están mezclados;
- una errata fuera de los alias previstos puede perder una intención;
- mantener cientos de frases manuales no escala;
- algunas preguntas de navegación (“¿dónde está…?”, “llévame a…”, “¿qué enlaces hay?”) deberían resolverse como orientación, no como pregunta factual.

### 2.4 `assets/assistant-core.mjs`

`rankLocalSources()` es un segundo fallback muy barato. Busca en `title`, `territory` y `keywords`, con pesos simples. Es correcto como red de seguridad, pero hoy desaprovecha campos posibles como alias, resumen, tarea/intent y acción. Conviene enriquecer el ranking antes de añadir otra librería.

### 2.5 `data/assistant-source-registry.json` + `assets/assistant-source-registry.js`

La política es deny-by-default: solo fuentes públicas conocidas. Es una buena frontera de seguridad. La registry contiene hubs y destinos importantes, mientras Pagefind cubre el corpus completo indexable.

No se debe convertir la registry en un segundo sitemap manual gigantesco. Su función ideal es ser un directorio pequeño de destinos canónicos de alta confianza. El contenido largo lo resuelve Pagefind.

### 2.6 `assets/assistant.js`

Flujo actual:

1. intenta respuesta local determinista;
2. si no existe, usa Pagefind local;
3. si Pagefind no puede cargar, rankea la registry;
4. solo si se habilita explícitamente el remoto, entra el Worker/Turnstile/Workers AI.

La arquitectura es mejor de lo que parece a primera vista: no es “solo keywords”. El punto que más conviene mejorar no es sustituirla, sino hacer más inteligente el enrutado local y aprovechar mejor los resultados que Pagefind ya devuelve.

Deuda observada en el fallback:

- Pagefind devuelve `plain_excerpt`, metadatos y `sub_results`, pero el asistente usa básicamente título + URL;
- la frase genérica “No tengo una respuesta exacta…” es correcta pero poco editorial;
- si no hay resultados, el usuario recibe una instrucción genérica en vez de una pequeña mesa de orientación estable;
- la respuesta podría decir “Por lo que preguntas, empezaría aquí” y presentar las dos o tres rutas con más sentido.

### 2.7 Pagefind

El repo ya contiene `pagefind@^1.5.2` y `scripts/build-pagefind-index.py`. El builder indexa solo páginas públicas/indexables y excluye chrome repetido. Esto elimina la necesidad de montar Elasticsearch, Algolia o un servidor de búsqueda.

Pagefind es especialmente adecuado aquí porque:

- genera un índice estático después del build;
- busca en el navegador, sin servidor de consultas;
- devuelve `url`, `excerpt`, `plain_excerpt` y `meta`;
- soporta filtros y metadatos;
- el título recibe un boost por defecto;
- permite ajustar ranking y peso por secciones;
- normaliza diacríticos por defecto;
- usa Web Worker cuando está disponible;
- ofrece `sub_results` por encabezados enlazables.

Fuentes oficiales:

- https://github.com/Pagefind/pagefind
- https://pagefind.app/docs/
- https://pagefind.app/docs/api/
- https://pagefind.app/docs/js-api-metadata/
- https://pagefind.app/docs/js-api-filtering/
- https://pagefind.app/docs/metadata/
- https://pagefind.app/docs/ranking/
- https://pagefind.app/docs/weighting/
- https://pagefind.app/docs/search-config/
- https://pagefind.app/docs/sub-results/
- https://pagefind.app/docs/indexing/

## 3. Alternativas gratuitas investigadas

### 3.1 Fuse.js

- Web: https://www.fusejs.io/
- Repo: https://github.com/krisk/Fuse

Fuzzy search client-side, sin infraestructura y sin dependencias. Tolera erratas con Bitap y permite claves ponderadas. Su build básico ronda pocos KB comprimidos.

Uso posible: fuzzy matching sobre las ~20–50 rutas canónicas del asistente.

Decisión V3: **no añadir ahora**. Para una registry tan pequeña podemos implementar tolerancia limitada a erratas sin dependencia y Pagefind ya cubre el contenido. Se reevalúa si el léxico crece mucho.

### 3.2 MiniSearch

- Web/docs: https://lucaong.github.io/minisearch/
- Repo: https://github.com/lucaong/minisearch

Búsqueda local en memoria, fuzzy/prefix, boosts y `autoSuggest()`. Muy buena alternativa para autocompletar y corregir consultas pequeñas.

Decisión V3: **evaluada, no adoptada**. Añadir otro índice de texto junto a Pagefind duplicaría responsabilidades. Su `autoSuggest()` sí queda anotado como opción futura si se quiere un buscador tipo command palette.

### 3.3 NLP.js

- Repo: https://github.com/axa-group/nlp.js
- FAQ v4: https://github.com/axa-group/nlp.js/blob/master/docs/v4/mini-faq.md

Permite entrenar intenciones con utterances, NER, contexto, respuestas y español. Es una solución real para pasar de reglas manuales a clasificación NLU.

Decisión V3: **P2, no prelaunch**. Para un asistente de navegación de una web pequeña añade entrenamiento, modelo, bundle/build y un nuevo punto de mantenimiento. Merece la pena si el catálogo supera aproximadamente decenas largas de intents, aparecen varios idiomas o las reglas empiezan a cruzarse demasiado.

### 3.4 Natural

- Repo: https://github.com/NaturalNode/natural

Incluye stemmer español, clasificadores y distancias de cadenas. Es potente pero orientado a NLP general en Node; no aporta suficiente ventaja frente a nuestra combinación determinista + Pagefind.

Decisión: **no adoptar**.

### 3.5 FlexSearch

- Repo: https://github.com/nextapps-de/flexsearch

Motor full-text muy rápido y configurable. De nuevo, solapa directamente con Pagefind y aumenta superficie técnica sin solucionar un problema que hoy tengamos.

Decisión: **no adoptar**.

## 4. IA gratuita: qué es realmente viable

### 4.1 Cloudflare Workers + Workers AI

El repo ya tiene un Worker de asistente preparado y protegido, pero apagado. Esa arquitectura es válida como capa opcional.

Fuentes oficiales:

- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/workers-ai/
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/workers-ai/platform/errors/

A 2026-08-24:

- Workers Free incluye 100.000 requests/día y 10 ms de CPU por invocación;
- Workers AI incluye una asignación gratuita de 10.000 Neurons/día;
- al superar la asignación gratuita, en Free las operaciones dejan de estar disponibles hasta el reset diario;
- algunos modelos concretos exigen Workers Paid, así que no se debe asumir que “cualquier modelo de Cloudflare es gratis”.

Conclusión: sirve como **mejora opcional**, no como dependencia de la experiencia básica. El asistente debe seguir siendo útil cuando AI está apagada, sin cuota o sin capacidad.

### 4.2 Cloudflare Turnstile

- https://developers.cloudflare.com/turnstile/plans/
- https://developers.cloudflare.com/turnstile/get-started/

Turnstile Free puede proteger el endpoint remoto. La validación debe mantenerse en servidor mediante Siteverify. La PR #92 conserva ownership de la configuración Cloudflare.

### 4.3 Cloudflare AI Search

- https://developers.cloudflare.com/ai-search/
- https://developers.cloudflare.com/ai-search/platform/limits-pricing/

En la beta actual permite búsqueda natural/semántica gestionada y tiene límites Free. Durante la open beta el producto es gratuito dentro de sus límites, pero Workers AI/AI Gateway pueden facturarse aparte y Cloudflare avisará antes de cambiar la tarificación.

Decisión: **P2 experimental**. No migrar el buscador actual antes de lanzamiento. Pagefind ya indexa el corpus público sin coste, sin servicio externo y con más privacidad. AI Search solo merece un experimento A/B si Pagefind falla de forma repetida en preguntas semánticas reales.

## 5. Arquitectura recomendada

### Capa 0 — contenido estático / no-JS

Siempre hay enlaces y ejemplos útiles aunque JavaScript falle. Obligatoria.

### Capa 1 — router local de intención

Para consultas previsibles y de alto valor:

- obra / libro concreto;
- fragmentos;
- Noveris;
- autor/prensa/contacto;
- eventos/premios;
- editoriales/convocatorias;
- herramientas;
- orientación general;
- small talk corto.

Debe ser determinista, con alias, tokens, exclusiones, prioridad y una tolerancia conservadora a erratas de entidades conocidas. Nunca debe “adivinar” una intención si la confianza es baja.

### Capa 2 — Pagefind como retrieval local

Para preguntas que no merecen un intent manual: “¿tenéis algo sobre diálogo?”, “¿hay una herramienta para legibilidad?”, “¿escribiste sobre portal fantasy?”, etc.

El bot no tiene que inventar una respuesta. Puede convertir el resultado en navegación natural:

> «Sí, hay una página que encaja con eso. Empezaría por esta: …»

Y acompañarla de excerpt + enlace.

### Capa 3 — directorio canónico

Si no hay coincidencia literal, no responder “no te he entendido”. Mostrar una salida editorial estable:

> «No encuentro una coincidencia clara, pero puedo llevarte por aquí: Obras · Cuaderno · Herramientas · Prensa.»

La registry canónica sirve para esto.

### Capa 4 — Workers AI opcional

Solo cuando:

- el usuario formula una pregunta real que requiere sintetizar varias páginas;
- hay fuentes controladas suficientes;
- el endpoint remoto está activado;
- Turnstile y rate limit están operativos;
- la respuesta cita las fuentes canónicas;
- si algo falla, vuelve a Capa 2/3.

No se usa IA remota para “hola”, “dónde están los libros” o “quiero el primer capítulo”.

## 6. Estrategia de comprensión sin coste

En vez de añadir cientos de keywords planas, separar cuatro conceptos:

1. **entidad**: `manecillas`, `samuel`, `noveris`, `editoriales`, `herramientas`;
2. **acción**: `leer`, `comprar`, `buscar`, `contactar`, `enviar`, `explorar`;
3. **intención**: `fragment`, `work-about`, `contact`, `events`, `tools`, `site-navigation`;
4. **contexto**: última intención/pregunta pendiente.

Ejemplos:

- “¿Dónde puedo probar Manecillas?” = entidad `manecillas` + acción `leer` → fragmentos.
- “¿Y Samuel?” después de preguntar por fragmentos = contexto `fragment-choice` + entidad `samuel`.
- “Llévame a lo de mandar novelas” = navegación + `enviar/manuscrito` → editoriales.
- “¿Dónde están todos los recursos?” = navegación + herramientas → hub de herramientas.

La respuesta no necesita ser generada por un LLM para sonar natural; necesita que la selección del destino sea correcta y que la microcopy esté escrita como conversación humana.

## 7. Contrato de fallback natural

Nunca usar como respuesta principal:

- «No te he entendido».
- «Entrada no válida» salvo validación técnica.
- «No sé» sin siguiente paso.
- una lista de cinco enlaces sin explicar por qué.

Usar según el caso:

### Coincidencia Pagefind fuerte

«He encontrado una página que encaja con lo que buscas. Empezaría por esta:» + resultado principal + excerpt + hasta dos alternativas.

### Varias rutas plausibles

«Puede que te refieras a una de estas dos cosas:» + dos acciones concretas.

### Sin coincidencia clara

«No encuentro una página que responda exactamente a eso. Si buscabas algo dentro de esta web, puedo llevarte a Obras, Cuaderno, Herramientas o Prensa.»

### Consulta externa

«Este asistente solo consulta el contenido de esta web. Si tu pregunta era sobre David, sus libros o recursos para escritores, dime qué necesitas y te llevo a la sección adecuada.»

## 8. Diseño editorial tipo LRB, clean-room

Patrones observables en https://www.lrb.co.uk/ que sí son transferibles como principios:

- jerarquía tipográfica como protagonista;
- densidad informativa alta sin depender de tarjetas;
- títulos + firma + excerpt en flujo vertical;
- reglas finas para separar piezas;
- navegación textual clara;
- contenido que se siente como publicación, no como dashboard.

Aplicación al asistente:

- transcript como columna editorial;
- `Consulta` / `Respuesta` como labels marginales o small caps;
- mensaje del usuario sin globo oscuro;
- fuentes como filas de índice, con título, excerpt y flecha;
- sugerencias como enlaces/acciones rectangulares, no chips;
- composer parecido a una caja de búsqueda editorial, no a WhatsApp;
- máximo de 2–3 destinos por respuesta para no convertirse en sitemap visual;
- widget sobrio y sin pulso perpetuo.

## 9. Qué se implementa en #94 y qué queda fuera

### P0 / #94

- mejor router local y tolerancia conservadora a alias/erratas;
- navegación natural y respuestas de orientación;
- aprovechar excerpts de Pagefind en el fallback;
- fallback estable con hubs canónicos en vez de “no te entendí”;
- catálogo de respuestas y ejemplos;
- mantener diseño editorial ya introducido en V2;
- tests de intents, ambigüedad, typo y off-domain.

### P1 coordinado con #91/#88

- enriquecer metadata Pagefind de territorios/tipo de contenido si las pruebas de relevancia lo justifican;
- evaluar pesos de Pagefind con su Playground, no a ojo;
- consolidar la registry con `content-registry.json` para reducir duplicación de aliases/jobs;
- incorporar snippets/sub-results en navegación avanzada.

### P2 / experimento

- Workers AI remoto en producción solo con feature flag;
- posible AI Search como experimento medido;
- NLP.js únicamente si el catálogo local crece lo suficiente para justificar entrenamiento.

## 10. Criterio de éxito

El asistente está terminado cuando una persona puede escribir frases normales —incluyendo pequeñas erratas— y casi siempre ocurre una de estas tres cosas:

1. recibe una respuesta breve y verificable con enlace;
2. recibe una aclaración concreta de dos opciones;
3. recibe una ruta editorial útil para seguir navegando.

Que “parezca inteligente” es secundario. Lo principal es que reduzca tiempo hasta el contenido correcto, nunca invente y siga funcionando gratis/local cuando la IA remota está apagada.