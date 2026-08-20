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

    // listIds is never taken from the client: a browser could otherwise ask
    // to be added to an arbitrary Brevo list by sending its own listIds.
    // The single allowed list is configured server-side via env.BREVO_LIST_ID.
    if (!env.BREVO_LIST_ID) {
      return new Response(JSON.stringify({ message: "Server misconfigured: BREVO_LIST_ID not set" }), {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
      });
    }
    const listIds = [Number(env.BREVO_LIST_ID)];

    // updateEnabled is hardcoded true (not read from the client): resubmitting
    // the same email should update attributes/list membership rather than error.
    const brevoRes = await fetch("https://api.brevo.com/v3/contacts", {
      method: "POST",
      headers: {
        "api-key": env.BREVO_API_KEY,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ email, listIds, attributes, updateEnabled: true }),
    });

    const text = await brevoRes.text();
    return new Response(text, {
      status: brevoRes.status,
      headers: {
        "Content-Type": "application/json",
        ...corsHeaders(origin),
      },
    });
  },
};

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : "",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}
