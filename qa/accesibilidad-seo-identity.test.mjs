import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('accesibilidad/index.html', 'utf8');
const attr = (tag, name) => new RegExp(`${name}="([^"]+)"`).exec(tag)?.[1];
const tag = (regex) => { const m = html.match(regex); assert.ok(m); return m[0]; };
const canonical = attr(tag(/<link\b[^>]*rel="canonical"[^>]*>/i), 'href');
const og = attr(tag(/<meta\b[^>]*property="og:url"[^>]*>/i), 'content');
const scripts = [...html.matchAll(/<script\b[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/gi)].map(m => JSON.parse(m[1]));
const page = scripts.find(obj => obj['@type'] === 'WebPage');

test('las identidades públicas son equivalentes', () => {
  assert.ok(page, 'Falta WebPage');
  assert.equal(canonical, 'https://davidportodiaz.com/accesibilidad/');
  assert.equal(og, canonical);
  assert.equal(page.url, canonical);
  assert.equal(page['@id'], canonical + '#page');
});

test('el idioma coincide entre documento y representación estructurada', () => {
  const language = attr(tag(/<html\b[^>]*>/i), 'lang');
  assert.equal(language, 'es');
  assert.equal(page.inLanguage, language);
});

test('la fecha visible es una fecha ISO válida y no futura', () => {
  const time = tag(/<time\b[^>]*datetime="[^"]+"[^>]*>/i);
  const date = attr(time, 'datetime');
  assert.match(date, /^\d{4}-\d{2}-\d{2}$/);
  const parsed = new Date(date + 'T00:00:00Z');
  assert.ok(Number.isFinite(parsed.valueOf()));
  assert.equal(parsed.toISOString().slice(0, 10), date);
  assert.ok(parsed.valueOf() <= Date.now(), 'Fecha de declaración futura');
});