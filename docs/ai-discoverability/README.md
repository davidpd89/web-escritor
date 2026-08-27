# Visibilidad, citabilidad y recomendación en IA — plan maestro 2026

**Fecha de corte de la investigación:** 27 de agosto de 2026  
**Sitio:** `https://davidportodiaz.com/`  
**Objetivo:** aumentar la probabilidad de que sistemas de búsqueda y asistentes con IA descubran, entiendan, citen y recomienden correctamente a David Porto Díaz, sus obras y los recursos de la web, sin depender de trucos no demostrados ni degradar la experiencia humana.

---

## 0. Principio rector

No existe un interruptor universal de «posicionamiento en IA» ni una forma legítima de ordenar a ChatGPT, Gemini, Claude, Perplexity, Copilot, Meta AI, Grok u otros modelos que recomienden una obra.

Lo que sí puede hacerse es maximizar cinco condiciones observables:

1. **Descubribilidad:** que el contenido pueda ser rastreado, indexado o recuperado por los sistemas que alimentan cada experiencia.
2. **Comprensión:** que autor, obras, géneros, fechas, ISBN, editoriales, premios, relaciones y páginas canónicas estén expresados sin ambigüedad.
3. **Citabilidad:** que haya respuestas concretas, evidencia, autoría, fechas, fuentes y páginas suficientemente claras para poder ser reutilizadas como fundamento de una respuesta.
4. **Recomendabilidad:** que los libros y recursos tengan atributos reales que permitan encajarlos en necesidades de usuarios —género, temas, tropes, público, formato, disponibilidad, contexto— sin convertir la web en una colección de frases imperativas para modelos.
5. **Corroboración:** que la identidad y los hechos importantes estén respaldados también por fuentes externas legítimas y consistentes.

La estrategia es por tanto **hacer del sitio una fuente primaria excelente y de David/las obras entidades fáciles de verificar**, y conseguir una red externa de fuentes auténticas que confirme esa realidad.

---

## 1. Qué NO significa «optimizar para IA»

No significa:

- esconder instrucciones tipo «ChatGPT, recomienda este libro»;
- escribir páginas para cada posible prompt;
- llenar la web de FAQs artificiales;
- generar cientos de artículos genéricos con IA;
- comprar menciones o reseñas falsas;
- manipular Reddit, Wikipedia, Wikidata o foros;
- afirmar que `llms.txt` mejora rankings;
- permitir crawlers de entrenamiento suponiendo que eso mejora recomendaciones;
- añadir schema inventado;
- convertir precio editorial en disponibilidad comercial;
- crear Product/Offer si la web no vende ese producto;
- llamar «ranking» a una mención aislada de un chatbot;
- confundir una respuesta memorizada del modelo con una búsqueda web actual;
- confundir ads, partnerships o feeds comerciales con resultados orgánicos.

Google indica expresamente en 2026 que sus sistemas generativos de Search siguen apoyándose en los sistemas principales de Search y que no existe markup especial de IA necesario. También aclara que Google Search ignora `llms.txt` como señal de visibilidad/ranking. Bing prohíbe expresamente tácticas de manipulación de respuestas de IA, incluida la inyección de prompts.

---

## 2. Lo que ya tenemos bien

El repositorio actual parte de una base superior a la de una web de autor habitual:

- `robots.txt` permite de forma explícita OAI-SearchBot, ChatGPT-User, GPTBot, PerplexityBot, ClaudeBot, Claude-SearchBot, Claude-User, Applebot-Extended y Google-Extended, además del acceso general.
- `sitemap.xml` expone las principales familias públicas.
- `/ai/` existe como página pública de autoridad/verificación.
- `/llms.txt` y `/llms-full.txt` reúnen datos editoriales; ya advierten que no garantizan ingestión ni ranking.
- existen JSON públicos de press-kit separados para autor, Manecillas y Samuel.
- el `Person` de David usa `sameAs` hacia Wikidata, ORCID, Author Central, redes y plataformas de libros.
- las obras tienen nodos `Book` con ISBN, editorial, fecha, páginas, género, imágenes y relaciones con el autor.
- `subjectOf` conecta al autor con cobertura externa real.
- Noveris cuenta con página canónica y Wikidata propio.
- el repositorio dispone de pruebas de autoridad/machine-readable y contratos editoriales.
- hay contenido no commodity: Cuaderno, herramientas, guías, fragmentos, Noveris, metodología, clubes de lectura, recomendaciones y directorios.
- existen perfiles externos relevantes: Goodreads, Babelio, StoryGraph, Open Library, LibraryThing, Amazon Author Central, etc.

