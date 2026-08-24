# Asistente editorial V4 — benchmark free-first y contrato de evolución

Fecha de investigación: 2026-08-24  
PR de trabajo: #94 · rama `assistant-editorial-ux-v2` · base `implementacion-web-2026`

> Este documento **complementa y corrige** V3 cuando haya discrepancias. El estado real del repositorio y la web publicada manda sobre documentación histórica.

## 1. Objetivo

Construir un asistente de sitio que sea excelente sin depender de pagar por cada conversación. «Excelente» aquí significa: rápido, útil, accesible, con navegación correcta, fuentes verificables, privacidad razonable, degradación limpia, diseño editorial coherente y una capa de IA remota solo cuando aporta valor.

No se persigue imitar ChatGPT, Intercom o un SaaS de soporte. La ventaja de `davidportodiaz.com` es otra: el dominio de conocimiento está acotado, el corpus es nuestro, existe Pagefind local y las rutas de mayor valor pueden resolverse de forma determinista.

## 2. Correcciones de autoridad respecto a V3

### 2.1 El mapa del sitio sí existe

La ruta pública canónica es:

- https://davidportodiaz.com/mapa-del-sitio/
- ruta de repo: `/mapa-del-sitio/index.html`

Por tanto, `site-map` es una fuente válida en `data/assistant-source-registry.json`. No debe volver a documentarse como ruta inexistente.

### 2.2 La arquitectura principal tiene cinco territorios

La navegación principal actual se expresa como:

1. Obras
2. Autor
3. Cuaderno
4. Herramientas
5. Prensa

El asistente debe usar esos cinco nombres cuando orienta al usuario. Eventos, premios, recomendaciones, editoriales, convocatorias, Noveris, fragmentos, etc. son destinos secundarios dentro de esa arquitectura, no territorios nuevos.

## 3. Benchmark de productos y repositorios

La investigación separa dos cosas: **motor/plataforma** y **UX de chat**. No todo lo que tiene más funciones es mejor dependencia para esta web.

### 3.1 Flowise + Flowise Chat Embed

Web / repos:

- https://flowiseai.com/
- https://github.com/FlowiseAI/Flowise
- https://github.com/FlowiseAI/FlowiseChatEmbed

Qué aporta como referencia:

- widget popup y full-page;
- tamaños responsive;
- starters;
- historial de input opcional;
- acción de limpiar chat;
- feedback;
- título de documentos fuente;
- observadores de input/mensajes/loading;
- sonidos opcionales de envío/recepción;
- proxy y whitelist de dominios para no exponer configuración sensible.

Decisión: **no sustituir el asistente actual por Flowise**. Su embed es una gran referencia funcional, pero añadir Flowise completo introduce servidor, flujos, administración y superficie operativa que no necesitamos para navegación/RAG de un sitio editorial pequeño.

Patrones que sí adoptamos como criterio:

- fuentes visibles y comprensibles;
- posibilidad de reinicio/limpieza si existe estado conversacional persistente;
- feedback solo cuando haya un destino real para almacenar/analizarlo;
- carga diferida del widget.

### 3.2 Dify

Web / repo:

- https://dify.ai/
- https://github.com/langgenius/dify

Qué aporta:

- workflows de IA;
- RAG;
- agentes;
- múltiples proveedores/modelos;
- observabilidad;
- APIs;
- self-hosting.

Decisión: **no adoptar prelaunch**. Es una plataforma excelente para aplicaciones LLM generales, pero para este sitio duplicaría Pagefind, registry, Worker y observabilidad. Si en el futuro el asistente se convierte en un producto independiente con herramientas/agentes, Dify vuelve a ser candidato.

### 3.3 Chatwoot

Web / repo:

- https://www.chatwoot.com/
- https://github.com/chatwoot/chatwoot

Qué aporta:

- widget de chat web maduro;
- personalización de marca;
- self-hosting y control de datos;
- base de conocimiento;
- soporte humano/omnichannel;
- capa de IA Captain.

Decisión: **no adoptar** para el asistente editorial. Chatwoot es una plataforma de atención al cliente; nuestra necesidad es recuperación/navegación de contenido. Solo tendría sentido si la web necesitara atención humana, inbox, WhatsApp, CRM conversacional o agentes de soporte.

