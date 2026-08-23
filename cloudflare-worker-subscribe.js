/**
 * Cloudflare Worker: Brevo newsletter subscription proxy
 *
 * Deployment steps:
 *   1. dash.cloudflare.com → Workers & Pages → Create Worker
 *   2. Paste this code and deploy
 *   3. Settings → Variables and Secrets → Add secret:
 *        Name:  BREVO_API_KEY
 *        Value: (tu clave xkeysib-... de https://app.brevo.com > API keys)
 *   4. Settings → Variables and Secrets → Add variable:
 *        Name:  BREVO_LIST_ID
 *        Value: 3   (el ID numerico de la lista de Brevo a la que se suscribe
 *                     todo el sitio; ver NEWSLETTER_CONFIG.endpoint en
 *                     script.js)
 *   5. Settings → Variables and Secrets → Add variable:
 *        Name:  BREVO_DOI_REDIRECT_URL
 *        Value: https://davidportodiaz.com/gracias-suscripcion/
 *        (la URL de retorno de doble confirmacion configurada en Brevo)
 *   6. Settings → Variables and Secrets → Add variable:
 *        Name:  BREVO_DOI_TEMPLATE_ID
 *        Value: (ID numérico de un template Brevo válido para DOI; no se guarda en el repo)
 *   7. Add a Cloudflare Workers Rate Limiting binding:
 *        Binding name: RATE_LIMITER
 *        Configure e.g. 5 requests / 60 s and choose the namespace_id in Cloudflare.
 *   8. Copy the Worker URL (e.g. https://subscribe.davidportodiaz.workers.dev)
 *   9. Update WORKER_URL in script.js with that URL
 *
 * The script.js file already has WORKER_URL ready — just update the placeholder.
 *
 * IMPORTANT: after editing this file, the change only takes effect once you
 * manually re-paste/redeploy it in the Cloudflare dashboard — pushing to this
 * git repo does not deploy the Worker.
 *
 * DEPLOY ORDER (2026-08-20, critical — do not deploy this Worker version
 * out of order): `main` (the live site) still expects the OLD Worker
 * contract — the client used to send listIds/attributes/updateEnabled
 * directly, which this new Worker version deliberately ignores. Deploying
 * THIS Worker before the new script.js (the one that sends only
 * { email, source, result? }) reaches production would break the live
 * newsletter forms, because the currently-deployed script.js still sends
 * the old shape and this Worker would silently drop the parts it no
 * longer reads. Correct order:
 *   1. merge implementacion-web-2026 → main (human decision, not automated)
 *   2. verify GitHub Pages actually serves the new script.js in production
 *   3. THEN deploy this Worker file in the Cloudflare dashboard
 *   4. smoke-test each newsletter form (home/fragmento/manecillas/cuaderno/
 *      popup/quiz) end-to-end against the real Worker before considering
 *      this done.
 *
 * BREVO — ESTADO REAL VERIFICADO (2026-08-20): la auditoría read-only
 * (scripts/brevo/audit-brevo.py) SÍ llegó a ejecutarse con éxito desde la
 * máquina de David. Confirmado contra la cuenta real: la lista canónica del
 * sitio es la ID 3 "Lectores web" (2 suscriptores reales) — que es la que
 * env.BREVO_LIST_ID debe apuntar — y el atributo de contacto SOURCE existe
 * ya (se creó en esa misma sesión), así que el SOURCE_MAP de este Worker
 * tiene dónde aterrizar. Existe además la lista ID 4 "identified_contacts"
 * (0 suscriptores), que NO es la del sitio.
 *
 * Si vuelve a aparecer un 401 "unrecognised IP address": la cuenta usa lista
 * blanca de IPs y la IPv6 doméstica rota el sufijo dentro del mismo prefijo
 * /64, así que autorizar una IP suelta caduca en la siguiente rotación —
 * autorizar el prefijo /64 en app.brevo.com/security/authorised_ips.
 *
 * SIGUE SIENDO GATE: si un alta en la lista 3 dispara alguna automatización
 * (hay plantillas Bienvenida_Samuel_* y Automatización #2_step_*), porque la
 * API v3 REST no expone Automation (/automation/emails y /automation/workflows
 * devuelven 404). Hay que mirarlo en el panel de Brevo. Por eso el copy de la
 * web sigue sin prometer entrega de capítulo: no está verificado.
 *
 * LECTORES BETA (N.1, 2026-08-23): `source: "lectores-beta"` is a
 * DELIBERATELY separate Brevo list from the general newsletter
 * (`env.BREVO_BETA_LIST_ID`, not `env.BREVO_LIST_ID`). The consent copy on
 * /lectores-beta/ is its own, distinct from "recibir novedades del autor" --
 * joining the beta program means receiving unpublished material and being
 * asked for feedback, a materially different purpose that must not share a
 * list/consent record with the general newsletter. Configure
 * BREVO_BETA_LIST_ID as its own Cloudflare secret/variable when the real
 * Brevo list exists; until then, POSTs with source="lectores-beta" fail
 * closed with 500 (same pattern as a missing BREVO_LIST_ID), never silently
 * falling back to the general list.
 *
 * SECURITY NOTE (2026-08-19): listIds is no longer accepted from the client.
 *
 * SECURITY NOTE (2026-08-20): the client input contract is now minimal by
 * design — the browser sends only { email, source, result?, website? }. `website`
 * is a honeypot and is never forwarded. Previously
 * this Worker destructured and forwarded `attributes` straight from the
 * client's POST body to Brevo unchecked, so a malicious client could have
 * attached arbitrary Brevo contact attributes (or, before the 08-19 fix,
 * arbitrary listIds/updateEnabled). Now:
 *   - `source` must match a known key in SOURCE_MAP (whitelist below); the
 *     Worker looks up the real Brevo SOURCE attribute value server-side —
 *     the client never controls the attribute value that gets stored.
 *   - `result` (only meaningful when source === "quiz") must match one of
 *     the four fixed Noveris quiz outcomes; anything else is dropped.
 *   - `listIds`, `attributes`, and `updateEnabled` are never read from the
 *     client at all — listIds comes from env.BREVO_LIST_ID, attributes is
 *     built entirely server-side from the validated source/result, and
 *     updateEnabled is hardcoded to true below.
 *
 * NOTE ON ABUSE PROTECTION: Origin/CORS are not bot protection. This Worker
 * uses a honeypot plus Cloudflare's native Rate Limiting binding. If RATE_LIMITER
 * is missing, malformed or throws, the Worker logs the degraded state and fails
 * open so a configuration error does not block legitimate readers; production
 * deployment must therefore verify the binding instead of assuming it exists.
 */

