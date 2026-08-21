# Asistente web — despliegue, seguridad y activación

Esta rama deja el código **seguro para fusionar**, pero la funcionalidad remota permanece desactivada hasta configurar Cloudflare y pasar staging. La página sigue `noindex,nofollow`; el Worker falla cerrado si falta cualquier binding, variable, secreto o modelo permitido. Fusionar el código no activa consumo de IA.

## Arquitectura

- Página: `/asistente/`.
- Endpoint preferido: Worker Route same-origin `https://davidportodiaz.com/api/assistant*`.
- Config pública: `GET /api/assistant/config`; solo expone `protocol_version`, estado de activación y la sitekey pública de Turnstile.
- Búsqueda local: intenta Pagefind; si no existe el índice o falla, usa el allowlist `data/assistant-source-registry.json`.
- Búsqueda remota: AI Search híbrido + BM25/vector + RRF, hasta 16 candidatos; máximo 6 chunks permitidos y 1.200 caracteres por chunk hacia generación.
- Generación V1: Workers AI mediante `messages` con política en rol `system`; se admite únicamente `@cf/qwen/qwen3-30b-a3b-fp8` hasta que otro modelo sea auditado y se actualice expresamente el allowlist de código.
- Fuentes: deny-by-default. Un chunk solo llega al modelo si se resuelve a un elemento del allowlist por `metadata.source_id` o por la URL canónica `item.key`.
- URLs: el modelo nunca controla un `href`; el frontend solo acepta rutas internas que empiezan por una única `/`.
- Citas: el modelo usa IDs internos para validación; el visitante ve `[1]`, `[2]…` y una lista ordenada de fuentes reales.
- Antiabuso: Turnstile validado en servidor + rate limit de sesión + rate limit secundario por IP + límite agregado por ubicación Cloudflare.
- Cuota persistente: D1 aplica un máximo de 5 generaciones por sesión/día UTC y 50 generaciones globales/día UTC. Los valores configurables solo pueden reducir esos máximos, nunca aumentarlos.
- Degradación: si falla cualquier capa remota o se agota una cuota, el visitante conserva los resultados locales.

## Garantía de coste V1

La intención de V1 es **coste automático de IA = 0**. A 21/08/2026, Workers AI incluye 10.000 neuronas/día gratis. En Workers Free, al superar la asignación las operaciones fallan; en Workers Paid, el exceso puede facturarse. Por eso no basta con un rate limit por minuto.

La implementación combina:

1. un único modelo V1 de bajo consumo permitido en código (`@cf/qwen/qwen3-30b-a3b-fp8`);
2. contexto acotado (6 × 1.200 caracteres) y salida máxima de 350 tokens;
3. cuota D1 exacta de 50 generaciones/día globales y 5 por sesión/día;
4. sin fallback a otro modelo/proveedor;
5. si se agota cualquier cuota, se devuelve 429 y el frontend continúa con búsqueda local.

Para una garantía operativa adicional, **preferir Workers Free para este Worker/entorno de IA**. Si se despliega en una cuenta Workers Paid, revisar antes de activar que no exista Unified Billing, prepaid credits o rutas dinámicas capaces de cambiar de proveedor/modelo. AI Gateway Spend Limits pueden usarse como barrera adicional, pero no deben ser la única protección porque su contabilidad es eventualmente consistente.

Cloudflare puede cambiar modelos, cuotas o precios. Antes de cada activación/revisión de infraestructura hay que comprobar la documentación vigente. Si el modelo deja de estar disponible gratis, el comportamiento correcto es mantener `ASSISTANT_ENABLED=false` hasta elegir y auditar otro.

## D1: cuota diaria

Crear una D1 específica o una tabla dedicada y aplicar:

`migrations/assistant-quota.sql`

Enlazarla como `ASSISTANT_QUOTA_DB`. La tabla usa clave compuesta `(bucket, day_utc)` y cada incremento se hace en una única sentencia `INSERT ... ON CONFLICT ... RETURNING`, evitando el clásico SELECT+UPDATE susceptible a carreras. El Worker elimina de forma oportunista buckets de más de ocho días cuando comienza un nuevo día global.

