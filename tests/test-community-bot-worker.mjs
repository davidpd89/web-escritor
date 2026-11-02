import assert from "node:assert/strict";
import fs from "node:fs";
import worker, { firmaDiscordValida } from "../bots/community-bot-worker.mjs";

const indice = fs.readFileSync(new URL("../data/bot-books.json", import.meta.url), "utf8");
const enviados = [];
globalThis.fetch = async (url, opts = {}) => {
  if (String(url).includes("bot-books.json")) return new Response(indice, { status: 200 });
  if (String(url).startsWith("https://api.telegram.org/")) { enviados.push({ metodo: String(url).split("/").pop(), cuerpo: JSON.parse(opts.body) }); return new Response("{}"); }
  throw new Error("fetch inesperado " + url);
};

// Firma Ed25519 como la envía Discord.
const { publicKey, privateKey } = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
const hex = b => Buffer.from(b).toString("hex");
const env = { DISCORD_PUBLIC_KEY: hex(await crypto.subtle.exportKey("raw", publicKey)), TELEGRAM_BOT_TOKEN: "x", TELEGRAM_WEBHOOK_SECRET: "s3cr3t" };
async function discord(body, { mala = false } = {}) {
  const ts = String(Math.floor(Date.now() / 1000)), txt = JSON.stringify(body);
  const firma = hex(await crypto.subtle.sign("Ed25519", privateKey, new TextEncoder().encode(ts + (mala ? txt + " " : txt))));
  return worker.fetch(new Request("https://bot.example/discord", { method: "POST", body: txt, headers: { "x-signature-ed25519": firma, "x-signature-timestamp": ts } }), env);
}

assert.equal(await firmaDiscordValida(env.DISCORD_PUBLIC_KEY, "", "1", "{}"), false);
assert.equal((await discord({ type: 1 }, { mala: true })).status, 401, "firma alterada se rechaza");
assert.deepEqual(await (await discord({ type: 1 })).json(), { type: 1 }, "PING → PONG");

const r = await (await discord({ type: 2, data: { name: "libro", options: [{ name: "busco", value: "algo de Neil Gaiman" }] } })).json();
assert.equal(r.type, 4);
assert.equal(r.data.embeds[0].title, "Coraline");
assert.match(r.data.embeds[0].url, /amazon\.es.*tag=davidporto-21/);
assert.deepEqual(r.data.allowed_mentions, { parse: [] }, "el bot nunca menciona a nadie");
const vacio = await (await discord({ type: 2, data: { name: "libro", options: [{ name: "busco", value: "qwerty zzz" }] } })).json();
assert.equal(vacio.data.flags, 64, "sin resultados: respuesta solo visible para quien preguntó");

// Telegram: secreto obligatorio, privado, grupo e inline.
const tgReq = (u, secreto = "s3cr3t") => worker.fetch(new Request("https://bot.example/telegram", { method: "POST", body: JSON.stringify(u), headers: { "x-telegram-bot-api-secret-token": secreto } }), env);
assert.equal((await tgReq({}, "otro")).status, 401);
await tgReq({ message: { message_id: 1, chat: { id: 5, type: "private" }, text: "thriller de menos de 10 euros" } });
assert.equal(enviados.at(-1).metodo, "sendMessage");
assert.match(enviados.at(-1).cuerpo.text, /tag=davidporto-21/);
const n = enviados.length;
await tgReq({ message: { message_id: 2, chat: { id: -9, type: "supergroup" }, text: "hola a todos" } });
assert.equal(enviados.length, n, "en grupos ignora la charla normal");
await tgReq({ message: { message_id: 3, chat: { id: -9, type: "supergroup" }, text: "/buscar@DavidPortoBot fantasía" } });
assert.equal(enviados.length, n + 1);
await tgReq({ inline_query: { id: "q1", query: "terror" } });
const inline = enviados.at(-1);
assert.equal(inline.metodo, "answerInlineQuery");
assert.ok(inline.cuerpo.results.length > 0 && inline.cuerpo.results.length <= 10);
assert.ok(inline.cuerpo.results.every(x => x.id.length <= 64));

console.log("test-community-bot-worker: PASS");
