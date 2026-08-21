import assert from "node:assert/strict";
import { PROTOCOL_VERSION, normalizeQuery, isValidAssistantResponse, rankLocalSources } from "../assets/assistant-core.mjs";
assert.equal(PROTOCOL_VERSION, 1);
assert.equal(normalizeQuery("  ¿Quién   es   David?  "), "¿Quién es David?");
assert.equal(normalizeQuery("a\u0301"), "á");
assert.equal(normalizeQuery("x".repeat(800)).length, 500);
const sources = [
  { id:"a", url:"/a/", title:"Las manecillas del recuerdo", territory:"obras", priority:1, visibility:"public", keywords:["reloj","memoria"] },
  { id:"b", url:"/b/", title:"Noveris", territory:"obras", priority:2, visibility:"public", keywords:["fantasía","magia"] },
  { id:"private", url:"/private/", title:"Secreto", territory:"x", priority:1, visibility:"private", keywords:["reloj"] },
];
assert.deepEqual(rankLocalSources("reloj memoria", sources).map((s) => s.id), ["a"]);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", sources:[{id:"a",url:"/a/",title:"A"}] }), true);
assert.equal(isValidAssistantResponse({ protocol_version:2, ok:true, answer:"Texto", sources:[] }), false);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", sources:[{id:"a",url:"https://evil.example",title:"A"}] }), false);
console.log("assistant-core: OK");
