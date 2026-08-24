import assert from "node:assert/strict";
import fs from "node:fs";
import { resolveLocalAnswer } from "../assets/assistant-local-knowledge.mjs";

const greeting = resolveLocalAnswer("Hola");
assert.equal(greeting?.intent, "greeting");
assert.deepEqual(greeting?.sourceIds, [], "a greeting must not fabricate documentary sources");
assert.ok(greeting?.suggestions?.length >= 2, "a greeting should offer useful next steps");

assert.equal(resolveLocalAnswer("Buenas tardes")?.intent, "greeting");
assert.equal(resolveLocalAnswer("¿Qué puedes hacer?")?.intent, "capabilities");
assert.equal(resolveLocalAnswer("Gracias")?.intent, "thanks");
assert.equal(resolveLocalAnswer("Hasta luego")?.intent, "farewell");

// A social prefix plus a real question must not hijack the real intent.
const greetedBookQuestion = resolveLocalAnswer("Hola, ¿de qué trata Las manecillas del recuerdo?");
assert.equal(greetedBookQuestion?.intent, "manecillas");
assert.ok(greetedBookQuestion?.sourceIds?.includes("work-manecillas"));

const embed = fs.readFileSync(new URL("../asistente/embed.html", import.meta.url), "utf8");
assert.match(embed, /<base\s+target=["']_top["']\s*\/?>/i, "embed links must navigate the top-level browsing context");

const assistantCss = fs.readFileSync(new URL("../assets/assistant.css", import.meta.url), "utf8");
assert.ok(!assistantCss.includes("border-radius:999px"), "assistant must not regress to pill-shaped chat controls");
assert.ok(assistantCss.includes(".assistant-message__sources a::after"), "sources must keep an explicit editorial navigation affordance");

const widgetCss = fs.readFileSync(new URL("../assets/assistant-widget.css", import.meta.url), "utf8");
assert.ok(!widgetCss.includes("assistant-widget-pulse"), "launcher must not pulse perpetually");

console.log("assistant-editorial-ux: OK");
