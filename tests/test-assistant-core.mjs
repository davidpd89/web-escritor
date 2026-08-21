import assert from "node:assert/strict";
import { PROTOCOL_VERSION, normalizeQuery, isSafeInternalPath, isValidAssistantResponse, formatCitationMarkers, rankLocalSources } from "../assets/assistant-core.mjs";
assert.equal(PROTOCOL_VERSION, 1);
assert.equal(normalizeQuery("  ¿Quién   es   David?  "), "¿Quién es David?");
assert.equal(normalizeQuery("a\u0301"), "á");
assert.equal(normalizeQuery("x".repeat(800)).length, 500);
assert.equal(isSafeInternalPath("/libros/"), true);
assert.equal(isSafeInternalPath("//evil.example/x"), false);
assert.equal(isSafeInternalPath("https://evil.example"), false);
assert.equal(isSafeInternalPath("/../secret"), false);
const sources = [
  { id:"a", url:"/a/", title:"Las manecillas del recuerdo", territory:"obras", priority:1, visibility:"public", keywords:["reloj","memoria"] },
  { id:"b", url:"/b/", title:"Noveris", territory:"obras", priority:2, visibility:"public", keywords:["fantasía","magia"] },
  { id:"private", url:"/private/", title:"Secreto", territory:"x", priority:1, visibility:"private", keywords:["reloj"] },
  { id:"evil", url:"//evil.example/", title:"Evil", territory:"x", priority:1, visibility:"public", keywords:["reloj"] },
];
assert.deepEqual(rankLocalSources("reloj memoria", sources).map((s) => s.id), ["a"]);
assert.equal(formatCitationMarkers("Dato [b]. Otro [a].", [sources[0], sources[1]]), "Dato [2]. Otro [1].");
assert.equal(formatCitationMarkers("Desconocida [x].", [sources[0]]), "Desconocida [x].");
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", abstained:false, sources:[{id:"a",url:"/a/",title:"A"}] }), true);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"No sé", abstained:true, sources:[] }), true);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", abstained:false, sources:[] }), false);
assert.equal(isValidAssistantResponse({ protocol_version:2, ok:true, answer:"Texto", abstained:false, sources:[] }), false);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", abstained:false, sources:[{id:"a",url:"//evil.example",title:"A"}] }), false);
console.log("assistant-core: OK");
