/**
 * Cloudflare Worker: Brevo newsletter subscription proxy
 *
 * Deployment steps:
 *   1. dash.cloudflare.com → Workers & Pages → Create Worker
 *   2. Paste this code and deploy
 *   3. Settings → Variables and Secrets → Add secret:
 *        Name:  BREVO_API_KEY
 *        Value: (tu clave xkeysib-... de https://app.brevo.com > API keys)
 *   4. Copy the Worker URL (e.g. https://subscribe.davidportodiaz.workers.dev)
 *   5. Update WORKER_URL in script.js with that URL
 *
 * The script.js file already has WORKER_URL ready — just update the placeholder.
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

    const { email, listIds, attributes, updateEnabled } = body;
    if (!email || !listIds) {
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

    const brevoRes = await fetch("https://api.brevo.com/v3/contacts", {
      method: "POST",
      headers: {
        "api-key": env.BREVO_API_KEY,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ email, listIds, attributes, updateEnabled }),
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
