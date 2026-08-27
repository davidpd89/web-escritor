# 06 — Playbook por plataforma de IA

**Corte:** 27/08/2026.  
**Fuentes:** documentación oficial de cada proveedor cuando existe. Si un proveedor no publica controles webmaster, se marca como `OBSERVE`, no se inventan señales.

---

# 1. Google Search: AI Overviews y AI Mode

## Cómo obtiene fuentes

Google describe sus experiencias generativas como construidas sobre sus sistemas principales de ranking/calidad de Search, usando técnicas como:

- retrieval-augmented generation;
- query fan-out;
- recuperación desde el índice de Search.

## Qué sí hacer

- SEO técnico normal;
- indexabilidad;
- snippet eligibility;
- contenido original/non-commodity;
- texto claro;
- imágenes/vídeo relevantes;
- páginas rápidas/usables;
- canonicalización;
- structured data normal cuando corresponde;
- Search Console;
- mantener `Include` en generative AI control si la función aparece.

## Qué no hacer

- `llms.txt` esperando ranking Google;
- AI-specific markup;
- chunking artificial;
- página por fan-out query;
- copy reescrito «para LLM»;
- menciones falsas;
- schema excesivo.

## Oportunidad del proyecto

La web ya tiene muy buena estructura. El mayor upside es contenido first-hand:

- Noveris;
- publicación;
- Manecillas;
- herramientas/metodología;
- crónicas y experiencias.

## Medición

Search Console Generative AI Performance, cuando esté habilitado.

---

# 2. Google Preferred Sources

## Estado 2026

Google permite a usuarios seleccionar dominios como preferred source.

Disponibilidad:

- Top Stories globalmente en idiomas de Search;
- rollout también en AI Mode y AI Overviews;
- desde 20/08/2026 existe un botón interactivo personalizado/documentado.

## Valor para este proyecto

Potencialmente útil para lectores recurrentes del Cuaderno, no como táctica para usuarios que todavía no conocen la web.

## Acción

1. comprobar que `davidportodiaz.com` aparece/puede seleccionarse;
2. evaluar un CTA discreto dentro del Cuaderno, no en toda la web;
3. usar deeplink oficial o botón recomendado;
4. medir uso solo si es posible sin tracking invasivo;
5. no presentarlo como «sube nuestro ranking global».

## Copy propuesto

> Si lees habitualmente el Cuaderno, puedes marcar davidportodiaz.com como fuente preferida en Google.

No usar urgencia o claims de algoritmo.

---

# 3. Gemini

## Fuente web

Gemini Apps puede utilizar información pública de Google Search; Deep Research incluye Search por defecto.

## Estrategia

Todo el trabajo de Google Search beneficia esta ruta de retrieval.

### No crear

- un sitemap Gemini;
- una API «submit to Gemini» inexistente;
- páginas especiales solo para Gemini.

### Benchmark

Incluir Gemini/Deep Research en la batería mensual porque el formato de respuesta/citas puede diferir de Search AI.

---

# 4. ChatGPT Search

## Elegibilidad

OpenAI dice que cualquier web pública puede aparecer.

Para facilitar que el contenido se descubra/cite:

- permitir OAI-SearchBot;
- permitir infraestructura/CDN al rango oficial;
- mantener la página indexable;
- ofrecer contenido útil/relevante.

## Ranking

OpenAI afirma que usa múltiples factores para relevancia y fiabilidad y que no existe garantía de posición.

## Referral analytics

Los enlaces de Search incluyen automáticamente:

`utm_source=chatgpt.com`

### Acción

Crear segmento analítico específico.

## Terceros

OpenAI indica que Search puede colaborar con otros proveedores de búsqueda y reformular queries.

### Implicación

No depender solo de OAI-SearchBot. Mantener buena indexación en ecosistemas Search más amplios.

### Importante

No afirmar qué proveedor concreto usa ChatGPT en una consulta determinada si OpenAI no lo publica.

---

# 5. ChatGPT Atlas / agentes

OpenAI documenta que la compatibilidad de webs con agentes se beneficia de:

- HTML/DOM comprensible;
- roles/ARIA;
- estados accesibles;
- controles accionables.

## Tareas del sitio que deberían poder entenderse

- encontrar libro;
- encontrar retailer;
- abrir fragmento;
- localizar press kit;
- localizar contacto;
- encontrar evento;
- suscribirse;
- abrir una herramienta.

## Regla

No introducir IDs/atributos «para ChatGPT» si una solución accesible estándar resuelve el problema.

---

