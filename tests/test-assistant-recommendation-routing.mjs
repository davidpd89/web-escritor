import assert from "node:assert/strict";
import { resolveLocalAnswer } from "../assets/assistant-local-knowledge.mjs";
import { ASSISTANT_SOURCE_REGISTRY } from "../assets/assistant-source-registry.js";

const registryIds = new Set(ASSISTANT_SOURCE_REGISTRY.map((source) => source.id));

const cases = [
  ["Recomiéndame portal fantasy juvenil en español", "recommendations-portal-fantasy", "recommendations-portal-fantasy"],
  ["¿Qué puedo leer si busco fantasía de portales en español?", "recommendations-portal-fantasy", "recommendations-portal-fantasy"],
  ["Quiero libros parecidos a Samuel por lo de cruzar a otro mundo", "recommendations-portal-fantasy", "recommendations-portal-fantasy"],
  ["Dame lecturas de portal fantasy", "recommendations-portal-fantasy", "recommendations-portal-fantasy"],
  ["Recomiéndame fantasía donde la magia tenga un coste", "recommendations-magic-cost", "recommendations-magic-cost"],
  ["¿Qué libros tienen magia con consecuencias o precio?", "recommendations-magic-cost", "recommendations-magic-cost"],
  ["Busco libros donde usar magia cueste algo", "recommendations-magic-cost", "recommendations-magic-cost"],
  ["Quiero leer fantasía con magia que exige un precio real", "recommendations-magic-cost", "recommendations-magic-cost"],
];

for (const [query, expectedIntent, expectedSource] of cases) {
  const answer = resolveLocalAnswer(query);
  assert.equal(answer?.intent, expectedIntent, `unexpected recommendation intent for: ${query}`);
  assert.deepEqual(answer?.sourceIds, [expectedSource], `unexpected recommendation source for: ${query}`);
  assert.ok(registryIds.has(expectedSource), `recommendation source is missing from generated registry: ${expectedSource}`);
}

const generic = resolveLocalAnswer("¿Qué me recomiendas leer?");
assert.equal(generic?.intent, "recommendations");
assert.deepEqual(generic?.sourceIds, ["recommendations-hub"]);

console.log("assistant-recommendation-routing: OK");
