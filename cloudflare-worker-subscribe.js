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
 *   5. Copy the Worker URL (e.g. https://subscribe.davidportodiaz.workers.dev)
 *   6. Update WORKER_URL in script.js with that URL
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
 * SECURITY NOTE (2026-08-19): listIds is no longer accepted from the client.
 *
 * SECURITY NOTE (2026-08-20): the client input contract is now minimal by
 * design — the browser sends only { email, source, result? }. Previously
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
 * NOTE ON ABUSE PROTECTION: the Origin check + CORS headers below stop
 * cross-site browser requests, but they are NOT rate limiting or bot
 * protection — a direct POST from a script (no browser, no Origin header
 * enforcement bypassable by omitting Origin entirely triggers the 403
 * below, but a non-browser client can still just spoof the Origin header)
 * can still hit this endpoint repeatedly. If abuse becomes a real problem,
 * add Turnstile and/or a KV-backed rate limit; neither is implemented here
 * to keep this pass scoped to the input-contract fix.
 */

const ALLOWED_ORIGIN = "https://davidportodiaz.com";

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
      return new Response("Bad Request", { status: 400 });
    }

    // Minimal client contract: only email/source/result are ever read from
    // the request body. Anything else the client sends (listIds, attributes,
    // updateEnabled, ...) is silently ignored, not forwarded to Brevo.
    const { email, source, result } = body;
    if (!email) {
      return new Response(JSON.stringify({ message: "Missing required fields" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
      });
    }

    // Basic email format validation to avoid forwarding garbage to Brevo
    const emailRe = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
    if (!emailRe.test(email)) {
      return new Response(JSON.stringify({ message: "Invalid email address" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
      });
    }

    // `source` must be one of the known whitelist keys. The client only
    // ever sends this short label; the actual Brevo attribute value is
    // looked up server-side from SOURCE_MAP, never taken from the client.
    if (typeof source !== "string" || !Object.prototype.hasOwnProperty.call(SOURCE_MAP, source)) {
      return new Response(JSON.stringify({ message: "Invalid or missing source" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
      });
    }

    const attributes = { SOURCE: SOURCE_MAP[source] };
    if (source === "quiz" && typeof result === "string" && NOVERIS_RESULTS.has(result)) {
      attributes.NOVERIS = result;
    }

    // Explicit server-config validation (point 22 of the 2026-08-20
    // corrective audit): both env values are checked for presence AND
    // shape before ever calling Brevo, instead of only checking BREVO_LIST_ID
    // truthiness and letting a malformed value silently become NaN.
    if (!env.BREVO_API_KEY || typeof env.BREVO_API_KEY !== "string") {
      console.error("Worker misconfigured: BREVO_API_KEY missing");
      return jsonResponse(origin, 500, { ok: false, message: "Servicio no disponible temporalmente." });
    }
    const listIdNumber = Number(env.BREVO_LIST_ID);
    if (!env.BREVO_LIST_ID || !Number.isInteger(listIdNumber) || listIdNumber <= 0) {
      console.error("Worker misconfigured: BREVO_LIST_ID is not a positive integer");
      return jsonResponse(origin, 500, { ok: false, message: "Servicio no disponible temporalmente." });
    }
    const listIds = [listIdNumber];

    // updateEnabled is hardcoded true (not read from the client): resubmitting
    // the same email should update attributes/list membership rather than error.
    let brevoRes;
    try {
      brevoRes = await fetch("https://api.brevo.com/v3/contacts", {
        method: "POST",
        headers: {
          "api-key": env.BREVO_API_KEY,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ email, listIds, attributes, updateEnabled: true }),
      });
    } catch (err) {
      console.error("Brevo request failed:", err);
      return jsonResponse(origin, 502, { ok: false, message: "No se ha podido completar la suscripción. Inténtalo de nuevo más tarde." });
    }

    // Never forward Brevo's raw response body to the client — it can carry
    // internal error detail that's not meant for a public API consumer.
    // Log the real response server-side (Cloudflare Worker logs only) and
    // return a minimal, safe, structured body instead. The one case the
    // client genuinely needs to distinguish is "this email is already
    // subscribed" (Brevo returns 400 for that), surfaced here as a clean
    // { duplicate: true } flag instead of asking the client to string-search
    // Brevo's raw error message.
    if (brevoRes.ok || brevoRes.status === 204) {
      return jsonResponse(origin, brevoRes.status === 204 ? 204 : 201, { ok: true });
    }

    let brevoBodyText = "";
    try {
      brevoBodyText = await brevoRes.text();
    } catch {
      // ignore — brevoBodyText stays empty, we only needed it for the duplicate check
    }
    if (brevoRes.status === 400 && brevoBodyText.toLowerCase().includes("already exist")) {
      return jsonResponse(origin, 400, { ok: false, duplicate: true });
    }

    console.error(`Brevo error ${brevoRes.status}:`, brevoBodyText.slice(0, 500));
    return jsonResponse(origin, 502, { ok: false, message: "No se ha podido completar la suscripción. Inténtalo de nuevo más tarde." });
  },
};

function jsonResponse(origin, status, bodyObj) {
  return new Response(JSON.stringify(bodyObj), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : "",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}
