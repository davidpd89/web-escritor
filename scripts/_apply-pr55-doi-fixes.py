#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 regex match, found {count}")
    return new


# ---------------------------------------------------------------------------
# Worker: preserve the existing file/history comments, replace only the DOI,
# config, CORS and rate-limit mechanics that are wrong in PR #55.
# ---------------------------------------------------------------------------
worker_path = ROOT / "cloudflare-worker-subscribe.js"
worker = worker_path.read_text(encoding="utf-8")

worker = replace_once(
    worker,
    ''' *   6. Settings → KV Namespace Bindings → Add binding:\n *        Variable name: RATE_LIMIT_KV\n *        KV namespace:  (namespace real creado en Cloudflare)\n *   7. Copy the Worker URL (e.g. https://subscribe.davidportodiaz.workers.dev)\n *   8. Update WORKER_URL in script.js with that URL\n''',
    ''' *   6. Settings → Variables and Secrets → Add variable:\n *        Name:  BREVO_DOI_TEMPLATE_ID\n *        Value: (ID numérico de un template Brevo válido para DOI; no se guarda en el repo)\n *   7. Add a Cloudflare Workers Rate Limiting binding:\n *        Binding name: RATE_LIMITER\n *        Configure e.g. 5 requests / 60 s and choose the namespace_id in Cloudflare.\n *   8. Copy the Worker URL (e.g. https://subscribe.davidportodiaz.workers.dev)\n *   9. Update WORKER_URL in script.js with that URL\n''',
    "worker deployment bindings",
)
worker = replace_once(
    worker,
    ''' * SECURITY NOTE (2026-08-20): the client input contract is now minimal by\n * design — the browser sends only { email, source, result? }. Previously\n''',
    ''' * SECURITY NOTE (2026-08-20): the client input contract is now minimal by\n * design — the browser sends only { email, source, result?, website? }. `website`\n * is a honeypot and is never forwarded. Previously\n''',
    "worker minimal contract comment",
)
worker = replace_once(
    worker,
    ''' * NOTE ON ABUSE PROTECTION: the Origin check + CORS headers below stop\n * cross-site browser requests, but they are NOT rate limiting or bot\n * protection — a direct POST from a script (no browser, no Origin header\n * enforcement bypassable by omitting Origin entirely triggers the 403\n * below, but a non-browser client can still just spoof the Origin header)\n * can still hit this endpoint repeatedly. If abuse becomes a real problem,\n * add Turnstile and/or a KV-backed rate limit; neither is implemented here\n * to keep this pass scoped to the input-contract fix.\n''',
    ''' * NOTE ON ABUSE PROTECTION: Origin/CORS are not bot protection. This Worker\n * uses a honeypot plus Cloudflare's native Rate Limiting binding. If RATE_LIMITER\n * is missing, malformed or throws, the Worker logs the degraded state and fails\n * open so a configuration error does not block legitimate readers; production\n * deployment must therefore verify the binding instead of assuming it exists.\n''',
    "worker abuse note",
)
worker = replace_once(
    worker,
    '''const ALLOWED_ORIGIN = "https://davidportodiaz.com";\nconst RATE_LIMIT_MAX_ATTEMPTS = 5;\nconst RATE_LIMIT_WINDOW_SECONDS = 10 * 60;\n''',
    '''const ALLOWED_ORIGIN = "https://davidportodiaz.com";\nconst BREVO_DOI_ENDPOINT = "https://api.brevo.com/v3/contacts/doubleOptinConfirmation";\nconst PENDING_CONFIRMATION_BODY = Object.freeze({ ok: true, state: "pending_confirmation" });\nconst EMAIL_RE = /^[^\\s@]{1,64}@[^\\s@]{1,253}\\.[^\\s@]{2,}$/;\n''',
    "worker constants",
)

