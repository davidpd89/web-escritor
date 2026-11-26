// ID de la página de autor de Amazon.es leído de la ficha de un libro, con un Edge real (puppeteer-core).
// curl/urllib acaban bloqueados tras unas decenas de peticiones; un navegador con perfil propio no.
// Uso: node scripts/enrich-amazon-author-ids.mjs [--limite N] [--pausa ms]
// Reanudable: salta a quien ya tiene amazon_autor_id o amazon_autor_id_probado. Un bloqueo no cuenta como intento.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(process.env.NODE_MODULES_FROM || path.join(root, 'package.json'));
const puppeteer = require('puppeteer-core');
const EDGE = process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const limit = Number(arg('limite', 0));
const pause = Number(arg('pausa', 1500));

const authorsPath = path.join(root, 'data/reading-authors.json');
const data = JSON.parse(fs.readFileSync(authorsPath, 'utf8'));
let books = JSON.parse(fs.readFileSync(path.join(root, 'data/reading-catalogue.json'), 'utf8'));
books = books.libros || books;
const norm = (s) => s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const isbn10 = (i) => {
  if (!/^978\d{10}$/.test(i || '')) return null;
  const core = i.slice(3, 12);
  const sum = [...core].reduce((t, c, k) => t + (10 - k) * Number(c), 0);
  const chk = (11 - (sum % 11)) % 11;
  return core + (chk === 10 ? 'X' : String(chk));
};
const byAuthor = new Map();
for (const b of books) for (const n of b.autores || []) if (/^97[89]\d{10}$/.test(b.isbn13 || '')) (byAuthor.get(n) || byAuthor.set(n, []).get(n)).push(b.isbn13);
const save = () => fs.writeFileSync(authorsPath, JSON.stringify(data, null, 2) + '\n');
const sortKeys = (o) => Array.isArray(o) ? o.map(sortKeys) : o && typeof o === 'object' ? Object.fromEntries(Object.keys(o).sort().map((k) => [k, sortKeys(o[k])])) : o;
const saveSorted = () => { const sorted = sortKeys(data); fs.writeFileSync(authorsPath, JSON.stringify(sorted, null, 2) + '\n'); };

// Edge propio en el puerto 9263 con perfil temporal (no toca los Edge de ChatGPT ni de RRSS); puppeteer.launch falla
// con el msedge.exe de Windows porque el lanzador cede el proceso y sale con código 0.
import { spawn } from 'node:child_process';
const PORT = Number(process.env.EDGE_PORT || 9263);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'amz-ids-'));
const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, '--lang=es-ES', '--no-first-run', '--no-default-browser-check', '--window-size=900,700', 'about:blank'], { stdio: 'ignore', detached: false });
let browser;
for (let i = 0; i < 40 && !browser; i++) {
  await new Promise((r) => setTimeout(r, 500));
  browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${PORT}` }).catch(() => null);
}
if (!browser) { edge.kill(); throw new Error('Edge no respondió en el puerto ' + PORT); }
const page = await browser.newPage();
await page.setExtraHTTPHeaders({ 'Accept-Language': 'es-ES,es;q=0.9' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function authorLinks(url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const html = await page.content();
  if (html.length < 20000 && /seguir comprando|captcha|robot/i.test(html)) throw new Error('bloqueo');
  const links = await page.$$eval('a[href*="/e/B"]', (as) => as.map((a) => a.getAttribute('href')));
  if (process.env.DEBUG) console.log(url, html.length, (await page.title()).slice(0, 60), links.slice(0, 3));
  return links;
}
async function resolveUrl(isbn) {
  const ten = isbn10(isbn);
  if (ten) return 'https://www.amazon.es/dp/' + ten;
  await page.goto('https://www.amazon.es/s?i=stripbooks&k=' + isbn, { waitUntil: 'domcontentloaded', timeout: 45000 });
  const asin = await page.$eval('[data-asin]:not([data-asin=""])', (e) => e.getAttribute('data-asin')).catch(() => null);
  return asin ? 'https://www.amazon.es/dp/' + asin : null;
}

const today = new Date().toISOString().slice(0, 10);
let todo = data.autores.filter((a) => !a.amazon_autor_id && !a.amazon_autor_id_probado && byAuthor.get(a.nombre));
if (limit) todo = todo.slice(0, limit);
let found = 0, tried = 0, blocked = 0;
for (const a of todo) {
  tried++;
  let id = null, ok = true;
  try {
    for (const isbn of byAuthor.get(a.nombre).slice(0, 2)) {
      const url = await resolveUrl(isbn);
      if (url) {
        const wanted = norm(a.nombre);
        const tokens = (t) => norm(t).split(' ').sort().join(' ');
        for (const href of await authorLinks(url)) {
          const m = href.match(/^\/([^/]+)\/e\/(B[0-9A-Z]{9})/);
          if (m && tokens(decodeURIComponent(m[1]).replace(/-/g, ' ')) === tokens(a.nombre)) { id = m[2]; break; }
        }
      }
      await sleep(pause);
      if (id) break;
    }
  } catch (e) {
    ok = false; blocked++;
    console.log('bloqueo/error', a.nombre, String(e.message).slice(0, 80));
    await sleep(60000);
  }
  if (ok) { if (id) { a.amazon_autor_id = id; found++; } else a.amazon_autor_id_probado = today; }
  if (tried % 20 === 0) { saveSorted(); console.log(`${tried}/${todo.length} con ID: ${found} bloqueos: ${blocked}`); }
}
saveSorted();
await browser.close().catch(() => {});
edge.kill();
console.log(`Hecho: ${tried} intentos, ${found} con ID, ${blocked} bloqueos.`);
