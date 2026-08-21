import assert from "node:assert/strict";
import fs from "node:fs/promises";

const workerCode = await fs.readFile(new URL("../cloudflare-worker-assistant.js", import.meta.url), "utf8");
const { default: worker } = await import(`data:text/javascript;base64,${Buffer.from(workerCode).toString("base64")}`);

const registry = {
  schema_version: 1,
  policy: "deny-by-default",
  sources: [
    { id:"work-manecillas", url:"/las-manecillas-del-recuerdo/", title:"Las manecillas del recuerdo", visibility:"public" },
    { id:"author", url:"/autor.html", title:"David Porto Díaz", visibility:"public" },
  ],
};
let turnstileSuccess = true;
const originalFetch = globalThis.fetch;
globalThis.fetch = async (input) => {
  const url = String(input);
  if (url.includes("turnstile/v0/siteverify")) return Response.json({ success:turnstileSuccess, action:"assistant_query", hostname:"davidportodiaz.com" });
  if (url.includes("assistant-source-registry.json")) return Response.json(registry);
  throw new Error(`unexpected fetch ${url}`);
};

const limiter = (success = true, onCall = () => {}) => ({ limit:async()=>{ onCall(); return { success }; } });
const makeEnv = (overrides = {}) => ({
  ASSISTANT_ENABLED:"true",
  ASSISTANT_MODEL:"@cf/test/model",
  TURNSTILE_SITE_KEY:"site-key",
  TURNSTILE_SECRET_KEY:"secret-key",
  TURNSTILE_HOSTNAMES:"davidportodiaz.com",
  SESSION_RATE_LIMITER:limiter(),
  IP_RATE_LIMITER:limiter(),
  GLOBAL_RATE_LIMITER:limiter(),
  ASSISTANT_SEARCH:{ search:async()=>({ chunks:[{ text:"La novela sale en septiembre.", score:.8, item:{ metadata:{ source_id:"work-manecillas" }, key:"https://davidportodiaz.com/las-manecillas-del-recuerdo/" } }] }) },
  AI:{ run:async()=>({ response:"La novela se publica en septiembre. [work-manecillas]" }) },
  ...overrides,
});
const headers = { Origin:"https://davidportodiaz.com", "Content-Type":"application/json", "CF-Connecting-IP":"203.0.113.10" };
const payload = (extra = {}) => JSON.stringify({ protocol_version:1, query:"¿Cuándo sale?", session_id:"123e4567-e89b-42d3-a456-426614174000", locale:"es", turnstile_token:"ok-token", ...extra });
const request = (extra = {}, customHeaders = headers) => new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:customHeaders, body:payload(extra) });

let response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant/config", { headers:{ Origin:"https://davidportodiaz.com" } }), makeEnv());
assert.equal(response.status, 200);
assert.deepEqual(await response.json(), { protocol_version:1, ok:true, enabled:true, turnstile_site_key:"site-key" });

response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:{ Origin:"https://evil.example", "Content-Type":"application/json" }, body:payload() }), makeEnv());
assert.equal(response.status, 403);
response = await worker.fetch(request(), makeEnv({ ASSISTANT_ENABLED:"false" }));
assert.equal(response.status, 503);
response = await worker.fetch(request({ protocol_version:2 }), makeEnv());
assert.equal(response.status, 409);
response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:{...headers, "Content-Length":"5000"}, body:"{}" }), makeEnv());
assert.equal(response.status, 413);

let globalCalls = 0;
response = await worker.fetch(request(), makeEnv({ SESSION_RATE_LIMITER:limiter(false), GLOBAL_RATE_LIMITER:limiter(true,()=>globalCalls++) }));
assert.equal(response.status, 429);
assert.equal(globalCalls, 0);

turnstileSuccess = false;
response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 403);
turnstileSuccess = true;

response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 200);
let data = await response.json();
assert.equal(data.abstained, false);
assert.deepEqual(data.sources.map((source)=>source.id), ["work-manecillas"]);

response = await worker.fetch(request(), makeEnv({
  ASSISTANT_SEARCH:{ search:async()=>({chunks:[{text:"Bio",score:.7,item:{key:"https://davidportodiaz.com/autor.html",metadata:{}}}]}) },
  AI:{ run:async()=>({response:"David es escritor. [author]"}) },
}));
assert.equal(response.status, 200);
data = await response.json();
assert.deepEqual(data.sources.map((source)=>source.id), ["author"]);

response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"Dato [author]"})} }));
assert.equal(response.status, 502);
assert.equal((await response.json()).code, "invalid_source_reference");
response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"Más en https://evil.example [work-manecillas]"})} }));
assert.equal(response.status, 502);
assert.equal((await response.json()).code, "unsafe_generation");
response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"NO_EVIDENCE"})} }));
assert.equal(response.status, 200);
assert.equal((await response.json()).abstained, true);
response = await worker.fetch(request(), makeEnv({ ASSISTANT_SEARCH:{search:async()=>({chunks:[]})} }));
assert.equal(response.status, 200);
assert.equal((await response.json()).abstained, true);

globalThis.fetch = originalFetch;
console.log("assistant-worker: OK");