new_handler_tail = r'''    let body;
    try {
      body = await request.json();
    } catch {
      return jsonResponse(origin, 400, { ok: false, message: "Solicitud no válida." });
    }

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return jsonResponse(origin, 400, { ok: false, message: "Solicitud no válida." });
    }

    // Minimal client contract: email/source/result/website only. `website` is
    // the honeypot and is never forwarded to Brevo.
    const { email, source, result, website } = body;

    // Honeypot responses intentionally match a legitimate accepted DOI request,
    // while skipping both Brevo and rate limiting.
    if (typeof website === "string" && website.trim() !== "") {
      return pendingConfirmationResponse(origin);
    }

    const normalizedEmail = typeof email === "string" ? email.trim() : "";
    if (!EMAIL_RE.test(normalizedEmail)) {
      return jsonResponse(origin, 400, { ok: false, message: "Dirección de email no válida." });
    }

    if (typeof source !== "string" || !Object.prototype.hasOwnProperty.call(SOURCE_MAP, source)) {
      return jsonResponse(origin, 400, { ok: false, message: "Origen de suscripción no válido." });
    }

    const config = validateBrevoConfig(env);
    if (!config.ok) {
      console.error(`Worker misconfigured: ${config.reason}`);
      return jsonResponse(origin, 500, { ok: false, message: "Servicio no disponible temporalmente." });
    }

    const rateLimit = await checkRateLimit(env, normalizedEmail);
    if (!rateLimit.allowed) {
      return jsonResponse(origin, 429, {
        ok: false,
        message: "Has hecho demasiados intentos. Inténtalo de nuevo más tarde.",
      });
    }

    const attributes = { SOURCE: SOURCE_MAP[source] };
    if (source === "quiz" && typeof result === "string" && NOVERIS_RESULTS.has(result)) {
      attributes.NOVERIS = result;
    }

    const brevoPayload = {
      email: normalizedEmail,
      includeListIds: [config.listId],
      redirectionUrl: config.redirectUrl,
      templateId: config.templateId,
      attributes,
    };

    let brevoRes;
    try {
      brevoRes = await fetch(BREVO_DOI_ENDPOINT, {
        method: "POST",
        headers: {
          "api-key": config.apiKey,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(brevoPayload),
      });
    } catch (err) {
      console.error("Brevo DOI request failed:", err);
      return jsonResponse(origin, 502, {
        ok: false,
        message: "No se ha podido iniciar la confirmación. Inténtalo de nuevo más tarde.",
      });
    }

    // Brevo documents 201 Created for createDoiContact. Do not accept another
    // 2xx as a valid DOI transition: an unexpected upstream contract must not
    // become a false pending/confirmed state in the browser.
    if (brevoRes.status === 201) {
      return pendingConfirmationResponse(origin);
    }

    let brevoBodyText = "";
    try {
      brevoBodyText = await brevoRes.text();
    } catch {
      // Best effort only. Upstream details are never forwarded to the browser.
    }
    console.error(`Brevo DOI error ${brevoRes.status}:`, brevoBodyText.slice(0, 500));
    return jsonResponse(origin, 502, {
      ok: false,
      message: "No se ha podido iniciar la confirmación. Inténtalo de nuevo más tarde.",
    });
  },
};'''
worker = regex_once(
    worker,
    r'''    const clientIp = getClientIp\(request\);.*?\n  \},\n\};''',
    new_handler_tail,
    "worker fetch DOI flow",
)