### 3.4 Botpress Webchat

Docs:

- https://botpress.com/docs/webchat/get-started/configure-your-webchat/
- https://botpress.com/docs/webchat/react-library/components/webchat/

Patrones útiles observados:

- feedback de mensajes;
- sonido opcional;
- historial;
- reinicio de conversación;
- elección sessionStorage/localStorage;
- launcher propio o elemento personalizado;
- mensaje proactivo con retraso;
- identidad y accesos de privacidad/condiciones.

Decisión: **benchmark UX, no dependencia**. Nuestro widget ya usa carga diferida, launcher propio y sessionStorage mínimo. Conservamos sessionStorage por privacidad y evitamos persistir transcript sin necesidad.

### 3.5 AnythingLLM

Web / repos:

- https://anythingllm.com/
- https://github.com/Mintplex-Labs/anything-llm
- https://github.com/Mintplex-Labs/anythingllm-embed

Qué aporta como referencia:

- chat de knowledge base embebible;
- sesiones por embed;
- límites por sesión/embed;
- greetings y copy configurable;
- RAG con documentos;
- presentación de fuentes;
- reset de conversación.

Decisión: **no adoptar**. Es una referencia directa para RAG embebido, pero requiere otra plataforma/servicio. Nuestro corpus ya está materializado en la web y Pagefind puede recuperarlo localmente sin coste por consulta.

### 3.6 assistant-ui

Web / repo:

- https://assistant-ui.com/
- https://github.com/assistant-ui/assistant-ui

Qué aporta como referencia UX:

- thread/composer/message/action bar separados;
- estados de streaming;
- retry/cancel;
- auto-scroll;
- adjuntos;
- atajos de teclado;
- accesibilidad;
- runtime desacoplado del proveedor de IA.

Decisión: **referencia UX, no librería**. La web no necesita introducir React para conseguir esas buenas prácticas. La separación conceptual sí se adopta: transcript, fuentes, sugerencias, composer y estado de request deben seguir siendo componentes lógicos distintos.

## 4. Búsqueda local: Pagefind sigue siendo la pieza correcta

Fuentes oficiales:

- https://github.com/Pagefind/pagefind
- https://pagefind.app/docs/api/
- https://pagefind.app/docs/metadata/
- https://pagefind.app/docs/ranking/
- https://pagefind.app/docs/weighting/
- https://pagefind.app/docs/sub-results/
- https://pagefind.app/docs/search-config/

El API de Pagefind devuelve para cada resultado:

- `url`;
- `excerpt`;
- `plain_excerpt`;
- `meta`;
- `sub_results` por encabezados enlazables.

También permite ajustar ranking y pesos. Esto es suficiente para construir una respuesta de búsqueda rica sin enviar la consulta a un tercero.

Contrato recomendado:

1. intent local fuerte → respuesta canónica;
2. si no hay intent → Pagefind;
3. presentar título + fragmento de contexto + enlace seguro;
4. si existen sub-results relevantes, valorar deep-link al encabezado en una iteración posterior;
5. si Pagefind no devuelve nada → registry canónica / mapa del sitio;
6. IA remota solo para síntesis de varias fuentes o preguntas realmente semánticas.

## 5. Capa remota gratuita: Cloudflare Workers AI

Fuentes oficiales:

- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/ai-gateway/reference/pricing/

Estado comprobado el 2026-08-24:

- Workers Free: hasta 100.000 requests/día, sujeto al resto de límites del plan;
- Workers AI: 10.000 Neurons/día sin cargo;
- algunos modelos de mayor coste exigen Workers Paid;
- AI Gateway ofrece funciones base como analítica, caching y rate limiting sin coste adicional en su capa core.

Conclusión: el remoto puede ser **free-first**, pero nunca debe ser la única forma de obtener una respuesta útil. Cuando se agota cuota, hay capacidad insuficiente o Turnstile falla, la experiencia debe volver automáticamente a Pagefind/registry.

## 6. Decisiones de producto cerradas en V4

### Se mantiene

- HTML útil sin JS;
- registry deny-by-default;
- URLs internas validadas;
- respuestas deterministas para rutas de alto valor;
- Pagefind como retrieval local;
- widget lazy-loaded;
- sessionStorage en vez de transcript persistente;
- Turnstile solo para remoto;
- kill switch de IA remota;
- sin upload de manuscritos al chatbot;
- sin guardar conversaciones por defecto.

