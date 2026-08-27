# 12 — Fuentes oficiales y corte 2026-08-27

**Fecha de investigación:** 27 de agosto de 2026.  
**Objetivo:** que cualquier recomendación de esta iniciativa pueda rastrearse hasta documentación primaria, y que cambios futuros de proveedor se detecten sin depender de blogs SEO de terceros.

---

## 1. Estados usados

- `GA / DOCUMENTED`: función o política documentada de forma general.
- `PREVIEW`: disponible como preview/beta y puede cambiar.
- `ROLLOUT`: desplegándose; no asumir disponibilidad en todas las cuentas/países.
- `CONDITIONAL`: solo aplica si existe una condición —merchant, app, vídeo, etc.—.
- `MONITOR`: proveedor/capacidad relevante pero sin control webmaster suficiente localizado.
- `NO SPECIAL SIGNAL`: proveedor documenta que una táctica no es una señal especial.

---

# 2. Google Search / Gemini

## G-AI-01 — Optimizing for generative AI features on Google Search

**URL:**  
https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

**Estado:** GA / DOCUMENTED  
**Revisada:** actualización visible julio 2026.

**Sustenta:**

- SEO sigue siendo base de AI Overviews/AI Mode;
- core ranking + RAG + query fan-out;
- contenido único/non-commodity;
- crawlability/indexability;
- semantic HTML/JS/page experience;
- imágenes/vídeo;
- evitar página por fan-out query;
- `llms.txt` no ayuda ni perjudica Google Search;
- no chunking obligatorio;
- no reescritura específica «para AI»;
- no menciones inauténticas;
- no schema especial AI;
- agentes/browser accessibility.

**Autoridad:** principal para claims GEO/AEO de Google.

---

## G-AI-02 — Search Central announcement of 2026 AI guide

**URL:**  
https://developers.google.com/search/blog/2026/05/a-new-resource-for-optimizing

**Estado:** DOCUMENTED  
**Fecha:** 2026-05-15.

**Sustenta:** Google presenta oficialmente la nueva guía y reafirma SEO + contenido único + mythbusting + agentic experiences.

---

## G-AI-03 — Search documentation updates

**URL:**  
https://developers.google.com/search/updates

**Estado:** DOCUMENTED / CHANGELOG.

**Uso:** revisar trimestralmente cambios en:

- AI guide;
- Preferred Sources;
- structured data;
- generative AI reports;
- agentic guidance.

---

## G-AI-04 — Preferred Sources

**URL:**  
https://developers.google.com/search/docs/appearance/preferred-sources

**Estado:** ROLLOUT / DOCUMENTED  
**Actualización observada:** 2026-08-20.

**Sustenta:**

- usuarios pueden seleccionar fuentes preferidas;
- impacto en experiencias compatibles;
- deeplink `https://www.google.com/preferences/source?q=example.com`;
- custom/preferred source button documentado en agosto 2026.

**Aplicación:** evaluar CTA discreto en Cuaderno si el dominio es elegible.

---

## G-AI-05 — Generative AI performance reports in Search Console

**URL de anuncio:**  
https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports

**Estado:** ROLLOUT / DOCUMENTED  
**Anuncio:** junio 2026.

**Sustenta:** medición específica de AI Overviews/AI Mode según disponibilidad.

**Implementación:** autoridad principal en PR #110 Search Console.

---

## G-AI-06 — Search generative AI control

**URL de ayuda:**  
https://support.google.com/webmasters/answer/16984139

**Estado:** ROLLOUT.

**Sustenta:** control de inclusión en funciones generativas de Search/Discover cuando disponible.

**Decisión actual:** Include mientras objetivo = máxima visibilidad.

---

## G-AI-07 — Gemini Apps: sources / Google Search

**URL:**  
https://support.google.com/gemini/answer/15719111

**Estado:** DOCUMENTED.

**Sustenta:** Gemini puede usar información pública procedente de Google Search y mostrar fuentes según experiencia.

---

## G-AI-08 — Gemini Deep Research

**URL:**  
https://support.google.com/gemini/answer/13695044

**Estado:** DOCUMENTED.

**Sustenta:** Google Search forma parte de las fuentes disponibles/por defecto en Deep Research según configuración/producto.

**Implicación:** no existe una segunda estrategia webmaster separada de Search para esta capa.

---

# 3. OpenAI / ChatGPT

## OAI-01 — Publishers and Developers FAQ / Search discovery

**URL:**  
https://help.openai.com/en/articles/12627856

**Estado:** DOCUMENTED.

**Sustenta:**

- websites públicas pueden aparecer en ChatGPT Search;
- OAI-SearchBot controla descubrimiento para Search;
- bloqueo puede impedir inclusión de contenido/snippets;
- referral links con `utm_source=chatgpt.com`;
- GPTBot es control separado para training/model improvement.