worker = replace_once(
    worker,
    '''function jsonResponse(origin, status, bodyObj) {\n  return new Response(JSON.stringify(bodyObj), {\n    status,\n    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },\n  });\n}\n\nfunction corsHeaders(origin) {\n  return {\n    "Access-Control-Allow-Origin": origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : "",\n    "Access-Control-Allow-Methods": "POST, OPTIONS",\n    "Access-Control-Allow-Headers": "Content-Type",\n    "Access-Control-Max-Age": "86400",\n  };\n}\n\nfunction getClientIp(request) {\n  return (\n    request.headers.get("CF-Connecting-IP") ||\n    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||\n    "unknown"\n  );\n}\n\nasync function isRateLimitAllowed(env, clientIp) {\n  const kv = env?.RATE_LIMIT_KV;\n  if (!kv || typeof kv.get !== "function" || typeof kv.put !== "function") {\n    return true;\n  }\n\n  const key = `newsletter:${clientIp}`;\n  let current = 0;\n  try {\n    const raw = await kv.get(key);\n    const parsed = Number.parseInt(raw || "0", 10);\n    current = Number.isFinite(parsed) && parsed > 0 ? parsed : 0;\n  } catch {\n    return true;\n  }\n\n  if (current >= RATE_LIMIT_MAX_ATTEMPTS) {\n    return false;\n  }\n\n  try {\n    await kv.put(key, String(current + 1), { expirationTtl: RATE_LIMIT_WINDOW_SECONDS });\n  } catch {\n    return true;\n  }\n  return true;\n}\n''',
    r'''function validateBrevoConfig(env) {
  const apiKey = typeof env?.BREVO_API_KEY === "string" ? env.BREVO_API_KEY.trim() : "";
  if (!apiKey) return { ok: false, reason: "BREVO_API_KEY missing" };

  const listId = Number(env?.BREVO_LIST_ID);
  if (!Number.isInteger(listId) || listId <= 0) {
    return { ok: false, reason: "BREVO_LIST_ID must be a positive integer" };
  }

  const templateId = Number(env?.BREVO_DOI_TEMPLATE_ID);
  if (!Number.isInteger(templateId) || templateId <= 0) {
    return { ok: false, reason: "BREVO_DOI_TEMPLATE_ID must be a positive integer" };
  }

  const redirectValue = typeof env?.BREVO_DOI_REDIRECT_URL === "string"
    ? env.BREVO_DOI_REDIRECT_URL.trim()
    : "";
  let redirect;
  try {
    redirect = new URL(redirectValue);
  } catch {
    return { ok: false, reason: "BREVO_DOI_REDIRECT_URL must be a valid HTTPS URL" };
  }
  if (redirect.protocol !== "https:" || redirect.username || redirect.password) {
    return { ok: false, reason: "BREVO_DOI_REDIRECT_URL must be a credential-free HTTPS URL" };
  }

  return { ok: true, apiKey, listId, templateId, redirectUrl: redirect.href };
}

async function checkRateLimit(env, email) {
  const limiter = env?.RATE_LIMITER;
  if (!limiter || typeof limiter.limit !== "function") {
    console.error("Worker misconfigured: RATE_LIMITER binding missing; continuing without rate limiting");
    return { allowed: true, enforced: false };
  }

  const key = await rateLimitKey(email);
  try {
    const result = await limiter.limit({ key });
    if (!result || typeof result.success !== "boolean") {
      console.error("RATE_LIMITER returned an invalid result; continuing without rate limiting");
      return { allowed: true, enforced: false };
    }
    return { allowed: result.success, enforced: true };
  } catch (err) {
    console.error("RATE_LIMITER failed; continuing without rate limiting:", err);
    return { allowed: true, enforced: false };
  }
}

async function rateLimitKey(email) {
  const normalized = email.trim().toLowerCase();
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  const hash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
  return `newsletter:${hash}`;
}

function pendingConfirmationResponse(origin) {
  return jsonResponse(origin, 201, PENDING_CONFIRMATION_BODY);
}

function jsonResponse(origin, status, bodyObj) {
  return new Response(JSON.stringify(bodyObj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...corsHeaders(origin),
    },
  });
}

function corsHeaders(origin) {
  const headers = {
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
  if (origin === ALLOWED_ORIGIN) {
    headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN;
  }
  return headers;
}
''',
    "worker helpers",
)
worker_path.write_text(worker, encoding="utf-8")

