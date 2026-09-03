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

const assistantJs = fs.readFileSync(new URL("../assets/assistant.js", import.meta.url), "utf8");
assert.ok(assistantJs.includes("plain_excerpt"), "Pagefind fallback must preserve a plain-text excerpt");
assert.ok(assistantJs.includes("assistant-source__excerpt"), "source rows must expose contextual excerpts when available");
assert.ok(assistantJs.includes("site-map"), "empty retrieval must fall back to the canonical site map");
assert.ok(!assistantJs.includes("innerHTML"), "assistant source rendering must stay textContent/DOM based, not raw HTML");

// Pseudo-element content audit (2026-09 round): assets/assistant.css labels
// each chat bubble's speaker purely via CSS ::before{content:"Asistente"/"Tú"}
// -- generated content that copy-paste, find-in-page, translation tools and
// some screen reader/browser combinations do not expose, unlike the sources
// list a few lines below in the same file, which already pairs its CSS label
// with a real aria-label. A chat transcript's speaker turns are meaningful
// content, not decoration, so each message article needs the same real
// accessible-name treatment.
assert.ok(assistantJs.includes('article.setAttribute("aria-label", role === "user" ? "Tú" : "Asistente")'), "cada mensaje del chat debe exponer su hablante en el árbol de accesibilidad, no solo vía CSS ::before");
assert.ok(assistantJs.includes('welcome.setAttribute("aria-label", "Asistente")'), "el mensaje de bienvenida estático también debe exponer su hablante de forma accesible");

const assistantCss = fs.readFileSync(new URL("../assets/assistant.css", import.meta.url), "utf8");
assert.ok(!assistantCss.includes("border-radius:999px"), "assistant must not regress to pill-shaped chat controls");
assert.ok(assistantCss.includes(".assistant-source__action::after"), "sources must keep an explicit editorial navigation affordance");
assert.ok(assistantCss.includes(".assistant-source__excerpt"), "source excerpts need an intentional editorial treatment");

const widgetCss = fs.readFileSync(new URL("../assets/assistant-widget.css", import.meta.url), "utf8");
assert.ok(!widgetCss.includes("assistant-widget-pulse"), "launcher must not pulse perpetually");

console.log("assistant-editorial-ux: OK");
