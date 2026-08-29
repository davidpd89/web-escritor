# B.2 · Política diferenciada de crawlers de IA en `robots.txt`

Fecha de reconstrucción: 2026-08-29  
Idea original: distinguir crawlers de búsqueda/citación, uso por usuario y entrenamiento en vez de un genérico «IA sí/no».  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `ALREADY_COVERED`.

## Veredicto reconciliado

**ALREADY_COVERED. MANTENER POLÍTICA DELIBERADA POR BOT Y REVISAR CAMBIOS OFICIALES.**

La idea original era correcta como modelo mental, pero #135 comprobó que el `robots.txt` real ya separaba las principales categorías y proveedores. La PR no debe reescribirlo por checklist: debe preservar la investigación, el propósito de cada token y el contrato de mantenimiento.

## 1. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` propuso separar:

- crawlers de entrenamiento/model development;
- crawlers de búsqueda/citación;
- fetches iniciados por usuarios;
- tokens de control de producto como Google-Extended.

Ejemplos citados: GPTBot vs OAI-SearchBot, ClaudeBot vs Claude-SearchBot y otras variantes.

## 2. Evolución en #135

### Revisión exhaustiva → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` inspeccionó el `robots.txt` real y encontró grupos explícitos para:

- OAI-SearchBot;
- ChatGPT-User;
- GPTBot;
- PerplexityBot;
- ClaudeBot;
- Claude-SearchBot;
- Claude-User;
- Google-Extended;
- Applebot-Extended.

Conclusión: no crear otra política; vigilar documentación oficial.

### Matriz final → `YA_CUBIERTO`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` reafirmó que ya existe separación entre Search/User/Training y que el trabajo pendiente es **mantenerla deliberadamente**.

### Autoridad final → `ALREADY_COVERED`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó el mismo estado.

### Revalidación independiente

La revisión independiente mantuvo B.1–B.9 y volvió a recomendar basarse en documentación primaria de proveedor, no blogs de GEO.

## 3. Estado real de `main` en 2026-08-29

`robots.txt` actual contiene:

```text
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: Google-Extended
Allow: /
```

Además mantiene `User-agent: *`, sitemap canónico y comentarios que explican que `llms.txt`/`llms-full.txt` son URLs ordinarias, no directivas robots.

## 4. Fuentes primarias revalidadas

### OpenAI

OpenAI Publishers and Developers FAQ (actualizada en agosto de 2026):

https://help.openai.com/en/articles/12627856-publishers-and-developers-faq

Principios:

- OAI-SearchBot es relevante para descubrimiento/summaries/snippets de ChatGPT Search;
- GPTBot es el control de posible model training;
- bloquear SearchBot y bloquear GPTBot son decisiones distintas;
- `noindex` es la señal para evitar que una página se muestre, pero el crawler debe poder leerla.

### Anthropic

Anthropic Help Center:

https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

Anthropic distingue bots para model development, web search y recuperación a petición del usuario. La política debe seguir esos tokens oficiales y no depender de IPs observadas informalmente.

### Google

Google Crawlers / Google-Extended:

https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers

`Google-Extended` es un **product token**, no un crawler HTTP independiente. Controla ciertos usos para Gemini/Vertex y no afecta inclusión/ranking en Google Search.

### Robots general

https://developers.google.com/search/docs/crawling-indexing/robots/intro

`robots.txt` gestiona crawling; no es un mecanismo fiable por sí solo para impedir indexación de una URL conocida.

## 5. Distinciones que deben conservarse

### Search / citation crawler

Objetivo: permitir que el proveedor recupere contenido público para resultados/respuestas cuando esa es la política elegida.

### User fetch

Acceso solicitado por un usuario concreto. Puede tener token distinto y semántica diferente.

### Training / model development

Control independiente. Permitir búsqueda no obliga a permitir entrenamiento y viceversa cuando el proveedor ofrece tokens separados.

### Product token

Ejemplo Google-Extended: no debe describirse como «bot de Google Search» ni inferir impacto de ranking.

## 6. La política actual es permisiva, no irreversible

#135 no estableció que todos los bots deban permitirse eternamente. Estableció que la decisión debe ser explícita y basada en producto/objetivo.

Si se cambia un `Allow` a `Disallow` en el futuro, registrar:

- proveedor;
- token exacto;
- propósito documentado;
- motivo de negocio/privacidad;
- efecto esperado;
- fecha/fuente;
- prueba de que el fichero publicado refleja el cambio.

## 7. Crawler access ≠ visibilidad garantizada

Permitir OAI-SearchBot/Claude-SearchBot/PerplexityBot no garantiza:

- crawl inmediato;
- indexación;
- cita;
- recomendación;
- ranking;
- tráfico.

También puede existir bloqueo efectivo por WAF/CDN/rate limiting aunque `robots.txt` diga `Allow`.

Esta separación aparece además en `docs/ai-discoverability/07-INDEXNOW-FRESCURA-WAF-Y-OPERACION-DE-CRAWLERS.md`.

## 8. Operación/observabilidad relacionada

El corpus de IA del repo propone clasificar logs por familias:

```text
search-openai
user-openai
training-openai
search-claude
user-claude
training-claude
search-perplexity
user-perplexity
search-google
search-bing
search-apple
other
```

La utilidad es no confundir training traffic con search visibility.

No hace falta implementar este logging solo para declarar B.2 cubierta; es una capa operativa aparte.

## 9. Qué NO hacer

- un bloque genérico `User-agent: AI`;
- asumir que nombres de bots no cambian nunca;
- copiar listas de blogs sin fuente primaria;
- permitir/bloquear por IP observada manualmente como única señal;
- decir que Google-Extended mejora Search;
- usar robots para proteger secretos/PII;
- bloquear Googlebot y esperar que `noindex` se procese;
- modificar todos los bots porque cambie uno;
- convertir una preferencia de entrenamiento en una afirmación sobre búsqueda/citas.

## 10. QA recomendado

Cuando cambie `robots.txt`:

1. parsear grupos y detectar duplicados/conflictos;
2. verificar URL pública `/robots.txt` 200;
3. comprobar sitemap canónico;
4. smoke de UAs prioritarios cuando sea técnicamente posible;
5. revisar WAF/CDN si el bot permitido recibe 403;
6. registrar fecha y URL de documentación del proveedor.

## 11. Definition of Done

- [x] hipótesis original preservada;
- [x] inspección del `robots.txt` de #135 preservada;
- [x] `ALREADY_COVERED` preservado;
- [x] diferenciación Search/User/Training/Product preservada;
- [x] OpenAI actual revalidado;
- [x] Anthropic actual revalidado;
- [x] Google-Extended revalidado;
- [x] estado real de `main` comprobado.

## 12. Trazabilidad #135

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- corpus `docs/ai-discoverability/` para crawlers/WAF/observabilidad.

Las pasadas y fuentes adicionales fueron revisadas; no convierten B.2 en implementación nueva.

## 13. Recomendación

**MERGE como reconstrucción completa + `ALREADY_COVERED`.** Mantener la matriz por bot y revisar cambios oficiales, sin reescribir la política existente.