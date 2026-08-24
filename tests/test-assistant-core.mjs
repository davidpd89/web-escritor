import assert from "node:assert/strict";
import { ASSISTANT_PUBLIC_CONFIG } from "../assets/assistant-config.js";
import {
  PROTOCOL_VERSION,
  QUERY_MIN_LENGTH,
  QUERY_MAX_LENGTH,
  normalizeQuery,
  foldQuery,
  isSafeInternalPath,
  isValidAssistantResponse,
  formatCitationMarkers,
  rankLocalSources,
} from "../assets/assistant-core.mjs";
import { resolveLocalAnswer } from "../assets/assistant-local-knowledge.mjs";
import { ASSISTANT_SOURCE_REGISTRY } from "../assets/assistant-source-registry.js";

assert.equal(PROTOCOL_VERSION, 1);
assert.equal(QUERY_MIN_LENGTH, 2);
assert.equal(QUERY_MAX_LENGTH, 500);
assert.equal(ASSISTANT_PUBLIC_CONFIG.remoteEnabled, false, "remote mode must default to OFF");
assert.equal(ASSISTANT_PUBLIC_CONFIG.assistantUrl, "/api/assistant");
assert.equal(ASSISTANT_PUBLIC_CONFIG.configUrl, "/api/assistant/config");
assert.equal(ASSISTANT_PUBLIC_CONFIG.turnstileSiteKey, "");

assert.equal(normalizeQuery("  ¿Quién   es   David?  "), "¿Quién es David?");
assert.equal(normalizeQuery("a\u0301"), "á");
assert.equal(normalizeQuery("x".repeat(800)).length, 500);
assert.equal(foldQuery("FANTASÍA y Biografía"), "fantasia y biografia");
assert.equal(isSafeInternalPath("/libros/"), true);
assert.equal(isSafeInternalPath("//evil.example/x"), false);
assert.equal(isSafeInternalPath("https://evil.example"), false);
assert.equal(isSafeInternalPath("/../secret"), false);
assert.equal(isSafeInternalPath("/ok/?x=1"), true);

const sources = [
  { id:"a", url:"/a/", title:"Las manecillas del recuerdo", territory:"obras", priority:1, visibility:"public", keywords:["reloj","memoria"] },
  { id:"b", url:"/b/", title:"Noveris", territory:"obras", priority:2, visibility:"public", keywords:["fantasía","magia"] },
  { id:"private", url:"/private/", title:"Secreto", territory:"x", priority:1, visibility:"private", keywords:["reloj"] },
  { id:"evil", url:"//evil.example/", title:"Evil", territory:"x", priority:1, visibility:"public", keywords:["reloj"] },
];
assert.deepEqual(rankLocalSources("reloj memoria", sources).map((s) => s.id), ["a"]);
assert.deepEqual(rankLocalSources("fantasia", sources).map((s) => s.id), ["b"], "local search should ignore Spanish diacritics");
assert.equal(formatCitationMarkers("Dato [b]. Otro [a].", [sources[0], sources[1]]), "Dato [2]. Otro [1].");
assert.equal(formatCitationMarkers("Desconocida [x].", [sources[0]]), "Desconocida [x].");

assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto [a]", abstained:false, sources:[{id:"a",url:"/a/",title:"A"}] }), true);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"No sé", abstained:true, sources:[] }), true);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto", abstained:false, sources:[{id:"a",url:"/a/",title:"A"}] }), false, "uncited remote answer must fail closed");
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto [b]", abstained:false, sources:[{id:"a",url:"/a/",title:"A"}] }), false, "unknown citation marker must fail closed");
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto [a]", abstained:false, sources:[{id:"a",url:"/a/",title:"A"},{id:"a",url:"/b/",title:"B"}] }), false, "duplicate source IDs must fail closed");
assert.equal(isValidAssistantResponse({ protocol_version:2, ok:true, answer:"Texto [a]", abstained:false, sources:[{id:"a",url:"/a/",title:"A"}] }), false);
assert.equal(isValidAssistantResponse({ protocol_version:1, ok:true, answer:"Texto [a]", abstained:false, sources:[{id:"a",url:"//evil.example",title:"A"}] }), false);

