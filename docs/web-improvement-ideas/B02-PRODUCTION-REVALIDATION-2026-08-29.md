# B.2 · Revalidación de producción · 2026-08-29

## Veredicto

**READY_NO_CODE · ALREADY_COVERED · PROVIDER_POLICY_WATCH**

El `robots.txt` actual ya mantiene una política suficientemente diferenciada para las familias de acceso que importan a este sitio. La revisión de documentación oficial vigente no revela una regresión que justifique reescribirlo.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- `robots.txt`;
- `scripts/check-ai-discoverability.py`;
- `tests/test-machine-authority.py`;
- documentación oficial vigente de OpenAI, Anthropic, Google, Apple y Perplexity.

## Estado actual de robots.txt

La política publicada distingue explícitamente:

- `OAI-SearchBot` — búsqueda OpenAI;
- `ChatGPT-User` — acciones iniciadas por usuario;
- `GPTBot` — model development/training;
- `PerplexityBot` — crawler de búsqueda;
- `Applebot-Extended` — control de uso de datos por Apple;
- `ClaudeBot` — model development;
- `Claude-SearchBot` — búsqueda;
- `Claude-User` — recuperación iniciada por usuario;
- `Google-Extended` — token de control de producto Gemini/Vertex;
- `User-agent: *` — acceso general;
- sitemap canónico.

Todos están actualmente permitidos por decisión explícita del sitio.

## OpenAI · revalidación 2026

La documentación oficial de crawlers mantiene la separación principal:

- `OAI-SearchBot`: Search;
- `GPTBot`: contenido potencialmente usado para entrenamiento de modelos fundacionales;
- `ChatGPT-User`: acciones iniciadas por usuarios; no determina elegibilidad en Search y robots.txt puede no aplicar a estos fetches;
- `OAI-AdsBot`: crawler específico para validar páginas que un anunciante envía como landing pages de anuncios de ChatGPT; no se usa para entrenar modelos fundacionales.

`OAI-AdsBot` no requiere cambio por B.2:

1. este sitio no está documentando aquí una integración de ChatGPT Ads;
2. el `User-agent: * / Allow: /` actual ya no lo bloquea;
3. solo tendría sentido añadir una regla específica si la política para AdsBot debiera diferir de la política general.

No ampliar una lista explícita por el mero hecho de que aparezca un crawler nuevo si su política efectiva ya es la deseada.

Fuentes:

- `https://developers.openai.com/api/docs/bots`;
- `https://help.openai.com/en/articles/12627856-publishers-and-developers-faq`;
- `https://help.openai.com/en/articles/20001243-advertiser-guidance-for-allowing-openai-web-crawlers`.

## Anthropic · revalidación 2026

Anthropic sigue documentando tres robots distintos:

- `ClaudeBot`: model development;
- `Claude-SearchBot`: búsqueda;
- `Claude-User`: recuperación a petición del usuario.

Los tres aparecen en robots.txt y la separación coincide con la semántica oficial.

Fuente:

- `https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler`.

## Google · revalidación 2026

`Google-Extended` continúa siendo un **product token**, no un crawler HTTP independiente. Controla determinados usos del contenido rastreado para Gemini/Vertex AI y no afecta inclusión ni ranking en Google Search.

La descripción/comentario actual del repo es correcta.

Fuente:

- `https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers`.

## Apple · revalidación 2026

Apple mantiene:

- `Applebot` como crawler que puede alimentar búsquedas y otras experiencias de Apple;
- `Applebot-Extended` como control adicional sobre uso para entrenamiento de modelos fundacionales; Apple declara que `Applebot-Extended` no rastrea páginas por sí mismo.

El repo no necesita un grupo explícito `Applebot` porque `User-agent: * / Allow: /` ya lo permite. El token que requiere una decisión distinta —`Applebot-Extended`— sí está explicitado.

Fuente:

- `https://support.apple.com/119829`.

## Perplexity · matiz actual

Perplexity documenta:

- `PerplexityBot` como crawler de búsqueda;
- `Perplexity-User` para acciones iniciadas por usuarios.

También indica que, al ser un fetch solicitado por usuario, `Perplexity-User` generalmente ignora reglas robots.txt.

Por tanto, no se añade un grupo `Perplexity-User` pretendiendo que robots.txt sea un control fiable de esos fetches. Si el sitio necesitara bloquearlos operativamente, habría que revisar mecanismos/WAF y documentación vigente del proveedor, no fabricar una garantía robots inexistente.

Fuente:

- `https://docs.perplexity.ai/docs/resources/perplexity-crawlers`.

## Autoridades técnicas existentes

`scripts/check-ai-discoverability.py` ya comprueba:

- sitemap canónico;
- que crawlers Search prioritarios puedan acceder a rutas clave;
- estado informativo de bots de training;
- indexabilidad/canonical de páginas representativas;
- aliases Anthropic legacy.

`tests/test-machine-authority.py` protege además que la política robots conserve tokens documentados prioritarios y que no reaparezcan aliases legacy.

No hace falta un segundo parser de robots para B.2.

## Decisión operativa

No modificar `robots.txt` hoy.

La política correcta es revisar cambios por proveedor y cambiar una regla solo si cambia una decisión real del sitio sobre:

- búsqueda/citación;
- fetch iniciado por usuario;
- entrenamiento/model development;
- anuncios;
- control de producto.

## Triggers de reapertura

1. cambio oficial de nombre/semántica de un token;
2. crawler nuevo cuyo acceso deba diferir de `User-agent: *`;
3. decisión de negocio/privacidad de bloquear training manteniendo Search;
4. WAF/CDN bloqueando un bot permitido con 403/429;
5. crawler prioritario que deje de estar cubierto por los checks propietarios;
6. incidentes reales de carga/rate limiting que exijan política específica.

## Qué no hacer

- listas de bots copiadas de blogs;
- asumir que cada token es un crawler HTTP real;
- tratar user-fetch como si robots.txt siempre aplicara;
- añadir explícitamente bots cuya política ya hereda correctamente de `*` sin motivo;
- confundir training con Search;
- afirmar que Google-Extended/Applebot-Extended mejoran ranking;
- basarse solo en user-agent sin considerar WAF/IP verificada cuando se investigan fallos reales.

## Definition of Done

- [x] robots.txt actual inspeccionado;
- [x] OpenAI actual revalidado;
- [x] Anthropic actual revalidado;
- [x] Google-Extended revalidado;
- [x] Applebot-Extended revalidado;
- [x] PerplexityBot/Perplexity-User revalidados;
- [x] OAI-AdsBot clasificado sin inflar la política;
- [x] owner QA existente localizado;
- [x] ausencia de hueco de producción demostrada;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Cierre

B.2 sigue `ALREADY_COVERED`. La mejora correcta no es aumentar el número de bloques de robots.txt, sino conservar una política intencional por producto y reaccionar solo a cambios oficiales o problemas de acceso observables.