---

## OAI-02 — ChatGPT Search

**URL:**  
https://help.openai.com/en/articles/9237897-chatgpt-search

**Estado:** DOCUMENTED.

**Sustenta:**

- Search usa web y fuentes;
- factores de relevancia/fiabilidad;
- no existe garantía de placement;
- puede usar partners/proveedores externos y reformular consultas.

**Límite:** no atribuir una respuesta individual a un search partner concreto sin evidencia.

---

## OAI-03 — OAI-SearchBot IP feed

**URL:**  
https://openai.com/searchbot.json

**Estado:** LIVE MACHINE-READABLE.

**Sustenta:** rangos oficiales dinámicos para OAI-SearchBot.

**Implementación:** WAF/reporting debe consumir fuente, no hardcodear permanentemente.

---

## OAI-04 — GPTBot IP feed

**URL:**  
https://openai.com/gptbot.json

**Estado:** LIVE MACHINE-READABLE.

**Uso:** verificación operacional del bot de training, no factor de ranking.

---

## OAI-05 — Product discovery / Agentic Commerce Protocol

**URL:**  
https://openai.com/index/powering-product-discovery-in-chatgpt/

**Estado:** DOCUMENTED / 2026.

**Sustenta:** merchants pueden aportar datos estructurados de producto mediante ACP; product discovery puede combinar feeds/fuentes.

**Aplicación actual:** DEFER para davidportodiaz.com salvo merchant/feed autorizado real.

---

## OAI-06 — Shopping with ChatGPT Search

**URL:**  
https://help.openai.com/en/articles/11128490

**Estado:** DOCUMENTED.

**Sustenta:** información de productos puede proceder de terceros/direct merchants; criterios relacionados con producto/merchant y disponibilidad.

---

## OAI-07 — Shopping research

**URL:**  
https://help.openai.com/en/articles/12911370-using-shopping-research-in-chatgpt

**Estado:** DOCUMENTED.

**Uso:** comprender que recomendaciones de compra combinan web/product sources y no dependen únicamente del sitio del autor.

---

## OAI-08 — Buy it in ChatGPT / Instant Checkout

**URL:**  
https://openai.com/index/buy-it-in-chatgpt/

**Estado:** CONDITIONAL / commerce.

**Aplicación:** no implementar sin venta directa/merchant readiness.

---

## OAI-09 — Product feed for Ads

**Estado:** ADVERTISING BETA / SEPARATE FROM ORGANIC.

**Fuente:** documentación oficial de OpenAI Ads/Product Feed consultada en investigación 2026.

**Regla registrada:** participar en product feed de ads no debe presentarse como mecanismo para entrar en respuestas orgánicas.

**Mantenimiento:** si se activa Ads en España/cuenta, volver a verificar URL/copy oficial vigente antes de cualquier decisión comercial.

---

# 4. Anthropic / Claude

## ANT-01 — Web crawling and robots

**URL:**  
https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

**Estado:** DOCUMENTED.

**Sustenta:** separación entre:

- ClaudeBot;
- Claude-SearchBot;
- Claude-User;

robots y efectos funcionales de bloqueo.

---

## ANT-02 — Bot IP machine-readable feed

**URL:**  
https://claude.com/crawling/bots.json

**Estado:** LIVE MACHINE-READABLE  
**creationTime observado:** agosto 2026.

**Sustenta:** prefijos IP operacionales publicados actualmente por Anthropic.

**Nota:** documentación textual histórica que decía que no se publicaban rangos puede ir por detrás. Para automatización operacional, comprobar siempre el feed oficial vigente y registrar discrepancia.

---

# 5. Perplexity

## PPLX-01 — Perplexity crawlers

**URL:**  
https://docs.perplexity.ai/docs/resources/perplexity-crawlers

**Estado:** DOCUMENTED.

**Sustenta:**

- PerplexityBot = search indexing/surfacing, no foundation-model training;
- Perplexity-User = user-initiated fetch;
- IP feeds;
- WAF allowlisting.

---

## PPLX-02 — robots.txt policy

**URL:**  
https://www.perplexity.ai/help-center/en/articles/10354969-how-does-perplexity-follow-robots-txt

**Estado:** DOCUMENTED  
**Actualización observada:** 2026-07-16.

**Sustenta:** PerplexityBot respeta robots y se retiró la antigua capacidad de resumir directamente URLs bloqueadas para reducir abuso.

---

## PPLX-03 — PerplexityBot IPs

**URL:**  
https://www.perplexity.com/perplexitybot.json

**Estado:** LIVE MACHINE-READABLE.

