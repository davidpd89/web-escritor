/**
 * Cloudflare Worker — bot de comunidad (Discord + Telegram) de davidportodiaz.com
 *
 * Rutas:
 *   POST /discord   Interactions Endpoint URL de la aplicación de Discord (slash command /libro).
 *   POST /telegram  Webhook del bot de Telegram (mensajes privados, /buscar y modo inline).
 *
 * El catálogo se lee de la web publicada (data/bot-books.json), así el bot siempre
 * recomienda lo mismo que hay en /lecturas/ sin desplegar nada nuevo.
 *
 * Secretos (wrangler secret put …), nunca en el repositorio:
 *   DISCORD_PUBLIC_KEY        clave pública de la aplicación (hex), para verificar Ed25519
 *   TELEGRAM_BOT_TOKEN        token de @BotFather
 *   TELEGRAM_WEBHOOK_SECRET   cadena aleatoria; Telegram la reenvía en cada petición
 * Variables opcionales:
 *   BOT_INDEX_URL             por defecto https://davidportodiaz.com/data/bot-books.json
 *   BOT_AI=true + binding AI  Workers AI reescribe la petición en palabras clave antes de buscar
 */
import { buscar, formatear } from './book-finder.mjs';

const INDEX_URL = 'https://davidportodiaz.com/data/bot-books.json';
const INDEX_TTL_MS = 10 * 60 * 1000;
const AI_MODEL = '@cf/meta/llama-3.1-8b-instruct';
let cache = { at: 0, indice: null };

const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export async function cargarIndice(env, fetcher = fetch) {
  if (cache.indice && Date.now() - cache.at < INDEX_TTL_MS) return cache.indice;
  const r = await fetcher(env.BOT_INDEX_URL || INDEX_URL, { cf: { cacheTtl: 600 } });
  if (!r.ok) { if (cache.indice) return cache.indice; throw new Error(`índice ${r.status}`); }
  cache = { at: Date.now(), indice: await r.json() };
  return cache.indice;
}

/** Con BOT_AI activo, el modelo solo traduce la petición a palabras clave; la búsqueda sigue siendo determinista. */
async function consultaConIA(env, frase) {
  if (env.BOT_AI !== 'true' || !env.AI) return frase;
  try {
    const out = await env.AI.run(AI_MODEL, {
      max_tokens: 60,
      messages: [
        { role: 'system', content: 'Convierte la petición de un lector en palabras clave en español para buscar en un catálogo de libros: género, tema, público (niños, juvenil), edad, formato (ebook, audiolibro, tapa dura, tapa blanda), precio máximo en euros y autor si lo nombra. Responde solo con las palabras clave, sin explicar nada.' },
        { role: 'user', content: frase.slice(0, 300) },
      ],
    });
    const kw = (out?.response || '').replace(/\s+/g, ' ').trim();
    return kw ? `${frase} ${kw}`.slice(0, 400) : frase;
  } catch { return frase; }
}

async function responder(env, frase, limite = 3) {
  const indice = await cargarIndice(env);
  let r = buscar(indice, frase, { limite });
  if (!r.resultados.length) r = buscar(indice, await consultaConIA(env, frase), { limite });
  return r;
}

// ---------- Discord ----------
const hex = h => Uint8Array.from(h.match(/../g), b => parseInt(b, 16));

export async function firmaDiscordValida(publicKeyHex, firma, timestamp, cuerpo) {
  if (!publicKeyHex || !firma || !timestamp) return false;
  try {
    const key = await crypto.subtle.importKey('raw', hex(publicKeyHex), { name: 'Ed25519' }, false, ['verify']);
    return await crypto.subtle.verify('Ed25519', key, hex(firma), new TextEncoder().encode(timestamp + cuerpo));
  } catch { return false; }
}

const recorte = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

function embedsDiscord({ resultados }) {
  return resultados.map(({ libro, compra, razones }) => ({
    title: recorte(libro.titulo, 250),
    url: compra ? compra.url : libro.amazon,
    description: recorte(libro.sinopsis, 300) + (razones.length ? `\n\n*${razones.join(' · ')}*` : ''),
    author: { name: recorte(libro.autores.join(', '), 250) },
    thumbnail: libro.portada ? { url: libro.portada } : undefined,
    fields: compra ? [{ name: 'Desde', value: `${(compra.precio / 100).toFixed(2).replace('.', ',')} € · ${compra.formato.replace('-', ' ')}`, inline: true }, { name: 'En la web', value: `[Ver en lecturas](${libro.web})`, inline: true }] : [{ name: 'En la web', value: `[Ver en lecturas](${libro.web})`, inline: true }],
    color: 0xb4532a,
  }));
}