La D1 no almacena preguntas, respuestas, IPs, emails ni contenido del sitio: solo buckets globales y el identificador aleatorio de sesión que ya vive en `sessionStorage`.

## Por qué el filtro metadata es opcional al principio

AI Search solo extrae metadatos web personalizados si las páginas publican los `<meta>` correspondientes y la instancia define ese schema. Esta PR no modifica las 18 páginas permitidas únicamente para añadir `source_id`/`visibility`, por lo que activar `filters: { visibility: "public" }` desde el primer despliegue podría dejar la recuperación vacía.

Por eso `ASSISTANT_REQUIRE_METADATA_FILTER=false` es el valor inicial seguro: AI Search recupera candidatos y el Worker aplica después un allowlist estricto **antes de que cualquier texto llegue al LLM**. Puede resolver cada candidato por `metadata.source_id` cuando exista o por `item.key`/URL canónica. Cuando el sitio publique metadata `source_id` y `visibility=public` de forma sistemática y se haya reindexado, se cambia a `ASSISTANT_REQUIRE_METADATA_FILTER=true` para filtrar también antes del retrieval.

## Configuración mínima de Cloudflare

1. Crear una instancia AI Search con índice vectorial + keyword y RRF.
2. Conectar el sitio/sitemap y limitar el contenido indexado a `main` para evitar header/footer/boilerplate.
3. Crear un **instance binding** `ASSISTANT_SEARCH`; la API usada es `env.ASSISTANT_SEARCH.search(...)`.
4. Crear binding Workers AI `AI`.
5. Crear D1, aplicar `migrations/assistant-quota.sql` y enlazarla como `ASSISTANT_QUOTA_DB`.
6. Crear tres Rate Limiting bindings con `namespace_id` distintos:
   - `SESSION_RATE_LIMITER`: 6/60 s como arranque;
   - `IP_RATE_LIMITER`: 30/60 s como límite secundario y deliberadamente más laxo;
   - `GLOBAL_RATE_LIMITER`: 120/60 s como cortafuegos grueso por ubicación Cloudflare.
7. Crear un widget Turnstile. Guardar:
   - `TURNSTILE_SITE_KEY` como variable pública del Worker;
   - `TURNSTILE_SECRET_KEY` como **secret**, nunca en Git;
   - `TURNSTILE_HOSTNAMES=davidportodiaz.com`.
8. Variables iniciales:
   - `ASSISTANT_ENABLED=false`;
   - `ASSISTANT_MODEL=@cf/qwen/qwen3-30b-a3b-fp8`;
   - `ASSISTANT_MATCH_THRESHOLD=0.42`;
   - `ASSISTANT_REQUIRE_METADATA_FILTER=false`;
   - `ASSISTANT_DAILY_SESSION_LIMIT=5`;
   - `ASSISTANT_DAILY_GLOBAL_LIMIT=50`.
9. Para staging, añadir su origen HTTPS en `ASSISTANT_ALLOWED_ORIGINS` y su hostname al widget/`TURNSTILE_HOSTNAMES`. No añadir `localhost` a producción.
10. Publicar el Worker en staging y ejecutar la batería E2E con las claves de prueba oficiales de Turnstile.
11. Solo tras pasar el gate, crear la Worker Route `/api/assistant*` y cambiar `ASSISTANT_ENABLED=true`.

## Contratos de seguridad que no deben relajarse

- POST exige `Origin` permitido; CORS no se considera autenticación.
- Turnstile se valida con Siteverify, `action=assistant_query` y hostname permitido. El token es de un solo uso y se resetea en el cliente tras cada intento.
- El cliente impone timeout propio a carga/callback de Turnstile para que un bloqueo de red o extensión nunca deje la interfaz ocupada indefinidamente.
- El body se lee con límite de bytes durante streaming; no se usa `request.text()` sin tope.
- El rate limit por sesión se evalúa antes de Turnstile; el global se evalúa después de Turnstile, para que tráfico con desafío inválido no agote el cortafuegos global.
- Los rate limits de Workers son permisivos, locales y eventualmente consistentes: **no son un contador de facturación exacto**. D1 es quien aplica el límite diario persistente de generación.
- La cuota D1 se consume únicamente cuando el retrieval ha producido chunks públicos válidos y antes de llamar al modelo.
- Si el modelo devuelve una URL, una cita no recuperada o ninguna cita en una respuesta factual, la generación se descarta.
- `NO_EVIDENCE` produce abstención segura.
- Respuestas y prompts no se cachean ni se deben registrar en AI Gateway.
- No existe fallback automático a proveedores de pago.
- El botón «Detener» cancela la petición del navegador y evita mostrar una respuesta ya no deseada. El binding de Workers AI no documenta actualmente un `AbortSignal` para cancelar una inferencia ya iniciada, por lo que la cuota diaria se consume antes de generación y no se promete recuperar ese cupo si el usuario detiene una inferencia en curso.

