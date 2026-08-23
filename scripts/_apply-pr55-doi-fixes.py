#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)

# Fix stale implementation comments and make the double-submit guard explicit.
worker_path = ROOT / "cloudflare-worker-subscribe.js"
worker = worker_path.read_text(encoding="utf-8")
worker = replace_once(
    worker,
    ''' *   - `listIds`, `attributes`, and `updateEnabled` are never read from the\n *     client at all — listIds comes from env.BREVO_LIST_ID, attributes is\n *     built entirely server-side from the validated source/result, and\n *     updateEnabled is hardcoded to true below.\n''',
    ''' *   - `includeListIds`, `templateId`, `redirectionUrl` and `attributes` are\n *     never accepted from the client. The list/template/redirect come from\n *     server-side configuration and attributes are built from validated enums.\n''',
    "worker stale single-opt-in comment",
)
worker_path.write_text(worker, encoding="utf-8")

script_path = ROOT / "script.js"
script = script_path.read_text(encoding="utf-8")
script = replace_once(
    script,
    '''// listIds/attributes/templateId/redirectionUrl are never client-controlled.\n// client-controlled — the Worker validates `source` against its own\n''',
    '''// listIds/attributes/templateId/redirectionUrl are never client-controlled.\n// The Worker validates `source` against its own\n''',
    "script duplicated comment",
)
script = replace_once(
    script,
    '''        statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n''',
    '''        if (subscribeForm.dataset.submitting === "true") return;\n        subscribeForm.dataset.submitting = "true";\n        statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n''',
    "quiz submitting guard",
)
script = replace_once(
    script,
    '''        } catch (err) {\n          statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = "Desbloquear mi arquetipo";\n        }\n''',
    '''        } catch (err) {\n          delete subscribeForm.dataset.submitting;\n          statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = "Desbloquear mi arquetipo";\n        }\n''',
    "quiz submitting reset",
)
script = replace_once(
    script,
    '''        if (statusEl) statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n''',
    '''        if (form.dataset.submitting === "true") return;\n        form.dataset.submitting = "true";\n        if (statusEl) statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n''',
    "generic submitting guard",
)
script = replace_once(
    script,
    '''        } catch (err) {\n          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = "Suscribirme";\n        }\n''',
    '''        } catch (err) {\n          delete form.dataset.submitting;\n          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = "Suscribirme";\n        }\n''',
    "generic submitting reset",
)
script = replace_once(
    script,
    '''      return {\n        eyebrow: "Primeros lectores de Noveris",\n        title: "Sigue el universo de Noveris.",\n        body: "Novedades sobre el universo de Noveris y avisos de nuevas firmas o lecturas. Un email cuando haya algo que valga la pena.",\n        cta: "Suscribirme",\n        okTitle: "Revisa tu correo",\n        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción.",\n        dupeTitle: "✓ Ya estás suscrito.",\n        dupeBody: "¡Gracias por seguir a David Porto Díaz!"\n      };\n''',
    '''      return {\n        eyebrow: "Primeros lectores de Noveris",\n        title: "Sigue el universo de Noveris.",\n        body: "Novedades sobre el universo de Noveris y avisos de nuevas firmas o lecturas. Un email cuando haya algo que valga la pena.",\n        cta: "Suscribirme",\n        okTitle: "Revisa tu correo",\n        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."\n      };\n''',
    "popup Noveris stale duplicate copy",
)
script = replace_once(
    script,
    '''    return {\n      eyebrow: "Novedades de David Porto Díaz",\n      title: "Sigue los próximos libros y artículos.",\n      body: "Nuevas publicaciones, artículos, firmas y recursos para lectores. Solo cuando haya algo que contar.",\n      cta: "Suscribirme",\n      okTitle: "Revisa tu correo",\n      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción.",\n      dupeTitle: "✓ Ya estás suscrito.",\n      dupeBody: "¡Gracias por seguir a David Porto Díaz!"\n    };\n''',
    '''    return {\n      eyebrow: "Novedades de David Porto Díaz",\n      title: "Sigue los próximos libros y artículos.",\n      body: "Nuevas publicaciones, artículos, firmas y recursos para lectores. Solo cuando haya algo que contar.",\n      cta: "Suscribirme",\n      okTitle: "Revisa tu correo",\n      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."\n    };\n''',
    "popup generic stale duplicate copy",
)
script = replace_once(
    script,
    '''    document.getElementById("nl-popup-form").addEventListener("submit", function (e) {\n      e.preventDefault();\n      scheduleTask(async function () {\n''',
    '''    document.getElementById("nl-popup-form").addEventListener("submit", function (e) {\n      e.preventDefault();\n      const popupForm = e.currentTarget;\n      scheduleTask(async function () {\n''',
    "popup capture form",
)
script = replace_once(
    script,
    '''        statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n          const result = await postNewsletter({\n            email: emailEl.value.trim(),\n            source: "popup",\n            website: honeypotValue(document.getElementById("nl-popup-form"))\n''',
    '''        if (popupForm.dataset.submitting === "true") return;\n        popupForm.dataset.submitting = "true";\n        statusEl.textContent = "";\n        submitBtn.disabled = true;\n        submitBtn.textContent = "Enviando…";\n        try {\n          const result = await postNewsletter({\n            email: emailEl.value.trim(),\n            source: "popup",\n            website: honeypotValue(popupForm)\n''',
    "popup submitting guard",
)
script = replace_once(
    script,
    '''        } catch (err) {\n          statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = copy.cta;\n        }\n''',
    '''        } catch (err) {\n          delete popupForm.dataset.submitting;\n          statusEl.textContent = newsletterErrorMessage(err.message);\n          submitBtn.disabled = false;\n          submitBtn.textContent = copy.cta;\n        }\n''',
    "popup submitting reset",
)
script_path.write_text(script, encoding="utf-8")

