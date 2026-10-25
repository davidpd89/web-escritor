import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const html = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');
const tags = [...html.matchAll(/<link\b[^>]*>/gi)].map(m => m[0]);
const attr = (tag, name) => new RegExp('(?:^|\\s)' + name + '\\s*=\s*["\x27]([^"\x27]+)["\x27]', 'i').exec(tag)?.[1];
const normalize = href => new URL(href, 'https://davidportodiaz.com').pathname;

const styles = new Set(tags.filter(tag => (attr(tag, 'rel') || '').split(/\s+/i).includes('stylesheet')).map(tag => normalize(attr(tag, 'href'))));
const preloads = tags.filter(tag => (attr(tag, 'rel') || '').split(/\s+/i).includes('preload') && attr(tag, 'as') === 'style');

test('las precargas CSS de accesibilidad son locales, únicas y entregables', () => {
  assert.ok(preloads.length > 0, '/accesibilidad/: faltan las precargas de estilos del shell');
  const seen = new Set();
  for (const tag of preloads) {
    const href = attr(tag, 'href');
    const url = new URL(href, 'https://davidportodiaz.com');
    assert.equal(url.origin, 'https://davidportodiaz.com', `/accesibilidad/: precarga externa ${href}`);
    assert.match(url.pathname, /\.css$/i, `/accesibilidad/: precarga no CSS ${href}`);
    assert.ok(!seen.has(url.pathname), `/accesibilidad/: precarga duplicada ${href}`);
    seen.add(url.pathname);
    assert.ok(fs.existsSync(path.join(root, url.pathname.slice(1))), `/accesibilidad/: precarga inexistente ${href}`);
  }
});

test('las precargas conservan un consumidor declarado o un cargador compartido', () => {
  const loaderFiles = ['assets/v1-shell.js', 'assets/v1-shell.css'];
  const loaders = loaderFiles.filter(p => fs.existsSync(path.join(root, p))).map(p => fs.readFileSync(path.join(root, p), 'utf8')).join('\n');
  for (const tag of preloads) {
    const href = attr(tag, 'href');
    const pathname = normalize(href);
    const basename = path.posix.basename(pathname);
    const consumed = styles.has(pathname) || loaders.includes(basename);
    assert.ok(consumed, `/accesibilidad/: precarga ${href} sin consumidor declarativo conocido`);
  }
});