# ---------------------------------------------------------------------------
# Frontend: pending != confirmed, safe honeypot geometry, no nl-subscribed set
# until the Brevo redirect page is reached.
# ---------------------------------------------------------------------------
script_path = ROOT / "script.js"
script = script_path.read_text(encoding="utf-8")
script = replace_once(
    script,
    '''// Client contract (2026-08-20): only { email, source, result? } is ever\n// sent to the Worker. listIds/attributes/updateEnabled are no longer\n''',
    '''// Client contract (2026-08-23): only { email, source, result?, website? } is ever\n// sent to the Worker. `website` is a honeypot and is never forwarded by the Worker.\n// listIds/attributes/templateId/redirectionUrl are never client-controlled.\n''',
    "script client contract comment",
)
script = replace_once(
    script,
    '''function honeypotValue(form) {\n  const field = form?.querySelector('input[name="website"]');\n  return field ? String(field.value || "").trim() : "";\n}\n''',
    '''function honeypotValue(form) {\n  const field = form?.querySelector('input[name="website"]');\n  return field ? String(field.value || "").trim() : "";\n}\n\nfunction installNewsletterHoneypot(form) {\n  if (!form || form.querySelector('input[name="website"]')) return;\n  const wrapper = document.createElement("div");\n  wrapper.setAttribute("aria-hidden", "true");\n  wrapper.setAttribute("inert", "");\n  wrapper.style.cssText = "position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;";\n  const field = document.createElement("input");\n  field.type = "text";\n  field.name = "website";\n  field.autocomplete = "off";\n  field.tabIndex = -1;\n  wrapper.appendChild(field);\n  form.appendChild(wrapper);\n}\n''',
    "script honeypot helper",
)
script = replace_once(
    script,
    '''    if (res.ok || res.status === 204) return { ok: true, code: "ok" };\n\n    if (res.status === 400) {\n      const body = await res.json().catch(() => ({}));\n      if (body.duplicate === true) return { ok: true, duplicate: true, code: "duplicate" };\n      return { ok: false, code: "invalid_request" };\n    }\n''',
    '''    if (res.ok) {\n      const body = await res.json().catch(() => ({}));\n      if (body && body.ok === true && body.state === "pending_confirmation") {\n        return { ok: true, state: "pending_confirmation", code: "pending_confirmation" };\n      }\n      return { ok: false, code: "invalid_response" };\n    }\n\n    if (res.status === 400) return { ok: false, code: "invalid_request" };\n''',
    "script pending response contract",
)
script = replace_once(
    script,
    '''  if (subscribeForm) {\n    subscribeForm.addEventListener("submit", (e) => {\n''',
    '''  if (subscribeForm) {\n    installNewsletterHoneypot(subscribeForm);\n    subscribeForm.addEventListener("submit", (e) => {\n''',
    "quiz honeypot install",
)
script = replace_once(
    script,
    '''          if (result.ok && !result.duplicate) {\n            localStorage.setItem("nl-subscribed", "1");\n            subscribeForm.dataset.done = "true";\n            subscribeForm.innerHTML = '<p class="quiz-subscribe-ok">✓ ¡Apuntado! Recibirás las novedades de Noveris.</p>';\n            _gcEvent("newsletter-quiz", "Newsletter: quiz Noveris");\n            setResultLocked(false);\n          } else if (result.ok && result.duplicate) {\n            localStorage.setItem("nl-subscribed", "1");\n            subscribeForm.dataset.done = "true";\n            subscribeForm.innerHTML = '<p class="quiz-subscribe-ok">✓ Ya estás suscrito. ¡Gracias!</p>';\n            setResultLocked(false);\n          } else {\n''',
    '''          if (result.ok && result.state === "pending_confirmation") {\n            subscribeForm.dataset.done = "true";\n            subscribeForm.innerHTML = '<p class="quiz-subscribe-ok">✓ Revisa tu correo y abre el enlace de confirmación para completar la suscripción.</p>';\n            _gcEvent("newsletter-pending-quiz", "Newsletter DOI pendiente: quiz Noveris");\n            setResultLocked(false);\n          } else {\n''',
    "quiz pending UI",
)
script = replace_once(
    script,
    '''  const NEWSLETTER_SUCCESS_COPY = {\n    home: "Te has suscrito correctamente. Recibirás las novedades de David Porto Díaz.",\n    fragmento: "Te has suscrito correctamente. Recibirás las novedades de David Porto Díaz.",\n    manecillas: "Te avisaré cuando Las manecillas del recuerdo esté disponible.",\n    cuaderno: "Te has suscrito correctamente. Recibirás las novedades de David Porto Díaz."\n  };\n''',
    '''  const NEWSLETTER_PENDING_COPY = {\n    home: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.",\n    fragmento: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.",\n    manecillas: "Revisa tu correo y confirma la suscripción. Después te avisaré cuando Las manecillas del recuerdo esté disponible.",\n    cuaderno: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz."\n  };\n''',
    "generic pending copy",
)
script = replace_once(
    script,
    '''    if (!form.querySelector('input[name="website"]')) {\n      const hp = document.createElement("input");\n      hp.type = "text";\n      hp.name = "website";\n      hp.autocomplete = "off";\n      hp.tabIndex = -1;\n      hp.setAttribute("aria-hidden", "true");\n      hp.style.cssText = "position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;";\n      form.appendChild(hp);\n    }\n    const successBody = NEWSLETTER_SUCCESS_COPY[sourceLabel] || "Recibirás las novedades de David Porto Díaz.";\n''',
    '''    installNewsletterHoneypot(form);\n    const pendingBody = NEWSLETTER_PENDING_COPY[sourceLabel] || "Revisa tu correo y confirma la suscripción para completarla.";\n''',
    "generic safe honeypot",
)
script = replace_once(
    script,
    '''          if (result.ok && !result.duplicate) {\n            localStorage.setItem("nl-subscribed", "1");\n            form.innerHTML = '<p class="quiz-subscribe-ok">✓ ¡Apuntado! ' + successBody + '</p>';\n            _gcEvent("newsletter-" + sourceLabel, "Newsletter: " + sourceLabel);\n          } else if (result.ok && result.duplicate) {\n            localStorage.setItem("nl-subscribed", "1");\n            form.innerHTML = '<p class="quiz-subscribe-ok">\\u2714 Ya est\\u00e1s suscrito a la lista. \\u00a1Gracias!</p>';\n          } else {\n''',
    '''          if (result.ok && result.state === "pending_confirmation") {\n            form.innerHTML = '<p class="quiz-subscribe-ok">✓ ' + pendingBody + '</p>';\n            _gcEvent("newsletter-pending-" + sourceLabel, "Newsletter DOI pendiente: " + sourceLabel);\n          } else {\n''',
    "generic pending UI",
)
script = script.replace(
    'okTitle: "✓ ¡Apuntado!",\n        okBody: "Recibirás las novedades de David Porto Díaz sobre el universo de Noveris."',
    'okTitle: "Revisa tu correo",\n        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."',
    1,
)
script = script.replace(
    'okTitle: "✓ ¡Apuntado!",\n      okBody: "Recibirás las novedades de David Porto Díaz."',
    'okTitle: "Revisa tu correo",\n      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."',
    1,
)
if script.count('okTitle: "Revisa tu correo"') != 2:
    raise SystemExit("popup pending copy: expected both contexts")
