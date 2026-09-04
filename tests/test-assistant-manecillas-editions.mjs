// Las manecillas del recuerdo has two distinct editions (paperback and
// Kindle) with their own dates, ISBNs, page counts and prices. Before this
// test existed, a date/price/pages/ISBN question resolved to whichever
// branch matched first regardless of which edition was actually asked
// about -- "¿cuándo salió en Kindle?" answered with the paperback's date,
// and a `asksBuy` branch mixed Kindle/ebook/price/Amazon terms without
// distinguishing "precio del Kindle" from "precio en papel". Each case here
// pins one edition-specific question to its correct, edition-correct fact.
import assert from "node:assert/strict";
import { resolveLocalAnswer } from "../assets/assistant-local-knowledge.mjs";

const cases = [
  ["¿cuándo salió Manecillas?", "manecillas-date", /3 de septiembre de 2026/],
  ["¿cuándo salió en Kindle?", "manecillas-date-kindle", /12 de agosto de 2026/],
  ["¿precio del Kindle?", "manecillas-buy", /2,99\s*€/],
  ["¿precio en papel de Manecillas?", "manecillas-buy-paper", /16\s*€.*no tiene todavía una URL de compra verificada/],
  ["ISBN del Kindle", "manecillas-isbn-kindle", /979-8906781925/],
  ["¿ISBN del libro impreso de Manecillas?", "manecillas-isbn-paper", /979-8-90514-935-1/],
  ["ASIN de Manecillas", "manecillas-asin", /B0HHM71F46/],
  ["¿cuántas páginas tiene Manecillas en papel?", "manecillas-pages-paper", /272 páginas/],
  ["¿cuántas páginas tiene Manecillas en Kindle?", "manecillas-pages-kindle", /227 páginas/],
  ["dónde compro Manecillas en Kindle", "manecillas-buy", /amzn\.to|Kindle/i],
  ["¿dónde compro Las manecillas del recuerdo en papel?", "manecillas-buy-paper", /no tiene todavía una URL de compra verificada/],
  ["¿qué diferencias hay entre las dos ediciones de Manecillas?", "manecillas-editions", /tapa blanda.*Kindle|Kindle.*tapa blanda/s],
];

for (const [query, expectedIntent, expectedPattern] of cases) {
  const answer = resolveLocalAnswer(query, {});
  assert.ok(answer, `no local answer resolved for: ${query}`);
  assert.equal(answer.intent, expectedIntent, `wrong intent for "${query}": got ${answer.intent}`);
  assert.match(answer.answer, expectedPattern, `wrong edition/fact in answer for "${query}": ${answer.answer}`);
}

// Cross-contamination guards: a Kindle-specific fact must never surface the
// paperback's value and vice versa.
const kindleDate = resolveLocalAnswer("¿cuándo salió en Kindle?", {});
assert.doesNotMatch(kindleDate.answer, /3 de septiembre de 2026/, "Kindle date answer leaked the paperback's date");

const paperPages = resolveLocalAnswer("¿cuántas páginas tiene Manecillas en papel?", {});
assert.doesNotMatch(paperPages.answer, /227/, "paperback page count answer leaked the Kindle print-length figure");

const kindlePages = resolveLocalAnswer("¿cuántas páginas tiene Manecillas en Kindle?", {});
assert.doesNotMatch(kindlePages.answer, /\b272\b/, "Kindle page-count answer leaked the paperback's real page count");

// A Samuel-scoped query must not be hijacked by the bare "kindle" heuristic
// used to disambiguate Manecillas' edition-less mentions.
const samuelStillSamuel = resolveLocalAnswer("¿de qué trata Samuel entre mundos?", {});
assert.equal(samuelStillSamuel.intent, "samuel");

console.log("assistant-manecillas-editions: OK");
