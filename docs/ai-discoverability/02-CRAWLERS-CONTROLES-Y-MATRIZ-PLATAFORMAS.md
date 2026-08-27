# 02 — Crawlers, controles y matriz de plataformas

**Corte:** 2026-08-27  
**Regla:** búsqueda, recuperación a petición y entrenamiento son finalidades distintas. No atribuir a una señal de training un beneficio orgánico que el proveedor no documenta.

---

## 1. Política propuesta para davidportodiaz.com

### Objetivo de visibilidad

Permitir al máximo:

- crawlers de Search;
- indexadores usados para respuestas con citas;
- user-agents de recuperación cuando una persona pide consultar la web;
- Googlebot/Bingbot/Applebot y crawlers ordinarios compatibles;

siempre que no causen abuso operacional.

### Objetivo de training

Tomar una decisión separada sobre:

- GPTBot;
- ClaudeBot;
- Google-Extended;
- Applebot-Extended.

La decisión puede ser «Allow», pero la justificación correcta sería política editorial/participación en mejora de modelos, **no** «esto hará que me recomienden más».

---

## 2. OpenAI

### OAI-SearchBot

**Función documentada:** crawler de búsqueda para descubrimiento y aparición en ChatGPT Search.

**Recomendación:** `Allow`.

OpenAI indica que cualquier web pública puede aparecer, pero para que el contenido pueda incluirse en resúmenes/snippets y citarse con claridad no debe bloquearse OAI-SearchBot.

### ChatGPT-User

**Función:** recuperación dirigida por una interacción de usuario / agentic browser.

**Recomendación:** `Allow`.

### GPTBot

**Función:** posible model training/development.

**Recomendación:** decisión independiente. El repo hoy lo permite.

No hay documentación oficial que afirme que permitir GPTBot aumente el ranking en ChatGPT Search.

### WAF

OpenAI publica rangos oficiales de OAI-SearchBot en:

`https://openai.com/searchbot.json`

También publica feeds separados para otros agentes.

#### Regla

Si Cloudflare está bloqueando tráfico legítimo:

- consumir la fuente oficial;
- comprobar `creationTime`;
- no copiar rangos una vez y asumir que son eternos;
- versionar solo lógica/configuración, no secretos;
- registrar cambios de allowlist.

### Referral

OpenAI documenta que los links de referencia de ChatGPT Search incluyen:

`utm_source=chatgpt.com`

Esto debe formar parte de la taxonomía analítica.

---

## 3. Anthropic / Claude

Anthropic separa tres robots.

### Claude-SearchBot

**Función:** navegar/indexar web para mejorar relevancia y exactitud de resultados de búsqueda de Claude.

**Recomendación:** `Allow`.

Anthropic advierte que bloquearlo puede reducir visibilidad/precisión en resultados de búsqueda del usuario.

### Claude-User

**Función:** acceso iniciado por un usuario de Claude.

**Recomendación:** `Allow`.

Bloquearlo puede impedir que Claude recupere la página cuando el usuario lo solicita.

### ClaudeBot

**Función:** model development/training potencial.

**Recomendación:** decisión editorial separada.

### IPs

La documentación textual de ayuda de Anthropic ha indicado históricamente que no se publicaban rangos. Sin embargo, a fecha de corte existe una fuente oficial machine-readable activa:

`https://claude.com/crawling/bots.json`

con `creationTime` y prefijos IP.

#### Regla de autoridad

Para automatización WAF:

- priorizar la fuente oficial machine-readable vigente;
- registrar discrepancias con help docs;
- no hardcodear eternamente los prefijos;
- fallar de forma segura si el endpoint cambia.

---

## 4. Perplexity

### PerplexityBot

**Función:** indexar páginas para mostrarlas/enlazarlas en Perplexity Search.

**Training:** Perplexity declara que no se utiliza para foundation-model training.

**Recomendación:** `Allow`.

Fuente IP oficial:

`https://www.perplexity.com/perplexitybot.json`

### Perplexity-User

**Función:** recuperación cuando un usuario solicita contenido.

**Recomendación:** permitir técnicamente.

Fuente IP:

`https://www.perplexity.com/perplexity-user.json`

La documentación técnica indica que, por tratarse de una petición del usuario, este fetcher generalmente ignora robots.txt; aun así conviene evitar bloquearlo en WAF.

### Cambio de 2026

El help center actualizado el 16/07/2026 afirma que PerplexityBot respeta robots.txt y que la antigua capacidad de resumir una URL bloqueada fue deshabilitada para evitar abuso.

### Repo actual

- `PerplexityBot` aparece explícito.
- `Perplexity-User` no aparece explícito, pero el `User-agent: * / Allow: /` no lo bloquea.

### Acción

Agregarlo explícitamente solo si aporta claridad operacional y el contrato de `robots.txt` lo considera útil. No es imprescindible para desbloquearlo si el wildcard ya permite acceso.

---

## 5. Google

### Googlebot

Es la base de descubrimiento/indexación de Search y, por extensión, de las superficies generativas de Search.