# Rewrite the implementation brief so it is a truthful current record rather
# than leaving the original KV/offscreen-honeypot instructions as if current.
brief_path = ROOT / "docs/PENDIENTE-B-BREVO-WORKER-DOI.md"
brief = '''# Pendiente B — Completar el flujo de doble confirmación de Brevo

Fecha de revisión final: 2026-08-23 · Base: `implementacion-web-2026` · Rama: `pendiente-b-brevo-worker-doi`

## Alcance

Esta PR cierra el flujo de newsletter desde el formulario hasta el retorno de confirmación sin desplegar nada ni guardar credenciales reales. Los cambios se limitan al Worker de suscripción, el cliente de newsletter en `script.js`, la página `/gracias-suscripcion/`, tests mockeados y documentación operativa.

## DOI real de Brevo

El alta inicial usa el endpoint oficial:

`POST https://api.brevo.com/v3/contacts/doubleOptinConfirmation`

El navegador solo envía `{ email, source, result?, website? }`. El Worker construye server-side:

- `includeListIds` desde `BREVO_LIST_ID`;
- `templateId` desde `BREVO_DOI_TEMPLATE_ID`;
- `redirectionUrl` desde `BREVO_DOI_REDIRECT_URL`;
- `attributes` desde las listas cerradas `SOURCE_MAP` / resultados válidos del quiz.

Una respuesta Brevo `201 Created` se traduce a `{ "ok": true, "state": "pending_confirmation" }`. Ningún 2xx inesperado se interpreta como confirmación.

El frontend no escribe `nl-subscribed=1` al enviar el formulario. Muestra «Revisa tu correo» y considera la suscripción pendiente. La escritura de `nl-subscribed=1` queda exclusivamente en `/gracias-suscripcion/`, página a la que Brevo redirige tras el clic en el email DOI.

## Página de retorno

`/gracias-suscripcion/index.html`:

- es `noindex, follow`;
- declara la suscripción confirmada;
- fija `nl-subscribed=1` antes de cargar el runtime global para impedir que el popup vuelva a aparecer tras la confirmación;
- usa el shell generado del sitio y debe seguir pasando `build-site-shell.py --check`.

## Honeypot

El campo `website` es un input de texto real para que los bots simples puedan rellenarlo, pero está dentro de un wrapper `aria-hidden` + `inert`, fuera del orden de tabulación y recortado con `clip`/`clip-path`. No usa desplazamientos negativos (`left:-9999px`) y no debe crear overflow horizontal.

Si `website` contiene texto, el Worker devuelve exactamente el mismo `201 pending_confirmation` que a una petición DOI aceptada, pero no consulta el rate limiter ni llama a Brevo.

## Rate limiting

La versión final no usa KV `get → put`. Usa el binding nativo de **Cloudflare Workers Rate Limiting** llamado `RATE_LIMITER`.

- La key es `newsletter:` + SHA-256 del email normalizado; no se envía el email en claro al limiter.
- Se evita usar una IP compartida como única key para no penalizar usuarios detrás de NAT, proxies o redes móviles.
- Si el binding devuelve `success: false`, la petición termina en `429` antes de Brevo.
- Si `RATE_LIMITER` falta, es inválido o lanza una excepción, el Worker registra de forma explícita que el rate limit está degradado y continúa. Esto evita bloquear lectores por una mala configuración, pero **la protección queda desactivada** y el despliegue no debe considerarse completo hasta verificar el binding real.

El límite efectivo (por ejemplo 5 solicitudes / 60 s) se configura en Cloudflare; no se inventa un `namespace_id` en el repositorio.

## Validación y errores

- Origin distinto de `https://davidportodiaz.com` → `403`.
- Preflight solo expone `Access-Control-Allow-Origin` para el origen permitido y añade `Vary: Origin`.
- JSON inválido / email inválido / source desconocido → `400` sin llamar a Brevo.
- Configuración Brevo incompleta o mal formada → `500` genérico y sin llamada a Brevo.
- Rate limit excedido → `429`.
- Error de red o error HTTP de Brevo → `502` genérico; el cuerpo/secretos de Brevo no se reenvían al navegador.
- Las respuestas JSON llevan `Cache-Control: no-store`.
- Los botones se deshabilitan y los tres flujos (quiz, formularios genéricos y popup) usan una guardia `data-submitting` para impedir dos POST simultáneos.

## Tests

Los tests no usan red ni credenciales reales. `globalThis.fetch` y `RATE_LIMITER` se mockean en proceso.

Cobertura focal:

- happy path DOI y payload exacto del endpoint oficial;
- rechazo de campos server-side inyectados por el cliente;
- email inválido y source inválido;
- honeypot sin llamada a Brevo ni limiter;
- rate limit permitido, bloqueado y modo degradado explícito;
- configuración incompleta de API key/list/template/redirect;
- fallo HTTP y fallo de red de Brevo sin fuga de detalles;
- `pending_confirmation` en frontend y ausencia de `nl-subscribed` antes del retorno;
- retorno `/gracias-suscripcion/` como único punto que fija estado confirmado;
- honeypot sin `left:-9999px`;
- guardia contra doble envío.

## Configuración externa pendiente

Antes de desplegar hay que completar lo documentado en `docs/BREVO-WORKER-DEPLOY.md`:

1. elegir/crear en Brevo un template DOI real y verificar que su detalle tenga `doiTemplate: true`;
2. configurar `BREVO_API_KEY`, `BREVO_LIST_ID`, `BREVO_DOI_TEMPLATE_ID` y `BREVO_DOI_REDIRECT_URL` en Cloudflare;
3. crear/configurar el binding nativo `RATE_LIMITER` con un `namespace_id` real y el límite acordado;
4. publicar primero el frontend compatible y después desplegar manualmente el Worker;
5. ejecutar un smoke test real envío → email DOI → confirmación → `/gracias-suscripcion/`.

Nada de lo anterior se despliega desde esta PR.
'''
brief_path.write_text(brief, encoding="utf-8")

# Strengthen the static frontend contract with the double-submit and stale-copy guards.
frontend_test_path = ROOT / "tests/test-newsletter-doi-frontend.mjs"
frontend_test = frontend_test_path.read_text(encoding="utf-8")
needle = "assert.ok(script.includes('setAttribute(\"inert\", \"\")'), 'dynamic honeypot must be removed from focus/a11y interaction');\n"
addition = needle + "assert.equal((script.match(/dataset\\.submitting === \\\"true\\\"/g) || []).length, 3, 'quiz, generic and popup must guard duplicate submits');\nassert.equal((script.match(/delete .*dataset\\.submitting/g) || []).length, 3, 'all submit guards must reset after failure');\nassert.ok(!script.includes('dupeTitle:'), 'single-opt-in duplicate success copy must not survive DOI migration');\n"
if frontend_test.count(needle) != 1:
    raise SystemExit("frontend test insertion point mismatch")
frontend_test = frontend_test.replace(needle, addition, 1)
frontend_test_path.write_text(frontend_test, encoding="utf-8")

print("PR55 DOI review cleanup applied")
