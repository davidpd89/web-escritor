// Candidatos de retrato para los autores sin foto: búsqueda de imágenes de Bing con un Edge real (puppeteer-core).
// Se queda solo con resultados cuyo título/URL contienen todas las palabras del nombre y no parecen portada, vídeo o stock.
// Uso: node scripts/author-photo-candidates.mjs [--limite N] [--pausa ms]   -> .local/author-photo-candidates.json (reanudable)
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path'; import { spawn } from 'node:child_process';
import { createRequire } from 'node:module'; import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(process.env.NODE_MODULES_FROM || path.join(root, 'package.json'));
const puppeteer = require('puppeteer-core');
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const limit = Number(arg('limite', 0)), pause = Number(arg('pausa', 1500)), PORT = Number(process.env.EDGE_PORT || 9263);
const norm = (s) => String(s).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const authors = JSON.parse(fs.readFileSync(path.join(root, 'data/reading-authors.json'), 'utf8')).autores;
const outPath = path.join(root, '.local/author-photo-candidates.json');
fs.mkdirSync(path.dirname(outPath), { recursive: true });
const out = fs.existsSync(outPath) ? JSON.parse(fs.readFileSync(outPath, 'utf8')) : {};
const BAD = /(shutterstock|istockphoto|alamy|gettyimages|dreamstime|depositphotos|freepik|youtube|ytimg|amazon\.|media-amazon|goodreads\.com\/book|casadellibro\.com\/libro|thickbox|portada|cover|book-?cover|\/libro\/|\.svg|logo|banner|sprite)/i;
const GOOD = /(wikipedia|wikimedia|planetadelibros|penguin|anagrama|periferica|siruela|asteroide|rbalibros|edicionesurano|nocturna|normaeditorial|harpercollins|simonandschuster|hachette|lafabrica|festival|elpais|abc\.es|lavanguardia|elmundo|rtve|cervantes|escritores|biografiasyvidas|lecturalia|todostuslibros|fnac|casadellibro|agencia|literar)/i;
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'ph-'));
const edge = spawn(process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', [`--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, '--lang=es-ES', '--no-first-run', '--window-size=900,700', 'about:blank'], { stdio: 'ignore' });
let browser; for (let i = 0; i < 40 && !browser; i++) { await new Promise((r) => setTimeout(r, 500)); browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${PORT}` }).catch(() => null); }
if (!browser) { edge.kill(); throw new Error('Edge no respondió'); }
const page = await browser.newPage();
let todo = authors.filter((a) => !a.foto && !(a.slug in out)); if (limit) todo = todo.slice(0, limit);
const save = () => fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
let n = 0, withCand = 0;
try {
  for (const a of todo) {
    n++;
    const tokens = norm(a.nombre).split(' ').filter((t) => t.length > 1);
    try {
      await page.goto('https://www.bing.com/images/search?q=' + encodeURIComponent(`"${a.nombre}" escritor autor`) + '&form=HDRSC2&first=1', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await new Promise((r) => setTimeout(r, 1800));
      const raw = await page.$$eval('a.iusc', (as) => as.slice(0, 24).map((x) => { try { const m = JSON.parse(x.getAttribute('m')); return { title: m.t || '', page: m.purl || '', img: m.murl || '', thumb: m.turl || '' }; } catch { return null; } }).filter(Boolean));
      const cands = raw.map((c) => {
        const text = norm(c.title + ' ' + c.page + ' ' + c.img.replace(/[-_.]/g, ' '));
        const all = tokens.every((t) => text.includes(t));
        const bad = BAD.test(c.img + ' ' + c.page + ' ' + c.title);
        return { ...c, score: (all ? 10 : 0) + (GOOD.test(c.page) ? 3 : 0) - (bad ? 20 : 0) };
      }).filter((c) => c.score >= 10).sort((x, y) => y.score - x.score).slice(0, 4);
      out[a.slug] = cands; if (cands.length) withCand++;
    } catch (e) { console.log('error', a.nombre, String(e.message).slice(0, 60)); await new Promise((r) => setTimeout(r, 20000)); }
    if (n % 20 === 0) { save(); console.log(`${n}/${todo.length} con candidatas: ${withCand}`); }
    await new Promise((r) => setTimeout(r, pause));
  }
} finally { save(); await browser.close().catch(() => {}); edge.kill(); }
console.log(`Hecho: ${n}, con candidatas ${withCand}`);