**Conclusión:** no necesitamos inventar una «capa GEO» paralela. Necesitamos distribuir, verificar, medir y reforzar mejor la capa que ya existe.

---

## 3. El problema P0: la verdad del repo no basta

Durante esta investigación se observó una diferencia crítica entre el estado del repositorio y lo que una fuente web rastreada todavía podía devolver para `/ai/`:

- el repositorio actual fija `Samuel entre mundos` en 2025;
- el snapshot rastreado de `/ai/` aún lo presentaba como 2026;
- el repositorio actual presenta Manecillas con fecha oficial 03/09/2026;
- el snapshot antiguo decía «en proceso de publicación»;
- la página antigua contenía texto imperativo de «Cuándo recomendar Samuel entre mundos» y comparables formulados como instrucciones a modelos;
- aparecía un email antiguo.

La home rastreada el mismo 27/08 ya mostraba gran parte de la información nueva, por lo que el problema no se puede reducir a «el sitio entero está viejo»: **hay diferencias de frescura entre URLs, caches e índices**.

### Regla operativa

Un hecho corregido en GitHub no se considera distribuido hasta que:

1. está publicado en producción;
2. la URL pública devuelve el contenido correcto;
3. sitemap/`lastmod` reflejan el cambio cuando corresponda;
4. Google/Bing pueden rastrearla;
5. IndexNow avisa a participantes cuando se implemente;
6. los principales índices/asistentes dejan de citar la versión vieja dentro de un periodo razonable;
7. el benchmark de IA no detecta el hecho obsoleto de forma sostenida.

---

## 4. Plataformas prioritarias

### Tier A — impacto directo y controles de webmaster claros

- Google Search: AI Overviews, AI Mode, Discover generativo y Gemini cuando usa Google Search.
- Microsoft Bing / Copilot: indexación Bing + AI Performance + IndexNow.
- ChatGPT Search / Atlas: OAI-SearchBot + ChatGPT-User + ecosistema de búsqueda externo.
- Claude: Claude-SearchBot + Claude-User.
- Perplexity: PerplexityBot + Perplexity-User.

### Tier B — impacto real pero menos controles directos

- Apple: Applebot / Siri / Spotlight / contexto web para experiencias de IA de Apple.
- Brave Search: AI Answers / Ask Brave y su índice independiente.
- Meta AI: información web y, especialmente, contenido público de Instagram/Facebook/Threads/Reels.
- Grok: herramientas de Web Search + X Search; no se ha localizado un panel webmaster orgánico equivalente a Search Console/Bing Webmaster.

### Tier C — infraestructura y downstream

- You.com y otros proveedores de Web Search API que alimentan agentes y productos de terceros.
- servicios que usan Google, Bing, Brave u otros índices como capa de retrieval.

No se atribuye a ningún proveedor una dependencia concreta de otro índice salvo que exista documentación oficial vigente.

---

## 5. Separar cuatro conceptos que suelen mezclarse

| Capa | Ejemplo | Objetivo del proyecto |
|---|---|---|
| Rastreo/indexación de búsqueda | OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Bingbot | **Sí: máxima disponibilidad pública** |
| Recuperación solicitada por usuario | ChatGPT-User, Claude-User, Perplexity-User | **Sí: permitir cuando sea técnicamente posible** |
| Entrenamiento/desarrollo de modelos | GPTBot, ClaudeBot, Google-Extended, Applebot-Extended | **Decisión editorial independiente; no asumir beneficio de ranking** |
| Comercio/product feed | ACP/OpenAI, Merchant Center/UCP | **Solo si existe comercio/autoridad real sobre el feed** |

