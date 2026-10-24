import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const xml = fs.readFileSync('cuaderno/feed.xml', 'utf8');
const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map(m => m[1]);
const field = (item, name) => item.match(new RegExp(`<${name}>([\\s\\S]*?)<\\/${name}>`))?.[1];
const urls = [];
const dates = [];
assert.ok(items.length >= 5, 'RSS demasiado pequeño o vacío');
for (const item of items) {
  const url = field(item, 'link');
  const guid = field(item, 'guid');
  const publication = field(item, 'pubDate');
  assert.equal(url, guid, `GUID diferente del enlace: ${url}`);
  const pathname = new URL(url).pathname;
  assert.match(pathname, /^\/cuaderno\/[a-z0-9-]+\/$/);
  const file = path.join('.', pathname, 'index.html');
  assert.ok(fs.existsSync(file), `RSS apunta a fichero inexistente: ${pathname}`);
  const html = fs.readFileSync(file, 'utf8');
  const graph = JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)?.[1] || '{}');
  const article = (graph['@graph'] || [graph]).find(x => x['@type'] === 'Article');
  assert.ok(article, `${pathname}: RSS contiene una página que no es Article`);
  assert.equal(url, article.url, `${pathname}: enlace diferente del schema`);
  assert.equal(new Date(publication).toISOString().slice(0, 10), article.datePublished);
  urls.push(url);
  dates.push(Date.parse(publication));
}
assert.equal(new Set(urls).size, urls.length, 'Entradas RSS duplicadas');
assert.deepEqual(dates, [...dates].sort((a, b) => b - a), 'RSS fuera de orden cronológico');
console.log(`OK: ${items.length} entradas RSS verificadas`);
