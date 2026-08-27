import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const base = process.env.BASE_SHA;
if (!base) throw new Error('BASE_SHA es obligatorio');
// Un BASE_SHA inválido haría que todas las páginas parezcan "nuevas" y el gate
// pasaría en vacío, así que se comprueba que la referencia existe de verdad.
try {
  execFileSync('git', ['rev-parse', '--verify', `${base}^{commit}`], { stdio: 'ignore' });
} catch {
  throw new Error(`BASE_SHA no resuelve a un commit: ${base}`);
}

const paths = [
  'herramientas/metadatos-libro/index.html',
  'herramientas/json-ld-escritores/index.html',
  'herramientas/kit-prensa-escritores/index.html',
  'herramientas/auditor-pagina-libro/index.html',
];

function attr(tag, name) {
  const m = String(tag).match(new RegExp(`\\b${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)')`, 'i'));
  return m ? (m[1] ?? m[2] ?? '') : '';
}
function meta(html, key, property=false) {
  const tags = html.match(/<meta\b[^>]*>/gi) || [];
  const marker = property ? 'property' : 'name';
  for (const tag of tags) if (attr(tag, marker).toLowerCase() === key.toLowerCase()) return attr(tag, 'content');
  return '';
}
function text(html) {
  return String(html).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}
function webApplication(html) {
  const scripts = [...html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)];
  for (const m of scripts) {
    try {
      const value = JSON.parse(m[1]);
      if (value?.['@type'] === 'WebApplication') return value;
    } catch {}
  }
  return null;
}
// El og:image/twitter:image sitewide paso de .webp a .jpg (WhatsApp no
// renderiza fiablemente previews WebP); esa migracion de formato de imagen
// no es una regresion de metadata protegida, asi que se normaliza aqui para
// que el guard siga cazando cualquier otro cambio real en estos campos.
const normalizeImageExt = url => String(url).replace(/\.(webp|jpe?g)$/i, '.__img__');
function extract(html) {
  const title = text((html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)||[,''])[1]);
  const h1 = text((html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)||[,''])[1]);
  const canonicalTag = (html.match(/<link\b[^>]*rel=["']canonical["'][^>]*>/i)||[''])[0];
  return {
    title,
    description: meta(html,'description'),
    canonical: attr(canonicalTag,'href'),
    robots: meta(html,'robots'),
    h1,
    ogTitle: meta(html,'og:title',true),
    ogDescription: meta(html,'og:description',true),
    ogImage: normalizeImageExt(meta(html,'og:image',true)),
    twitterCard: meta(html,'twitter:card'),
    twitterTitle: meta(html,'twitter:title'),
    twitterDescription: meta(html,'twitter:description'),
    twitterImage: normalizeImageExt(meta(html,'twitter:image')),
    webApplication: webApplication(html),
  };
}

// Una página que no existía en la base no tiene metadata previa que preservar,
// así que se omite en lugar de romper el gate con un error crudo de git. Sólo
// aplica al caso "nueva en esta rama": si el fichero existe en la base y se ha
// borrado, readFileSync falla y el gate sigue avisando.
function existsInBase(path) {
  try {
    execFileSync('git', ['cat-file', '-e', `${base}:${path}`], { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

const introduced = [];
for (const path of paths) {
  if (!existsInBase(path)) { introduced.push(path); continue; }
  const before = execFileSync('git', ['show', `${base}:${path}`], { encoding: 'utf8' });
  const after = fs.readFileSync(path, 'utf8');
  assert.deepEqual(extract(after), extract(before), `regresión de metadata/H1 en ${path}`);
}
if (introduced.length) {
  console.log(`PUBLISHING METADATA PRESERVATION: ${introduced.length} página(s) nuevas respecto a la base, sin metadata que preservar:`);
  for (const path of introduced) console.log(` - ${path}`);
}
console.log('PUBLISHING METADATA PRESERVATION: OK');