const registryIds = new Set(ASSISTANT_SOURCE_REGISTRY.map((source) => source.id));
const localCases = [
  ["¿De qué trata Las manecillas del recuerdo?", "manecillas"],
  ["¿Cuándo se publica Las manecillas del recuerdo?", "manecillas-date"],
  ["¿De qué trata Samuel entre mundos?", "samuel"],
  ["¿Qué premio ganó Samuel entre mundos?", "samuel-awards"],
  ["¿Qué es Noveris?", "noveris"],
  ["¿Dónde mando un manuscrito?", "editorials"],
  ["¿Qué concursos para escritores hay?", "opportunities"],
  ["¿Qué herramientas gratuitas hay?", "tools"],
  ["¿Cómo puedo contactar con David?", "press"],
  ["¿Hay eventos o firmas?", "events"],
  ["¿Qué premios tiene?", "awards"],
  ["¿Qué libros hay?", "works"],
  ["¿Qué puedo encontrar en esta web?", "site-overview"],
  ["Llévame a los libros", "works"],
  ["No sé por dónde empezar", "site-overview"],
  ["¿Hay un mapa de la web?", "site-overview"],
  ["Quiero probar el libro del reloj", "manecillas-fragment"],
  ["Soy periodista y quiero contactar", "press"],
  ["Busco dónde mandar mi novela", "editorials"],
  ["Quiero ver el Cuaderno", "notebook"],
];
for (const [query, expectedIntent] of localCases) {
  const answer = resolveLocalAnswer(query);
  assert.equal(answer?.intent, expectedIntent, `unexpected local intent for: ${query}`);
  assert.ok(answer?.answer?.length > 15, `local answer is too thin for: ${query}`);
  for (const sourceId of answer?.sourceIds || []) assert.ok(registryIds.has(sourceId), `${expectedIntent}: unknown source_id ${sourceId}`);
}

const typoManecillas = resolveLocalAnswer("¿De qué trata maneciyas?");
assert.equal(typoManecillas?.intent, "manecillas", "known work names should tolerate a small typo");
const typoManecillasFragment = resolveLocalAnswer("quiero leer un fragmento de maneciyas");
assert.equal(typoManecillasFragment?.intent, "manecillas-fragment");

const manecillasDate = resolveLocalAnswer("¿Cuándo se publica Las manecillas del recuerdo?");
assert.match(manecillasDate?.answer || "", /La fecha de publicación .*3 de septiembre de 2026.*Monza Ediciones/i);
assert.doesNotMatch(manecillasDate?.answer || "", /\bse publica\b/i, "publication answer must not drift with runner/client date");

const samuelAwards = resolveLocalAnswer("¿Fue Samuel entre mundos finalista del Juan Andrés Teno?");
assert.equal(samuelAwards?.intent, "samuel-awards");
assert.match(samuelAwards?.answer || "", /No se atribuye.*Samuel entre mundos.*Letras Como Espada/i);
assert.match(samuelAwards?.answer || "", /Top 10.*Juan Andrés Teno.*obra presentada no está identificada/i);
assert.deepEqual(samuelAwards?.sourceIds, ["awards", "work-samuel"]);

const choice = resolveLocalAnswer("Quiero leer un fragmento");
assert.equal(choice?.intent, "fragment-choice");
assert.equal(choice?.pending, "fragment-choice");
assert.equal(choice?.suggestions?.length, 2);
assert.equal(resolveLocalAnswer("Samuel", { pending: "fragment-choice" })?.intent, "samuel-fragment");
assert.equal(resolveLocalAnswer("Las manecillas", { pending: "fragment-choice" })?.intent, "manecillas-fragment");

const overview = resolveLocalAnswer("¿Qué enlaces hay?");
assert.equal(overview?.intent, "site-overview");
assert.ok(overview?.suggestions?.length >= 3);

assert.equal(resolveLocalAnswer("Hola, ¿de qué trata Las manecillas del recuerdo?")?.intent, "manecillas", "social prefix must not hijack a real question");
assert.equal(resolveLocalAnswer("¿Qué tiempo hace en Bilbao?"), null, "off-domain questions must remain outside the deterministic router");
assert.equal(resolveLocalAnswer("algo completamente ajeno que no está previsto"), null);

console.log("assistant-core: OK");