# 6. ChatGPT Shopping / product discovery

## Estado 2026

ChatGPT usa:

- datos de producto de merchants vía Agentic Commerce Protocol;
- información pública;
- otras fuentes comerciales;
- datos de terceros.

Puede considerar para merchants:

- disponibilidad;
- precio;
- calidad;
- vendedor principal.

## Libros

Un libro puede aparecer como producto aunque davidportodiaz.com no sea merchant, mediante retailers/fuentes externas.

## Qué hacer ahora

Samuel:

- ISBN correcto;
- título/autor/editorial consistentes;
- retailer URLs reales;
- imagen oficial;
- reseñas genuinas externas.

Manecillas:

- esperar retailer verificado;
- mantener ISBN/editorial/fecha;
- sincronizar fichas una vez publicadas.

## ACP directo

`DEFER`.

Solo evaluar si:

- David vende directamente;
- o la editorial/merchant autoriza formalmente un feed;
- hay inventario/precio/checkout que el integrador controla.

## Ads

Los feeds del gestor de anuncios son una superficie pagada distinta y en la beta documentada no convierten los productos en recomendaciones orgánicas de conversaciones. No confundir ads con organic discovery.

---

# 7. Claude Search

## Claude-SearchBot

Debe permanecer permitido.

## Claude-User

Debe permanecer permitido.

## ClaudeBot

Training separado.

## Estrategia de contenido

No existe documentación oficial de «optimización Claude» más específica que:

- permitir retrieval;
- contenido accesible;
- páginas fiables;
- información clara.

No inventar `claude.txt`.

## Medición

Benchmark manual/API cuando exista búsqueda web habilitada en el producto usado para medir.

---

# 8. Perplexity

## Retrieval

PerplexityBot:

- search indexing;
- no foundation model pretraining;
- respeta robots.

Perplexity-User:

- fetch de usuario;
- IP publicada;
- generalmente ignora robots por naturaleza de petición directa según docs técnicas.

## Ventaja potencial del sitio

Perplexity da mucha visibilidad a citas. Una web con:

- fuentes;
- autoría;
- metodología;
- fechas;
- correcciones;

es más fácil de justificar como fuente.

## Source labels 2026

Perplexity revisa ciertos dominios y puede asignar:

- Government;
- Academic;
- Trusted.

Criterios publicados incluyen:

- corregir errores;
- identificar al autor;
- separar publicidad/opinión/información;
- publicar dentro de ámbito de experiencia.

### Acción

Fortalecer esas prácticas por valor editorial, no «para conseguir badge».

### Si creemos que hay un problema de etiqueta

Perplexity indica `support@perplexity.ai` para propietarios.

No escribir pidiendo un badge sin evidencia/razón.

---

# 9. Microsoft Copilot / Bing generative answers

## AI Performance

Desde febrero 2026 Bing Webmaster Tools ofrece preview que mide:

- Total Citations;
- Average Cited Pages;
- cited URLs;
- grounding queries;
- trends.

Microsoft recalca:

- citas ≠ ranking;
- cita ≠ autoridad universal;
- datos pueden ser sampleados/agregados.

## Acción P0

Configurar/abrir Bing Webmaster Tools y capturar baseline.

## Optimización recomendada por Microsoft

- profundidad/expertise;
- estructura clara;
- evidencia;
- frescura;
- reducción de ambigüedad entre formatos.

## IndexNow

Implementar.

## Seguridad contra GEO spam

Bing Webmaster Guidelines considera problemático:

- contenido escalado;
- texto artificial para AI;
- scraped content;
- structured data engañoso;
- prompt injection destinada a manipular sistemas generativos.

No crear hidden prompts.

---

# 10. Apple / Siri / Spotlight

## Applebot

Permitir para discovery.

## Applebot-Extended

Training control independiente.

## Opportunity

Mantener:

- author/book facts indexables;
- imágenes;
- páginas rápidas;
- mobile;
- enlaces externos;
- noindex correcto.

No hay una «Apple AI Console» general equivalente a Bing AI Performance.

---

# 11. Brave AI Answers / Ask Brave

## Índice

Brave mantiene índice propio.

## Crawler

No UA diferenciado; si no es crawlable por Googlebot, no lo rastrea.

## Respuestas

- AI Answers cita fuentes;
- Ask Brave cita fuentes;
- Featured Snippets puede extraer una fuente particularmente buena.

## Acción

- comprobar presencia periódicamente;
- no crear robots especial;
- mantener contenido extractable y original.

---

# 12. Meta AI