**Recomendación:** permitir.

### AI Overviews / AI Mode

Google dice que las páginas necesitan:

- estar indexadas;
- ser elegibles para snippet;
- estar incluidas en funciones generativas mediante el control de Search Console cuando esa función esté disponible.

No existe un bot «AIOverviewsBot» que debamos añadir.

### Google-Extended

**Función:** token de control para usos relacionados con Gemini/model development fuera de la indexación de Google Search según documentación de Google.

**No es:** un crawler independiente de Search ni una señal de ranking.

### Search generative AI control

Cuando esté disponible:

`Search Console → Settings → Search generative AI`

La estrategia actual del proyecto es **Include**.

Esta configuración se documenta en profundidad en la PR específica de Search Console. Esta PR solo mantiene la dependencia.

---

## 6. Microsoft / Bing / Copilot

### Bingbot

Base de crawling/indexación Bing.

**Recomendación:** permitir.

### Copilot / generative answers

Bing Webmaster Guidelines y AI Performance conectan explícitamente la salud del índice Bing con grounding/citations en Copilot, respuestas generativas de Bing y partners seleccionados.

### Control práctico

- robots ordinarios;
- canonical;
- noindex;
- `data-nosnippet` cuando proceda;
- sitemap;
- IndexNow;
- Bing Webmaster Tools.

### `data-nosnippet`

Bing añadió soporte en 2025 para excluir secciones concretas de snippets y respuestas generativas manteniendo el resto de la página elegible.

En este sitio hoy no hay una necesidad general de usarlo. Puede ser útil si en el futuro hay:

- extractos premium;
- material beta;
- tablas sensibles;
- fragmentos que deben indexarse como página pero no reutilizarse en respuestas.

No aplicar indiscriminadamente.

---

## 7. Apple

### Applebot

Applebot rastrea contenido para tecnologías de búsqueda de Apple, incluyendo Spotlight, Siri y Safari. Apple también indica que datos rastreados pueden aportar contexto actualizado para contenido generado con modelos de IA en productos/servicios Apple.

**Recomendación:** permitir.

### Applebot-Extended

No rastrea. Es un token que controla cómo Apple puede usar datos obtenidos por Applebot para entrenamiento de modelos generales.

**Recomendación:** decisión editorial separada.

Apple confirma que bloquear Applebot-Extended no impide que una página siga apareciendo en Search.

### `isAccessibleForFree`

Apple documenta que páginas con `isAccessibleForFree:false` pueden aparecer en resultados, pero su contenido no se usa como contexto adicional para contenido generado por modelos de IA.

No aplica hoy a las páginas públicas de este proyecto, salvo futura zona premium.

---

## 8. Brave Search / Ask Brave

### Crawler

Brave declara que su crawler no anuncia un user-agent diferenciado. Si una página no es crawlable por Googlebot, Brave tampoco la rastrea.

### Experiencias

- AI Answers;
- Ask Brave;
- Featured Snippets;
- descripciones generadas.

Todas pueden citar/extractar contenido del índice Brave.

### Recomendación

No inventar un `BraveBot` en robots.

Priorizar:

- Googlebot-crawlability;
- noindex correcto;
- contenido original;
- títulos/estructura claros;
- páginas estables.

---

## 9. Gemini App

Gemini Apps puede utilizar información pública de Google Search. Deep Research incluye Google Search como fuente por defecto.

### Implicación

No existe para el webmaster un «Gemini index» independiente que debamos enviar en paralelo a Search.

Las mejoras de:

- Google Search indexing;
- AI Mode/AIO eligibility;
- autoridad;
- frescura;

son también relevantes para las partes de Gemini que recurren a Search.

### No confundir

`Google-Extended` con indexación de Gemini App desde Search.

---

## 10. Meta AI

### Estado público

Meta ha anunciado más contenido web en tiempo real mediante partnerships y enlaces de salida.

También dispone de un enorme corpus de contenido público dentro de:

- Instagram;
- Facebook;
- Threads;
- Reels.

### Control webmaster

No se ha encontrado un panel público equivalente a Search Console para registrar `davidportodiaz.com` y solicitar prioridad orgánica en Meta AI.

### Estrategia

- perfiles públicos coherentes;
- contenido original;
- entidad/título/obra identificables en copy;
- enlaces a páginas canónicas cuando proceda;
- participación auténtica;
- no spam.

---

## 11. xAI / Grok

xAI documenta herramientas de:

- Web Search;
- X Search;
- citations.

### Control webmaster

No se ha localizado en la investigación una guía oficial de crawler/robots o panel de webmaster orgánico equivalente a OpenAI/Claude/Perplexity/Bing.

### Decisión

`MONITOR`.

No crear reglas robots para un user-agent supuesto.

### X Search

Si en el futuro David mantiene una cuenta oficial X, la consistencia de entidad y los posts públicos pueden importar para resultados que Grok recupere mediante X Search.

El estado actual de perfiles canónicos del repo no incluye X; no inventarlo.

---

## 12. You.com y Search APIs downstream