## Privacidad antes de activar IA

Aunque el código puede fusionarse apagado, **no retirar `noindex` ni activar `ASSISTANT_ENABLED`** hasta actualizar `privacidad.html` con:

- finalidad: responder/localizar contenido solicitado por el visitante;
- datos enviados al Worker: pregunta, locale, token antiabuso e identificador aleatorio de sesión;
- uso de Cloudflare Turnstile/Workers AI/AI Search como infraestructura;
- ausencia de almacenamiento deliberado de conversaciones en D1;
- D1 solo conserva buckets pseudónimos de cuota con limpieza aproximada de ocho días;
- GoatCounter no debe recibir el texto de la pregunta;
- forma de ejercer derechos/contacto aplicable.

La activación debe revisarse también frente a las condiciones/DPA vigentes de Cloudflare y la configuración real de logs. No activar payload logging de prompts/respuestas.

## Gate de integración/activación

Antes de quitar `noindex` o añadir el asistente a navegación/sitemap:

- `python scripts/check-assistant-contract.py`;
- `python tests/test-assistant-contract.py`;
- `node tests/test-assistant-core.mjs`;
- `node tests/test-assistant-worker.mjs`;
- `node --check assets/assistant.js`;
- `node --check cloudflare-worker-assistant.js`;
- CI completo verde (`Tool engine tests`, `Check content indexes`, `Lighthouse CI` y cualquier check que se añada después);
- Lighthouse debe incluir expresamente `http://localhost/asistente/`; mientras esté en `noindex`, SEO agregado permanece desactivado para esa ruta pero título, meta, canonical, enlaces, accesibilidad, rendimiento y CLS/TBT sí se verifican;
- probar 403/409/413/415/429/502/503, timeout, JSON inválido, Turnstile fallido/expirado y protocolo incompatible;
- probar límites D1 de sesión/global y caída de D1 (`quota_unavailable`);
- probar chunk sin `source_id` pero con `item.key` permitido;
- probar `source_id` inventado y URL `//evil.example`;
- probar respuesta generada que contiene una URL y confirmar que se rechaza;
- probar prompt injection en query y dentro de un chunk;
- probar AI Search/Workers AI caídos y confirmar que resultados locales siguen visibles;
- comprobar las tres preguntas iniciales, citas `[1]…`, botón «Detener», 320 px, 390 px, teclado, zoom 200 %, `prefers-reduced-motion` y lector de pantalla;
- actualizar y revisar `privacidad.html`;
- confirmar que AI Gateway no guarda payloads y que Unified Billing/fallback de pago no están habilitados para esta ruta;
- confirmar que `@cf/qwen/qwen3-30b-a3b-fp8` continúa disponible dentro del nivel gratuito y volver a revisar su coste en neuronas;
- confirmar que AI Search continúa dentro del nivel gratuito previsto o mantener remota desactivada;
- solo entonces integrar `/asistente/` en `content-registry`, `navigation`, sitemap y retirar `noindex`.

## Deliberadamente fuera de esta PR

- No se crean recursos Cloudflare ni secretos desde GitHub.
- No se activa el Worker.
- No se genera todavía Pagefind porque el repositorio no tiene pipeline Pagefind; el cliente ya degrada al registry sin romperse.
- No se añaden metatags `source_id/visibility` a todas las páginas; son una optimización de fase de activación, no un requisito para que el Worker sea seguro.
- No se modifica `privacidad.html` todavía porque el tratamiento remoto sigue desactivado; su actualización es gate obligatorio antes de activar.
- No se modifica `main` ni el estado de otras PR.