---

## PPLX-04 — Perplexity-User IPs

**URL:**  
https://www.perplexity.com/perplexity-user.json

**Estado:** LIVE MACHINE-READABLE.

---

## PPLX-05 — Source Labels

**URL:**  
https://www.perplexity.ai/help-center/en/articles/20260806-understanding-source-labels

**Estado:** DOCUMENTED  
**Actualización:** agosto 2026.

**Sustenta:**

- Government / Academic / Trusted;
- revisión a nivel de dominio;
- criterios como correcciones, autoría, separación de publicidad/opinión/información y expertise;
- ausencia de label no implica baja calidad;
- partnerships/pagos no determinan label.

**Aplicación:** trust hygiene, no «badge chasing».

---

# 6. Microsoft Bing / Copilot

## BING-01 — AI Performance in Bing Webmaster Tools

**URL:**  
https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview

**Estado:** PUBLIC PREVIEW  
**Fecha:** 2026-02-10.

**Sustenta:**

- citas en Microsoft Copilot;
- AI-generated summaries de Bing;
- select partner integrations;
- Total Citations;
- Average Cited Pages;
- cited URLs;
- grounding queries;
- tendencias.

**Límite:** citation no equivale a ranking/authority/placement.

---

## BING-02 — Bing Webmaster Guidelines

**URL:**  
https://www.bing.com/webmasters/help/bing-webmaster-guidelines-30fba23a

**Estado:** DOCUMENTED / current.

**Sustenta anti-patrones 2026:**

- scraped/republished content sin valor;
- artificial language/keyword stuffing para rankings o AI citations;
- contenido generado automáticamente a escala sin control;
- affiliate thin content;
- misleading structured data;
- **prompt injection and AI manipulation**;
- posible reducción de ranking/grounding visibility o delisting.

Esta fuente es especialmente importante para impedir «hidden prompts» dirigidos a Copilot/LLMs.

---

## BING-03 — `data-nosnippet`

**Estado:** DOCUMENTED por Bing para control selectivo de snippets/AI answers.

**Uso:** CONDITIONAL. No aplicar globalmente; reservar para secciones que deban seguir indexables pero no reutilizarse en snippets/generative answers.

**Mantenimiento:** verificar la documentación vigente antes de implementar un caso real.

---

# 7. IndexNow

## INX-01 — Protocol documentation

**URL:**  
https://www.indexnow.org/documentation

**Estado:** GA / DOCUMENTED.

**Sustenta:**

- endpoint/protocolo;
- URL submission;
- key ownership;
- batch;
- status codes.

---

## INX-02 — FAQ

**URL:**  
https://www.indexnow.org/faq

**Estado:** DOCUMENTED.

**Sustenta:** engines participantes comparten notificaciones y IndexNow es aviso de cambio, no garantía de indexación/ranking.

---

## INX-03 — Endpoint

**URL:**  
https://api.indexnow.org/indexnow

**Estado:** LIVE ENDPOINT.

**Regla:** usar tras deployment, con URLs cambiadas reales.

---

# 8. Apple

## APPLE-01 — About Applebot

**URL:**  
https://support.apple.com/es-es/119829

**Estado:** DOCUMENTED.

**Sustenta:**

- Applebot sirve Search/Spotlight/Siri/Safari;
- crawled data puede aportar contexto actualizado para contenido generado por modelos de IA en productos/servicios Apple;
- Applebot-Extended controla uso para entrenamiento de modelos generales;
- bloquear Applebot-Extended no bloquea Search;
- `isAccessibleForFree:false` y contexto AI.

---

# 9. Brave Search

## BRAVE-01 — AI / Answers help

**URL:**  
https://search.brave.com/help/ai

**Estado:** DOCUMENTED.

**Sustenta:** AI Answers/Ask Brave y citas/fuentes del índice Brave.

---

## BRAVE-02 — Brave Search crawler

**URL:**  
https://search.brave.com/help/brave-search-crawler

**Estado:** DOCUMENTED.

**Sustenta:** crawler no utiliza un user-agent diferenciado; crawlability se relaciona con la política de Googlebot.

**Regla:** no inventar `BraveBot`.

---

# 10. Meta AI / Meta social recommendation

## META-01 — More international news/content to Meta AI

**URL:**  
https://about.fb.com/news/2026/03/bringing-more-international-news-and-content-to-meta-ai/

**Estado:** DOCUMENTED / partnerships.

**Sustenta:** expansión de contenido web/news real-time y enlaces de salida en Meta AI.

**Límite:** no implica un programa público universal de publisher submission para davidportodiaz.com.

---

## META-02 — 2026 AI drives performance / original content

**URL:**  
https://about.fb.com/news/2026/01/2026-ai-drives-performance/