You.com comercializa Search API y extracción optimizada para aplicaciones LLM/agents.

### Significado

Puede actuar como capa de retrieval para terceros.

### Control webmaster

No se ha localizado un panel específico que justifique trabajo propio en esta iniciativa.

### Estrategia

La misma base:

- crawlability;
- autoridad;
- contenido útil;
- claridad;
- frescura;
- fuentes externas.

---

## 13. Mistral / Le Chat y otros asistentes

Cuando un asistente usa búsqueda web pero no ofrece un crawler/panel verificable públicamente:

- no inventar controles;
- medir empíricamente en benchmark;
- trabajar upstream: Google/Bing/Brave/otros índices + contenido oficial;
- registrar la plataforma como `OBSERVE` hasta que publique documentación de webmaster.

Esto aplica también a asistentes emergentes o regionales.

---

## 14. Matriz de decisión

| Plataforma | Discovery/search | User fetch | Training separado | Panel/medición webmaster | Acción |
|---|---|---|---|---|---|
| Google AI Search | Googlebot/index Search | n/a | Google-Extended | Search Console GenAI | P0/P1 |
| Gemini | Google Search público | según producto | Google-Extended | indirecto vía Search Console | P1 |
| ChatGPT Search | OAI-SearchBot | ChatGPT-User | GPTBot | referrals; sin console propia pública | P0 |
| Claude | Claude-SearchBot | Claude-User | ClaudeBot | sin console pública | P0 |
| Perplexity | PerplexityBot | Perplexity-User | no foundation training vía bot | sin webmaster console general | P0 |
| Bing/Copilot | Bingbot | ecosistema Bing | n/a separado aquí | **AI Performance** | P0 |
| Apple | Applebot | productos Apple | Applebot-Extended | sin console general | P1 |
| Brave | crawler no UA diferenciado | producto propio | no tratado aquí | sin console comparable | P1 |
| Meta AI | web/partners + Meta public content | producto propio | controles distintos | sin webmaster console localizado | P1 social |
| Grok | Web Search + X Search | producto propio | no tratado | sin panel localizado | monitor |
| You.com/downstream | índice/search API | según cliente | no tratado | sin panel localizado | monitor |

---

## 15. Robots recomendado conceptualmente

No aplicar automáticamente; revisar con la política editorial.

```text
# Search / discovery
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

# Training / model development — decisión separada
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /
```

La versión actual ya cubre casi todo esto. El valor de este bloque es conceptual: saber qué se está autorizando.

---

## 16. Bot policy file interno propuesto

Crear en una futura implementación:

`data/ai-crawler-policy.json`

Ejemplo conceptual:

```json
{
  "OAI-SearchBot": {"purpose":"search", "policy":"allow"},
  "ChatGPT-User": {"purpose":"user-fetch", "policy":"allow"},
  "GPTBot": {"purpose":"training", "policy":"allow", "rankingBenefitClaimed":false},
  "Claude-SearchBot": {"purpose":"search", "policy":"allow"},
  "Claude-User": {"purpose":"user-fetch", "policy":"allow"},
  "ClaudeBot": {"purpose":"training", "policy":"allow", "rankingBenefitClaimed":false},
  "PerplexityBot": {"purpose":"search", "policy":"allow"},
  "Applebot-Extended": {"purpose":"training-control", "policy":"allow", "rankingBenefitClaimed":false},
  "Google-Extended": {"purpose":"training-control", "policy":"allow", "rankingBenefitClaimed":false}
}
```

### Utilidad

- evitar que comentarios humanos se conviertan en la única documentación;
- generar/validar `robots.txt`;
- impedir confundir training/search;
- testear regresiones;
- adjuntar fuente oficial y `verifiedAt`.

No convertirlo en archivo público de ranking.

---

## 17. Criterios de aceptación de crawler readiness

Para cada crawler prioritario:

- [ ] robots permite el acceso deseado;
- [ ] no hay `noindex` accidental en páginas canónicas;
- [ ] Cloudflare no responde challenge/403 al tráfico válido;
- [ ] HTML útil aparece sin depender de una interacción compleja;
- [ ] canonical es correcto;
- [ ] sitemap contiene la URL si corresponde;
- [ ] logs pueden detectar hits del UA sin almacenar PII innecesaria;
- [ ] no se sirve contenido especial engañoso al crawler;
- [ ] las rutas machine-readable no contienen secretos/operativa interna innecesaria;
- [ ] training policy está documentada por separado.

---

## 18. Lo que Claude NO debe hacer al implementar

- no forzar allowlists IP basadas en blogs de terceros;
- no bloquear un crawler solo porque su IP cambió;
- no añadir user-agents inventados;
- no hacer cloaking para IA;
- no servir copy distinto a bots salvo controles estándar legítimos;
- no asumir que `Crawl-delay` funciona igual para todos;
- no permitir un bot de training con el argumento «me posicionará»;
- no quitar `noindex` de páginas privadas/staging para «que la IA las conozca»;
- no debilitar Cloudflare de forma global para permitir un bot: usar reglas específicas y verificadas.