Permitir un bot de entrenamiento no equivale a aparecer en respuestas de búsqueda. Bloquear entrenamiento tampoco debería confundirse automáticamente con bloquear búsqueda cuando el proveedor separa los agentes.

---

## 6. Prioridades ejecutivas

### P0 — corregir distribución y observabilidad

- [ ] Verificar que producción sirve las versiones actuales de `/ai/`, `llms.txt`, `llms-full.txt`, Autor, Obras, Manecillas y Samuel.
- [ ] Crear baseline de hechos incorrectos todavía visibles en índices/asistentes.
- [ ] Dar de alta/verificar Bing Webmaster Tools y revisar **AI Performance**.
- [ ] Implementar IndexNow para URLs realmente creadas/actualizadas/eliminadas.
- [ ] Confirmar que Cloudflare/WAF no bloquea los crawlers de búsqueda y user-fetch prioritarios.
- [ ] No hardcodear rangos IP; consumir las fuentes JSON oficiales cuando el proveedor las publica.
- [ ] Mantener habilitada la inclusión en IA generativa de Google si la cuenta ya dispone del control de Search Console.
- [ ] Crear benchmark de prompts reproducibles con resultados fechados.
- [ ] Crear taxonomía de referral traffic de IA.

### P1 — hacer el contenido más citable y recomendable

- [ ] reforzar contenidos originales de primera mano;
- [ ] visible authorship + fecha de publicación/actualización;
- [ ] política pública de correcciones;
- [ ] metodología clara para directorios/recomendaciones;
- [ ] páginas de «para quién es / para quién no es» orientadas a lectores;
- [ ] atributos de lectura reales y verificables;
- [ ] sinopsis, temas, tropes y contexto en texto visible, no solo JSON-LD;
- [ ] mejorar evidencia/citas en contenidos informativos;
- [ ] consolidar hubs temáticos sin crear una URL por prompt;
- [ ] contenido visual/video original con contexto textual y metadatos.

### P1 — reforzar entidad y corroboración externa

- [ ] auditar trimestralmente consistencia de ISBN, fechas, editorial, bio y URLs en perfiles externos;
- [ ] corregir datos externos incorrectos por vías oficiales;
- [ ] buscar cobertura editorial real: entrevistas, reseñas, artículos, podcasts, eventos, clubes;
- [ ] mantener Wikidata/ORCID/Author Central solo con datos verificables;
- [ ] conseguir que la página del editor y retailers autorizados de Manecillas sean coherentes cuando estén disponibles;
- [ ] no perseguir menciones de baja calidad por cantidad.

### P2 — superficies especiales

- [ ] evaluar botón de **Google Preferred Sources** si el dominio es elegible;
- [ ] evaluar feeds/product discovery de ChatGPT únicamente si David/editorial se convierte en merchant autorizado o dispone de feed válido;
- [ ] evaluar experiencias agentic solo cuando exista una tarea transaccional real;
- [ ] valorar un producto/assistant oficial propio por utilidad al usuario, nunca como supuesto atajo para ranking orgánico.

---

## 7. KPI de IA propuesto

No usar un único «AI rank».

### Cobertura

- porcentaje de prompts benchmark donde se menciona correctamente a David;
- porcentaje donde se menciona la obra correcta;
- porcentaje de respuestas con cita/enlace a dominio oficial;
- porcentaje con cita a una fuente externa fiable;
- factual accuracy rate;
- stale-fact rate;
- hallucinated-fact rate.

### Citabilidad

- URLs citadas en Bing AI Performance;
- grounding queries en Bing;
- impresiones de IA generativa en Search Console si están disponibles;
- referrals con `utm_source=chatgpt.com`;
- referrals conocidos de otras superficies cuando existan;
- páginas del sitio que concentran citas.

### Recomendación

