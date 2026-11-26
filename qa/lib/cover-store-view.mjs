// Vista esperada de un fichero fuente tal como lo publica el despliegue cuando hay portadas en el almacén externo
// (espejo en JS de scripts/reading_cover_store.py: rewrite_text + allow_img_host). Las auditorías de paridad con
// producción comparan contra esta vista, no contra el fuente crudo: con el manifiesto lleno, producción lleva la URL
// del almacén en las portadas y su host en la CSP.
import crypto from 'node:crypto';
import fs from 'node:fs';

const SITE = 'https://davidportodiaz.com';
const PREFIX = '/assets/reading-covers/';
const NAME = /^[a-z0-9][a-z0-9-]*\.(?:webp|jpg|jpeg|png)$/;

export function loadCoverStore(path = 'data/reading-covers-store.json', localDir = 'assets/reading-covers') {
  if (!fs.existsSync(path)) return { base: '', stored: new Set(), extra: [], where: {} };
  const data = JSON.parse(fs.readFileSync(path, 'utf8'));
  const trim = url => String(url || '').replace(/\/+$/, '');
  const sha = data.sha256 || {};
  // Igual que reading_cover_store.stale_local: una portada con otros bytes en el repo se publica desde el repo.
  const stale = name => {
    const local = `${localDir}/${name}`;
    return fs.existsSync(local) && crypto.createHash('sha256').update(fs.readFileSync(local)).digest('hex') !== sha[name];
  };
  // Varios almacenes: `almacenes` lista los siguientes al primero y `almacen` da el número (1 = almacenes[0]).
  return { base: trim(data.base_url), stored: new Set((data.archivos || []).filter(n => !stale(n))), extra: (data.almacenes || []).map(trim), where: data.almacen || {} };
}

function urlOf(store, name) {
  const k = (store.where || {})[name];
  return k ? store.extra[k - 1] : store.base;
}

// Sustituye cada referencia a una portada del almacén (ruta del sitio o URL completa) sin construir una regex dinámica.
function rewriteRefs(text, store) {
  let out = '';
  let from = 0;
  for (let at = text.indexOf(PREFIX); at !== -1; at = text.indexOf(PREFIX, from)) {
    let end = at + PREFIX.length;
    while (end < text.length && /[a-z0-9.-]/.test(text[end])) end += 1;
    const name = text.slice(at + PREFIX.length, end);
    const start = text.startsWith(SITE, at - SITE.length) && at >= SITE.length ? at - SITE.length : at;
    if (NAME.test(name) && store.stored.has(name)) {
      out += text.slice(from, start) + `${urlOf(store, name)}/${name}`;
    } else {
      out += text.slice(from, end);
    }
    from = end;
  }
  return out + text.slice(from);
}

export function expectedPublished(text, { html = false, store = loadCoverStore() } = {}) {
  if (!store.stored.size) return text;
  let out = rewriteRefs(text, store);
  if (html) {
    const hosts = [...new Set([store.base, ...(store.extra || [])].map(url => { const u = new URL(url); return `${u.protocol}//${u.host}`; }))];
    out = out.replace(/(img-src[^;"]*?)(?=;|"|$)/g, directive => directive + hosts.filter(h => !directive.includes(h)).map(h => ` ${h}`).join(''));
  }
  return out;
}

// Mismos sufijos que reescribe el despliegue (scripts/reading_cover_store.py TEXT_SUFFIXES).
const TEXT_SUFFIXES = new Set(['.html', '.json', '.js', '.mjs', '.xml', '.txt', '.css', '.webmanifest', '.rss']);
let cachedStore = null;

// Lee un fichero del repo tal como lo publica el despliegue. Toda auditoría de producción lee con esto:
// leer el fuente crudo hace que las portadas que ya están en el almacén parezcan rotas o distintas en producción.
// encoding null devuelve un Buffer (comparaciones byte a byte); los binarios no se tocan.
export function readPublished(path, { encoding = 'utf8', store } = {}) {
  const raw = fs.readFileSync(path);
  const dot = path.lastIndexOf('.');
  const suffix = dot === -1 ? '' : path.slice(dot).toLowerCase();
  if (!TEXT_SUFFIXES.has(suffix)) return encoding ? raw.toString(encoding) : raw;
  const view = expectedPublished(raw.toString('utf8'), { html: suffix === '.html', store: store || (cachedStore ||= loadCoverStore()) });
  return encoding ? view : Buffer.from(view, 'utf8');
}
