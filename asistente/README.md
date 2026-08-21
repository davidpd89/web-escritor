# Asistente — ownership, activación y QA

`/asistente/` es una herramienta editorial con funcionamiento local obligatorio y respuesta remota opcional. El modo local no depende de un proveedor de IA, de Turnstile ni del Worker.

## Ownership

- `asistente/index.html`: estructura y copy de la página.
- `assets/assistant.css`: estilos propios; reutiliza los tokens y componentes V1.
- `assets/assistant-config.js`: configuración pública. `remoteEnabled` debe permanecer `false` por defecto; no contiene secretos.
- `assets/assistant-core.mjs`: contrato compartido del cliente, límites, ranking local y validación de respuestas/citas.
- `assets/assistant.js`: orquestación del navegador, Pagefind, fallback local, Turnstile y llamada remota.
- `data/assistant-source-registry.json`: **fuente canónica** de la allowlist pública del asistente.
- `assets/assistant-source-registry.js`: **generado** desde el JSON anterior. No editar a mano.
- `cloudflare-worker-assistant.js`: endpoint `/api/assistant` y `/api/assistant/config`.
- `migrations/assistant-quota.sql`: esquema D1 de cuotas diarias.

## Generación y parity

Tras modificar `data/assistant-source-registry.json`:

```bash
node scripts/build-assistant-source-registry.mjs
node scripts/build-assistant-source-registry.mjs --check
node scripts/test-assistant-index-parity.mjs
```

CI falla si el artefacto generado diverge del JSON canónico.

## Activación remota

Hay dos llaves independientes y ambas deben estar activas:

1. cliente: `ASSISTANT_PUBLIC_CONFIG.remoteEnabled = true`;
2. servidor: `ASSISTANT_ENABLED=true` y todos los bindings/secrets requeridos por el Worker.

Con cualquiera de las dos en OFF no se consume IA. El navegador nunca contiene `TURNSTILE_SECRET_KEY`, credenciales de modelo ni secretos de Cloudflare.

Antes de activar el Worker deben existir la D1 de cuotas, los tres rate limiters, AI Search, Workers AI, la site key/secret de Turnstile y `TURNSTILE_HOSTNAMES`. El modelo V1 está restringido en servidor a la allowlist `FREE_V1_MODELS`.

## Seguridad de fuentes

El Worker resuelve cada chunk contra la allowlist. Si existen a la vez `metadata.source_id` e `item.key`, ambos deben identificar la misma fuente canónica; si no, el chunk se descarta. Las URLs de las citas nunca proceden del texto del modelo. El cliente vuelve a validar IDs, rutas internas, duplicados y marcadores antes de renderizar, usando `textContent`.

## QA de merge

```bash
python3 tests/test-assistant-contract.py
node tests/test-assistant-core.mjs
node tests/test-assistant-worker.mjs
node tests/test-assistant-hardening.mjs
```

El workflow `Assistant hardening QA` añade navegador real con 7 viewports, 6 capturas, teclado, no-JS, reduced motion, text spacing/200 %, targets táctiles, modo local, modo remoto simulado, XSS, Turnstile y sentinel de fugas de consulta. Lighthouse audita `/asistente/` desde `lighthouserc.json`.
