// Vista esperada de un fichero fuente tal como lo publica el despliegue cuando hay portadas en el almacén externo
// (espejo en JS de scripts/reading_cover_store.py: rewrite_text + allow_img_host). Las auditorías de paridad con
// producción comparan contra esta vista, no contra el fuente crudo: con el manifiesto lleno, producción lleva la URL
// del almacén en las portadas y su host en la CSP.
import fs from 'node:fs';

const SITE = 'https://davidportodiaz.com';
const PREFIX = '/assets/reading-covers/';
const NAME = /^[a-z0-9][a-z0-9-]*\.(?:webp|jpg|jpeg|png)$/;

export function loadCoverStore(path = 'data/reading-covers-store.json') {
  if (!fs.existsSync(path)) return { base: '', stored: new Set(), extra: [], where: {} };
  const data = JSON.parse(fs.readFileSync(path, 'utf8'));
  const trim = url => String(url || '').replace(/\/+$/, '');
  // Varios almacenes: `almacenes` lista los siguientes al primero y `almacen` da el número (1 = almacenes[0]).
  return { base: trim(data.base_url), stored: new Set(data.archivos || []), extra: (data.almacenes || []).map(trim), where: data.almacen || {} };
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
