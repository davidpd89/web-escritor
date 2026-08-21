import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const base = process.env.BASE_SHA;
if (!base) throw new Error('BASE_SHA es obligatorio');

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
    ogImage: meta(html,'og:image',true),
    twitterCard: meta(html,'twitter:card'),
    twitterTitle: meta(html,'twitter:title'),
    twitterDescription: meta(html,'twitter:description'),
    twitterImage: meta(html,'twitter:image'),
    webApplication: webApplication(html),
  };
}

for (const path of paths) {
  const before = execFileSync('git', ['show', `${base}:${path}`], { encoding: 'utf8' });
  const after = fs.readFileSync(path, 'utf8');
  assert.deepEqual(extract(after), extract(before), `regresión de metadata/H1 en ${path}`);
}
console.log('PUBLISHING METADATA PRESERVATION: OK');