## Web

Meta amplía contenido real-time mediante partnerships con medios.

No se ha localizado una vía pública general para que una web de autor se adhiera como partner editorial.

## Social

El activo práctico está en contenido público de:

- Instagram;
- Facebook;
- Threads;
- Reels.

Meta comunica que sus sistemas de recomendación priorizan crecientemente contenido original.

## Acción

- originales, no repost farms;
- libro/autor en lenguaje natural;
- enlaces canónicos;
- vídeo con subtítulos;
- interacción real;
- no hashtag stuffing.

---

# 13. Grok / xAI

## Herramientas oficiales

xAI ofrece Web Search y X Search con citas en API/productos.

## Sin webmaster console localizado

No hay evidencia en esta investigación de un submit/crawler control público específico que debamos implementar.

## Estrategia

- buena presencia en web indexable;
- si existe X oficial en el futuro, contenido público consistente;
- benchmark;
- monitorizar documentación.

No crear cuenta X solo por Grok si no hay estrategia real de canal.

---

# 14. You.com / Search APIs de terceros

## Rol

Search APIs pueden convertirse en upstream de numerosos agentes.

## Acción

No hay trabajo especial demostrado aparte de:

- indexación abierta;
- contenido citable;
- autoridad;
- frescura.

## Medición

Añadir a benchmark si el producto tiene relevancia real/audiencia.

---

# 15. Mistral Le Chat / otros

Si no existe guía de webmaster oficial verificable:

- `OBSERVE`;
- probar factual accuracy;
- registrar fuentes cuando las muestre;
- no inventar bots;
- no crear archivos especiales.

---

# 16. Deep Research surfaces

Incluir en benchmark, separadas de búsqueda rápida:

- ChatGPT Deep Research/research workflows si usan web;
- Gemini Deep Research;
- Perplexity Research;
- otras superficies equivalentes.

### Por qué

Pueden seleccionar un conjunto más amplio de fuentes y producir citas distintas a una respuesta rápida.

### No comparar como si fueran el mismo producto

Registrar `surface` y `model`.

---

# 17. Local/recommendation queries

David puede aparecer en contextos locales legítimos:

- escritor gallego;
- escritor de Pontevedra;
- autor residente en Madrid;
- Feria del Libro de Madrid;
- firmas/eventos.

### Regla

No crear Google Business Profile falso como si la web fuera una librería/local abierto al público.

Usar hechos locales en páginas del autor/eventos y cobertura real.

---

# 18. Recommendation query families

### Samuel

- fantasía juvenil española;
- fantasía de portales en español;
- magia con coste;
- mundo dimensional;
- romance no central;
- aventura juvenil;
- libro para club de lectura de fantasía.

### Manecillas

- novela coral española;
- ficción especulativa sobre memoria;
- narrativa familiar;
- novelas sobre objetos heredados;
- historias conectadas por un objeto;
- lectura para clubes si la guía existe.

### David/web

- herramientas gratuitas para escritores;
- directorio de editoriales;
- convocatorias;
- recursos de worldbuilding;
- autor español de fantasía juvenil.

No forzar presencia donde el encaje no es real.

---

# 19. No confundir modelo y search layer

Perplexity puede usar distintos modelos para sintetizar pero su Search layer determina fuentes. Gemini puede usar Search. Grok tiene Web/X tools. ChatGPT puede usar proveedores externos.

### Por tanto

«GPT me recomienda» no siempre significa «GPT aprendió mi web en training».

Puede significar:

- retrieval actual;
- índice externo;
- memoria paramétrica;
- producto/comercio;
- contexto del usuario;
- combinación.

La optimización debe concentrarse en las capas que podemos observar y controlar.

---

# 20. Estado recomendado

| Plataforma | Prioridad | Acción inmediata |
|---|---:|---|
| Google AI Search | P0 | Search Console + contenido + recrawl |
| Gemini | P1 | heredar Google + benchmark |
| ChatGPT Search | P0 | crawler/WAF + referral + benchmark |
| Claude Search | P0 | crawler/WAF + benchmark |
| Perplexity | P0 | crawler/WAF + trust hygiene + benchmark |
| Bing/Copilot | P0 | AI Performance + IndexNow |
| Apple | P1 | mantener Applebot + benchmark eventual |
| Brave | P1 | verificar indexación/citas |
| Meta AI | P1 | social original + monitor |
| Grok | P2 | monitor + X solo si canal real |
| You/downstream | P2 | monitor |
| emergentes | P3 | revisar trimestralmente |
