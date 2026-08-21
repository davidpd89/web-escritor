import assert from "node:assert/strict";
import fs from "node:fs/promises";

const workerCode = await fs.readFile(new URL("../cloudflare-worker-assistant.js", import.meta.url), "utf8");
const { default: worker } = await import(`data:text/javascript;base64,${Buffer.from(workerCode).toString("base64")}`);
const sentinel = "ASSISTANT_QA_SECRET_582931";
const registry = { schema_version:1, policy:"deny-by-default", sources:[{id:"author",url:"/autor.html",title:"David Porto Díaz",visibility:"public"}] };
const sessionId = "123e4567-e89b-42d3-a456-426614174000";
const headers = { Origin:"https://davidportodiaz.com", "Content-Type":"application/json", "CF-Connecting-IP":"203.0.113.10" };
const limiter = (success=true) => ({ limit:async()=>({success}) });
function db(){ return { prepare(){ return { bind(){ return { first:async()=>({count:1}), run:async()=>({success:true}) }; } }; } }; }
function env(extra={}) { return {
  ASSISTANT_ENABLED:"true", ASSISTANT_MODEL:"@cf/qwen/qwen3-30b-a3b-fp8",
  TURNSTILE_SITE_KEY:"site", TURNSTILE_SECRET_KEY:"secret", TURNSTILE_HOSTNAMES:"davidportodiaz.com",
  SESSION_RATE_LIMITER:limiter(), IP_RATE_LIMITER:limiter(), GLOBAL_RATE_LIMITER:limiter(), ASSISTANT_QUOTA_DB:db(),
  ASSISTANT_SEARCH:{search:async()=>({chunks:[{text:"David es escritor.",score:.9,item:{metadata:{source_id:"author"},key:"https://davidportodiaz.com/autor.html"}}]})},
  AI:{run:async()=>({response:"David es escritor. [author]"})}, ...extra,
}; }
function req(query, extra={}) { return new Request("https://davidportodiaz.com/api/assistant", {method:"POST",headers,body:JSON.stringify({protocol_version:1,query,session_id:sessionId,locale:"es",turnstile_token:"token",...extra})}); }

const originalFetch = globalThis.fetch;
let outbound = [];
globalThis.fetch = async (input) => {
  const url = String(input); outbound.push(url);
  if (url === "https://challenges.cloudflare.com/turnstile/v0/siteverify") return Response.json({success:true,action:"assistant_query",hostname:"davidportodiaz.com"});
  if (url === "https://davidportodiaz.com/data/assistant-source-registry.json") return Response.json(registry);
  throw new Error(`unexpected outbound URL: ${url}`);
};

// Kill switch: disabled means no external fetch, no retrieval and no generation.
outbound = [];
let searchCalls=0, aiCalls=0;
let r = await worker.fetch(req(sentinel), env({ASSISTANT_ENABLED:"false",ASSISTANT_SEARCH:{search:async()=>{searchCalls++;}},AI:{run:async()=>{aiCalls++;}}}));
assert.equal(r.status,503); assert.equal(searchCalls,0); assert.equal(aiCalls,0); assert.deepEqual(outbound,[]);

for (const query of ["", "x"]) { outbound=[]; r=await worker.fetch(req(query),env()); assert.equal(r.status,400); assert.deepEqual(outbound,[]); }
r=await worker.fetch(req({attack:"object"}),env()); assert.equal(r.status,400);
r=await worker.fetch(req("x".repeat(500)),env()); assert.equal(r.status,200);
outbound=[]; r=await worker.fetch(req("x".repeat(501)),env()); assert.equal(r.status,400); assert.deepEqual(outbound,[]);
r=await worker.fetch(req("ab\u0000cd"),env()); assert.equal(r.status,400);

for (const size of [10_000,100_000]) {
  outbound=[];
  const body=JSON.stringify({protocol_version:1,query:"x".repeat(size),session_id:sessionId,locale:"es",turnstile_token:"token"});
  r=await worker.fetch(new Request("https://davidportodiaz.com/api/assistant",{method:"POST",headers,body}),env());
  assert.equal(r.status,413); assert.deepEqual(outbound,[]);
}

// Registry override is server-owned but still constrained to the exact allowlisted path/origin.
outbound=[];
r=await worker.fetch(req("quién es David"),env({ASSISTANT_REGISTRY_URL:"https://evil.example/data/assistant-source-registry.json",ASSISTANT_ALLOWED_ORIGINS:"https://evil.example"}));
assert.equal(r.status,503); assert.equal(outbound.some((url)=>url.includes("evil.example")),false);

// Fail closed when a limiter binding errors.
r=await worker.fetch(req("quién es David"),env({SESSION_RATE_LIMITER:{limit:async()=>{throw new Error(sentinel);}}}));
assert.equal(r.status,503); assert.equal((await r.json()).code,"rate_limit_unavailable");

// Static regression guards: never log exception messages or interpolate the QA sentinel.
assert.equal(workerCode.includes("error.message"),false);
assert.equal(workerCode.includes(sentinel),false);

globalThis.fetch=originalFetch;
console.log("assistant-hardening: OK");