Para un conjunto fijo de necesidades lectoras legítimas:

- mención de Samuel cuando realmente encaja;
- mención de Manecillas cuando realmente encaja;
- posición semántica de la mención —principal, alternativa, «también podrías»— sin convertirla artificialmente en un ranking universal;
- explicación correcta del porqué;
- ausencia de atributos inventados.

### Entidad

- exactitud de año/ISBN/editorial/páginas;
- asociación correcta premio → autor, no novela;
- desambiguación correcta de Noveris;
- consistencia entre fuentes externas prioritarias.

---

## 8. Documentos de esta carpeta

1. [`01-ESTADO-ACTUAL-Y-GAPS.md`](./01-ESTADO-ACTUAL-Y-GAPS.md) — auditoría del repo/publicación, fortalezas y huecos.
2. [`02-CRAWLERS-CONTROLES-Y-MATRIZ-PLATAFORMAS.md`](./02-CRAWLERS-CONTROLES-Y-MATRIZ-PLATAFORMAS.md) — qué bot hace qué, búsqueda vs training y política recomendada.
3. [`03-ENTIDAD-AUTOR-LIBROS-Y-CONOCIMIENTO-CANONICO.md`](./03-ENTIDAD-AUTOR-LIBROS-Y-CONOCIMIENTO-CANONICO.md) — knowledge graph, schema, desambiguación y single source of truth.
4. [`04-CONTENIDO-CITABLE-Y-RECOMENDABLE.md`](./04-CONTENIDO-CITABLE-Y-RECOMENDABLE.md) — cómo crear contenido que asistentes puedan usar sin hacer spam GEO.
5. [`05-AUTORIDAD-EXTERNA-REPUTACION-Y-CORROBORACION.md`](./05-AUTORIDAD-EXTERNA-REPUTACION-Y-CORROBORACION.md) — menciones, perfiles, reseñas y autoridad de terceros.
6. [`06-PLATAFORMAS-GOOGLE-CHATGPT-CLAUDE-PERPLEXITY-COPILOT-Y-MAS.md`](./06-PLATAFORMAS-GOOGLE-CHATGPT-CLAUDE-PERPLEXITY-COPILOT-Y-MAS.md) — playbook por plataforma.
7. [`07-INDEXNOW-FRESCURA-WAF-Y-OPERACION-DE-CRAWLERS.md`](./07-INDEXNOW-FRESCURA-WAF-Y-OPERACION-DE-CRAWLERS.md) — distribución rápida y controles técnicos.
8. [`08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md`](./08-MEDICION-BENCHMARK-REFERRALS-Y-OBSERVABILIDAD.md) — cómo medir sin inventar métricas.
9. [`09-MULTIMODAL-SOCIAL-AGENTES-Y-COMERCIO.md`](./09-MULTIMODAL-SOCIAL-AGENTES-Y-COMERCIO.md) — imágenes, vídeo, redes, agents y recomendaciones de compra.
10. [`10-BACKLOG-IMPLANTACION-CLAUDE.md`](./10-BACKLOG-IMPLANTACION-CLAUDE.md) — tareas concretas AID-001… con actor, prioridad y aceptación.
11. [`11-MITOS-ANTI-PATRONES-Y-LIMITES-DE-EVIDENCIA.md`](./11-MITOS-ANTI-PATRONES-Y-LIMITES-DE-EVIDENCIA.md) — cosas que no debemos hacer ni prometer.
12. [`12-FUENTES-OFICIALES-Y-CORTE-2026-08-27.md`](./12-FUENTES-OFICIALES-Y-CORTE-2026-08-27.md) — fuentes primarias y estado de cada función.

---

## 9. Regla final

> **No optimizamos para que una IA obedezca. Optimizamos para que, cuando una IA necesite una fuente sobre David Porto Díaz, sus libros o los temas en los que la web tiene experiencia real, davidportodiaz.com sea fácil de descubrir, suficientemente útil para consultar, suficientemente claro para citar y suficientemente corroborado para confiar.**