### No se añade

- Flowise/Dify/AnythingLLM como dependencia prelaunch;
- React solo para el chat;
- vector DB externa;
- Algolia/Elasticsearch;
- persistencia de transcript;
- sonido por defecto;
- avatar humano falso;
- falsa sensación de «IA que lo sabe todo»;
- feedback sin backend/analítica donde tenga utilidad real.

### Sí se mejora

- comprensión de acciones + entidades, no solo frases exactas;
- tolerancia conservadora a erratas en entidades conocidas;
- cinco territorios actuales;
- mapa del sitio como salida estable;
- source registry enriquecida con aliases/summary/action;
- Pagefind como búsqueda de corpus completo;
- copy editorial en lugar de mensajes de error técnicos.

## 7. Contrato UX

### Primera impresión

El widget no debe competir con el contenido. Un launcher sobrio es suficiente. No usar pulsos infinitos ni globos agresivos.

### Apertura

- foco al composer cuando sea correcto;
- `Escape` cierra el widget;
- existe acceso a página completa;
- links de fuentes navegan el top-level, no se quedan atrapados en el iframe;
- loading/typing no bloquea ni desplaza de forma brusca.

### Respuesta

Orden recomendado:

1. respuesta breve;
2. fuentes relevantes;
3. sugerencias solo si reducen incertidumbre;
4. composer disponible inmediatamente.

No añadir metadatos ornamentales que parezcan sistema de soporte («ticket», «agente», «estado»).

### Error / falta de coincidencia

Nunca dejar callejón sin salida. Orden de degradación:

1. resultado Pagefind;
2. destinos registry;
3. mapa del sitio;
4. sugerencia de reformular con libro, herramienta, evento o sección.

## 8. Contrato de seguridad y privacidad

- Solo enlaces same-origin con `isSafeInternalPath`.
- Nunca renderizar HTML bruto de fuente no confiable; para snippets preferir `plain_excerpt` o `textContent`.
- Registry pública y pequeña; deny-by-default.
- El Worker remoto no recibe contenido de manuscritos desde este chatbot.
- Turnstile/rate limit son defensa de la capa remota, no requisito para la navegación local.
- No registrar prompt completo en logs persistentes salvo decisión explícita y documentada de privacidad.
- Mantener CSP compatible con Turnstile solo donde corresponda.

## 9. Matriz de prioridad para futuros agentes

| Prioridad | Mejora | Regla de ejecución |
|---|---|---|
| P0 | Registry generada siempre en paridad | CI debe fallar si JSON y JS divergen |
| P0 | intents de navegación de alto valor | test con lenguaje natural, posesivos y variantes |
| P0 | fallback siempre útil | nunca respuesta muerta |
| P0 | navegación segura de fuentes | same-origin + top-level desde iframe |
| P1 | snippets Pagefind en fuentes | usar `plain_excerpt`, truncado, `textContent` |
| P1 | deep-links de `sub_results` | solo si mejoran la precisión y pasan validación |
| P1 | acción «reiniciar» | útil si se amplía contexto; no persistir transcript por defecto |
| P1 | telemetría de errores agregada | sin registrar contenido sensible |
| P2 | Workers AI | solo con fuentes controladas, citas y fallback local |
| P2 | feedback | solo con almacenamiento/analítica útil y política definida |
| P2 | NLU externo | solo si las reglas dejan de escalar |

## 10. Criterio de merge de #94

La PR puede considerarse lista cuando:

1. `assets/assistant-source-registry.js` está regenerado desde JSON;
2. tests de intent incluyen lenguaje natural como «Busco dónde mandar mi novela»;
3. el overview menciona los cinco territorios y el mapa del sitio;
4. Assistant hardening / contract / browser QA pasan;
5. tests de core/editorial pasan;
6. Cross-engine y Pa11y del asistente no introducen regresiones;
7. cualquier rojo restante está demostrado como heredado del base y documentado, no ignorado;
8. sigue sin activar IA remota ni desplegar infraestructura.

No se mergea a `main` desde esta PR. Su base continúa siendo `implementacion-web-2026`.
