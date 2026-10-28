import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const html = readFileSync(new URL('../redes-sociales/index.html', import.meta.url), 'utf8');
const head = html.split(/<\/head>/i)[0];
const attr = (tag, name) => tag.match(new RegExp('\\b' + name + '="([^"]*)"', 'i'))?.[1] ?? null;
const metas = [...head.matchAll(/<meta\b[^>]*>/gi)].map(m => m[0]);
const links = [...head.matchAll(/<link\b[^>]*>/gi)].map(m => m[0]);
const meta = (name, value) => metas.filter(tag => attr(tag, name) === value);

test('redes-sociales: canonical, Open Graph y WebPage coinciden', () => {
  const canonical = links.filter(tag => (attr(tag, 'rel') ?? '').split(/\s+/).includes('canonical'));
  assert.equal(canonical.length, 1, '/redes-sociales/: canonical debe ser único');
  const url = attr(canonical[0], 'href');
  assert.equal(url, 'https://davidportodiaz.com/redes-sociales/', '/redes-sociales/: canonical incorrecto');
  assert.deepEqual(meta('property', 'og:url').map(tag => attr(tag, 'content')), [url], '/redes-sociales/: og:url divergente');
  const blocks = [...head.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi)].map(m => JSON.parse(m[1]));
  const nodes = blocks.flatMap(block => Array.isArray(block) ? block : block['@graph'] ?? [block]);
  const pages = nodes.filter(node => node && node['@type'] === 'WebPage' && node.url === url);
  assert.equal(pages.length, 1, '/redes-sociales/: WebPage propio ausente o duplicado');
  assert.equal(pages[0]['@id'], url + '#page', '/redes-sociales/: @id del documento incorrecto');
});

test('redes-sociales: metadatos públicos indexables', () => {
  const title = head.match(/<title>([\s\S]*?)<\/title>/i)?.[1]?.trim();
  assert.ok(title, '/redes-sociales/: título vacío');
  const descriptions = meta('name', 'description').map(tag => attr(tag, 'content'));
  assert.equal(descriptions.length, 1, '/redes-sociales/: description debe ser única');
  assert.ok(descriptions[0]?.trim(), '/redes-sociales/: description vacía');
  const robots = meta('name', 'robots').map(tag => attr(tag, 'content'));
  assert.equal(robots.length, 1, '/redes-sociales/: robots debe ser único');
  assert.ok(/(?:^|,)index(?:,|$)/.test(robots[0].replace(/\s/g, '')), '/redes-sociales/: indexación deshabilitada');
  assert.ok(!/noindex/i.test(robots[0]), '/redes-sociales/: noindex contradictorio');
});