script = replace_once(
    script,
    '''      '<input type="text" id="nl-popup-website" name="website" autocomplete="off" tabindex="-1" aria-hidden="true" style="position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden;" />' +\n''',
    '''      '<div aria-hidden="true" inert style="position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;"><input type="text" id="nl-popup-website" name="website" autocomplete="off" tabindex="-1" /></div>' +\n''',
    "popup safe honeypot",
)
script = replace_once(
    script,
    '''          if (result.ok && !result.duplicate) {\n            localStorage.setItem(SUBSCRIBED_KEY, "1");\n            const panel = document.getElementById("nl-popup-panel");\n            panel.innerHTML = '<p style="font-family:Cormorant Garamond,Georgia,serif;font-size:1.5rem;color:#e0b979;text-align:center;margin:0 0 10px">' + copy.okTitle + '</p><p style="color:#b6a894;text-align:center;font-size:0.94rem;margin:0">' + copy.okBody + '</p>';\n            _gcEvent("newsletter-popup", "Newsletter: popup");\n            setTimeout(dismiss, 3200);\n          } else if (result.ok && result.duplicate) {\n            localStorage.setItem(SUBSCRIBED_KEY, "1");\n            const panel = document.getElementById("nl-popup-panel");\n            panel.innerHTML = '<p style="font-family:Cormorant Garamond,Georgia,serif;font-size:1.5rem;color:#e0b979;text-align:center;margin:0 0 10px">' + copy.dupeTitle + '</p><p style="color:#b6a894;text-align:center;font-size:0.94rem;margin:0">' + copy.dupeBody + '</p>';\n            setTimeout(dismiss, 3200);\n          } else {\n''',
    '''          if (result.ok && result.state === "pending_confirmation") {\n            const panel = document.getElementById("nl-popup-panel");\n            panel.innerHTML = '<p style="font-family:Cormorant Garamond,Georgia,serif;font-size:1.5rem;color:#e0b979;text-align:center;margin:0 0 10px">' + copy.okTitle + '</p><p style="color:#b6a894;text-align:center;font-size:0.94rem;margin:0">' + copy.okBody + '</p>';\n            _gcEvent("newsletter-pending-popup", "Newsletter DOI pendiente: popup");\n            setTimeout(dismiss, 5000);\n          } else {\n''',
    "popup pending UI",
)
if 'left:-9999px' in script:
    raise SystemExit("unsafe offscreen honeypot remains in script.js")
if 'localStorage.setItem("nl-subscribed", "1")' in script or 'localStorage.setItem(SUBSCRIBED_KEY, "1")' in script:
    raise SystemExit("script.js still marks newsletter as confirmed before DOI return")
script_path.write_text(script, encoding="utf-8")

