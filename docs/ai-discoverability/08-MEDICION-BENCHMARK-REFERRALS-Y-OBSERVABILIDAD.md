# 08 — Medición, benchmark, referrals y observabilidad

## 1. Objetivo

Saber si la estrategia mejora sin depender de capturas anecdóticas, herramientas que inventan un «AI rank» o cambios de modelo que hacen incomparable una semana con otra.

---

## 2. Lo que podemos medir de verdad

### Directamente por proveedor

- Bing Webmaster Tools AI Performance;
- Google Search Console Generative AI Performance cuando esté disponible;
- referrals de ChatGPT (`utm_source=chatgpt.com`);
- referrals HTTP de otras superficies cuando no se pierdan;
- server logs de crawlers;
- resultados de un benchmark controlado.

### No observable de forma completa

- «qué piensa el modelo sobre David»;
- porcentaje global de conversaciones donde recomienda un libro;
- ranking interno universal de ChatGPT/Claude/Gemini;
- prompts privados de otros usuarios;
- impacto de training en una recomendación concreta.

---

## 3. Benchmark de prompts

Crear un corpus versionado, no improvisado.

Ruta propuesta:

`data/ai-discoverability-benchmark.json`

### Categorías

#### Entity facts

- ¿Quién es David Porto Díaz?
- ¿Qué libros ha publicado David Porto Díaz?
- ¿Cuándo se publicó Samuel entre mundos?
- ¿Quién publica Las manecillas del recuerdo?
- ¿Qué es Noveris?
- ¿Qué premio ha ganado David Porto Díaz?

#### Discovery

- escritores gallegos actuales de fantasía;
- autores españoles de fantasía juvenil;
- recursos gratuitos para escritores en español;
- webs de escritores con herramientas para manuscritos.

#### Recommendation fit — Samuel

- fantasía juvenil española con portales;
- novela en español con sistema de magia que tiene un coste;
- fantasía juvenil donde el romance no sea el centro;
- libros españoles de portal fantasy;
- novela de fantasía para club de lectura juvenil/adulto.

#### Recommendation fit — Manecillas

- novela coral española sobre memoria/familia;
- ficción especulativa sobre un objeto que conecta varias vidas;
- novelas contemporáneas con elemento especulativo y estructura coral;
- libro para club de lectura sobre memoria y familia.

#### Topic authority

- qué es portal fantasy;
- cómo diseñar magia con coste;
- herramientas para detectar repeticiones en un manuscrito;
- editoriales españolas de fantasía que reciben manuscritos —solo si el directorio tiene datos vigentes;
- convocatorias abiertas para escritores —temporal.

#### Negative controls

Prompts donde **no debería** aparecer:

- mejor romantasy erótica adulta;
- ciencia ficción hard espacial;
- autor de thriller nórdico;
- librería física en Madrid.

Sirven para detectar sobreoptimización o hallucination.

---

## 4. Tamaño recomendado

Inicial:

- 50 prompts;
- 10 facts;
- 10 discovery;
- 10 Samuel;
- 10 Manecillas;
- 5 topic authority;
- 5 negative controls.

Después ampliar a 100 solo si el análisis sigue siendo manejable.

No generar 10.000 prompts sintéticos para fabricar una métrica falsa de precisión.

---

## 5. Plataformas del benchmark

### Tier A mensual

- ChatGPT Search;
- Gemini / Search-grounded;
- Claude con web search;
- Perplexity Search;
- Microsoft Copilot;

### Tier B trimestral

- Brave Ask;
- Apple/Siri cuando la consulta web sea comparable;
- Meta AI;
- Grok;
- You.com / otros con relevancia.

### Deep research separado

No mezclar resultados de Deep Research con search rápido.

---

## 6. Metadata por ejecución

Guardar:

```json
{
  "runDate": "2026-08-27",
  "platform": "chatgpt",
  "surface": "search",
  "model": "as-displayed-by-product",
  "locale": "es-ES",
  "loggedIn": true,
  "locationMode": "default",
  "promptId": "REC-SAM-001"
}
```

### No guardar

- cookies;
- cuenta;
- conversaciones privadas ajenas;
- IDs personales;
- datos no necesarios.

---

## 7. Scoring por prompt

### Factual accuracy

`0–1`

- 1: hechos centrales correctos;
- 0: contiene un error material.

