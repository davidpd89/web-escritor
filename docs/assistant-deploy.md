# Asistente web — despliegue, seguridad y activación

Esta rama deja el código **seguro para fusionar**, pero la funcionalidad remota permanece desactivada hasta configurar Cloudflare. La página sigue `noindex,nofollow`; el Worker falla cerrado si falta cualquier binding, variable o secreto requerido. Fusionar el código no activa consumo de IA.

## Arquitectura

- Página: `/asistente/`.
- Endpoint preferido: Worker Route same-origin `https://davidportodiaz.com/api/assistant*`.
- Config pública: `GET /api/assistant/config`; solo expone `protocol_version`, estado de activación y la sitekey pública de Turnstile.
- Búsqueda local: intenta Pagefind; si no existe el índice o falla, usa el allowlist `data/assistant-source-registry.json`.
- Búsqueda remota: AI Search híbrido + BM25/vector + RRF, con hasta 20 candidatos y máximo 8 chunks permitidos hacia generación.
- Generación: Workers AI mediante `messages` con política en rol `system`; `ASSISTANT_MODEL` se fija solo en servidor.
- Fuentes: deny-by-default. Un chunk solo llega al modelo si se resuelve a un elemento del allowlist por `metadata.source_id` o por la URL canónica `item.key`.
- URLs: el modelo nunca controla un `href`; el frontend solo acepta rutas internas que empiezan por una única `/`.
- Antiabuso: Turnstile validado en servidor + rate limit de sesión + rate limit secundario por IP + límite agregado por ubicación Cloudflare.
- Degradación: si falla cualquier capa remota, el visitante conserva los resultados locales.

## Por qué el filtro metadata es opcional al principio

AI Search solo extrae metadatos web personalizados si las páginas publican los `<meta>` correspondientes y la instancia define ese schema. Esta PR no modifica las 18 páginas permitidas únicamente para añadir `source_id`/`visibility`, por lo que activar `filters: { visibility: "public" }` desde el primer despliegue podría dejar la recuperación vacía.

Por eso `ASSISTANT_REQUIRE_METADATA_FILTER=false` es el valor inicial seguro: AI Search recupera candidatos y el Worker aplica después un allowlist estricto **antes de que cualquier texto llegue al LLM**. Puede resolver cada candidato por `metadata.source_id` cuando exista o por `item.key`/URL canónica. Cuando el sitio publique metadata `source_id` y `visibility=public` de forma sistemática y se haya reindexado, se cambia a `ASSISTANT_REQUIRE_METADATA_FILTER=true` para filtrar también antes del retrieval.

## Configuración mínima de Cloudflare

1. Crear una instancia AI Search con índice vectorial + keyword y RRF.
2. Conectar el sitio/sitemap y limitar el contenido indexado a `main` para evitar header/footer/boilerplate.
3. Crear un **instance binding** `ASSISTANT_SEARCH`; la API usada es `env.ASSISTANT_SEARCH.search(...)`.
4. Crear binding Workers AI `AI`.
5. Crear tres Rate Limiting bindings con `namespace_id` distintos:
   - `SESSION_RATE_LIMITER`: 6/60 s como arranque;
   - `IP_RATE_LIMITER`: 30/60 s como límite secundario y deliberadamente más laxo;
   - `GLOBAL_RATE_LIMITER`: 120/60 s como cortafuegos grueso por ubicación Cloudflare.
6. Crear un widget Turnstile. Guardar:
   - `TURNSTILE_SITE_KEY` como variable pública del Worker;
   - `TURNSTILE_SECRET_KEY` como **secret**, nunca en Git;
   - `TURNSTILE_HOSTNAMES=davidportodiaz.com`.
7. Variables iniciales:
   - `ASSISTANT_ENABLED=false`;
   - `ASSISTANT_MODEL=<modelo Workers AI elegido tras evals>`;
   - `ASSISTANT_MATCH_THRESHOLD=0.42`;
   - `ASSISTANT_REQUIRE_METADATA_FILTER=false`.
8. Para staging, añadir su origen HTTPS en `ASSISTANT_ALLOWED_ORIGINS` y su hostname al widget/`TURNSTILE_HOSTNAMES`. No añadir `localhost` a producción.
9. Publicar el Worker en staging y ejecutar la batería E2E con las claves de prueba oficiales de Turnstile.
10. Solo tras pasar el gate, crear la Worker Route `/api/assistant*` y cambiar `ASSISTANT_ENABLED=true`.

## Contratos de seguridad que no deben relajarse

- POST exige `Origin` permitido; CORS no se considera autenticación.
- Turnstile se valida con Siteverify, `action=assistant_query` y hostname permitido. El token es de un solo uso y se resetea en el cliente tras cada intento.
- El body se lee con límite de bytes durante streaming; no se usa `request.text()` sin tope.
- El rate limit por sesión se evalúa antes del global para que una sesión ya bloqueada no consuma el contador global.
- Los rate limits de Workers son permisivos, locales y eventualmente consistentes: **no son un contador de facturación exacto**.
- Si el modelo devuelve una URL, una cita no recuperada o ninguna cita en una respuesta factual, la generación se descarta.
- `NO_EVIDENCE` produce abstención segura.
- Respuestas y prompts no se cachean ni se deben registrar en AI Gateway.
- No existe fallback automático a proveedores de pago.

## Gate de integración/activación

Antes de quitar `noindex` o añadir el asistente a navegación/sitemap:

- `python scripts/check-assistant-contract.py`;
- `python tests/test-assistant-contract.py`;
- `node tests/test-assistant-core.mjs`;
- `node tests/test-assistant-worker.mjs`;
- `node --check assets/assistant.js`;
- `node --check cloudflare-worker-assistant.js`;
- CI completo verde (`Tool engine tests`, `Check content indexes`, `Lighthouse CI` y cualquier check que se añada después);
- probar 403/409/413/415/429/502/503, timeout, JSON inválido, Turnstile fallido/expirado y protocolo incompatible;
- probar chunk sin `source_id` pero con `item.key` permitido;
- probar `source_id` inventado y URL `//evil.example`;
- probar respuesta generada que contiene una URL y confirmar que se rechaza;
- probar prompt injection en query y dentro de un chunk;
- probar AI Search/Workers AI caídos y confirmar que resultados locales siguen visibles;
- comprobar 320 px, 390 px, teclado, zoom 200 %, `prefers-reduced-motion` y lector de pantalla;
- confirmar que AI Gateway no guarda payloads y que Unified Billing/fallback de pago no están habilitados para esta ruta;
- confirmar que el modelo elegido continúa disponible dentro del plan gratuito deseado;
- solo entonces integrar `/asistente/` en `content-registry`, `navigation`, sitemap y retirar `noindex`.

## Deliberadamente fuera de esta PR

- No se crean recursos Cloudflare ni secretos desde GitHub.
- No se activa el Worker.
- No se genera todavía Pagefind porque el repositorio no tiene pipeline Pagefind; el cliente ya degrada al registry sin romperse.
- No se añaden metatags `source_id/visibility` a todas las páginas; son una optimización de fase de activación, no un requisito para que el Worker sea seguro.
- No se modifica `main` ni el estado de otras PR.