export async function manejarDiscord(request, env) {
  const cuerpo = await request.text();
  const ok = await firmaDiscordValida(env.DISCORD_PUBLIC_KEY, request.headers.get('x-signature-ed25519'), request.headers.get('x-signature-timestamp'), cuerpo);
  if (!ok) return new Response('firma no válida', { status: 401 });
  const i = JSON.parse(cuerpo);
  if (i.type === 1) return json({ type: 1 }); // PING
  if (i.type === 2 && i.data?.name === 'libro') {
    const frase = String(i.data.options?.find(o => o.name === 'busco')?.value || '').slice(0, 300);
    const r = await responder(env, frase);
    if (!r.resultados.length) return json({ type: 4, data: { content: formatear(r, frase), flags: 64 } });
    return json({ type: 4, data: {
      content: `📚 Para «${recorte(frase, 120)}»${r.total > r.resultados.length ? ` (hay ${r.total} en total)` : ''}:`,
      embeds: embedsDiscord(r),
      allowed_mentions: { parse: [] },
    } });
  }
  return json({ type: 4, data: { content: 'Comando no reconocido.', flags: 64 } });
}

// ---------- Telegram ----------
const tg = (env, metodo, data) => fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${metodo}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(data) });
const AYUDA = 'Escríbeme lo que te apetece leer y te busco libros del catálogo de davidportodiaz.com. Por ejemplo: «un thriller de menos de 10 €», «fantasía para mi hijo de 11 años» o «algo de Neil Gaiman». También funciona en cualquier chat escribiendo @ y mi nombre seguido de la búsqueda.';

export async function manejarTelegram(request, env) {
  if (!env.TELEGRAM_WEBHOOK_SECRET || request.headers.get('x-telegram-bot-api-secret-token') !== env.TELEGRAM_WEBHOOK_SECRET) return new Response('no', { status: 401 });
  const u = await request.json();
  if (u.inline_query) {
    const frase = u.inline_query.query.trim().slice(0, 200);
    const r = frase.length < 3 ? { resultados: [] } : await responder(env, frase, 10);
    const results = r.resultados.map(({ libro, compra }) => ({
      type: 'article', id: libro.id.slice(0, 64), title: libro.titulo,
      description: `${libro.autores.join(', ')}${compra ? ` · ${(compra.precio / 100).toFixed(2).replace('.', ',')} €` : ''}`,
      thumbnail_url: libro.portada || undefined,
      input_message_content: { message_text: formatear({ resultados: [{ libro, compra, razones: [] }], total: 1 }, frase).replace(/\*\*/g, '*').replace(/^\*1\. /, '*'), parse_mode: 'Markdown', link_preview_options: { url: compra ? compra.url : libro.amazon } },
    }));
    await tg(env, 'answerInlineQuery', { inline_query_id: u.inline_query.id, results, cache_time: 300, is_personal: false });
    return new Response('ok');
  }
  const m = u.message;
  if (!m?.text) return new Response('ok');
  const privado = m.chat.type === 'private';
  let frase = m.text.trim();
  if (/^\/(start|ayuda|help)\b/.test(frase)) frase = '';
  else if (/^\/buscar\b/.test(frase)) frase = frase.replace(/^\/buscar(@\w+)?/, '').trim();
  else if (!privado) return new Response('ok'); // en grupos solo responde a /buscar
  const texto = frase ? formatear(await responder(env, frase), frase).replace(/\*\*/g, '*') : AYUDA;
  await tg(env, 'sendMessage', { chat_id: m.chat.id, text: texto, parse_mode: 'Markdown', reply_parameters: { message_id: m.message_id }, link_preview_options: { is_disabled: true } });
  return new Response('ok');
}

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (request.method !== 'POST') return new Response('Bot de comunidad de davidportodiaz.com', { status: 200 });
    if (pathname === '/discord') return manejarDiscord(request, env);
    if (pathname === '/telegram') return manejarTelegram(request, env);
    return new Response('no encontrado', { status: 404 });
  },
};