También registrar cada error individual.

### Official mention

- `0`: no menciona;
- `1`: menciona David/obra;
- `2`: menciona y enlaza/cita sitio oficial.

### Recommendation fit

- `0`: no aparece;
- `1`: aparece pero sin explicación útil;
- `2`: aparece con encaje correcto;
- `-1`: aparece aunque no encaja / recomendación engañosa.

### Citation quality

Clasificar:

- official-site;
- publisher;
- retailer;
- bibliographic;
- reputable-media;
- community;
- unknown/low-quality.

---

## 8. No crear un ranking único

Evitar:

> AI Visibility Score = 87/100

si oculta que:

- ChatGPT acierta facts pero no recomienda;
- Copilot cita herramientas;
- Perplexity usa fuentes externas;
- Gemini tiene stale data en una query.

### Dashboard

Mostrar dimensiones separadas.

---

## 9. Variabilidad

Las respuestas son no deterministas y dependen de:

- modelo;
- fecha;
- producto;
- sesión;
- ubicación;
- personalización;
- providers;
- cambios del índice.

### Regla

Para prompts estratégicos, ejecutar 3 réplicas cuando se quiera medir un cambio serio.

No para todos los prompts todas las semanas.

---

## 10. Frecuencia

### Semanal

- P0 factual smoke: 10 prompts;
- Bing AI Performance;
- stale facts.

### Mensual

- benchmark 50 completo;
- referrals IA;
- Search Console GenAI;
- crawler traffic.

### Trimestral

- Tier B;
- perfiles externos;
- crawler docs/provider changes;
- revisión de fuentes.

### Eventos

Ejecutar además tras:

- lanzamiento;
- cambio de ISBN/editorial;
- gran rediseño;
- publicación de nueva obra;
- incidente de stale data;
- cambios de robots/WAF.

---

## 11. Bing AI Performance

Capturar por periodo:

- total citations;
- average cited pages;
- top cited URLs;
- grounding queries;
- trend.

### Si aparecen intents/topics/citation share

Registrar como campos opcionales y marcar `preview`.

### No inferir

- que una cita es posición #1;
- que citation share es cuota total de «la IA»;
- que todas las respuestas de Copilot están representadas.

---

## 12. Search Console Generative AI

Si la propiedad tiene rollout:

- páginas;
- países;
- dispositivos;
- fechas;
- impresiones.

### Integración

Cruzar con territorios ya definidos en PR Search Console:

- Autor;
- Obras;
- Cuaderno;
- Herramientas;
- Recursos;
- Recomendaciones.

No duplicar código/estrategia de la PR #110.

---

## 13. Referral analytics

### ChatGPT

Segmentar `utm_source=chatgpt.com`.

### Otros

Mantener lista configurable de referrers observados, por ejemplo:

- `perplexity.ai`;
- `claude.ai`;
- dominios Bing/Copilot;
- Gemini/Google cuando sean identificables.

### Cuidado

Apps nativas, deep links y privacy layers pueden eliminar `Referer`.

`0 referrals` ≠ `0 menciones`.

---

## 14. Taxonomía propuesta

```json
{
  "chatgpt": {
    "utmSources": ["chatgpt.com"],
    "referrerHosts": ["chatgpt.com"]
  },
  "perplexity": {
    "referrerHosts": ["perplexity.ai"]
  }
}
```

Actualizar solo con tráfico observado/documentación fiable.

---

## 15. Crawler observability

Métricas mensuales:

| Crawler | Hits | 2xx | 3xx | 4xx | 5xx | páginas críticas visitadas |
|---|---:|---:|---:|---:|---:|---|

### Señales de problema

- OAI-SearchBot 403 sostenido;
- Claude-SearchBot nunca accede después de publicación material;
- Bingbot recibe 5xx;
- PerplexityBot solo ve robots y no páginas;
- crawler cae en redirect loop.

No exigir que cada bot visite cada semana.

---

## 16. Source citation ledger

Guardar qué URLs usa cada plataforma en benchmark.

Campos:

- platform;
- promptId;
- citedUrl;
- sourceType;
- official/external;
- correct;
- stale;
- date.

### Preguntas que responderemos

