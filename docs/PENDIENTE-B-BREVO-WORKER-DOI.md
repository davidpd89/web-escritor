# Pendiente B — Completar el flujo de doble confirmación de Brevo

Fecha de revisión final: 2026-08-23 · Base: `implementacion-web-2026` · Rama: `pendiente-b-brevo-worker-doi`

## Alcance

Esta PR cierra el flujo de newsletter desde el formulario hasta el retorno de confirmación sin desplegar nada ni guardar credenciales reales. Los cambios se limitan al Worker de suscripción, el cliente de newsletter en `script.js`, la página `/gracias-suscripcion/`, tests mockeados y documentación operativa.

## DOI real de Brevo

El alta inicial usa `POST https://api.brevo.com/v3/contacts/doubleOptinConfirmation`.

El navegador solo envía `{ email, source, result?, website? }`. El Worker construye server-side:

- `includeListIds` desde `BREVO_LIST_ID`;
- `templateId` desde `BREVO_DOI_TEMPLATE_ID`;
- `redirectionUrl` desde `BREVO_DOI_REDIRECT_URL`;
- `attributes` desde listas cerradas de source y resultado del quiz.

Solo una respuesta Brevo `201 Created` se traduce a `{ "ok": true, "state": "pending_confirmation" }`. Ningún 2xx inesperado ni un error de «contacto existente» se interpreta como confirmación.

El frontend no escribe `nl-subscribed=1` al enviar. Muestra «Revisa tu correo» y considera la suscripción pendiente. `nl-subscribed=1` se fija únicamente en `/gracias-suscripcion/`, la página de retorno tras el clic del usuario en el email DOI.

## Página de retorno

`/gracias-suscripcion/index.html` es `noindex, follow`, declara la confirmación y fija el estado local antes de cargar el runtime global para impedir que el popup reaparezca. Usa el shell del sitio y queda sujeto al builder existente.

## Honeypot

`website` sigue siendo un input de texto para bots simples, pero vive en un wrapper `aria-hidden` + `inert`, fuera de tabulación y recortado con `clip`/`clip-path`. No usa `left:-9999px` ni crea overflow horizontal.

Si llega relleno, el Worker devuelve el mismo `201 pending_confirmation` externo que una petición DOI aceptada y no llama ni al limiter ni a Brevo.

## Rate limiting

No se usa KV `get → put`. Se usa el binding nativo de Cloudflare Workers Rate Limiting `RATE_LIMITER`.

- key: `newsletter:` + SHA-256 del email normalizado; el limiter no recibe el email en claro;
- no se usa una IP compartida como única clave;
- `success:false` → `429` antes de Brevo;
- binding ausente, inválido o con excepción → log explícito y fail-open para no bloquear lectores por un error de despliegue. En ese estado la protección está desactivada y el despliegue no debe considerarse completo.

El límite y `namespace_id` se configuran con valores reales en Cloudflare; no se inventan en el repositorio.

## Validación, privacidad y errores

- Origin distinto del sitio → `403`; CORS solo expone `Access-Control-Allow-Origin` al origen permitido y añade `Vary: Origin`.
- JSON, email o source inválidos → `400` sin Brevo.
- Configuración Brevo incompleta → `500` genérico, sin Brevo.
- Rate limit → `429`.
- Error de red, error HTTP de Brevo o 2xx inesperado → `502` genérico.
- El body de error de Brevo no debe reenviarse ni registrarse: puede contener PII o detalles del proveedor.
- Las respuestas JSON llevan `Cache-Control: no-store`.
- Quiz, formularios y popup usan una guardia de envío para impedir POST simultáneos.

## Tests mockeados

Sin red ni credenciales reales. Cobertura exigida: DOI happy path y payload, CORS, email/source inválidos, honeypot, limiter permitido/bloqueado/degradado, configuración incompleta, error/duplicado de Brevo sin fuga, quiz válido/inválido/no-quiz, semántica `pending_confirmation`, retorno confirmado, honeypot sin overflow, doble envío, Sitewide Reflow y tests generales afectados.

## Configuración externa pendiente antes de desplegar

1. elegir o crear un template DOI real en Brevo y verificar que su detalle tenga `doiTemplate: true`;
2. configurar `BREVO_API_KEY`, `BREVO_LIST_ID`, `BREVO_DOI_TEMPLATE_ID` y `BREVO_DOI_REDIRECT_URL` en Cloudflare;
3. crear/configurar `RATE_LIMITER` con `namespace_id` real y el límite acordado;
4. publicar primero el frontend compatible y después desplegar manualmente el Worker;
5. smoke test real: envío → email DOI → clic → `/gracias-suscripcion/`.

Nada de lo anterior se despliega desde esta PR.
