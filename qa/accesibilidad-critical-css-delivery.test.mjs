import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const page = '/accesibilidad/';
const html = fs.readFileSync(path.join(root, 'accesibilidad/index.html'), 'utf8');

function attrs(tag) {
  return Object.fromEntries([...tag.matchAll(/([\w-]+)\s*=\s*(["'])(.*?)\2/g)].map(m => [m[1].toLowerCase(), m[3]]));
}

const styles = [...html.matchAll(/<link\b[^>]*>/gi)]
  .map(m => attrs(m[0]))
  .filter(a => (a.rel || '').toLowerCase().split(/\s+/).includes('stylesheet'));

test('la declaración recibe sus hojas CSS críticas sin referencias rotas', () => {
  assert.ok(styles.length > 0, `${page}: no hay hojas stylesheet`);
  const unique = new Set();
  let total = 0;
  for (const style of styles) {
    const url = new URL(style.href, 'https://davidportodiaz.com');
    assert.equal(url.origin, 'https://davidportodiaz.com', `${page}: stylesheet externo ${style.href}`);
    assert.match(url.pathname, /\.css$/i, `${page}: recurso no CSS ${style.href}`);
    if (unique.has(url.pathname)) continue;
    unique.add(url.pathname);
    const file = path.join(root, url.pathname.slice(1));
    assert.ok(fs.existsSync(file), `${page}: CSS inexistente ${style.href}`);
    const bytes = fs.statSync(file).size;
    assert.ok(bytes > 0, `${page}: CSS vacío ${style.href}`);
    total += bytes;
  }
  assert.ok(unique.has('/assets/v1-accessibility-statement.css'), `${page}: falta la hoja local de accesibilidad`);
  assert.ok(total <= 512 * 1024, `${page}: CSS bloqueante ${total} bytes supera 524288`);
});