- ¿qué páginas del sitio son más citables?
- ¿qué fuentes externas dominan la entidad?
- ¿un dato erróneo viene de nuestra web o de un tercero?
- ¿cuándo aparece por primera vez Manecillas en fuentes externas?

---

## 17. Error taxonomy

### E1 — stale

Dato correcto históricamente pero viejo.

### E2 — hallucination

Dato sin soporte.

### E3 — entity collision

David/Noveris/obra confundidos con otra entidad.

### E4 — attribution

Premio/editorial/obra mal atribuidos.

### E5 — commerce

Retailer/precio/stock inventado.

### E6 — recommendation mismatch

Libro recomendado para un criterio que contradice su ficha.

### E7 — source quality

Respuesta correcta pero sustentada en fuente dudosa cuando existe una fuente mejor.

---

## 18. Incident threshold

Abrir issue P0 si:

- 2+ plataformas repiten un error factual crítico;
- Bing/Google cita una página vieja tras una corrección significativa durante un periodo anormal;
- la web oficial es la fuente del error;
- crawler search prioritario queda bloqueado por WAF;
- ISBN/editorial/fecha comercial se hallucina sistemáticamente.

---

## 19. Experimentos

Para probar una mejora:

1. congelar prompts afectados;
2. capturar baseline;
3. hacer **un cambio útil humano**;
4. publicar;
5. anotar fecha;
6. esperar ventana razonable;
7. repetir benchmark;
8. comparar factual/citation/fit;
9. no atribuir causalidad fuerte con una sola respuesta.

---

## 20. Terceros de «GEO tracking»

Herramientas externas pueden ser útiles para:

- automatizar prompts;
- capturar citas;
- observar tendencias;
- comparar marcas.

Pero Google advierte que terceros no tienen acceso a sus sistemas internos de ranking/IA.

### Criterios para contratar

- plataformas cubiertas;
- posibilidad de fijar locale;
- prompts exportables;
- respuestas/citas crudas disponibles;
- frecuencia;
- metodología publicada;
- no inventar «internal ranking data»;
- coste por prompt;
- GDPR/DPA;
- retención;
- API;
- capacidad de excluir personalización.

No seleccionar marca sin evaluación actual de precios/terms.

---

## 21. API benchmark

Automatizar solo mediante APIs oficiales permitidas.

### Posibles capas

- proveedor con web search tool;
- prompt corpus;
- parser de citations;
- fact evaluator basado en canonical facts;
- almacenamiento JSONL.

### Nunca

- scraping automatizado de interfaces consumidor si incumple terms;
- crear cuentas masivas;
- enviar prompts desde proxies para falsear locales;
- usar el propio modelo medido como único juez de corrección.

---

## 22. Evaluación factual automática

Para hechos atómicos puede automatizarse:

- regex/structured extraction;
- ISBN;
- año;
- editorial;
- páginas;
- premio.

Para recomendación, revisión humana sigue siendo necesaria.

---

## 23. Dashboard mínimo

### Cards

- factual accuracy 30d;
- official citation rate;
- stale errors abiertos;
- Bing AI citations;
- Google GenAI impressions;
- ChatGPT referral sessions;
- crawler blocks.

### Charts

- citas por plataforma/mes;
- cited pages;
- error types;
- recommendation fit;
- external vs official citations.

No unir todas en una «nota SEO IA».

---

## 24. Datos históricos

Guardar snapshots para distinguir:

- «nunca aparecía»;
- «empezó a aparecer»;
- «aparece menos»;
- «cambió la fuente».

Sin histórico, un cambio de respuesta parece más significativo de lo que es.

---

## 25. Privacidad

El benchmark no necesita datos personales.

Analytics:

- agregada;
- respetar política actual;
- no fingerprinting para identificar «usuario que vino de IA»;
- no enviar prompts de usuarios reales del asistente propio a herramientas GEO.

---

## 26. DoD de medición

- [ ] corpus versionado;
- [ ] facts esperados por prompt factual;
- [ ] negative controls;
- [ ] 5 plataformas Tier A;
- [ ] metadata de run;
- [ ] citas capturadas;
- [ ] errores categorizados;
- [ ] Bing AI baseline;
- [ ] Google GenAI baseline si disponible;
- [ ] ChatGPT referral segment;
- [ ] crawler report;
- [ ] informe mensual legible por humano;
- [ ] ninguna métrica presentada como ranking interno del proveedor.