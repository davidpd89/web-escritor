import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('accesibilidad/index.html', 'utf8');
const css = fs.readFileSync('assets/v1-accessibility-statement.css', 'utf8');
const clean = css.replace(/\/\*[\s\S]*?\*\//g, '');

const selectors = [...clean.matchAll(/([^{}]+)\{[^{}]*\}/g)].flatMap(match => match[1].split(',').map(s => s.trim())).filter(Boolean);

test('la hoja local tiene reglas y todas están delimitadas por la familia', () => {
  assert.ok(selectors.length > 0);
  for (const selector of selectors) {
    assert.match(selector, /\[data-family=["']accesibilidad["']\]/, `Selector sin aislamiento: ${selector}`);
  }
});

test('las clases locales utilizadas tienen correspondencia documental', () => {
  for (const name of ['a11y-narrow', 'a11y-route-list']) {
    assert.ok(css.includes('.' + name), `No existe estilo para ${name}`);
    assert.ok(html.includes(name), `No existe elemento para ${name}`);
  }
  assert.match(html, /data-family="accesibilidad"/);
  assert.match(html, /v1-accessibility-statement\.css/);
});

test('la hoja local no introduce recursos externos', () => {
  assert.doesNotMatch(clean, /@import\b|url\(\s*['"]?https?:\/\//i);
});