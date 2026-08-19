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
 *                     todo el sitio; ver NEWSLETTER_CONFIG.defaultListIds en
 *                     script.js — debe coincidir)
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
 * Previously the browser could specify any Brevo listIds/updateEnabled value
 * in the POST body and this Worker forwarded it unchecked to Brevo — a
 * malicious client could have subscribed an email to an arbitrary list. The
 * Worker now always uses env.BREVO_LIST_ID server-side and ignores any
 * listIds sent by the client.
 */

const ALLOWED_ORIGIN = "https://davidportodiaz.com";

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

    const { email, attributes } = body;
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