# ---------------------------------------------------------------------------
# Worker contract tests: fully mocked; no network or real credentials.
# ---------------------------------------------------------------------------
worker_test = r'''// Contract tests for the newsletter Worker. No real Brevo or Cloudflare calls.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import worker from '../cloudflare-worker-subscribe.js';

const ALLOWED_ORIGIN = 'https://davidportodiaz.com';
const DOI_ENDPOINT = 'https://api.brevo.com/v3/contacts/doubleOptinConfirmation';
const REDIRECT_URL = 'https://davidportodiaz.com/gracias-suscripcion/';

function makeRateLimiter({ success = true, throwError = null, result = null } = {}) {
  const calls = [];
  return {
    calls,
    async limit(input) {
      calls.push(input);
      if (throwError) throw throwError;
      return result ?? { success };
    },
  };
}

function makeEnv(overrides = {}) {
  return {
    BREVO_API_KEY: 'test-api-key',
    BREVO_LIST_ID: '3',
    BREVO_DOI_TEMPLATE_ID: '42',
    BREVO_DOI_REDIRECT_URL: REDIRECT_URL,
    RATE_LIMITER: makeRateLimiter(),
    ...overrides,
  };
}

function makeRequest(body, { method = 'POST', origin = ALLOWED_ORIGIN } = {}) {
  const init = { method, headers: { Origin: origin, 'Content-Type': 'application/json' } };
  if (body !== undefined && method !== 'OPTIONS' && method !== 'GET') {
    init.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  return new Request('https://subscribe.example.workers.dev/', init);
}

function withMockedBrevoFetch(fakeStatus, fakeBody, fn, { throwError = null } = {}) {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    if (throwError) throw throwError;
    const body = fakeStatus === 204 ? null : JSON.stringify(fakeBody ?? {});
    return new Response(body, { status: fakeStatus, headers: { 'Content-Type': 'application/json' } });
  };
  return Promise.resolve(fn(calls)).finally(() => { globalThis.fetch = originalFetch; });
}

async function run() {
  const source = await fs.readFile(new URL('../cloudflare-worker-subscribe.js', import.meta.url), 'utf8');
  assert.ok(source.includes('/v3/contacts/doubleOptinConfirmation'));
  assert.ok(!source.includes('fetch("https://api.brevo.com/v3/contacts"'));

  let res = await worker.fetch(makeRequest(undefined, { method: 'OPTIONS' }), makeEnv());
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('Access-Control-Allow-Origin'), ALLOWED_ORIGIN);
  assert.equal(res.headers.get('Vary'), 'Origin');

  res = await worker.fetch(makeRequest(undefined, { method: 'OPTIONS', origin: 'https://evil.example' }), makeEnv());
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('Access-Control-Allow-Origin'), null);

  res = await worker.fetch(makeRequest(undefined, { method: 'GET' }), makeEnv());
  assert.equal(res.status, 405);
  res = await worker.fetch(makeRequest({ email: 'a@b.com', source: 'home' }, { origin: 'https://evil.example' }), makeEnv());
  assert.equal(res.status, 403);

  res = await worker.fetch(makeRequest('{not json'), makeEnv());
  assert.equal(res.status, 400);
  for (const invalid of [
    { source: 'home' },
    { email: 'not-an-email', source: 'home' },
    { email: 'a@b.com', source: 'unknown-source' },
  ]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(makeRequest(invalid), makeEnv()).then(r => {
      assert.equal(calls.length, 0); return r;
    }));
    assert.equal(res.status, 400);
  }

  for (const [name, value] of [
    ['BREVO_API_KEY', undefined],
    ['BREVO_LIST_ID', undefined], ['BREVO_LIST_ID', 'bad'],
    ['BREVO_DOI_TEMPLATE_ID', undefined], ['BREVO_DOI_TEMPLATE_ID', '0'],
    ['BREVO_DOI_REDIRECT_URL', undefined],
    ['BREVO_DOI_REDIRECT_URL', 'http://davidportodiaz.com/gracias-suscripcion/'],
    ['BREVO_DOI_REDIRECT_URL', 'not-a-url'],
  ]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(
      makeRequest({ email: 'config@example.com', source: 'home' }), makeEnv({ [name]: value })
    ).then(r => { assert.equal(calls.length, 0); return r; }));
    assert.equal(res.status, 500, `${name}=${String(value)}`);
  }

  const limiter = makeRateLimiter();
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({
      email: ' Reader@Example.com ', source: 'home', listIds: [999], includeListIds: [999],
      templateId: 999, redirectionUrl: 'https://evil.example/',
      attributes: { SOURCE: 'attacker', ADMIN: true }, updateEnabled: true,
    }), makeEnv({ RATE_LIMITER: limiter }));
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, DOI_ENDPOINT);
    const forwarded = JSON.parse(calls[0].init.body);
    assert.deepEqual(forwarded, {
      email: 'Reader@Example.com', includeListIds: [3], redirectionUrl: REDIRECT_URL,
      templateId: 42, attributes: { SOURCE: 'home' },
    });
    assert.equal('listIds' in forwarded, false);
    assert.equal('updateEnabled' in forwarded, false);
    return response;
  });
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });
  assert.equal(limiter.calls.length, 1);
  assert.match(limiter.calls[0].key, /^newsletter:[a-f0-9]{64}$/);
  assert.ok(!limiter.calls[0].key.includes('Reader@Example.com'));

  await withMockedBrevoFetch(201, {}, async calls => {
    await worker.fetch(makeRequest({ email: 'quiz@example.com', source: 'quiz', result: 'sabio' }), makeEnv());
    assert.deepEqual(JSON.parse(calls[0].init.body).attributes, { SOURCE: 'quiz-noveris', NOVERIS: 'sabio' });
  });
  await withMockedBrevoFetch(201, {}, async calls => {
    await worker.fetch(makeRequest({ email: 'quiz2@example.com', source: 'quiz', result: '<script>' }), makeEnv());
    assert.deepEqual(JSON.parse(calls[0].init.body).attributes, { SOURCE: 'quiz-noveris' });
  });

  const hpLimiter = makeRateLimiter({ success: false });
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({ email: 'bot@example.com', source: 'home', website: 'spam' }), makeEnv({ RATE_LIMITER: hpLimiter }));
    assert.equal(calls.length, 0); return response;
  });
  assert.equal(hpLimiter.calls.length, 0);
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { ok: true, state: 'pending_confirmation' });

  const blockedLimiter = makeRateLimiter({ success: false });
  res = await withMockedBrevoFetch(201, {}, async calls => {
    const response = await worker.fetch(makeRequest({ email: 'limited@example.com', source: 'home' }), makeEnv({ RATE_LIMITER: blockedLimiter }));
    assert.equal(calls.length, 0); return response;
  });
  assert.equal(res.status, 429);

  for (const rateOverride of [undefined, {}, makeRateLimiter({ throwError: new Error('binding unavailable') }), makeRateLimiter({ result: {} })]) {
    res = await withMockedBrevoFetch(201, {}, calls => worker.fetch(
      makeRequest({ email: 'degraded@example.com', source: 'home' }), makeEnv({ RATE_LIMITER: rateOverride })
    ).then(r => { assert.equal(calls.length, 1); return r; }));
    assert.equal(res.status, 201);
  }

  res = await withMockedBrevoFetch(401, { code: 'unauthorized', message: 'xkeysib-SECRETVALUE' }, () =>
    worker.fetch(makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv())
  );
  assert.equal(res.status, 502);
  const safeError = JSON.stringify(await res.json());
  assert.ok(!safeError.includes('SECRETVALUE'));
  assert.ok(!safeError.includes('unauthorized'));

  res = await withMockedBrevoFetch(201, {}, () => worker.fetch(
    makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv()
  ), { throwError: new Error('network down') });
  assert.equal(res.status, 502);

  res = await withMockedBrevoFetch(204, undefined, () => worker.fetch(
    makeRequest({ email: 'reader@example.com', source: 'home' }), makeEnv()
  ));
  assert.equal(res.status, 502);

  console.log('test-cloudflare-worker-subscribe: all assertions passed');
}
await run();
'''
(ROOT / "tests/test-cloudflare-worker-subscribe.mjs").write_text(worker_test, encoding="utf-8")