**Estado:** DOCUMENTED.

**Sustenta:** evolución de recommendation systems y énfasis creciente en contenido original en Instagram/Meta surfaces.

**Aplicación:** original social content, no repost farm.

---

# 11. xAI / Grok

## XAI-01 — Web Search tool

**URL:**  
https://docs.x.ai/developers/tools/web-search

**Estado:** DOCUMENTED.

**Sustenta:** Grok/xAI puede recuperar web mediante Web Search y devolver citations.

---

## XAI-02 — X Search

**URL:**  
https://docs.x.ai/developers/tools/x-search

**Estado:** DOCUMENTED.

**Sustenta:** retrieval de contenido de X.

---

## XAI-03 — Tools overview

**URL:**  
https://docs.x.ai/developers/tools/overview

**Estado:** DOCUMENTED.

**Límite:** esta investigación no localizó una guía webmaster pública de crawler/robots ni panel de submit orgánico específico. Mantener `MONITOR`.

---

# 12. Search APIs downstream

## YOU-01 — You.com / Web Search APIs

**Estado:** MONITOR.

Se confirmó durante investigación la existencia de Search APIs orientadas a LLM/agents, pero no se localizó un control webmaster que justifique configuración específica del sitio.

**Regla:** no crear trabajo técnico separado hasta que exista una señal/control oficial relevante.

---

# 13. Superficies internas del proyecto usadas como evidencia

## REPO-01 — `robots.txt`

**Estado:** ya permite crawlers prioritarios y training tokens descritos en README.

## REPO-02 — `llms.txt`

**Estado:** máquina-friendly, no ranking guarantee.

## REPO-03 — `llms-full.txt`

**Estado:** actualizado tras PR #109; revisar wording operativo residual.

## REPO-04 — `/ai/`

**Estado repo:** nueva página factual.

**Observación externa:** una vista rastreada recuperada el 27/08 aún conservaba una versión antigua. Tratar como evidencia de stale distribution, no prueba concluyente del HTML de origen actual.

## REPO-05 — Home JSON-LD

**Estado:** Person/Book/WebSite con sameAs/subjectOf y facts fuertes.

## REPO-06 — Press-kit JSON

**Estado:** autor + obras, superficie pública machine-readable.

## REPO-07 — `editorial-facts` / tests

**Estado:** autoridad interna y QA; no debe hacerse pública solo por AI discoverability.

---

# 14. Fuentes secundarias

Esta iniciativa puede consultar estudios, papers o herramientas externas para generar hipótesis, pero:

- no sustituyen documentación del proveedor para explicar controles de crawler/ranking;
- no se convierten en «factores confirmados»;
- deben marcarse `INFERENCE` o `OBSERVED`;
- no se usan para prometer resultados.

---

# 15. Revisión trimestral obligatoria

Buscar cambios en:

### Google

- AI guide;
- Search Console GenAI;
- Preferred Sources;
- agentic guidance/UCP.

### OpenAI

- Search bot docs;
- IP ranges;
- shopping/ACP;
- apps/agent browsing;
- referral behavior.

### Anthropic

- crawler UAs;
- bots.json;
- search behavior.

### Perplexity

- crawler docs;
- user-fetch policy;
- Source Labels;
- IP feeds.

### Bing

- AI Performance;
- webmaster guidelines;
- IndexNow;
- `data-nosnippet`/AI controls.

### Apple / Brave / Meta / xAI

- crawler/search/AI product changes;
- nuevos webmaster controls.

---

# 16. Política de actualización de esta carpeta

Cuando cambie una fuente:

1. actualizar URL/estado;
2. registrar fecha;
3. identificar docs afectados;
4. modificar backlog si cambia acción;
5. no reescribir historia silenciosamente si el cambio invalida una decisión material;
6. crear nota de migración cuando un bot/control sea retirado.

---

# 17. Criterio de autoridad

Orden de confianza para afirmaciones sobre una plataforma:

1. documentación oficial actual del producto;
2. changelog/blog oficial fechado;
3. endpoint machine-readable oficial;
4. observación reproducible propia;
5. investigación de terceros;
6. opinión SEO/comunidad.

Si 1–3 contradicen 5–6, esta documentación debe seguir 1–3 salvo evidencia de bug explícita.

---

# 18. Límite final

Ninguna de estas fuentes promete:

- que David será recomendado;
- que un libro aparecerá primero;
- que todos los modelos tendrán el dato al mismo tiempo;
- que una cita se mantendrá estable;
- que training produce organic search placement.

La documentación sí permite construir un sistema serio para maximizar **accesibilidad, frescura, comprensión, verificabilidad, citabilidad y encaje real de recomendación**.