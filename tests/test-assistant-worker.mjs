import assert from "node:assert/strict";
import fs from "node:fs/promises";

const workerCode = await fs.readFile(new URL("../cloudflare-worker-assistant.js", import.meta.url), "utf8");
const { default: worker } = await import(`data:text/javascript;base64,${Buffer.from(workerCode).toString("base64")}`);

const baseRegistry = {
  schema_version: 1,
  policy: "deny-by-default",
  sources: [
    { id:"work-manecillas", url:"/las-manecillas-del-recuerdo/", title:"Las manecillas del recuerdo", visibility:"public" },
    { id:"author", url:"/autor.html", title:"David Porto Díaz", visibility:"public" },
  ],
};
let registryPayload = baseRegistry;
let turnstileSuccess = true;
let turnstileHostname = "davidportodiaz.com";
let turnstileAction = "assistant_query";
const originalFetch = globalThis.fetch;
globalThis.fetch = async (input) => {
  const url = String(input);
  if (url.includes("turnstile/v0/siteverify")) return Response.json({ success:turnstileSuccess, action:turnstileAction, hostname:turnstileHostname });
  if (url.includes("assistant-source-registry.json")) return Response.json(registryPayload);
  throw new Error(`unexpected fetch ${url}`);
};

const limiter = (success = true, onCall = () => {}) => ({ limit:async()=>{ onCall(); return { success }; } });
function makeQuotaDb(seed = {}) {
  const counts = new Map(Object.entries(seed));
  return {
    counts,
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              assert.match(sql, /INSERT INTO assistant_daily_quota/);
              const [bucket, day] = args;
              const key = `${bucket}|${day}`;
              const count = (counts.get(key) || 0) + 1;
              counts.set(key, count);
              return { count };
            },
            async run() {
              if (/DELETE FROM assistant_daily_quota/.test(sql)) {
                const [cutoff] = args;
                for (const key of [...counts.keys()]) {
                  const day = key.slice(key.lastIndexOf("|") + 1);
                  if (day < cutoff) counts.delete(key);
                }
              }
              return { success:true };
            },
          };
        },
      };
    },
  };
}
const makeEnv = (overrides = {}) => ({
  ASSISTANT_ENABLED:"true",
  ASSISTANT_MODEL:"@cf/qwen/qwen3-30b-a3b-fp8",
  TURNSTILE_SITE_KEY:"site-key",
  TURNSTILE_SECRET_KEY:"secret-key",
  TURNSTILE_HOSTNAMES:"davidportodiaz.com",
  SESSION_RATE_LIMITER:limiter(),
  IP_RATE_LIMITER:limiter(),
  GLOBAL_RATE_LIMITER:limiter(),
  ASSISTANT_QUOTA_DB:makeQuotaDb(),
  ASSISTANT_SEARCH:{ search:async()=>({ chunks:[{ text:"La novela sale en septiembre.", score:.8, item:{ metadata:{ source_id:"work-manecillas" }, key:"https://davidportodiaz.com/las-manecillas-del-recuerdo/" } }] }) },
  AI:{ run:async()=>({ response:"La novela se publica en septiembre. [work-manecillas]" }) },
  ...overrides,
});
const headers = { Origin:"https://davidportodiaz.com", "Content-Type":"application/json", "CF-Connecting-IP":"203.0.113.10" };
const sessionId = "123e4567-e89b-42d3-a456-426614174000";
const payload = (extra = {}) => JSON.stringify({ protocol_version:1, query:"¿Cuándo sale?", session_id:sessionId, locale:"es", turnstile_token:"ok-token", ...extra });
const request = (extra = {}, customHeaders = headers) => new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:customHeaders, body:payload(extra) });
const today = new Date().toISOString().slice(0, 10);

let response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant/config", { headers:{ Origin:"https://davidportodiaz.com" } }), makeEnv());
assert.equal(response.status, 200);
assert.deepEqual(await response.json(), { protocol_version:1, ok:true, enabled:true, turnstile_site_key:"site-key" });
response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant/config", { headers:{ Origin:"https://evil.example" } }), makeEnv());
assert.equal(response.status, 403);
response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant/config", { headers:{ Origin:"https://davidportodiaz.com" } }), makeEnv({ASSISTANT_MODEL:"@cf/zai-org/glm-5.2"}));
assert.equal((await response.json()).enabled, false);

response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:{ Origin:"https://evil.example", "Content-Type":"application/json" }, body:payload() }), makeEnv());
assert.equal(response.status, 403);
response = await worker.fetch(request(), makeEnv({ ASSISTANT_ENABLED:"false" }));
assert.equal(response.status, 503);
response = await worker.fetch(request({ protocol_version:2 }), makeEnv());
assert.equal(response.status, 409);
response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:{ Origin:"https://davidportodiaz.com", "CF-Connecting-IP":"203.0.113.10", "Content-Type":"text/plain" }, body:payload() }), makeEnv());
assert.equal(response.status, 415);
response = await worker.fetch(new Request("https://davidportodiaz.com/api/assistant", { method:"POST", headers:{...headers, "Content-Length":"5000"}, body:"{}" }), makeEnv());
assert.equal(response.status, 413);