frontend_test = r'''import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const script = await fs.readFile(new URL('../script.js', import.meta.url), 'utf8');
const thanks = await fs.readFile(new URL('../gracias-suscripcion/index.html', import.meta.url), 'utf8');

assert.ok(script.includes('state === "pending_confirmation"'), 'frontend must require pending_confirmation');
assert.ok(script.includes('Revisa tu correo'), 'pending DOI copy must be visible');
assert.ok(!script.includes('localStorage.setItem("nl-subscribed", "1")'), 'initial submit must not mark confirmed');
assert.ok(!script.includes('localStorage.setItem(SUBSCRIBED_KEY, "1")'), 'popup submit must not mark confirmed');
assert.ok(!script.includes('left:-9999px'), 'honeypot must not create offscreen reflow');
assert.ok(script.includes('clip-path:inset(50%)'), 'honeypot uses clipped in-layout geometry');
assert.ok(script.includes('setAttribute("inert", "")'), 'dynamic honeypot must be removed from focus/a11y interaction');

assert.match(thanks, /<meta name="robots" content="noindex, follow"/);
assert.ok(thanks.includes('localStorage.setItem("nl-subscribed", "1")'), 'DOI return marks browser confirmed');
assert.ok(thanks.indexOf('localStorage.setItem("nl-subscribed", "1")') < thanks.indexOf('/script.js'), 'confirmed state must be set before global runtime');
assert.ok(thanks.includes('Suscripción confirmada'));

console.log('test-newsletter-doi-frontend: all assertions passed');
'''
(ROOT / "tests/test-newsletter-doi-frontend.mjs").write_text(frontend_test, encoding="utf-8")