const ALLOWED_ORIGIN = "https://davidportodiaz.com";
const BREVO_DOI_ENDPOINT = "https://api.brevo.com/v3/contacts/doubleOptinConfirmation";
const PENDING_CONFIRMATION_BODY = Object.freeze({ ok: true, state: "pending_confirmation" });
const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;

// Server-side whitelist: maps a client-supplied `source` label to the exact
// Brevo SOURCE attribute value. Must stay in sync with the source labels
// script.js actually sends (search NEWSLETTER_CONFIG / submitNewsletter /
// source: in script.js). The client never sends the mapped value itself.
const SOURCE_MAP = {
  quiz: "quiz-noveris",
  home: "home",
  fragmento: "fragmento",
  manecillas: "manecillas",
  cuaderno: "cuaderno",
  popup: "popup",
  "lectores-beta": "lectores-beta",
};

// Fuentes que deben aterrizar en una lista de Brevo DISTINTA de la general
// (env.BREVO_LIST_ID), porque su proposito/consentimiento es materialmente
// distinto de "recibir novedades del autor" (N.1, 2026-08-23). Anadir aqui
// cualquier fuente futura que necesite la misma separacion.
const SEPARATE_LIST_ENV_KEY = {
  "lectores-beta": "BREVO_BETA_LIST_ID",
};

// Bounded enum for the Noveris quiz result attribute. script.js computes
// this client-side from a fixed set of 4 possible quiz outcomes (never free
// text), but the Worker still validates it rather than trusting the client.
const NOVERIS_RESULTS = new Set(["mensajero", "sabio", "silenciadora", "guardian"]);

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin),
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Only accept requests from the real site
    if (origin !== ALLOWED_ORIGIN) {
      return new Response("Forbidden", { status: 403 });
    }

    let body;
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

    const config = validateBrevoConfig(env, source);
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
};

function validateBrevoConfig(env, source) {
  const apiKey = typeof env?.BREVO_API_KEY === "string" ? env.BREVO_API_KEY.trim() : "";
  if (!apiKey) return { ok: false, reason: "BREVO_API_KEY missing" };

  // La mayoria de fuentes usan la lista general; las declaradas en
  // SEPARATE_LIST_ENV_KEY usan su propia variable de entorno y NUNCA caen
  // de vuelta a BREVO_LIST_ID si falta -- fallar cerrado, no mezclar listas.
  const listEnvKey = SEPARATE_LIST_ENV_KEY[source] || "BREVO_LIST_ID";
  const listId = Number(env?.[listEnvKey]);
  if (!Number.isInteger(listId) || listId <= 0) {
    return { ok: false, reason: `${listEnvKey} must be a positive integer` };
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