let globalCalls = 0;
response = await worker.fetch(request(), makeEnv({ SESSION_RATE_LIMITER:limiter(false), GLOBAL_RATE_LIMITER:limiter(true,()=>globalCalls++) }));
assert.equal(response.status, 429);
assert.equal(globalCalls, 0);
response = await worker.fetch(request(), makeEnv({ IP_RATE_LIMITER:limiter(false), GLOBAL_RATE_LIMITER:limiter(true,()=>globalCalls++) }));
assert.equal(response.status, 429);

turnstileSuccess = false;
globalCalls = 0;
response = await worker.fetch(request(), makeEnv({GLOBAL_RATE_LIMITER:limiter(true,()=>globalCalls++)}));
assert.equal(response.status, 403);
assert.equal(globalCalls, 0);
turnstileSuccess = true;
turnstileHostname = "evil.example";
response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 403);
turnstileHostname = "davidportodiaz.com";
turnstileAction = "other_action";
response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 403);
turnstileAction = "assistant_query";

response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 200);
let data = await response.json();
assert.equal(data.abstained, false);
assert.deepEqual(data.sources.map((source)=>source.id), ["work-manecillas"]);

let capturedSearchRequest = null;
response = await worker.fetch(request(), makeEnv({
  ASSISTANT_REQUIRE_METADATA_FILTER:"true",
  ASSISTANT_SEARCH:{ search:async(args)=>{
    capturedSearchRequest = args;
    return { chunks:[{ text:"La novela sale en septiembre.", score:.8, item:{ metadata:{ source_id:"work-manecillas" }, key:"https://davidportodiaz.com/las-manecillas-del-recuerdo/" } }] };
  } },
}));
assert.equal(response.status, 200);
assert.deepEqual(capturedSearchRequest.ai_search_options.retrieval.filters, { visibility:"public" });
assert.equal(capturedSearchRequest.ai_search_options.retrieval.retrieval_type, "hybrid");
assert.equal(capturedSearchRequest.ai_search_options.retrieval.fusion_method, "rrf");
assert.equal(capturedSearchRequest.ai_search_options.retrieval.context_expansion, 1);

response = await worker.fetch(request(), makeEnv({
  ASSISTANT_SEARCH:{ search:async()=>({chunks:[{text:"Bio",score:.7,item:{key:"https://davidportodiaz.com/autor.html",metadata:{}}}]}) },
  AI:{ run:async()=>({response:"David es escritor. [author]"}) },
}));
assert.equal(response.status, 200);
data = await response.json();
assert.deepEqual(data.sources.map((source)=>source.id), ["author"]);

response = await worker.fetch(request(), makeEnv({
  ASSISTANT_SEARCH:{ search:async()=>({chunks:[{text:"Malicioso",score:.99,item:{key:"https://evil.example/autor.html",metadata:{}}}]}) },
}));
assert.equal(response.status, 200);
assert.equal((await response.json()).abstained, true);

response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"Dato [author]"})} }));
assert.equal(response.status, 502);
assert.equal((await response.json()).code, "invalid_source_reference");
response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"Dato sin cita"})} }));
assert.equal(response.status, 502);
assert.equal((await response.json()).code, "missing_source_reference");
response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"Más en https://evil.example [work-manecillas]"})} }));
assert.equal(response.status, 502);
assert.equal((await response.json()).code, "unsafe_generation");
response = await worker.fetch(request(), makeEnv({ AI:{run:async()=>({response:"NO_EVIDENCE"})} }));
assert.equal(response.status, 200);
assert.equal((await response.json()).abstained, true);
response = await worker.fetch(request(), makeEnv({ ASSISTANT_SEARCH:{search:async()=>({chunks:[]})} }));
assert.equal(response.status, 200);
assert.equal((await response.json()).abstained, true);

registryPayload = { schema_version:1, policy:"deny-by-default", sources:[{id:"bad",url:"//evil.example",title:"Bad",visibility:"public"}] };
response = await worker.fetch(request(), makeEnv());
assert.equal(response.status, 503);
assert.equal((await response.json()).code, "registry_unavailable");
registryPayload = baseRegistry;

const sessionQuotaDb = makeQuotaDb({[`session:${sessionId}|${today}`]:5});
response = await worker.fetch(request(), makeEnv({ASSISTANT_QUOTA_DB:sessionQuotaDb}));
assert.equal(response.status, 429);
assert.equal((await response.json()).code, "daily_session_limit");
const globalQuotaDb = makeQuotaDb({[`global|${today}`]:50});
response = await worker.fetch(request(), makeEnv({ASSISTANT_QUOTA_DB:globalQuotaDb}));
assert.equal(response.status, 429);
assert.equal((await response.json()).code, "daily_global_limit");

const failingDb = { prepare(){ throw new Error("db-down"); } };
response = await worker.fetch(request(), makeEnv({ASSISTANT_QUOTA_DB:failingDb}));
assert.equal(response.status, 503);
assert.equal((await response.json()).code, "quota_unavailable");

globalThis.fetch = originalFetch;
console.log("assistant-worker: OK");