# ---------------------------------------------------------------------------
# Deployment documentation: no invented IDs/secrets; explicit degraded mode.
# ---------------------------------------------------------------------------
deploy = '''# Brevo Worker: despliegue pendiente tras PR55

Esta PR deja preparado el flujo DOI real, pero el despliegue en Cloudflare y la configuración de Brevo siguen siendo manuales y quedan fuera del repositorio.

## Variables y bindings requeridos

- `BREVO_API_KEY` (secret): clave API de Brevo.
- `BREVO_LIST_ID` (variable): ID numérico de la lista canónica. No se inventa ni se fija uno nuevo en esta PR.
- `BREVO_DOI_TEMPLATE_ID` (variable): ID numérico de un template de Brevo válido para double opt-in (`doiTemplate: true`). Debe elegirse/configurarse en la cuenta real.
- `BREVO_DOI_REDIRECT_URL` (variable): `https://davidportodiaz.com/gracias-suscripcion/`.
- `RATE_LIMITER` (binding nativo de **Cloudflare Workers Rate Limiting**): configurar en Cloudflare, por ejemplo 5 solicitudes por 60 segundos. `namespace_id` debe ser un entero positivo único elegido en la cuenta real; no se guarda un ID inventado en el repo.

El Worker usa `POST https://api.brevo.com/v3/contacts/doubleOptinConfirmation`. El navegador nunca envía `listIds`, `templateId`, `redirectionUrl` ni atributos arbitrarios: lista, template y redirect son configuración server-side.

## Rate limiting y modo degradado

El binding `RATE_LIMITER` es la protección de rate limit. Si falta, no expone `.limit()` o lanza una excepción, el Worker **lo registra como error de configuración y continúa sin rate limit**. Ese fail-open es deliberado para no bloquear lectores legítimos por un error de despliegue, pero significa que la protección está desactivada: antes de publicar hay que verificar el binding real. No se debe considerar el Worker protegido solo porque el código contenga la llamada.

La clave enviada al limiter es un SHA-256 del email normalizado, no el email en claro y no una IP compartida.

## Gates externos antes de desplegar

1. Crear/elegir un template DOI real en Brevo y verificar que sea DOI-compatible (`doiTemplate: true`).
2. Configurar `BREVO_DOI_TEMPLATE_ID`, `BREVO_LIST_ID`, `BREVO_DOI_REDIRECT_URL` y el secret `BREVO_API_KEY` en Cloudflare.
3. Crear/configurar el binding `RATE_LIMITER` con un `namespace_id` real del account y el límite acordado.
4. Desplegar manualmente el Worker solo después de que el frontend compatible esté en producción.
5. Hacer un smoke test real con un email de prueba: envío → email DOI → clic de confirmación → `/gracias-suscripcion/`.

Los tests del repositorio usan mocks y no envían emails ni contienen credenciales reales.
'''
(ROOT / "docs/BREVO-WORKER-DEPLOY.md").write_text(deploy, encoding="utf-8")

brief_path = ROOT / "docs/PENDIENTE-B-BREVO-WORKER-DOI.md"
brief = brief_path.read_text(encoding="utf-8")
marker = "# Pendiente B — Completar el flujo de doble confirmación de Brevo\n"
if marker not in brief:
    raise SystemExit("brief heading not found")
closure = '''# Pendiente B — Completar el flujo de doble confirmación de Brevo

> **Actualización de revisión 23/08/2026.** La implementación final de esta PR usa el endpoint DOI oficial `POST /v3/contacts/doubleOptinConfirmation`, con `BREVO_DOI_TEMPLATE_ID`, `BREVO_LIST_ID` y `BREVO_DOI_REDIRECT_URL` configurados server-side. El rate limit KV descrito en el borrador original queda sustituido por el binding nativo `RATE_LIMITER` de Cloudflare Workers. El honeypot ya no se desplaza a `left:-9999px`: usa clipping + `inert` sin overflow. Tras el POST el estado es `pending_confirmation`; `nl-subscribed=1` solo se fija en la página de retorno tras confirmar el email.
'''
brief = brief.replace(marker, closure, 1)
brief = brief.replace("rate limit básico KV-backed", "rate limit mediante el binding nativo de Cloudflare Workers Rate Limiting", 1)
brief = brief.replace("mock/stub de KV", "mock/stub del binding `RATE_LIMITER`", 1)
brief = brief.replace("código de rate limiting existe, con su propio test usando un KV simulado", "código de rate limiting existe, con su propio test usando un binding `RATE_LIMITER` simulado", 1)
brief_path.write_text(brief, encoding="utf-8")

print("PR55 DOI fixes applied")
